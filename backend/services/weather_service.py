import logging
import requests
from datetime import datetime, timedelta
from config import Config
from .weather_alert_service import WeatherAlertService

logger = logging.getLogger(__name__)


def get_weather_for_date(city_location_id, date_str):
    if not Config.QWEATHER_API_KEY:
        logger.warning("QWEATHER_API_KEY 未配置")
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
                if forecast.get('fxDate') == date_str:
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

    except Exception:
        logger.exception("天气 API 请求异常")
        return None


def update_schedules_weather_for_user(user_id, city_location_id):
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

    except Exception:
        db.session.rollback()
        logger.exception("更新天气失败")
        return 0


def get_weather_with_alerts(city_location_id, date_str):
    if not Config.QWEATHER_API_KEY:
        logger.warning("QWEATHER_API_KEY 未配置")
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
                if forecast.get('fxDate') == date_str:
                    return _build_weather_result(forecast)

            target_date = datetime.strptime(date_str, '%Y-%m-%d')
            today_date = datetime.strptime(today, '%Y-%m-%d')
            days_diff = (target_date - today_date).days

            if 0 <= days_diff < len(daily_forecasts):
                forecast = daily_forecasts[days_diff]
                return _build_weather_result(forecast)

        return None

    except Exception:
        logger.exception("天气 API 请求异常")
        return None


def _build_weather_result(forecast):
    text_day = forecast.get('textDay', '未知')
    temp_min = forecast.get('tempMin', '?')
    temp_max = forecast.get('tempMax', '?')
    weather_text = f"{text_day}，气温 {temp_min}~{temp_max}℃"
    alerts = WeatherAlertService.get_weather_alerts(forecast)
    return {
        'weather_text': weather_text,
        'alerts': alerts,
        'raw_data': forecast,
    }
