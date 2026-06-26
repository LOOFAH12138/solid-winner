# -*- coding: utf-8 -*-
"""化学成分服务层"""
from database import get_db


class ComponentService:

    @staticmethod
    def list_components(search="", formula="", herb_id="", page=1, page_size=10):
        conn = get_db()
        conditions = []
        params = []

        if search:
            conditions.append("(c.name LIKE ? OR c.cas_number LIKE ?)")
            like_val = "%" + search + "%"
            params.extend([like_val, like_val])
        if formula:
            conditions.append("c.formula LIKE ?")
            params.append("%" + formula + "%")
        if herb_id:
            conditions.append("c.herb_id = ?")
            params.append(herb_id)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        total = conn.execute("SELECT COUNT(*) FROM chemical_component c" + where, params).fetchone()[0]

        offset = (page - 1) * page_size
        rows = conn.execute("""
            SELECT c.*, h.name AS herb_name
            FROM chemical_component c
            LEFT JOIN herb h ON c.herb_id = h.tcmbank_id
            """ + where + " ORDER BY c.cloud_id DESC LIMIT ? OFFSET ?",
            params + [page_size, offset]
        ).fetchall()
        conn.close()
        return {"items": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def get_component(cloud_id):
        conn = get_db()
        comp = conn.execute("""
            SELECT c.*, h.name AS herb_name
            FROM chemical_component c
            LEFT JOIN herb h ON c.herb_id = h.tcmbank_id
            WHERE c.cloud_id = ?
        """, (cloud_id,)).fetchone()
        conn.close()
        return dict(comp) if comp else None

    @staticmethod
    def create_component(data):
        return {"error": "从 CSV 导入的数据不支持手动创建"}

    @staticmethod
    def update_component(cloud_id, data):
        return {"error": "从 CSV 导入的数据不支持手动更新"}

    @staticmethod
    def delete_component(cloud_id):
        return {"error": "从 CSV 导入的数据不支持手动删除"}
