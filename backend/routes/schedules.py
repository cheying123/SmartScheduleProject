# NEW_FILE_CODE
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from extensions import db
from models.schedule import Schedule
from models.user import User
from utils.jwt_utils import token_required
from services.weather_service import get_weather_for_date
from services.nlp_parser import parse_natural_language
from services.conflict_detector import detect_schedule_conflicts

schedules_bp = Blueprint('schedules', __name__, url_prefix='/api/schedules')

@schedules_bp.route('', methods=['GET'])
@token_required
def get_schedules(current_user):
    """获取当前用户的所有日程"""
    schedules = Schedule.query.filter_by(user_id=current_user.id).order_by(Schedule.start_time.asc()).all()
    
    # 自动更新天气信息
    today = datetime.now().strftime('%Y-%m-%d')
    max_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    city_location_id = current_user.location or "101010100"
    
    for schedule in schedules:
        schedule_date = schedule.start_time.strftime('%Y-%m-%d')
        if today <= schedule_date <= max_date:
            try:
                weather_info = get_weather_for_date(city_location_id, schedule_date)
                if weather_info:
                    schedule.weather_info = weather_info
            except Exception as e:
                print(f"更新天气失败 {schedule_date}: {e}")
    
    db.session.commit()
    return jsonify([s.to_dict() for s in schedules])


