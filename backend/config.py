import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ========== 数据库配置 ==========
    # 优先使用 MySQL（配置了 DB_HOST 时），否则自动使用 SQLite
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')

    # 桌面模式强制使用 SQLite（Electron 启动时设置此环境变量）
    if os.getenv('SMARTSCHEDULE_DESKTOP') == 'true':
        DB_HOST = None

    if DB_HOST:
        # MySQL 模式
        if not all([DB_USER, DB_PASSWORD, DB_NAME]):
            raise ValueError("配置了 DB_HOST 但缺少 DB_USER/DB_PASSWORD/DB_NAME")
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    else:
        # SQLite 模式（默认，无需安装任何数据库）
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(db_dir, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(db_dir, "schedule.db")}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT 配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_IDENTITY_CLAIM = 'user_id'

    # 天气 API 配置
    QWEATHER_API_KEY = os.getenv('QWEATHER_API_KEY')

    # AI 配置
    AI_API_KEY = os.getenv('AI_API_KEY')
    AI_API_URL = os.getenv('AI_API_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
    AI_MODEL = os.getenv('AI_MODEL', 'qwen-turbo')
