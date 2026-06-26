# -*- coding: utf-8 -*-
"""测试 Disease 同步各步骤"""
import sys
sys.path.insert(0, '.')
from services.neo4j_service import _run_query_stream
import time

# 步骤1: 收集 disease names
print("步骤 1: 收集 Disease names...")
start = time.time()
all_disease_names = set()
count = 0
for batch_data in _run_query_stream("MATCH (n:Disease) RETURN properties(n) AS props", batch_size=5000):
    for rec in batch_data:
        props = rec["props"]
        cloud_id = props.get("id:ID(Disease)", "")
        name = props.get("name:String", "")
        if cloud_id and name:
            all_disease_names.add(name)
        count += 1
    print(f"  已收到批次, 累计: {count}, 唯一 names: {len(all_disease_names)}")
elapsed = time.time() - start
print(f"步骤1 完成: 总记录 {count}, 唯一 names {len(all_disease_names)}, 耗时 {elapsed:.2f}s")

# 步骤2: 批量 INSERT
print("步骤 2: 批量 INSERT...")
from database import get_db
db = get_db()
start = time.time()
db.executemany("INSERT OR IGNORE INTO disease (name) VALUES (?)", [(n,) for n in all_disease_names])
db.commit()
elapsed = time.time() - start
print(f"步骤2 完成: 耗时 {elapsed:.2f}s")

# 步骤3: 批量查询 id
print("步骤 3: 批量查询 id...")
start = time.time()
disease_name_to_id = {}
name_list = list(all_disease_names)
for i in range(0, len(name_list), 1000):
    batch_names = name_list[i:i+1000]
    query = "SELECT name, id FROM disease WHERE name IN (" + ",".join(["?"] * len(batch_names)) + ")"
    for name, row_id in db.execute(query, batch_names).fetchall():
        disease_name_to_id[name] = row_id
elapsed = time.time() - start
print(f"步骤3 完成: 映射 {len(disease_name_to_id)} 条, 耗时 {elapsed:.2f}s")

# 步骤4: 批量更新属性
print("步骤 4: 批量更新 Disease 属性...")
start = time.time()
batch = []
update_count = 0
for batch_data in _run_query_stream("MATCH (n:Disease) RETURN properties(n) AS props", batch_size=5000):
    for rec in batch_data:
        props = rec["props"]
        name = props.get("name:String", "")
        if name not in disease_name_to_id:
            continue
        batch.append((
            props.get("category:String", "") or "",
            (props.get("description:String", "") or "")[:500],
            disease_name_to_id[name],
        ))
        update_count += 1
        if len(batch) >= 2000:
            db.executemany("UPDATE disease SET category=?, description=? WHERE id=?", batch)
            db.commit()
            batch = []
if batch:
    db.executemany("UPDATE disease SET category=?, description=? WHERE id=?", batch)
    db.commit()
elapsed = time.time() - start
print(f"步骤4 完成: 更新 {update_count} 条, 耗时 {elapsed:.2f}s")

db.close()
print(f"\n总计耗时: {time.time() - start:.2f}s")
