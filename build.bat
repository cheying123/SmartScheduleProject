@echo off
chcp 65001 >nul
title SmartSchedule 打包工具

echo ========================================
echo   SmartSchedule 打包工具
echo ========================================
echo.

:: 1. 构建前端
echo [1/3] 构建前端...
cd /d "%~dp0frontend"
call npm run build
if %errorlevel% neq 0 (
    echo 前端构建失败！
    pause
    exit /b 1
)
echo 前端构建完成
echo.

:: 2. 安装打包依赖
echo [2/3] 安装打包依赖...
cd /d "%~dp0"
call .venv\Scripts\pip install pyinstaller -q
echo.

:: 3. 执行打包
echo [3/3] 正在打包，请耐心等待（约2-5分钟）...
call .venv\Scripts\pyinstaller build.spec --clean -y
if %errorlevel% neq 0 (
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！
echo   输出位置: dist\SmartSchedule.exe
echo ========================================
echo.
echo 将 dist\SmartSchedule.exe 发给用户即可使用。
echo 用户首次运行会自动在 exe 同目录创建 data 文件夹。
echo.
pause
