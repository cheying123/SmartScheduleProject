"""
SmartSchedule 桌面版启动器
使用系统原生 WebView2 窗口，无需额外下载浏览器。
双击此脚本或 desktop_run.vbs 即可启动。
"""
import os
import sys
import json
import logging
import threading
import webbrowser
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger('SmartSchedule')

# 项目根目录
ROOT_DIR = Path(__file__).parent
os.chdir(ROOT_DIR)
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / 'backend'))

APP_VERSION = "1.0.0"
GITHUB_REPO = "cheying123/SmartScheduleProject"
BACKEND_PORT = 5000

backend_thread = None
window = None


def create_tray_icon():
    """创建系统托盘图标"""
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=(79, 70, 229, 255))
        # 简单的 "S" 字母
        draw.text((20, 14), "S", fill=(255, 255, 255, 255))
        return img
    except ImportError:
        return None


def start_backend():
    """启动 Flask 后端"""
    from app import create_app
    app = create_app()
    try:
        import waitress
        waitress.serve(app, host='127.0.0.1', port=BACKEND_PORT)
    except ImportError:
        app.run(host='127.0.0.1', port=BACKEND_PORT, debug=False)


def wait_for_backend(timeout=15):
    """等待后端就绪"""
    import time
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(
                f'http://127.0.0.1:{BACKEND_PORT}/health', timeout=2)
            if resp.status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def check_update():
    """检查 GitHub 是否有新版本"""
    try:
        import requests
        resp = requests.get(
            f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest',
            timeout=5,
            headers={'Accept': 'application/json'}
        )
        if resp.status_code == 200:
            data = resp.json()
            latest = data.get('tag_name', '').lstrip('v')
            if latest and latest > APP_VERSION:
                return {
                    'version': latest,
                    'url': data.get('html_url', ''),
                    'body': data.get('body', ''),
                }
    except Exception as e:
        logger.warning(f"更新检查失败: {e}")
    return None


def on_app_started():
    """应用启动后的回调"""
    logger.info("桌面窗口已打开")
    update_info = check_update()
    if update_info and window:
        js = f"""
        document.body.dispatchEvent(new CustomEvent('update-available', {{
            detail: {{ version: '{update_info["version"]}', url: '{update_info["url"]}' }}
        }}));
        """
        try:
            window.evaluate_js(js)
        except Exception:
            pass


def main():
    global window, backend_thread

    logger.info(f"SmartSchedule v{APP_VERSION} 桌面版启动")

    # 强制桌面模式（SQLite）
    os.environ['SMARTSCHEDULE_DESKTOP'] = 'true'

    # 启动后端线程
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # 等待后端就绪
    if not wait_for_backend():
        logger.warning("后端启动较慢，继续等待...")

    # 启动桌面窗口
    try:
        import webview

        tray_icon = create_tray_icon()

        window = webview.create_window(
            title='SmartSchedule 智能日程',
            url=f'http://127.0.0.1:{BACKEND_PORT}',
            width=1200,
            height=800,
            min_size=(860, 600),
            resizable=True,
            text_select=True,
        )

        webview.start(on_app_started, gui='edgechromium')

        logger.info("SmartSchedule 桌面版已退出")

    except ImportError:
        logger.error("pywebview 未安装，请执行: pip install pywebview")
        webbrowser.open(f'http://127.0.0.1:{BACKEND_PORT}')
        import time
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error(f"桌面窗口启动失败: {e}")
        logger.info("回退到浏览器模式...")
        webbrowser.open(f'http://127.0.0.1:{BACKEND_PORT}')
        import time
        while True:
            time.sleep(1)


if __name__ == '__main__':
    main()
