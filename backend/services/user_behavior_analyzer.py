
# """
# 用户行为分析服务
# 分析用户的日程习惯、工作效率时间段，为智能推荐提供数据支持
# """
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from models.schedule import Schedule
import statistics

class UserBehaviorAnalyzer:
    
    @staticmethod
    def analyze_productivity_hours(user_id, days=30):
        """
        分析用户的高效工作时间段
        
        Args:
            user_id: 用户 ID
            days: 分析最近多少天的数据
            
        Returns:
            {
                'productive_hours': [9, 14, 10],
                'distribution': {9: 15, 10: 12, ...},
                'total_tasks': 45,
                'completion_rate': 0.85
            }
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        schedules = Schedule.query.filter(
            Schedule.user_id == user_id,
            Schedule.start_time >= start_date,
            Schedule.start_time <= end_date
        ).all()
        
        if not schedules:
            return {
                'productive_hours': [],
                'distribution': {},
                'total_tasks': 0,
                'completion_rate': 0
            }
        
        hour_distribution = defaultdict(int)
        completed_count = 0
        
        for schedule in schedules:
            local_hour = (schedule.start_time + timedelta(hours=8)).hour
            hour_distribution[local_hour] += 1
            
            if schedule.is_completed:
                completed_count += 1
        
        sorted_hours = sorted(hour_distribution.items(), 
                             key=lambda x: x[1], reverse=True)
        top_hours = [h[0] for h in sorted_hours[:3]]
        
        return {
            'productive_hours': top_hours,
            'distribution': dict(hour_distribution),
            'total_tasks': len(schedules),
            'completion_rate': completed_count / len(schedules) if schedules else 0
        }
    
    @staticmethod
    def analyze_weekly_pattern(user_id, weeks=4):
        """
        分析用户的周模式（哪几天比较忙）
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(weeks=weeks)
        
        schedules = Schedule.query.filter(
            Schedule.user_id == user_id,
            Schedule.start_time >= start_date,
            Schedule.start_time <= end_date
        ).all()
        
        if not schedules:
            return {
                'busy_days': [],
                'day_distribution': {},
                'average_tasks_per_day': 0
            }
        
        day_distribution = defaultdict(int)
        for schedule in schedules:
            weekday = schedule.start_time.weekday()
            day_distribution[weekday] += 1
        
        sorted_days = sorted(day_distribution.items(), 
                            key=lambda x: x[1], reverse=True)
        busy_days = [d[0] for d in sorted_days[:3]]
        
        total_days = weeks * 7
        avg_tasks = len(schedules) / total_days
        
        return {
            'busy_days': busy_days,
            'day_distribution': dict(day_distribution),
            'average_tasks_per_day': round(avg_tasks, 2)
        }
    
    @staticmethod
    def analyze_task_duration_preference(user_id):
        """
        分析用户的任务时长偏好
        """
        schedules = Schedule.query.filter_by(user_id=user_id).all()
        
        durations = []
        for schedule in schedules:
            if schedule.end_time:
                duration = (schedule.end_time - schedule.start_time).total_seconds() / 60
                if 15 <= duration <= 180:
                    durations.append(duration)
        
        if not durations:
            return {
                'average_duration_minutes': 60,
                'preferred_break_minutes': 15,
                'max_focus_minutes': 90
            }
        
        avg_duration = statistics.mean(durations)
        
        return {
            'average_duration_minutes': round(avg_duration, 2),
            'preferred_break_minutes': 15,
            'max_focus_minutes': round(max(durations), 2)
        }
    
    @staticmethod
    def analyze_priority_distribution(user_id, days=30):
        """
        分析用户的优先级分布
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        schedules = Schedule.query.filter(
            Schedule.user_id == user_id,
            Schedule.start_time >= start_date
        ).all()
        
        priority_counts = Counter([s.priority for s in schedules])
        
        return {
            'distribution': dict(priority_counts),
            'high_priority_ratio': sum(priority_counts.get(p, 0) for p in [4, 5]) / len(schedules) if schedules else 0
        }
    
    @staticmethod
    def generate_personalized_recommendations(user_id):
        """
        基于用户行为生成个性化推荐
        """
        recommendations = []
        
        productivity_data = UserBehaviorAnalyzer.analyze_productivity_hours(user_id)
        weekly_data = UserBehaviorAnalyzer.analyze_weekly_pattern(user_id)
        duration_data = UserBehaviorAnalyzer.analyze_task_duration_preference(user_id)
        
        if productivity_data['productive_hours']:
            hours_str = '、'.join([f'{h}点' for h in productivity_data['productive_hours'][:2]])
            confidence = productivity_data['completion_rate']
            
            recommendations.append({
                'type': 'time_optimization',
                'title': '发现您的高效时段',
                'message': f'根据历史数据，您在{hours_str}效率较高，建议将重要任务安排在这些时段',
                'confidence': round(confidence, 2),
                'data': productivity_data
            })
        
        if weekly_data['busy_days']:
            busy_days_str = '、'.join([f'周{["一", "二", "三", "四", "五", "六", "日"][d]}' 
                                      for d in weekly_data['busy_days'][:2]])
            
            sorted_busy = sorted(weekly_data['busy_days'])
            has_consecutive = any(
                sorted_busy[i+1] - sorted_busy[i] == 1 
                for i in range(len(sorted_busy)-1)
            )
            
            if has_consecutive:
                recommendations.append({
                    'type': 'work_life_balance',
                    'title': '注意劳逸结合',
                    'message': f'您的{busy_days_str}安排较为密集，建议在中间安排短暂休息',
                    'confidence': 0.75
                })
        
        if duration_data['average_duration_minutes'] > 90:
            recommendations.append({
                'type': 'focus_optimization',
                'title': '优化专注时长',
                'message': f'您的平均任务时长为{duration_data["average_duration_minutes"]}分钟，建议尝试番茄工作法（25 分钟专注 +5 分钟休息）提升效率',
                'confidence': 0.70
            })
        
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return recommendations[:5]