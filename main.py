# -*- coding: utf-8 -*-
"""
下班提醒助手 (Work-Off Reminder) - 程序主入口
包含单实例管理、定时调度、全屏弹窗、桌面挂件及托盘常驻守护
"""
import sys
import os

# 确保当前目录位于 sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from app.config import ConfigManager
from app.scheduler import ReminderScheduler
from app.ui.popup import FullscreenPopup
from app.ui.settings import SettingsDialog
from app.ui.tray import TrayManager
from app.ui.pet import DesktopPetWidget
from app.weather import WeatherService
from app.ui.assets import create_app_icon

SERVER_PIPE_NAME = "WorkOffReminder_SingleInstance_Channel_v1"

class WorkOffApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # 保证关闭所有窗口后应用继续在托盘后台驻留
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setWindowIcon(create_app_icon(32))

        # 单实例防重复运行检测
        if self._check_existing_instance():
            sys.exit(0)

        # 1. 初始化配置管理器
        self.config_mgr = ConfigManager()

        # 2. 初始化调度器
        self.scheduler = ReminderScheduler(self.config_mgr)

        # 3. 初始化全屏弹窗
        self.popup = FullscreenPopup(self.config_mgr)

        # 4. 初始化天气服务 (南京浦口区)
        self.weather = WeatherService()

        # 5. 初始化桌面宠物挂件 (猫咪趴牌造型 + 倒计时 + 天气)
        self.pet = DesktopPetWidget(self.config_mgr, self.scheduler, self.weather)

        # 6. 初始化设置窗口 (现代控制中心)
        self.settings_dialog = SettingsDialog(self.config_mgr, scheduler=self.scheduler, weather_service=self.weather)

        # 7. 初始化托盘管理器
        self.tray = TrayManager(self.config_mgr, self.scheduler)

        # 绑定事件信号
        self._bind_signals()

        # 启动单实例本地服务端
        self._start_ipc_server()

    def _check_existing_instance(self) -> bool:
        """检查是否已有实例运行，若有则向其发送激活信号后返回 True"""
        socket = QLocalSocket()
        socket.connectToServer(SERVER_PIPE_NAME)
        if socket.waitForConnected(500):
            socket.write(b"SHOW_SETTINGS")
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            return True
        return False

    def _start_ipc_server(self):
        """开启本地 IPC 服务，用于接收后续启动请求"""
        self.ipc_server = QLocalServer(self.app)
        self.ipc_server.removeServer(SERVER_PIPE_NAME)
        self.ipc_server.listen(SERVER_PIPE_NAME)
        self.ipc_server.newConnection.connect(self._handle_ipc_connection)

    def _handle_ipc_connection(self):
        client = self.ipc_server.nextPendingConnection()
        if client:
            client.waitForReadyRead(500)
            cmd = client.readAll().data().decode("utf-8")
            if "SHOW_SETTINGS" in cmd:
                self._show_settings()
            client.disconnectFromServer()

    def _bind_signals(self):
        # 定时器触发 -> 打开全屏弹窗
        self.scheduler.trigger_reminder.connect(self._on_reminder_triggered)

        # 弹窗点击稍后提醒 -> 调度器添加贪睡目标
        self.popup.snooze_requested.connect(self._on_snooze_requested)

        # 托盘菜单联动
        self.tray.open_settings_requested.connect(self._show_settings)
        self.tray.test_popup_requested.connect(self._trigger_test_popup)
        self.tray.toggle_pet_requested.connect(self._on_toggle_pet)
        self.tray.exit_requested.connect(self._exit_app)

        # 桌面挂件联动
        self.pet.open_settings_requested.connect(self._show_settings)
        self.pet.test_popup_requested.connect(self._trigger_test_popup)
        self.pet.exit_requested.connect(self._exit_app)

        # 设置窗口事件
        self.settings_dialog.config_saved.connect(self._on_config_saved)
        self.settings_dialog.test_requested.connect(self._trigger_test_popup)

    def _on_reminder_triggered(self, time_desc: str):
        """下班闹钟到达，弹出全屏提醒"""
        self.popup.trigger_popup()
        self.tray.update_tooltip()

    def _on_snooze_requested(self, minutes: int):
        """稍后提醒请求"""
        self.scheduler.add_snooze(minutes)
        self.tray.update_tooltip()
        self.tray.show_message("稍后提醒", f"已为您设置 {minutes} 分钟后再次提醒")

    def _show_settings(self):
        """显示设置窗口"""
        self.settings_dialog.load_from_config()
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def _trigger_test_popup(self):
        """测试全屏预览"""
        self.popup.trigger_popup()

    def _on_toggle_pet(self, checked: bool):
        """切换桌宠挂件显示状态"""
        if checked:
            self.pet.show()
        else:
            self.pet.hide()

    def _on_config_saved(self):
        """配置更新后刷新各组件"""
        self.popup.apply_styles()
        self.pet.override_theme = self.config_mgr.get("pet_override_theme", "auto")
        self.pet.apply_styles()
        self.pet._refresh_content()
        if self.config_mgr.get("show_pet", True):
            self.pet.show()
        else:
            self.pet.hide()
        self.tray.sync_pet_checkbox()
        self.tray.sync_autostart_checkbox()
        self.tray.update_tooltip()
        self.tray.show_message("设置已保存", "提醒配置与样式已即时生效")

    def _exit_app(self):
        """优雅退出"""
        self.scheduler.stop()
        if hasattr(self, "ipc_server"):
            self.ipc_server.close()
        self.app.quit()

    def run(self):
        # 显示托盘图标并启动调度
        self.tray.show()
        self.scheduler.start()
        self.weather.start()

        # 根据配置决定是否在桌面展示挂件
        if self.config_mgr.get("show_pet", True):
            self.pet.show()

        # 启动时气泡提示
        self.tray.show_message(
            "下班提醒助手已启动", 
            "正在后台守护您的下班时间，双击托盘图标或桌宠挂件可进行个性化设置。"
        )

        return self.app.exec()

def main():
    app_instance = WorkOffApp()
    sys.exit(app_instance.run())

if __name__ == "__main__":
    main()
