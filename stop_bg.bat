@echo off
chcp 65001 >nul
title SmartSchedule - 停止后台服务

echo 正在停止 SmartSchedule 后台服务...

:: 查找并结束 pythonw 进程（运行 app.py 的）
taskkill /f /fi "WINDOWTITLE eq pythonw*" 2>nul

:: 更精确的方式：结束占用 5000 端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a 2>nul
)

echo 已停止。
pause
