from flask import Blueprint, request, jsonify
from extensions import db
from models.user import User
from utils.jwt_utils import token_required
from services.weather_service import update_schedules_weather_for_user
import requests
from config import Config

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取用户个人资料"""
    return jsonify(current_user.to_dict()), 200


@users_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """更新用户个人资料"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据为空'}), 400
    
    try:
        old_location = current_user.location
        
        if 'username' in data:
            current_user.username = data['username']
        if 'email' in data:
            current_user.email = data['email']
        if 'location' in data:
            current_user.location = data['location']
            if data.get('location_name'):
                current_user.location_name = data['location_name']
        if 'weather_alerts_enabled' in data:
            current_user.weather_alerts_enabled = data['weather_alerts_enabled']
        
        # 处理工作时间偏好
        if 'preferred_work_hours' in data:
            current_user.preferred_work_hours = data['preferred_work_hours']
        
        db.session.commit()
        
        result = current_user.to_dict()
        
        if old_location != current_user.location and current_user.location:
            updated_count = update_schedules_weather_for_user(current_user.id, current_user.location)
            result['weather_updated'] = True
            result['updated_count'] = updated_count
            result['message'] = f'城市已更新，已同步更新 {updated_count} 个日程的天气信息'
        else:
            result['weather_updated'] = False
        
        return jsonify(result), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500