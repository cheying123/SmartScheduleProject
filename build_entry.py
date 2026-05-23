"""
SmartSchedule 打包入口
PyInstaller 打包后，用户双击此 exe 即可启动。
"""
import os
import sys
import logging
import threading
import webbrowser

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger('SmartSchedule')

APP_VERSION = "1.0.0"
BACKEND_PORT = 5000


def main():
    # 确定基础目录
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    os.chdir(base_dir)
    os.environ['SMARTSCHEDULE_DESKTOP'] = 'true'

    # 确保 backend 模块可导入
    backend_dir = os.path.join(base_dir, 'backend')
    if os.path.isdir(backend_dir):
        sys.path.insert(0, backend_dir)

    logger.info(f'SmartSchedule v{APP_VERSION} 启动中...')

    # 导入并启动 Flask 后端
    from app import create_app
    flask_app = create_app()

    def run_backend():
        try:
            import waitress
            waitress.serve(flask_app, host='127.0.0.1', port=BACKEND_PORT)
        except ImportError:
            flask_app.run(host='127.0.0.1', port=BACKEND_PORT, debug=False)

    t = threading.Thread(target=run_backend, daemon=True)
    t.start()

    # 等待后端就绪
    import urllib.request
    import time
    ready = False
    for _ in range(30):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{BACKEND_PORT}/health', timeout=2) as r:
                if r.status == 200:
                    ready = True
                    break
        except Exception:
            pass
        time.sleep(0.5)

    if ready:
        logger.info(f'服务已启动: http://127.0.0.1:{BACKEND_PORT}')
        threading.Timer(1.5, lambda: webbrowser.open(
            f'http://127.0.0.1:{BACKEND_PORT}')).start()
    else:
        logger.warning('后端启动超时')
        webbrowser.open(f'http://127.0.0.1:{BACKEND_PORT}')

    # 保持进程运行
    try:
        t.join()
    except KeyboardInterrupt:
        logger.info('正在退出...')


if __name__ == '__main__':
    main()
