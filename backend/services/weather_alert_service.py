from datetime import datetime, timedelta
from config import Config
import requests

class WeatherAlertService:
    """天气智能提醒服务"""
    
    # 天气类型关键词映射
    WEATHER_KEYWORDS = {
        'rain': ['雨', '雷阵雨', '小雨', '中雨', '大雨', '暴雨', '大暴雨', '特大暴雨'],
        'snow': ['雪', '小雪', '中雪', '大雪', '暴雪', '雨夹雪'],
        'fog': ['雾', '霾', '沙尘暴', '扬沙'],
        'wind': ['风', '微风', '大风', '台风', '龙卷风'],
        'storm': ['雷暴', '冰雹', '强对流'],
        'cloudy': ['多云', '阴'],
        'sunny': ['晴', '晴朗']
    }
    
    # 温度阈值配置
    TEMP_THRESHOLDS = {
        'heat_warning': 35,
        'heat_alert': 30,
        'cold_warning': -5,
        'cold_alert': 5,
        'comfortable_min': 18,
        'comfortable_max': 26
    }
    
    # 空气质量指数阈值
    AQI_THRESHOLDS = {
        'excellent': 50,
        'good': 100,
        'light_pollution': 150,
        'moderate_pollution': 200,
        'heavy_pollution': 300
    }
    
    @staticmethod
    def get_weather_alerts(weather_data):
        """根据天气数据生成智能提醒"""
        alerts = []
        
        if not weather_data:
            return alerts
        
        # 1. 降水相关提醒
        precipitation_alerts = WeatherAlertService._check_precipitation(weather_data)
        alerts.extend(precipitation_alerts)
        
        # 2. 温度相关提醒
        temperature_alerts = WeatherAlertService._check_temperature(weather_data)
        alerts.extend(temperature_alerts)
        
        # 3. 风力相关提醒
        wind_alerts = WeatherAlertService._check_wind(weather_data)
        alerts.extend(wind_alerts)
        
        # 4. 紫外线提醒
        uv_alerts = WeatherAlertService._check_uv(weather_data)
        alerts.extend(uv_alerts)
        
        # 5. 空气质量提醒（如果有数据）
        if 'aqi' in weather_data:
            aqi_alerts = WeatherAlertService._check_air_quality(weather_data)
            alerts.extend(aqi_alerts)
        
        # 6. 舒适度提醒
        comfort_alerts = WeatherAlertService._check_comfort(weather_data)
        alerts.extend(comfort_alerts)
        
        return alerts
    
    @staticmethod
    def _check_precipitation(weather_data):
        """检查降水相关提醒"""
        alerts = []
        text_day = weather_data.get('textDay', '')
        
        for keyword in WeatherAlertService.WEATHER_KEYWORDS['rain']:
            if keyword in text_day:
                alerts.append({
                    'type': 'rain_alert',
                    'message': '☔ 今天有雨，出门记得携带雨具！',
                    'priority': 'high',
                    'icon': 'umbrella'
                })
                break
        
        for keyword in WeatherAlertService.WEATHER_KEYWORDS['snow']:
            if keyword in text_day:
                temp_min = int(weather_data.get('tempMin', 10))
                if temp_min < 0:
                    alerts.append({
                        'type': 'snow_alert',
                        'message': '❄️ 今天有降雪且气温较低，注意防寒保暖，出行小心路滑！',
                        'priority': 'high',
                        'icon': 'snowflake'
                    })
                else:
                    alerts.append({
                        'type': 'snow_alert',
                        'message': '❄️ 今天有降雪，出行注意交通安全！',
                        'priority': 'medium',
                        'icon': 'snowflake'
                    })
                break
        
        for keyword in WeatherAlertService.WEATHER_KEYWORDS['storm']:
            if keyword in text_day:
                alerts.append({
                    'type': 'storm_alert',
                    'message': '⛈️ 今天有强对流天气，请注意安全，尽量避免户外活动！',
                    'priority': 'high',
                    'icon': 'thunderstorm'
                })
                break
        
        for keyword in WeatherAlertService.WEATHER_KEYWORDS['fog']:
            if keyword in text_day:
                alerts.append({
                    'type': 'fog_alert',
                    'message': '🌫️ 今天有雾/霾，能见度较低，出行注意安全，建议佩戴口罩！',
                    'priority': 'medium',
                    'icon': 'cloud'
                })
                break
        
        return alerts
    
    @staticmethod
    def _check_temperature(weather_data):
        """检查温度相关提醒"""
        alerts = []
        temp_max = int(weather_data.get('tempMax', 25))
        temp_min = int(weather_data.get('tempMin', 15))
        
        if temp_max >= WeatherAlertService.TEMP_THRESHOLDS['heat_warning']:
            alerts.append({
                'type': 'heat_warning',
                'message': f'🌡️ 高温预警！最高气温达{temp_max}℃，请注意防暑降温，避免长时间户外活动！',
                'priority': 'high',
                'icon': 'sun'
            })
        elif temp_max >= WeatherAlertService.TEMP_THRESHOLDS['heat_alert']:
            alerts.append({
                'type': 'heat_alert',
                'message': f'☀️ 天气较热，最高气温{temp_max}℃，注意补充水分，适当减少户外活动。',
                'priority': 'medium',
                'icon': 'sun'
            })
        
        if temp_min <= WeatherAlertService.TEMP_THRESHOLDS['cold_warning']:
            alerts.append({
                'type': 'cold_warning',
                'message': f'🥶 严寒预警！最低气温{temp_min}℃，请注意防寒保暖，预防感冒！',
                'priority': 'high',
                'icon': 'snowflake'
            })
        elif temp_min <= WeatherAlertService.TEMP_THRESHOLDS['cold_alert']:
            alerts.append({
                'type': 'cold_alert',
                'message': f'🧥 天气较冷，最低气温{temp_min}℃，注意添衣保暖。',
                'priority': 'medium',
                'icon': 'snowflake'
            })
        
        temp_diff = temp_max - temp_min
        if temp_diff > 10:
            alerts.append({
                'type': 'temp_difference_alert',
                'message': f'📊 昼夜温差较大（{temp_diff}℃），建议采用"洋葱式"穿衣法，适时增减衣物。',
                'priority': 'medium',
                'icon': 'thermometer'
            })
        
        return alerts
    
    @staticmethod
    def _check_wind(weather_data):
        """检查风力相关提醒"""
        alerts = []
        wind_scale = weather_data.get('windScale', '')
        
        try:
            wind_level = int(wind_scale.replace('级', '')) if wind_scale else 0
        except:
            wind_level = 0
        
        if wind_level >= 7:
            alerts.append({
                'type': 'strong_wind_warning',
                'message': f'💨 大风预警！风力{wind_level}级，请避免户外活动，远离广告牌和临时建筑物！',
                'priority': 'high',
                'icon': 'wind'
            })
        elif wind_level >= 5:
            alerts.append({
                'type': 'wind_alert',
                'message': f'🍃 风力较大（{wind_level}级），外出时注意固定好随身物品。',
                'priority': 'medium',
                'icon': 'wind'
            })
        
        return alerts
    
    @staticmethod
    def _check_uv(weather_data):
        """检查紫外线提醒"""
        alerts = []
        uv_index = weather_data.get('uvIndex', '')
        
        try:
            uv_level = int(uv_index) if uv_index else 0
        except:
            uv_level = 0
        
        if uv_level >= 8:
            alerts.append({
                'type': 'uv_warning',
                'message': '☀️ 紫外线强度很强！外出请做好防晒措施（防晒霜、遮阳伞、太阳镜）。',
                'priority': 'high',
                'icon': 'sun'
            })
        elif uv_level >= 5:
            alerts.append({
                'type': 'uv_alert',
                'message': '🌞 紫外线较强，建议涂抹防晒霜，戴帽子或太阳镜。',
                'priority': 'medium',
                'icon': 'sun'
            })
        
        return alerts
    
    @staticmethod
    def _check_air_quality(weather_data):
        """检查空气质量提醒"""
        alerts = []
        aqi = weather_data.get('aqi', None)
        
        if aqi is None:
            return alerts
        
        thresholds = WeatherAlertService.AQI_THRESHOLDS
        
        if aqi <= thresholds['excellent']:
            alerts.append({
                'type': 'air_excellent',
                'message': '🌿 空气质量优，非常适合户外运动和开窗通风！',
                'priority': 'low',
                'icon': 'leaf'
            })
        elif aqi <= thresholds['good']:
            alerts.append({
                'type': 'air_good',
                'message': '✅ 空气质量良好，可以正常进行户外活动。',
                'priority': 'low',
                'icon': 'check-circle'
            })
        elif aqi <= thresholds['light_pollution']:
            alerts.append({
                'type': 'air_light_pollution',
                'message': '⚠️ 空气质量轻度污染，敏感人群应减少户外活动。',
                'priority': 'medium',
                'icon': 'alert-triangle'
            })
        elif aqi <= thresholds['moderate_pollution']:
            alerts.append({
                'type': 'air_moderate_pollution',
                'message': '😷 空气质量中度污染，建议减少户外活动，外出佩戴口罩。',
                'priority': 'high',
                'icon': 'mask'
            })
        else:
            alerts.append({
                'type': 'air_heavy_pollution',
                'message': '🚨 空气质量重度污染！请避免户外活动，关闭门窗，使用空气净化器。',
                'priority': 'high',
                'icon': 'alert-circle'
            })
        
        return alerts
    
    @staticmethod
    def _check_comfort(weather_data):
        """检查舒适度提醒"""
        alerts = []
        temp_max = int(weather_data.get('tempMax', 25))
        temp_min = int(weather_data.get('tempMin', 15))
        humidity = int(weather_data.get('humidity', 50))
        
        avg_temp = (temp_max + temp_min) / 2
        
        min_comfort = WeatherAlertService.TEMP_THRESHOLDS['comfortable_min']
        max_comfort = WeatherAlertService.TEMP_THRESHOLDS['comfortable_max']
        
        if min_comfort <= avg_temp <= max_comfort and 40 <= humidity <= 70:
            alerts.append({
                'type': 'comfort_good',
                'message': '😊 今天体感舒适，温度和湿度都很适宜，保持好心情！',
                'priority': 'low',
                'icon': 'smile'
            })
        
        if humidity > 80:
            alerts.append({
                'type': 'humidity_high',
                'message': f'💧 空气湿度较大（{humidity}%），体感闷热，注意通风除湿。',
                'priority': 'medium',
                'icon': 'droplet'
            })
        elif humidity < 30:
            alerts.append({
                'type': 'humidity_low',
                'message': f'🏜️ 空气干燥（{humidity}%），注意补水和皮肤保湿，可使用加湿器。',
                'priority': 'medium',
                'icon': 'droplet'
            })
        
        return alerts


def generate_weather_alerts(weather_data):
    """生成天气智能提醒的便捷函数"""
    return WeatherAlertService.get_weather_alerts(weather_data)