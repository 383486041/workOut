# -*- coding: utf-8 -*-
"""
下班提醒助手 - 现代化控制中心与设置界面
包含侧边栏导航、概览工作台、日程管理、桌宠装扮选择器、全屏视觉与系统集成
全套矢量 SVG 图标接入，多选框对勾精准渲染，现代卡片交互布局。
严格禁止 Emoji 符号。
"""
import os
import datetime
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QCheckBox, QTimeEdit, QListWidget,
    QFileDialog, QColorDialog, QSpinBox, QComboBox, QSlider, QGroupBox,
    QMessageBox, QListWidgetItem, QFrame, QScrollArea, QStackedWidget,
    QButtonGroup, QProgressBar, QApplication, QGridLayout
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal, QTimer, QRectF, QSize
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon, QPainter, QBrush, QPen

from app.config import DEFAULT_CONFIG
from app.autostart import is_autostart_enabled, set_autostart
from app.ui.assets import GRADIENT_PRESETS, create_app_icon
from app.ui.svg_icons import (
    get_svg_icon, get_svg_pixmap, get_checkbox_check_path, ensure_icons_exported
)


class SettingsDialog(QDialog):
    """现代控制中心与个性化设置窗口"""
    config_saved = pyqtSignal()   # 配置保存信号
    test_requested = pyqtSignal() # 立即测试全屏提醒信号

    def __init__(self, config_manager, scheduler=None, weather_service=None, parent=None):
        super().__init__(parent)
        self.config_mgr = config_manager
        self.scheduler = scheduler
        self.weather_service = weather_service

        # 确保 SVG 资源文件输出就绪
        ensure_icons_exported()

        self.setWindowTitle("下班提醒助手 - 控制中心")
        self.setWindowIcon(create_app_icon(32))
        self.setMinimumSize(920, 640)
        self.resize(940, 660)

        # 临时颜色变量
        self.current_title_color = "#FFFFFF"
        self.current_subtitle_color = "#E2E8F0"
        self.current_clock_color = "#38BDF8"
        self.current_bg_color = "#0F172A"

        # 选中的宠物装扮
        self.selected_pet_theme = "auto"

        # 实时刷新定时器 (窗口展示时每秒刷新概览页倒计时)
        self.overview_timer = QTimer(self)
        self.overview_timer.timeout.connect(self._refresh_overview_live)

        self._init_ui()
        self.load_from_config()

    def _init_ui(self):
        """构建界面布局与核心样式表"""
        check_svg_url = get_checkbox_check_path()

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #F8FAFC;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }}
            /* 侧边栏样式 */
            QFrame#SidebarFrame {{
                background-color: #0F172A;
                border-right: 1px solid #1E293B;
            }}
            QLabel#SidebarTitle {{
                color: #F8FAFC;
                font-size: 15px;
                font-weight: bold;
            }}
            QLabel#SidebarSubtitle {{
                color: #64748B;
                font-size: 11px;
            }}
            QLabel#SidebarBadge {{
                color: #38BDF8;
                background-color: rgba(56, 189, 248, 0.12);
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton.NavButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: #94A3B8;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding: 10px 14px;
            }}
            QPushButton.NavButton:hover {{
                background-color: rgba(255, 255, 255, 0.06);
                color: #F1F5F9;
            }}
            QPushButton.NavButton:checked {{
                background-color: #1E293B;
                color: #FFFFFF;
                font-weight: bold;
                border-left: 3px solid #38BDF8;
            }}
            QFrame#SidebarMiniCard {{
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
            }}
            /* 内容区顶部与卡片 */
            QFrame#ContentHeader {{
                background-color: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }}
            QLabel#HeaderTitle {{
                color: #0F172A;
                font-size: 18px;
                font-weight: bold;
            }}
            QLabel#HeaderSubtitle {{
                color: #64748B;
                font-size: 12px;
            }}
            QFrame.SectionCard {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }}
            QLabel.CardHeaderTitle {{
                color: #0F172A;
                font-size: 14px;
                font-weight: bold;
            }}
            QLabel.CardHeaderSub {{
                color: #64748B;
                font-size: 12px;
            }}
            /* 基础输入控件 */
            QLineEdit, QTextEdit, QTimeEdit, QComboBox, QSpinBox {{
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 10px;
                background-color: #FFFFFF;
                font-size: 13px;
                color: #0F172A;
            }}
            QLineEdit:focus, QTextEdit:focus, QTimeEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border: 1.5px solid #0284C7;
                outline: none;
            }}
            /* 按钮通用 */
            QPushButton {{
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: 500;
                color: #334155;
            }}
            QPushButton:hover {{
                background-color: #E2E8F0;
                border-color: #94A3B8;
            }}
            QPushButton#btn_primary {{
                background-color: #0284C7;
                color: #FFFFFF;
                border: none;
                font-weight: bold;
                padding: 8px 22px;
            }}
            QPushButton#btn_primary:hover {{
                background-color: #0369A1;
            }}
            QPushButton#btn_test {{
                background-color: #059669;
                color: #FFFFFF;
                border: none;
                font-weight: bold;
                padding: 8px 18px;
            }}
            QPushButton#btn_test:hover {{
                background-color: #047857;
            }}
            /* 列表控件 */
            QListWidget {{
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                background-color: #F8FAFC;
                padding: 6px;
            }}
            QListWidget::item {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 6px 10px;
                margin-bottom: 4px;
                color: #1E293B;
                font-size: 13px;
            }}
            QListWidget::item:hover {{
                background-color: #F0F9FF;
                border-color: #7DD3FC;
            }}
            QListWidget::item:selected {{
                background-color: #E0F2FE;
                border: 1.5px solid #0284C7;
                color: #0369A1;
                font-weight: bold;
            }}
            /* 水平滑块 */
            QSlider::groove:horizontal {{
                height: 5px;
                background: #E2E8F0;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: #0284C7;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
                background: #FFFFFF;
                border: 2px solid #0284C7;
            }}
            /* 核心多选框 (精准白色对勾渲染) */
            QCheckBox {{
                font-size: 13px;
                color: #334155;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1.5px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
            }}
            QCheckBox::indicator:unchecked:hover {{
                border-color: #0284C7;
                background-color: #F0F9FF;
            }}
            QCheckBox::indicator:checked {{
                background-color: #0284C7;
                border: 1.5px solid #0284C7;
                image: url({check_svg_url});
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: #0369A1;
                border-color: #0369A1;
                image: url({check_svg_url});
            }}
            /* 工作日独立芯片多选框 */
            QCheckBox#DayCheckBox {{
                background-color: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
                font-size: 13px;
                color: #334155;
            }}
            QCheckBox#DayCheckBox:hover {{
                background-color: #F0F9FF;
                border-color: #38BDF8;
                color: #0284C7;
            }}
            QCheckBox#DayCheckBox:checked {{
                background-color: #F0F9FF;
                border-color: #0284C7;
                color: #0369A1;
            }}
        """)

        # 主水平布局：左侧导航 + 右侧内容
        main_h_layout = QHBoxLayout(self)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # 1. 左侧深色导航栏
        self.sidebar = QFrame()
        self.sidebar.setObjectName("SidebarFrame")
        self.sidebar.setFixedWidth(210)
        self._build_sidebar()
        main_h_layout.addWidget(self.sidebar)

        # 2. 右侧主体容器
        right_container = QWidget()
        right_v_layout = QVBoxLayout(right_container)
        right_v_layout.setContentsMargins(0, 0, 0, 0)
        right_v_layout.setSpacing(0)

        # 顶部标题栏
        self.header_bar = QFrame()
        self.header_bar.setObjectName("ContentHeader")
        self.header_bar.setFixedHeight(64)
        self._build_header_bar()
        right_v_layout.addWidget(self.header_bar)

        # 多页面堆叠区
        self.stack = QStackedWidget()
        self._build_page_overview()
        self._build_page_schedule()
        self._build_page_pet()
        self._build_page_popup()
        self._build_page_system()

        right_v_layout.addWidget(self.stack, 1)

        # 底部操作栏
        self.footer_bar = QFrame()
        self.footer_bar.setObjectName("FooterBar")
        self.footer_bar.setStyleSheet("QFrame#FooterBar { background-color: #FFFFFF; border-top: 1px solid #E2E8F0; }")
        self.footer_bar.setFixedHeight(60)
        self._build_footer_bar()
        right_v_layout.addWidget(self.footer_bar)

        main_h_layout.addWidget(right_container, 1)

    def _build_sidebar(self):
        """构建侧边栏导航"""
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(16, 20, 16, 18)
        layout.setSpacing(12)

        # 顶部品牌标识
        brand_layout = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(create_app_icon(32).pixmap(32, 32))
        brand_layout.addWidget(icon_lbl)

        title_v_box = QVBoxLayout()
        title_v_box.setSpacing(2)
        lbl_title = QLabel("下班提醒助手")
        lbl_title.setObjectName("SidebarTitle")
        lbl_sub = QLabel("Work-Off Assistant")
        lbl_sub.setObjectName("SidebarSubtitle")
        title_v_box.addWidget(lbl_title)
        title_v_box.addWidget(lbl_sub)
        brand_layout.addLayout(title_v_box)
        brand_layout.addStretch()
        layout.addLayout(brand_layout)

        # 运行状态指示微标签 (含盾牌矢量图标)
        status_box = QHBoxLayout()
        status_box.setSpacing(6)
        lbl_shield = QLabel()
        lbl_shield.setPixmap(get_svg_pixmap("shield_check", "#38BDF8", size=14))
        lbl_badge = QLabel("常驻托盘守护中")
        lbl_badge.setObjectName("SidebarBadge")
        status_box.addWidget(lbl_shield)
        status_box.addWidget(lbl_badge)
        status_box.addStretch()
        layout.addLayout(status_box)

        layout.addSpacing(10)

        # 导航按钮组 (全面嵌入矢量 SVG 图标)
        self.nav_btn_group = QButtonGroup(self)
        self.nav_btn_group.setExclusive(True)

        nav_items = [
            ("工作台概览", "nav_dashboard", 0),
            ("提醒时间与工作日", "nav_schedule", 1),
            ("桌面挂件装扮", "nav_pet", 2),
            ("全屏提醒视觉", "nav_popup", 3),
            ("系统与行为设置", "nav_system", 4)
        ]

        self.nav_buttons = []
        for name, icon_name, idx in nav_items:
            btn = QPushButton(f"  {name}")
            btn.setProperty("class", "NavButton")
            btn.setProperty("icon_name", icon_name)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # 初始图标：索引 0 高亮 sky blue，其余 slate
            c = "#38BDF8" if idx == 0 else "#94A3B8"
            btn.setIcon(get_svg_icon(icon_name, c, size=18))
            btn.setIconSize(QSize(18, 18))

            if idx == 0:
                btn.setChecked(True)

            btn.clicked.connect(lambda checked, i=idx: self._on_nav_clicked(i))
            self.nav_btn_group.addButton(btn, idx)
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        # 底部信息卡片
        self.mini_card = QFrame()
        self.mini_card.setObjectName("SidebarMiniCard")
        mc_layout = QVBoxLayout(self.mini_card)
        mc_layout.setContentsMargins(10, 10, 10, 10)
        mc_layout.setSpacing(4)

        mc_title = QLabel("今日下班目标")
        mc_title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
        self.mc_target_val = QLabel("18:30 (计算中...)")
        self.mc_target_val.setStyleSheet("color: #38BDF8; font-size: 13px; font-weight: bold;")
        self.mc_weather_val = QLabel("南京浦口·晴")
        self.mc_weather_val.setStyleSheet("color: #CBD5E1; font-size: 11px;")

        mc_layout.addWidget(mc_title)
        mc_layout.addWidget(self.mc_target_val)
        mc_layout.addWidget(self.mc_weather_val)

        layout.addWidget(self.mini_card)

    def _build_header_bar(self):
        """构建内容区顶部标题栏"""
        layout = QHBoxLayout(self.header_bar)
        layout.setContentsMargins(24, 0, 24, 0)

        title_v = QVBoxLayout()
        title_v.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title_v.setSpacing(2)
        self.lbl_head_title = QLabel("工作台概览")
        self.lbl_head_title.setObjectName("HeaderTitle")
        self.lbl_head_sub = QLabel("查看今日下班倒计时、日程安排与实时环境概览")
        self.lbl_head_sub.setObjectName("HeaderSubtitle")
        title_v.addWidget(self.lbl_head_title)
        title_v.addWidget(self.lbl_head_sub)
        layout.addLayout(title_v)

        layout.addStretch()

    def _build_footer_bar(self):
        """构建底部操作栏"""
        layout = QHBoxLayout(self.footer_bar)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(12)

        self.btn_reset = QPushButton(" 恢复默认")
        self.btn_reset.setIcon(get_svg_icon("reset_undo", "#64748B", size=16))
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.clicked.connect(self._on_reset_clicked)
        layout.addWidget(self.btn_reset)

        layout.addStretch()

        # 立即测试全屏弹窗
        self.btn_test = QPushButton(" 立即全屏测试")
        self.btn_test.setObjectName("btn_test")
        self.btn_test.setIcon(get_svg_icon("test_play", "#FFFFFF", size=15))
        self.btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test.clicked.connect(self._on_test_clicked)
        layout.addWidget(self.btn_test)

        self.btn_cancel = QPushButton(" 取消")
        self.btn_cancel.setIcon(get_svg_icon("close_x", "#64748B", size=14))
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton(" 保存并应用")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.setIcon(get_svg_icon("check", "#FFFFFF", size=16))
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._on_save_clicked)
        layout.addWidget(self.btn_save)

    def _on_nav_clicked(self, index: int):
        """切换左侧导航页面并实时刷新导航矢量图标色彩"""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            is_active = (i == index)
            btn.setChecked(is_active)
            icon_name = btn.property("icon_name")
            if icon_name:
                c = "#38BDF8" if is_active else "#94A3B8"
                btn.setIcon(get_svg_icon(icon_name, c, size=18))

        titles = [
            ("工作台概览", "今日下班倒计时、日程安排与实时环境概览"),
            ("提醒时间与工作日", "配置下班提醒时间点与工作日自动生效规则"),
            ("桌面挂件装扮", "个性化配置桌面猫咪挂件的 8 大时段装扮与交互位置"),
            ("全屏提醒视觉", "定制到达下班时间时的全屏沉浸提示弹窗风格"),
            ("系统与行为设置", "配置 Windows 开机自启、稍后提醒与系统交互")
        ]
        if 0 <= index < len(titles):
            t, sub = titles[index]
            self.lbl_head_title.setText(t)
            self.lbl_head_sub.setText(sub)

    # ==================== PAGE 0: 工作台概览 ====================

    def _build_page_overview(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 1. 倒计时沉浸大卡片
        hero_card = QFrame()
        hero_card.setObjectName("HeroCard")
        hero_card.setStyleSheet("""
            QFrame#HeroCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E293B, stop:1 #0F172A);
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        hc_layout = QVBoxLayout(hero_card)
        hc_layout.setContentsMargins(20, 18, 20, 18)
        hc_layout.setSpacing(10)

        top_row = QHBoxLayout()
        self.lbl_overview_target = QLabel("目标下班时间: 18:30")
        self.lbl_overview_target.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: 500; background: transparent;")
        top_row.addWidget(self.lbl_overview_target)
        top_row.addStretch()

        self.lbl_hero_sub = QLabel("正在计算下班时间...")
        self.lbl_hero_sub.setStyleSheet("color: #FBBF24; font-size: 12px; font-weight: bold; background: transparent;")
        top_row.addWidget(self.lbl_hero_sub)
        hc_layout.addLayout(top_row)

        self.lbl_hero_cd = QLabel("00:00:00")
        self.lbl_hero_cd.setStyleSheet("""
            color: #FFFFFF;
            font-family: 'Arial', 'Segoe UI', sans-serif;
            font-size: 42px;
            font-weight: bold;
            letter-spacing: 2px;
            background: transparent;
        """)
        hc_layout.addWidget(self.lbl_hero_cd)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        self.hero_progress_bar = QProgressBar()
        self.hero_progress_bar.setFixedHeight(8)
        self.hero_progress_bar.setRange(0, 100)
        self.hero_progress_bar.setValue(60)
        self.hero_progress_bar.setTextVisible(False)
        self.hero_progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #334155;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38BDF8, stop:1 #34D399);
                border-radius: 4px;
            }
        """)
        bottom_row.addWidget(self.hero_progress_bar, 1)

        self.lbl_hero_pct = QLabel("0%")
        self.lbl_hero_pct.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold; background: transparent;")
        bottom_row.addWidget(self.lbl_hero_pct)
        hc_layout.addLayout(bottom_row)

        layout.addWidget(hero_card)

        # 2. 状态信息三列卡片网格
        grid_row = QHBoxLayout()
        grid_row.setSpacing(14)

        # 卡片 1: 今日提醒安排
        card1 = self._create_info_card("今日提醒安排", "已配置的下班提醒时间点", "nav_schedule")
        c1_layout = card1.layout()
        self.lbl_c1_content = QLabel("18:00")
        self.lbl_c1_content.setStyleSheet("color: #0F172A; font-size: 14px; font-weight: bold; padding: 6px 0;")
        c1_layout.addWidget(self.lbl_c1_content)
        btn_c1_edit = QPushButton(" 管理时间点")
        btn_c1_edit.setIcon(get_svg_icon("nav_schedule", "#334155", size=14))
        btn_c1_edit.clicked.connect(lambda: self._on_nav_clicked(1))
        c1_layout.addWidget(btn_c1_edit)
        grid_row.addWidget(card1)

        # 卡片 2: 环境与装扮感知
        card2 = self._create_info_card("环境与装扮感知", "南京浦口区实时气象与形态", "theme_morning")
        c2_layout = card2.layout()
        self.lbl_c2_content = QLabel("浦口·晴 25℃")
        self.lbl_c2_content.setStyleSheet("color: #0F172A; font-size: 14px; font-weight: bold; padding: 6px 0;")
        c2_layout.addWidget(self.lbl_c2_content)
        btn_c2_theme = QPushButton(" 切换装扮形态")
        btn_c2_theme.setIcon(get_svg_icon("nav_pet", "#334155", size=14))
        btn_c2_theme.clicked.connect(lambda: self._on_nav_clicked(2))
        c2_layout.addWidget(btn_c2_theme)
        grid_row.addWidget(card2)

        # 卡片 3: 桌面挂件常驻状态
        card3 = self._create_info_card("桌面挂件状态", "常驻桌面与交互记忆", "nav_pet")
        c3_layout = card3.layout()
        self.lbl_c3_content = QLabel("常驻显示 · 始终置顶")
        self.lbl_c3_content.setStyleSheet("color: #0F172A; font-size: 14px; font-weight: bold; padding: 6px 0;")
        c3_layout.addWidget(self.lbl_c3_content)
        btn_c3_reset = QPushButton(" 恢复右下角位置")
        btn_c3_reset.setIcon(get_svg_icon("reset_undo", "#334155", size=14))
        btn_c3_reset.clicked.connect(self._reset_pet_position)
        c3_layout.addWidget(btn_c3_reset)
        grid_row.addWidget(card3)

        layout.addLayout(grid_row)
        layout.addStretch()

        self.stack.addWidget(page)

    def _create_info_card(self, title: str, subtitle: str, icon_name: str = None) -> QFrame:
        """快速构建白色圆角功能卡片"""
        card = QFrame()
        card.setProperty("class", "SectionCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 16, 16, 16)
        c_layout.setSpacing(6)

        header_box = QHBoxLayout()
        header_box.setSpacing(8)
        if icon_name:
            ic_lbl = QLabel()
            ic_lbl.setPixmap(get_svg_pixmap(icon_name, "#0284C7", size=16))
            header_box.addWidget(ic_lbl)

        t_lbl = QLabel(title)
        t_lbl.setProperty("class", "CardHeaderTitle")
        header_box.addWidget(t_lbl)
        header_box.addStretch()
        c_layout.addLayout(header_box)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setProperty("class", "CardHeaderSub")
        c_layout.addWidget(sub_lbl)

        return card

    def _refresh_overview_live(self):
        """实时刷新概览页与侧边栏"""
        if self.scheduler:
            data = self.scheduler.get_pet_status()
            cd_str = data.get("time_str", "00:00:00")
            sub_str = data.get("sub_text", "")
            prog = float(data.get("progress", 0.0))
            tgt = data.get("target_time", "")

            self.lbl_hero_cd.setText(cd_str)
            self.hero_progress_bar.setValue(int(prog * 100))
            self.lbl_hero_pct.setText(f"{int(prog * 100)}%")

            if tgt:
                self.lbl_overview_target.setText(f"目标下班时间: {tgt}")
                self.lbl_hero_sub.setText(f"{sub_str}，专注收尾中")
                self.mc_target_val.setText(f"{tgt} ({sub_str})")
            else:
                self.lbl_overview_target.setText("下班时间已过")
                self.lbl_hero_sub.setText("享受美好个人时间")
                self.mc_target_val.setText("已下班")

        # 天气文本
        w_text = "南京浦口·晴 25℃"
        if self.weather_service and self.weather_service.cached_weather:
            w = self.weather_service.cached_weather
            w_text = f"南京浦口·{w.get('type', '晴')} {w.get('temp', '25℃')}"

        self.lbl_c2_content.setText(w_text)
        self.mc_weather_val.setText(w_text)

    # ==================== PAGE 1: 提醒时间与工作日 ====================

    def _build_page_schedule(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 1. 提醒时间点管理卡片
        card_times = QFrame()
        card_times.setProperty("class", "SectionCard")
        ct_layout = QVBoxLayout(card_times)
        ct_layout.setContentsMargins(18, 18, 18, 18)
        ct_layout.setSpacing(12)

        ct_title = QLabel("下班提醒时间管理 (支持设置多个时间点)")
        ct_title.setProperty("class", "CardHeaderTitle")
        ct_sub = QLabel("可在一天中设置多个提醒点，例如：17:55 提前整理工位，18:00 准时打卡下班。")
        ct_sub.setProperty("class", "CardHeaderSub")
        ct_layout.addWidget(ct_title)
        ct_layout.addWidget(ct_sub)

        # 快捷常用时间点芯片栏
        quick_chips_box = QHBoxLayout()
        quick_chips_box.setSpacing(8)
        lbl_chip_tip = QLabel("常用快捷时间：")
        lbl_chip_tip.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500;")
        quick_chips_box.addWidget(lbl_chip_tip)

        common_presets = ["17:30", "18:00", "18:30", "19:00", "20:00"]
        for p_time in common_presets:
            chip_btn = QPushButton(f"＋ {p_time}")
            chip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            chip_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    border: 1px dashed #CBD5E1;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 12px;
                    font-weight: 600;
                    color: #475569;
                }
                QPushButton:hover {
                    background-color: #F0F9FF;
                    border-color: #0284C7;
                    color: #0284C7;
                }
            """)
            chip_btn.clicked.connect(lambda checked, t_val=p_time: self._add_reminder_time(t_val))
            quick_chips_box.addWidget(chip_btn)

        quick_chips_box.addStretch()
        ct_layout.addLayout(quick_chips_box)

        # 自定义时间选择行
        add_row = QHBoxLayout()
        add_row.setSpacing(10)
        add_row.addWidget(QLabel("自定义时间点："))
        self.time_picker = QTimeEdit()
        self.time_picker.setDisplayFormat("HH:mm")
        self.time_picker.setTime(QTime(18, 0))
        self.time_picker.setFixedWidth(100)
        add_row.addWidget(self.time_picker)

        self.btn_add_time = QPushButton(" ＋ 添加此时间点")
        self.btn_add_time.setIcon(get_svg_icon("add_plus", "#0284C7", size=16))
        self.btn_add_time.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_time.clicked.connect(lambda: self._add_reminder_time(None))
        add_row.addWidget(self.btn_add_time)

        self.btn_del_time = QPushButton(" － 删除选中项")
        self.btn_del_time.setIcon(get_svg_icon("delete_trash", "#64748B", size=15))
        self.btn_del_time.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del_time.clicked.connect(self._del_reminder_time)
        add_row.addWidget(self.btn_del_time)

        add_row.addStretch()
        ct_layout.addLayout(add_row)

        # 时间列表容器与精美列表
        self.list_times = QListWidget()
        self.list_times.setMaximumHeight(135)
        self.list_times.itemDoubleClicked.connect(self._del_reminder_time)
        ct_layout.addWidget(self.list_times)
        layout.addWidget(card_times)

        # 2. 工作日筛选卡片 (对勾多选框)
        card_days = QFrame()
        card_days.setProperty("class", "SectionCard")
        cd_layout = QVBoxLayout(card_days)
        cd_layout.setContentsMargins(18, 18, 18, 18)
        cd_layout.setSpacing(14)

        cd_title = QLabel("工作日生效筛选")
        cd_title.setProperty("class", "CardHeaderTitle")
        cd_sub = QLabel("仅在勾选的工作日触发提醒，非工作日挂件将显示休息状态。")
        cd_sub.setProperty("class", "CardHeaderSub")
        cd_layout.addWidget(cd_title)
        cd_layout.addWidget(cd_sub)

        # 快速预设按钮行
        quick_row = QHBoxLayout()
        quick_row.setSpacing(10)
        quick_row.addWidget(QLabel("快速预设："))

        btn_workdays = QPushButton(" 标准工作日 (周一至周五)")
        btn_workdays.setIcon(get_svg_icon("briefcase", "#0284C7", size=16))
        btn_workdays.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_workdays.clicked.connect(lambda: self._set_weekdays_selected([0, 1, 2, 3, 4]))
        quick_row.addWidget(btn_workdays)

        btn_all = QPushButton(" 全天候 (周一至周日)")
        btn_all.setIcon(get_svg_icon("calendar", "#0284C7", size=16))
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(lambda: self._set_weekdays_selected([0, 1, 2, 3, 4, 5, 6]))
        quick_row.addWidget(btn_all)

        btn_weekends = QPushButton(" 仅周末 (周六与周日)")
        btn_weekends.setIcon(get_svg_icon("coffee", "#0284C7", size=16))
        btn_weekends.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_weekends.clicked.connect(lambda: self._set_weekdays_selected([5, 6]))
        quick_row.addWidget(btn_weekends)

        quick_row.addStretch()
        cd_layout.addLayout(quick_row)

        # 7 天独立选择芯片 (每个均带对勾视觉反馈)
        days_box = QHBoxLayout()
        days_box.setSpacing(10)
        self.day_checkboxes = []
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for idx, name in enumerate(day_names):
            cb = QCheckBox(name)
            cb.setObjectName("DayCheckBox")
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            self.day_checkboxes.append(cb)
            days_box.addWidget(cb)
        days_box.addStretch()
        cd_layout.addLayout(days_box)

        layout.addWidget(card_days)
        layout.addStretch()

        self.stack.addWidget(page)

    def _add_time_item_to_list(self, t_str: str):
        """向时间列表添加具备矢量时钟图标与精致格式的列表项"""
        item = QListWidgetItem()
        item.setText(f"  {t_str}    (下班打卡提醒点)")
        item.setData(Qt.ItemDataRole.UserRole, t_str)
        item.setIcon(get_svg_icon("clock", "#0284C7", size=16))
        item.setSizeHint(QSize(100, 36))
        font = QFont("Microsoft YaHei", 10)
        font.setBold(True)
        item.setFont(font)
        self.list_times.addItem(item)

    def _add_reminder_time(self, custom_time_str=None):
        """添加提醒时间点"""
        t_str = custom_time_str if custom_time_str else self.time_picker.time().toString("HH:mm")
        existing = [
            self.list_times.item(i).data(Qt.ItemDataRole.UserRole) or 
            self.list_times.item(i).text().strip().split()[0] 
            for i in range(self.list_times.count())
        ]
        if t_str in existing:
            QMessageBox.information(self, "提示", f"时间点 {t_str} 已经存在了。")
            return
        existing.append(t_str)
        existing.sort()
        self.list_times.clear()
        for t in existing:
            self._add_time_item_to_list(t)
        if hasattr(self, "lbl_c1_content"):
            self.lbl_c1_content.setText(" · ".join(existing) if existing else "未配置")

    def _del_reminder_time(self):
        """删除当前选中的时间点"""
        row = self.list_times.currentRow()
        if row >= 0:
            self.list_times.takeItem(row)
            existing = [
                self.list_times.item(i).data(Qt.ItemDataRole.UserRole) or 
                self.list_times.item(i).text().strip().split()[0] 
                for i in range(self.list_times.count())
            ]
            if hasattr(self, "lbl_c1_content"):
                self.lbl_c1_content.setText(" · ".join(existing) if existing else "未配置")
        else:
            QMessageBox.information(self, "提示", "请先在列表中选中要删除的时间点。")

    def _set_weekdays_selected(self, day_indices):
        """快速批量设定工作日勾选状态"""
        for idx, cb in enumerate(self.day_checkboxes):
            cb.setChecked(idx in day_indices)

    # ==================== PAGE 2: 桌面挂件装扮 ====================

    def _build_page_pet(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 1. 挂件 8 大时段装扮选择器卡片
        card_themes = QFrame()
        card_themes.setProperty("class", "SectionCard")
        ct_layout = QVBoxLayout(card_themes)
        ct_layout.setContentsMargins(18, 18, 18, 18)
        ct_layout.setSpacing(12)

        ct_title = QLabel("桌面猫咪挂件装扮形态")
        ct_title.setProperty("class", "CardHeaderTitle")
        ct_sub = QLabel("根据南京浦口实时天气与不同作息时段自动感知切换，也可强制锁定为心仪装扮。")
        ct_sub.setProperty("class", "CardHeaderSub")
        ct_layout.addWidget(ct_title)
        ct_layout.addWidget(ct_sub)

        # 9 个卡片 2 列网格布局 (嵌入专属矢量装扮图标)
        self.theme_btn_group = QButtonGroup(self)
        self.theme_btn_group.setExclusive(True)

        theme_options = [
            ("auto", "自动感知环境 (推荐)", "随时间、温度与天气全自动动态切换", "theme_auto"),
            ("morning", "晨间咖啡 (06:00 - 11:00)", "小猫配香浓咖啡，元气满满一整天", "theme_morning"),
            ("noon", "午间打盹 (11:00 - 14:00)", "微闭双眼呼噜泡泡，小憩片刻", "theme_noon"),
            ("afternoon", "午后期待 (14:00 - 18:00)", "小木钟渴望下班，冲刺收尾", "theme_afternoon"),
            ("evening", "晚间拉旗 (18:00 - 23:00)", "七彩拉旗庆祝，下班美好时光", "theme_evening"),
            ("night", "深夜睡帽 (23:00 - 06:00)", "蓝底波点睡帽 + 月牙星星", "theme_night"),
            ("rain", "荷叶雨伞 (雨天/雷雨)", "头顶绿荷叶避雨，温馨提醒带伞", "theme_rain"),
            ("cold", "围巾积雪 (降雪/寒冷)", "红色毛线围巾 + 木牌上下积雪", "theme_cold"),
            ("hot", "切块西瓜 (高温酷暑)", "大块切片西瓜解渴降温", "theme_hot")
        ]

        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(10)

        self.theme_radio_buttons = {}
        for idx, (key, name, desc, icon_name) in enumerate(theme_options):
            btn = QPushButton(f"  {name}\n    {desc}")
            btn.setIcon(get_svg_icon(icon_name, "#0284C7", size=22))
            btn.setIconSize(QSize(22, 22))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    padding: 10px 14px;
                    text-align: left;
                    font-size: 12px;
                    color: #334155;
                    line-height: 1.4;
                }
                QPushButton:hover {
                    background-color: #F1F5F9;
                    border-color: #CBD5E1;
                }
                QPushButton:checked {
                    background-color: #EFF6FF;
                    border: 2px solid #0284C7;
                    color: #0369A1;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self._on_pet_theme_selected(k))
            self.theme_btn_group.addButton(btn)
            self.theme_radio_buttons[key] = btn
            r, c = divmod(idx, 2)
            grid_layout.addWidget(btn, r, c)

        ct_layout.addWidget(grid_container)
        layout.addWidget(card_themes)

        # 2. 挂件行为与参数卡片 (对勾复选框)
        card_params = QFrame()
        card_params.setProperty("class", "SectionCard")
        cp_layout = QVBoxLayout(card_params)
        cp_layout.setContentsMargins(18, 18, 18, 18)
        cp_layout.setSpacing(14)

        cp_title = QLabel("挂件显示与交互参数")
        cp_title.setProperty("class", "CardHeaderTitle")
        cp_layout.addWidget(cp_title)

        self.cb_show_pet = QCheckBox("在桌面常驻显示下班倒计时挂件")
        cp_layout.addWidget(self.cb_show_pet)

        self.cb_pet_locked = QCheckBox("锁定挂件位置 (禁止鼠标误拖动)")
        cp_layout.addWidget(self.cb_pet_locked)

        # 不透明度滑块
        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("挂件不透明度："))
        self.slider_pet_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_pet_opacity.setRange(40, 100)
        self.slider_pet_opacity.setValue(95)
        self.lbl_pet_op_val = QLabel("95%")
        self.lbl_pet_op_val.setFixedWidth(40)
        self.slider_pet_opacity.valueChanged.connect(lambda val: self.lbl_pet_op_val.setText(f"{val}%"))
        op_row.addWidget(self.slider_pet_opacity)
        op_row.addWidget(self.lbl_pet_op_val)
        cp_layout.addLayout(op_row)

        btn_reset_pos = QPushButton(" 重置挂件位置到屏幕右下角")
        btn_reset_pos.setIcon(get_svg_icon("reset_undo", "#334155", size=15))
        btn_reset_pos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset_pos.clicked.connect(self._reset_pet_position)
        cp_layout.addWidget(btn_reset_pos)

        layout.addWidget(card_params)
        layout.addStretch()

        scroll.setWidget(container)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        self.stack.addWidget(page)

    def _on_pet_theme_selected(self, theme_key: str):
        self.selected_pet_theme = theme_key

    def _reset_pet_position(self):
        """恢复挂件到屏幕右下角"""
        screen = QApplication.primaryScreen().availableGeometry()
        w, h = 260, 212
        target_x = screen.width() - w - 30
        target_y = screen.height() - h - 40
        self.config_mgr.set("pet_pos_x", target_x)
        self.config_mgr.set("pet_pos_y", target_y)
        self.config_mgr.save()
        QMessageBox.information(self, "位置重置", "挂件已恢复至屏幕右下角默认位置。")

    # ==================== PAGE 3: 全屏提醒视觉 ====================

    def _build_page_popup(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 1. 文案定制卡片
        card_text = QFrame()
        card_text.setProperty("class", "SectionCard")
        ctx_layout = QVBoxLayout(card_text)
        ctx_layout.setContentsMargins(18, 18, 18, 18)
        ctx_layout.setSpacing(12)

        ctx_title = QLabel("提示文案内容")
        ctx_title.setProperty("class", "CardHeaderTitle")
        ctx_layout.addWidget(ctx_title)

        ctx_layout.addWidget(QLabel("主标题内容："))
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("例如：今日下班时间到啦！")
        ctx_layout.addWidget(self.edit_title)

        ctx_layout.addWidget(QLabel("副标题 / 温馨提醒详细内容："))
        self.edit_subtitle = QTextEdit()
        self.edit_subtitle.setMaximumHeight(70)
        self.edit_subtitle.setPlaceholderText("例如：辛苦了一整天，请记得保存工作、打卡下班...")
        ctx_layout.addWidget(self.edit_subtitle)

        self.cb_show_clock = QCheckBox("在全屏弹窗中展示当前实时大时钟")
        ctx_layout.addWidget(self.cb_show_clock)

        layout.addWidget(card_text)

        # 2. 字体与色彩卡片
        card_font = QFrame()
        card_font.setProperty("class", "SectionCard")
        cf_layout = QVBoxLayout(card_font)
        cf_layout.setContentsMargins(18, 18, 18, 18)
        cf_layout.setSpacing(12)

        cf_title = QLabel("字体与颜色自定义")
        cf_title.setProperty("class", "CardHeaderTitle")
        cf_layout.addWidget(cf_title)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("字体选择："))
        self.cb_font_family = QComboBox()
        self.cb_font_family.addItems(["Microsoft YaHei", "SimHei", "KaiTi", "Segoe UI", "Arial", "Impact"])
        font_row.addWidget(self.cb_font_family)
        font_row.addStretch()
        cf_layout.addLayout(font_row)

        # 主标题大小与颜色
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("主标题字号："))
        self.spin_title_size = QSpinBox()
        self.spin_title_size.setRange(20, 72)
        row1.addWidget(self.spin_title_size)

        row1.addWidget(QLabel("主标题颜色："))
        self.btn_title_color = QPushButton("选择颜色")
        self.btn_title_color.clicked.connect(lambda: self._choose_color("title"))
        row1.addWidget(self.btn_title_color)
        row1.addStretch()
        cf_layout.addLayout(row1)

        # 副标题字号与颜色
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("副标题字号："))
        self.spin_subtitle_size = QSpinBox()
        self.spin_subtitle_size.setRange(12, 36)
        row2.addWidget(self.spin_subtitle_size)

        row2.addWidget(QLabel("副标题颜色："))
        self.btn_subtitle_color = QPushButton("选择颜色")
        self.btn_subtitle_color.clicked.connect(lambda: self._choose_color("subtitle"))
        row2.addWidget(self.btn_subtitle_color)
        row2.addStretch()
        cf_layout.addLayout(row2)

        # 时钟颜色
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("实时时钟颜色："))
        self.btn_clock_color = QPushButton("选择颜色")
        self.btn_clock_color.clicked.connect(lambda: self._choose_color("clock"))
        row3.addWidget(self.btn_clock_color)
        row3.addStretch()
        cf_layout.addLayout(row3)

        layout.addWidget(card_font)

        # 3. 背景与遮罩样式卡片
        card_bg = QFrame()
        card_bg.setProperty("class", "SectionCard")
        cbg_layout = QVBoxLayout(card_bg)
        cbg_layout.setContentsMargins(18, 18, 18, 18)
        cbg_layout.setSpacing(12)

        cbg_title = QLabel("背景渲染与遮罩视觉")
        cbg_title.setProperty("class", "CardHeaderTitle")
        cbg_layout.addWidget(cbg_title)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("背景渲染模式："))
        self.cb_bg_type = QComboBox()
        self.cb_bg_type.addItem("极简沉浸暗黑磨砂 (推荐)", "preset_dark")
        self.cb_bg_type.addItem("绚丽渐变色彩", "gradient")
        self.cb_bg_type.addItem("纯色背景", "color")
        self.cb_bg_type.addItem("自定义壁纸图片", "image")
        self.cb_bg_type.currentIndexChanged.connect(self._on_bg_type_changed)
        mode_row.addWidget(self.cb_bg_type)
        mode_row.addStretch()
        cbg_layout.addLayout(mode_row)

        # 渐变预设
        self.widget_gradient = QWidget()
        wg_layout = QHBoxLayout(self.widget_gradient)
        wg_layout.setContentsMargins(0, 0, 0, 0)
        wg_layout.addWidget(QLabel("渐变色彩方案："))
        self.cb_gradient_preset = QComboBox()
        for k, v in GRADIENT_PRESETS.items():
            self.cb_gradient_preset.addItem(f"{v['name']} ({v['desc']})", k)
        wg_layout.addWidget(self.cb_gradient_preset)
        wg_layout.addStretch()
        cbg_layout.addWidget(self.widget_gradient)

        # 纯色底色
        self.widget_color = QWidget()
        wc_layout = QHBoxLayout(self.widget_color)
        wc_layout.setContentsMargins(0, 0, 0, 0)
        wc_layout.addWidget(QLabel("纯色背景底色："))
        self.btn_bg_color = QPushButton("选择底色")
        self.btn_bg_color.clicked.connect(lambda: self._choose_color("bg"))
        wc_layout.addWidget(self.btn_bg_color)
        wc_layout.addStretch()
        cbg_layout.addWidget(self.widget_color)

        # 自定义图片
        self.widget_image = QWidget()
        wi_layout = QHBoxLayout(self.widget_image)
        wi_layout.setContentsMargins(0, 0, 0, 0)
        self.edit_image_path = QLineEdit()
        self.edit_image_path.setReadOnly(True)
        self.edit_image_path.setPlaceholderText("选择本地图片壁纸 (JPG, PNG, WebP)...")
        wi_layout.addWidget(self.edit_image_path)
        btn_browse = QPushButton("浏览...")
        btn_browse.clicked.connect(self._browse_image)
        wi_layout.addWidget(btn_browse)
        btn_clear = QPushButton("清除")
        btn_clear.clicked.connect(lambda: self.edit_image_path.clear())
        wi_layout.addWidget(btn_clear)
        cbg_layout.addWidget(self.widget_image)

        # 遮罩滑块
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("暗色遮罩浓度："))
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(20, 100)
        self.slider_opacity.setValue(85)
        self.lbl_opacity_val = QLabel("85%")
        self.slider_opacity.valueChanged.connect(lambda val: self.lbl_opacity_val.setText(f"{val}%"))
        slider_row.addWidget(self.slider_opacity)
        slider_row.addWidget(self.lbl_opacity_val)
        cbg_layout.addLayout(slider_row)

        layout.addWidget(card_bg)
        layout.addStretch()

        scroll.setWidget(container)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        self.stack.addWidget(page)

    # ==================== PAGE 4: 系统与行为设置 ====================

    def _build_page_system(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 1. 提醒行为卡片 (对勾复选框)
        card_bh = QFrame()
        card_bh.setProperty("class", "SectionCard")
        cbh_layout = QVBoxLayout(card_bh)
        cbh_layout.setContentsMargins(18, 18, 18, 18)
        cbh_layout.setSpacing(14)

        cbh_title = QLabel("提醒与交互行为")
        cbh_title.setProperty("class", "CardHeaderTitle")
        cbh_layout.addWidget(cbh_title)

        self.cb_sound = QCheckBox("全屏提醒触发时播放温馨提示音")
        cbh_layout.addWidget(self.cb_sound)

        snooze_row = QHBoxLayout()
        snooze_row.addWidget(QLabel("点击“稍后提醒”延后时长："))
        self.spin_snooze = QSpinBox()
        self.spin_snooze.setRange(1, 60)
        self.spin_snooze.setSuffix(" 分钟")
        snooze_row.addWidget(self.spin_snooze)
        snooze_row.addStretch()
        cbh_layout.addLayout(snooze_row)

        auto_close_row = QHBoxLayout()
        auto_close_row.addWidget(QLabel("弹窗无操作自动关闭时间："))
        self.spin_auto_close = QSpinBox()
        self.spin_auto_close.setRange(0, 300)
        self.spin_auto_close.setSpecialValueText("不自动关闭 (需手动点击)")
        self.spin_auto_close.setSuffix(" 秒")
        auto_close_row.addWidget(self.spin_auto_close)
        auto_close_row.addStretch()
        cbh_layout.addLayout(auto_close_row)

        layout.addWidget(card_bh)

        # 2. 系统开机与环境集成 (对勾复选框)
        card_sys = QFrame()
        card_sys.setProperty("class", "SectionCard")
        csys_layout = QVBoxLayout(card_sys)
        csys_layout.setContentsMargins(18, 18, 18, 18)
        csys_layout.setSpacing(14)

        csys_title = QLabel("系统与自启动")
        csys_title.setProperty("class", "CardHeaderTitle")
        csys_layout.addWidget(csys_title)

        self.cb_autostart = QCheckBox("Windows 开机自动在后台启动")
        csys_layout.addWidget(self.cb_autostart)

        tip_lbl = QLabel("开启自启动后，程序将在系统开机时静默入驻托盘与桌面右下角守护您的下班时间。")
        tip_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        tip_lbl.setWordWrap(True)
        csys_layout.addWidget(tip_lbl)

        layout.addWidget(card_sys)
        layout.addStretch()

        self.stack.addWidget(page)

    # --- 逻辑加载与存取 ---

    def load_from_config(self):
        """从当前配置载入所有控件状态"""
        cfg = self.config_mgr.config

        # 列表时间点
        self.list_times.clear()
        times = cfg.get("reminder_times", ["18:00"])
        for t in sorted(times):
            self._add_time_item_to_list(t)

        # 刷新概览卡片1内容
        if hasattr(self, "lbl_c1_content"):
            self.lbl_c1_content.setText(" · ".join(sorted(times)) if times else "未配置")

        # 工作日
        workdays = cfg.get("workdays", [0, 1, 2, 3, 4])
        for idx, cb in enumerate(self.day_checkboxes):
            cb.setChecked(idx in workdays)

        # 文案
        self.edit_title.setText(cfg.get("title_text", "今日下班时间到啦！"))
        self.edit_subtitle.setPlainText(cfg.get("subtitle_text", "辛苦了一整天，请记得保存工作、打卡下班，好好享受美好生活！"))
        self.cb_show_clock.setChecked(cfg.get("show_clock", True))

        # 字体
        font_idx = self.cb_font_family.findText(cfg.get("font_family", "Microsoft YaHei"))
        if font_idx >= 0:
            self.cb_font_family.setCurrentIndex(font_idx)
        self.spin_title_size.setValue(cfg.get("title_font_size", 50))
        self.spin_subtitle_size.setValue(cfg.get("subtitle_font_size", 20))

        # 颜色
        self.current_title_color = cfg.get("title_color", "#FFFFFF")
        self.current_subtitle_color = cfg.get("subtitle_color", "#E2E8F0")
        self.current_clock_color = cfg.get("clock_color", "#38BDF8")
        self.current_bg_color = cfg.get("background_color", "#0F172A")
        self._update_color_buttons()

        # 背景模式
        bg_type = cfg.get("background_type", "preset_dark")
        idx = self.cb_bg_type.findData(bg_type)
        if idx >= 0:
            self.cb_bg_type.setCurrentIndex(idx)
        self._on_bg_type_changed(idx)

        grad_preset = cfg.get("gradient_preset", "aurora")
        g_idx = self.cb_gradient_preset.findData(grad_preset)
        if g_idx >= 0:
            self.cb_gradient_preset.setCurrentIndex(g_idx)

        self.edit_image_path.setText(cfg.get("custom_image_path", ""))
        self.slider_opacity.setValue(int(cfg.get("overlay_opacity", 0.85) * 100))

        # 挂件设置
        self.cb_show_pet.setChecked(cfg.get("show_pet", True))
        self.cb_pet_locked.setChecked(cfg.get("pet_locked", False))
        self.slider_pet_opacity.setValue(int(cfg.get("pet_opacity", 0.95) * 100))

        theme = cfg.get("pet_override_theme", "auto")
        self.selected_pet_theme = theme
        if theme in self.theme_radio_buttons:
            self.theme_radio_buttons[theme].setChecked(True)

        # 系统与行为
        self.cb_sound.setChecked(cfg.get("enable_sound", True))
        self.spin_snooze.setValue(cfg.get("snooze_minutes", 5))
        self.spin_auto_close.setValue(cfg.get("auto_close_seconds", 0))

        # 开机自启
        self.cb_autostart.setChecked(is_autostart_enabled())

        self._refresh_overview_live()

    def _choose_color(self, target: str):
        init_color = QColor("#FFFFFF")
        if target == "title": init_color = QColor(self.current_title_color)
        elif target == "subtitle": init_color = QColor(self.current_subtitle_color)
        elif target == "clock": init_color = QColor(self.current_clock_color)
        elif target == "bg": init_color = QColor(self.current_bg_color)

        color = QColorDialog.getColor(init_color, self, "选择颜色")
        if color.isValid():
            hex_val = color.name().upper()
            if target == "title": self.current_title_color = hex_val
            elif target == "subtitle": self.current_subtitle_color = hex_val
            elif target == "clock": self.current_clock_color = hex_val
            elif target == "bg": self.current_bg_color = hex_val
            self._update_color_buttons()

    def _update_color_buttons(self):
        self.btn_title_color.setStyleSheet(f"background-color: {self.current_title_color}; color: {'#000' if QColor(self.current_title_color).lightness() > 128 else '#FFF'};")
        self.btn_subtitle_color.setStyleSheet(f"background-color: {self.current_subtitle_color}; color: {'#000' if QColor(self.current_subtitle_color).lightness() > 128 else '#FFF'};")
        self.btn_clock_color.setStyleSheet(f"background-color: {self.current_clock_color}; color: {'#000' if QColor(self.current_clock_color).lightness() > 128 else '#FFF'};")
        self.btn_bg_color.setStyleSheet(f"background-color: {self.current_bg_color}; color: {'#000' if QColor(self.current_bg_color).lightness() > 128 else '#FFF'};")

    def _on_bg_type_changed(self, index: int):
        bg_type = self.cb_bg_type.currentData()
        self.widget_gradient.setVisible(bg_type == "gradient")
        self.widget_color.setVisible(bg_type == "color")
        self.widget_image.setVisible(bg_type == "image")

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择壁纸图片", "", "图片文件 (*.jpg *.jpeg *.png *.webp)"
        )
        if path:
            self.edit_image_path.setText(os.path.normpath(path))

    def _on_save_clicked(self):
        """保存配置到磁盘"""
        cfg = self.config_mgr.config

        # 时间列表 (提取纯时间字符串)
        times = []
        for i in range(self.list_times.count()):
            it = self.list_times.item(i)
            t_val = it.data(Qt.ItemDataRole.UserRole)
            if not t_val:
                t_val = it.text().strip().split()[0]
            if t_val:
                times.append(t_val)

        if not times:
            QMessageBox.warning(self, "提示", "请至少设置一个下班提醒时间点。")
            return
        cfg["reminder_times"] = sorted(times)

        # 工作日
        cfg["workdays"] = [idx for idx, cb in enumerate(self.day_checkboxes) if cb.isChecked()]

        # 文案
        cfg["title_text"] = self.edit_title.text().strip() or "今日下班时间到啦！"
        cfg["subtitle_text"] = self.edit_subtitle.toPlainText().strip()
        cfg["show_clock"] = self.cb_show_clock.isChecked()

        # 字体
        cfg["font_family"] = self.cb_font_family.currentText()
        cfg["title_font_size"] = self.spin_title_size.value()
        cfg["subtitle_font_size"] = self.spin_subtitle_size.value()

        # 颜色
        cfg["title_color"] = self.current_title_color
        cfg["subtitle_color"] = self.current_subtitle_color
        cfg["clock_color"] = self.current_clock_color
        cfg["background_color"] = self.current_bg_color

        # 背景模式
        cfg["background_type"] = self.cb_bg_type.currentData()
        cfg["gradient_preset"] = self.cb_gradient_preset.currentData()
        cfg["custom_image_path"] = self.edit_image_path.text().strip()
        cfg["overlay_opacity"] = self.slider_opacity.value() / 100.0

        # 挂件设置
        cfg["show_pet"] = self.cb_show_pet.isChecked()
        cfg["pet_locked"] = self.cb_pet_locked.isChecked()
        cfg["pet_opacity"] = self.slider_pet_opacity.value() / 100.0
        cfg["pet_override_theme"] = self.selected_pet_theme

        # 系统与行为
        cfg["enable_sound"] = self.cb_sound.isChecked()
        cfg["snooze_minutes"] = self.spin_snooze.value()
        cfg["auto_close_seconds"] = self.spin_auto_close.value()

        # 自启动
        autostart_enabled = self.cb_autostart.isChecked()
        cfg["autostart"] = autostart_enabled
        set_autostart(autostart_enabled)

        self.config_mgr.save()
        self.config_saved.emit()

        QMessageBox.information(self, "保存成功", "所有个性化设置已成功保存并立即生效。")
        self.accept()

    def _on_test_clicked(self):
        """触发全屏预览"""
        self.test_requested.emit()

    def _on_reset_clicked(self):
        """恢复默认设置"""
        ret = QMessageBox.question(
            self, "确认恢复默认",
            "是否确定恢复全部设置项到初始默认状态？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.config_mgr.reset_to_default()
            self.load_from_config()
            self.config_saved.emit()
            QMessageBox.information(self, "已恢复默认", "所有设置已恢复到默认初始状态。")

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_overview_live()
        if not self.overview_timer.isActive():
            self.overview_timer.start(1000)

    def hideEvent(self, event):
        super().hideEvent(event)
        if self.overview_timer.isActive():
            self.overview_timer.stop()
