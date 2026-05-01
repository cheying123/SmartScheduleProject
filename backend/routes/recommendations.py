

import logging
from flask import Blueprint, jsonify
from models.schedule import Schedule
from datetime import datetime, timedelta
from services.countdown_service import CountdownService
from collections import Counter
from utils.jwt_utils import token_required

logger = logging.getLogger(__name__)

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/api')


def generate_schedule_recommendations(user_id):
    """
    基于用户历史日程生成智能推荐（保留原有功能）
    """
    recommendations = []
    
    # 获取用户的历史日程
    user_schedules = Schedule.query.filter_by(user_id=user_id).order_by(Schedule.start_time).all()
    
    if len(user_schedules) < 3:
        return [{'type': 'info', 'message': '日程数据不足，暂无法提供智能推荐'}]
    
    # 分析用户的工作时间偏好（UTC 转本地时间）
    work_hours = []
    for schedule in user_schedules:
        # 数据库存储的是 UTC 时间，需要转换为本地时间（+8 小时）
        utc_time = schedule.start_time
        local_time = utc_time + timedelta(hours=8)  # 北京时间 UTC+8
        local_hour = local_time.hour
        work_hours.append(local_hour)
    
    if work_hours:
        hour_counter = Counter(work_hours)
        most_common_hour = hour_counter.most_common(1)[0][0]
        
        # 推荐相似时间段安排类似活动
        recommendations.append({
            'type': 'time_preference',
            'message': f'根据历史记录，您通常在{most_common_hour}点安排活动，建议保持这个习惯',
            'suggested_hour': most_common_hour
        })
    
    # 检测是否有足够的休息时间（使用本地时间）
    morning_activities = []
    afternoon_activities = []
    
    for schedule in user_schedules:
        # UTC 转本地时间
        local_time = schedule.start_time + timedelta(hours=8)
        local_hour = local_time.hour
        
        if local_hour < 12:
            morning_activities.append(schedule)
        elif 12 <= local_hour < 18:
            afternoon_activities.append(schedule)
    
    if len(morning_activities) > len(afternoon_activities) * 2:
        recommendations.append({
            'type': 'balance',
            'message': '您上午的日程较多，建议适当安排下午的休息时间'
        })
    
    # 检查天气相关的建议（使用本地时间）
    now_local = datetime.now() + timedelta(hours=8)
    today_local = now_local.date()
    
    today_schedules = []
    for schedule in user_schedules:
        # UTC 转本地时间后比较日期
        local_date = (schedule.start_time + timedelta(hours=8)).date()
        if local_date == today_local:
            today_schedules.append(schedule)
    
    if today_schedules:
        weather_msg = "今天有日程安排，请查看具体日程的天气提示"
        recommendations.append({
            'type': 'weather',
            'message': weather_msg
        })
    
    return recommendations


@recommendations_bp.route('/recommendations', methods=['GET'])
@token_required
def get_recommendations(current_user):
    """获取智能推荐和即将开始的日程提醒"""
    current_user_id = current_user.id
    
    all_recommendations = []
    
    # 1. 获取原有的智能推荐
    try:
        smart_recommendations = generate_schedule_recommendations(current_user_id)
        all_recommendations.extend(smart_recommendations)
    except Exception as e:
        logger.error("生成智能推荐失败: %s", e)
    
    # 2. 新增：获取即将开始的日程提醒（未来 48 小时内）
    try:
        # 重要说明：
        # - datetime.now() 返回的是服务器系统时间（UTC）
        # - 数据库存储的是 UTC 时间
        # - 因此可以直接用 datetime.now() 查询数据库
        
        now_utc = datetime.utcnow()  # 明确的 UTC 时间
        end_time_utc = now_utc + timedelta(hours=48)
        
        # 用于显示的本地时间（北京时间）
        tz_offset = 8  # 北京时间 UTC+8
        now_local = now_utc + timedelta(hours=tz_offset)
        
        logger.debug("查询参数: user_id=%s, UTC范围: %s 到 %s", current_user_id, now_utc, end_time_utc)

        # 查询未来 48 小时内的所有日程（数据库存储的是 UTC 时间）
        upcoming_schedules = Schedule.query.filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time >= now_utc,
            Schedule.start_time <= end_time_utc
        ).order_by(Schedule.start_time).all()

        logger.debug("找到 %d 个即将开始的日程", len(upcoming_schedules))
        
        # 为每个即将开始的日程生成倒计时提醒
        for schedule in upcoming_schedules:
            # 将 UTC 时间转换为本地时间（+8 小时）
            local_start_time = schedule.start_time + timedelta(hours=tz_offset)
            
            logger.debug("日程: %s, UTC: %s, 北京: %s", schedule.title, schedule.start_time, local_start_time)

            # 使用本地时间生成倒计时信息
            countdown_info = CountdownService.get_countdown_info(
                local_start_time,
                'comprehensive'
            )
            
            if countdown_info and not countdown_info['is_started']:
                # 计算剩余分钟数
                remaining_minutes = abs(countdown_info['remaining_seconds']) / 60
                
                # 定义提醒时间段（分钟）和对应的优先级
                reminder_windows = [
                    (15, 'urgent'),
                    (60, 'high'),
                    (180, 'medium'),
                    (1440, 'low'),
                    (2880, 'info')
                ]
                
                # 确定优先级并生成提醒
                for window, priority in reminder_windows:
                    if remaining_minutes <= window:
                        all_recommendations.append({
                            'id': f'countdown_{schedule.id}',
                            'type': 'schedule_reminder',
                            'priority': priority,
                            'message': f'⏰ 【{schedule.title}】{countdown_info["remind_message"]}',
                            'schedule_id': schedule.id,
                            'schedule_title': schedule.title,
                            'start_time': local_start_time.isoformat(),
                            'start_time_utc': schedule.start_time.isoformat(),
                            'countdown': countdown_info,
                            'created_at': now_local.isoformat()
                        })
                        logger.debug("添加提醒 -> 优先级: %s (剩余%.0f分钟)", priority, remaining_minutes)
                        break
            
    except Exception as e:
        logger.exception("生成日程提醒失败")
    
    # 3. 排序：按优先级和剩余时间排序（紧急的在前）
    priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    
    all_recommendations.sort(key=lambda x: (
        priority_order.get(x.get('priority', 'info'), 5),
        x.get('countdown', {}).get('remaining_seconds', 999999)
    ))
    
    return jsonify(all_recommendations)


@recommendations_bp.route('/smart-recommendations', methods=['GET'])
@token_required
def get_smart_recommendations(current_user):
    """获取纯智能推荐（不包含日程提醒）"""
    current_user_id = current_user.id
    
    try:
        # 获取智能推荐（时间偏好、平衡建议、天气等）
        smart_recommendations = generate_schedule_recommendations(current_user_id)
        # 只返回非日程提醒类型的推荐
        filtered_recommendations = [r for r in smart_recommendations if r.get('type') != 'schedule_reminder']
        return jsonify(filtered_recommendations)
    except Exception as e:
        logger.error("获取智能推荐失败: %s", e)
        return jsonify([])