@schedules_bp.route('', methods=['POST'])
@token_required
def create_schedule(current_user):
    """创建新日程"""
    data = request.get_json()
    
    if not data or 'title' not in data or 'start_time' not in data:
        return jsonify({'error': '缺少必要参数 title 或 start_time'}), 400

    try:
        local_dt = datetime.fromisoformat(data['start_time'].replace('Z', ''))
        schedule_date = local_dt.strftime('%Y-%m-%d')
        
        city_location_id = current_user.location or "101010100"
        weather_info = get_weather_for_date(city_location_id, schedule_date)
        
        new_schedule = Schedule(
            user_id=current_user.id,
            title=data['title'],
            content=data.get('content', ''),
            start_time=local_dt,
            end_time=datetime.fromisoformat(data['end_time'].replace('Z', '')) if data.get('end_time') else None,
            weather_info=weather_info,
            priority=data.get('priority', 1),
            is_recurring=data.get('is_recurring', False),
            recurring_pattern=data.get('recurring_pattern'),
            tags=data.get('tags')
        )
        db.session.add(new_schedule)
        db.session.commit()
        
        return jsonify(new_schedule.to_dict()), 201
        
    except ValueError as e:
        return jsonify({'error': f'时间格式错误：{str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'服务器内部错误：{str(e)}'}), 500


@schedules_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_schedule(current_user, id):
    """更新日程"""
    schedule = Schedule.query.get_or_404(id)

    if schedule.user_id != current_user.id:
        return jsonify({'error': '无权操作此日程'}), 403

    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据为空'}), 400
    
    try:
        city_location_id = current_user.location or "101010100"
        
        if 'start_time' in data:
            local_dt = datetime.fromisoformat(data['start_time'].replace('Z', ''))
            
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '')) if data.get('end_time') else local_dt + timedelta(hours=1)
            
            conflicts = detect_schedule_conflicts(
                current_user.id,
                local_dt,
                end_time,
                exclude_id=id
            )
            
            if conflicts:
                return jsonify({
                    'error': '检测到日程冲突',
                    'conflicts': [{
                        'schedule_id': c['schedule_id'],
                        'title': c['title'],
                        'start_time': c['start_time'].strftime('%Y-%m-%dT%H:%M:%SZ')
                    } for c in conflicts]
                }), 409
            
            schedule.start_time = local_dt
            schedule.end_time = end_time
            schedule_date = schedule.start_time.strftime('%Y-%m-%d')
            schedule.weather_info = get_weather_for_date(city_location_id, schedule_date)
        
        if 'title' in data:
            schedule.title = data['title']
        if 'content' in data:
            schedule.content = data['content']
        if 'priority' in data:
            schedule.priority = int(data['priority'])
        if 'is_recurring' in data:
            schedule.is_recurring = bool(data['is_recurring'])
        if 'recurring_pattern' in data:
            schedule.recurring_pattern = data['recurring_pattern']
        if 'tags' in data:
            schedule.tags = data['tags']
        
        db.session.commit()
        return jsonify(schedule.to_dict()), 200
        
    except ValueError as e:
        return jsonify({'error': f'时间格式错误：{str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'服务器内部错误：{str(e)}'}), 500


@schedules_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_schedule(current_user, id):
    """删除日程"""
    try:
        schedule = Schedule.query.get_or_404(id)
        
        if schedule.user_id != current_user.id:
            return jsonify({'error': '无权操作此日程'}), 403
        
        db.session.delete(schedule)
        db.session.commit()
        return jsonify({'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500


@schedules_bp.route('/natural-language', methods=['POST'])
@token_required
def create_schedule_natural(current_user):
    """使用自然语言创建日程"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': '缺少文本指令'}), 400
    
    timezone_offset = data.get('timezone_offset', 480)
    
    try:
        parsed_data = parse_natural_language(data['text'], timezone_offset)
        
        if not parsed_data:
            return jsonify({'error': '解析失败，无法理解您的指令'}), 400
        
        conflicts = detect_schedule_conflicts(
            current_user.id,
            parsed_data['start_time'],
            parsed_data.get('end_time')
        )
        
        if conflicts:
            def utc_to_local(utc_dt):
                if utc_dt is None:
                    return None
                return utc_dt + timedelta(minutes=timezone_offset)
            
            return jsonify({
                'error': '检测到日程冲突',
                'conflicts': [{
                    'schedule_id': c['schedule_id'],
                    'title': c['title'],
                    'start_time': utc_to_local(c['start_time']).strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': utc_to_local(c['end_time']).strftime('%Y-%m-%dT%H:%M:%S') if c['end_time'] else None
                } for c in conflicts],
                'parsed_data': {
                    'title': parsed_data['title'],
                    'start_time': utc_to_local(parsed_data['start_time']).strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': utc_to_local(parsed_data['end_time']).strftime('%Y-%m-%dT%H:%M:%S') if parsed_data['end_time'] else None
                }
            }), 409
        
        local_date = (parsed_data['start_time'] + timedelta(minutes=timezone_offset)).strftime('%Y-%m-%d')
        city_location_id = current_user.location or "101010100"
        weather_info = get_weather_for_date(city_location_id, local_date)
        
        new_schedule = Schedule(
            user_id=current_user.id,
            title=parsed_data['title'],
            content=parsed_data.get('content', ''),
            start_time=parsed_data['start_time'],
            end_time=parsed_data.get('end_time'),
            weather_info=weather_info,
            is_recurring=parsed_data.get('is_recurring', False),
            recurring_pattern=parsed_data.get('recurring_pattern'),
            priority=parsed_data.get('priority', 1),
            tags=parsed_data.get('tags')
        )
        
        db.session.add(new_schedule)
        db.session.commit()
        
        return jsonify({
            'message': '日程创建成功',
            'schedule': new_schedule.to_dict(),
            'ai_parsed': parsed_data.get('ai_parsed', False),
            'timezone_info': {
                'offset_minutes': timezone_offset
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'解析失败：{str(e)}'}), 500


@schedules_bp.route('/check-conflict', methods=['POST'])
@token_required
def check_conflict(current_user):
    """检查指定时间段是否有冲突"""
    data = request.get_json()
    
    if not data or 'start_time' not in data or 'end_time' not in data:
        return jsonify({'error': '缺少开始或结束时间'}), 400
    
    try:
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', ''))
        end_time = datetime.fromisoformat(data['end_time'].replace('Z', ''))
        
        conflicts = detect_schedule_conflicts(current_user.id, start_time, end_time)
        
        return jsonify({
            'has_conflict': len(conflicts) > 0,
            'conflicts': [{
                'schedule_id': c['schedule_id'],
                'title': c['title'],
                'start_time': c['start_time'].strftime('%Y-%m-%dT%H:%M:%SZ'),
                'end_time': c['end_time'].strftime('%Y-%m-%dT%H:%M:%SZ') if c['end_time'] else None
            } for c in conflicts]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500