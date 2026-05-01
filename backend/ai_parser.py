"""
AI 自然语言解析服务
使用大模型 API 解析语音识别文本，提取日程信息
"""
import os
import re
import json
import logging
import requests
from datetime import datetime, timedelta
from config import Config
from utils.time_utils import convert_to_datetime

logger = logging.getLogger(__name__)

AI_API_KEY = os.environ.get('AI_API_KEY')
AI_API_URL = os.environ.get('AI_API_URL', Config.AI_API_URL)
AI_MODEL = os.environ.get('AI_MODEL', Config.AI_MODEL)

_RESPONSE_PATHS = [
    lambda x: x['choices'][0]['message']['content'],
    lambda x: x['choices'][0]['delta']['content'],
    lambda x: x['output']['choices'][0]['message']['content'],
    lambda x: x['output']['choices'][0]['text'],
    lambda x: x['result'],
    lambda x: x['response'],
]


def check_ai_config():
    return bool(AI_API_KEY)


def parse_with_ai(text, timezone_offset=480):
    if not check_ai_config():
        logger.debug("未配置 AI_API_KEY，将使用传统规则解析")
        return None

    now = datetime.now()
    current_date_str = now.strftime('%Y年%m月%d日')
    current_weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()]

    this_wednesday = now + timedelta(days=(2 - now.weekday()) % 7)
    next_wednesday = this_wednesday + timedelta(days=7)
    next_monday = now + timedelta(days=(7 - now.weekday()) % 7)

    weekday_map = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

    prompt = f"""
请将用户的自然语言输入解析为结构化的日程信息。

上下文信息：
- 当前日期：{current_date_str} ({current_weekday})
- 今天是：{now.strftime('%Y年%m月%d日')} ({current_weekday})
- 这周三：{this_wednesday.strftime('%Y年%m月%d日')} ({weekday_map[this_wednesday.weekday()]})
- 下周三：{next_wednesday.strftime('%Y年%m月%d日')} ({weekday_map[next_wednesday.weekday()]})
- 下周一：{next_monday.strftime('%Y年%m月%d日')} ({weekday_map[next_monday.weekday()]})

用户输入：{text}

请严格按照以下 JSON 格式返回结果，不要有任何其他文字：
{{"title": "...", "start_time": "YYYY-MM-DDTHH:MM:SS", "end_time": "YYYY-MM-DDTHH:MM:SS", "content": "...", "is_recurring": false, "recurring_pattern": null, "priority": 1}}
"""

    logger.debug("开始 AI 解析: %s", text)

    payload = {
        'model': AI_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.05,
    }

    try:
        response = requests.post(
            AI_API_URL,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            logger.error("AI API 请求失败，状态码: %d", response.status_code)
            return None

        result = extract_json_from_response(response.json())

        if result:
            logger.debug("AI 解析成功: %s", json.dumps(result, ensure_ascii=False))
            if result.get('start_time'):
                result['start_time'] = convert_to_datetime(result['start_time'], timezone_offset)
            if result.get('end_time'):
                result['end_time'] = convert_to_datetime(result['end_time'], timezone_offset)
            return result
        else:
            logger.error("无法从 AI 响应中解析 JSON")
            return None

    except requests.exceptions.Timeout:
        logger.error("AI API 请求超时")
        return None
    except requests.exceptions.RequestException as e:
        logger.error("AI API 请求异常: %s", e)
        return None
    except Exception:
        logger.exception("AI 解析过程中发生异常")
        return None


def extract_json_from_response(response_data):
    content = None
    for path_func in _RESPONSE_PATHS:
        try:
            content = path_func(response_data)
            break
        except (KeyError, IndexError, TypeError):
            continue

    if content is None:
        return None

    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


def validate_and_normalize(data: dict, timezone_offset_minutes: int = 480) -> dict:
    normalized = {
        'title': data.get('title', '').strip(),
        'content': data.get('content', ''),
        'start_time': data.get('start_time'),
        'end_time': data.get('end_time'),
        'is_recurring': bool(data.get('is_recurring', False)),
        'recurring_pattern': data.get('recurring_pattern'),
        'priority': int(data.get('priority', 1)),
        'tags': data.get('tags', []),
    }

    if not normalized['title']:
        normalized['title'] = '未命名日程'

    if not 1 <= normalized['priority'] <= 5:
        normalized['priority'] = 1

    if normalized['is_recurring'] and normalized['recurring_pattern'] not in ('daily', 'weekly', 'monthly'):
        normalized['recurring_pattern'] = None
        normalized['is_recurring'] = False

    if isinstance(normalized['start_time'], str):
        try:
            normalized['start_time'] = datetime.fromisoformat(normalized['start_time'])
        except (ValueError, TypeError):
            normalized['start_time'] = None

    if isinstance(normalized['end_time'], str):
        try:
            normalized['end_time'] = datetime.fromisoformat(normalized['end_time'])
        except (ValueError, TypeError):
            normalized['end_time'] = None

    if normalized['start_time'] and not normalized['end_time']:
        normalized['end_time'] = normalized['start_time'] + timedelta(hours=1)

    if normalized['start_time']:
        normalized['start_time'] = normalized['start_time'] - timedelta(minutes=timezone_offset_minutes)
    if normalized['end_time']:
        normalized['end_time'] = normalized['end_time'] - timedelta(minutes=timezone_offset_minutes)

    return normalized


if __name__ == '__main__':
    test_texts = [
        "安排下周三下午两点的团队会议",
        "提醒我每周一早上检查邮箱",
        "明天上午 9 点与客户见面",
    ]

    for text in test_texts:
        result = parse_with_ai(text)
        if result:
            print(f"输入：{text}\n输出：{json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"输入：{text}\n输出：AI 解析失败，将使用传统方法")