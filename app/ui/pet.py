# -*- coding: utf-8 -*-
"""
桌面宠物挂件模块 (Desktop Pet)
基于用户母版参考规范的 8 大动态装扮系统：
1. 晨间 (06:00 - 11:00): 咖啡杯冒热气
2. 午间 (11:00 - 14:00): 呼噜泡泡 Zzz...
3. 午后 (14:00 - 18:00): 挂钟/时钟渴望下班
4. 晚间 (18:00 - 23:00): 彩旗彩带下班庆祝
5. 深夜 (23:00 - 06:00): 蓝底波点睡帽 + 月牙星星
6. 雨天 / 雷雨: 撑绿荷叶伞 + 木牌水珠
7. 降雪 / 寒冷 (< 8℃): 红色围巾 + 木牌上下积雪与冰凌
8. 高温酷暑 (> 32℃): 切块西瓜 + 汗珠

南京浦口区实时气象接入，精准倒计时与工时微进度条。
严格禁止 Emoji 符号。
"""
import os
import datetime
from PyQt6.QtWidgets import (
    QWidget, QMenu, QApplication
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, pyqtSignal, QRectF, QPointF
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QLinearGradient,
    QMouseEvent, QAction, QCursor, QPainterPath, QActionGroup
)
from app.ui.pet_assets import get_pet_pixmap


