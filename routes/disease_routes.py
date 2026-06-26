# -*- coding: utf-8 -*-
"""病症路由"""
from flask import Blueprint, request, jsonify
from database import get_db

disease_bp = Blueprint("disease", __name__)


@disease_bp.route("/api/diseases", methods=["GET"])
def list_diseases():
    """分页查询病症"""
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    
    conn = get_db()
    conditions = []
    params = []
    
    if search:
        conditions.append("(d.name LIKE ? OR d.description LIKE ?)")
        like_val = "%" + search + "%"
        params.extend([like_val, like_val])
    if category:
        conditions.append("d.category = ?")
        params.append(category)
    
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    count_sql = "SELECT COUNT(*) FROM disease d" + where
    total = conn.execute(count_sql, params).fetchone()[0]
    
    offset = (page - 1) * page_size
    sql = "SELECT d.* FROM disease d" + where + " ORDER BY d.cloud_id DESC LIMIT ? OFFSET ?"
    rows = conn.execute(sql, params + [page_size, offset]).fetchall()
    conn.close()
    
    return jsonify({"success": True, "items": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size})


@disease_bp.route("/api/diseases/<cloud_id>", methods=["GET"])
def get_disease(cloud_id):
    """获取单个病症详情"""
    conn = get_db()
    disease = conn.execute("SELECT * FROM disease WHERE cloud_id = ?", (cloud_id,)).fetchone()
    conn.close()
    
    if not disease:
        return jsonify({"success": False, "error": "病症不存在"}), 404
    
    result = dict(disease)
    # 获取相关药材
    conn = get_db()
    herbs = conn.execute("""
        SELECT h.tcmbank_id, h.name, hd.indication
        FROM herb_disease hd
        JOIN herb h ON hd.herb_tcmbank_id = h.tcmbank_id
        WHERE hd.disease_cloud_id = ?
    """, (cloud_id,)).fetchall()
    result["herbs"] = [dict(h) for h in herbs]
    conn.close()
    
    return jsonify({"success": True, "data": result})
