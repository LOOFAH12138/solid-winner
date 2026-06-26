# -*- coding: utf-8 -*-
"""检查本地数据库数据"""
from database import get_db

db = get_db()

# 检查各表数据量
tables = ['herb', 'prescription', 'disease', 'chemical_component']
for table in tables:
    count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count} 条")
    if count > 0:
        sample = db.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()
        print(f"  样例: {dict(sample)}")

db.close()
