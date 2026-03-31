import os
from flask import Flask, jsonify, request
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


def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    
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
    
    # 根路由
    @app.route('/')
    def index():
        return jsonify({'message': 'SmartSchedule API is running!'})
    
    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'database': 'connected'})
    
    # 全局 CORS 中间件 - 确保所有 /api/ 请求都有 CORS 头
    @app.after_request
    def add_cors_headers(response):
        if request.path.startswith('/api/'):
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000, host='0.0.0.0')