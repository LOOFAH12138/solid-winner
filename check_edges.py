# -*- coding: utf-8 -*-
"""详细检查云端 Neo4j 的边数据"""
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
    # 1. 所有关系类型和数量
    print("=" * 80)
    print("1. 所有关系类型及数量:")
    print("=" * 80)
    r = s.run("""
        MATCH ()-[rel]->()
        RETURN type(rel) AS rel_type, count(*) AS cnt
        ORDER BY cnt DESC
    """)
    for rec in r:
        print(f"  {rec['rel_type']}: {rec['cnt']}")

    print()
    
    # 2. 每种关系的源节点标签、目标节点标签、属性
    print("=" * 80)
    print("2. 关系详情（样例 + 属性）:")
    print("=" * 80)
    
    for rel_type in ['TREATS', 'FOUND_IN']:
        print(f"\n--- {rel_type} 关系 ---")
        r = s.run(f"""
            MATCH (a)-[r:{rel_type}]->(b)
            LIMIT 3
            RETURN labels(a) AS a_labels, properties(a) AS a_props,
                   type(r) AS rel_type, properties(r) AS rel_props,
                   labels(b) AS b_labels, properties(b) AS b_props
        """)
        for rec in r:
            a = dict(rec["a_props"])
            b = dict(rec["b_props"])
            rel_p = dict(rec["rel_props"])
            print(f"  {a.get('name:String', a.get('name'))} -[{rel_type}{rel_p}]--> {b.get('name:String', b.get('name'))}")
    
    # 3. 检查是否有其他标签的关系
    print("\n" + "=" * 80)
    print("3. 其他关系类型:")
    print("=" * 80)
    r = s.run("""
        MATCH ()-[rel]->()
        RETURN type(rel) AS rel_type, count(*) AS cnt
        ORDER BY cnt DESC
        LIMIT 20
    """)
    all_rels = list(r)
    if all_rels:
        for rec in all_rels:
            print(f"  {rec['rel_type']}: {rec['cnt']}")
    else:
        print("  (只有 TREATS 和 FOUND_IN 两种关系)")
    
    # 4. 检查关系中的属性
    print("\n" + "=" * 80)
    print("4. 关系属性详情:")
    print("=" * 80)
    for rel_type in ['TREATS', 'FOUND_IN']:
        r = s.run(f"""
            MATCH ()-[r:{rel_type}]->()
            RETURN properties(r) AS rel_props
            LIMIT 5
        """)
        print(f"\n{rel_type} 属性样例:")
        for rec in r:
            props = dict(rec["rel_props"])
            print(f"  {props}")

d.close()
