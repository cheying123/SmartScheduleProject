from extensions import db
from .user import User
from .schedule import Schedule
from .conflict import ScheduleConflict, UserBehaviorLog

__all__ = ['User', 'Schedule', 'ScheduleConflict', 'UserBehaviorLog']


# 在 d:\SmartScheduleProject\backend\models\__init__.py 文件中添加
class Conversation(db.Model):
    """AI 对话历史模型"""
    __tablename__ = 'conversation'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'message': self.message,
            'session_id': self.session_id,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_at else None
        }