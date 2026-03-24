import os
import datetime
import requests
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

import jwt
import bcrypt
from functools import wraps

import re
from datetime import timedelta
import jieba
from collections import Counter

from flask_migrate import Migrate

# 导入 AI 解析模块
from ai_parser import parse_with_ai

# --- 1. 初始化和配置 ---
load_dotenv()

app = Flask(__name__)

# 从环境变量读取数据库配置
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

# 检查必要的环境变量是否存在
if not all([db_user, db_password, db_host, db_name]):
    raise ValueError("缺少必要的数据库环境变量配置")

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}}, supports_credentials=True)


QWEATHER_API_KEY = os.getenv('QWEATHER_API_KEY')  # 获取 (和风)QWeather API Key
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')# JWT 密钥
JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 小时

# --- 2. 数据库模型定义 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    
    # 用户偏好设置
    preferred_work_hours = db.Column(db.JSON, nullable=True)  # 偏好工作时间段
    preferred_break_hours = db.Column(db.JSON, nullable=True)  # 偏好休息时间段
    location = db.Column(db.String(255), nullable=True)  # 用户所在城市
    weather_alerts_enabled = db.Column(db.Boolean, default=True)  # 是否启用天气提醒
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_at else None,
            'location': self.location,
            'weather_alerts_enabled': self.weather_alerts_enabled
        }



class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('schedules', lazy=True))
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)  # 结束时间
    weather_info = db.Column(db.String(255), nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)  # 是否重复
    recurring_pattern = db.Column(db.String(50), nullable=True)  # 重复模式：daily, weekly, monthly
    priority = db.Column(db.Integer, default=1)  # 优先级 1-5
    tags = db.Column(db.JSON, nullable=True)  # 标签
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'start_time': self.start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end_time': self.end_time.strftime('%Y-%m-%dT%H:%M:%SZ') if self.end_time else None,
            'weather_info': self.weather_info,
            'is_recurring': self.is_recurring,
            'recurring_pattern': self.recurring_pattern,
            'priority': self.priority,
            'tags': self.tags,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_at else None
        }
    

# 日程冲突记录表
class ScheduleConflict(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule1_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    schedule2_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    conflict_type = db.Column(db.String(50), nullable=True)  # 冲突类型
    suggested_solution = db.Column(db.Text, nullable=True)  # 建议解决方案
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())# --- 3. 天气服务函数 ---


# 用户行为日志表（用于智能推荐）
class UserBehaviorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # 行为类型
    action_data = db.Column(db.JSON, nullable=True)  # 行为数据
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.now())



