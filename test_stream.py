# -*- coding: utf-8 -*-
"""测试 _run_query_stream 是否正常工作"""
import sys
sys.path.insert(0, '.')
from services.neo4j_service import _run_query_stream
import time

print("测试 _run_query_stream...")
start = time.time()
count = 0
for batch_data in _run_query_stream("MATCH (n:Herb) RETURN properties(n) AS props", batch_size=100):
    elapsed = time.time() - start
    print(f"  收到批次: {len(batch_data)} 条, 累计: {count + len(batch_data)}, 耗时: {elapsed:.2f}s")
    count += len(batch_data)
    if count >= 300:
        print("  测试 300 条后停止")
        break

print(f"总记录: {count}, 总耗时: {time.time() - start:.2f}s")
