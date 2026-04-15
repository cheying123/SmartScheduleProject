# NEW_FILE_CODE
from datetime import datetime, timedelta
from collections import Counter
from models.schedule import Schedule
from services.weather_service import get_weather_with_alerts

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
    
    # ===== 优化后的天气相关建议 =====
    now_beijing = datetime.now() + timedelta(hours=8)
    today_beijing = now_beijing.date()
    tomorrow_beijing = today_beijing + timedelta(days=1)
    
    # 获取今天的日程
    today_schedules = [
        s for s in user_schedules 
        if (s.start_time + timedelta(hours=8)).date() == today_beijing
    ]
    
    # 获取明天的日程
    tomorrow_schedules = [
        s for s in user_schedules 
        if (s.start_time + timedelta(hours=8)).date() == tomorrow_beijing
    ]
    
    # 尝试获取用户的城市位置信息
    from app import db
    from models.user import User
    user = User.query.get(user_id)
    city_location_id = user.location if user and user.location else "101010100"  # 默认北京
    
    # 获取今天和明天的天气预报
    try:
        today_weather = get_weather_with_alerts(city_location_id, today_beijing.strftime('%Y-%m-%d'))
        tomorrow_weather = get_weather_with_alerts(city_location_id, tomorrow_beijing.strftime('%Y-%m-%d'))
        
        # 生成智能天气建议
        weather_advice = _generate_weather_advice(today_weather, tomorrow_weather, today_schedules, tomorrow_schedules)
        if weather_advice:
            recommendations.extend(weather_advice)
            
    except Exception as e:
        print(f"生成天气建议失败：{e}")
        # 降级方案：如果有日程，给出通用提示
        if today_schedules or tomorrow_schedules:
            recommendations.append({
                'type': 'weather',
                'message': '近期有日程安排，建议关注天气变化'
            })
    
    return recommendations


