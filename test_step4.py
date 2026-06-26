# -*- coding: utf-8 -*-
"""只测试步骤 4"""
import sys
sys.path.insert(0, '.')
from services.neo4j_service import _run_query_stream
from database import get_db
import time

db = get_db()

# 步骤 3 的映射（硬编码测试）
print("步骤 3: 建立映射...")
name_list = list(set(["Disease_" + str(i) for i in range(100)]))
disease_name_to_id = {}
for i, name in enumerate(name_list):
    db.execute("INSERT OR IGNORE INTO disease (name) VALUES (?)", (name,))
db.commit()
for name in name_list:
    row = db.execute("SELECT id FROM disease WHERE name = ?", (name,)).fetchone()
    if row:
        disease_name_to_id[name] = row[0]
print(f"  映射 {len(disease_name_to_id)} 条")

# 步骤 4: 只取前 100 条测试
print("步骤 4: 测试小批量...")
start = time.time()
batch = []
count = 0
for batch_data in _run_query_stream("MATCH (n:Disease) RETURN properties(n) AS props LIMIT 100", batch_size=100):
    print(f"  收到批次: {len(batch_data)} 条")
    for rec in batch_data:
        props = rec["props"]
        name = props.get("name:String", "")
        if name in disease_name_to_id:
            batch.append((props.get("category:String", "") or "", ""[:500], disease_name_to_id[name]))
            count += 1
            if len(batch) >= 10:
                db.executemany("UPDATE disease SET category=?, description=? WHERE id=?", batch)
                db.commit()
                batch = []
if batch:
    db.executemany("UPDATE disease SET category=?, description=? WHERE id=?", batch)
    db.commit()
elapsed = time.time() - start
print(f"小批量测试完成: {count} 条, 耗时 {elapsed:.2f}s")

db.close()
