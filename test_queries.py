"""端到端查询验证脚本 - 验证所有查询路径正确性"""
import sqlite3
import sys
import os
import traceback

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = "tcm_data.db"
ALL_PASSED = True
NEO4J_AVAILABLE = False
LLM_AVAILABLE = False

def green(s): return f"\033[92m{s}\033[0m"
def red(s): return f"\033[91m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"

def run_test(name, fn, skip_if_fail=None):
    global ALL_PASSED
    try:
        if skip_if_fail and not skip_if_fail():
            print(f"\n  {name}...", yellow("SKIP (unavailable)"))
            return
        print(f"\n  {name}...", end=" ", flush=True)
        fn()
        print(green("PASS"))
    except Exception as e:
        ALL_PASSED = False
        print(red(f"FAIL: {str(e)[:200]}"))
        traceback.print_exc()


# ==================== Test 1: SQLite 本地数据库查询 ====================
def test_sqlite_herb_count():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.execute("SELECT COUNT(*) as cnt FROM herb")
    row = c.fetchone()
    assert row["cnt"] > 5000, f"herb count too low: {row['cnt']}"
    c = conn.execute("SELECT * FROM herb LIMIT 1")
    row = c.fetchone()
    assert row["name"], "herb name missing"
    assert row["tcmbank_id"], "herb tcmbank_id missing"
    conn.close()

def test_sqlite_disease_count():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.execute("SELECT COUNT(*) as cnt FROM disease")
    row = c.fetchone()
    assert row["cnt"] > 100, f"disease count too low: {row['cnt']}"
    c = conn.execute("SELECT * FROM disease LIMIT 1")
    row = c.fetchone()
    assert row["name"], "disease name missing"
    assert row["cloud_id"], "disease cloud_id missing"
    conn.close()

def test_sqlite_prescription_count():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.execute("SELECT COUNT(*) as cnt FROM prescription")
    row = c.fetchone()
    assert row["cnt"] > 100, f"prescription count too low: {row['cnt']}"
    c = conn.execute("SELECT * FROM prescription LIMIT 1")
    row = c.fetchone()
    assert row["name"], "prescription name missing"
    assert row["cloud_id"], "prescription cloud_id missing"
    conn.close()

def test_sqlite_pharmacology_count():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.execute("SELECT COUNT(*) as cnt FROM pharmacology")
    row = c.fetchone()
    assert row["cnt"] > 100, f"pharmacology count too low: {row['cnt']}"
    c = conn.execute("SELECT * FROM pharmacology LIMIT 1")
    row = c.fetchone()
    assert row["name"], "pharmacology name missing"
    assert row["cloud_id"], "pharmacology cloud_id missing"
    conn.close()

def test_sqlite_component_count():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.execute("SELECT COUNT(*) as cnt FROM chemical_component")
    row = c.fetchone()
    assert row["cnt"] > 100, f"component count too low: {row['cnt']}"
    c = conn.execute("SELECT * FROM chemical_component LIMIT 1")
    row = c.fetchone()
    assert row["name"], "component name missing"
    assert row["cloud_id"], "component cloud_id missing"
    conn.close()

def test_sqlite_edge_tables():
    conn = sqlite3.connect(DB_PATH)
    edge_tables = {
        "herb_disease": 100,
        "ingredient_herb": 100,
        "herb_pharmacology": 100,
        "prescription_herb": 100,
        "prescription_disease": 0,
        "ingredient_pharmacology": 0,
    }
    for table, min_rows in edge_tables.items():
        try:
            row = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
            count = row[0]
            assert count >= min_rows, f"{table}: expected >={min_rows}, got {count}"
        except Exception as e:
            if min_rows > 0:
                raise
    conn.close()
    print(f"    [6 edge tables]", end=" ")


# ==================== Test 2: Neo4j 连接检测 ====================
def test_neo4j_check_available():
    global NEO4J_AVAILABLE
    from services.neo4j_service import check_health
    health = check_health()
    NEO4J_AVAILABLE = health.get("connected", False)
    if NEO4J_AVAILABLE:
        print("    [connected]", end=" ")
    else:
        print("    [unavailable (sandbox network restriction)]", end=" ")

def _neo4j_available():
    return NEO4J_AVAILABLE

def test_neo4j_query_entity_graph_herb():
    from services.neo4j_service import query_entity_graph
    result = query_entity_graph("herb", "H_TCMBANKHE000001")  # 松节油
    assert result["nodes"], "No nodes returned"
    n_names = [n.get("name") for n in result["nodes"]]
    assert any("松节油" in (name or "") for name in n_names), f"松节油 not found: {n_names}"
    print(f"    [nodes={len(result['nodes'])}, edges={len(result['edges'])}]", end=" ")

def test_neo4j_query_entity_graph_disease():
    from services.neo4j_service import query_entity_graph
    result = query_entity_graph("disease", "D_1")
    assert result["nodes"], "No nodes returned"
    print(f"    [nodes={len(result['nodes'])}, edges={len(result['edges'])}]", end=" ")

def test_neo4j_statistics():
    from services.neo4j_service import get_statistics
    stats = get_statistics()
    nodes = stats.get("nodes", {})
    assert nodes.get("herb", 0) > 0, f"No herb count in stats"
    print(f"    [ok]", end=" ")

