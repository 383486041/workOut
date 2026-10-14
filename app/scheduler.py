# -*- coding: utf-8 -*-
"""
超轻量定时检测引擎
仅在每秒对比整分整秒，内存与 CPU 消耗接近 0%，支持多时间点、工作日过滤与贪睡机制
"""
import datetime
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class ReminderScheduler(QObject):
    """定时提醒调度器"""
    trigger_reminder = pyqtSignal(str)  # 触发信号，附带时间说明（如 "18:00" 或 "稍后提醒"）

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_mgr = config_manager
        
        # 记录已触发的时间戳字符串，如 "2026-10-08 18:00"，防止同一分钟重复触发
        self.last_triggered_key = None
        
        # 贪睡时间目标点 (datetime 对象)
        self.snooze_target = None

        # 主定时器：1秒一次极轻量检查（仅两三个整型比较，CPU 0%）
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._check_time)
        self.is_paused = False

    def start(self):
        """启动调度器"""
        self.timer.start()

    def stop(self):
        """停止调度器"""
        self.timer.stop()

    def set_paused(self, paused: bool):
        """暂停/恢复提醒"""
        self.is_paused = paused

    def add_snooze(self, minutes: int):
        """设置贪睡延迟"""
        self.snooze_target = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        print(f"[Scheduler] 已设置贪睡提醒，将在 {self.snooze_target.strftime('%H:%M:%S')} 再次提示")

    def _check_time(self):
        """秒级时间检测核心逻辑"""
        if self.is_paused:
            return

        now = datetime.datetime.now()
        current_minute_str = now.strftime("%Y-%m-%d %H:%M")
        current_time_str = now.strftime("%H:%M")
        weekday = now.weekday()  # 0: 周一 ... 6: 周日

        # 1. 检查贪睡闹钟
        if self.snooze_target is not None:
            if now >= self.snooze_target:
                self.snooze_target = None
                self.last_triggered_key = current_minute_str
                self.trigger_reminder.emit(f"稍后提醒 ({current_time_str})")
                return

        # 2. 检查工作日过滤
        workdays = self.config_mgr.get("workdays", [0, 1, 2, 3, 4])
        if weekday not in workdays:
            return

        # 3. 检查当前时间是否在设定的下班时间列表中
        reminder_times = self.config_mgr.get("reminder_times", ["18:00"])
        if current_time_str in reminder_times:
            # 保证每分钟只触发一次
            if self.last_triggered_key != current_minute_str:
                self.last_triggered_key = current_minute_str
                self.trigger_reminder.emit(f"下班时间 ({current_time_str})")

    def get_next_reminder_desc(self) -> str:
        """获取下一次提醒的时间文本描述（用于系统托盘 Tooltip）"""
        if self.is_paused:
            return "提醒已暂停"

        now = datetime.datetime.now()
        
        # 如果有活跃的贪睡闹钟
        if self.snooze_target and self.snooze_target > now:
            diff_secs = int((self.snooze_target - now).total_seconds())
            mins, secs = divmod(diff_secs, 60)
            return f"稍后提醒：{self.snooze_target.strftime('%H:%M:%S')} (约{mins}分{secs}秒后)"

        workdays = self.config_mgr.get("workdays", [0, 1, 2, 3, 4])
        reminder_times = sorted(self.config_mgr.get("reminder_times", ["18:00"]))

        if not workdays or not reminder_times:
            return "未启用任何提醒时间"

        # 向后扫描 14 天找到最近的下一次触发时间
        for day_offset in range(14):
            check_date = now.date() + datetime.timedelta(days=day_offset)
            if check_date.weekday() in workdays:
                for t_str in reminder_times:
                    try:
                        hour, minute = map(int, t_str.split(":"))
                        candidate_dt = datetime.datetime(
                            check_date.year, check_date.month, check_date.day, hour, minute, 0
                        )
                        if candidate_dt > now:
                            day_label = "今天" if day_offset == 0 else ("明天" if day_offset == 1 else f"{check_date.strftime('%m-%d')}")
                            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                            w_name = weekday_names[check_date.weekday()]
                            return f"下次下班提醒：{day_label} ({w_name}) {t_str}"
                    except Exception:
                        continue

        return "暂无即将到来的提醒"

    def get_pet_status(self) -> dict:
        """计算桌宠当前展示状态与精确倒计时数据"""
        now = datetime.datetime.now()
        workdays = self.config_mgr.get("workdays", [0, 1, 2, 3, 4])
        reminder_times = sorted(self.config_mgr.get("reminder_times", ["18:00"]))

        # 1. 非工作日
        if now.weekday() not in workdays:
            return {
                "status": "holiday",
                "time_str": "今日休息",
                "sub_text": "今日非工作日，享受假期",
                "progress": 1.0,
                "tip": "今天无需上班"
            }

        # 2. 未设置提醒时间
        if not reminder_times:
            return {
                "status": "holiday",
                "time_str": "未设时间",
                "sub_text": "请在设置中添加提醒时间",
                "progress": 0.0,
                "tip": "未设定下班时间"
            }

        # 3. 寻找今天即将到来的最近提醒时间点
        today_target = None
        for t_str in reminder_times:
            try:
                h, m = map(int, t_str.split(":"))
                target_dt = datetime.datetime(now.year, now.month, now.day, h, m, 0)
                if target_dt > now:
                    today_target = (target_dt, t_str)
                    break
            except Exception:
                continue

        if today_target:
            target_dt, t_str = today_target
            diff_secs = max(0, int((target_dt - now).total_seconds()))
            hours, remainder = divmod(diff_secs, 3600)
            mins, secs = divmod(remainder, 60)

            # 进度估算（以早 9:00 或工作时长为基准）
            work_start_dt = datetime.datetime(now.year, now.month, now.day, 9, 0, 0)
            if target_dt > work_start_dt:
                total_work_secs = (target_dt - work_start_dt).total_seconds()
                elapsed_secs = (now - work_start_dt).total_seconds()
                progress = max(0.0, min(1.0, elapsed_secs / total_work_secs))
            else:
                progress = 0.5

            if hours > 0:
                sub_text = f"还有 {hours}小时{mins}分"
            else:
                sub_text = f"还有 {mins}分{secs}秒"

            if diff_secs <= 600:
                tip = "快下班了，准备收拾工位"
            elif diff_secs <= 3600:
                tip = "最后冲刺，坚持就是胜利"
            elif progress >= 0.75:
                tip = "今日进度大半，继续加油"
            elif progress >= 0.5:
                tip = "下午好，保持专注"
            else:
                tip = "新的一天，活力满满"

            return {
                "status": "working",
                "time_str": f"{hours:02d}:{mins:02d}:{secs:02d}",
                "sub_text": sub_text,
                "target_time": t_str,
                "progress": progress,
                "tip": tip
            }
        else:
            # 今天时间已过
            return {
                "status": "off_work",
                "time_str": "已下班",
                "sub_text": "今天工作辛苦了，好好放松",
                "progress": 1.0,
                "tip": "已经下班啦，别加班了"
            }
