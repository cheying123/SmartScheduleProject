# NEW_FILE_CODE
from datetime import datetime, timedelta
from collections import Counter
from models.schedule import Schedule

def generate_schedule_recommendations(user_id):
    """
    基于用户历史日程生成智能推荐
    
    Args:
        user_id: 用户 ID
        
    Returns:
        推荐列表
    """
    recommendations = []
    
    user_schedules = Schedule.query.filter_by(user_id=user_id).order_by(Schedule.start_time).all()
    
    if len(user_schedules) < 3:
        return [{'type': 'info', 'message': '日程数据不足，暂无法提供智能推荐'}]
    
    # 分析工作时间偏好（UTC 转本地时间 UTC+8）
    work_hours = []
    for schedule in user_schedules:
        utc_time = schedule.start_time
        local_time = utc_time + timedelta(hours=8)
        local_hour = local_time.hour
        work_hours.append(local_hour)
    
    if work_hours:
        hour_counter = Counter(work_hours)
        most_common_hour = hour_counter.most_common(1)[0][0]
        
        recommendations.append({
            'type': 'time_preference',
            'message': f'根据历史记录，您通常在{most_common_hour}点安排活动，建议保持这个习惯',
            'suggested_hour': most_common_hour
        })
    
    # 检测休息时间
    morning_activities = []
    afternoon_activities = []
    
    for schedule in user_schedules:
        utc_time = schedule.start_time
        local_time = utc_time + timedelta(hours=8)
        local_hour = local_time.hour
        
        if local_hour < 12:
            morning_activities.append(schedule)
        elif 12 <= local_hour < 18:
            afternoon_activities.append(schedule)
    
    if len(morning_activities) > len(afternoon_activities) * 2:
        recommendations.append({
            'type': 'balance',
            'message': '您上午的日程较多，建议适当安排下午的休息时间'
        })
    
    # 天气相关建议
    now_beijing = datetime.now() + timedelta(hours=8)
    today_beijing = now_beijing.date()
    
    today_schedules = [
        s for s in user_schedules 
        if (s.start_time + timedelta(hours=8)).date() == today_beijing
    ]
    
    if today_schedules:
        recommendations.append({
            'type': 'weather',
            'message': '今天有日程安排，请查看具体日程的天气提示'
        })
    
    return recommendations