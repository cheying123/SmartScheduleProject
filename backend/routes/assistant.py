from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.weather_service import get_weather_for_date
from services.ai_service import AIService
from models.schedule import Schedule
from models.user import User # ✅ 新增：导入 User 模型
from extensions import db
from datetime import datetime, timedelta

assistant_bp = Blueprint('assistant', __name__)

@assistant_bp.route('/daily-briefing', methods=['GET'])
@jwt_required()
def get_daily_briefing():
    user_id = get_jwt_identity()
    
    # ✅ 修复：使用北京时间 (UTC+8) 来确定“今天”是哪一天
    now_beijing = datetime.utcnow() + timedelta(hours=8)
    today_str = now_beijing.strftime('%Y-%m-%d')
    
    try:
        # 1. 获取用户信息以提取城市 ID
        user = User.query.get(user_id)
        # 如果用户没设置城市，默认用北京；否则用用户设置的城市 ID
        city_location_id = user.location if user and user.location else "101010100"
        city_name = user.location_name if user and user.location_name else "北京"
        
        print(f"🌍 为用户 {user.username} 获取 {city_name} ({city_location_id}) 的天气")

        # 2. 获取今日日程 (注意：数据库存的是 UTC，查询时要用 UTC 范围)
        start_utc = now_beijing.replace(hour=0, minute=0, second=0) - timedelta(hours=8)
        end_utc = start_utc + timedelta(days=1)
        
        schedules = Schedule.query.filter(
            Schedule.user_id == user_id,
            Schedule.start_time >= start_utc,
            Schedule.start_time < end_utc
        ).order_by(Schedule.start_time).all()
        
        # 3. 获取天气 (使用用户所在城市的 ID)
        weather_text = get_weather_for_date(city_location_id, today_str)
        
        # 4. 构建上下文给 AI
        schedule_summary = []
        for s in schedules:
            local_time = s.start_time + timedelta(hours=8)
            schedule_summary.append(f"{local_time.strftime('%H:%M')} {s.title}")
            
        context = f"今天在{city_name}有 {len(schedules)} 个日程：{', '.join(schedule_summary)}。天气：{weather_text or '未知'}。"
        
        # 5. 调用 AI
        ai_advice = f"祝您在{city_name}度过充满活力的一天！"
        try:
            ai_service = AIService()
            if ai_service.api_key:
                prompt = f"作为一个日程助手，根据以下信息给用户一句简短的晨间建议（50字以内）：{context}"
                response = ai_service.chat([{'role': 'user', 'content': prompt}])
                if response and not response.startswith("抱歉") and not response.startswith("⚠️"):
                    ai_advice = response
        except Exception as e:
            print(f"AI 建议生成失败: {e}")

        # 6. 解析天气
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
            'ai_advice': ai_advice
        }), 200
        
    except Exception as e:
        print(f"❌ 获取每日简报失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500