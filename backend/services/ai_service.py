"""
AI 对话服务
集成 DeepSeek、Qwen 等大模型，提供智能推荐和对话功能
注意：此服务使用 ANALYSIS_AI_* 配置，与原有的 AI_API_* 配置独立
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models.schedule import Schedule

load_dotenv()

logger = logging.getLogger(__name__)

_WEEKDAY_MAP = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']


def _parse_ai_response(result):
    if 'output' in result and 'choices' in result['output']:
        return result['output']['choices'][0]['message']['content']
    if 'output' in result and 'text' in result['output']:
        return result['output']['text']
    if 'choices' in result:
        return result['choices'][0]['message']['content']
    if 'content' in result:
        return result['content']
    return None


class AIService:
    """AI 服务类 - 专用于效率分析页面的 AI 对话助手"""

    def __init__(self):
        self.api_key = os.getenv('ANALYSIS_AI_API_KEY', '')
        self.api_url = os.getenv('ANALYSIS_AI_API_URL',
                                 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
        self.model = os.getenv('ANALYSIS_AI_MODEL', 'qwen-turbo')

    def chat(self, messages, user_data=None):
        if not self.api_key:
            return "⚠️ 未配置 ANALYSIS_AI_API_KEY，请联系管理员"

        try:
            full_messages = [
                {'role': 'system', 'content': self._build_system_prompt(user_data)},
                *messages,
            ]

            payload = {
                'model': self.model,
                'input': {'messages': full_messages},
                'parameters': {'temperature': 0.7, 'max_tokens': 1500},
            }

            logger.debug("发送 AI 请求: url=%s, model=%s", self.api_url, self.model)

            response = requests.post(
                self.api_url,
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            ai_message = _parse_ai_response(result)

            if not ai_message:
                logger.error("无法解析 AI 响应格式: %s", result)
                return "抱歉，AI 响应格式异常，请稍后再试"

            logger.debug("AI 回复: %s...", ai_message[:100])
            return ai_message

        except Exception:
            logger.exception("AI 对话错误")
            return "抱歉，AI 服务暂时不可用"

    @staticmethod
    def generate_text(prompt, max_tokens=200):
        service = AIService()
        if not service.api_key:
            return "⚠️ AI 功能未配置"

        try:
            payload = {
                'model': service.model,
                'input': {'messages': [{'role': 'user', 'content': prompt}]},
                'parameters': {'temperature': 0.3, 'max_tokens': max_tokens},
            }

            response = requests.post(
                service.api_url,
                headers={'Authorization': f'Bearer {service.api_key}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=8
            )
            response.raise_for_status()

            result = response.json()
            return _parse_ai_response(result) or "抱歉，无法生成摘要"

        except Exception:
            logger.exception("文本生成失败")
            return "抱歉，AI 服务暂时繁忙，请稍后再试。"

    def _build_system_prompt(self, user_data):
        prompt = """你是一个专业的智能日程管理助手，帮助用户分析日程数据并提供可执行的优化建议。

## 回答规范
1. 使用友好的语气，像朋友一样交流
2. 回答要简洁、具体、可执行
3. 使用 **加粗** 强调重点内容
4. 列举条目时使用 - 符号
5. 适当使用空行分隔不同主题

## 你可以帮助用户
- 分析时间安排是否合理
- 评估日程优先级设置是否恰当
- 发现潜在的时间管理问题
- 提供提高效率的具体方法
- 给出工作生活平衡的建议
- 结合完成率数据给出改善方案

如果用户询问与日程管理无关的问题，礼貌地引导回日程管理话题。

