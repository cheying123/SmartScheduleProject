# 创建新文件：d:\SmartScheduleProject\backend\routes\ai.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Conversation, db
from services.ai_service import AIService
from services.user_behavior_analyzer import UserBehaviorAnalyzer
import uuid

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')
ai_service = AIService()

@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """与 AI 进行对话"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        message = data.get('message')
        session_id = data.get('session_id')
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        user_history = Conversation.query.filter_by(
            user_id=current_user_id,
            session_id=session_id
        ).order_by(Conversation.created_at).limit(10).all()
        
        messages = [{'role': conv.role, 'content': conv.message} for conv in user_history]
        
        # 如果是第一条消息，自动添加用户的日程数据
        if len(user_history) == 0:
            schedule_context = ai_service.get_schedule_context_for_ai(current_user_id, days=7)
            initial_message = f"""我的日程数据如下：
{schedule_context}

我的问题是：{message}"""
            messages.append({'role': 'user', 'content': initial_message})
        else:
            messages.append({'role': 'user', 'content': message})
        
        user_stats = {
            'productivity': UserBehaviorAnalyzer.analyze_productivity_hours(current_user_id),
            'weekly_pattern': UserBehaviorAnalyzer.analyze_weekly_pattern(current_user_id)
        }
        
        ai_response = ai_service.chat(messages, user_stats)
        
        user_conv = Conversation(
            user_id=current_user_id,
            role='user',
            message=message,
            session_id=session_id
        )
        
        assistant_conv = Conversation(
            user_id=current_user_id,
            role='assistant',
            message=ai_response,
            session_id=session_id
        )
        
        db.session.add(user_conv)
        db.session.add(assistant_conv)
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'session_id': session_id,
            'message_id': user_conv.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ AI 对话失败：{str(e)}")
        return jsonify({'error': str(e)}), 500 

@ai_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_ai_recommendations():
    """获取 AI 生成的智能推荐"""
    try:
        current_user_id = get_jwt_identity()
        
        user_stats = {
            'productivity': UserBehaviorAnalyzer.analyze_productivity_hours(current_user_id),
            'weekly_pattern': UserBehaviorAnalyzer.analyze_weekly_pattern(current_user_id),
            'duration_preference': UserBehaviorAnalyzer.analyze_task_duration_preference(current_user_id),
            'priority_distribution': UserBehaviorAnalyzer.analyze_priority_distribution(current_user_id),
            'user_id': current_user_id  # 🎯 新增：传递 user_id 用于查询日程
        }
        
        recommendations = ai_service.generate_ai_recommendations(user_stats)
        
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        print(f"❌ 获取 AI 推荐失败：{str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/smart-analysis', methods=['GET'])
@jwt_required()
def get_smart_analysis():
    """获取 AI 对最近日程的智能分析报告"""
    try:
        current_user_id = get_jwt_identity()
        days = request.args.get('days', 7, type=int)
        
        # 获取基础统计
        user_stats = {
            'productivity': UserBehaviorAnalyzer.analyze_productivity_hours(current_user_id),
            'weekly_pattern': UserBehaviorAnalyzer.analyze_weekly_pattern(current_user_id)
        }
        
        # 分析最近的日程
        schedule_report = ai_service.analyze_recent_schedules(current_user_id, days)
        
        # 生成 AI 推荐
        recommendations = ai_service.generate_ai_recommendations(user_stats)
        
        return jsonify({
            'report': schedule_report,
            'recommendations': recommendations,
            'stats': {
                'total_tasks': user_stats['productivity'].get('total_tasks', 0),
                'productive_hours': user_stats['productivity'].get('productive_hours', []),
                'busy_days': user_stats['weekly_pattern'].get('busy_days', [])
            }
        }), 200
        
    except Exception as e:
        print(f"❌ 智能分析失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@ai_bp.route('/conversations/<session_id>', methods=['GET'])
@jwt_required()
def get_conversation_history(session_id):
    """获取指定会话的对话历史"""
    try:
        current_user_id = get_jwt_identity()
        
        conversations = Conversation.query.filter_by(
            user_id=current_user_id,
            session_id=session_id
        ).order_by(Conversation.created_at).all()
        
        return jsonify({
            'session_id': session_id,
            'messages': [conv.to_dict() for conv in conversations]
        }), 200
        
    except Exception as e:
        print(f"❌ 获取对话历史失败：{str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_all_sessions():
    """获取所有会话列表"""
    try:
        current_user_id = get_jwt_identity()
        
        sessions = db.session.query(
            Conversation.session_id,
            db.func.min(Conversation.created_at).label('first_message_time'),
            db.func.max(Conversation.created_at).label('last_message_time')
        ).filter_by(user_id=current_user_id).group_by(
            Conversation.session_id
        ).order_by(
            db.func.max(Conversation.created_at).desc()
        ).all()
        
        return jsonify({
            'sessions': [{
                'session_id': s.session_id,
                'first_message_time': s.first_message_time.strftime('%Y-%m-%d %H:%M:%S') if s.first_message_time else None,
                'last_message_time': s.last_message_time.strftime('%Y-%m-%d %H:%M:%S') if s.last_message_time else None
            } for s in sessions]
        }), 200
        
    except Exception as e:
        print(f"❌ 获取会话列表失败：{str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/conversations/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    """删除指定会话"""
    try:
        current_user_id = get_jwt_identity()
        
        conversations = Conversation.query.filter_by(
            user_id=current_user_id,
            session_id=session_id
        ).all()
        
        for conv in conversations:
            db.session.delete(conv)
        
        db.session.commit()
        
        return jsonify({'message': '会话已删除'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 删除会话失败：{str(e)}")
        return jsonify({'error': str(e)}), 500
    

@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def ai_chat():
    """AI 对话接口，支持日程查询和闲聊"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400

        # 调用 AI 服务生成回复
        response_text = ai_service.chat_with_context(current_user_id, user_message)
        
        return jsonify({
            'reply': response_text,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ AI 聊天失败：{str(e)}")
        return jsonify({'error': str(e)}), 500