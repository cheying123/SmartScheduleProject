from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    
    # 用户偏好设置
    preferred_work_hours = db.Column(db.JSON, nullable=True)
    preferred_break_hours = db.Column(db.JSON, nullable=True)
    location = db.Column(db.String(255), nullable=True)  # 城市 ID
    location_name = db.Column(db.String(255), nullable=True)  # 城市名称
    weather_alerts_enabled = db.Column(db.Boolean, default=True)
    
    # 关联关系
    schedules = db.relationship('Schedule', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_at else None,
            'location': self.location,
            'location_name': self.location_name,
            'weather_alerts_enabled': self.weather_alerts_enabled,
            'preferred_work_hours': self.preferred_work_hours
        }