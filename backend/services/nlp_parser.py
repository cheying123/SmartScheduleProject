import re
import logging
from datetime import datetime, timedelta, time
from config import Config
from ai_parser import parse_with_ai as ai_parse

logger = logging.getLogger(__name__)


def parse_natural_language(text: str, timezone_offset: int = 480) -> dict:
    ai_result = _parse_with_ai(text, timezone_offset)

    if ai_result:
        logger.debug("AI 解析成功")
        ai_result['ai_parsed'] = True
        return ai_result

    logger.debug("AI 解析失败，使用传统规则解析")
    return _parse_with_rules(text, timezone_offset)


def _parse_with_ai(text: str, timezone_offset_minutes: int = 480) -> dict:
    if not Config.AI_API_KEY:
        return None

    try:
        return ai_parse(text, timezone_offset_minutes)
    except Exception:
        logger.exception("AI 解析异常")
        return None


def _parse_with_rules(text: str, timezone_offset: int = 480) -> dict:
    """
    使用规则解析自然语言文本
    
    Args:
        text: 文本内容
        timezone_offset: 时区偏移量（分钟）
        
    Returns:
        解析后的日程信息
    """
    result = {
        'title': '',
        'start_time': None,
        'end_time': None,
        'content': '',
        'is_recurring': False,
        'recurring_pattern': None,
        'priority': 1,
        'tags': [],
        'ai_parsed': False
    }
    
    # 星期映射
    week_map = {
        '周一': 0, '星期一': 0,
        '周二': 1, '星期二': 1,
        '周三': 2, '星期三': 2,
        '周四': 3, '星期四': 3,
        '周五': 4, '星期五': 4,
        '周六': 5, '星期六': 5,
        '周日': 6, '星期天': 6, '星期日': 6
    }
    
    now = datetime.utcnow() + timedelta(minutes=timezone_offset)
    target_date = now.date()
    
    # 处理相对日期
    if '下周' in text:
        days_ahead = 7 - now.weekday() + 7
        target_date = now.date() + timedelta(days=days_ahead)
    elif '明天' in text:
        target_date = now.date() + timedelta(days=1)
    elif '后天' in text:
        target_date = now.date() + timedelta(days=2)
    elif '今天' in text:
        target_date = now.date()
    
    # 处理星期几
    for week_name, week_num in week_map.items():
        if week_name in text:
            days_diff = (week_num - now.weekday()) % 7
            if days_diff == 0 and '下' not in text:
                days_diff = 7
            target_date = now.date() + timedelta(days=days_diff)
            break
    
    # 处理时间
    hour = 14
    minute = 0
    
    time_match = re.search(r'([一二三四五六七八九十\d]+)[点时]', text)
    if time_match:
        time_str = time_match.group(1)
        chinese_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        
        if time_str.isdigit():
            hour = int(time_str)
        elif time_str in chinese_nums:
            hour = chinese_nums[time_str]
        elif time_str == '十':
            hour = 10
        
        if '半' in text:
            minute = 30
    
    if '下午' in text and hour < 12:
        hour += 12
    elif '上午' in text and hour >= 12:
        hour -= 12
    elif '早上' in text and hour >= 12:
        hour -= 12
    
    result['start_time'] = datetime.combine(target_date, time(hour, minute)) - timedelta(minutes=timezone_offset)
    result['end_time'] = result['start_time'] + timedelta(hours=1)
    
    # 提取标题
    title = ''
    title_patterns = [
        r'(?:帮我|给我|请)?安排[一下]*(.+?)(?:的|$|？)',
        r'(?:帮我|给我|请)?提醒我(.+?)(?:的|$|？)',
        r'(?:帮我|给我|请)?记(?:录|下)(.+?)(?:的|$|？)',
        r'(?:帮我|给我|请)?创建(.+?)(?:的|$|？)',
        r'(?:帮我|给我|请)?添加(.+?)(?:的|$|？)',
    ]

    for pattern in title_patterns:
        match = re.search(pattern, text)
        if match:
            title = match.group(1).strip()
            break

    # 如果上面的没匹配到：去掉常见前缀和时间词后取剩余文本
    if not title:
        cleaned = re.sub(r'(?:帮我|给我|请|麻烦你|安排|提醒|记一下|记下|创建|添加)\s*', '', text)
        cleaned = re.sub(r'(?:明天|后天|今天|下周|下个|下周|这周|这个)\s*', '', cleaned)
        cleaned = re.sub(r'[上下]午\s*', '', cleaned)
        cleaned = re.sub(r'\d+\s*[点时]\s*\d*\s*分?', '', cleaned)
        cleaned = re.sub(r'(?:的|了|吧|嘛)$', '', cleaned)
        title = cleaned.strip()

    # 去掉尾部残留的时间介词和结构助词
    title = re.sub(r'(?:在|于|从|到|的)$', '', title).strip()

    if title:
        result['title'] = title
    else:
        result['title'] = text
    
    # 检查重复
    if '每' in text:
        result['is_recurring'] = True
        if '周' in text:
            result['recurring_pattern'] = 'weekly'
        elif '天' in text or '日' in text:
            result['recurring_pattern'] = 'daily'
        elif '月' in text:
            result['recurring_pattern'] = 'monthly'
    
    # 优先级
    if '重要' in text or '紧急' in text:
        result['priority'] = 5
    elif '优先' in text:
        result['priority'] = 4
    elif '一般' in text:
        result['priority'] = 2
    
    return result