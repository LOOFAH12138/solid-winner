# -*- coding: utf-8 -*-
"""从 CSV 文件导入数据到 Neo4j"""
import csv
import os
from services.neo4j_service import _run_query

# CSV 文件路径
CSV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neo4j_import")

def import_herbs():
    """导入药材数据"""
    csv_file = os.path.join(CSV_DIR, "nodes_Herb.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    count = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            _run_query("""
                MERGE (n:Herb {id: $id})
                SET n.name = $name, n.latinName = $latinName, 
                    n.category = $category, n.nature = $nature, 
                    n.flavor = $flavor, n.meridian = $meridian,
                    n.pinyin = $pinyin, n.englishName = $englishName
            """, {
                "id": row.get("id", ""),
                "name": row.get("name", ""),
                "latinName": row.get("latinName", ""),
                "category": row.get("category", ""),
                "nature": row.get("nature", ""),
                "flavor": row.get("flavor", ""),
                "meridian": row.get("meridian", ""),
                "pinyin": row.get("pinyin", ""),
                "englishName": row.get("englishName", "")
            })
            count += 1
            if count % 100 == 0:
                print(f"  已导入 {count} 个药材...")
    
    return count

def import_ingredients():
    """导入成分数据"""
    csv_file = os.path.join(CSV_DIR, "nodes_Ingredient.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    count = 0
    batch = []
    batch_size = 30  # 减小批次大小，降低负载
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append({
                "id": row.get("id", ""),
                "name": row.get("name", ""),
                "molecularFormula": row.get("molecularFormula", ""),
                "casNumber": row.get("casNumber", ""),
                "bioactivity": row.get("bioactivity", "")
            })
            
            if len(batch) >= batch_size:
                for item in batch:
                    _run_query("""
                        MERGE (n:Ingredient {id: $id})
                        SET n.name = $name, n.molecularFormula = $molecularFormula,
                            n.casNumber = $casNumber, n.bioactivity = $bioactivity
                    """, item)
                count += len(batch)
                print(f"  已导入 {count} 个成分...")
                batch = []
        
        # 导入剩余数据
        for item in batch:
            _run_query("""
                MERGE (n:Ingredient {id: $id})
                SET n.name = $name, n.molecularFormula = $molecularFormula,
                    n.casNumber = $casNumber, n.bioactivity = $bioactivity
            """, item)
        count += len(batch)
    
    return count

def import_diseases():
    """导入病症数据"""
    csv_file = os.path.join(CSV_DIR, "nodes_Disease.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    count = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            _run_query("""
                MERGE (n:Disease {id: $id})
                SET n.name = $name, n.category = $category,
                    n.meshClass = $meshClass, n.tcmSyndrome = $tcmSyndrome,
                    n.description = $description
            """, {
                "id": row.get("id", ""),
                "name": row.get("name", ""),
                "category": row.get("category", ""),
                "meshClass": row.get("meshClass", ""),
                "tcmSyndrome": row.get("tcmSyndrome", ""),
                "description": row.get("description", "")
            })
            count += 1
            if count % 100 == 0:
                print(f"  已导入 {count} 个病症...")
    
    return count

def import_derived_from():
    """导入 DERIVED_FROM 关系"""
    csv_file = os.path.join(CSV_DIR, "edges_DERIVED_FROM.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    count = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            start_id = row.get(":START_ID(Ingredient)", "").strip()
            end_id = row.get(":END_ID(Herb)", "").strip()
            
            if start_id and end_id:
                _run_query("""
                    MATCH (ing:Ingredient {id: $start_id})
                    MATCH (h:Herb {id: $end_id})
                    CREATE (ing)-[:DERIVED_FROM]->(h)
                """, {
                    "start_id": start_id,
                    "end_id": end_id
                })
                count += 1
                if count % 100 == 0:
                    print(f"  已导入 {count} 条关系...")
    
    return count

def import_treats():
    """导入 TREATS 关系"""
    csv_file = os.path.join(CSV_DIR, "edges_TREATS.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    count = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            start_id = row.get(":START_ID(Herb)", "").strip()
            end_id = row.get(":END_ID(Disease)", "").strip()
            indication = row.get("indication", "").strip()
            
            if start_id and end_id:
                _run_query("""
                    MATCH (h:Herb {id: $start_id})
                    MATCH (d:Disease {id: $end_id})
                    CREATE (h)-[:TREATS {indication: $indication}]->(d)
                """, {
                    "start_id": start_id,
                    "end_id": end_id,
                    "indication": indication
                })
                count += 1
                if count % 100 == 0:
                    print(f"  已导入 {count} 条关系...")
    
    return count

def main():
    print("=" * 60)
    print("开始从 CSV 文件导入数据到 Neo4j")
    print("=" * 60)
    
    try:
        # 1. 导入节点
        print("\n1. 导入药材数据...")
        herb_count = import_herbs()
        print(f"   完成: {herb_count} 个药材")
        
        print("\n2. 导入成分数据...")
        ingredient_count = import_ingredients()
        print(f"   完成: {ingredient_count} 个成分")
        
        print("\n3. 导入病症数据...")
        disease_count = import_diseases()
        print(f"   完成: {disease_count} 个病症")
        
        # 2. 导入关系
        print("\n4. 导入 DERIVED_FROM 关系...")
        derived_count = import_derived_from()
        print(f"   完成: {derived_count} 条关系")
        
        print("\n5. 导入 TREATS 关系...")
        treats_count = import_treats()
        print(f"   完成: {treats_count} 条关系")
        
        print("\n" + "=" * 60)
        print("导入完成！")
        print(f"  药材: {herb_count}")
        print(f"  成分: {ingredient_count}")
        print(f"  病症: {disease_count}")
        print(f"  关系: {derived_count + treats_count}")
        print("=" * 60)
        
        # 3. 查询统计
        print("\n验证导入结果：")
        stats = _run_query("MATCH (n) RETURN labels(n) AS label, count(*) AS cnt ORDER BY cnt DESC")
        for row in stats:
            label = row["label"][0] if row["label"] else "Unknown"
            print(f"  {label}: {row['cnt']}")
        
        rel_stats = _run_query("MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS cnt ORDER BY cnt DESC")
        for row in rel_stats:
            print(f"  {row['rel_type']}: {row['cnt']}")
        
    except Exception as e:
        import traceback
        print(f"\n导入失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
