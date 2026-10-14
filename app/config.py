# -*- coding: utf-8 -*-
"""
配置管理器：负责加载、保存和维护用户的所有偏好设置
"""
import os
import sys
import json
import copy

DEFAULT_CONFIG = {
    # 提醒时间与工作日
    "reminder_times": ["18:00"],  # 支持多个提醒时间点，如 ["17:55", "18:00"]
    "workdays": [0, 1, 2, 3, 4],  # 0: 周一, 1: 周二, 2: 周三, 3: 周四, 4: 周五, 5: 周六, 6: 周日
    "snooze_minutes": 5,          # 贪睡延迟提醒分钟数
    "enable_sound": True,         # 是否播放提示音
    "auto_close_seconds": 0,      # 弹窗自动关闭倒计时（0表示不自动关闭，需手动点击）

    # 提示文案设置
    "title_text": "今日下班时间到啦！",
    "subtitle_text": "辛苦了一整天，请记得保存工作、打卡下班，好好享受美好的个人生活吧！",
    "show_clock": True,           # 是否在全屏弹窗中显示当前实时大时钟

    # 字体与排版
    "font_family": "Microsoft YaHei", # 字体：微软雅黑
    "title_font_size": 36,
    "subtitle_font_size": 18,
    "title_color": "#FFFFFF",
    "subtitle_color": "#E2E8F0",
    "clock_color": "#38BDF8",

    # 背景样式配置
    # background_type: "preset_dark" | "gradient" | "color" | "image"
    "background_type": "preset_dark",
    "background_color": "#0F172A",     # 纯色背景色
    "gradient_preset": "sunset",       # 渐变预设: "sunset" | "aurora" | "midnight" | "ocean"
    "custom_image_path": "",           # 自定义背景图片绝对路径
    "overlay_opacity": 0.85,           # 遮罩层不透明度 (0.1 ~ 1.0)
    "card_background_color": "rgba(30, 41, 59, 0.75)", # 卡片磨砂背景

    # 系统设置
    "autostart": False,                # 开机自启动

    # 桌面宠物挂件设置
    "show_pet": True,                  # 是否显示桌面挂件
    "pet_pos_x": -1,                   # 桌面挂件记忆坐标 X (-1 表示右下角自适应)
    "pet_pos_y": -1,                   # 桌面挂件记忆坐标 Y
    "pet_opacity": 0.95,               # 挂件不透明度
    "pet_locked": False,               # 是否锁定位置禁止拖动
}

class ConfigManager:
    def __init__(self, config_path=None):
        if config_path is None:
            if getattr(sys, "frozen", False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_path = os.path.join(base_dir, "config.json")
        else:
            self.config_path = config_path
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """从本地 json 加载配置，若不存在或损坏则使用默认配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # 合并默认值，防止缺失新字段
                        for k, v in DEFAULT_CONFIG.items():
                            if k in data:
                                self.config[k] = data[k]
                            else:
                                self.config[k] = v
                        return
            except Exception as e:
                print(f"[ConfigManager] 读取配置文件失败，使用默认配置: {e}")
        self.save()

    def save(self):
        """将当前配置写入文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[ConfigManager] 写入配置文件失败: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def update(self, new_data: dict):
        self.config.update(new_data)
        self.save()