def get_weather_for_date(city_location_id, date_str):
    """
    获取指定日期的天气预报信息
    city_location_id: 城市 location ID（如北京是 101010100）
    date_str: 日期字符串，格式 YYYY-MM-DD
    """
    if not QWEATHER_API_KEY:
        print("警告：QWEATHER_API_KEY 未配置")
        return "天气 API Key 未配置"
    
    try:
        # 使用 3 天天气预报 API
        url = f"https://mh78m2gduk.re.qweatherapi.com/v7/weather/7d?location={city_location_id}&key={QWEATHER_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # print(f"\n=== 天气查询调试信息 ===")
        # print(f"城市 ID: {city_location_id}")
        # print(f"查询日期：{date_str}")
        # print(f"API 返回码：{data.get('code')}")
        
        if data.get('code') == '200':
            daily_forecasts = data.get('daily', [])
            # print(f"获取到 {len(daily_forecasts)} 天的天气预报")
            
            # 打印所有可用的日期
            for i, forecast in enumerate(daily_forecasts):
                fx_date = forecast.get('fxDate')
                text_day = forecast.get('textDay', '未知')
                temp_min = forecast.get('tempMin', '?')
                temp_max = forecast.get('tempMax', '?')
                # print(f"  第{i}天：{fx_date} - {text_day}, {temp_min}~{temp_max}℃")
            
            # 尝试精确匹配日期
            for daily_forecast in daily_forecasts:
                fx_date = daily_forecast.get('fxDate')
                if fx_date == date_str:
                    text_day = daily_forecast.get('textDay', '未知')
                    temp_min = daily_forecast.get('tempMin', '?')
                    temp_max = daily_forecast.get('tempMax', '?')
                    result = f"{text_day}，气温 {temp_min}~{temp_max}℃"
                    # print(f"✓ 匹配成功：{result}")
                    # print(f"========================\n")
                    return result
            
            # 如果没找到 exact match，尝试获取今天或明天的预报
            from datetime import datetime, timedelta
            today = datetime.now().strftime('%Y-%m-%d')
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            if date_str == today and len(daily_forecasts) > 0:
                # 查询今天但没匹配到，使用第一天的预报
                first_day = daily_forecasts[0]
                text_day = first_day.get('textDay', '未知')
                temp_min = first_day.get('tempMin', '?')
                temp_max = first_day.get('tempMax', '?')
                result = f"{text_day}，气温 {temp_min}~{temp_max}℃"
                print(f"✓ 使用第一天预报（今天）：{result}")
                print(f"========================\n")
                return result
            elif date_str == tomorrow and len(daily_forecasts) > 1:
                # 查询明天，使用第二天的预报
                second_day = daily_forecasts[1]
                text_day = second_day.get('textDay', '未知')
                temp_min = second_day.get('tempMin', '?')
                temp_max = second_day.get('tempMax', '?')
                result = f"{text_day}，气温 {temp_min}~{temp_max}℃"
                print(f"✓ 使用第二天预报（明天）：{result}")
                print(f"========================\n")
                return result
                
        else:
            error_msg = data.get('code', 'Unknown')
            print(f"✗ API 返回错误：{error_msg}")
            
        print(f"✗ 未找到匹配的日期")
        print(f"========================\n")
        return "未能查询到该日天气"
        
    except requests.exceptions.Timeout:
        print("✗ 天气 API 请求超时")
        return "天气服务暂不可用（超时）"
    except requests.exceptions.RequestException as e:
        print(f"✗ 网络请求失败：{e}")
        return "天气服务暂不可用（网络错误）"
    except Exception as e:
        print(f"✗ 天气 API 请求异常：{e}")
        return "天气服务暂不可用"
