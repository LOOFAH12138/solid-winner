# -*- coding: utf-8 -*-
"""测试 sync_from_neo4j 各步骤耗时"""
import ssl
import time
import sqlite3
from neo4j import GraphDatabase

URI = "neo4j://e92008e6.databases.neo4j.io:7687"
USER = "e92008e6"
PWD = "ggiHLVb04FTPl2FWcOfkTsWMM2aLy-JTXLTCyhq6K6E"
DB = "e92008e6"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

d = GraphDatabase.driver(URI, auth=(USER, PWD), ssl_context=ctx)
db = sqlite3.connect("tcm_data.db")
db.row_factory = sqlite3.Row

# 测试 Disease 同步
print("测试 Disease 节点同步:")

# 步骤1: 查询并收集 name
start = time.time()
all_disease_names = set()
count = 0
with d.session(database=DB) as s:
    result = s.run("MATCH (n:Disease) RETURN properties(n) AS props")
    for rec in result:
        props = rec["props"]
        cloud_id = props.get("id:ID(Disease)", "")
        name = props.get("name:String", "")
        if cloud_id and name:
            all_disease_names.add(name)
        count += 1
        if count % 10000 == 0:
            print(f"  已处理 {count} 条")
print(f"  步骤1 (收集 names): {time.time() - start:.2f}s, 共 {len(all_disease_names)} 个唯一 name")

# 步骤2: 批量 INSERT
start = time.time()
for name_batch in [list(all_disease_names)[i:i+1000] for i in range(0, len(all_disease_names), 1000)]:
    db.executemany("INSERT OR IGNORE INTO disease (name) VALUES (?)", [(n,) for n in name_batch])
db.commit()
print(f"  步骤2 (批量 INSERT): {time.time() - start:.2f}s")

# 步骤3: 批量查询 id
start = time.time()
disease_name_to_id = {}
for name_batch in [list(all_disease_names)[i:i+1000] for i in range(0, len(all_disease_names), 1000)]:
    query = "SELECT name, id FROM disease WHERE name IN (" + ",".join(["?"] * len(name_batch)) + ")"
    for name, row_id in db.execute(query, name_batch).fetchall():
        disease_name_to_id[name] = row_id
print(f"  步骤3 (批量查询 id): {time.time() - start:.2f}s, 共 {len(disease_name_to_id)} 个映射")

d.close()
db.close()
