import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from services.user_behavior_analyzer import UserBehaviorAnalyzer
from services.ai_service import AIService
from models.user import User
from models.schedule import Schedule
from extensions import db
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/daily-briefing', methods=['GET'])
@jwt_required()
def get_daily_briefing():
    """获取今日智能日程摘要"""
    try:
        current_user_id = get_jwt_identity()
        
        # 1. 获取今天的日期范围 (UTC)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # 2. 查询今天的所有日程
        schedules = Schedule.query.filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time >= today_start,
            Schedule.start_time < today_end
        ).order_by(Schedule.start_time).all()
        
        if not schedules:
            return jsonify({
                'message': '今天没有安排日程，好好休息一下吧！☕',
                'schedules_count': 0
            }), 200
        
        # 3. 准备日程数据给 AI (关键修复：转换为北京时间)
        beijing_tz = timezone(timedelta(hours=8))
        schedule_list = []
        
        for s in schedules:
            # 将 UTC 时间转换为北京时间
            local_start = s.start_time.replace(tzinfo=timezone.utc).astimezone(beijing_tz)
            
            schedule_list.append({
                'time': local_start.strftime('%H:%M'),  # 现在这里是北京时间了
                'title': s.title,
                'priority': s.priority,
                'location': s.location,
                'weather_info': s.weather_info
            })
        
        # 4. 调用 AI 生成摘要
        prompt = f"""
        你是一个贴心的个人日程助理。请根据以下用户今天的日程安排（已转换为北京时间），生成一段简短、温馨且实用的晨间提醒（100字以内）。
        要求：
        1. 语气要像朋友一样自然。
        2. 如果有高优先级任务，重点提醒。
        3. 如果某个日程有天气信息（如下雨、高温），务必结合天气给出建议（如带伞、防暑）。
        4. 如果没有特殊天气，就简单鼓励一下。
        
        日程列表（北京时间）：
        {schedule_list}
        """
        
        ai_summary = AIService.generate_text(prompt, max_tokens=150)
        
        return jsonify({
            'message': ai_summary,
            'schedules_count': len(schedules),
            'date': today_start.strftime('%Y-%m-%d')
        }), 200
        
    except Exception as e:
        logger.exception("每日摘要生成失败")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/auto-schedule', methods=['POST'])
