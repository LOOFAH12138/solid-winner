# -*- coding: utf-8 -*-
"""测试正确的 Cypher 语法来获取属性"""
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
    # 方法1：直接返回所有属性
    print("方法1: properties(n)")
    r = s.run("MATCH (n:Herb) RETURN properties(n) LIMIT 1")
    for rec in r:
        props = rec["properties(n)"]
        print(f"  Keys: {list(props.keys())}")
        print(f"  name:String = {props.get('name:String', 'NOT FOUND')}")
        print(f"  id:ID(Herb) = {props.get('id:ID(Herb)', 'NOT FOUND')}")
    
    # 方法2：用变量别名
    print("\n方法2: 用别名访问")
    r = s.run("MATCH (n:Herb) RETURN properties(n) AS props LIMIT 1")
    for rec in r:
        props = rec["props"]
        print(f"  name:String = {props.get('name:String', 'NOT FOUND')}")

d.close()
