# -*- coding: utf-8 -*-
"""简化的同步函数——一次查询完成插入和更新"""
import sys
sys.path.insert(0, '.')
from services.neo4j_service import _run_query_stream
from database import get_db
import time

def sync_simple():
    """简化版同步：每批数据先插入 SQLite，再在同一批中更新属性"""
    db = get_db()
    
    def get_field(props, key, default=""):
        val = props.get(key, "")
        if not val:
            base_key = key.rsplit(":", 1)[0] if ":" in key else key
            val = props.get(base_key, default)
        return val or default

    # ========== 1. Herb ==========
    print("同步 Herb...")
    herb_map = {}  # cloud_id -> sqlite_id
    batch = []
    count = 0
    for batch_data in _run_query_stream("MATCH (n:Herb) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            cloud_id = props.get("id:ID(Herb)", "")
            name = props.get("name:String", "")
            if not cloud_id or not name:
                continue
            
            # INSERT OR IGNORE
            db.execute("INSERT OR IGNORE INTO herb (name) VALUES (?)", (name,))
            # 获取 id
            row = db.execute("SELECT id FROM herb WHERE name = ?", (name,)).fetchone()
            if not row:
                continue
            sqlite_id = row[0]
            herb_map[cloud_id] = sqlite_id
            
            # 准备更新
            batch.append((
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
            count += 1
            if len(batch) >= 1000:
                db.executemany("""UPDATE herb SET latin_name=?, category=?, nature=?, taste=?, meridian=?,
                    efficacy=?, toxicity=?, dosage=?, description=?, pinyin_name=?, tcm_name_en=?,
                    use_part=?, indication=?, therapeutic_cn_class=?, tcmbank_id=? WHERE id=?""", batch)
                db.commit()
                batch = []
    if batch:
        db.executemany("""UPDATE herb SET latin_name=?, category=?, nature=?, taste=?, meridian=?,
            efficacy=?, toxicity=?, dosage=?, description=?, pinyin_name=?, tcm_name_en=?,
            use_part=?, indication=?, therapeutic_cn_class=?, tcmbank_id=? WHERE id=?""", batch)
        db.commit()
    print(f"  Herb: {count} 条, map: {len(herb_map)}")
    
    # ========== 2. Disease ==========
    print("同步 Disease...")
    disease_map = {}
    batch = []
    count = 0
    for batch_data in _run_query_stream("MATCH (n:Disease) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            cloud_id = props.get("id:ID(Disease)", "")
            name = props.get("name:String", "")
            if not cloud_id or not name:
                continue
            
            db.execute("INSERT OR IGNORE INTO disease (name) VALUES (?)", (name,))
            row = db.execute("SELECT id FROM disease WHERE name = ?", (name,)).fetchone()
            if not row:
                continue
            sqlite_id = row[0]
            disease_map[cloud_id] = sqlite_id
            
            batch.append((
                get_field(props, "category:String"),
                get_field(props, "description:String")[:500],
                sqlite_id,
            ))
            count += 1
            if len(batch) >= 2000:
                db.executemany("UPDATE disease SET category=?, description=? WHERE id=?", batch)
                db.commit()
                batch = []
    if batch:
        db.executemany("UPDATE disease SET category=?, description=? WHERE id=?", batch)
        db.commit()
    print(f"  Disease: {count} 条, map: {len(disease_map)}")
    
    # ========== 3. Ingredient ==========
    print("同步 Ingredient...")
    comp_map = {}
    batch = []
    count = 0
    for batch_data in _run_query_stream("MATCH (n) WHERE 'Ingredient' IN labels(n) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            cloud_id = props.get("id:ID(Ingredient)", "")
            name = props.get("name:String", "")
            if not cloud_id or not name:
                continue
            
            db.execute("INSERT OR IGNORE INTO chemical_component (name) VALUES (?)", (name,))
            row = db.execute("SELECT id FROM chemical_component WHERE name = ?", (name,)).fetchone()
            if not row:
                continue
            sqlite_id = row[0]
            comp_map[cloud_id] = sqlite_id
            
            batch.append((
                get_field(props, "molecularFormula:String"),
                get_field(props, "casNumber:String"),
                sqlite_id,
            ))
            count += 1
            if len(batch) >= 2000:
                db.executemany("UPDATE chemical_component SET formula=?, cas_number=? WHERE id=?", batch)
                db.commit()
                batch = []
    if batch:
        db.executemany("UPDATE chemical_component SET formula=?, cas_number=? WHERE id=?", batch)
        db.commit()
    print(f"  Ingredient: {count} 条, map: {len(comp_map)}")
    
    # ========== 4. TREATS 关系 ==========
    print("同步 TREATS 关系...")
    treat_count = 0
    batch = []
    for batch_data in _run_query_stream("MATCH (h)-[r:TREATS]->(d) RETURN h, d, r", batch_size=5000):
        for rec in batch_data:
            h = rec["h"]
            d = rec["d"]
            h_id = h.get("id:ID(Herb)", "")
            d_id = d.get("id:ID(Disease)", "")
            if h_id in herb_map and d_id in disease_map:
                indication = get_field(rec["r"], "indication:String", "")
                batch.append((herb_map[h_id], disease_map[d_id], indication[:200]))
                treat_count += 1
                if len(batch) >= 1000:
                    db.executemany(
                        "INSERT OR IGNORE INTO herb_disease (herb_id, disease_id, relationship_type, evidence_level) VALUES (?, ?, 'TREATS', ?)",
                        batch
                    )
                    db.commit()
                    batch = []
    if batch:
        db.executemany(
            "INSERT OR IGNORE INTO herb_disease (herb_id, disease_id, relationship_type, evidence_level) VALUES (?, ?, 'TREATS', ?)",
            batch
        )
        db.commit()
    print(f"  TREATS: {treat_count}")
    
    # ========== 5. FOUND_IN 关系 ==========
    print("同步 FOUND_IN 关系...")
    contains_count = 0
    batch = []
    for batch_data in _run_query_stream("MATCH (ing)-[r:FOUND_IN]->(h) RETURN ing, h, r", batch_size=5000):
        for rec in batch_data:
            ing = rec["ing"]
            h = rec["h"]
            ing_id = ing.get("id:ID(Ingredient)", "")
            h_id = h.get("id:ID(Herb)", "")
            if ing_id in comp_map and h_id in herb_map:
                batch.append((herb_map[h_id], comp_map[ing_id]))
                contains_count += 1
                if len(batch) >= 1000:
                    db.executemany("UPDATE chemical_component SET herb_id=? WHERE id=?", batch)
                    db.commit()
                    batch = []
    if batch:
        db.executemany("UPDATE chemical_component SET herb_id=? WHERE id=?", batch)
        db.commit()
    print(f"  CONTAINS: {contains_count}")
    
    db.close()
    print("同步完成!")

if __name__ == "__main__":
    sync_simple()
