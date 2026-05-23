@echo off
chcp 65001 >nul
title SmartSchedule - 后台服务

echo 正在启动 SmartSchedule 后台服务...
echo 启动后会自动打开浏览器访问 http://localhost:5000
echo.

cd /d "%~dp0backend"
start /min "" "%~dp0.venv\Scripts\pythonw.exe" app.py

timeout /t 3 /nobreak >nul
start http://localhost:5000

echo 服务已启动！
echo 双击 start_bg.vbs 可静默启动（无窗口）
echo 双击 stop_bg.bat 可停止服务
pause
