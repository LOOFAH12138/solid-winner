# -*- coding: utf-8 -*-
"""化学成分路由"""
from flask import Blueprint, request, jsonify
from services.component_service import ComponentService

component_bp = Blueprint("component", __name__)


@component_bp.route("/api/components", methods=["GET"])
def list_components():
    search = request.args.get("search", "")
    formula = request.args.get("formula", "")
    herb_id = request.args.get("herb_id", "")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    result = ComponentService.list_components(search, formula, herb_id, page, page_size)
    return jsonify({"success": True, **result})


@component_bp.route("/api/components/<component_id>", methods=["GET"])
def get_component(component_id):
    result = ComponentService.get_component(component_id)
    if result is None:
        return jsonify({"success": False, "error": "成分不存在"}), 404
    return jsonify({"success": True, "data": result})


@component_bp.route("/api/components", methods=["POST"])
def create_component():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"success": False, "error": "成分名称不能为空"}), 400
    result = ComponentService.create_component(data)
    return jsonify({"success": True, "data": result}), 201


@component_bp.route("/api/components/<component_id>", methods=["PUT"])
def update_component(component_id):
    data = request.get_json()
    result = ComponentService.update_component(component_id, data)
    return jsonify({"success": True, "data": result})


@component_bp.route("/api/components/<component_id>", methods=["DELETE"])
def delete_component(component_id):
    result = ComponentService.delete_component(component_id)
    return jsonify({"success": True, "data": result})