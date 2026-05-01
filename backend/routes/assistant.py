import logging
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.weather_service import get_weather_for_date
from services.ai_service import AIService
from models.schedule import Schedule
from models.user import User
from extensions import db
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

assistant_bp = Blueprint('assistant', __name__)


@assistant_bp.route('/daily-briefing', methods=['GET'])
@jwt_required()
def get_daily_briefing():
    user_id = get_jwt_identity()
    now_beijing = datetime.utcnow() + timedelta(hours=8)
    today_str = now_beijing.strftime('%Y-%m-%d')

    try:
        user = User.query.get(user_id)
        city_location_id = user.location if user and user.location else "101010100"
        city_name = user.location_name if user and user.location_name else "北京"

        logger.debug("为用户 %s 获取 %s (%s) 的天气", user.username if user else '?', city_name, city_location_id)

        start_utc = now_beijing.replace(hour=0, minute=0, second=0) - timedelta(hours=8)
        end_utc = start_utc + timedelta(days=1)

        schedules = Schedule.query.filter(
            Schedule.user_id == user_id,
            Schedule.start_time >= start_utc,
            Schedule.start_time < end_utc,
        ).order_by(Schedule.start_time).all()

        weather_text = get_weather_for_date(city_location_id, today_str)

        schedule_summary = []
        for s in schedules:
            local_time = s.start_time + timedelta(hours=8)
            schedule_summary.append(f"{local_time.strftime('%H:%M')} {s.title}")

        context = f"今天在{city_name}有 {len(schedules)} 个日程：{', '.join(schedule_summary)}。天气：{weather_text or '未知'}。"

        ai_advice = f"祝您在{city_name}度过充满活力的一天！"
        try:
            ai_service = AIService()
            if ai_service.api_key:
                prompt = f"作为一个日程助手，根据以下信息给用户一句简短的晨间建议（50字以内）：{context}"
                response = ai_service.chat([{'role': 'user', 'content': prompt}])
                if response and not response.startswith("抱歉") and not response.startswith("⚠️"):
                    ai_advice = response
        except Exception:
            logger.exception("AI 建议生成失败")

        weather_obj = {'text': '未知', 'temperature': '--'}
        if weather_text:
            parts = weather_text.split('，')
            weather_obj['text'] = parts[0]
            if len(parts) > 1:
                temp_part = parts[1].replace('气温 ', '').replace('℃', '')
                weather_obj['temperature'] = temp_part

        return jsonify({
            'date': today_str,
            'schedule_count': len(schedules),
            'schedules': [{'id': s.id, 'title': s.title, 'time': (s.start_time + timedelta(hours=8)).isoformat()} for s in schedules],
            'weather': weather_obj,
            'ai_advice': ai_advice,
        }), 200

    except Exception:
        logger.exception("获取每日简报失败")
        return jsonify({'error': '获取每日简报失败，请稍后重试'}), 500
