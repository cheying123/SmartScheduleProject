

from datetime import datetime, timedelta

class CountdownService:
    """时间倒计时提醒服务"""
    
    # 默认提醒时间点（分钟）
    DEFAULT_REMINDER_POINTS = [15, 30, 60, 1440]  # 15 分钟、30 分钟、1 小时、1 天
    
    # 自定义提醒时间点配置
    REMINDER_CONFIGS = {
        'minimal': [5, 15],  # 最小化：仅提前 5 分钟和 15 分钟
        'standard': [15, 30, 60],  # 标准：15 分钟、30 分钟、1 小时
        'comprehensive': [15, 30, 60, 120, 1440],  # 全面：2 小时、1 天
        'important': [30, 60, 120, 1440, 2880]  # 重要事件：提前 2 天
    }
    
    @staticmethod
    def get_countdown_info(target_time, reminder_config='standard'):
        """
        获取倒计时信息
        
        Args:
            target_time: 目标时间（datetime 对象或 ISO 格式字符串）
            reminder_config: 提醒配置，可以是：
                           - 字符串：'minimal', 'standard', 'comprehensive', 'important'
                           - 列表：自定义分钟数列表，如 [10, 30, 60]
        
        Returns:
            dict: 包含倒计时信息的字典
                {
                    'target_time': '2025-04-01T14:30:00',
                    'current_time': '2025-04-01T14:00:00',
                    'remaining_seconds': 1800,
                    'remaining_text': '30 分钟',
                    'is_started': False,
                    'is_ended': False,
                    'should_remind': True,
                    'remind_message': '距离开始还有 30 分钟',
                    'urgency_level': 'medium'  # low, medium, high, urgent
                }
        """
        if isinstance(target_time, str):
            try:
                target_time = datetime.fromisoformat(target_time.replace('Z', ''))
            except:
                return None
        
        now = datetime.now()
        
        # 计算时间差
        time_diff = target_time - now
        remaining_seconds = int(time_diff.total_seconds())
        
        # 判断状态
        is_started = remaining_seconds <= 0
        is_ended = False
        
        # 获取提醒配置
        reminder_points = CountdownService._get_reminder_points(reminder_config)
        
        # 检查是否需要提醒
        should_remind = False
        remind_message = ''
        urgency_level = 'low'
        
        if not is_started and remaining_seconds > 0:
            # 转换为分钟
            remaining_minutes = remaining_seconds / 60
            
            # 检查是否在提醒点附近（前后 1 分钟内）
            for point in reminder_points:
                if abs(remaining_minutes - point) <= 1:
                    should_remind = True
                    remind_message = CountdownService._generate_remind_message(remaining_seconds, point)
                    urgency_level = CountdownService._get_urgency_level(remaining_minutes)
                    break
            
            # 如果没有触发特定提醒点，生成常规倒计时文案
            if not should_remind:
                remind_message = CountdownService._generate_countdown_text(remaining_seconds)
                urgency_level = CountdownService._get_urgency_level(remaining_minutes)
        
        elif is_started:
            # 已经开始
            elapsed_seconds = abs(remaining_seconds)
            remind_message = CountdownService._generate_elapsed_text(elapsed_seconds)
            urgency_level = 'low'
        
        return {
            'target_time': target_time.isoformat(),
            'current_time': now.isoformat(),
            'remaining_seconds': remaining_seconds,
            'remaining_text': CountdownService._format_duration(remaining_seconds),
            'is_started': is_started,
            'is_ended': is_ended,
            'should_remind': should_remind,
            'remind_message': remind_message,
            'urgency_level': urgency_level
        }
    
    @staticmethod
    def get_schedule_countdown_list(schedules, reminder_config='standard'):
        """
        批量获取日程的倒计时信息
        
        Args:
            schedules: 日程列表，每个日程应包含 start_time 字段
            reminder_config: 提醒配置
        
        Returns:
            list: 包含日程 ID 和倒计时信息的列表
        """
        countdown_list = []
        
        for schedule in schedules:
            start_time = schedule.get('start_time')
            if not start_time:
                continue
            
            countdown_info = CountdownService.get_countdown_info(start_time, reminder_config)
            if countdown_info:
                countdown_info['schedule_id'] = schedule.get('id')
                countdown_info['title'] = schedule.get('title')
                countdown_list.append(countdown_info)
        
        # 按剩余时间排序（即将开始的在前）
        countdown_list.sort(key=lambda x: x['remaining_seconds'])
        
        return countdown_list
    
    @staticmethod
    def _get_reminder_points(config):
        """获取提醒时间点配置"""
        if isinstance(config, str):
            return CountdownService.REMINDER_CONFIGS.get(config, CountdownService.DEFAULT_REMINDER_POINTS)
        elif isinstance(config, list):
            return config
        return CountdownService.DEFAULT_REMINDER_POINTS
    
    @staticmethod
    def _generate_remind_message(remaining_seconds, nearest_point):
        """生成提醒消息"""
        minutes = int(remaining_seconds / 60)
        hours = int(minutes / 60)
        days = int(hours / 24)
        
        if nearest_point >= 1440:  # 1 天以上
            day_text = f'{days}天'
            if days > 1:
                return f'⏰ 提醒：距离开始还有{day_text}，请提前做好准备'
            else:
                return f'⏰ 提醒：明天这个时候就要开始了，请做好准备'
        elif nearest_point >= 60:
            return f'⏰ 提醒：距离开始还有{hours}小时，请提前准备'
        elif nearest_point >= 30:
            return f'⏰ 提醒：距离开始还有{minutes}分钟，请尽快准备'
        else:
            return f'⏰ 提醒：距离开始只有{minutes}分钟了，请立即准备'
    
    @staticmethod
    def _generate_countdown_text(remaining_seconds):
        """生成常规倒计时文本"""
        duration = CountdownService._format_duration(remaining_seconds)
        return f'⏳ 距离开始还有{duration}'
    
    @staticmethod
    def _generate_elapsed_text(elapsed_seconds):
        """生成已开始的时间文本"""
        duration = CountdownService._format_duration(elapsed_seconds)
        return f'✅ 已开始{duration}'
    
    @staticmethod
    def _format_duration(seconds):
        """格式化时间间隔为可读文本"""
        if seconds < 0:
            seconds = abs(seconds)
        
        minutes = int(seconds / 60)
        hours = int(minutes / 60)
        days = int(hours / 24)
        
        if days > 0:
            remaining_hours = hours % 24
            if remaining_hours > 0:
                return f'{days}天{remaining_hours}小时'
            return f'{days}天'
        elif hours > 0:
            remaining_minutes = minutes % 60
            if remaining_minutes > 0:
                return f'{hours}小时{remaining_minutes}分钟'
            return f'{hours}小时'
        elif minutes > 0:
            return f'{minutes}分钟'
        else:
            return f'{seconds}秒'
    
    @staticmethod
    def _get_urgency_level(remaining_minutes):
        """获取紧急程度"""
        if remaining_minutes <= 5:
            return 'urgent'  # 非常紧急（红色）
        elif remaining_minutes <= 15:
            return 'high'  # 紧急（橙色）
        elif remaining_minutes <= 60:
            return 'medium'  # 中等（黄色）
        elif remaining_minutes <= 1440:  # 24 小时内
            return 'low'  # 低（蓝色）
        else:
            return 'info'  # 提示（灰色）


# 便捷函数
def get_countdown(target_time, config='standard'):
    """获取倒计时信息的便捷函数"""
    return CountdownService.get_countdown_info(target_time, config)


def get_schedules_countdown(schedules, config='standard'):
    """批量获取日程倒计时的便捷函数"""
    return CountdownService.get_schedule_countdown_list(schedules, config)