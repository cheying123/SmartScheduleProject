import jwt
import datetime
from config import Config

def generate_token(user_id, username):
    """生成 JWT Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')


def token_required(f):
    """JWT Token 验证装饰器"""
    from functools import wraps
    from flask import request, jsonify
    from models.user import User
    from extensions import db
    
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': '无效的 Token 格式'}), 401
        
        if not token:
            return jsonify({'error': 'Token 缺失'}), 401
        
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(payload['user_id'])
            if not current_user:
                return jsonify({'error': '用户不存在'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token 已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的 Token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated