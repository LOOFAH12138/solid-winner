# -*- coding: utf-8 -*-
"""检查 SQLite 数据库表结构"""
import sqlite3

db = sqlite3.connect('database.db')
cursor = db.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("数据库表:")
print("=" * 80)
for table in tables:
    table_name = table[0]
    print(f"\n表: {table_name}")
    
    # 获取列信息
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]:25s} {col[2]:15s} {'PK' if col[5] else ' '}")
    
    # 获取行数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  行数: {count}")

db.close()
