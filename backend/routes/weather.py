from flask import Blueprint, request, jsonify
from utils.jwt_utils import token_required
from services.weather_service import update_schedules_weather_for_user

weather_bp = Blueprint('weather', __name__, url_prefix='/api/weather')

@weather_bp.route('/update-all', methods=['POST'])
@token_required
def update_all_weather(current_user):
    """更新当前用户所有日程的天气信息"""
    try:
        city_location_id = current_user.location or "101010100"
        
        updated_count = update_schedules_weather_for_user(current_user.id, city_location_id)
        
        return jsonify({
            'message': f'已更新 {updated_count} 个日程的天气信息',
            'updated_count': updated_count,
            'city': current_user.location_name or city_location_id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500