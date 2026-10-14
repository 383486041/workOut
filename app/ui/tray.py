# -*- coding: utf-8 -*-
"""
系统托盘管理模块
负责托盘图标显示、右键菜单交互、下次提醒时间 Tooltip 动态更新以及开机自启快捷切换
"""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from app.ui.assets import create_app_icon
from app.autostart import is_autostart_enabled, set_autostart

class TrayManager(QObject):
    """托盘图标与交互管理"""
    open_settings_requested = pyqtSignal()
    test_popup_requested = pyqtSignal()
    toggle_pet_requested = pyqtSignal(bool)
    exit_requested = pyqtSignal()

    def __init__(self, config_manager, scheduler, parent=None):
        super().__init__(parent)
        self.config_mgr = config_manager
        self.scheduler = scheduler

        self.tray_icon = QSystemTrayIcon(parent)
        self.tray_icon.setIcon(create_app_icon(32))

        # 定时更新 Tooltip (每 30 秒更新一次下次提醒时间状态)
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.timeout.connect(self.update_tooltip)
        self.tooltip_timer.start(30000)

        self._init_menu()
        self.update_tooltip()

        # 托盘点击事件：左键单双击打开设置
        self.tray_icon.activated.connect(self._on_tray_activated)

    def show(self):
        self.tray_icon.show()

    def update_tooltip(self):
        """动态更新托盘鼠标悬浮提示"""
        desc = self.scheduler.get_next_reminder_desc()
        self.tray_icon.setToolTip(f"下班提醒助手\n{desc}")

    def show_message(self, title: str, message: str):
        """显示系统气泡通知"""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    def _init_menu(self):
        """初始化托盘右键菜单"""
        self.menu = QMenu()

        # 1. 打开设置
        action_settings = QAction("打开设置中心", self.menu)
        action_settings.triggered.connect(self.open_settings_requested.emit)
        self.menu.addAction(action_settings)

        # 2. 立即测试全屏弹窗
        action_test = QAction("立即测试全屏提醒", self.menu)
        action_test.triggered.connect(self.test_popup_requested.emit)
        self.menu.addAction(action_test)

        # 3. 桌面挂件开关
        self.action_pet = QAction("显示桌面倒计时挂件", self.menu)
        self.action_pet.setCheckable(True)
        self.action_pet.setChecked(self.config_mgr.get("show_pet", True))
        self.action_pet.triggered.connect(self._on_pet_toggled)
        self.menu.addAction(self.action_pet)

        self.menu.addSeparator()

        # 4. 暂停/恢复提醒
        self.action_pause = QAction("暂停今天提醒", self.menu)
        self.action_pause.setCheckable(True)
        self.action_pause.setChecked(False)
        self.action_pause.triggered.connect(self._on_pause_toggled)
        self.menu.addAction(self.action_pause)

        # 5. 开机自启动
        self.action_autostart = QAction("开机自启动", self.menu)
        self.action_autostart.setCheckable(True)
        self.action_autostart.setChecked(is_autostart_enabled())
        self.action_autostart.triggered.connect(self._on_autostart_toggled)
        self.menu.addAction(self.action_autostart)

        self.menu.addSeparator()

        # 5. 关于
        action_about = QAction("关于软件", self.menu)
        action_about.triggered.connect(self._show_about)
        self.menu.addAction(action_about)

        # 6. 退出
        action_exit = QAction("退出程序", self.menu)
        action_exit.triggered.connect(self.exit_requested.emit)
        self.menu.addAction(action_exit)

        self.tray_icon.setContextMenu(self.menu)

    def sync_autostart_checkbox(self):
        """同步开机自启勾选状态"""
        self.action_autostart.setChecked(is_autostart_enabled())

    def sync_pet_checkbox(self):
        """同步桌宠挂件勾选状态"""
        self.action_pet.setChecked(self.config_mgr.get("show_pet", True))

    def _on_pet_toggled(self, checked: bool):
        self.config_mgr.set("show_pet", checked)
        self.config_mgr.save()
        self.toggle_pet_requested.emit(checked)

    def _on_pause_toggled(self, checked: bool):
        self.scheduler.set_paused(checked)
        if checked:
            self.action_pause.setText("恢复定时提醒")
            self.show_message("下班提醒", "已临时暂停提醒")
        else:
            self.action_pause.setText("暂停今天提醒")
            self.show_message("下班提醒", "已恢复定时提醒")
        self.update_tooltip()

    def _on_autostart_toggled(self, checked: bool):
        success = set_autostart(checked)
        if success:
            self.config_mgr.set("autostart", checked)
            self.config_mgr.save()
            status_text = "已开启开机自启动" if checked else "已取消开机自启动"
            self.show_message("自启动设置", status_text)
        else:
            self.action_autostart.setChecked(not checked)

    def _on_tray_activated(self, reason):
        # 双击或单击打开设置窗口
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.open_settings_requested.emit()

    def _show_about(self):
        QMessageBox.information(
            None,
            "关于 下班提醒助手",
            "<h3>下班提醒助手 (Work-Off Reminder)</h3>"
            "<p>专为职场人士打造的 Windows 下班全屏提醒工具。</p>"
            "<ul>"
            "<li><b>极低占用</b>：后台空闲状态 0% CPU，超轻内存消耗</li>"
            "<li><b>视觉优雅</b>：全屏平滑淡入淡出动画，磨砂质感与实时大时钟</li>"
            "<li><b>高度定制</b>：多时间点、工作日筛选、自定义标语、字体、色彩及壁纸</li>"
            "<li><b>开箱即用</b>：开机自启、系统托盘常驻守护</li>"
            "</ul>"
            "<p style='color: #64748B;'>祝您每天工作顺利，准时下班！</p>"
        )
