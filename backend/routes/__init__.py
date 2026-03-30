# NEW_FILE_CODE
from .auth import auth_bp
from .schedules import schedules_bp
from .users import users_bp
from .recommendations import recommendations_bp

__all__ = ['auth_bp', 'schedules_bp', 'users_bp', 'recommendations_bp']