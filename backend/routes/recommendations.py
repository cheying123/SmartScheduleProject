# NEW_FILE_CODE
from flask import Blueprint, jsonify
from utils.jwt_utils import token_required
from services.recommendation_engine import generate_schedule_recommendations

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/api')

@recommendations_bp.route('/recommendations', methods=['GET'])
@token_required
def get_recommendations(current_user):
    """获取智能日程推荐"""
    try:
        recommendations = generate_schedule_recommendations(current_user.id)
        return jsonify({'recommendations': recommendations}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500