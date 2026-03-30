# NEW_FILE_CODE
import requests
from datetime import datetime, timedelta
from config import Config

def get_weather_for_date(city_location_id, date_str):
    """
    获取指定日期的天气预报信息
    
    Args:
        city_location_id: 城市 location ID
        date_str: 日期字符串，格式 YYYY-MM-DD
        
    Returns:
        天气预报信息字符串
    """
    if not Config.QWEATHER_API_KEY:
        print("警告：QWEATHER_API_KEY 未配置")
        return None
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        if date_str < today:
            return None
        
        url = f"https://mh78m2gduk.re.qweatherapi.com/v7/weather/7d?location={city_location_id}&key={Config.QWEATHER_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get('code') == '200':
            daily_forecasts = data.get('daily', [])
            
            for forecast in daily_forecasts:
                fx_date = forecast.get('fxDate')
                if fx_date == date_str:
                    text_day = forecast.get('textDay', '未知')
                    temp_min = forecast.get('tempMin', '?')
                    temp_max = forecast.get('tempMax', '?')
                    return f"{text_day}，气温 {temp_min}~{temp_max}℃"
            
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
            today_date = datetime.strptime(today, '%Y-%m-%d')
            days_diff = (target_date - today_date).days
            
            if 0 <= days_diff < len(daily_forecasts):
                forecast = daily_forecasts[days_diff]
                text_day = forecast.get('textDay', '未知')
                temp_min = forecast.get('tempMin', '?')
                temp_max = forecast.get('tempMax', '?')
                return f"{text_day}，气温 {temp_min}~{temp_max}℃"
            
        return None
        
    except Exception as e:
        print(f"天气 API 请求异常：{e}")
        return None


def update_schedules_weather_for_user(user_id, city_location_id):
    """
    更新指定用户所有日程的天气信息
    
    Args:
        user_id: 用户 ID
        city_location_id: 城市 ID
        
    Returns:
        更新的日程数量
    """
    from models.schedule import Schedule
    from extensions import db
    
    try:
        schedules = Schedule.query.filter_by(user_id=user_id).all()
        
        today = datetime.now().strftime('%Y-%m-%d')
        max_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        updated_count = 0
        
        for schedule in schedules:
            schedule_date = schedule.start_time.strftime('%Y-%m-%d')
            
            if today <= schedule_date <= max_date:
                weather_info = get_weather_for_date(city_location_id, schedule_date)
                if weather_info:
                    schedule.weather_info = weather_info
                    updated_count += 1
        
        db.session.commit()
        return updated_count
        
    except Exception as e:
        db.session.rollback()
        print(f"更新天气失败：{e}")
        return 0