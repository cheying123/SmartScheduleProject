"""
AI 自然语言解析服务
使用大模型 API 解析语音识别文本，提取日程信息
"""
import os
import json
import requests
from dotenv import load_dotenv
import datetime
from datetime import timedelta
load_dotenv()

# AI API 配置（以通义千问为例，可根据需要切换）
AI_API_KEY = os.getenv('AI_API_KEY', '')  # 在 .env 文件中配置
AI_API_URL = os.getenv('AI_API_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
AI_MODEL = os.getenv('AI_MODEL', 'qwen-turbo')


def parse_with_ai(text: str, timezone_offset_minutes: int = 480) -> dict:
    """
    使用 AI 解析自然语言文本，提取日程信息
    
    Args:
        text: 语音识别后的文本
        
    Returns:
        解析后的日程信息字典
    """
    if not AI_API_KEY:
        # 如果没有配置 AI API Key，返回 None 使用传统解析方法
        print("=" * 60)
        print("⚠️ 未配置 AI_API_KEY，将使用传统规则解析")
        print("=" * 60)
        return None
    
    # 计算时区信息
    offset_hours = timezone_offset_minutes // 60
    offset_minutes = abs(timezone_offset_minutes) % 60
    sign = '+' if timezone_offset_minutes >= 0 else '-'
    timezone_str = f"UTC{sign}{offset_hours}:{str(offset_minutes).zfill(2)}"
    
    # 获取当前日期时间（根据用户时区）
    now = datetime.datetime.utcnow() + timedelta(minutes=timezone_offset_minutes)
    current_date_str = now.strftime("%Y年%m月%d日 %H:%M")
    weekday_map = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    current_weekday = weekday_map[now.weekday()]
    
     # 计算具体的相对日期示例
    tomorrow = now + timedelta(days=1)
    day_after_tomorrow = now + timedelta(days=2)
    
    # 计算下一个星期一的日期
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # 如果今天是周一，"下周一"是下周
    next_monday = now + timedelta(days=days_until_monday)
    
    # 计算下一个星期三的日期
    days_until_wednesday = (2 - now.weekday()) % 7
    if days_until_wednesday == 0:
        days_until_wednesday = 7
    next_wednesday = now + timedelta(days=days_until_wednesday)

    # 构建提示词 - 添加当前日期信息
    prompt = f"""
你是一个智能日程助手，请从以下用户输入中提取日程信息，并以 JSON 格式返回。

【重要信息】
当前日期时间：{current_date_str} ({current_weekday})
用户时区：{timezone_str}

用户输入："{text}"

请提取以下字段：
- title: 日程标题（必填，简洁明了）
- content: 日程详细内容（可选）
- start_time: 开始时间（ISO 8601 格式，如：2024-01-15T14:00:00）
- end_time: 结束时间（ISO 8601 格式，可选）
- is_recurring: 是否重复（布尔值）
- recurring_pattern: 重复模式（daily/weekly/monthly，仅在重复时填写）
- priority: 优先级（1-5 的整数，1 为普通，5 为非常重要）
- tags: 标签数组（可选）

- 今天：{now.strftime('%Y年%m月%d日')} ({current_weekday})
- 明天：{tomorrow.strftime('%Y年%m月%d日')} ({weekday_map[tomorrow.weekday()]})
- 后天：{day_after_tomorrow.strftime('%Y年%m月%d日')} ({weekday_map[day_after_tomorrow.weekday()]})
- 下周一：{next_monday.strftime('%Y年%m月%d日')} ({weekday_map[next_monday.weekday()]})
- 下周三：{next_wednesday.strftime('%Y年%m月%d日')} ({weekday_map[next_wednesday.weekday()]})



【时间转换规则 - 必须严格遵守】
1. 必须根据上面提供的【日期计算参考】来转换相对时间
2. 具体计算方法：
   - "明天" = {tomorrow.strftime('%Y年%m月%d日')}
   - "后天" = {day_after_tomorrow.strftime('%Y年%m月%d日')}
   - "下周一" = {next_monday.strftime('%Y年%m月%d日')}（注意：不是本周一，是下周一）
   - "下周三" = {next_wednesday.strftime('%Y年%m月%d日')}
   - "这周五" = 本周五，如果今天是周五之后则是下周五
   - "上午 9 点" = 09:00
   - "早上 6 点" = 06:00
   - "下午 2 点" = 14:00
   - "晚上 8 点" = 20:00
3. 如果只说了时间没有说日期，默认是今天
4. 所有时间必须转换为 ISO 8601 格式：YYYY-MM-DDTHH:MM:SS
5. 返回的时间是用户本地时区的时间（{timezone_str}）
6. 如果某些字段无法确定，可以留空或使用默认值
7. 只返回 JSON 对象，不要有其他说明文字

【示例 - 基于今天的实际日期】
假设今天是 {now.strftime('%Y年%m月%d日')} ({current_weekday})，用户在 {timezone_str} 时区：

用户说："明天早上 9 点与客户见面"
明天的日期是：{tomorrow.strftime('%Y年%m月%d日')}
{{
    "title": "与客户见面",
    "content": "",
    "start_time": "{tomorrow.strftime('%Y-%m-%d')}T09:00:00",
    "end_time": "{tomorrow.strftime('%Y-%m-%d')}T10:00:00",
    "is_recurring": false,
    "recurring_pattern": null,
    "priority": 2,
    "tags": ["工作"]
}}

用户说："下周一早上 6 点叫我起床"
下周一的日期是：{next_monday.strftime('%Y年%m月%d日')}
{{
    "title": "叫起床",
    "content": "",
    "start_time": "{next_monday.strftime('%Y-%m-%d')}T06:00:00",
    "end_time": "{next_monday.strftime('%Y-%m-%d')}T06:05:00",
    "is_recurring": false,
    "recurring_pattern": null,
    "priority": 1,
    "tags": []
}}
"""

    try:
        print("\n" + "=" * 60)
        print("🤖 开始 AI 解析")
        print("=" * 60)
        print(f"📝 用户输入：{text}")
        print(f"🌍 用户时区：{timezone_str} (偏移量：{timezone_offset_minutes} 分钟)")
        print(f"📅 当前日期：{current_date_str} ({current_weekday})")
        print(f"📆 日期参考:")
        print(f"   今天：{now.strftime('%Y年%m月%d日')} ({current_weekday})")
        print(f"   明天：{tomorrow.strftime('%Y年%m月%d日')} ({weekday_map[tomorrow.weekday()]})")
        print(f"   下周一：{next_monday.strftime('%Y年%m月%d日')} ({weekday_map[next_monday.weekday()]})")
        print(f"   下周三：{next_wednesday.strftime('%Y年%m月%d日')} ({weekday_map[next_wednesday.weekday()]})")
        print("-" * 60)
        
        # 调用 AI API
        headers = {
            'Authorization': f'Bearer {AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': AI_MODEL,
            'input': {
                'messages': [
                    {
                        'role': 'system',
                        'content': f'你是一个专业的日程助手，擅长从自然语言中提取结构化的日程信息。你会根据用户提供的具体日期计算参考，准确地将相对时间（如"明天"、"下周一"）转换为正确的日期。'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            },
            'parameters': {
                'temperature': 0.1,  # 降低温度，让输出更精确
                'max_tokens': 500
            }
        }
        
        print("📤 发送到 AI 的请求内容:")
        print(f"   URL: {AI_API_URL}")
        print(f"   Model: {AI_MODEL}")
        print(f"   Temperature: 0.1 (更精确)")
        print(f"   User Prompt (前 500 字符): {prompt[:500]}...")
        print("-" * 60)
        
        response = requests.post(AI_API_URL, headers=headers, json=payload, timeout=10)
        
        print(f"📥 收到 AI 响应 - 状态码：{response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # 打印完整的响应
            print("-" * 60)
            print("✅ AI 返回的完整 JSON 响应:")
            import json
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print("-" * 60)
            
            # 解析 AI 返回的结果
            ai_output = result.get('output', {}).get('text', '')
            print(f"📄 AI 返回的原始文本:\n{ai_output}")
            print("-" * 60)
            
            # 清理输出，提取 JSON 部分
            json_start = ai_output.find('{')
            json_end = ai_output.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_output[json_start:json_end]
                print(f"🔍 提取到的 JSON 字符串:\n{json_str}")
                
                parsed_data = json.loads(json_str)
                
                print("-" * 60)
                print("📋 AI 解析的原始数据（用户本地时间）:")
                print(json.dumps(parsed_data, ensure_ascii=False, indent=2))
                print("-" * 60)
                
                # 验证和补充必要字段，并转换为 UTC
                final_result = validate_and_normalize(parsed_data, timezone_offset_minutes)
                
                print("✅ 标准化后的最终结果（已转换为 UTC）:")
                print(json.dumps({
                    'title': final_result['title'],
                    'content': final_result['content'],
                    'start_time': final_result['start_time'].isoformat() if final_result['start_time'] else None,
                    'end_time': final_result['end_time'].isoformat() if final_result['end_time'] else None,
                    'is_recurring': final_result['is_recurring'],
                    'recurring_pattern': final_result['recurring_pattern'],
                    'priority': final_result['priority'],
                    'tags': final_result['tags']
                }, ensure_ascii=False, indent=2))
                print("=" * 60)
                print("✨ AI 解析完成\n")
                
                return final_result
            else:
                print(f"❌ AI 返回格式异常，未找到 JSON 对象：{ai_output}")
                print("=" * 60)
                return None
        else:
            print(f"❌ AI API 请求失败：{response.status_code}")
            print(f"响应内容：{response.text}")
            print("=" * 60)
            return None
            
    except Exception as e:
        print(f"❌ AI 解析异常：{e}")
        import traceback
        print(traceback.format_exc())
        print("=" * 60)
        return None

def validate_and_normalize(data: dict, timezone_offset_minutes: int = 480) -> dict:
    """
    验证和标准化 AI 解析结果，并将本地时间转换为 UTC
    
    Args:
        data: AI 解析的原始数据（本地时间）
        timezone_offset_minutes: 时区偏移量（分钟）
        
    Returns:
        标准化后的数据（UTC 时间）
    """
    normalized = {
        'title': data.get('title', '').strip(),
        'content': data.get('content', ''),
        'start_time': data.get('start_time'),
        'end_time': data.get('end_time'),
        'is_recurring': bool(data.get('is_recurring', False)),
        'recurring_pattern': data.get('recurring_pattern'),
        'priority': int(data.get('priority', 1)),
        'tags': data.get('tags', [])
    }
    
    # 确保有标题
    if not normalized['title']:
        normalized['title'] = '未命名日程'
    
    # 确保优先级在有效范围
    if not 1 <= normalized['priority'] <= 5:
        normalized['priority'] = 1
    
    # 确保重复模式有效
    if normalized['is_recurring'] and normalized['recurring_pattern'] not in ['daily', 'weekly', 'monthly']:
        normalized['recurring_pattern'] = None
        normalized['is_recurring'] = False
    
    # 确保 start_time 是 datetime 对象或可以解析的字符串
    if isinstance(normalized['start_time'], str):
        try:
            from datetime import datetime
            normalized['start_time'] = datetime.fromisoformat(normalized['start_time'])
        except:
            normalized['start_time'] = None
    
    # 确保 end_time 是 datetime 对象或可以解析的字符串
    if isinstance(normalized['end_time'], str):
        try:
            from datetime import datetime
            normalized['end_time'] = datetime.fromisoformat(normalized['end_time'])
        except:
            normalized['end_time'] = None
    
    # 如果 start_time 存在但 end_time 不存在，设置默认结束时间为开始后 1 小时
    if normalized['start_time'] and not normalized['end_time']:
        normalized['end_time'] = normalized['start_time'] + timedelta(hours=1)
    
    # 将用户本地时间转换为 UTC 时间存储到数据库
    # UTC = 本地时间 - 时区偏移量
    if normalized['start_time']:
        normalized['start_time'] = normalized['start_time'] - timedelta(minutes=timezone_offset_minutes)
    
    if normalized['end_time']:
        normalized['end_time'] = normalized['end_time'] - timedelta(minutes=timezone_offset_minutes)
    
    return normalized


# 测试函数
if __name__ == '__main__':
    test_texts = [
        "安排下周三下午两点的团队会议",
        "提醒我每周一早上检查邮箱",
        "明天上午 9 点与客户见面"
    ]
    
    for text in test_texts:
        print(f"\n输入：{text}")
        result = parse_with_ai(text)
        if result:
            print(f"输出：{json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print("输出：AI 解析失败，将使用传统方法")