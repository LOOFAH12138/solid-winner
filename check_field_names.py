# -*- coding: utf-8 -*-
"""验证 Python neo4j 驱动的字段名格式"""
import ssl
from neo4j import GraphDatabase

URI = "neo4j://e92008e6.databases.neo4j.io:7687"
USER = "e92008e6"
PWD = "ggiHLVb04FTPl2FWcOfkTsWMM2aLy-JTXLTCyhq6K6E"
DB = "e92008e6"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

d = GraphDatabase.driver(URI, auth=(USER, PWD), ssl_context=ctx)

with d.session(database=DB) as s:
    # 方法1：直接返回节点
    print("方法1：返回节点")
    r = s.run("MATCH (n:Herb) WHERE n.name = '松节油' RETURN n LIMIT 1")
    for rec in r:
        n = rec["n"]
        print(f"  节点类型: {type(n)}")
        print(f"  属性键: {list(n.keys())}")
        print(f"  属性: {dict(n.items())}")
    
    # 方法2：用 _run_query 格式
    print("\n方法2：用 _run_query 格式")
    records = s.run("MATCH (n:Herb) RETURN n LIMIT 1")
    for rec in records:
        n = rec["n"]
        print(f"  属性键: {list(n.keys())}")
        cloud_id = n.get("id:ID(Herb)", "NOT_FOUND")
        name = n.get("name:String", "NOT_FOUND") or n.get("name", "NOT_FOUND")
        print(f"  id:ID(Herb) = {cloud_id}")
        print(f"  name:String = {name}")
        
        # 试试直接用属性名
        print(f"  n['name'] = {n.get('name', 'NOT_FOUND')}")
        print(f"  n['nature'] = {n.get('nature', 'NOT_FOUND')}")
        print(f"  n['meridian'] = {n.get('meridian', 'NOT_FOUND')}")

d.close()
