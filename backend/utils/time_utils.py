from datetime import datetime, timedelta


def utc_to_local(utc_dt, timezone_offset_minutes=480):
    """
    将 UTC 时间转换为本地时间
    
    Args:
        utc_dt: UTC 时间（datetime 对象或 ISO 字符串）
        timezone_offset_minutes: 时区偏移量（分钟），默认 480（UTC+8）
        
    Returns:
        本地时间（datetime 对象）
    """
    if isinstance(utc_dt, str):
        utc_dt = datetime.fromisoformat(utc_dt.replace('Z', ''))
    
    return utc_dt + timedelta(minutes=timezone_offset_minutes)


def local_to_utc(local_dt, timezone_offset_minutes=480):
    """
    将本地时间转换为 UTC 时间
    
    Args:
        local_dt: 本地时间（datetime 对象或 ISO 字符串）
        timezone_offset_minutes: 时区偏移量（分钟），默认 480（UTC+8）
        
    Returns:
        UTC 时间（datetime 对象）
    """
    if isinstance(local_dt, str):
        local_dt = datetime.fromisoformat(local_dt.replace('Z', ''))
    
    return local_dt - timedelta(minutes=timezone_offset_minutes)


def get_timezone_info():
    """
    获取当前时区信息
    
    Returns:
        包含时区信息的字典
    """
    now = datetime.now()
    timezone_offset = -now.timestamp() % (24 * 3600) / 60
    offset_hours = int(abs(timezone_offset) // 60)
    offset_minutes = int(abs(timezone_offset) % 60)
    
    sign = '+' if timezone_offset >= 0 else '-'
    
    return {
        'offset_minutes': timezone_offset,
        'offset_hours': offset_hours,
        'offset_minutes_str': f"{sign}{offset_hours}:{str(offset_minutes).zfill(2)}",
        'timezone_name': f"UTC{sign}{offset_hours}:{str(offset_minutes).zfill(2)}"
    }


def format_datetime(dt, format_string='%Y-%m-%d %H:%M:%S'):
    """
    格式化日期时间对象
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', ''))
    
    return dt.strftime(format_string)


def parse_datetime(date_string, formats=None):
    """
    解析日期时间字符串
    """
    if formats is None:
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d',
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"无法解析日期字符串：{date_string}")


def is_past_time(dt, timezone_offset_minutes=480):
    """
    判断给定时间是否已经过去
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', ''))
    
    now = datetime.utcnow() + timedelta(minutes=timezone_offset_minutes)
    
    dt_date = datetime(dt.year, dt.month, dt.day)
    now_date = datetime(now.year, now.month, now.day)
    
    return dt_date < now_date


def get_relative_date(days=0, weeks=0, months=0):
    """
    获取相对日期
    """
    now = datetime.now()
    
    total_days = days + (weeks * 7)
    
    if months != 0:
        new_month = now.month + months
        new_year = now.year + (new_month - 1) // 12
        new_month = ((new_month - 1) % 12) + 1
        
        import calendar
        last_day_of_month = calendar.monthrange(new_year, new_month)[1]
        new_day = min(now.day, last_day_of_month)
        
        result = now.replace(year=new_year, month=new_month, day=new_day)
    else:
        result = now + timedelta(days=total_days)
    
    return result