# 自然语言解析函数
def parse_natural_language(text,timezone_offset=480):
    """
    解析自然语言指令，提取日程信息
    优先使用 AI 解析，失败时使用传统规则解析
    
    :param text: 用户输入的文本
    :param timezone_offset: 时区偏移量（分钟），默认 480（UTC+8）
    :return: 解析后的日程信息
    """
    
     # 尝试使用 AI 解析（传入时区偏移量）
    ai_result = parse_with_ai(text, timezone_offset)
    
    if ai_result:
        print(f"✓ AI 解析成功：{ai_result}")
        return ai_result
    
    print("✗ AI 解析失败，使用传统规则解析")
    
    # AI 解析失败时使用传统规则解析
    result = {
        'title': '',
        'start_time': None,
        'end_time': None,
        'content': '',
        'is_recurring': False,
        'recurring_pattern': None,
        'priority': 1
    }
    
    # 时间关键词映射
    time_keywords = {
        '早上': 8, '上午': 9, '中午': 12, '下午': 14, '傍晚': 17, '晚上': 19, '深夜': 22,
        '点': 0, '点钟': 0, '时': 0
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
    
    # 提取标题（移除时间相关词汇）
    time_patterns = [
        r'安排 (.*?)(?:的 | ？)',
        r'提醒我 (.*?)(?:的 | ？)',
        r'(.*?)会议',
        r'(.*?)活动'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            result['title'] = match.group(1).strip()
            break
    
    if not result['title']:
        result['title'] = text
    
    # 计算日期
    now = datetime.datetime.now()
    target_date = now.date()
    
    # 处理"下周"、"明天"等相对日期
    if '下周' in text:
        days_ahead = 7 - now.weekday() + 7  # 到下週同一天的天数
        target_date = now.date() + timedelta(days=days_ahead)
    elif '明天' in text:
        target_date = now.date() + timedelta(days=1)
    elif '今天' in text:
        target_date = now.date()
    
    # 处理星期几
    for week_name, week_num in week_map.items():
        if week_name in text:
            days_diff = (week_num - now.weekday()) % 7
            if days_diff == 0 and '下' not in text:
                days_diff = 7  # 如果说的是今天之后的下一个该星期
            target_date = now.date() + timedelta(days=days_diff)
            break
    
    # 处理具体时间
    hour = 14  # 默认下午 2 点
    minute = 0
    
    # 提取数字时间（如"两点"、"3 点"）
    chinese_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    
    time_match = re.search(r'([一二三四五六七八九十\d]+)[点时]', text)
    if time_match:
        time_str = time_match.group(1)
        if time_str.isdigit():
            hour = int(time_str)
        elif time_str in chinese_nums:
            hour = chinese_nums[time_str]
        elif time_str == '十':
            hour = 10
        elif '半' in text:
            minute = 30
    
    # 处理"下午"、"上午"等
    if '下午' in text and hour < 12:
        hour += 12
    elif '上午' in text and hour >= 12:
        hour -= 12
    
    # 构建开始时间
    result['start_time'] = datetime.datetime.combine(target_date, datetime.time(hour, minute))
    
    # 默认结束时间为 1 小时后
    result['end_time'] = result['start_time'] + timedelta(hours=1)
    
    # 检查是否是重复性日程
    if '每' in text:
        result['is_recurring'] = True
        if '周' in text:
            result['recurring_pattern'] = 'weekly'
        elif '天' in text or '日' in text:
            result['recurring_pattern'] = 'daily'
        elif '月' in text:
            result['recurring_pattern'] = 'monthly'
    
    # 提取优先级
    if '重要' in text or '紧急' in text:
        result['priority'] = 5
    elif '优先' in text:
        result['priority'] = 4
    elif '一般' in text:
        result['priority'] = 2
    
    return result

# 冲突检测函数
def detect_schedule_conflicts(user_id, new_start_time, new_end_time, exclude_id=None):
    """
    检测日程冲突
    :param user_id: 用户 ID
    :param new_start_time: 新日程开始时间
    :param new_end_time: 新日程结束时间（可以为 None，会自动假设为 1 小时）
    :param exclude_id: 要排除的日程 ID（用于编辑时检查）
    :return: 冲突列表
    """
    conflicts = []
    
     # 如果结束时间为 None，假设持续 1 小时
    if new_end_time is None:
        new_end_time = new_start_time + timedelta(hours=1)

    # 确保传入的时间是 naive datetime
    if new_start_time.tzinfo is not None:
        new_start_time = new_start_time.replace(tzinfo=None)
    if new_end_time.tzinfo is not None:
        new_end_time = new_end_time.replace(tzinfo=None)
    
    # 查询用户的所有日程
    query = Schedule.query.filter_by(user_id=user_id)
    if exclude_id:
        query = query.filter(Schedule.id != exclude_id)
    
    schedules = query.all()
    
    for schedule in schedules:
        # 确保数据库取出的时间也是 naive
        existing_start = schedule.start_time
        if existing_start.tzinfo is not None:
            existing_start = existing_start.replace(tzinfo=None)
        
        # 如果有结束时间，使用结束时间；否则假设持续 1 小时
        if schedule.end_time:
            existing_end = schedule.end_time
            if existing_end.tzinfo is not None:
                existing_end = existing_end.replace(tzinfo=None)
        else:
            existing_end = existing_start + timedelta(hours=1)
        
        # 检查时间重叠
        if (new_start_time < existing_end and new_end_time > existing_start):
            conflicts.append({
                'schedule_id': schedule.id,
                'title': schedule.title,
                'start_time': schedule.start_time,
                'end_time': existing_end,
                'conflict_type': 'time_overlap'
            })
    
    return conflicts

# 智能推荐函数
def generate_schedule_recommendations(user_id):
    """
    基于用户历史日程生成智能推荐
    """
    recommendations = []
    
    # 获取用户的历史日程
    user_schedules = Schedule.query.filter_by(user_id=user_id).order_by(Schedule.start_time).all()
    
    if len(user_schedules) < 3:
        return [{'type': 'info', 'message': '日程数据不足，暂无法提供智能推荐'}]
    
    # 分析用户的工作时间偏好（UTC 转本地时间）
    work_hours = []
    for schedule in user_schedules:
        # 数据库存储的是 UTC 时间，需要转换为本地时间（+8 小时）
        utc_time = schedule.start_time
        local_time = utc_time + timedelta(hours=8)  # 北京时间 UTC+8
        local_hour = local_time.hour
        work_hours.append(local_hour)
    
    if work_hours:
        hour_counter = Counter(work_hours)
        most_common_hour = hour_counter.most_common(1)[0][0]
        
        # 推荐相似时间段安排类似活动
        recommendations.append({
            'type': 'time_preference',
            'message': f'根据历史记录，您通常在{most_common_hour}点安排活动，建议保持这个习惯',
            'suggested_hour': most_common_hour
        })
    
    # 检测是否有足够的休息时间（使用本地时间）
    morning_activities = []
    afternoon_activities = []
    
    for schedule in user_schedules:
        # UTC 转本地时间
        utc_time = schedule.start_time
        local_time = utc_time + timedelta(hours=8)
        local_hour = local_time.hour
        
        if local_hour < 12:
            morning_activities.append(schedule)
        elif 12 <= local_hour < 18:
            afternoon_activities.append(schedule)
    
    if len(morning_activities) > len(afternoon_activities) * 2:
        recommendations.append({
            'type': 'balance',
            'message': '您上午的日程较多，建议适当安排下午的休息时间'
        })
    
    # 检查天气相关的建议（使用本地日期）
    now_beijing = datetime.datetime.now() + timedelta(hours=8)  # 北京时间
    today_beijing = now_beijing.date()
    
    today_schedules = []
    for schedule in user_schedules:
        # UTC 转本地日期
        utc_time = schedule.start_time
        local_date = (utc_time + timedelta(hours=8)).date()
        if local_date == today_beijing:
            today_schedules.append(schedule)
    
    if today_schedules:
        weather_msg = "今天天气情况已更新，请查看具体日程的天气提示"
        recommendations.append({
            'type': 'weather',
            'message': weather_msg
        })
    
    return recommendations

def generate_token(user_id, username):
    """生成 JWT Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

def token_required(f):
    """JWT Token 验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从 Authorization header 获取 token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': '无效的 Token 格式'}), 401
        
        if not token:
            return jsonify({'error': 'Token 缺失'}), 401
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(payload['user_id'])
            if not current_user:
                return jsonify({'error': '用户不存在'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token 已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的 Token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# --- 5. API 接口定义 (注册登录)---
@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '缺少用户名或密码'}), 400
    
    # 验证用户名格式
    if len(data['username']) < 3 or len(data['username']) > 20:
        return jsonify({'error': '用户名长度应在 3-20 个字符之间'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在，请选择其他用户名'}), 409
    
    # 检查邮箱是否已存在（如果提供了邮箱）
    if data.get('email') and User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '邮箱已被注册'}), 409
    
    # TODO: 添加用户名、邮箱、密码的验证逻辑
    # # 检查用户名是否已存在
    # if User.query.filter_by(username=data['username']).first():
    #     return jsonify({'error': '用户名已存在'}), 409
    
    
    try:
        # 密码加密
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        new_user = User(
            username=data['username'],
            password_hash=password_hash,
            email=data.get('email')
        )
        db.session.add(new_user)
        db.session.commit()
        
        # 生成 token
        token = generate_token(new_user.id, new_user.username)
        
        return jsonify({
            'message': '注册成功',
            'user': new_user.to_dict(),
            'token': token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'注册失败：{str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '缺少用户名或密码'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 生成 token
    token = generate_token(user.id, user.username)
    
    return jsonify({
        'message': '登录成功',
        'user': user.to_dict(),
        'token': token
    }), 200

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """获取当前用户信息"""
    return jsonify(current_user.to_dict()), 200

# --- 5. API 接口定义(基础功能) ---
@app.route('/api/schedules', methods=['GET'])
@token_required
def get_schedules(current_user):
    """获取当前用户的所有日程，并自动更新天气信息"""
    schedules = Schedule.query.filter_by(user_id=current_user.id).order_by(Schedule.start_time.asc()).all()
    
    # 自动更新每个日程的天气信息
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    for schedule in schedules:
        schedule_date = schedule.start_time.strftime('%Y-%m-%d')
        
        # 只更新今天和明天的天气（天气预报通常只有 3-7 天）
        if schedule_date == today or schedule_date == tomorrow:
            try:
                weather_info = get_weather_for_date("101010100", schedule_date)
                # 只有当 API 返回有效数据时才更新
                if weather_info and "未能查询" not in weather_info and "API Key" not in weather_info:
                    schedule.weather_info = weather_info
                    print(f"✓ 已更新 {schedule_date} 的天气：{weather_info}")
            except Exception as e:
                print(f"✗ 更新天气失败 {schedule_date}: {e}")
    
    # 提交天气信息更新
    db.session.commit()
    
    return jsonify([s.to_dict() for s in schedules])

@app.route('/api/schedules', methods=['POST'])
@token_required
def create_schedule(current_user):
    """创建新日程"""
    data = request.get_json()
    
    if not data or 'title' not in data or 'start_time' not in data:
        return jsonify({'error': '缺少必要参数 title 或 start_time'}), 400

    try:
        print(f"\n=== 创建日程调试信息 ===")
        print(f"前端传来的原始时间：{data['start_time']}")
        
        # 前端传来的是本地时间的 ISO 字符串（如：2026-03-22T17:54:00）
        # 我们直接将其作为本地时间存储，不做转换
        local_dt = datetime.datetime.fromisoformat(data['start_time'].replace('Z', ''))
        
        print(f"解析后的本地时间：{local_dt}")
        
        schedule_date = local_dt.strftime('%Y-%m-%d')
        weather_info = get_weather_for_date("101010100", schedule_date)
        
        new_schedule = Schedule(
            user_id=current_user.id,
            title=data['title'],
            content=data.get('content', ''),
            start_time=local_dt,  # 直接存储本地时间
            weather_info=weather_info,
            priority=data.get('priority', 1),
            is_recurring=data.get('is_recurring', False),
            recurring_pattern=data.get('recurring_pattern', None)
        )
        db.session.add(new_schedule)
        db.session.commit()
        
        print(f"保存的时间：{new_schedule.start_time}")
        print(f"========================\n")
        
        return jsonify(new_schedule.to_dict()), 201
        
    except ValueError as e:
        print(f"❌ 时间格式错误：{e}")
        return jsonify({'error': f'时间格式错误：{str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建失败：{e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'服务器内部错误：{str(e)}'}), 500

# 更新日程接口以支持冲突检测
@app.route('/api/schedules/<int:id>', methods=['PUT'])
@token_required
def update_schedule(current_user, id):
    schedule = Schedule.query.get_or_404(id)

     # 验证日程是否属于当前用户
     # 觉得没必要，毕竟不同的人的日程相互看不到 (冗余 1)   
    if schedule.user_id != current_user.id:
        return jsonify({'error': '无权操作此日程'}), 403

    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据为空'}), 400
    
    try:
        print(f"\n=== 更新日程调试信息 ===")
        print(f"日程 ID: {id}")
        print(f"前端传来的数据：{data}")
        
        # 如果要修改时间，直接存储为本地时间
        if 'start_time' in data:
            print(f"原始时间字符串：{data['start_time']}")
            
            # 移除 Z 标记，直接解析为本地时间
            time_str = data['start_time'].replace('Z', '')
            local_dt = datetime.datetime.fromisoformat(time_str)
            
            print(f"解析后的本地时间：{local_dt}")
            
            # 计算结束时间（如果没有提供，默认 1 小时）
            end_time = local_dt + timedelta(hours=1)
            if 'end_time' in data:
                end_time_str = data['end_time'].replace('Z', '')
                end_time = datetime.datetime.fromisoformat(end_time_str)
            
            # 检测冲突
            conflicts = detect_schedule_conflicts(
                current_user.id,
                local_dt,
                end_time,
                exclude_id=id
            )
            
            if conflicts:
                print(f"检测到 {len(conflicts)} 个冲突")
                return jsonify({
                    'error': '检测到日程冲突',
                    'conflicts': [{
                        'schedule_id': c['schedule_id'],
                        'title': c['title'],
                        'start_time': c['start_time'].strftime('%Y-%m-%dT%H:%M:%SZ')
                    } for c in conflicts]
                }), 409
            
            schedule.start_time = local_dt
            schedule_date = schedule.start_time.strftime('%Y-%m-%d')
            schedule.weather_info = get_weather_for_date("101010100", schedule_date)
        
        if 'title' in data:
            schedule.title = data['title']
        if 'content' in data:
            schedule.content = data['content']
        if 'priority' in data:
            schedule.priority = int(data['priority'])
        if 'is_recurring' in data:
            # 安全地转换为 bool
            is_rec = data['is_recurring']
            if isinstance(is_rec, str):
                schedule.is_recurring = is_rec.lower() in ['true', '1', 'yes']
            elif isinstance(is_rec, bool):
                schedule.is_recurring = is_rec
            else:
                schedule.is_recurring = bool(is_rec) if is_rec is not None else False
        if 'recurring_pattern' in data:
            schedule.recurring_pattern = data['recurring_pattern'] if data['recurring_pattern'] else None
        
        print(f"更新后的时间：{schedule.start_time}")
        print(f"========================\n")
        
        db.session.commit()
        return jsonify(schedule.to_dict()), 200
        
    except ValueError as e:
        print(f"❌ 时间格式错误：{e}")
        print(f"错误详情：{str(e)}")
        return jsonify({'error': f'时间格式错误：{str(e)}'}), 400
    except Exception as e:
        print(f"❌ 更新失败：{e}")
        print(f"错误类型：{type(e).__name__}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': f'服务器内部错误：{str(e)}'}), 500

@app.route('/api/schedules/<int:id>', methods=['DELETE'])
@token_required
def delete_schedule(current_user, id):
    """删除日程"""
    try:
        schedule = Schedule.query.get_or_404(id)
        
        # 验证日程是否属于当前用户
        # 这里应该只用遍历自己的日程就行了，毕竟你看不到别人的日程(修改1)
        if schedule.user_id != current_user.id:
            return jsonify({'error': '无权操作此日程'}), 403
        
        db.session.delete(schedule)
        db.session.commit()
        return jsonify({'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500
    

@app.route('/api/schedules/natural-language', methods=['POST'])
@token_required
def create_schedule_natural(current_user):
    """使用自然语言创建日程"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': '缺少文本指令'}), 400
    
    # 获取用户时区（默认为 UTC+8，即北京时间）
    timezone_offset = data.get('timezone_offset', 480)  # 分钟
    timezone_str = data.get('timezone', 'UTC+8:00')
    
    try:
        # 解析自然语言（传入时区偏移量）
        parsed_data = parse_natural_language(data['text'], timezone_offset)
        
        print(f"\n📋 解析后的数据（UTC 时间）:")
        print(f"   用户时区：{timezone_str} (偏移量：{timezone_offset} 分钟)")
        print(f"   title: {parsed_data['title']}")
        print(f"   start_time: {parsed_data['start_time']}")
        print(f"   end_time: {parsed_data.get('end_time')}")
        print("-" * 60)
        
        # 检测冲突（使用 UTC 时间）
        conflicts = detect_schedule_conflicts(
            current_user.id,
            parsed_data['start_time'],
            parsed_data.get('end_time')
        )
        
        if conflicts:
            # 转换回用户本地时间显示
            def utc_to_local(utc_dt):
                if utc_dt is None:
                    return None
                return utc_dt + timedelta(minutes=timezone_offset)
            
            return jsonify({
                'error': '检测到日程冲突',
                'conflicts': [{
                    'schedule_id': c['schedule_id'],
                    'title': c['title'],
                    'start_time': utc_to_local(c['start_time']).strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': utc_to_local(c['end_time']).strftime('%Y-%m-%dT%H:%M:%S') if c['end_time'] else None
                } for c in conflicts],
                'parsed_data': {
                    'title': parsed_data['title'],
                    'start_time': utc_to_local(parsed_data['start_time']).strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_time': utc_to_local(parsed_data['end_time']).strftime('%Y-%m-%dT%H:%M:%S') if parsed_data['end_time'] else None
                }
            }), 409
        
        # 获取天气信息（使用用户本地时间的日期）
        local_date = (parsed_data['start_time'] + timedelta(minutes=timezone_offset)).strftime('%Y-%m-%d')
        weather_info = get_weather_for_date("101010100", local_date)
        
        # 创建日程（存储 UTC 时间到数据库）
        new_schedule = Schedule(
            user_id=current_user.id,
            title=parsed_data['title'],
            content=parsed_data.get('content', ''),
            start_time=parsed_data['start_time'],  # UTC 时间
            end_time=parsed_data.get('end_time'),  # UTC 时间
            weather_info=weather_info,
            is_recurring=parsed_data.get('is_recurring', False),
            recurring_pattern=parsed_data.get('recurring_pattern'),
            priority=parsed_data.get('priority', 1)
        )
        
        db.session.add(new_schedule)
        db.session.commit()
        
        # 返回给前端时转换为 UTC 格式（前端自己处理时区转换）
        result = new_schedule.to_dict()
        
        print(f"✅ 日程创建成功:")
        print(f"   数据库存储（UTC）: {result['start_time']}")
        print(f"   用户本地时间：{(parsed_data['start_time'] + timedelta(minutes=timezone_offset)).strftime('%Y-%m-%dT%H:%M:%S')}")
        print("=" * 60)
        
        return jsonify({
            'message': '日程创建成功',
            'schedule': result,
            'ai_parsed': True,
            'timezone_info': {
                'user_timezone': timezone_str,
                'offset_minutes': timezone_offset
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建日程失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'解析失败：{str(e)}'}), 500

# 新增：获取智能推荐
@app.route('/api/recommendations', methods=['GET'])
@token_required
def get_recommendations(current_user):
    """获取智能日程推荐"""
    try:
        recommendations = generate_schedule_recommendations(current_user.id)
        return jsonify({'recommendations': recommendations}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 新增：检查冲突
@app.route('/api/schedules/check-conflict', methods=['POST'])
@token_required
def check_conflict(current_user):
    """检查指定时间段是否有冲突"""
    data = request.get_json()
    
    if not data or 'start_time' not in data or 'end_time' not in data:
        return jsonify({'error': '缺少开始或结束时间'}), 400
    
    try:
        start_time = datetime.datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = datetime.datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        conflicts = detect_schedule_conflicts(current_user.id, start_time, end_time)
        
        return jsonify({
            'has_conflict': len(conflicts) > 0,
            'conflicts': [{
                'schedule_id': c['schedule_id'],
                'title': c['title'],
                'start_time': c['start_time'].strftime('%Y-%m-%dT%H:%M:%SZ'),
                'end_time': c['end_time'].strftime('%Y-%m-%dT%H:%M:%SZ')
            } for c in conflicts]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


# --- 5. 启动服务 ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)