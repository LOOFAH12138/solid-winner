# -*- coding: utf-8 -*-
"""使用 UNWIND 高效导入 CSV 数据到 Neo4j"""
import csv
import os
from services.neo4j_service import _run_query

CSV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neo4j_import")

def import_herbs():
    """使用 UNWIND 批量导入药材数据"""
    csv_file = os.path.join(CSV_DIR, "nodes_Herb.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    print("导入药材数据...")
    herbs = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            herbs.append({
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
    
    # 分批导入，每批 100 条
    batch_size = 100
    count = 0
    
    for i in range(0, len(herbs), batch_size):
        batch = herbs[i:i+batch_size]
        try:
            _run_query("""
                UNWIND $data AS row
                MERGE (n:Herb {id: row.id})
                SET n.name = row.name, 
                    n.latinName = row.latinName, 
                    n.category = row.category, 
                    n.nature = row.nature, 
                    n.flavor = row.flavor, 
                    n.meridian = row.meridian,
                    n.pinyin = row.pinyin, 
                    n.englishName = row.englishName
            """, {"data": batch})
            count += len(batch)
            print(f"  已导入 {count}/{len(herbs)} 个药材...")
        except Exception as e:
            print(f"  导入失败: {e}")
            break
    
    return count

def import_ingredients():
    """使用 UNWIND 批量导入成分数据"""
    csv_file = os.path.join(CSV_DIR, "nodes_Ingredient.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    print("导入成分数据...")
    ingredients = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ingredients.append({
                "id": row.get("id", ""),
                "name": row.get("name", ""),
                "molecularFormula": row.get("molecularFormula", ""),
                "casNumber": row.get("casNumber", ""),
                "bioactivity": row.get("bioactivity", "")
            })
    
    batch_size = 100
    count = 0
    
    for i in range(0, len(ingredients), batch_size):
        batch = ingredients[i:i+batch_size]
        try:
            _run_query("""
                UNWIND $data AS row
                MERGE (n:Ingredient {id: row.id})
                SET n.name = row.name, 
                    n.molecularFormula = row.molecularFormula,
                    n.casNumber = row.casNumber, 
                    n.bioactivity = row.bioactivity
            """, {"data": batch})
            count += len(batch)
            print(f"  已导入 {count}/{len(ingredients)} 个成分...")
        except Exception as e:
            print(f"  导入失败: {e}")
            break
    
    return count

def import_diseases():
    """使用 UNWIND 批量导入病症数据"""
    csv_file = os.path.join(CSV_DIR, "nodes_Disease.csv")
    if not os.path.exists(csv_file):
        print("文件不存在:", csv_file)
        return 0
    
    print("导入病症数据...")
    diseases = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            diseases.append({
                "id": row.get("id", ""),
                "name": row.get("name", ""),
                "category": row.get("category", ""),
                "meshClass": row.get("meshClass", ""),
                "tcmSyndrome": row.get("tcmSyndrome", ""),
                "description": row.get("description", "")
            })
    
    batch_size = 100
    count = 0
    
    for i in range(0, len(diseases), batch_size):
        batch = diseases[i:i+batch_size]
        try:
            _run_query("""
                UNWIND $data AS row
                MERGE (n:Disease {id: row.id})
                SET n.name = row.name, 
                    n.category = row.category,
                    n.meshClass = row.meshClass, 
                    n.tcmSyndrome = row.tcmSyndrome,
                    n.description = row.description
            """, {"data": batch})
            count += len(batch)
            print(f"  已导入 {count}/{len(diseases)} 个病症...")
        except Exception as e:
            print(f"  导入失败: {e}")
            break
    
    return count

def main():
    print("=" * 60)
    print("使用 UNWIND 批量导入 CSV 数据到 Neo4j")
    print("=" * 60)
    
    try:
        print("\n1/3 导入药材数据...")
        herb_count = import_herbs()
        print(f"   完成: {herb_count} 个药材\n")
        
        print("2/3 导入成分数据...")
        ingredient_count = import_ingredients()
        print(f"   完成: {ingredient_count} 个成分\n")
        
        print("3/3 导入病症数据...")
        disease_count = import_diseases()
        print(f"   完成: {disease_count} 个病症\n")
        
        print("=" * 60)
        print("导入完成！")
        print(f"  药材: {herb_count}")
        print(f"  成分: {ingredient_count}")
        print(f"  病症: {disease_count}")
        print("=" * 60)
        
        # 验证
        nodes = _run_query('MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC')
        print("\n验证结果：")
        for r in nodes:
            print(f"  {r['label']}: {r['cnt']}")
        
    except Exception as e:
        import traceback
        print(f"\n导入失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