def _generate_weather_advice(today_weather, tomorrow_weather, today_schedules, tomorrow_schedules):
    """
    根据天气数据生成智能建议
    
    Args:
        today_weather: 今天天气数据
        tomorrow_weather: 明天天气数据
        today_schedules: 今天的日程列表
        tomorrow_schedules: 明天的日程列表
        
    Returns:
        天气建议列表
    """
    advice_list = []
    
    # 天气关键词映射
    weather_keywords = {
        '雨': ['雨', 'rain', '小雨', '中雨', '大雨', '暴雨', '雷阵雨'],
        '雪': ['雪', 'snow', '小雪', '中雪', '大雪'],
        '晴': ['晴', 'sunny', 'clear'],
        '阴': ['阴', 'cloudy', 'overcast'],
        '雾': ['雾', 'fog', 'haze'],
        '风': ['风', 'wind', '大风'],
        '高温': ['高温', '热', 'hot', '35', '36', '37', '38', '39', '40'],
        '低温': ['低温', '冷', 'cold', '-5', '-10', '-15', '零下']
    }
    
    def check_weather_condition(weather_text, conditions):
        """检查天气文本是否包含特定条件"""
        if not weather_text:
            return False
        weather_lower = weather_text.lower()
        for condition in conditions:
            if condition.lower() in weather_lower:
                return True
        return False
    
    # ===== 今天的天气建议 =====
    if today_weather and today_schedules:
        weather_text = today_weather.get('weather_text', '')
        temp_max = today_weather.get('temp_max', '')
        temp_min = today_weather.get('temp_min', '')
        
        # 雨天建议
        if check_weather_condition(weather_text, weather_keywords['雨']):
            advice_list.append({
                'type': 'weather',
                'priority': 'high',
                'message': f'🌧️ 今天有雨（{weather_text}），出行记得带伞，注意交通安全',
                'weather_type': 'rain'
            })
        
        # 雪天建议
        elif check_weather_condition(weather_text, weather_keywords['雪']):
            advice_list.append({
                'type': 'weather',
                'priority': 'high',
                'message': f'❄️ 今天有雪（{weather_text}），路面湿滑，建议提前出门',
                'weather_type': 'snow'
            })
        
        # 高温建议
        elif check_weather_condition(weather_text, weather_keywords['高温']) or (temp_max and int(temp_max) >= 35):
            advice_list.append({
                'type': 'weather',
                'priority': 'medium',
                'message': f'☀️ 今天高温（最高{temp_max}°C），注意防暑降温，多喝水',
                'weather_type': 'hot'
            })
        
        # 低温建议
        elif check_weather_condition(weather_text, weather_keywords['低温']) or (temp_min and int(temp_min) <= -5):
            advice_list.append({
                'type': 'weather',
                'priority': 'medium',
                'message': f'🥶 今天低温（最低{temp_min}°C），注意保暖，预防感冒',
                'weather_type': 'cold'
            })
        
        # 雾霾建议
        elif check_weather_condition(weather_text, weather_keywords['雾']):
            advice_list.append({
                'type': 'weather',
                'priority': 'medium',
                'message': f'🌫️ 今天有雾霾（{weather_text}），建议佩戴口罩，减少户外活动',
                'weather_type': 'fog'
            })
        
        # 大风建议
        elif check_weather_condition(weather_text, weather_keywords['风']):
            advice_list.append({
                'type': 'weather',
                'priority': 'low',
                'message': f'💨 今天有大风（{weather_text}），注意防风，避免高空作业',
                'weather_type': 'wind'
            })
        
        # 晴天建议
        elif check_weather_condition(weather_text, weather_keywords['晴']):
            advice_list.append({
                'type': 'weather',
                'priority': 'info',
                'message': f'☀️ 今天天气晴朗，适合户外活动和运动',
                'weather_type': 'sunny'
            })
    
    # ===== 明天的天气建议 =====
    if tomorrow_weather and tomorrow_schedules:
        weather_text = tomorrow_weather.get('weather_text', '')
        temp_max = tomorrow_weather.get('temp_max', '')
        temp_min = tomorrow_weather.get('temp_min', '')
        
        # 明天有雨
        if check_weather_condition(weather_text, weather_keywords['雨']):
            advice_list.append({
                'type': 'weather',
                'priority': 'medium',
                'message': f'🌧️ 明天预报有雨（{weather_text}），提前准备雨具',
                'weather_type': 'rain_tomorrow'
            })
        
        # 明天有雪
        elif check_weather_condition(weather_text, weather_keywords['雪']):
            advice_list.append({
                'type': 'weather',
                'priority': 'medium',
                'message': f'❄️ 明天预报有雪（{weather_text}），注意出行安全',
                'weather_type': 'snow_tomorrow'
            })
        
        # 明天高温
        elif check_weather_condition(weather_text, weather_keywords['高温']) or (temp_max and int(temp_max) >= 35):
            advice_list.append({
                'type': 'weather',
                'priority': 'low',
                'message': f'☀️ 明天高温（最高{temp_max}°C），做好防暑准备',
                'weather_type': 'hot_tomorrow'
            })
        
        # 明天低温
        elif check_weather_condition(weather_text, weather_keywords['低温']) or (temp_min and int(temp_min) <= -5):
            advice_list.append({
                'type': 'weather',
                'priority': 'low',
                'message': f'🥶 明天低温（最低{temp_min}°C），注意添衣保暖',
                'weather_type': 'cold_tomorrow'
            })
    
    # ===== 特殊场景建议 =====
    # 今天和明天都有日程，且天气差异大
    if today_weather and tomorrow_weather and today_schedules and tomorrow_schedules:
        today_text = today_weather.get('weather_text', '')
        tomorrow_text = tomorrow_weather.get('weather_text', '')
        
        # 今天晴，明天雨
        if check_weather_condition(today_text, weather_keywords['晴']) and check_weather_condition(tomorrow_text, weather_keywords['雨']):
            advice_list.append({
                'type': 'weather',
                'priority': 'info',
                'message': f'⚠️ 天气变化提醒：今天晴朗，明天转雨，注意调整出行计划',
                'weather_type': 'weather_change'
            })
    
    return advice_list