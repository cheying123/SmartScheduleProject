from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from services.user_behavior_analyzer import UserBehaviorAnalyzer
from models.user import User
from extensions import db
import traceback

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/productivity-hours', methods=['GET'])
@jwt_required()
def get_productivity_hours():
    """获取用户的高效工作时间段"""
    try:
        current_user_id = get_jwt_identity()
        print(f"✅ Token 解析成功，用户 ID: {current_user_id}")
        
        days = request.args.get('days', 30, type=int)
        
        result = UserBehaviorAnalyzer.analyze_productivity_hours(current_user_id, days)
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ 错误详情：{str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/weekly-pattern', methods=['GET'])
@jwt_required()
def get_weekly_pattern():
    """获取用户的周模式"""
    try:
        current_user_id = get_jwt_identity()
        print(f"✅ Token 解析成功，用户 ID: {current_user_id}")
        
        weeks = request.args.get('weeks', 4, type=int)
        
        result = UserBehaviorAnalyzer.analyze_weekly_pattern(current_user_id, weeks)
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ 错误详情：{str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """获取个性化智能推荐"""
    try:
        current_user_id = get_jwt_identity()
        print(f"✅ Token 解析成功，用户 ID: {current_user_id}")
        
        recommendations = UserBehaviorAnalyzer.generate_personalized_recommendations(current_user_id)
        return jsonify({'recommendations': recommendations}), 200
    except Exception as e:
        print(f"❌ 错误详情：{str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_full_statistics():
    """获取完整的用户行为统计"""
    try:
        current_user_id = get_jwt_identity()
        print(f"✅ Token 解析成功，用户 ID: {current_user_id}")
        
        stats = {
            'productivity': UserBehaviorAnalyzer.analyze_productivity_hours(current_user_id),
            'weekly_pattern': UserBehaviorAnalyzer.analyze_weekly_pattern(current_user_id),
            'duration_preference': UserBehaviorAnalyzer.analyze_task_duration_preference(current_user_id),
            'priority_distribution': UserBehaviorAnalyzer.analyze_priority_distribution(current_user_id),
            'tag_distribution': _get_tag_distribution(current_user_id) # 新增：标签分布
        }
        
        return jsonify(stats), 200
    except Exception as e:
        print(f"❌ 错误详情：{str(e)}")
        print(traceback.format_exc())
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
