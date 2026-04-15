# NEW_FILE_CODE
from datetime import timedelta
from models.schedule import Schedule
from services.user_behavior_analyzer import UserBehaviorAnalyzer

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


class ConflictDetector:
    
    @staticmethod
    def detect_conflicts(user_id, new_start_time, new_end_time, exclude_id=None):
        """
        检测日程冲突(ConflictDetector类的静态方法)
        
        Args:
            user_id: 用户 ID
            new_start_time: 新日程开始时间
            new_end_time: 新日程结束时间
            exclude_id: 要排除的日程 ID（用于编辑时检查）
            
        Returns:
            冲突列表
        """
        return detect_schedule_conflicts(user_id, new_start_time, new_end_time, exclude_id)

    @staticmethod
    def suggest_alternative_slots(user_id, original_start_time, duration_minutes=60, exclude_id=None):
        """
        智能推荐替代时间段
        :param user_id: 用户ID
        :param original_start_time: 原计划的开始时间 (datetime对象)
        :param duration_minutes: 日程持续时间（分钟）
        :return: 包含3个建议时间段的列表
        """
        suggestions = []
        
        # 1. 获取用户的行为分析数据（高效时段、繁忙日期等）
        analyzer = UserBehaviorAnalyzer()
        try:
            stats = analyzer.analyze_user_behavior(user_id)
            productive_hours = stats.get('productivity', {}).get('productive_hours', [9, 10, 14, 15])
            busy_days = stats.get('weekly_pattern', {}).get('busy_days', [])
        except:
            productive_hours = [9, 10, 14, 15] # 默认值
            busy_days = []

        # 2. 搜索策略：从原时间往后找，优先匹配高效时段，避开繁忙日
        current_check = original_start_time + timedelta(minutes=duration_minutes)
        max_search_days = 3 # 只往后找3天
        
        while len(suggestions) < 3 and (current_check - original_start_time).days <= max_search_days:
            # 检查是否是繁忙日
            if current_check.weekday() in busy_days:
                current_check += timedelta(hours=1)
                continue
            
            # 检查是否在高效时段内 (8点到20点之间)
            hour = current_check.hour
            if 8 <= hour <= 20:
                # 计算结束时间
                check_end = current_check + timedelta(minutes=duration_minutes)
                
                # 调用现有的检测逻辑检查是否有冲突
                conflicts = ConflictDetector.detect_conflicts(user_id, current_check, check_end, exclude_id)
                
                if not conflicts:
                    # 如果该小时是高效时段，加分；否则普通
                    reason = "该时段无冲突"
                    if hour in productive_hours:
                        reason = f"这是您的高效工作时段（{hour}点），且无冲突"
                    
                    suggestions.append({
                        'start_time': current_check.isoformat(),
                        'end_time': check_end.isoformat(),
                        'reason': reason
                    })
            
            # 每次递增30分钟继续寻找
            current_check += timedelta(minutes=30)
            
        return suggestions
