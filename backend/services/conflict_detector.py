# NEW_FILE_CODE
from datetime import timedelta
from models.schedule import Schedule

def detect_schedule_conflicts(user_id, new_start_time, new_end_time, exclude_id=None):
    """
    检测日程冲突
    
    Args:
        user_id: 用户 ID
        new_start_time: 新日程开始时间
        new_end_time: 新日程结束时间
        exclude_id: 要排除的日程 ID（用于编辑时检查）
        
    Returns:
        冲突列表
    """
    conflicts = []
    
    if new_end_time is None:
        new_end_time = new_start_time + timedelta(hours=1)
    
    # 确保传入的时间是 naive datetime
    if new_start_time.tzinfo is not None:
        new_start_time = new_start_time.replace(tzinfo=None)
    if new_end_time.tzinfo is not None:
        new_end_time = new_end_time.replace(tzinfo=None)
    
    query = Schedule.query.filter_by(user_id=user_id)
    if exclude_id:
        query = query.filter(Schedule.id != exclude_id)
    
    schedules = query.all()
    
    for schedule in schedules:
        existing_start = schedule.start_time
        if existing_start.tzinfo is not None:
            existing_start = existing_start.replace(tzinfo=None)
        
        existing_end = schedule.end_time
        if existing_end is None:
            existing_end = existing_start + timedelta(hours=1)
        elif existing_end.tzinfo is not None:
            existing_end = existing_end.replace(tzinfo=None)
        
        # 检查时间重叠
        if (new_start_time < existing_end and new_end_time > existing_start):
            conflicts.append({
                'schedule_id': schedule.id,
                'title': schedule.title,
                'start_time': schedule.start_time,
                'end_time': existing_end,
                'conflict_type': 'time_overlap'
            })
    
    return conflicts