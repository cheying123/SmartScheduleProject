from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from services.user_behavior_analyzer import UserBehaviorAnalyzer
from models.user import User
from extensions import db
import traceback

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/productivity-hours', methods=['GET'])
@jwt_required()
def get_productivity_hours():
    """获取用户的高效工作时间段"""
    try:
        current_user_id = get_jwt_identity()
        print(f"✅ Token 解析成功，用户 ID: {current_user_id}")
        
        days = request.args.get('days', 30, type=int)
        
        result = UserBehaviorAnalyzer.analyze_productivity_hours(current_user_id, days)
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ 错误详情：{str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/weekly-pattern', methods=['GET'])
@jwt_required()
def get_weekly_pattern():
    """获取用户的周模式"""
    try:
        current_user_id = get_jwt_identity()
        print(f"✅ Token 解析成功，用户 ID: {current_user_id}")
        
        weeks = request.args.get('weeks', 4, type=int)
        
        result = UserBehaviorAnalyzer.analyze_weekly_pattern(current_user_id, weeks)
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ 错误详情：{str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """获取个性化智能推荐"""
    try:
        current_user_id = get_jwt_identity()
        print(f"✅ Token 解析成功，用户 ID: {current_user_id}")
        
        recommendations = UserBehaviorAnalyzer.generate_personalized_recommendations(current_user_id)
        return jsonify({'recommendations': recommendations}), 200
    except Exception as e:
        print(f"❌ 错误详情：{str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_full_statistics():
    """获取完整的用户行为统计"""
    try:
        current_user_id = get_jwt_identity()
        print(f"✅ Token 解析成功，用户 ID: {current_user_id}")
        
        stats = {
            'productivity': UserBehaviorAnalyzer.analyze_productivity_hours(current_user_id),
            'weekly_pattern': UserBehaviorAnalyzer.analyze_weekly_pattern(current_user_id),
            'duration_preference': UserBehaviorAnalyzer.analyze_task_duration_preference(current_user_id),
            'priority_distribution': UserBehaviorAnalyzer.analyze_priority_distribution(current_user_id)
        }
        
        return jsonify(stats), 200
    except Exception as e:
        print(f"❌ 错误详情：{str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500