class DesktopPetWidget(QWidget):
    """桌面猫咪趴牌倒计时挂件主窗体"""
    open_settings_requested = pyqtSignal()
    test_popup_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    THEME_NAMES = {
        "morning": "晨间咖啡 (06:00 - 11:00)",
        "noon": "午间打盹 (11:00 - 14:00)",
        "afternoon": "午后期待 (14:00 - 18:00)",
        "evening": "晚间拉旗 (18:00 - 23:00)",
        "night": "深夜睡帽 (23:00 - 06:00)",
        "rain": "荷叶雨伞 (雨天/雷雨)",
        "cold": "围巾积雪 (降雪/寒冷)",
        "hot": "切块西瓜 (高温酷暑)"
    }

    THEME_TIPS = {
        "morning": "早安！元气满满",
        "noon": "午休片刻，精神饱满",
        "afternoon": "午后冲刺，坚持到底",
        "evening": "下班啦！享受美好夜晚",
        "night": "夜深了，早点休息",
        "rain": "外面下雨，记得带伞",
        "cold": "天气寒冷，注意添衣",
        "hot": "天气炎热，多喝温水"
    }

    # 各装扮在 260x212 挂件木牌上的专属安全布局区域 (plaque_rect)
    THEME_BOUNDS = {
        "morning":   QRectF(36, 122, 126, 64),  # 避开右侧咖啡杯与升腾热气
        "afternoon": QRectF(36, 122, 126, 64),  # 避开右侧挂钟与感叹号
        "hot":       QRectF(102, 122, 124, 64), # 避开左下方大块切片西瓜
        "cold":      QRectF(34, 122, 78, 64),   # 避开正中偏左垂挂的红色围巾流苏
        "evening":   QRectF(48, 126, 164, 60),  # 避开木牌上沿拉旗
        "noon":      QRectF(48, 122, 164, 64),  # 木牌正中宽敞区域
        "night":     QRectF(48, 122, 164, 64),  # 木牌正中宽敞区域
        "rain":      QRectF(48, 122, 164, 64),  # 木牌正中宽敞区域
    }

    def __init__(self, config_manager, scheduler, weather_service, parent=None):
        super().__init__(parent)
        self.config_mgr = config_manager
        self.scheduler = scheduler
        self.weather_service = weather_service

        # 窗口标志：无边框、置顶、透明通道
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 挂件尺寸 (宽 260，高 212)
        self.widget_width = 260
        self.widget_height = 212
        self.setFixedSize(self.widget_width, self.widget_height)

        # 拖拽与悬停状态
        self.drag_position = QPoint()
        self.is_dragging = False
        self.is_hovered = False

        # 装扮模式："auto" 或指定装扮名 (morning, noon, afternoon, evening, night, rain, cold, hot)
        self.override_theme = self.config_mgr.get("pet_override_theme", "auto")
        self.current_theme = "afternoon"

        # 运行时缓存数据
        self.weather_display_text = "浦口·晴 25℃"
        self.weather_type = "晴"
        self.countdown_text = "00:00:00"
        self.sub_text = "正在计算下班时间..."
        self.target_time_text = ""
        self.progress_value = 0.5

        # 1 秒定时器刷新倒计时与状态
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._refresh_content)
        self.tick_timer.start(1000)

        self.apply_styles()
        self._restore_position()
        self._refresh_content()

        # 绑定天气更新事件
        if self.weather_service:
            self.weather_service.weather_updated.connect(self._on_weather_updated)
            self._on_weather_updated(self.weather_service.cached_weather)

    def apply_styles(self):
        """应用不透明度设置"""
        opacity = self.config_mgr.get("pet_opacity", 0.95)
        self.setWindowOpacity(opacity)

    def _determine_auto_theme(self) -> str:
        """
        根据当前南京浦口天气、气温与具体时段判定装扮形态：
        优先级 1：特殊天气/温度装扮 (降雪/寒冷 -> cold, 下雨/雷雨 -> rain, 高温酷暑 -> hot)
        优先级 2：日常作息时段装扮 (morning, noon, afternoon, evening, night)
        """
        weather = self.weather_service.cached_weather if self.weather_service else {}
        w_type = weather.get("type", "")
        temp_str = weather.get("temp", "").replace("℃", "")
        try:
            temp = float(temp_str)
        except Exception:
            temp = 20.0

        # 极端气象优先判断
        if any(k in w_type for k in ["雨", "雷", "暴雨", "阵雨"]):
            return "rain"
        if any(k in w_type for k in ["雪", "暴雪", "雨夹雪"]) or temp < 8.0:
            return "cold"
        if temp >= 32.0:
            return "hot"

        # 日常时段判断
        hour = datetime.datetime.now().hour
        if 6 <= hour < 11:
            return "morning"
        elif 11 <= hour < 14:
            return "noon"
        elif 14 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 23:
            return "evening"
        else:
            return "night"

    def _on_weather_updated(self, weather_data: dict):
        """天气数据异步更新回调"""
        if not weather_data:
            return
        w_type = weather_data.get("type", "晴")
        temp = weather_data.get("temp", "25℃")
        self.weather_type = w_type
        # 统一精简规范格式，例如 "浦口·晴 25℃"
        clean_temp = temp.replace(" ", "")
        if not clean_temp.endswith("℃") and clean_temp:
            clean_temp += "℃"
        self.weather_display_text = f"浦口·{w_type} {clean_temp}".strip()
        self._refresh_content()

    def _refresh_content(self):
        """更新倒计时与状态描述"""
        if self.override_theme != "auto" and self.override_theme in self.THEME_NAMES:
            new_theme = self.override_theme
        else:
            new_theme = self._determine_auto_theme()

        if new_theme != self.current_theme:
            self.current_theme = new_theme

        data = self.scheduler.get_pet_status() if self.scheduler else {}
        self.countdown_text = data.get("time_str", "00:00:00")
        self.sub_text = data.get("sub_text", "")
        self.progress_value = float(data.get("progress", 0.0))
        self.target_time_text = data.get("target_time", "")

        self.update()

    def paintEvent(self, event):
        """
        全量绘制：
        第 1 层：绘制当前主题 3D 猫咪木牌（260x212 高清无损）
        第 2 层：绘制半透明质感嵌入铭牌，彻底规避木纹杂色干扰
        第 3 层：在安全区域内层次分明地绘制天气、大倒计时、微进度条与贴心状态
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.widget_width, self.widget_height

        # 1. 绘制对应主题母版背景
        px = get_pet_pixmap(self.current_theme)
        if not px.isNull():
            painter.drawPixmap(0, 0, w, h, px)

        # 2. 获取当前主题专属铭牌安全区域
        plaque_rect = self.THEME_BOUNDS.get(self.current_theme, QRectF(48, 122, 164, 64))
        is_narrow = (plaque_rect.width() < 90)

        # 3. 绘制半透明暖木色微光嵌板底衬
        if self.is_hovered:
            plaque_bg = QColor(32, 18, 9, 135)
            plaque_pen = QPen(QColor(255, 235, 205, 55), 0.9)
        else:
            plaque_bg = QColor(22, 12, 6, 115)
            plaque_pen = QPen(QColor(255, 235, 205, 30), 0.8)

        painter.setPen(plaque_pen)
        painter.setBrush(QBrush(plaque_bg))
        painter.drawRoundedRect(plaque_rect, 7.0, 7.0)

        # 4. 绘制顶行：天气微矢量图标与文字
        weather_str = self.weather_display_text
        if is_narrow:
            # 狭窄模式精简文字
            weather_str = weather_str.replace("浦口·", "")

        font_weather = QFont("Microsoft YaHei", 7)
        font_weather.setBold(True)
        painter.setFont(font_weather)

        fm = painter.fontMetrics()
        txt_w = fm.horizontalAdvance(weather_str)
        icon_size = 11.0
        gap = 4.0
        tot_w = icon_size + gap + txt_w
        start_x = plaque_rect.center().x() - tot_w / 2.0
        line1_y = plaque_rect.top() + 3.0

        # 绘制微天气矢量图标
        icon_rect = QRectF(start_x, line1_y + 1.5, icon_size, icon_size)
        self._draw_weather_icon(painter, icon_rect, self.weather_type)

        # 绘制天气文字
        painter.setPen(QColor("#FEF3C7"))
        painter.drawText(QRectF(start_x + icon_size + gap, line1_y, txt_w + 5.0, 14.0),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, weather_str)

        # 5. 绘制核心倒计时大字
        cd_font_size = 11 if is_narrow else 13
        font_cd = QFont("Arial", cd_font_size, QFont.Weight.Bold)
        font_cd.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8 if is_narrow else 1.1)
        painter.setFont(font_cd)

        cd_rect = QRectF(plaque_rect.left(), plaque_rect.top() + 17.0, plaque_rect.width(), 20.0)
        # 细腻微暗阴影
        painter.setPen(QColor(0, 0, 0, 160))
        painter.drawText(QRectF(cd_rect.x(), cd_rect.y() + 1.0, cd_rect.width(), cd_rect.height()),
                         Qt.AlignmentFlag.AlignCenter, self.countdown_text)
        # 纯净象牙白正面文字
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(cd_rect, Qt.AlignmentFlag.AlignCenter, self.countdown_text)

        # 6. 绘制工时精致微进度条
        bar_w = min(plaque_rect.width() - 32.0, 108.0)
        bar_h = 3.5
        bar_x = plaque_rect.center().x() - bar_w / 2.0
        bar_y = plaque_rect.top() + 39.5
        bar_rect = QRectF(bar_x, bar_y, bar_w, bar_h)

        # 槽底
        painter.setPen(QPen(QColor(255, 255, 255, 25), 0.6))
        painter.setBrush(QBrush(QColor(0, 0, 0, 140)))
        painter.drawRoundedRect(bar_rect, 1.75, 1.75)

        # 进度填充
        pct = max(0.0, min(1.0, self.progress_value))
        if pct > 0.01:
            fill_w = bar_w * pct
            fill_rect = QRectF(bar_x, bar_y, fill_w, bar_h)
            grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
            grad.setColorAt(0.0, QColor("#38BDF8"))
            grad.setColorAt(1.0, QColor("#34D399"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(grad)
            painter.drawRoundedRect(fill_rect, 1.75, 1.75)

        # 7. 绘制底行状态/目标提醒文案 (严格置于进度条下方，绝不发生重叠)
        font_sub = QFont("Microsoft YaHei", 6 if is_narrow else 7)
        font_sub.setWeight(QFont.Weight.Medium)
        painter.setFont(font_sub)

        if self.is_hovered:
            sub_display = self.THEME_TIPS.get(self.current_theme, "保持好心情")
            sub_color = QColor("#FEF08A")
        else:
            if self.target_time_text:
                if is_narrow:
                    sub_display = f"目标 {self.target_time_text}"
                else:
                    # 简化剩余时长描述，例如 "目标 18:30 · 余4h"
                    short_sub = self.sub_text.replace("还有 ", "余").replace("小时", "h").replace("分钟", "m")
                    sub_display = f"目标 {self.target_time_text} · {short_sub}"
            else:
                sub_display = self.sub_text or "下班倒计时"
            sub_color = QColor("#FDE68A")

        sub_rect = QRectF(plaque_rect.left(), plaque_rect.top() + 46.0, plaque_rect.width(), 16.0)
        painter.setPen(sub_color)
        painter.drawText(sub_rect, Qt.AlignmentFlag.AlignCenter, sub_display)

        painter.end()

    def _draw_weather_icon(self, painter: QPainter, rect: QRectF, w_type: str):
        """矢量精简天气小图标"""
        cx = rect.center().x()
        cy = rect.center().y()

        if "晴" in w_type and "多云" not in w_type and "雨" not in w_type:
            # 晴天暖阳
            painter.setBrush(QBrush(QColor("#F59E0B")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - 3.0, cy - 3.0, 6.0, 6.0))
            pen = QPen(QColor("#F59E0B"), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(cx, cy - 4.5), QPointF(cx, cy - 3.5))
            painter.drawLine(QPointF(cx, cy + 3.5), QPointF(cx, cy + 4.5))
            painter.drawLine(QPointF(cx - 4.5, cy), QPointF(cx - 3.5, cy))
            painter.drawLine(QPointF(cx + 3.5, cy), QPointF(cx + 4.5, cy))

        elif "雨" in w_type or "雷" in w_type:
            # 雨天云朵与雨点
            painter.setBrush(QBrush(QColor("#94A3B8")))
            painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addEllipse(QRectF(cx - 4.0, cy - 3.0, 4.5, 4.5))
            path.addEllipse(QRectF(cx - 1.0, cy - 4.5, 5.5, 5.5))
            path.addRoundedRect(QRectF(cx - 4.5, cy - 1.5, 9.0, 3.5), 1.2, 1.2)
            painter.drawPath(path)
            # 雨丝
            pen = QPen(QColor("#38BDF8"), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(cx - 2.0, cy + 2.5), QPointF(cx - 3.0, cy + 4.5))
            painter.drawLine(QPointF(cx + 1.5, cy + 2.5), QPointF(cx + 0.5, cy + 4.5))

        elif "雪" in w_type:
            # 雪花
            pen = QPen(QColor("#E2E8F0"), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(cx, cy - 4.0), QPointF(cx, cy + 4.0))
            painter.drawLine(QPointF(cx - 3.5, cy - 2.0), QPointF(cx + 3.5, cy + 2.0))
            painter.drawLine(QPointF(cx - 3.5, cy + 2.0), QPointF(cx + 3.5, cy - 2.0))

        else:
            # 多云 / 阴天
            if "多云" in w_type:
                painter.setBrush(QBrush(QColor("#FBBF24")))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(cx - 1.0, cy - 4.0, 4.0, 4.0))

            painter.setBrush(QBrush(QColor("#94A3B8") if "阴" in w_type else QColor("#E2E8F0")))
            painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addEllipse(QRectF(cx - 4.0, cy - 2.0, 4.5, 4.5))
            path.addEllipse(QRectF(cx - 1.0, cy - 3.5, 5.0, 5.0))
            path.addRoundedRect(QRectF(cx - 4.5, cy - 0.8, 9.5, 3.8), 1.2, 1.2)
            painter.drawPath(path)

    # --- 交互事件 ---

    def _restore_position(self):
        """恢复上次放置的屏幕坐标"""
        x = self.config_mgr.get("pet_pos_x", -1)
        y = self.config_mgr.get("pet_pos_y", -1)
        screen = QApplication.primaryScreen().availableGeometry()

        if x < 0 or y < 0 or x > screen.width() or y > screen.height():
            target_x = screen.width() - self.width() - 30
            target_y = screen.height() - self.height() - 40
            self.move(target_x, target_y)
        else:
            self.move(x, y)

    def _save_position(self):
        """记录当前窗口坐标"""
        self.config_mgr.set("pet_pos_x", self.pos().x())
        self.config_mgr.set("pet_pos_y", self.pos().y())
        self.config_mgr.save()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.config_mgr.get("pet_locked", False):
                self.is_dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self._save_position()
            event.accept()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_settings_requested.emit()
            event.accept()

    def contextMenuEvent(self, event):
        """右键快捷菜单 (严格无 Emoji)"""
        menu = QMenu(self)

        action_refresh_weather = QAction("刷新南京浦口天气", menu)
        action_refresh_weather.triggered.connect(self._manual_refresh_weather)
        menu.addAction(action_refresh_weather)

        # 装扮形态切换子菜单
        theme_menu = menu.addMenu("时段与天气装扮")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        act_auto = QAction("自动感知环境 (推荐)", theme_menu)
        act_auto.setCheckable(True)
        act_auto.setChecked(self.override_theme == "auto")
        act_auto.triggered.connect(lambda: self._set_theme("auto"))
        theme_group.addAction(act_auto)
        theme_menu.addAction(act_auto)
        theme_menu.addSeparator()

        for t_key, t_name in self.THEME_NAMES.items():
            act = QAction(t_name, theme_menu)
            act.setCheckable(True)
            act.setChecked(self.override_theme == t_key)
            act.triggered.connect(lambda checked, k=t_key: self._set_theme(k))
            theme_group.addAction(act)
            theme_menu.addAction(act)

        menu.addSeparator()

        action_lock = QAction("锁定位置 (禁止拖动)", menu)
        action_lock.setCheckable(True)
        action_lock.setChecked(self.config_mgr.get("pet_locked", False))
        action_lock.triggered.connect(self._toggle_lock)
        menu.addAction(action_lock)

        action_top = QAction("始终置顶显示", menu)
        action_top.setCheckable(True)
        action_top.setChecked(bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        action_top.triggered.connect(self._toggle_top)
        menu.addAction(action_top)

        # 透明度子菜单
        opacity_menu = menu.addMenu("透明度调节")
        cur_op = int(self.config_mgr.get("pet_opacity", 0.95) * 100)
        op_group = QActionGroup(self)
        op_group.setExclusive(True)
        for op_val in [100, 90, 80, 70]:
            act_op = QAction(f"{op_val}%", opacity_menu)
            act_op.setCheckable(True)
            act_op.setChecked(abs(cur_op - op_val) < 5)
            act_op.triggered.connect(lambda checked, v=op_val/100.0: self._set_opacity(v))
            op_group.addAction(act_op)
            opacity_menu.addAction(act_op)

        menu.addSeparator()

        action_settings = QAction("打开设置中心", menu)
        action_settings.triggered.connect(self.open_settings_requested.emit)
        menu.addAction(action_settings)

        action_test = QAction("立即测试全屏提醒", menu)
        action_test.triggered.connect(self.test_popup_requested.emit)
        menu.addAction(action_test)

        action_hide = QAction("隐藏挂件 (可从托盘重新开启)", menu)
        action_hide.triggered.connect(self._hide_pet)
        menu.addAction(action_hide)

        menu.addSeparator()

        action_exit = QAction("退出程序", menu)
        action_exit.triggered.connect(self.exit_requested.emit)
        menu.addAction(action_exit)

        menu.exec(QCursor.pos())

    def _set_theme(self, theme_key: str):
        self.override_theme = theme_key
        self.config_mgr.set("pet_override_theme", theme_key)
        self.config_mgr.save()
        self._refresh_content()

    def _set_opacity(self, opacity: float):
        self.config_mgr.set("pet_opacity", opacity)
        self.config_mgr.save()
        self.apply_styles()

    def _manual_refresh_weather(self):
        if self.weather_service:
            self.weather_display_text = "浦口 刷新中..."
            self.weather_service.fetch_weather_async()
            self.update()

    def _toggle_lock(self, checked: bool):
        self.config_mgr.set("pet_locked", checked)
        self.config_mgr.save()

    def _toggle_top(self, checked: bool):
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _hide_pet(self):
        self.config_mgr.set("show_pet", False)
        self.config_mgr.save()
        self.hide()
