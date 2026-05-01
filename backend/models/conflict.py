from extensions import db

class ScheduleConflict(db.Model):
    __tablename__ = 'schedule_conflict'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule1_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    schedule2_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    conflict_type = db.Column(db.String(50), nullable=True)
    suggested_solution = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())


class UserBehaviorLog(db.Model):
    __tablename__ = 'user_behavior_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    action_data = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.now())