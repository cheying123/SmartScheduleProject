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
                
                # 重置完成状态，因为新周期应该是未完成的
                schedule.is_completed = False
                schedule.completed_at = None

                updated_count += 1
                logger.info(f"📅 重复日程已更新: {schedule.id}, 下次开始时间: {next_start}, 结束时间: {next_end}")

        logger.info(f"✅ 本次共更新了 {updated_count} 个重复日程")
        db.session.commit()