# -*- coding: utf-8 -*-
"""测试直接 Bolt 流式查询"""
import ssl
import time
from neo4j import GraphDatabase

URI = "neo4j://e92008e6.databases.neo4j.io:7687"
USER = "e92008e6"
PWD = "ggiHLVb04FTPl2FWcOfkTsWMM2aLy-JTXLTCyhq6K6E"
DB = "e92008e6"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

d = GraphDatabase.driver(URI, auth=(USER, PWD), ssl_context=ctx)

# 方法 1: 用 with session
print("方法 1: with session + yield")
def stream1():
    with d.session(database=DB) as session:
        result = session.run("MATCH (n:Disease) RETURN properties(n) AS props")
        batch = []
        count = 0
        for record in result:
            batch.append(dict(record))
            count += 1
            if len(batch) >= 5000:
                yield batch
                batch = []
                print(f"  Yield {count}")
        if batch:
            yield batch
            print(f"  Final {count}")

start = time.time()
total = 0
for batch in stream1():
    total += len(batch)
print(f"总记录: {total}, 耗时: {time.time() - start:.2f}s")

d.close()
