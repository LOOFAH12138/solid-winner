# -*- coding: utf-8 -*-
"""优化的同步函数——每批 INSERT 后批量查询 id"""
import sys
sys.path.insert(0, '.')
from services.neo4j_service import _run_query_stream
from database import get_db
import time

def sync_optimized():
    """优化版：每批数据 INSERT 后立即查询该批的 id，避免逐条查询"""
    db = get_db()
    
    def get_field(props, key, default=""):
        val = props.get(key, "")
        if not val:
            base_key = key.rsplit(":", 1)[0] if ":" in key else field_key
            val = props.get(base_key, default)
        return val or default

    # ========== 1. Herb ==========
    print("同步 Herb...")
    herb_map = {}  # cloud_id -> sqlite_id
    batch_insert = []  # 待插入的 name
    batch_update = []  # 准备好更新的记录
    
    for batch_data in _run_query_stream("MATCH (n:Herb) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            cloud_id = props.get("id:ID(Herb)", "")
            name = props.get("name:String", "")
            if not cloud_id or not name:
                continue
            batch_insert.append(name)
            batch_update.append({
                "cloud_id": cloud_id,
                "props": props,
            })
        
        # 批量 INSERT
        if batch_insert:
            db.executemany("INSERT OR IGNORE INTO herb (name) VALUES (?)", [(n,) for n in batch_insert])
            db.commit()
            
            # 批量查询这些 name 的 id
            name_list = list(set(batch_insert))
            for i in range(0, len(name_list), 1000):
                batch_names = name_list[i:i+1000]
                query = "SELECT name, id FROM herb WHERE name IN (" + ",".join(["?"] * len(batch_names)) + ")"
                name_to_id = {}
                for name, row_id in db.execute(query, batch_names).fetchall():
                    name_to_id[name] = row_id
            
            # 批量更新属性
            update_batch = []
            for item in batch_update:
                name = batch_insert[item["cloud_id"]]  # 需要重新关联
                props = item["props"]
                if name in name_to_id:
                    sqlite_id = name_to_id[name]
                    # 找到对应的 cloud_id
                    cloud_id = None
                    for j, bname in enumerate(batch_insert):
                        if bname == name:
                            cloud_id = item["cloud_id"]
                            break
                    
                    update_batch.append((
                        get_field(props, "latinName:String"),
                        get_field(props, "category:String"),
                        get_field(props, "nature:String"),
                        get_field(props, "flavor:String"),
                        get_field(props, "meridian:String"),
                        get_field(props, "efficacy"),
                        get_field(props, "toxicity:String"),
                        get_field(props, "dosage:String"),
                        get_field(props, "description:String")[:500],
                        get_field(props, "pinyin:String"),
                        get_field(props, "englishName:String"),
                        get_field(props, "use_part:String"),
                        get_field(props, "indication:String"),
                        get_field(props, "therapeutic_cn_class:String"),
                        get_field(props, "id:ID(Herb)", ""),
                        sqlite_id,
                    ))
            
            if update_batch:
                db.executemany("""UPDATE herb SET latin_name=?, category=?, nature=?, taste=?, meridian=?,
                    efficacy=?, toxicity=?, dosage=?, description=?, pinyin_name=?, tcm_name_en=?,
                    use_part=?, indication=?, therapeutic_cn_class=?, tcmbank_id=? WHERE id=?""", update_batch)
                db.commit()
        
        # 构建 herb_map
        for i, name in enumerate(batch_insert):
            # 需要找到对应的 cloud_id
            pass
        
        batch_insert = []
        batch_update = []
    
    print("  Herb 同步完成")
    db.close()

if __name__ == "__main__":
    sync_optimized()
