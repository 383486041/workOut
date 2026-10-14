# -*- coding: utf-8 -*-
"""
Windows 开机自启动管理模块
基于注册表 CurrentVersion\\Run 实现，免管理员权限
"""
import os
import sys
import winreg

APP_NAME = "WorkOffReminder"

def get_launch_command() -> str:
    """获取启动本程序的完整命令行（打包后直接使用 exe，开发环境下优先使用 pythonw.exe）"""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_py = os.path.join(base_dir, "main.py")
    
    # 查找 pythonw.exe
    py_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(py_dir, "pythonw.exe")
    if os.path.exists(pythonw):
        runner = pythonw
    else:
        runner = sys.executable

    return f'"{runner}" "{main_py}"'

def is_autostart_enabled() -> bool:
    """检查是否已经设置了开机自启动"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(val)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[Autostart] 查询开机自启失败: {e}")
        return False

def set_autostart(enable: bool) -> bool:
    """设置或取消开机自启动"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                cmd = get_launch_command()
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                print(f"[Autostart] 已开启开机自启: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    print("[Autostart] 已关闭开机自启")
                except FileNotFoundError:
                    pass
            return True
    except Exception as e:
        print(f"[Autostart] 设置开机自启失败: {e}")
        return False
