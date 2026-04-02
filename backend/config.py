# NEW_FILE_CODE
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""
    
    # 数据库配置
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
        raise ValueError("缺少必要的数据库环境变量配置")
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT 配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 小时
    JWT_TOKEN_LOCATION = ['headers', 'cookies']  # 新增：允许从 headers 和 cookies 获取 token
    JWT_COOKIE_SECURE = False  # 开发环境设为 False，生产环境改为 True
    JWT_COOKIE_CSRF_PROTECT = False  # 开发环境暂时关闭 CSRF 保护
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    
    JWT_IDENTITY_CLAIM = 'user_id'
    
    


    # 天气 API 配置
    QWEATHER_API_KEY = os.getenv('QWEATHER_API_KEY')
    
    # AI 配置
    AI_API_KEY = os.getenv('AI_API_KEY')
    AI_API_URL = os.getenv('AI_API_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
    AI_MODEL = os.getenv('AI_MODEL', 'qwen-turbo')