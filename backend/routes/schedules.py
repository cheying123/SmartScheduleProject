from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from extensions import db
from models.schedule import Schedule
from models.user import User
from utils.jwt_utils import token_required
from services.weather_service import get_weather_for_date, get_weather_with_alerts
from services.nlp_parser import parse_natural_language
from services.conflict_detector import detect_schedule_conflicts

from services.weather_service import get_weather_for_date, get_weather_with_alerts
from services.conflict_detector import detect_schedule_conflicts
from services.countdown_service import CountdownService

schedules_bp = Blueprint('schedules', __name__, url_prefix='/api/schedules')


@schedules_bp.route('', methods=['GET'])
@token_required
def get_schedules(current_user):
    """获取当前用户的所有日程，并自动更新天气信息"""
    from datetime import datetime, timedelta
    
    schedules = Schedule.query.filter_by(user_id=current_user.id).order_by(Schedule.start_time.asc()).all()
    
    # 自动更新每个日程的天气信息（未来 7 天内）
    today = datetime.now().strftime('%Y-%m-%d')
    seven_days_later = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    schedule_list = []
    
    for schedule in schedules:
        schedule_date = schedule.start_time.strftime('%Y-%m-%d')
        
        # 检查是否需要更新天气（未来 7 天内没有天气信息的日程）
        needs_weather_update = (
            today <= schedule_date <= seven_days_later and 
            (not schedule.weather_info or '气温' not in schedule.weather_info)
        )
        
        if needs_weather_update:
            try:
                city_location_id = current_user.location or "101010100"
                weather_result = get_weather_with_alerts(city_location_id, schedule_date)
                if weather_result:
                    schedule.weather_info = weather_result['weather_text']
                    print(f"✓ 已更新 {schedule_date} 的天气：{weather_result['weather_text']}")
                    if weather_result['alerts']:
                        print(f"  生成 {len(weather_result['alerts'])} 条智能提醒")
            except Exception as e:
                print(f"✗ 更新天气失败 {schedule_date}: {e}")
        
        # 转换日程为字典格式
        schedule_dict = schedule.to_dict()
        
        # 附加天气提醒信息（如果在未来 7 天内且有提醒）
        if today <= schedule_date <= seven_days_later:
            try:
                city_location_id = current_user.location or "101010100"
                weather_result = get_weather_with_alerts(city_location_id, schedule_date)
                if weather_result and weather_result['alerts']:
                    schedule_dict['weather_alerts'] = weather_result['alerts']
            except:
                pass
        
        # 附加倒计时信息（新增）
        try:
            countdown_info = CountdownService.get_countdown_info(schedule.start_time, 'standard')
            if countdown_info:
                schedule_dict['countdown'] = countdown_info
        except Exception as e:
            print(f"✗ 生成倒计时失败：{e}")
        
        schedule_list.append(schedule_dict)
    
    # 提交天气信息更新
    db.session.commit()
    
    return jsonify(schedule_list)


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
        
        new_schedule = Schedule(
            user_id=current_user.id,
            title=data['title'],
            content=data.get('content', ''),
            start_time=local_dt,
            end_time=datetime.fromisoformat(data['end_time'].replace('Z', '')) if data.get('end_time') else None,
            weather_info=None,
            priority=data.get('priority', 1),
            is_recurring=data.get('is_recurring', False),
            recurring_pattern=data.get('recurring_pattern'),
            tags=data.get('tags')
        )
        db.session.add(new_schedule)
        
        # 如果是未来 7 天内的日程，立即更新天气（包括智能提醒）
        today = datetime.now().strftime('%Y-%m-%d')
        target_date = datetime.strptime(schedule_date, '%Y-%m-%d')
        today_date = datetime.strptime(today, '%Y-%m-%d')
        days_diff = (target_date - today_date).days
        
        # 获取未来 7 天内（包括今天）的天气预报和智能提醒
        if 0 <= days_diff <= 7:
            city_location_id = current_user.location or "101010100"
            try:
                weather_result = get_weather_with_alerts(city_location_id, schedule_date)
                if weather_result:
                    # 存储完整天气信息（包括提醒）
                    new_schedule.weather_info = weather_result['weather_text']
                    print(f"✓ 更新天气成功：{schedule_date} (未来第{days_diff}天)")
                    print(f"   天气：{weather_result['weather_text']}")
                    if weather_result.get('alerts'):
                        print(f"   提醒数量：{len(weather_result['alerts'])}")
            except Exception as e:
                print(f"✗ 更新天气失败 {schedule_date}: {e}")
        
        db.session.commit()
        return jsonify(new_schedule.to_dict()), 201
        
    except ValueError as e:
        return jsonify({'error': f'时间格式错误：{str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'服务器内部错误：{str(e)}'}), 500
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
            
            # 计算日期差，判断是否在未来 7 天内
            today = datetime.now().strftime('%Y-%m-%d')
            target_date = datetime.strptime(schedule_date, '%Y-%m-%d')
            today_date = datetime.strptime(today, '%Y-%m-%d')
            days_diff = (target_date - today_date).days
            
            # 如果是未来 7 天内的日程，更新天气（包括智能提醒）
            if 0 <= days_diff <= 7:
                try:
                    weather_result = get_weather_with_alerts(city_location_id, schedule_date)
                    if weather_result:
                        schedule.weather_info = weather_result['weather_text']
                        print(f"✓ 更新天气成功：{schedule_date} (未来第{days_diff}天)")
                except Exception as e:
                    print(f"✗ 更新天气失败 {schedule_date}: {e}")
        
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
        
        # 计算日期差，判断是否在未来 7 天内
        today = datetime.now().strftime('%Y-%m-%d')
        target_date = datetime.strptime(local_date, '%Y-%m-%d')
        today_date = datetime.strptime(today, '%Y-%m-%d')
        days_diff = (target_date - today_date).days
        
        # 如果是未来 7 天内，获取完整天气信息（包括智能提醒）
        weather_info = None
        if 0 <= days_diff <= 7:
            try:
                weather_result = get_weather_with_alerts(city_location_id, local_date)
                if weather_result:
                    weather_info = weather_result['weather_text']
                    print(f"✓ 自然语言创建 - 天气：{weather_result['weather_text']}")
                    if weather_result.get('alerts'):
                        print(f"   提醒数量：{len(weather_result['alerts'])}")
            except Exception as e:
                print(f"✗ 获取天气失败 {local_date}: {e}")
        
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