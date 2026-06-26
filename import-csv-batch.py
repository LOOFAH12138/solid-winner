# -*- coding: utf-8 -*-
"""分批导入 CSV 数据到 Neo4j"""
import csv
import os
from services.neo4j_service import _run_query

CSV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neo4j_import")

def import_herbs():
    """导入药材数据"""
    csv_file = os.path.join(CSV_DIR, "nodes_Herb.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    print("导入药材数据...")
    count = 0
    batch = []
    batch_size = 20  # 每批20条，降低负载
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append({
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
            
            if len(batch) >= batch_size:
                for item in batch:
                    _run_query("""
                        MERGE (n:Herb {id: $id})
                        SET n.name = $name, n.latinName = $latinName, 
                            n.category = $category, n.nature = $nature, 
                            n.flavor = $flavor, n.meridian = $meridian,
                            n.pinyin = $pinyin, n.englishName = $englishName
                    """, item)
                count += len(batch)
                print(f"  已导入 {count} 个药材...")
                batch = []
        
        for item in batch:
            _run_query("""
                MERGE (n:Herb {id: $id})
                SET n.name = $name, n.latinName = $latinName, 
                    n.category = $category, n.nature = $nature, 
                    n.flavor = $flavor, n.meridian = $meridian,
                    n.pinyin = $pinyin, n.englishName = $englishName
            """, item)
        count += len(batch)
    
    return count

def import_ingredients():
    """导入成分数据"""
    csv_file = os.path.join(CSV_DIR, "nodes_Ingredient.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    print("导入成分数据...")
    count = 0
    batch = []
    batch_size = 20
    
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
    
    print("导入病症数据...")
    count = 0
    batch = []
    batch_size = 20
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append({
                "id": row.get("id", ""),
                "name": row.get("name", ""),
                "category": row.get("category", ""),
                "meshClass": row.get("meshClass", ""),
                "tcmSyndrome": row.get("tcmSyndrome", ""),
                "description": row.get("description", "")
            })
            
            if len(batch) >= batch_size:
                for item in batch:
                    _run_query("""
                        MERGE (n:Disease {id: $id})
                        SET n.name = $name, n.category = $category,
                            n.meshClass = $meshClass, n.tcmSyndrome = $tcmSyndrome,
                            n.description = $description
                    """, item)
                count += len(batch)
                print(f"  已导入 {count} 个病症...")
                batch = []
        
        for item in batch:
            _run_query("""
                MERGE (n:Disease {id: $id})
                SET n.name = $name, n.category = $category,
                    n.meshClass = $meshClass, n.tcmSyndrome = $tcmSyndrome,
                    n.description = $description
            """, item)
        count += len(batch)
    
    return count

def import_derived_from():
    """导入 DERIVED_FROM 关系"""
    csv_file = os.path.join(CSV_DIR, "edges_DERIVED_FROM.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    print("导入 DERIVED_FROM 关系...")
    count = 0
    batch = []
    batch_size = 50
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            start_id = row.get(":START_ID(Ingredient)", "").strip()
            end_id = row.get(":END_ID(Herb)", "").strip()
            batch.append({"start_id": start_id, "end_id": end_id})
            
            if len(batch) >= batch_size:
                for item in batch:
                    if item["start_id"] and item["end_id"]:
                        _run_query("""
                            MATCH (ing:Ingredient {id: $start_id})
                            MATCH (h:Herb {id: $end_id})
                            MERGE (ing)-[:DERIVED_FROM]->(h)
                        """, item)
                count += len(batch)
                print(f"  已导入 {count} 条关系...")
                batch = []
        
        for item in batch:
            if item["start_id"] and item["end_id"]:
                _run_query("""
                    MATCH (ing:Ingredient {id: $start_id})
                    MATCH (h:Herb {id: $end_id})
                    MERGE (ing)-[:DERIVED_FROM]->(h)
                """, item)
        count += len(batch)
    
    return count

def import_treats():
    """导入 TREATS 关系"""
    csv_file = os.path.join(CSV_DIR, "edges_TREATS.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    print("导入 TREATS 关系...")
    count = 0
    batch = []
    batch_size = 50
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            start_id = row.get(":START_ID(Herb)", "").strip()
            end_id = row.get(":END_ID(Disease)", "").strip()
            indication = row.get("indication", "").strip()
            batch.append({"start_id": start_id, "end_id": end_id, "indication": indication})
            
            if len(batch) >= batch_size:
                for item in batch:
                    if item["start_id"] and item["end_id"]:
                        _run_query("""
                            MATCH (h:Herb {id: $start_id})
                            MATCH (d:Disease {id: $end_id})
                            MERGE (h)-[:TREATS {indication: $indication}]->(d)
                        """, item)
                count += len(batch)
                print(f"  已导入 {count} 条关系...")
                batch = []
        
        for item in batch:
            if item["start_id"] and item["end_id"]:
                _run_query("""
                    MATCH (h:Herb {id: $start_id})
                    MATCH (d:Disease {id: $end_id})
                    MERGE (h)-[:TREATS {indication: $indication}]->(d)
                """, item)
        count += len(batch)
    
    return count

def main():
    print("=" * 60)
    print("分批导入 CSV 数据到 Neo4j")
    print("=" * 60)
    
    try:
        print("\n1/5 导入药材数据...")
        herb_count = import_herbs()
        print(f"   完成: {herb_count} 个药材\n")
        
        print("2/5 导入成分数据...")
        ingredient_count = import_ingredients()
        print(f"   完成: {ingredient_count} 个成分\n")
        
        print("3/5 导入病症数据...")
        disease_count = import_diseases()
        print(f"   完成: {disease_count} 个病症\n")
        
        print("4/5 导入 DERIVED_FROM 关系...")
        derived_count = import_derived_from()
        print(f"   完成: {derived_count} 条关系\n")
        
        print("5/5 导入 TREATS 关系...")
        treats_count = import_treats()
        print(f"   完成: {treats_count} 条关系\n")
        
        print("=" * 60)
        print("导入完成！")
        print(f"  药材: {herb_count}")
        print(f"  成分: {ingredient_count}")
        print(f"  病症: {disease_count}")
        print(f"  关系: {derived_count + treats_count}")
        print("=" * 60)
        
        # 验证
        nodes = _run_query('MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC')
        print("\n验证结果：")
        for r in nodes:
            print(f"  {r['label']}: {r['cnt']}")
        
        rels = _run_query('MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS cnt ORDER BY cnt DESC')
        print("\n关系统计：")
        for r in rels:
            print(f"  {r['rel_type']}: {r['cnt']}")
        
    except Exception as e:
        import traceback
        print(f"\n导入失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
