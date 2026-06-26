# -*- coding: utf-8 -*-
"""数据导入路由"""
import os
import uuid
from flask import Blueprint, request, jsonify
from services.import_service import ImportService
from database import get_db

import_bp = Blueprint("import", __name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


@import_bp.route("/api/import/preview", methods=["POST"])
def preview_import():
    """预览上传文件"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未上传文件"}), 400
    file = request.files["file"]
    file_type = request.form.get("type", "csv")
    if file.filename == "":
        return jsonify({"success": False, "error": "文件名为空"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_type == "csv" and ext != "csv":
        return jsonify({"success": False, "error": "文件扩展名与类型不匹配"}), 400
    if file_type == "json" and ext != "json":
        return jsonify({"success": False, "error": "文件扩展名与类型不匹配"}), 400
    if file_type == "excel" and ext not in ("xlsx", "xls"):
        return jsonify({"success": False, "error": "文件扩展名与类型不匹配"}), 400

    filename = str(uuid.uuid4()) + "." + ext
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    try:
        result = ImportService.preview_file(filepath, file_type)
        result["temp_file"] = filename
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": "文件解析失败: " + str(e)}), 400


@import_bp.route("/api/import/confirm", methods=["POST"])
def confirm_import():
    """确认导入"""
    data = request.get_json()
    temp_file = data.get("temp_file")
    file_type = data.get("type", "csv")
    entity_type = data.get("entity_type")

    if not temp_file or not entity_type:
        return jsonify({"success": False, "error": "参数不完整"}), 400

    filepath = os.path.join(UPLOAD_DIR, temp_file)
    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "临时文件不存在，请重新上传"}), 400

    try:
        result = ImportService.import_data(filepath, file_type, entity_type)
        os.remove(filepath)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": "导入失败: " + str(e)}), 400


@import_bp.route("/api/stats", methods=["GET"])
def get_stats():
    """获取统计数据"""
    conn = get_db()
    herb_count = conn.execute("SELECT COUNT(*) FROM herb").fetchone()[0]
    disease_count = conn.execute("SELECT COUNT(*) FROM disease").fetchone()[0]
    comp_count = conn.execute("SELECT COUNT(*) FROM chemical_component").fetchone()[0]
    treat_count = conn.execute("SELECT COUNT(*) FROM herb_disease").fetchone()[0]

    # 最近动态
    recent = conn.execute("""
        SELECT 'herb' AS type, name AS title, created_at FROM herb
        UNION ALL
        SELECT 'disease', name, created_at FROM disease
        UNION ALL
        SELECT 'component', name, created_at FROM chemical_component
        ORDER BY created_at DESC LIMIT 10
    """).fetchall()

    # 性味分布
    taste_dist = conn.execute("""
        SELECT nature, COUNT(*) AS cnt FROM herb WHERE nature != '' GROUP BY nature ORDER BY cnt DESC
    """).fetchall()

    conn.close()
    return jsonify({"success": True, "data": {
        "counts": {
            "herbs": herb_count,
            "diseases": disease_count,
            "components": comp_count,
            "treatments": treat_count
        },
        "recent": [dict(r) for r in recent],
        "nature_distribution": [dict(t) for t in taste_dist]
    }})