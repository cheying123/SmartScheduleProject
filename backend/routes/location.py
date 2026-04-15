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


@location_bp.route('/search', methods=['GET'])
@token_required
def search_cities(current_user):
    """搜索城市列表"""
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword or len(keyword) < 1:
        return jsonify({'cities': []}), 200
    
    try:
        QWEATHER_API_KEY = Config.QWEATHER_API_KEY
        
        if not QWEATHER_API_KEY:
            return jsonify({'error': '天气 API Key 未配置'}), 500
        
        # 使用和风天气城市搜索API
        url = f"https://mh78m2gduk.re.qweatherapi.com/geo/v2/city/lookup?location={keyword}&key={QWEATHER_API_KEY}&number=10"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get('code') == '200':
            locations = data.get('location', [])
            
            # 格式化城市列表
            cities = []
            for loc in locations:
                city_info = {
                    'id': loc['id'],
                    'name': loc.get('name', ''),
                    'adm1': loc.get('adm1', ''),  # 省份
                    'adm2': loc.get('adm2', ''),  # 区县
                    'country': loc.get('country', ''),
                    'display_name': _format_city_name(loc)
                }
                cities.append(city_info)
            
            return jsonify({'cities': cities}), 200
        else:
            return jsonify({'cities': [], 'error': '搜索失败'}), 200
            
    except Exception as e:
        print(f"城市搜索失败：{e}")
        return jsonify({'cities': [], 'error': str(e)}), 500


def _format_city_name(location):
    """格式化城市显示名称"""
    adm1 = location.get('adm1', '')
    adm2 = location.get('adm2', '')
    name = location.get('name', '')
    
    # 如果是直辖市或特别行政区，只显示一级行政区 + 城市名
    if adm1 in ['北京', '上海', '天津', '重庆', '香港', '澳门', '台湾']:
        return f"{adm1}{name}" if name != adm1 else adm1
    
    # 普通城市：省份 + 城市 + 区县
    parts = []
    if adm1:
        parts.append(adm1)
    if adm2 and adm2 != name:
        parts.append(adm2)
    if name and name not in parts:
        parts.append(name)
    
    return ''.join(parts) if parts else name
