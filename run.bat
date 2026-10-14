@echo off
chcp 65001 >nul
title 启动下班提醒助手

echo 正在启动下班提醒助手...
cd /d "%~dp0"

where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0main.py"
    echo 已在后台静默启动（托盘运行），请查看任务栏右下角托盘图标。
) else (
    start "" python "%~dp0main.py"
    echo 已启动程序，请查看任务栏右下角托盘图标。
)

timeout /t 2 >nul
exit
