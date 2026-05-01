import logging
from flask import Flask, jsonify
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


def create_app():
    app = Flask(__name__)
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
    app.register_blueprint(location_bp)  # 新增
    app.register_blueprint(analytics_bp)  # 新增：注册分析蓝图
    app.register_blueprint(ai_bp) # AI 分析助手（使用 ANALYSIS_AI_* 配置）
    
    # ⚙️ 启动定时任务：每天凌晨 00:01 检查重复日程
    scheduler = BackgroundScheduler()

    # 修复：使用 app.app_context() 包装任务，确保数据库操作有上下文
    def job_wrapper():
        with app.app_context():
            try:
                RecurringService.process_recurring_schedules()
            except Exception:
                logger.exception("定时任务执行失败")


    scheduler.add_job(
        func=job_wrapper,  # ← 这里要改成 job_wrapper，不能直接传 RecurringService...
        trigger="cron",
        hour=0,
        minute=1,
        id='recurring_schedule_job',
        replace_existing=True
    )
    scheduler.start()

    # 根路由
    @app.route('/')
    def index():
        return jsonify({'message': 'SmartSchedule API is running!'})
    
    # 健康检查
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok'})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000, host='0.0.0.0')