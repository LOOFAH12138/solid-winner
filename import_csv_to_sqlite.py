# -*- coding: utf-8 -*-
"""CSV → SQLite 批量导入脚本

处理 neo4j_import/ 目录下的 CSV 文件（Neo4j 格式头）,
将其导入本地 SQLite 数据库。
"""
import csv
import os
import sys
import time

# 项目根目录
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

sys.path.insert(0, ROOT)
from database import init_db, get_db

# CSV 目录
CSV_DIR = os.path.join(ROOT, "neo4j_import")
BATCH_SIZE = 5000

# --- 列名映射：Neo4j CSV 头 -> SQLite 列名 ---
HERB_COL_MAP = {
    "id:ID(Herb)": "tcmbank_id",
    "name:String": "name",
    "latinName:String": "latin_name",
    "category:String": "category",
    "nature:String": "nature",
    "flavor:String[]": "taste",
    "meridian:String": "meridian",
    "pinyin:String": "pinyin_name",
    "englishName:String": "tcm_name_en",
}

DISEASE_COL_MAP = {
    "id:ID(Disease)": "cloud_id",
    "name:String": "name",
    "category:String": "category",
    "meshClass:String": "mesh_class",
    "tcmSyndrome:String": "tcm_syndrome",
    "description:String": "description",
}

INGREDIENT_COL_MAP = {
    "id:ID(Ingredient)": "cloud_id",
    "name:String": "name",
    "molecularFormula:String": "formula",
    "casNumber:String": "cas_number",
    "bioactivity:String": "bioactivity",
}

PRESCRIPTION_COL_MAP = {
    ":ID(Prescription)": "cloud_id",
    "name:String": "name",
    "source:String": "source",
    "efficacy:String": "efficacy",
}

PHARMACOLOGY_COL_MAP = {
    ":ID(Pharmacology)": "cloud_id",
    "name:String": "name",
}


def get_progress(total):
    """估算进度百分比"""
    return lambda i: f"{i}/{total} ({100*i//max(total,1)}%)" if total else f"{i}/?"


def import_nodes(csv_file, table, col_map):
    """导入节点 CSV"""
    path = os.path.join(CSV_DIR, csv_file)
    if not os.path.exists(path):
        print(f"  [SKIP] {csv_file} 不存在")
        return 0

    conn = get_db()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        csv_headers = reader.fieldnames
        sql_columns = []
        for h in csv_headers:
            if h in col_map:
                sql_columns.append(col_map[h])
        placeholders = ", ".join(["?"] * len(sql_columns))
        cols_str = ", ".join(sql_columns)
        
        # 使用 INSERT OR REPLACE 处理重复
        sql = f"INSERT OR REPLACE INTO {table} ({cols_str}) VALUES ({placeholders})"

        count = 0
        rows = []
        for row in reader:
            values = [row.get(k, "") or "" for k in csv_headers if k in col_map]
            rows.append(values)
            if len(rows) >= BATCH_SIZE:
                conn.executemany(sql, rows)
                conn.commit()
                count += len(rows)
                print(f"\r  {csv_file}: {count} rows", end="", flush=True)
                rows = []

        if rows:
            conn.executemany(sql, rows)
            conn.commit()
            count += len(rows)

    conn.close()
    print(f"\r  {csv_file}: {count} rows              ")
    return count


def import_edge(csv_file, table, src_col, tgt_col, extra_csv_cols=None):
    """导入关系边 CSV"""
    path = os.path.join(CSV_DIR, csv_file)
    if not os.path.exists(path):
        print(f"  [SKIP] {csv_file} 不存在")
        return 0

    conn = get_db()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA foreign_keys=OFF")

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        csv_headers = reader.fieldnames

        # 查找源和目标列
        src_key = next((h for h in csv_headers if ":START_ID" in h), None)
        tgt_key = next((h for h in csv_headers if ":END_ID" in h), None)
        if not src_key or not tgt_key:
            print(f"\r  [SKIP] {csv_file}: 找不到 START_ID/END_ID")
            conn.close()
            return 0

        # 构建 SQL 列名（去类型后缀）
        db_cols = [src_col, tgt_col]
        if extra_csv_cols:
            for ec in extra_csv_cols:
                # 去掉类型后缀: "indication:String" -> "indication"
                base = ec.split(":")[0] if ":" in ec else ec
                db_cols.append(base)
        placeholders = ", ".join(["?"] * len(db_cols))
        cols_str = ", ".join(db_cols)
        sql = f"INSERT OR REPLACE INTO {table} ({cols_str}) VALUES ({placeholders})"

        count = 0
        rows = []
        for row in reader:
            values = [row[src_key], row[tgt_key]]
            if extra_csv_cols:
                for ec in extra_csv_cols:
                    values.append(row.get(ec, "") or "")
            rows.append(values)
            if len(rows) >= BATCH_SIZE:
                conn.executemany(sql, rows)
                conn.commit()
                count += len(rows)
                print(f"\r  {csv_file}: {count} rows", end="", flush=True)
                rows = []

        if rows:
            conn.executemany(sql, rows)
            conn.commit()
            count += len(rows)

    conn.close()
    print(f"\r  {csv_file}: {count} rows              ")
    return count


