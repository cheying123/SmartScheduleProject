# 完整文件：d:\SmartScheduleProject\backend\services\ai_service.py
"""
AI 对话服务
集成 DeepSeek、Qwen 等大模型，提供智能推荐和对话功能
注意：此服务使用 ANALYSIS_AI_* 配置，与原有的 AI_API_* 配置独立
"""
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class AIService:
    """AI 服务类 - 专用于效率分析页面的 AI 对话助手"""
    
    def __init__(self):
        # 使用独立的 ANALYSIS_AI_* 配置，不影响原有的 AI_API_* 配置
        self.api_key = os.getenv('ANALYSIS_AI_API_KEY', '')
        self.api_url = os.getenv('ANALYSIS_AI_API_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
        self.model = os.getenv('ANALYSIS_AI_MODEL', 'qwen-turbo')
    
    def chat(self, messages, user_data=None):
        """
        与 AI 进行对话
        
        Args:
            messages: 对话历史列表，格式为 [{'role': 'user/assistant', 'content': '消息内容'}]
            user_data: 用户数据（日程统计信息等）
            
        Returns:
            AI 的回复内容
        """
        if not self.api_key:
            return "⚠️ 未配置 ANALYSIS_AI_API_KEY，请联系管理员"
        
        try:
            system_prompt = self._build_system_prompt(user_data)
            
            full_messages = [
                {'role': 'system', 'content': system_prompt},
                *messages
            ]
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'input': {
                    'messages': full_messages
                },
                'parameters': {
                    'temperature': 0.7,
                    'max_tokens': 1500
                }
            }
            
            print("=" * 60)
            print("🤖 发送 AI 请求...")
            print(f"📍 API URL: {self.api_url}")
            print(f"📍 Model: {self.model}")
            print("-" * 60)
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            print("✅ AI 响应原始数据:")
            print(result)
            print("-" * 60)
            
            # 兼容多种响应格式
            ai_message = ""
            
            # 格式 1: 通义千问标准格式
            if 'output' in result and 'choices' in result['output']:
                ai_message = result['output']['choices'][0]['message']['content']
            # 格式 2: 通义千问简化格式
            elif 'output' in result and 'text' in result['output']:
                ai_message = result['output']['text']
            # 格式 3: 直接 choices
            elif 'choices' in result:
                ai_message = result['choices'][0]['message']['content']
            # 格式 4: content 字段
            elif 'content' in result:
                ai_message = result['content']
            else:
                print("❌ 无法解析的响应格式")
                ai_message = "抱歉，AI 响应格式异常，请稍后再试"
            
            print(f"📝 AI 回复：{ai_message[:100]}...")
            print("=" * 60)
            
            return ai_message
            
        except Exception as e:
            print(f"❌ AI 调用失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return f"抱歉，AI 服务暂时不可用：{str(e)}"
    
    def _build_system_prompt(self, user_data):
        """构建系统提示词"""
        prompt = """你是一个专业的智能日程分析助手，专门帮助用户分析日程习惯并提供个性化建议。

你的主要职责：
1. 分析用户的高效工作时间段和繁忙日期
2. 提供日程安排优化建议
3. 提醒用户注意休息和工作平衡
4. 根据天气情况给出出行建议
5. 回答用户关于时间管理和日程规划的任何问题

请使用友好、专业、鼓励的语气，给出的建议要具体、可执行。
如果用户询问与日程管理无关的问题，礼貌地引导回日程管理话题。"""

        if user_data:
            prompt += "\n\n【当前用户的日程数据】"
            if user_data.get('productive_hours'):
                prompt += f"\n• 高效时段：{', '.join(map(str, user_data['productive_hours']))}点"
            if user_data.get('busy_days'):
                weekday_map = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                busy_days_str = ', '.join([weekday_map[d] for d in user_data['busy_days']])
                prompt += f"\n• 繁忙日期：{busy_days_str}"
            if user_data.get('total_tasks'):
                prompt += f"\n• 总任务数：{user_data['total_tasks']}个"
            if user_data.get('completion_rate'):
                prompt += f"\n• 完成率：{user_data['completion_rate']:.1%}"
            
            prompt += "\n\n请基于以上数据，为用户提供有针对性的个性化建议。"
        
        return prompt
    
    def generate_ai_recommendations(self, user_statistics):
        """
        基于用户统计数据生成 AI 推荐（包含详细的日程数据）
        
        Args:
            user_statistics: 用户统计字典，包含 productivity、weekly_pattern 等，必须包含 user_id
            
        Returns:
            AI 生成的推荐列表
        """
        try:
            user_data = {
                'productive_hours': user_statistics.get('productivity', {}).get('productive_hours', []),
                'busy_days': user_statistics.get('weekly_pattern', {}).get('busy_days', []),
                'total_tasks': user_statistics.get('productivity', {}).get('total_tasks', 0),
                'completion_rate': user_statistics.get('productivity', {}).get('completion_rate', 0)
            }
            
            # 🎯 新增：获取用户最近的详细日程数据
            from models.schedule import Schedule
            from datetime import datetime, timedelta
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)  # 获取最近 30 天的日程
            
            schedules = Schedule.query.filter(
                Schedule.user_id == user_data.get('user_id'),
                Schedule.start_time >= start_date,
                Schedule.start_time <= end_date
            ).order_by(Schedule.start_time.desc()).all()
            
            # 构建详细的日程列表
            schedule_list = []
            for schedule in schedules[:30]:  # 最多取 30 条
                local_time = schedule.start_time + timedelta(hours=8)
                time_str = local_time.strftime('%m-%d %H:%M')
                weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][local_time.weekday()]
                
                schedule_info = {
                    'time': f"{time_str}({weekday})",
                    'title': schedule.title,
                    'content': schedule.content or '',
                    'priority': schedule.priority,
                    'is_recurring': schedule.is_recurring or False
                }
                schedule_list.append(schedule_info)
            
            print("\n" + "=" * 60)
            print("🔮 开始生成 AI 推荐...")
            print(f"📊 用户数据：{user_data}")
            print(f"📅 日程数量：{len(schedule_list)}")
            print("-" * 60)
            
            # 🎯 构建包含详细日程的提示词
            schedule_details = ""
            if schedule_list:
                schedule_details = "\n【我最近的日程安排】\n"
                for i, s in enumerate(schedule_list, 1):
                    priority_str = "⭐" * s['priority'] if s['priority'] else ""
                    schedule_details += f"{i}. {s['time']} - {s['title']}"
                    if s['content']:
                        schedule_details += f" ({s['content'][:50]})"
                    if priority_str:
                        schedule_details += f" {priority_str}"
                    if s['is_recurring']:
                        schedule_details += " [重复]"
                    schedule_details += "\n"
            
            messages = [{
                'role': 'user',
                'content': f"""请根据我的日程数据和以下详细日程安排，给我一些个性化的日程管理建议。

我的高效时段：{user_data.get('productive_hours', [])}
我的繁忙日期：{user_data.get('busy_days', [])}
总任务数：{user_data.get('total_tasks', 0)}
完成率：{user_data.get('completion_rate', 0):.1%}
{schedule_details}

请从以下几个角度给我建议：
1. 时间分配是否合理？哪些时间段可以更好地利用？
2. 我的日程安排有什么特点或问题？
3. 如何提高我的日程管理效率？
4. 对于重复性活动，有什么优化建议？

请用简洁、实用的条目列出建议。"""
            }]
            
            ai_response = self.chat(messages, user_data)
            
            if not ai_response or ai_response.startswith("抱歉") or ai_response.startswith("⚠️"):
                print("⚠️ AI 返回了错误信息，使用默认推荐")
                return [{
                    'type': 'ai_insight',
                    'title': 'AI 洞察',
                    'message': '继续记录您的日程，积累更多数据后我将为您提供更精准的分析建议！',
                    'confidence': 0.8
                }]
            
            recommendations = []
            
            lines = ai_response.split('\n')
            current_rec = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('•') or line.startswith('-'):
                    if current_rec:
                        recommendations.append(current_rec)
                    current_rec = {
                        'type': 'ai_insight',
                        'title': f'AI 建议 {len(recommendations) + 1}',
                        'message': line.lstrip('0123456789.•-').strip(),
                        'confidence': 0.9
                    }
                elif current_rec and line:
                    current_rec['message'] += '\n' + line
            
            if current_rec:
                recommendations.append(current_rec)
            
            if not recommendations:
                recommendations.append({
                    'type': 'ai_insight',
                    'title': 'AI 洞察',
                    'message': ai_response,
                    'confidence': 0.85
                })
            
            print(f"✅ 生成了 {len(recommendations)} 条推荐")
            print("=" * 60)
            
            return recommendations
            
        except Exception as e:
            print(f"❌ 生成 AI 推荐失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return [{
                'type': 'ai_insight',
                'title': '系统提示',
                'message': f'生成推荐时出现错误：{str(e)}',
                'confidence': 0.5
            }]
    
    def analyze_recent_schedules(self, user_id, days=7):
        """
        分析用户的所有日程，生成智能报告
        
        Args:
            user_id: 用户 ID
            days: 分析最近多少天（此参数已废弃，现在分析所有日程）
            
        Returns:
            详细的分析报告字符串
        """
        from models.schedule import Schedule
        from datetime import datetime, timedelta
        
        try:
            # 🎯 修改：获取用户的所有日程（不限制时间范围）
            schedules = Schedule.query.filter(
                Schedule.user_id == user_id
            ).order_by(Schedule.start_time.desc()).all()
            
            if not schedules:
                return "您还没有创建任何日程哦～ 快去添加一些日程吧！"
            
            # 分析日程模式
            morning_count = sum(1 for s in schedules if (s.start_time + timedelta(hours=8)).hour < 12)
            afternoon_count = sum(1 for s in schedules if 12 <= (s.start_time + timedelta(hours=8)).hour < 18)
            evening_count = sum(1 for s in schedules if (s.start_time + timedelta(hours=8)).hour >= 18)
            
            total_count = len(schedules)
            
            # 计算有日程的天数范围
            if schedules:
                earliest_date = min(s.start_time for s in schedules)
                latest_date = max(s.start_time for s in schedules)
                days_span = (latest_date - earliest_date).days + 1
                avg_per_day = total_count / days_span if days_span > 0 else total_count
            else:
                avg_per_day = 0
            
            # 构建详细报告
            report = f"""我分析了您的所有日程数据（共 {total_count} 个日程），发现以下特点：

【总体情况】
• 共创建了 {total_count} 个日程
• 平均每天 {avg_per_day:.1f} 个活动
"""
            
            if morning_count > afternoon_count * 1.5:
                report += f"\n【时间分布】\n• 您明显是个'晨型人'，{morning_count}个活动都安排在上午\n• 下午相对轻松，可以适当增加一些重要任务"
            elif afternoon_count > morning_count * 1.5:
                report += f"\n【时间分布】\n• 您更喜欢在下午工作，{afternoon_count}个活动集中在下午\n• 上午的时间利用率还有提升空间哦"
            elif evening_count > total_count * 0.4:
                report += f"\n【时间分布】\n• 注意到您晚上安排了{evening_count}个活动\n• 要注意劳逸结合，避免影响休息"
            else:
                report += f"\n【时间分布】\n• 上午：{morning_count}个 | 下午：{afternoon_count}个 | 晚上：{evening_count}个\n• 时间分配比较均衡"
            
            # 检查是否有重复模式
            titles = [s.title.lower() for s in schedules]
            title_counter = {}
            for title in titles:
                title_counter[title] = title_counter.get(title, 0) + 1
            
            recurring_activities = [(k, v) for k, v in title_counter.items() if v >= 2]
            if recurring_activities:
                report += "\n\n【习惯发现】\n"
                for title, count in sorted(recurring_activities, key=lambda x: x[1], reverse=True)[:5]:
                    report += f"• '{title}' 出现了{count}次，这是您的固定安排吗？\n"
            
            # 给出建议
            report += "\n【智能建议】\n"
            if avg_per_day > 3:
                report += "• 您的日程很充实呢！不过也要注意留出缓冲时间，避免过度疲劳\n"
            elif avg_per_day < 1:
                report += "• 最近比较清闲呢，可以考虑安排一些学习或自我提升的活动\n"
            else:
                report += "• 目前的节奏不错，保持下去！可以尝试把重要任务安排在高效时段\n"
            
            if morning_count > 0:
                report += "• 上午精力充沛，适合处理需要深度思考的工作\n"
            if afternoon_count > 0:
                report += "• 下午适合安排会议、沟通等协作性工作\n"
            
            return report
            
        except Exception as e:
            print(f"❌ 分析最近日程失败：{str(e)}")
            return f"分析失败：{str(e)}"
    
    
    
    def get_schedule_context_for_ai(self, user_id, days=7):
        """
        获取用户最近日程的上下文信息，用于 AI 对话
        
        Args:
            user_id: 用户 ID
            days: 分析最近多少天
            
        Returns:
            格式化的日程上下文字符串
        """
        from models.schedule import Schedule
        from datetime import datetime, timedelta
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            schedules = Schedule.query.filter(
                Schedule.user_id == user_id,
                Schedule.start_time >= start_date,
                Schedule.start_time <= end_date
            ).order_by(Schedule.start_time.desc()).limit(15).all()
            
            if not schedules:
                return "用户最近没有创建任何日程"
            
            context = "【用户最近的日程安排】\n"
            for schedule in schedules:
                local_time = schedule.start_time + timedelta(hours=8)
                time_str = local_time.strftime('%m-%d %H:%M')
                weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][local_time.weekday()]
                
                context += f"• {time_str}({weekday}) - {schedule.title}"
                if schedule.content:
                    context += f" ({schedule.content[:30]})"
                if schedule.priority and schedule.priority >= 4:
                    context += " ⭐重要"
                context += "\n"
            
            return context.strip()
            
        except Exception as e:
            print(f"❌ 获取日程上下文失败：{str(e)}")
            return "无法获取用户日程数据"