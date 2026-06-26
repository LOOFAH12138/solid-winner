# -*- coding: utf-8 -*-
"""检查 Neo4j 数据"""
from services.neo4j_service import _run_query

print("=" * 60)
print("Neo4j 数据检查")
print("=" * 60)

nodes = _run_query('MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC')
print("\n节点统计：")
for r in nodes:
    print(f"  {r['label']}: {r['cnt']}")

rels = _run_query('MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS cnt ORDER BY cnt DESC')
print("\n关系统计：")
for r in rels:
    print(f"  {r['rel_type']}: {r['cnt']}")

total_nodes = _run_query('MATCH (n) RETURN count(n) AS total')
print(f"\n总节点数: {total_nodes[0]['total']}")

total_rels = _run_query('MATCH ()-[r]->() RETURN count(r) AS total')
print(f"总关系数: {total_rels[0]['total']}")

print("\n" + "=" * 60)
