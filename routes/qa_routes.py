# -*- coding: utf-8 -*-
"""智能问答路由 - 使用 Agent 工作链"""
from flask import Blueprint, request, jsonify
from services.agent_qa import AgentQA

qa_bp = Blueprint("qa", __name__)


@qa_bp.route("/api/qa/search", methods=["POST"])
def search():
    """Agent 工作链式问答搜索"""
    data = request.get_json()
    question = data.get("question", "")
    model = data.get("model", "agnes-2.0-flash")
    
    if not question:
        return jsonify({"success": False, "error": "问题不能为空"}), 400
    
    try:
        # 使用 Agent 工作链
        result = AgentQA.chat(question, model=model)
        
        # 保存问答记录
        from services.knowledge_service import QAService
        QAService.save_qa(
            question, 
            result["answer"], 
            None, 
            result.get("model")
        )
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@qa_bp.route("/api/qa/history", methods=["GET"])
def history():
    """获取问答历史"""
    from services.knowledge_service import QAService
    limit = int(request.args.get("limit", 20))
    records = QAService.get_recent_qa(limit)
    return jsonify({"success": True, "data": records})


@qa_bp.route("/api/qa/rate", methods=["POST"])
def rate():
    """评价问答"""
    from services.knowledge_service import QAService
    data = request.get_json()
    qa_id = data.get("qa_id")
    rating = data.get("rating")
    feedback = data.get("feedback")
    
    if not qa_id:
        return jsonify({"success": False, "error": "qa_id 不能为空"}), 400
    
    QAService.rate_qa(qa_id, rating, feedback)
    return jsonify({"success": True})