def show_stats():
    """显示导入后的统计"""
    conn = get_db()
    tables = {
        "herb": "中药材",
        "disease": "病症",
        "chemical_component": "化学成分",
        "prescription": "方剂",
        "pharmacology": "药理学",
        "herb_disease": "Herb-Disease 关系",
        "prescription_herb": "方剂-药材 关系",
        "ingredient_herb": "成分-药材 关系",
        "herb_pharmacology": "药材-药理学 关系",
        "ingredient_pharmacology": "成分-药理学 关系",
    }
    print()
    print("=" * 55)
    print("  导入后数据统计")
    print("=" * 55)
    for table, label in tables.items():
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {label:20s}: {cnt:>8,}")
        except:
            print(f"  {label:20s}:   (表不存在)")
    conn.close()


def main():
    init_db()
    t0 = time.time()

    # 确保现有核心表有正确结构
    conn = get_db()
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.commit()
    conn.close()

    print("=" * 55)
    print("  CSV → SQLite 数据导入")
    print("=" * 55)
    print()

    # 1. 节点表
    print("[1/4] 导入节点数据...")
    n1 = import_nodes("nodes_Herb.csv", "herb", HERB_COL_MAP)
    n2 = import_nodes("nodes_Disease.csv", "disease", DISEASE_COL_MAP)
    n3 = import_nodes("nodes_Ingredient.csv", "chemical_component", INGREDIENT_COL_MAP)
    n4 = import_nodes("nodes_Prescription.csv", "prescription", PRESCRIPTION_COL_MAP)
    n5 = import_nodes("nodes_Pharmacology.csv", "pharmacology", PHARMACOLOGY_COL_MAP)
    print(f"  节点合计: {n1 + n2 + n3 + n4 + n5:,}")

    # 2. 关系表
    print()
    print("[2/4] 导入关系边数据...")
    r1 = import_edge("edges_TREATS.csv", "herb_disease", "herb_tcmbank_id", "disease_cloud_id", ["indication:String"])
    r2 = import_edge("edges_CONTAINS_HERB.csv", "prescription_herb", "prescription_id", "herb_id")
    r3 = import_edge("edges_DERIVED_FROM.csv", "ingredient_herb", "ingredient_id", "herb_id")
    r4 = import_edge("edges_Herb_HAS_PHARMACOLOGY.csv", "herb_pharmacology", "herb_id", "pharmacology_id")
    r5 = import_edge("edges_Ingredient_HAS_PHARMACOLOGY.csv", "ingredient_pharmacology", "ingredient_id", "pharmacology_id")
    print(f"  关系合计: {r1 + r2 + r3 + r4 + r5:,}")

    # 3. 更新 herb 表的 cloud_id 索引（通过 ingredient_herb 反向更新）
    print()
    print("[3/4] 更新药材的 herb_id 关联...")
    conn = get_db()
    cnt = conn.execute("""
        UPDATE chemical_component 
        SET herb_id = (SELECT ih.herb_id FROM ingredient_herb ih 
                       WHERE ih.ingredient_id = chemical_component.cloud_id LIMIT 1)
        WHERE EXISTS (SELECT 1 FROM ingredient_herb ih WHERE ih.ingredient_id = chemical_component.cloud_id)
    """).rowcount
    conn.commit()
    conn.close()
    print(f"  更新了 {cnt:,} 条成分的 herb_id")

    elapsed = time.time() - t0
    print()
    print(f"  总耗时: {elapsed:.1f} 秒")

    # 4. 统计
    show_stats()
    print()
    print("导入完成!")


if __name__ == "__main__":
    main()