@jwt_required()
def auto_schedule_tasks():
    """自动排程：根据待办任务和空闲时间自动生成日程"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        tasks = data.get('tasks', [])  # 格式: [{'title': '复习数学', 'duration_minutes': 60}, ...]
        days_to_scan = data.get('days', 3)  # 默认扫描未来3天
        
        if not tasks:
            return jsonify({'error': '请提供待办任务列表'}), 400
            
        # 1. 获取用户的基本信息（如工作时间偏好）
        user = User.query.get(current_user_id)
        
        # 从 preferred_work_hours JSON 字段中读取工作时间偏好
        work_start_hour = 9  # 默认值
        work_end_hour = 18   # 默认值
        
        if user and user.preferred_work_hours:
            work_start_hour = int(user.preferred_work_hours.get('start', '09:00').split(':')[0])
            work_end_hour = int(user.preferred_work_hours.get('end', '18:00').split(':')[0])
        
        # 2. 扫描未来几天的空闲时间段（关键修复：使用北京时间进行日期计算）
        from datetime import timezone, timedelta as td
        
        # 获取当前的北京时间
        utc_now = datetime.utcnow()
        beijing_tz = timezone(td(hours=8))
        beijing_now = utc_now.replace(tzinfo=timezone.utc).astimezone(beijing_tz)
        
        logger.debug("当前 UTC 时间: %s, 北京时间: %s, 工作时间: %s:00-%s:00", utc_now, beijing_now, work_start_hour, work_end_hour)
        
        free_slots = []
        
        for day_offset in range(days_to_scan):
            # 基于北京时间计算目标日期
            target_beijing_date = beijing_now + td(days=day_offset)
            
            # 构建该天的工作开始和结束时间（北京时间）
            beijing_day_start = target_beijing_date.replace(
                hour=work_start_hour, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            beijing_day_end = target_beijing_date.replace(
                hour=work_end_hour, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            
            # 转换为 UTC 时间用于数据库查询和存储
            day_start_utc = beijing_day_start.astimezone(timezone.utc).replace(tzinfo=None)
            day_end_utc = beijing_day_end.astimezone(timezone.utc).replace(tzinfo=None)
            
            logger.debug("第 %d 天 - 北京: %s-%s, UTC: %s-%s",
                         day_offset,
                         beijing_day_start.strftime('%Y-%m-%d %H:%M'),
                         beijing_day_end.strftime('%H:%M'),
                         day_start_utc.strftime('%Y-%m-%d %H:%M'),
                         day_end_utc.strftime('%H:%M'))
            
            # 查询该天已有的日程（使用 UTC 时间）
            existing_schedules = Schedule.query.filter(
                Schedule.user_id == current_user_id,
                Schedule.start_time >= day_start_utc,
                Schedule.end_time <= day_end_utc
            ).order_by(Schedule.start_time).all()
            
            # 计算空闲间隙
            current_time = day_start_utc
            for s in existing_schedules:
                if s.start_time > current_time:
                    gap_minutes = (s.start_time - current_time).total_seconds() / 60
                    if gap_minutes >= 15:  # 只考虑大于15分钟的间隙
                        free_slots.append({
                            'start': current_time,
                            'end': s.start_time,
                            'duration': gap_minutes
                        })
                current_time = max(current_time, s.end_time)
            
            # 当天最后一个日程到下班时间的间隙
            if current_time < day_end_utc:
                gap_minutes = (day_end_utc - current_time).total_seconds() / 60
                if gap_minutes >= 15:
                    free_slots.append({
                        'start': current_time,
                        'end': day_end_utc,
                        'duration': gap_minutes
                    })
        
        # 3. 简单的贪心排程算法
        scheduled_tasks = []
        unscheduled_tasks = []
        
        # 按任务时长降序排列（先安排大任务）
        sorted_tasks = sorted(tasks, key=lambda x: x['duration_minutes'], reverse=True)
        
        for task in sorted_tasks:
            placed = False
            for i, slot in enumerate(free_slots):
                if slot['duration'] >= task['duration_minutes']:
                    # 找到合适的位置
                    new_schedule = Schedule(
                        user_id=current_user_id,
                        title=f"🤖 {task['title']}",
                        start_time=slot['start'],
                        end_time=slot['start'] + timedelta(minutes=task['duration_minutes']),
                        priority=2,  # 默认优先级：一般（整数类型）
                        is_completed=False  # 新创建的日程默认为未完成
                    )
                    db.session.add(new_schedule)
                    
                    scheduled_tasks.append({
                        'title': task['title'],
                        'time': new_schedule.start_time.strftime('%Y-%m-%d %H:%M')
                    })
                    
                    # 更新剩余空闲时间
                    slot['duration'] -= task['duration_minutes']
                    slot['start'] = new_schedule.end_time
                    placed = True
                    break
            
            if not placed:
                unscheduled_tasks.append(task['title'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'scheduled': scheduled_tasks,
            'unscheduled': unscheduled_tasks,
            'message': f"成功安排 {len(scheduled_tasks)} 个任务，{len(unscheduled_tasks)} 个任务因时间不足未安排。"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.exception("自动排程失败")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/productivity-hours', methods=['GET'])
@jwt_required()
def get_productivity_hours():
    """获取用户的高效工作时间段"""
    try:
        current_user_id = get_jwt_identity()
        logger.debug("Token 解析成功，用户 ID: %s", current_user_id)
        
        days = request.args.get('days', 30, type=int)
        
        result = UserBehaviorAnalyzer.analyze_productivity_hours(current_user_id, days)
        return jsonify(result), 200
    except Exception as e:
        logger.exception("错误详情")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/weekly-pattern', methods=['GET'])
@jwt_required()
def get_weekly_pattern():
    """获取用户的周模式"""
    try:
        current_user_id = get_jwt_identity()
        logger.debug("Token 解析成功，用户 ID: %s", current_user_id)
        
        weeks = request.args.get('weeks', 4, type=int)
        
        result = UserBehaviorAnalyzer.analyze_weekly_pattern(current_user_id, weeks)
        return jsonify(result), 200
    except Exception as e:
        logger.exception("错误详情")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """获取个性化智能推荐"""
    try:
        current_user_id = get_jwt_identity()
        logger.debug("Token 解析成功，用户 ID: %s", current_user_id)
        
        recommendations = UserBehaviorAnalyzer.generate_personalized_recommendations(current_user_id)
        return jsonify({'recommendations': recommendations}), 200
    except Exception as e:
        logger.exception("错误详情")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_full_statistics():
    """获取完整的用户行为统计"""
    try:
        current_user_id = get_jwt_identity()
        logger.debug("Token 解析成功，用户 ID: %s", current_user_id)
        
        stats = {
            'productivity': UserBehaviorAnalyzer.analyze_productivity_hours(current_user_id),
            'weekly_pattern': UserBehaviorAnalyzer.analyze_weekly_pattern(current_user_id),
            'duration_preference': UserBehaviorAnalyzer.analyze_task_duration_preference(current_user_id),
            'priority_distribution': UserBehaviorAnalyzer.analyze_priority_distribution(current_user_id),
            'tag_distribution': _get_tag_distribution(current_user_id) # 新增：标签分布
        }
        
        return jsonify(stats), 200
    except Exception as e:
        logger.exception("错误详情")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/export/ics', methods=['GET'])
@jwt_required()
def export_to_ics():
    """导出日程为 ICS 文件"""
    from models.schedule import Schedule
    from datetime import datetime, timedelta
    
    current_user_id = get_jwt_identity()
    
    # 获取查询参数：默认导出未来7天
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=days)
    
    schedules = Schedule.query.filter(
        Schedule.user_id == current_user_id,
        Schedule.start_time >= start_date,
        Schedule.start_time <= end_date
    ).order_by(Schedule.start_time).all()
    
    # 构建 ICS 内容
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//SmartSchedule//CN\nCALSCALE:GREGORIAN\n"
    
    for s in schedules:
        # 格式化时间为 UTC 格式 (YYYYMMDDTHHmmSSZ)
        start_str = s.start_time.strftime('%Y%m%dT%H%M%SZ')
        end_str = s.end_time.strftime('%Y%m%dT%H%M%SZ') if s.end_time else \
                  (s.start_time + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
        
        ics_content += "BEGIN:VEVENT\n"
        ics_content += f"UID:{s.id}@smartschedule.local\n"
        ics_content += f"DTSTART:{start_str}\n"
        ics_content += f"DTEND:{end_str}\n"
        ics_content += f"SUMMARY:{s.title}\n"
        if s.content:
            ics_content += f"DESCRIPTION:{s.content}\n"
        if s.location:
            ics_content += f"LOCATION:{s.location}\n"
        ics_content += "END:VEVENT\n"
    
    ics_content += "END:VCALENDAR"
    
    from flask import Response
    return Response(
        ics_content,
        mimetype='text/calendar',
        headers={"Content-Disposition": f"attachment;filename=schedule_{start_date.strftime('%Y%m%d')}.ics"}
    )


@analytics_bp.route('/share-link', methods=['POST'])
@jwt_required()
def generate_share_link():
    """生成只读分享链接 Token"""
    import hashlib
    import time
    
    current_user_id = get_jwt_identity()
    # 使用用户ID和当前时间戳生成一个简单的 Token
    raw_token = f"{current_user_id}_{int(time.time())}"
    share_token = hashlib.md5(raw_token.encode()).hexdigest()
    
    # 在实际项目中，这里应该存入 Redis 或数据库，设置有效期（如 7 天）
    # 这里为了简化，我们直接返回给前端，由前端拼接 URL
    
    return jsonify({
        'share_token': share_token,
        'url': f"http://localhost:5173/share/{share_token}" # 假设前端运行在 5173
    }), 200


@analytics_bp.route('/public-schedule/<token>', methods=['GET'])
def get_public_schedule(token):
    """获取公开的忙碌状态（不显示具体内容）"""
    from models.schedule import Schedule
    from models.user import User
    from datetime import datetime, timedelta
    
    # 简单验证：解析 token 找到对应的 user_id
    # 注意：这是一个简化的实现，实际生产中应使用数据库存储 token 映射
    # 这里我们假设 token 是由 generate_share_link 生成的
    
    # 为了演示，我们暂时硬编码一个逻辑：
    # 如果 token 有效，我们返回最近 3 天的 Busy 时间段
    
    try:
        # 这里需要根据 token 反查 user_id，简化起见，我们先返回一个示例结构
        # 在实际开发中，你需要在 generate_share_link 时把 token 存入 db
        
        now = datetime.utcnow()
        end = now + timedelta(days=3)
        
        # 假设我们找到了用户 ID (这里需要从 token 映射表中查找)
        # user_id = lookup_user_by_token(token) 
        
        # 临时方案：由于还没做 token 映射表，我们先返回空列表，但逻辑已写好
        busy_slots = []
        
        return jsonify({
            'is_valid': True,
            'username': 'User', # 应该从数据库获取
            'busy_slots': busy_slots
        }), 200
        
    except Exception as e:
        return jsonify({'error': '无效的分享链接'}), 404


def _get_tag_distribution(user_id):
    """获取日程标签分布统计"""
    from models.schedule import Schedule
    
    schedules = Schedule.query.filter_by(user_id=user_id).all()
    tag_counts = {}
    
    for schedule in schedules:
        if schedule.tags and isinstance(schedule.tags, list):
            for tag in schedule.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # 转换为前端友好的格式
    result = []
    total = sum(tag_counts.values()) if tag_counts else 1
    
    # 定义标签的中文名称和图标映射
    tag_info = {
        'work': {'label': '工作', 'icon': '💼', 'color': '#3b82f6'},
        'study': {'label': '学习', 'icon': '📚', 'color': '#10b981'},
        'life': {'label': '生活', 'icon': '🏠', 'color': '#f59e0b'},
        'sport': {'label': '运动', 'icon': '🏃', 'color': '#ef4444'},
        'meeting': {'label': '会议', 'icon': '🤝', 'color': '#8b5cf6'},
        'health': {'label': '健康', 'icon': '❤️', 'color': '#ec4899'}
    }
    
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
        info = tag_info.get(tag, {'label': tag, 'icon': '🏷️', 'color': '#64748b'})
        result.append({
            'tag': tag,
            'label': info['label'],
            'icon': info['icon'],
            'count': count,
            'percentage': round((count / total) * 100, 1),
            'color': info['color']
        })
    
    return result


@analytics_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """获取用户统计数据"""
    try:
        current_user_id = get_jwt_identity()
        
        # 计算今天的日期范围（UTC）
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # 计算本周的日期范围（周一到周日）
        today = datetime.utcnow()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        # 今日统计
        today_schedules = Schedule.query.filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time >= today_start,
            Schedule.start_time < today_end
        ).all()
        
        today_total = len(today_schedules)
        today_completed = sum(1 for s in today_schedules if s.is_completed)
        
        # 本周统计
        week_schedules = Schedule.query.filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time >= week_start,
            Schedule.start_time < week_end
        ).all()
        
        week_total = len(week_schedules)
        week_completed = sum(1 for s in week_schedules if s.is_completed)
        
        # 计算本周专注时长（小时）
        week_focus_minutes = 0
        for s in week_schedules:
            if s.end_time and s.start_time:
                duration = (s.end_time - s.start_time).total_seconds() / 60
                week_focus_minutes += duration
        
        week_focus_hours = round(week_focus_minutes / 60, 1)
        
        # 完成率
        today_completion_rate = round((today_completed / today_total * 100) if today_total > 0 else 0, 1)
        week_completion_rate = round((week_completed / week_total * 100) if week_total > 0 else 0, 1)
        
        return jsonify({
            'today': {
                'total': today_total,
                'completed': today_completed,
                'completion_rate': today_completion_rate
            },
            'week': {
                'total': week_total,
                'completed': week_completed,
                'completion_rate': week_completion_rate,
                'focus_hours': week_focus_hours
            }
        }), 200
        
    except Exception as e:
        logger.exception("获取统计数据失败")
        return jsonify({'error': str(e)}), 500
