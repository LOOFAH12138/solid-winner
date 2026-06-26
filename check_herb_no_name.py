# -*- coding: utf-8 -*-
"""检查哪些 Herb 没有 name 字段"""
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
    # 统计有 name 和没有 name 的 Herb
    r = s.run("MATCH (n:Herb) RETURN count(*) AS total")
    for rec in r:
        print(f"Total Herb: {rec['total']}")
    
    r = s.run("MATCH (n:Herb) WHERE n.name:String IS NOT NULL RETURN count(*) AS with_name")
    for rec in r:
        print(f"With name: {rec['with_name']}")
    
    r = s.run("MATCH (n:Herb) WHERE n.name:String IS NULL RETURN count(*) AS without_name")
    for rec in r:
        print(f"Without name: {rec['without_name']}")
    
    # 查看没有 name 的 Herb 样例
    r = s.run("MATCH (n:Herb) WHERE n.name:String IS NULL RETURN properties(n) LIMIT 3")
    print("\nHerb without name:")
    for rec in r:
        props = rec["properties(n)"]
        print(f"  {props}")

d.close()
