# NEW_FILE_CODE
from flask import Blueprint, request, jsonify
from utils.jwt_utils import token_required
import requests
from config import Config

location_bp = Blueprint('location', __name__, url_prefix='/api/location')

@location_bp.route('/geocode', methods=['POST'])
@token_required
def geocode_location(current_user):
    """根据经纬度获取城市信息"""
    data = request.get_json()
    
    if not data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': '缺少经纬度参数'}), 400
    
    try:
        latitude = data['latitude']
        longitude = data['longitude']
        
        QWEATHER_API_KEY = Config.QWEATHER_API_KEY
        
        if not QWEATHER_API_KEY:
            return jsonify({'error': '天气 API Key 未配置'}), 500
        
        url = f"https://mh78m2gduk.re.qweatherapi.com/geo/v2/city/lookup?location={longitude},{latitude}&key={QWEATHER_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get('code') == '200' and len(data.get('location', [])) > 0:
            location_info = data['location'][0]
            city_id = location_info['id']
            adm1 = location_info.get('adm1', '')
            adm2 = location_info.get('adm2', '')
            city_name = f"{adm1}{adm2}" if adm1 and adm2 else location_info.get('name', city_id)
            
            return jsonify({
                'city_location_id': city_id,
                'city_name': city_name,
                'latitude': latitude,
                'longitude': longitude
            }), 200
        else:
            return jsonify({'error': '无法解析地理位置'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500