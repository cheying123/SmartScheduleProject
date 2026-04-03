import os
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager  # 新增导入
from config import Config
from extensions import db, migrate, cors
from models.user import User
from models.schedule import Schedule
from models.conflict import ScheduleConflict, UserBehaviorLog
from routes.auth import auth_bp
from routes.schedules import schedules_bp
from routes.users import users_bp
from routes.recommendations import recommendations_bp
from routes.weather import weather_bp
from routes.location import location_bp  # 新增
from routes.analytics import analytics_bp  # 新增导入
from routes.ai import ai_bp


def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)  # 新增：初始化 JWTManager
    
        # CORS 配置 - 只允许一个 origin，避免重复
    cors.init_app(
        app, 
        resources={r"/api/*": {"origins": "*"}}, 
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
    )
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(schedules_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(location_bp)  # 新增
    app.register_blueprint(analytics_bp)  # 新增：注册分析蓝图
    app.register_blueprint(ai_bp) # AI 分析助手（使用 ANALYSIS_AI_* 配置）
    
    # 根路由
    @app.route('/')
    def index():
        return jsonify({'message': 'SmartSchedule API is running!'})
    
    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'database': 'connected'})
    
    # 健康检查
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok'})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000, host='0.0.0.0')