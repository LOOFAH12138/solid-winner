# -*- coding: utf-8 -*-
"""测试从 Neo4j 同步到 SQLite"""
import sys
sys.path.insert(0, '.')
from services.neo4j_service import sync_from_neo4j

try:
    result = sync_from_neo4j()
    print("\n同步结果:")
    for k, v in result.items():
        print(f"  {k}: {v}")
except Exception as e:
    print(f"同步失败: {e}")
    import traceback
    traceback.print_exc()