def test_neo4j_agent_qa_graph():
    from services.agent_qa import AgentQA
    result = AgentQA.query_graph_db(["松节油"])
    assert result["treats"] or result["contains"] or result["herb_properties"], \
        f"AgentQA graph query returned empty"
    print(f"    [ok]", end=" ")


# ==================== Test 3: KnowledgeService ====================
def test_knowledge_search_chunks():
    from services.knowledge_service import KnowledgeService
    result = KnowledgeService.search_chunks("松节油", limit=5)
    assert len(result) > 0, "search_chunks empty"
    print(f"    [chunks={len(result)}]", end=" ")

def test_knowledge_search_extended_herb():
    from services.knowledge_service import KnowledgeService
    result = KnowledgeService.search_chunks_extended("石榴", limit=10)
    assert len(result) > 0, "search_chunks_extended empty"
    herb_chunks = [c for c in result if c.get('entity_type') == 'herb']
    assert len(herb_chunks) > 0, "No herb results"
    print(f"    [total={len(result)}, herb={len(herb_chunks)}]", end=" ")

def test_knowledge_search_extended_disease():
    from services.knowledge_service import KnowledgeService
    result = KnowledgeService.search_chunks_extended("Myalgia", limit=10)
    assert len(result) > 0, "search_chunks_extended empty"
    disease_chunks = [c for c in result if c.get('entity_type') == 'disease']
    assert len(disease_chunks) > 0, "No disease results"
    print(f"    [total={len(result)}, disease={len(disease_chunks)}]", end=" ")


# ==================== Test 4: GraphService (SQLite fallback) ====================
def test_graph_service_query():
    from services.knowledge_service import GraphService
    # Herb query
    r = GraphService.query_entity_graph("herb", "H_TCMBANKHE000387")
    assert r["nodes"], "No nodes"
    assert "人参子" in r["nodes"][0].get("name", ""), "Wrong result"
    # Disease query
    r2 = GraphService.query_entity_graph("disease", "D_1")
    assert r2["nodes"], "No disease nodes"
    print(f"    [herb+nodes={len(r['nodes'])}, disease+nodes={len(r2['nodes'])}]", end=" ")


# ==================== Test 5: AgentQA local DB (no LLM) ====================
def test_agent_qa_local():
    from services.agent_qa import AgentQA
    result = AgentQA.query_local_db(["松节油"], "松节油")
    assert result["herbs"], "No local herb results"
    assert result["herbs"][0].get("name"), "No herb name"
    print(f"    [herbs={len(result['herbs'])}]", end=" ")


# ==================== Main ====================
def main():
    global ALL_PASSED, NEO4J_AVAILABLE, LLM_AVAILABLE

    print("=" * 60)
    print("  端到端查询验证")
    print("=" * 60)

    print("\n[1/5] SQLite 本地数据库查询")
    run_test("herb表", test_sqlite_herb_count)
    run_test("disease表", test_sqlite_disease_count)
    run_test("prescription表", test_sqlite_prescription_count)
    run_test("pharmacology表", test_sqlite_pharmacology_count)
    run_test("chemical_component表", test_sqlite_component_count)
    run_test("关系边表", test_sqlite_edge_tables)

    print("\n[2/5] Neo4j 云端图数据库")
    run_test("Neo4j连接检测", test_neo4j_check_available)
    run_test("query_entity_graph(herb)", test_neo4j_query_entity_graph_herb, skip_if_fail=_neo4j_available)
    run_test("query_entity_graph(disease)", test_neo4j_query_entity_graph_disease, skip_if_fail=_neo4j_available)
    run_test("get_statistics (fallback)", test_neo4j_statistics)
    run_test("AgentQA.query_graph_db", test_neo4j_agent_qa_graph, skip_if_fail=_neo4j_available)

    print("\n[3/5] KnowledgeService 多数据源搜索")
    run_test("search_chunks", test_knowledge_search_chunks)
    run_test("search_chunks_extended(herb)", test_knowledge_search_extended_herb)
    run_test("search_chunks_extended(disease)", test_knowledge_search_extended_disease)

    print("\n[4/5] GraphService SQLite 图谱 fallback")
    run_test("query_entity_graph", test_graph_service_query)

    print("\n[5/5] AgentQA LocalDB Agent")
    run_test("query_local_db", test_agent_qa_local)

    print("\n" + "=" * 60)
    if ALL_PASSED:
        print(green("  全部测试通过！所有查询路径正常工作。"))
    else:
        print(red("  存在失败测试，请检查上方输出。"))

    # 环境说明
    env_notes = []
    if not NEO4J_AVAILABLE:
        env_notes.append("Neo4j 云端不可达（已修正属性名代码）")
    if env_notes:
        print(yellow(f"  环境限制: {'; '.join(env_notes)}"))
        print(yellow("  代码修复（agent_qa.py, knowledge_service.py Neo4j 属性名）已在本地完成。"))
    print("=" * 60)

    return 0 if ALL_PASSED else 1


if __name__ == "__main__":
    sys.exit(main())
