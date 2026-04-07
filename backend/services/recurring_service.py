from datetime import datetime, timedelta
from models.schedule import Schedule
from extensions import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecurringService:
    @staticmethod
    def process_recurring_schedules():
        """
        处理所有已结束的重复日程：
        采用“滚动更新”策略：旧日程时间直接跳转到下一个周期。
        """
        logger.info("🔄 开始检查重复日程...")
        now = datetime.utcnow()
        
        # 查找所有开启了重复、且结束时间已经过去的日程
        schedules = Schedule.query.filter(
            Schedule.is_recurring == True,
            Schedule.recurring_pattern != None
        ).all()
        
        updated_count = 0
        
        for schedule in schedules:
            # 确定当前日程的结束时间
            current_end = schedule.end_time if schedule.end_time else schedule.start_time + timedelta(hours=1)
            
            # 如果日程还没结束，跳过
            if current_end > now:
                continue
            
            # 计算下一次的时间
            next_start = None
            duration = schedule.end_time - schedule.start_time if schedule.end_time else timedelta(hours=1)
            
            # 循环直到找到未来的时间（防止跨度很大的重复，比如每月31号）
            while True:
                if schedule.recurring_pattern == 'daily':
                    next_start = schedule.start_time + timedelta(days=1)
                elif schedule.recurring_pattern == 'weekly':
                    next_start = schedule.start_time + timedelta(weeks=1)
                elif schedule.recurring_pattern == 'monthly':
                    month = schedule.start_time.month + 1
                    year = schedule.start_time.year
                    if month > 12:
                        month = 1
                        year += 1
                    try:
                        next_start = schedule.start_time.replace(year=year, month=month)
                    except ValueError:
                        # 如果下个月没有这一天（如31号），则跳到下下个月
                        schedule.start_time = next_start if next_start else schedule.start_time + timedelta(days=32)
                        continue
                
                if next_start and next_start > now:
                    break
                
                # 如果算出来的下次时间还是过去，继续往后推（针对 daily/weekly）
                schedule.start_time = next_start

            if next_start:
                next_end = next_start + duration
                
                # 更新数据库中的日程时间
                schedule.start_time = next_start
                schedule.end_time = next_end
                
                # 重新获取天气信息（如果在未来7天内）
                from services.weather_service import get_weather_with_alerts
                schedule_date = next_start.strftime('%Y-%m-%d')
                today = datetime.now().strftime('%Y-%m-%d')
                target_date = datetime.strptime(schedule_date, '%Y-%m-%d')
                today_date = datetime.strptime(today, '%Y-%m-%d')
                days_diff = (target_date - today_date).days
                
                if 0 <= days_diff <= 7:
                    city_location_id = schedule.user.location if schedule.user else "101010100"
                    try:
                        weather_result = get_weather_with_alerts(city_location_id, schedule_date)
                        if weather_result:
                            schedule.weather_info = weather_result['weather_text']
                    except Exception as e:
                        logger.error(f"更新天气失败: {e}")

                updated_count += 1
                logger.info(f"✅ 日程 '{schedule.title}' 已滚动至: {next_start}")
        
        if updated_count > 0:
            db.session.commit()
            logger.info(f"🎉 共更新了 {updated_count} 个重复日程")
        
        return updated_count