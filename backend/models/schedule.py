# NEW_FILE_CODE
from extensions import db
from datetime import datetime

class Schedule(db.Model):
    __tablename__ = 'schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)

    weather_info = db.Column(db.String(255), nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_pattern = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.Integer, default=1)
    tags = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())

    # ========== 新增字段开始 ==========
    
    # 任务完成状态追踪（用于用户行为分析）
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # 位置信息（用于通勤分析和冲突检测）
    location = db.Column(db.String(200), nullable=True)
    
    # 会议相关功能
    is_meeting = db.Column(db.Boolean, default=False)
    meeting_url = db.Column(db.String(500), nullable=True)
    attendees = db.Column(db.JSON, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'start_time': self.start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end_time': self.end_time.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_time else None,
            'weather_info': self.weather_info,
            'is_recurring': self.is_recurring,
            'recurring_pattern': self.recurring_pattern,
            'priority': self.priority,
            'tags': self.tags,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_at else None,

            # ========== 新增字段序列化 ==========
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.strftime('%Y-%m-%dT%H:%M:%SZ') if self.completed_at else None,
            'location': self.location,
            'is_meeting': self.is_meeting,
            'meeting_url': self.meeting_url,
            'attendees': self.attendees
            # ========== 新增字段序列化结束 ==========
        }