# -*- coding: utf-8 -*-
"""药材路由"""
from flask import Blueprint, request, jsonify
from services.herb_service import HerbService

herb_bp = Blueprint("herb", __name__)


@herb_bp.route("/api/herbs", methods=["GET"])
def list_herbs():
    search = request.args.get("search", "")
    nature = request.args.get("nature", "")
    taste = request.args.get("taste", "")
    meridian = request.args.get("meridian", "")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    result = HerbService.list_herbs(search, nature, taste, meridian, page, page_size)
    return jsonify({"success": True, **result})


@herb_bp.route("/api/herbs/all", methods=["GET"])
def all_herbs_simple():
    """获取所有药材简要列表（下拉选择用）"""
    result = HerbService.get_all_simple()
    return jsonify({"success": True, "data": result})


@herb_bp.route("/api/herbs/<herb_id>", methods=["GET"])
def get_herb(herb_id):
    result = HerbService.get_herb(herb_id)
    if result is None:
        return jsonify({"success": False, "error": "药材不存在"}), 404
    return jsonify({"success": True, "data": result})


@herb_bp.route("/api/herbs", methods=["POST"])
def create_herb():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"success": False, "error": "药材名称不能为空"}), 400
    result = HerbService.create_herb(data)
    return jsonify({"success": True, "data": result}), 201


@herb_bp.route("/api/herbs/<herb_id>", methods=["PUT"])
def update_herb(herb_id):
    data = request.get_json()
    result = HerbService.update_herb(herb_id, data)
    return jsonify({"success": True, "data": result})


@herb_bp.route("/api/herbs/<herb_id>", methods=["DELETE"])
def delete_herb(herb_id):
    result = HerbService.delete_herb(herb_id)
    return jsonify({"success": True, "data": result})