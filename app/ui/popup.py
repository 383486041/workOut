# -*- coding: utf-8 -*-
"""
全屏提醒弹窗模块
包含现代扁平/磨砂视觉、独立的淡入淡出动画、实时时钟、自定义背景与操作按钮
"""
import os
import winsound
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGraphicsDropShadowEffect, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QTime
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPixmap, QLinearGradient, QBrush, 
    QKeyEvent, QCursor
)
from app.ui.assets import GRADIENT_PRESETS

class FullscreenPopup(QWidget):
    """全屏下班提醒窗口"""
    snooze_requested = pyqtSignal(int)  # 信号：传递贪睡分钟数
    closed = pyqtSignal()               # 信号：窗口完全关闭

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_mgr = config_manager
        self.config = self.config_mgr.config
        
        # 窗口属性：无边框、强置顶、支持透明/半透明绘制
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 彻底解耦淡入与淡出动画控制器，避免复用同一对象导致淡入结束误触发淡出隐藏
        self.fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_anim.setDuration(350)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(300)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_anim.finished.connect(self._on_fade_out_finished)

        # 实时时钟刷新定时器
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)

        # 自动关闭倒计时定时器
        self.auto_close_remaining = 0
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.timeout.connect(self._tick_auto_close)

        # 背景图片缓存
        self.cached_bg_pixmap = None
        self.cached_bg_path = None

        self._init_ui()

    def _init_ui(self):
        """构建界面布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 居中卡片容器
        self.card = QFrame()
        self.card.setObjectName("CenterCard")
        self.card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.card.setMinimumWidth(580)
        self.card.setMaximumWidth(780)

        # 阴影特效
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(48)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 12)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(48, 42, 48, 42)
        card_layout.setSpacing(22)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 0. 顶部操作栏
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        self.top_badge = QLabel("下班提醒助手")
        self.top_badge.setStyleSheet("color: rgba(255, 255, 255, 0.55); font-size: 13px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        top_bar.addWidget(self.top_badge)
        top_bar.addStretch()

        self.btn_top_close = QPushButton("×")
        self.btn_top_close.setObjectName("btn_top_close")
        self.btn_top_close.setFixedSize(28, 28)
        self.btn_top_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_top_close.setToolTip("关闭提醒 (Esc)")
        self.btn_top_close.clicked.connect(self.close_with_animation)
        top_bar.addWidget(self.btn_top_close)
        card_layout.addLayout(top_bar)

        # 1. 实时时钟显示
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet("background: transparent;")
        card_layout.addWidget(self.clock_label)

        # 2. 主标题
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("background: transparent;")
        card_layout.addWidget(self.title_label)

        # 3. 分隔线
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); max-height: 1px;")
        card_layout.addWidget(divider)

        # 4. 副标题 / 详细提醒内容
        self.subtitle_label = QLabel()
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet("background: transparent; line-height: 1.6;")
        card_layout.addWidget(self.subtitle_label)

        # 5. 按钮组
        button_layout = QHBoxLayout()
        button_layout.setSpacing(18)
        button_layout.setContentsMargins(0, 15, 0, 0)

        # 主按钮：收到/打卡下班
        self.btn_confirm = QPushButton("收到，准备下班")
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setFixedHeight(48)
        self.btn_confirm.clicked.connect(self.close_with_animation)
        button_layout.addWidget(self.btn_confirm)

        # 稍后提醒按钮
        self.btn_snooze = QPushButton("稍后提醒")
        self.btn_snooze.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_snooze.setFixedHeight(48)
        self.btn_snooze.clicked.connect(self._on_snooze_clicked)
        button_layout.addWidget(self.btn_snooze)

        card_layout.addLayout(button_layout)

        # 6. 底部微提示（按 Esc 或点击右上角关闭）
        self.hint_label = QLabel("按 Esc 键或点击右上角 × 可关闭此窗口")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("color: rgba(255, 255, 255, 0.45); font-size: 13px; background: transparent;")
        card_layout.addWidget(self.hint_label)

        main_layout.addWidget(self.card)

    def apply_styles(self):
        """依据当前最新配置重新渲染样式与文本"""
        self.config = self.config_mgr.config
        font_family = self.config.get("font_family", "Microsoft YaHei")

        # 1. 实时时钟样式
        if self.config.get("show_clock", True):
            self.clock_label.setVisible(True)
            clock_color = self.config.get("clock_color", "#38BDF8")
            self.clock_label.setFont(QFont(font_family, 48, QFont.Weight.Bold))
            self.clock_label.setStyleSheet(f"color: {clock_color}; background: transparent; letter-spacing: 2px;")
            self._update_clock()
        else:
            self.clock_label.setVisible(False)

        # 2. 主标题样式与内容
        title_text = self.config.get("title_text", "今日下班时间到啦！")
        title_size = self.config.get("title_font_size", 34)
        title_color = self.config.get("title_color", "#FFFFFF")
        self.title_label.setText(title_text)
        self.title_label.setFont(QFont(font_family, title_size, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {title_color}; background: transparent;")

        # 3. 副标题样式与内容
        subtitle_text = self.config.get("subtitle_text", "辛苦了一整天，请记得保存工作、打卡下班，好好享受生活！")
        subtitle_size = self.config.get("subtitle_font_size", 16)
        subtitle_color = self.config.get("subtitle_color", "#E2E8F0")
        self.subtitle_label.setText(subtitle_text)
        self.subtitle_label.setFont(QFont(font_family, subtitle_size, QFont.Weight.Normal))
        self.subtitle_label.setStyleSheet(f"color: {subtitle_color}; background: transparent;")

        # 4. 贪睡按钮文案
        snooze_min = self.config.get("snooze_minutes", 5)
        self.btn_snooze.setText(f"稍后提醒 ({snooze_min}分钟)")

        # 5. 卡片样式与按钮样式 (现代磨砂玻璃样式)
        bg_type = self.config.get("background_type", "preset_dark")
        if bg_type in ("gradient", "image"):
            card_bg = "rgba(15, 23, 42, 0.72)"
        else:
            card_bg = "rgba(20, 28, 48, 0.90)"

        self.card.setStyleSheet(f"""
            QFrame#CenterCard {{
                background-color: {card_bg};
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 24px;
            }}
            QPushButton {{
                font-family: "{font_family}";
                font-size: 15px;
                font-weight: bold;
                border-radius: 12px;
                padding: 0 20px;
            }}
            QPushButton#{self.btn_confirm.objectName()} {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669);
                color: #FFFFFF;
                border: none;
            }}
            QPushButton#{self.btn_confirm.objectName()}:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34D399, stop:1 #10B981);
            }}
            QPushButton#{self.btn_confirm.objectName()}:pressed {{
                background: #047857;
            }}
            QPushButton#{self.btn_snooze.objectName()} {{
                background-color: rgba(255, 255, 255, 0.12);
                color: #F1F5F9;
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
            QPushButton#{self.btn_snooze.objectName()}:hover {{
                background-color: rgba(255, 255, 255, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }}
            QPushButton#{self.btn_snooze.objectName()}:pressed {{
                background-color: rgba(255, 255, 255, 0.08);
            }}
            QPushButton#btn_top_close {{
                background-color: rgba(255, 255, 255, 0.12);
                color: rgba(255, 255, 255, 0.7);
                border: none;
                border-radius: 14px;
                padding: 0;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton#btn_top_close:hover {{
                background-color: rgba(239, 68, 68, 0.85);
                color: #FFFFFF;
            }}
        """)
        self.btn_confirm.setObjectName("btn_confirm")
        self.btn_snooze.setObjectName("btn_snooze")

        # 预加载图片背景
        img_path = self.config.get("custom_image_path", "")
        if bg_type == "image" and img_path and os.path.exists(img_path):
            if self.cached_bg_path != img_path:
                self.cached_bg_pixmap = QPixmap(img_path)
                self.cached_bg_path = img_path
        else:
            self.cached_bg_pixmap = None
            self.cached_bg_path = None

    def trigger_popup(self):
        """触发并展现全屏弹窗（含平滑淡入动画与提示音）"""
        self.apply_styles()

        # 停止可能存在的旧动画
        self.fade_out_anim.stop()
        self.fade_in_anim.stop()

        # 精确适配当前屏幕几何尺寸，强行全屏覆盖
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        # 提示音
        if self.config.get("enable_sound", True):
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

        # 启动时钟定时器
        self.clock_timer.start(1000)

        # 自动关闭逻辑
        auto_sec = self.config.get("auto_close_seconds", 0)
        if auto_sec > 0:
            self.auto_close_remaining = auto_sec
            self.btn_confirm.setText(f"收到，准备下班 ({self.auto_close_remaining}s)")
            self.auto_close_timer.start(1000)
        else:
            self.auto_close_timer.stop()
            self.btn_confirm.setText("收到，准备下班")

        # 强制重绘背景
        self.update()

        # 显示全屏并置顶
        self.setWindowOpacity(0.0)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

        # 执行独立淡入动画
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.start()

    def close_with_animation(self):
        """平滑淡出并关闭"""
        self.clock_timer.stop()
        self.auto_close_timer.stop()

        self.fade_in_anim.stop()
        self.fade_out_anim.stop()
        self.fade_out_anim.setStartValue(self.windowOpacity())
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.start()

    def _on_fade_out_finished(self):
        """仅在淡出动画完成时隐藏并发出关闭信号"""
        self.hide()
        self.closed.emit()

    def _on_snooze_clicked(self):
        """点击稍后提醒"""
        snooze_min = self.config.get("snooze_minutes", 5)
        self.snooze_requested.emit(snooze_min)
        self.close_with_animation()

    def _update_clock(self):
        """更新大时钟显示"""
        now = QTime.currentTime()
        self.clock_label.setText(now.toString("HH:mm:ss"))

    def _tick_auto_close(self):
        """自动关闭倒计时"""
        self.auto_close_remaining -= 1
        if self.auto_close_remaining <= 0:
            self.auto_close_timer.stop()
            self.close_with_animation()
        else:
            self.btn_confirm.setText(f"收到，准备下班 ({self.auto_close_remaining}s)")

    def paintEvent(self, event):
        """绘制全屏背景（渐变、纯色、自定义图片、遮罩）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        bg_type = self.config.get("background_type", "preset_dark")
        overlay_opacity = self.config.get("overlay_opacity", 0.85)

        if bg_type == "image" and self.cached_bg_pixmap and not self.cached_bg_pixmap.isNull():
            # 绘制缩放壁纸图片
            scaled_pixmap = self.cached_bg_pixmap.scaled(
                w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                Qt.TransformationMode.SmoothTransformation
            )
            sx = (scaled_pixmap.width() - w) // 2
            sy = (scaled_pixmap.height() - h) // 2
            painter.drawPixmap(0, 0, scaled_pixmap, sx, sy, w, h)
            overlay_alpha = int(overlay_opacity * 255)
            painter.fillRect(0, 0, w, h, QColor(10, 15, 30, overlay_alpha))

        elif bg_type == "gradient":
            # 绘制渐变背景
            preset_name = self.config.get("gradient_preset", "sunset")
            preset_info = GRADIENT_PRESETS.get(preset_name, GRADIENT_PRESETS["sunset"])
            gradient = QLinearGradient(0, 0, w, h)
            for stop_pos, hex_color in preset_info["stops"]:
                gradient.setColorAt(stop_pos, QColor(hex_color))
            painter.fillRect(0, 0, w, h, QBrush(gradient))
            # 遮罩浓度
            overlay_alpha = int(overlay_opacity * 100)
            painter.fillRect(0, 0, w, h, QColor(0, 0, 0, overlay_alpha))

        elif bg_type == "color":
            # 绘制自定义纯色背景
            color_hex = self.config.get("background_color", "#0F172A")
            bg_color = QColor(color_hex)
            alpha = int(overlay_opacity * 255)
            bg_color.setAlpha(alpha)
            painter.fillRect(0, 0, w, h, bg_color)

        else:
            # 默认 preset_dark (极简深邃暗黑磨砂风)
            gradient = QLinearGradient(0, 0, 0, h)
            gradient.setColorAt(0.0, QColor(15, 23, 42, 235))
            gradient.setColorAt(1.0, QColor(2, 6, 23, 245))
            painter.fillRect(0, 0, w, h, QBrush(gradient))

        painter.end()

    def keyPressEvent(self, event: QKeyEvent):
        """按下 Esc 退出弹窗"""
        if event.key() == Qt.Key.Key_Escape:
            self.close_with_animation()
        else:
            super().keyPressEvent(event)
