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
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_at else None
        }