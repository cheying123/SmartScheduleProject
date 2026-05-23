import logging
import os
import sys
from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from config import Config
from extensions import db, migrate, cors
from routes.auth import auth_bp
from routes.schedules import schedules_bp
from routes.users import users_bp
from routes.recommendations import recommendations_bp
from routes.weather import weather_bp
from routes.location import location_bp
from routes.analytics import analytics_bp
from routes.ai import ai_bp
from routes.assistant import assistant_bp
from apscheduler.schedulers.background import BackgroundScheduler
from services.recurring_service import RecurringService

logger = logging.getLogger(__name__)

# 前端构建输出目录（支持 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    FRONTEND_DIST = os.path.join(sys._MEIPASS, 'frontend', 'dist')
else:
    FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'dist')

def create_app():
    app = Flask(__name__, static_folder=None)  # 关闭默认静态文件
    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=False,
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )

    # 创建数据库表
    with app.app_context():
        db.create_all()

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(schedules_bp)
    app.register_blueprint(assistant_bp, url_prefix='/api/assistant') # ✅ 确保这一行存在
    app.register_blueprint(users_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(analytics_bp)  # 注册分析蓝图
    app.register_blueprint(ai_bp) # AI 分析助手（使用 ANALYSIS_AI_* 配置）

    # 启动定时任务：每天凌晨 00:01 检查重复日程
    scheduler = BackgroundScheduler()

    # 使用 app.app_context() 包装任务，确保数据库操作有上下文
    def job_wrapper():
        with app.app_context():
            try:
                RecurringService.process_recurring_schedules()
            except Exception:
                logger.exception("定时任务执行失败")


    scheduler.add_job(
        func=job_wrapper,
        trigger="cron",
        hour=0,
        minute=1,
        id='recurring_schedule_job',
        replace_existing=True
    )
    scheduler.start()

    # 健康检查
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok'})

    # 托管前端静态文件（如果 dist 目录存在）
    if os.path.isdir(FRONTEND_DIST):
        # 静态文件路由
        @app.route('/assets/<path:filename>')
        def serve_frontend_assets(filename):
            return send_from_directory(os.path.join(FRONTEND_DIST, 'assets'), filename)

        # SPA 回退：所有非 API 路由都返回 index.html
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_frontend(path):
            if path.startswith('api/'):
                return jsonify({'error': 'Not found'}), 404
            file_path = os.path.join(FRONTEND_DIST, path)
            if path and os.path.isfile(file_path):
                return send_from_directory(FRONTEND_DIST, path)
            return send_from_directory(FRONTEND_DIST, 'index.html')
    else:
        # 没有前端构建时，显示简单提示
        @app.route('/')
        def index():
            return jsonify({'message': 'SmartSchedule API is running! (Frontend not built yet)'})

    # 版本信息（放在 SPA 路由之后注册，确保优先匹配）
    @app.route('/api/version', methods=['GET'])
    def version_info():
        return jsonify({
            'version': '1.0.0',
            'desktop': os.environ.get('SMARTSCHEDULE_DESKTOP') == 'true',
        })

    # 检查更新（从 GitHub）
    @app.route('/api/check-update', methods=['GET'])
    def check_update():
        import requests
        try:
            resp = requests.get(
                'https://api.github.com/repos/cheying123/SmartScheduleProject/releases/latest',
                timeout=5,
                headers={'Accept': 'application/json'}
            )
            if resp.status_code == 200:
                data = resp.json()
                latest = data.get('tag_name', 'v1.0.0').lstrip('v')
                current = '1.0.0'
                return jsonify({
                    'has_update': latest > current,
                    'latest_version': latest,
                    'current_version': current,
                    'download_url': data.get('html_url', ''),
                    'body': data.get('body', ''),
                })
        except Exception as e:
            logger.debug(f"更新检查失败: {e}")
            return jsonify({'has_update': False, 'error': str(e)}), 200
        return jsonify({'has_update': False})

    return app

if __name__ == '__main__':
    app = create_app()
    # 后台模式（pythonw.exe）下禁用 reloader，避免弹出窗口
    debug_mode = 'pythonw' not in sys.executable.lower()
    app.run(debug=debug_mode, port=5000, host='0.0.0.0')