注意：日程数据中的时间已转换为北京时间（UTC+8），分析时请基于这个时区判断。"""

        if user_data:
            prompt += "\n\n## 当前用户的日程数据"
            if user_data.get('productive_hours'):
                prompt += f"\n- 高效时段：{', '.join(map(str, user_data['productive_hours']))}点"
            if user_data.get('busy_days'):
                busy_days_str = ', '.join([_WEEKDAY_MAP[d] for d in user_data['busy_days']])
                prompt += f"\n- 繁忙日期：{busy_days_str}"
            if user_data.get('total_tasks'):
                prompt += f"\n- 总任务数：{user_data['total_tasks']}个"
            if user_data.get('completion_rate'):
                prompt += f"\n- 完成率：{user_data['completion_rate']:.1%}"
            if user_data.get('avg_duration'):
                prompt += f"\n- 平均任务时长：{user_data['avg_duration']}分钟"
            if user_data.get('high_priority_ratio'):
                prompt += f"\n- 高优先级任务占比：{user_data['high_priority_ratio']:.0%}"

            prompt += "\n\n基于以上数据，给出有针对性的个性化建议。"

        return prompt

    def generate_ai_recommendations(self, user_statistics):
        try:
            user_id = user_statistics.get('user_id')
            productivity = user_statistics.get('productivity', {})
            weekly = user_statistics.get('weekly_pattern', {})
            duration = user_statistics.get('duration_preference', {})
            priority_dist = user_statistics.get('priority_distribution', {})

            user_data = {
                'productive_hours': productivity.get('productive_hours', []),
                'busy_days': weekly.get('busy_days', []),
                'total_tasks': productivity.get('total_tasks', 0),
                'completion_rate': productivity.get('completion_rate', 0),
                'avg_duration': duration.get('average_duration_minutes', 0),
                'high_priority_ratio': priority_dist.get('high_priority_ratio', 0),
            }

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)

            schedules = Schedule.query.filter(
                Schedule.user_id == user_id,
                Schedule.start_time >= start_date,
                Schedule.start_time <= end_date,
            ).order_by(Schedule.start_time.desc()).all()

            schedule_list = []
            for s in schedules[:30]:
                local_time = s.start_time + timedelta(hours=8)
                schedule_list.append({
                    'time': f"{local_time.strftime('%m-%d %H:%M')}({_WEEKDAY_MAP[local_time.weekday()]})",
                    'title': s.title,
                    'content': s.content or '',
                    'priority': s.priority,
                    'is_recurring': s.is_recurring or False,
                })

            logger.debug("生成 AI 推荐: user_data=%s, schedule_count=%d", user_data, len(schedule_list))

            schedule_details = ""
            if schedule_list:
                schedule_details = "\n【我最近的日程安排】（以下时间均为北京时间 UTC+8）\n"
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
                'content': f"""请根据我的日程数据，给出 4-6 条个性化的日程管理建议。

【我的数据】
- 高效时段：{user_data.get('productive_hours', [])}
- 繁忙日期：{user_data.get('busy_days', [])}
- 总任务数：{user_data.get('total_tasks', 0)}
- 完成率：{user_data.get('completion_rate', 0):.1%}
- 平均任务时长：{user_data.get('avg_duration', 0)}分钟
- 高优先级占比：{user_data.get('high_priority_ratio', 0):.0%}
{schedule_details}

请用以下格式输出（每个建议以【】开头）：

【时间分配】针对时间安排的分析和建议
【效率提升】关于如何提高效率的具体方法
【工作平衡】关于劳逸结合的建议
【习惯养成】关于优化日程习惯的建议
【优先事项】关于任务优先级管理的建议

