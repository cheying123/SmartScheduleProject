# NEW_FILE_CODE
from flask import Blueprint, request, jsonify
from extensions import db
from models.user import User
from utils.jwt_utils import generate_token, token_required
import bcrypt

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '缺少用户名或密码'}), 400
    
    if len(data['username']) < 3 or len(data['username']) > 20:
        return jsonify({'error': '用户名长度应在 3-20 个字符之间'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在'}), 409
    
    if data.get('email') and User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '邮箱已被注册'}), 409
    
    try:
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        new_user = User(
            username=data['username'],
            password_hash=password_hash,
            email=data.get('email')
        )
        db.session.add(new_user)
        db.session.commit()
        
        token = generate_token(new_user.id, new_user.username)
        
        return jsonify({
            'message': '注册成功',
            'user': new_user.to_dict(),
            'token': token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'注册失败：{str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '缺少用户名或密码'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    token = generate_token(user.id, user.username)
    
    return jsonify({
        'message': '登录成功',
        'user': user.to_dict(),
        'token': token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """获取当前用户信息"""
    return jsonify(current_user.to_dict()), 200