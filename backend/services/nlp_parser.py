from flask import current_app
import re
from datetime import datetime, timedelta
from config import Config


def parse_natural_language(text: str, timezone_offset: int = 480) -> dict:
    """
    解析自然语言指令，提取日程信息
    
    采用双层解析策略：
    1. 优先使用 AI 解析（更智能，支持复杂语义）
    2. AI 失败时使用规则解析（快速、可靠）
    
    Args:
        text: 用户输入的文本
        timezone_offset: 时区偏移量（分钟），默认 480（UTC+8）
        
    Returns:
        解析后的日程信息字典
    """
    
    # 第一层：尝试 AI 解析
    ai_result = _parse_with_ai(text, timezone_offset)
    
    if ai_result:
        print(f"✓ AI 解析成功")
        ai_result['ai_parsed'] = True
        return ai_result
    
    # 第二层：AI 失败，使用规则解析
    print("✗ AI 解析失败，使用传统规则解析")
    return _parse_with_rules(text, timezone_offset)


def _parse_with_ai(text: str, timezone_offset_minutes: int = 480) -> dict:
    """
    使用 AI 解析自然语言文本
    
    Args:
        text: 文本内容
        timezone_offset_minutes: 时区偏移量（分钟）
        
    Returns:
        AI 解析结果，失败返回 None
    """
    if not Config.AI_API_KEY:
        return None
    
    try:
        from ai_parser import parse_with_ai as ai_parse
        return ai_parse(text, timezone_offset_minutes)
    except Exception as e:
        print(f"AI 解析异常：{e}")
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
    
    result['start_time'] = datetime.combine(target_date, datetime.time(hour, minute))
    result['end_time'] = result['start_time'] + timedelta(hours=1)
    
    # 提取标题
    title_patterns = [
        r'安排 (.*?)(?:的 | ？)',
        r'提醒我 (.*?)(?:的 | ？)',
        r'(.*?)会议',
        r'(.*?)活动'
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, text)
        if match:
            result['title'] = match.group(1).strip()
            break
    
    if not result['title']:
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