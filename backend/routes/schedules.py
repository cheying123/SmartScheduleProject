from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import traceback
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
from services.recurring_service import RecurringService  # ← 新增导入

from services.conflict_detector import ConflictDetector

# 将第三方库的导入移到前面
from icalendar import Calendar, Event
import pytz

schedules_bp = Blueprint('schedules', __name__, url_prefix='/api/schedules')


@schedules_bp.route('', methods=['GET'])
@token_required
def get_schedules(current_user):
    """获取当前用户的所有日程，并自动更新天气信息，自动更新过期重复日程"""

    # ⚡ 核心改动：在返回数据前，先执行重复日程检查
    try:
        RecurringService.process_recurring_schedules()
    except Exception as e:
        print(f"⚠️ 自动更新重复日程失败: {e}")

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
        
        # 【新增】计算结束时间
        end_dt = None
        if data.get('end_time'):
            end_dt = datetime.fromisoformat(data['end_time'].replace('Z', ''))
        else:
            end_dt = local_dt + timedelta(hours=1)
        
        # 【新增】冲突检测
        conflicts = ConflictDetector.detect_conflicts(
            current_user.id,
            local_dt,
            end_dt
        )
        
        if conflicts:
            # 【新增】当检测到冲突时，自动生成建议方案
            duration = 60
            if data.get('end_time'):
                duration = int((end_dt - local_dt).total_seconds() / 60)
            
            suggestions = ConflictDetector.suggest_alternative_slots(
                current_user.id, 
                local_dt, 
                duration
            )
            
            def utc_to_local(utc_dt):
                if utc_dt is None:
                    return None
                timezone_offset = data.get('timezone_offset', 480)
                return utc_dt + timedelta(minutes=timezone_offset)
            
            return jsonify({
                'error': '检测到日程冲突',
                'conflicts': [{
                    'schedule_id': c['schedule_id'],
                    'title': c['title'],
                    'start_time': utc_to_local(c['start_time']).strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': utc_to_local(c['end_time']).strftime('%Y-%m-%dT%H:%M:%S') if c['end_time'] else None
                } for c in conflicts],
                'suggestions': [{
                    'start_time': utc_to_local(datetime.fromisoformat(s['start_time'])).strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': utc_to_local(datetime.fromisoformat(s['end_time'])).strftime('%Y-%m-%dT%H:%M:%S'),
                    'reason': s['reason']
                } for s in suggestions],
                'parsed_data': {
                    'title': data['title'],
                    'start_time': utc_to_local(local_dt).strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': utc_to_local(end_dt).strftime('%Y-%m-%dT%H:%M:%S') if end_dt else None
                }
            }), 409
        
        new_schedule = Schedule(
            user_id=current_user.id,
            title=data['title'],
            content=data.get('content', ''),
            start_time=local_dt,
            end_time=end_dt if data.get('end_time') else None,
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
            
            # 处理结束时间：如果有值则转换，如果是空字符串则设为 None，否则默认为开始时间后 1 小时
            if data.get('end_time') and data['end_time'].strip():
                end_time = datetime.fromisoformat(data['end_time'].replace('Z', ''))
            elif data.get('end_time') == '':
                end_time = None
            else:
                end_time = local_dt + timedelta(hours=1)
            
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
    """使用自然语言创建日程（直接创建）"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': '缺少文本指令'}), 400
    
    timezone_offset = data.get('timezone_offset', 480)
    
    try:
        parsed_data = parse_natural_language(data['text'], timezone_offset)
        
        if not parsed_data:
            return jsonify({'error': '解析失败，无法理解您的指令'}), 400
        
        # 使用新的 ConflictDetector 类进行检测
        conflicts = ConflictDetector.detect_conflicts(
            current_user.id,
            parsed_data['start_time'],
            parsed_data.get('end_time') or (parsed_data['start_time'] + timedelta(hours=1))
        )
        
        if conflicts:

            # 【新增】当检测到冲突时，自动生成建议方案
            duration = 60
            if parsed_data.get('end_time'):
                duration = int((parsed_data['end_time'] - parsed_data['start_time']).total_seconds() / 60)
            
            suggestions = ConflictDetector.suggest_alternative_slots(
                current_user.id, 
                parsed_data['start_time'], 
                duration
            )
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
                'suggestions': [{
                    'start_time': utc_to_local(datetime.fromisoformat(s['start_time'])).strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': utc_to_local(datetime.fromisoformat(s['end_time'])).strftime('%Y-%m-%dT%H:%M:%S'),
                    'reason': s['reason']
                } for s in suggestions], # 【新增】返回建议列表
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


@schedules_bp.route('/nlp-parse', methods=['POST'])
@token_required
def parse_natural_language_only(current_user):
    """仅解析自然语言，不创建日程（用于预填表单）"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': '缺少文本指令'}), 400
    
    timezone_offset = data.get('timezone_offset', 480)
    
    try:
        parsed_data = parse_natural_language(data['text'], timezone_offset)
        
        if not parsed_data:
            return jsonify({'error': '解析失败，无法理解您的指令'}), 400
        
        # 转换为本地时间格式供前端显示
        def utc_to_local_iso(utc_dt):
            if utc_dt is None:
                return ''
            local_dt = utc_dt + timedelta(minutes=timezone_offset)
            return local_dt.strftime('%Y-%m-%dT%H:%M')
        
        # 返回解析结果，但不创建数据库记录
        result = {
            'title': parsed_data['title'],
            'content': parsed_data.get('content', ''),
            'start_time': utc_to_local_iso(parsed_data['start_time']),
            'end_time': utc_to_local_iso(parsed_data.get('end_time')),
            'priority': parsed_data.get('priority', 1),
            'is_recurring': parsed_data.get('is_recurring', False),
            'recurring_pattern': parsed_data.get('recurring_pattern'),
            'tags': parsed_data.get('tags', []),
            'ai_parsed': parsed_data.get('ai_parsed', False),
            'confidence': 'high' if parsed_data.get('ai_parsed') else 'medium'
        }
        
        return jsonify(result), 200
        
    except Exception as e:
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
    

@schedules_bp.route('/force-create', methods=['POST'])
@token_required
def force_create_schedule(current_user):
    """强制创建日程（忽略冲突）"""
    data = request.get_json()
    
    if not data or 'title' not in data or 'start_time' not in data:
        return jsonify({'error': '缺少必要参数 title 或 start_time'}), 400
    
    try:
        # 解析时间
        local_dt = datetime.fromisoformat(data['start_time'].replace('Z', ''))
        
        # 处理结束时间
        end_time = None
        if data.get('end_time') and data['end_time'].strip():
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', ''))
        elif data.get('end_time') == '':
            end_time = None
        else:
            end_time = local_dt + timedelta(hours=1)
        
        # 创建日程（不检查冲突）
        new_schedule = Schedule(
            user_id=current_user.id,
            title=data['title'],
            content=data.get('content', ''),
            start_time=local_dt,
            end_time=end_time,
            weather_info=None,
            priority=data.get('priority', 1),
            is_recurring=data.get('is_recurring', False),
            recurring_pattern=data.get('recurring_pattern'),
            tags=data.get('tags')
        )
        
        db.session.add(new_schedule)
        
        # 如果是未来 7 天内的日程，更新天气
        schedule_date = local_dt.strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        target_date = datetime.strptime(schedule_date, '%Y-%m-%d')
        today_date = datetime.strptime(today, '%Y-%m-%d')
        days_diff = (target_date - today_date).days
        
        if 0 <= days_diff <= 7:
            city_location_id = current_user.location or "101010100"
            try:
                weather_result = get_weather_with_alerts(city_location_id, schedule_date)
                if weather_result:
                    new_schedule.weather_info = weather_result['weather_text']
                    print(f"✓ 强制创建 - 更新天气成功：{schedule_date}")
            except Exception as e:
                print(f"✗ 强制创建 - 更新天气失败 {schedule_date}: {e}")
        
        db.session.commit()
        
        return jsonify({
            'message': '日程创建成功（已忽略冲突）',
            'schedule': new_schedule.to_dict(),
            'conflict_ignored': True
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'时间格式错误：{str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"❌ 强制创建失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'服务器内部错误：{str(e)}'}), 500


@schedules_bp.route('/<int:id>/complete', methods=['PATCH'])
@token_required
def mark_schedule_complete(current_user, id):
    """标记日程为已完成/未完成"""
    schedule = Schedule.query.get_or_404(id)
    
    if schedule.user_id != current_user.id:
        return jsonify({'error': '无权操作此日程'}), 403
    
    # 直接切换完成状态，不需要请求体
    schedule.is_completed = not schedule.is_completed
    
    db.session.commit()
    
    return jsonify({
        'message': '状态更新成功',
        'schedule': schedule.to_dict()
    }), 200

@schedules_bp.route('/export', methods=['GET', 'POST'])
@token_required
def export_schedules(current_user):
    """导出用户的日程为iCalendar格式"""
    try:
        # 根据请求方法处理参数
        if request.method == 'GET':
            # GET请求：使用查询参数
            include_recurring = request.args.get('include_recurring', 'true').lower() == 'true'
            include_expired = request.args.get('include_expired', 'true').lower() == 'true'
            include_completed = request.args.get('include_completed', 'true').lower() == 'true'
            start_date = request.args.get('start', None)
            end_date = request.args.get('end', None)
            
            # 获取筛选参数
            schedule_ids = request.args.getlist('ids')  # 支持多个ID参数
        else:  # POST请求
            # POST请求：使用JSON或表单数据，支持ID列表
            if request.is_json:
                data = request.get_json()
            else:
                # 处理表单数据
                data = dict(request.form)
                
                # 特殊处理 schedule_ids，因为可能有多个同名参数
                schedule_ids_from_form = request.form.getlist('schedule_ids')
                if schedule_ids_from_form:
                    data['schedule_ids'] = schedule_ids_from_form

            include_recurring = data.get('include_recurring', True)
            include_expired = data.get('include_expired', True)
            include_completed = data.get('include_completed', True)
            start_date = data.get('start_date') or data.get('start')
            end_date = data.get('end_date') or data.get('end')
            schedule_ids = data.get('schedule_ids', [])  # 从请求体获取ID列表
            
            # 确保schedule_ids是列表格式
            if isinstance(schedule_ids, str):
                schedule_ids = [int(id) for id in schedule_ids.split(',') if id.strip()]
            elif isinstance(schedule_ids, list):
                # 如果是列表，需要处理每个元素（可能来自表单的数据是字符串）
                schedule_ids = [int(id) for id in schedule_ids if id]
        
        # 构建查询
        query = Schedule.query.filter_by(user_id=current_user.id)
        
        # 如果提供了ID列表，则只查询这些ID
        if schedule_ids:
            schedule_ids = [int(id) for id in schedule_ids]
            query = query.filter(Schedule.id.in_(schedule_ids))
        else:
            # 否则使用其他筛选条件
            # 根据是否包含重复日程进行筛选
            if not include_recurring:
                query = query.filter(Schedule.is_recurring == False)
            
            # 根据时间范围筛选
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Schedule.start_time >= start_dt)
            
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # 包含结束日期的整天
                query = query.filter(Schedule.start_time < end_dt)
            
            # 根据是否包含过期日程进行筛选
            if not include_expired:
                now = datetime.now()
                query = query.filter(Schedule.start_time >= now)
                
            # 根据是否包含已完成日程进行筛选
            if not include_completed:
                query = query.filter(Schedule.is_completed == False)
        
        # 获取用户的所有符合条件的日程
        schedules = query.order_by(Schedule.start_time.asc()).all()
        
        # 创建iCalendar对象
        cal = Calendar()
        cal.add('prodid', '-//SmartSchedule//Schedule Export//EN')
        cal.add('version', '2.0')
        
        # 时区设置
        beijing_tz = pytz.timezone('Asia/Shanghai')
        
        for schedule in schedules:
            event = Event()
            event.add('uid', f"{schedule.id}@smartschedule")
            event.add('summary', schedule.title)
            event.add('dtstart', beijing_tz.localize(schedule.start_time))
            
            # 如果有结束时间，则添加
            if schedule.end_time:
                event.add('dtend', beijing_tz.localize(schedule.end_time))
            else:
                # 如果没有结束时间，默认为开始时间后1小时
                event.add('dtend', beijing_tz.localize(schedule.start_time + timedelta(hours=1)))
            
            # 添加描述
            if schedule.content:
                event.add('description', schedule.content)
            
            # 添加位置
            if schedule.location:
                event.add('location', schedule.location)
                
            # 添加创建时间
            event.add('dtstamp', datetime.now(pytz.utc))
            
            # 添加循环规则（如果日程是循环的）
            if schedule.is_recurring and schedule.recurring_pattern:
                # 将中文循环模式转换为iCalendar标准的RRULE
                if schedule.recurring_pattern == 'daily':
                    event.add('rrule', {'FREQ': 'DAILY'})
                elif schedule.recurring_pattern == 'weekly':
                    event.add('rrule', {'FREQ': 'WEEKLY'})
                elif schedule.recurring_pattern == 'monthly':
                    event.add('rrule', {'FREQ': 'MONTHLY'})
                elif schedule.recurring_pattern == 'yearly':
                    event.add('rrule', {'FREQ': 'YEARLY'})
            
            cal.add_component(event)
        
        # 返回iCalendar数据
        return cal.to_ical(), 200, {
            'Content-Type': 'text/calendar; charset=utf-8',
            'Content-Disposition': 'attachment; filename=schedules.ics'
        }
        
    except Exception as e:
        print(f"导出日程失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '导出日程失败'}), 500

@schedules_bp.route('/import', methods=['POST'])
@token_required
def import_schedules(current_user):
    """导入iCalendar格式的日程"""
    try:
        # 检查请求中是否包含文件
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
            
        if not file.filename.endswith(('.ics', '.ical', '.ifb')):
            return jsonify({'error': '不支持的文件格式，请上传.ics文件'}), 400

        # 读取并解析iCalendar文件
        ics_content = file.read().decode('utf-8')
        calendar = Calendar.from_ical(ics_content)
        
        imported_count = 0
        skipped_count = 0
        
        # 时区设置
        beijing_tz = pytz.timezone('Asia/Shanghai')
        
        for component in calendar.walk():
            if component.name == "VEVENT":
                # 提取事件信息
                title = str(component.get('summary', ''))
                description = str(component.get('description', ''))
                location = str(component.get('location', ''))
                
                # 处理开始时间
                dtstart = component.get('dtstart').dt
                if isinstance(dtstart, datetime):
                    # 如果是带时区的时间，转换为本地时间
                    if dtstart.tzinfo is not None:
                        dtstart = dtstart.astimezone(beijing_tz)
                    else:
                        # 如果没有时区信息，假定为北京时间
                        dtstart = beijing_tz.localize(dtstart)
                    start_time = dtstart.replace(tzinfo=None)  # 转换为naive datetime
                else:
                    # 如果是date类型，转换为datetime
                    start_time = datetime.combine(dtstart, datetime.min.time())
                
                # 处理结束时间
                dtend_val = component.get('dtend')
                if dtend_val:
                    dtend = dtend_val.dt
                    if isinstance(dtend, datetime):
                        if dtend.tzinfo is not None:
                            dtend = dtend.astimezone(beijing_tz)
                        else:
                            dtend = beijing_tz.localize(dtend)
                        end_time = dtend.replace(tzinfo=None)
                    else:
                        end_time = datetime.combine(dtend, datetime.min.time())
                else:
                    # 如果没有结束时间，默认为开始时间后1小时
                    end_time = start_time + timedelta(hours=1)
                
                # 检查是否已存在相同标题和时间段的日程（避免重复导入）
                # 使用标题、开始时间和结束时间的组合来判断重复
                existing_schedule = Schedule.query.filter(
                    Schedule.title == title,
                    Schedule.start_time == start_time,
                    Schedule.end_time == end_time,
                    Schedule.user_id == current_user.id
                ).first()
                
                if existing_schedule:
                    # 如果已存在，则跳过
                    skipped_count += 1
                    continue
                
                # 创建新的日程
                new_schedule = Schedule(
                    title=title,
                    content=description,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    user_id=current_user.id
                    # 不设置uid，因为数据库中不存在该字段
                )
                
                # 如果有提醒时间，可以尝试解析
                alarms = component.get('valarm', [])
                if alarms:
                    # 目前简化处理，可以根据需要添加提醒逻辑
                    pass
                
                db.session.add(new_schedule)
                imported_count += 1
        
        # 提交到数据库
        db.session.commit()
        
        return jsonify({
            'message': f'成功导入 {imported_count} 个日程，跳过 {skipped_count} 个重复日程',
            'imported_count': imported_count,
            'skipped_count': skipped_count
        }), 200
        
    except UnicodeDecodeError:
        return jsonify({'error': '文件编码错误，请确保文件是UTF-8编码'}), 400
    except ValueError as e:
        return jsonify({'error': f'iCalendar格式错误: {str(e)}'}), 400
    except Exception as e:
        print(f"导入日程失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '导入日程失败'}), 500
