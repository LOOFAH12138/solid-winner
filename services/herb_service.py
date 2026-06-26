# -*- coding: utf-8 -*-
"""药材服务层"""
from database import get_db


class HerbService:

    @staticmethod
    def list_herbs(search="", nature="", taste="", meridian="", page=1, page_size=10):
        conn = get_db()
        conditions = []
        params = []

        if search:
            conditions.append("(h.name LIKE ? OR h.latin_name LIKE ? OR h.pinyin_name LIKE ?)")
            like_val = "%" + search + "%"
            params.extend([like_val, like_val, like_val])
        if nature:
            conditions.append("h.nature = ?")
            params.append(nature)
        if taste:
            conditions.append("h.taste LIKE ?")
            params.append("%" + taste + "%")
        if meridian:
            conditions.append("h.meridian LIKE ?")
            params.append("%" + meridian + "%")

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        count_sql = "SELECT COUNT(*) FROM herb h" + where
        total = conn.execute(count_sql, params).fetchone()[0]

        offset = (page - 1) * page_size
        sql = "SELECT h.* FROM herb h" + where + " ORDER BY h.tcmbank_id DESC LIMIT ? OFFSET ?"
        rows = conn.execute(sql, params + [page_size, offset]).fetchall()
        conn.close()

        return {
            "items": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    def get_herb(tcmbank_id):
        conn = get_db()
        herb = conn.execute("SELECT * FROM herb WHERE tcmbank_id = ?", (tcmbank_id,)).fetchone()
        if not herb:
            conn.close()
            return None
        result = dict(herb)
        # 关联成分
        comps = conn.execute("""
            SELECT cc.cloud_id, cc.name, cc.formula, cc.cas_number, cc.bioactivity
            FROM chemical_component cc
            WHERE cc.herb_id = ?
        """, (tcmbank_id,)).fetchall()
        result["components"] = [dict(c) for c in comps]
        
        # 关联病症 (herb_disease)
        treats = conn.execute("""
            SELECT hd.disease_cloud_id, d.name as disease_name, hd.indication
            FROM herb_disease hd
            JOIN disease d ON hd.disease_cloud_id = d.cloud_id
            WHERE hd.herb_tcmbank_id = ?
        """, (tcmbank_id,)).fetchall()
        result["treatments"] = [dict(t) for t in treats]
        
        conn.close()
        return result

    @staticmethod
    def create_herb(data):
        # 注意：从 CSV 导入的数据不应该手动创建
        return {"error": "从 CSV 导入的数据不支持手动创建"}

    @staticmethod
    def update_herb(tcmbank_id, data):
        # 注意：从 CSV 导入的数据不应该手动更新
        return {"error": "从 CSV 导入的数据不支持手动更新"}

    @staticmethod
    def delete_herb(tcmbank_id):
        # 注意：从 CSV 导入的数据不应该手动删除
        return {"error": "从 CSV 导入的数据不支持手动删除"}

    @staticmethod
    def get_all_simple():
        """获取所有药材的简要信息（用于下拉选择）"""
        conn = get_db()
        rows = conn.execute("SELECT tcmbank_id AS id, name FROM herb ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]