每条建议不低于 2 句话，包含具体可执行的操作。"""
            }]

            ai_response = self.chat(messages, user_data)

            if not ai_response or ai_response.startswith("抱歉") or ai_response.startswith("⚠️"):
                logger.warning("AI 返回了错误信息，使用默认推荐")
                return [{
                    'type': '时间偏好',
                    'title': 'AI 洞察',
                    'message': '继续记录您的日程，积累更多数据后我将为您提供更精准的分析建议！',
                    'confidence': 0.8,
                }]

            # 类型映射：中文【标题】→ type值
            type_keywords = {
                '时间分配': '时间偏好',
                '效率提升': '效率提升',
                '工作平衡': '日程平衡',
                '习惯养成': '习惯养成',
                '优先事项': '时间偏好',
            }
            title_keywords = {
                '时间分配': '优化时间分配',
                '效率提升': '提升工作效率',
                '工作平衡': '保持工作平衡',
                '习惯养成': '培养良好习惯',
                '优先事项': '管理优先级',
            }

            recommendations = []
            lines = ai_response.split('\n')
            current_rec = None

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue

                # 检测新建议的开始【...】
                section_match = False
                for cn_key, type_val in type_keywords.items():
                    if cn_key in stripped and stripped.startswith('【'):
                        if current_rec:
                            recommendations.append(current_rec)
                        current_rec = {
                            'type': type_val,
                            'title': title_keywords.get(cn_key, 'AI 建议'),
                            'message': stripped,
                            'confidence': 0.85,
                        }
                        section_match = True
                        break

                if section_match:
                    continue

                if current_rec and not stripped.startswith('【'):
                    current_rec['message'] += '\n' + stripped

            if current_rec:
                recommendations.append(current_rec)

            # 如果解析失败，用整段文本兜底
            if not recommendations:
                recommendations.append({
                    'type': 'AI 洞察',
                    'title': '综合分析',
                    'message': ai_response[:500],
                    'confidence': 0.8,
                })

            logger.debug("生成了 %d 条推荐", len(recommendations))
            return recommendations

        except Exception:
            logger.exception("生成 AI 推荐失败")
            return [{
                'type': 'AI 洞察',
                'title': '系统提示',
                'message': '生成推荐时出现错误，请稍后重试',
                'confidence': 0.5,
            }]

    def analyze_recent_schedules(self, user_id, days=7):
        try:
            schedules = Schedule.query.filter(
                Schedule.user_id == user_id,
            ).order_by(Schedule.start_time.desc()).all()

            if not schedules:
                return "您还没有创建任何日程哦～ 快去添加一些日程吧！"

            morning_count = sum(1 for s in schedules if (s.start_time + timedelta(hours=8)).hour < 12)
            afternoon_count = sum(1 for s in schedules if 12 <= (s.start_time + timedelta(hours=8)).hour < 18)
            evening_count = sum(1 for s in schedules if (s.start_time + timedelta(hours=8)).hour >= 18)

            total_count = len(schedules)

            earliest_date = min(s.start_time for s in schedules)
            latest_date = max(s.start_time for s in schedules)
            days_span = (latest_date - earliest_date).days + 1
            avg_per_day = total_count / days_span if days_span > 0 else total_count

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

            titles = [s.title.lower() for s in schedules]
            title_counter = {}
            for title in titles:
                title_counter[title] = title_counter.get(title, 0) + 1

            recurring_activities = [(k, v) for k, v in title_counter.items() if v >= 2]
            if recurring_activities:
                report += "\n\n【习惯发现】\n"
                for title, count in sorted(recurring_activities, key=lambda x: x[1], reverse=True)[:5]:
                    report += f"• '{title}' 出现了{count}次，这是您的固定安排吗？\n"

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

        except Exception:
            logger.exception("分析最近日程失败")
            return "分析失败，请稍后重试"

    def get_schedule_context_for_ai(self, user_id, days=7):
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            schedules = Schedule.query.filter(
                Schedule.user_id == user_id,
                Schedule.start_time >= start_date,
                Schedule.start_time <= end_date,
            ).order_by(Schedule.start_time.desc()).limit(15).all()

            if not schedules:
                return "用户最近没有创建任何日程"

            context = "【用户最近的日程安排】（以下时间均为北京时间 UTC+8）\n"
            for s in schedules:
                local_time = s.start_time + timedelta(hours=8)
                context += f"• {local_time.strftime('%m-%d %H:%M')}({_WEEKDAY_MAP[local_time.weekday()]}) - {s.title}"
                if s.content:
                    context += f" ({s.content[:30]})"
                if s.priority and s.priority >= 4:
                    context += " ⭐重要"
                context += "\n"

            return context.strip()

        except Exception:
            logger.exception("获取日程上下文失败")
            return "无法获取用户日程数据"
