# -*- coding: utf-8 -*-
"""Neo4j 知识图谱服务 —— 驱动连接、数据同步、图谱查询"""
import os
from database import get_db
from .knowledge_service import GraphService

# Neo4j 连接配置（通过环境变量覆盖，默认使用 Aura 云端实例）
NEO4J_URI = os.environ.get("NEO4J_URI", "neo4j://e92008e6.databases.neo4j.io:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "e92008e6")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "ggiHLVb04FTPl2FWcOfkTsWMM2aLy-JTXLTCyhq6K6E")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "e92008e6")

# 延迟导入 driver，避免未安装 neo4j 时启动失败
_neo4j_driver = None


def _get_driver():
    """获取 Neo4j driver 实例（延迟初始化）"""
    global _neo4j_driver
    if _neo4j_driver is not None:
        return _neo4j_driver
    try:
        from neo4j import GraphDatabase
        import ssl
        # Aura 使用加密连接，跳过 SSL 验证（国内环境证书问题）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        _neo4j_driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            ssl_context=ctx,
        )
    except ImportError as e:
        raise RuntimeError("未安装 neo4j 驱动，请运行: pip install neo4j (详细: " + str(e) + ")")
    except Exception as e:
        _neo4j_driver = None
        raise RuntimeError("Neo4j 连接失败: " + str(e))
    return _neo4j_driver


def _run_query(query, params=None, db=None):
    """执行单条 Cypher 查询并返回记录列表"""
    driver = _get_driver()
    target_db = db or NEO4J_DATABASE
    with (driver.session(database=target_db)) as session:
        result = session.run(query, params or {})
        return [dict(r) for r in result]


def _run_query_stream(query, params=None, batch_size=20000):
    """流式执行 Cypher 查询，分批返回结果"""
    driver = _get_driver()
    with (driver.session(database=NEO4J_DATABASE)) as session:
        result = session.run(query, params or {})
        batch = []
        for record in result:
            batch.append(dict(record))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


def _get_prop(props, *keys, default=None):
    """从节点/关系属性字典中获取值，支持多键名回退。
    
    Neo4j CSV 导入的属性名带有类型后缀（如 name:String, id:ID(Herb)），
    而 MERGE 同步的属性名是标准的（如 name, id）。此函数兼容两种格式。
    """
    for key in keys:
        if key in props:
            val = props[key]
            if val is not None:
                return val
        # 尝试去掉类型后缀的变体
        if ":" in key:
            base = key.split(":")[0]
            if base in props:
                val = props[base]
                if val is not None:
                    return val
        # 尝试给基础名加 :String 后缀
        if not ":" in key and (key + ":String") in props:
            val = props[key + ":String"]
            if val is not None:
                return val
    return default


def _extract_node_props(n_dict):
    """从 Neo4j Node 对象中提取属性字典"""
    if isinstance(n_dict, dict):
        return n_dict
    if hasattr(n_dict, "items"):
        return dict(n_dict.items())
    # 如果是 neo4j.graph.Node 对象，用 properties()
    if hasattr(n_dict, "properties"):
        return n_dict.properties
    return {}


def _extract_rel_props(r_obj):
    """从关系对象中提取属性"""
    if hasattr(r_obj, "items"):
        return dict(r_obj.items())
    if hasattr(r_obj, "properties"):
        return r_obj.properties
    return {}


def check_health():
    """检查 Neo4j 连接健康状态"""
    try:
        driver = _get_driver()
        driver.verify_connectivity()
        result = _run_query("RETURN 1 AS status")
        return {
            "connected": True,
            "uri": NEO4J_URI,
            "status": "ok",
        }
    except Exception as e:
        return {
            "connected": False,
            "uri": NEO4J_URI,
            "error": str(e),
        }


def sync_all_to_neo4j(batch_node=1000, batch_edge=5000):
    """将 SQLite 数据全量同步到 Neo4j（批量 UNWIND 模式，高效）

    Args:
        batch_node: 节点批次大小
        batch_edge: 边批次大小
    """
    db = get_db()
    try:
        _get_driver()  # 确保能连接
    except RuntimeError as e:
        db.close()
        raise e

    stats = {}

    # ---------- 删除旧约束 ----------
    drop_keys = [
        "DROP CONSTRAINT `id:ID(Herb)_Herb_key`",
        "DROP CONSTRAINT `id:ID(Ingredient)_Ingredient_key`",
        "DROP CONSTRAINT `id:ID(Disease)_Disease_key`",
    ]
    for cql in drop_keys:
        try:
            _run_query(cql)
        except Exception:
            pass

    for name in ["herb_id", "prescription_id", "component_id", "study_id", "disease_id"]:
        try:
            _run_query(f"DROP CONSTRAINT {name}")
        except Exception:
            pass

    # ---------- 创建新约束 ----------
    for name, clause in [
        ("herb_id", "FOR (n:Herb) REQUIRE n.id IS UNIQUE"),
        ("prescription_id", "FOR (n:Prescription) REQUIRE n.id IS UNIQUE"),
        ("component_id", "FOR (n:ChemicalComponent) REQUIRE n.id IS UNIQUE"),
        ("disease_id", "FOR (n:Disease) REQUIRE n.id IS UNIQUE"),
    ]:
        try:
            _run_query(f"CREATE CONSTRAINT {name} IF NOT EXISTS {clause}")
        except Exception:
            pass

    # ---------- 清空旧数据 ----------
    try:
        _run_query("MATCH (n) DETACH DELETE n")
        stats["cleared"] = True
    except Exception:
        stats["cleared"] = False

    # =========================================================================
    # 批量同步节点 (UNWIND)
    # =========================================================================

    def _batch_sync_nodes(rows, label, key_field, props_fn):
        """批量同步节点"""
        for i in range(0, len(rows), batch_node):
            batch = rows[i:i + batch_node]
            items = []
            for r in batch:
                props = props_fn(r)
                props["id"] = r[key_field] or ""
                items.append(props)
            _run_query(
                f"UNWIND $batch AS row MERGE (n:{label} {{id: row.id}}) SET n += row",
                {"batch": items}
            )
        return len(rows)

    # Herb
    herbs = db.execute("SELECT * FROM herb").fetchall()
    stats["herb_nodes"] = _batch_sync_nodes(herbs, "Herb", "tcmbank_id", lambda r: {
        "name": r["name"] or "",
        "latin_name": r["latin_name"] or "",
        "category": r["category"] or "",
        "nature": r["nature"] or "",
        "taste": r["taste"] or "",
        "meridian": r["meridian"] or "",
        "tcmbank_id": r["tcmbank_id"] or "",
        "pinyin_name": r["pinyin_name"] or "",
        "tcm_name_en": r["tcm_name_en"] or "",
        "efficacy": r["efficacy"] or "",
        "toxicity": r["toxicity"] or "",
        "dosage": r["dosage"] or "",
        "description": (r["description"] or "")[:500],
        "use_part": r["use_part"] or "",
        "indication": r["indication"] or "",
        "therapeutic_cn_class": r["therapeutic_cn_class"] or "",
    })

    # Prescription
    pres = db.execute("SELECT * FROM prescription").fetchall()
    stats["prescription_nodes"] = _batch_sync_nodes(pres, "Prescription", "cloud_id", lambda r: {
        "name": r["name"] or "",
        "source": r["source"] or "",
        "efficacy": r["efficacy"] or "",
        "category": r["category"] or "",
        "indications": r["indications"] or "",
    })

    # Pharmacology
    pharms = db.execute("SELECT * FROM pharmacology").fetchall()
    stats["pharmacology_nodes"] = _batch_sync_nodes(pharms, "Pharmacology", "cloud_id", lambda r: {
        "name": r["name"] or "",
    })

    # ChemicalComponent
    comps = db.execute("SELECT * FROM chemical_component").fetchall()
    stats["component_nodes"] = _batch_sync_nodes(comps, "ChemicalComponent", "cloud_id", lambda r: {
        "name": r["name"] or "",
        "formula": r["formula"] or "",
        "cas_number": r["cas_number"] or "",
        "bioactivity": r["bioactivity"] or "",
    })

    # Disease
    diseases = db.execute("SELECT * FROM disease").fetchall()
    stats["disease_nodes"] = _batch_sync_nodes(diseases, "Disease", "cloud_id", lambda r: {
        "name": r["name"] or "",
        "category": r["category"] or "",
        "tcm_syndrome": r["tcm_syndrome"] or "",
        "description": (r["description"] or "")[:500],
        "mesh_class": r["mesh_class"] or "",
    })

    # =========================================================================
    # 批量同步关系 (UNWIND)
    # =========================================================================
    edge_count = 0

    # TREATS: Herb -> Disease
    hd_list = db.execute("SELECT * FROM herb_disease").fetchall()
    for i in range(0, len(hd_list), batch_edge):
        batch = hd_list[i:i + batch_edge]
        items = [{"herb_id": r["herb_tcmbank_id"] or "", "disease_id": r["disease_cloud_id"] or "",
                   "indication": r["indication"] or ""} for r in batch]
        _run_query("""UNWIND $batch AS row
            MATCH (h:Herb {id: row.herb_id}) MATCH (d:Disease {id: row.disease_id})
            MERGE (h)-[:TREATS {indication: row.indication}]->(d)""", {"batch": items})
        edge_count += len(batch)

    # DERIVED_FROM: ChemicalComponent -> Herb
    ih_list = db.execute("SELECT * FROM ingredient_herb").fetchall()
    for i in range(0, len(ih_list), batch_edge):
        batch = ih_list[i:i + batch_edge]
        items = [{"ing_id": r["ingredient_id"] or "", "herb_id": r["herb_id"] or ""} for r in batch]
        _run_query("""UNWIND $batch AS row
            MATCH (ing:ChemicalComponent {id: row.ing_id}) MATCH (h:Herb {id: row.herb_id})
            MERGE (ing)-[:DERIVED_FROM]->(h)""", {"batch": items})
        edge_count += len(batch)

    # CONTAINS_HERB: Prescription -> Herb
    ph_list = db.execute("SELECT * FROM prescription_herb").fetchall()
    for i in range(0, len(ph_list), batch_edge):
        batch = ph_list[i:i + batch_edge]
        items = [{"pres_id": r["prescription_id"] or "", "herb_id": r["herb_id"] or "",
                   "dosage": r["dosage"] or ""} for r in batch]
        _run_query("""UNWIND $batch AS row
            MATCH (p:Prescription {id: row.pres_id}) MATCH (h:Herb {id: row.herb_id})
            MERGE (p)-[:CONTAINS_HERB {dosage: row.dosage}]->(h)""", {"batch": items})
        edge_count += len(batch)

    # Herb -> HAS_PHARMACOLOGY -> Pharmacology
    hp_list = db.execute("SELECT * FROM herb_pharmacology").fetchall()
    for i in range(0, len(hp_list), batch_edge):
        batch = hp_list[i:i + batch_edge]
        items = [{"herb_id": r["herb_id"] or "", "pharm_id": r["pharmacology_id"] or ""} for r in batch]
        _run_query("""UNWIND $batch AS row
            MATCH (h:Herb {id: row.herb_id}) MATCH (p:Pharmacology {id: row.pharm_id})
            MERGE (h)-[:HAS_PHARMACOLOGY]->(p)""", {"batch": items})
        edge_count += len(batch)

    # Ingredient -> HAS_PHARMACOLOGY -> Pharmacology
    ip_list = db.execute("SELECT * FROM ingredient_pharmacology").fetchall()
    for i in range(0, len(ip_list), batch_edge):
        batch = ip_list[i:i + batch_edge]
        items = [{"ing_id": r["ingredient_id"] or "", "pharm_id": r["pharmacology_id"] or ""} for r in batch]
        _run_query("""UNWIND $batch AS row
            MATCH (ing:ChemicalComponent {id: row.ing_id}) MATCH (p:Pharmacology {id: row.pharm_id})
            MERGE (ing)-[:HAS_PHARMACOLOGY]->(p)""", {"batch": items})
        edge_count += len(batch)

    stats["edge_count"] = edge_count

    stats["edges"] = edge_count

    db.close()
    return stats


def _sqlite_id_to_neo4j_id(entity_type, sqlite_id):
    """将 SQLite 的自增 ID 映射到 Neo4j 的 id:ID(...) 值
    
    通过查询 Neo4j 建立 SQLite id -> Neo4j id 的映射。
    如果找不到，返回 None。
    """
    label_map = {
        "herb": "Herb", "prescription": "Prescription",
        "component": "ChemicalComponent", "study": "PharmaStudy",
        "disease": "Disease", "ingredient": "Ingredient",
    }
    label = label_map.get(entity_type)
    if not label:
        return None
    
    try:
        # 尝试通过 name 来匹配（最可靠的方式）
        # 先从 SQLite 获取 name
        from database import get_db
        db = get_db()
        table_map = {
            "herb": "herb", "prescription": "prescription",
            "component": "chemical_component", "study": "pharma_study",
            "disease": "disease", "ingredient": "chemical_component",
        }
        table = table_map.get(entity_type)
        if not table:
            db.close()
            return None
        
        name = None
        if table in ("herb", "prescription", "disease"):
            row = db.execute(f"SELECT name FROM {table} WHERE id = ?", (sqlite_id,)).fetchone()
            if row:
                name = row["name"]
        elif table in ("component", "study"):
            row = db.execute(f"SELECT name FROM {table} WHERE id = ?", (sqlite_id,)).fetchone()
            if row:
                name = row["name"]
        elif table == "study":
            row = db.execute(f"SELECT title FROM pharma_study WHERE id = ?", (sqlite_id,)).fetchone()
            if row:
                name = row["title"]
        db.close()
        
        if not name:
            return None
        
        # 在 Neo4j 中通过 name 查找对应的节点，获取其 id:ID(...) 值
        result = _run_query(
            "MATCH (n:`" + label + "` {name: $name}) RETURN n.`id:ID(" + label + ")` AS neo4j_id LIMIT 1",
            {"name": name}
        )
        if result and result[0].get("neo4j_id"):
            return result[0]["neo4j_id"]
        return None
    except Exception:
        return None


def query_entity_graph(entity_type, entity_id):
    """从 Neo4j 查询实体为中心的图谱子图
    
    entity_id 可以是 SQLite 的主键值（tcmbank_id 或 cloud_id）或 Neo4j 的 id:ID(...) 值。
    对于 herb，entity_id 是 tcmbank_id；对于 disease/component，是 cloud_id。
    """
    label_map = {
        "herb": "Herb", "prescription": "Prescription",
        "component": "ChemicalComponent", "study": "PharmaStudy",
        "disease": "Disease", "ingredient": "Ingredient",
        "pharmacology": "Pharmacology",
    }
    reverse_label_map = {v: k for k, v in label_map.items()}
    # SQLite 主键列名 -> Neo4j 标签的映射
    id_column_map = {
        "herb": "tcmbank_id",
        "disease": "cloud_id",
        "component": "cloud_id",
    }
    label = label_map.get(entity_type)
    if not label:
        return {"nodes": [], "edges": []}

    try:
        # entity_id 是 Neo4j 节点的 id 属性值（如 H_TCMBANKHE000001）
        neo4j_id = str(entity_id)

        # 统一使用标准 id 属性名（sync_all_to_neo4j 已清除 CSV 格式残留）
        id_attr_name = "id"

        # 查询节点和一度关系
        records = _run_query("""
            MATCH (n:`""" + label + """` {`""" + id_attr_name + """`: $id})-[r]-(m)
            RETURN n, r, m, type(r) AS rel_type, labels(n) AS n_labels, labels(m) AS m_labels
        """, {"id": neo4j_id})

        nodes = {}
        edges = []

        # 中心节点
        center = _run_query(
            "MATCH (n:`" + label + "` {`" + id_attr_name + "`: $id}) RETURN n",
            {"id": neo4j_id}
        )
        for c in center:
            n_props = _extract_node_props(c["n"])
            nid = _get_prop(n_props, "id", default=None)
            if nid is None:
                continue
            name = _get_prop(n_props, "name", default="")
            nodes[entity_type + "_" + str(nid)] = {
                "type": entity_type, "id": nid, "name": name,
            }

        for rec in records:
            n_props = _extract_node_props(rec["n"])
            m_props = _extract_node_props(rec["m"])
            n_labels = rec["n_labels"]
            m_labels = rec["m_labels"]
            r = rec["r"]

            nid = _get_prop(n_props, "id", default=None)
            mid = _get_prop(m_props, "id", default=None)
            if nid is None or mid is None:
                continue

            n_type = "unknown"
            for lbl in n_labels:
                if lbl in reverse_label_map:
                    n_type = reverse_label_map[lbl]
                    break
            m_type = "unknown"
            for lbl in m_labels:
                if lbl in reverse_label_map:
                    m_type = reverse_label_map[lbl]
                    break

            n_key = n_type + "_" + str(nid)
            m_key = m_type + "_" + str(mid)
            n_name = _get_prop(n_props, "name", default="")
            m_name = _get_prop(m_props, "name", default="")
            m_title = _get_prop(m_props, "title", default="")
            if not m_name:
                m_name = m_title

            if n_key not in nodes:
                nodes[n_key] = {"type": n_type, "id": nid, "name": n_name}
            if m_key not in nodes:
                nodes[m_key] = {"type": m_type, "id": mid, "name": m_name}

            rel_props = _extract_rel_props(r)
            edges.append({
                "source": n_key, "target": m_key,
                "relationship": rec["rel_type"],
                "properties": rel_props,
            })

        return {"nodes": list(nodes.values()), "edges": edges}
    except Exception:
        # fallback to SQLite
        return GraphService.query_entity_graph(entity_type, entity_id)


def get_statistics():
    """从 Neo4j 获取图谱统计信息"""
    try:
        rec = _run_query("""
            MATCH (n)
            RETURN labels(n) AS label, count(*) AS cnt
            ORDER BY cnt DESC
        """)
        node_counts = {}
        for r in rec:
            lbl = r["label"][0] if r["label"] else "Unknown"
            # 映射为友好名称
            friendly = {"Herb": "Herb", "Prescription": "Prescription",
                        "ChemicalComponent": "ChemicalComponent", "PharmaStudy": "PharmaStudy",
                        "Disease": "Disease", "Ingredient": "Ingredient",
                        "Pharmacology": "Pharmacology"}
            node_counts[friendly.get(lbl, lbl)] = r["cnt"]

        rel_rec = _run_query("""
            MATCH ()-[r]->()
            RETURN type(r) AS rel_type, count(*) AS cnt
            ORDER BY cnt DESC
        """)
        rel_counts = {}
        for r in rel_rec:
            rel_counts[r["rel_type"]] = r["cnt"]

        return {"nodes": node_counts, "relationships": rel_counts}
    except Exception:
        # fallback to SQLite
        return GraphService.get_statistics()


def sync_from_neo4j():
    """从云端 Neo4j 导出数据到本地 SQLite
    
    策略：分批从 Neo4j 读取数据，每批立即插入 SQLite，避免大内存占用和网络传输瓶颈。
    """
    db = get_db()
    try:
        driver = _get_driver()
    except RuntimeError as e:
        db.close()
        raise e

    stats = {}

    def get_field(n, field_key, default=""):
        """从节点获取字段，支持多键名回退"""
        val = n.get(field_key, "")
        if not val:
            base_key = field_key.rsplit(":", 1)[0] if ":" in field_key else field_key
            val = n.get(base_key, default)
        return (val or default)

    # ========== 1. 同步 Herb 节点 ==========
    print("  同步 Herb 节点...")
    herb_cloud_to_name = {}
    herb_name_to_id = {}
    all_herb_names = set()
    
    for batch_data in _run_query_stream("MATCH (n:Herb) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            cloud_id = props.get("id:ID(Herb)", "")
            name = props.get("name:String", "")
            if cloud_id and name:
                herb_cloud_to_name[cloud_id] = name
                all_herb_names.add(name)
    
    # 批量 INSERT herb
    db.executemany("INSERT OR IGNORE INTO herb (name) VALUES (?)", [(n,) for n in all_herb_names])
    db.commit()
    
    # 构建 name -> sqlite_id（批量查询，分批避免参数过多）
    herb_name_to_id = {}
    name_list = list(all_herb_names)
    for i in range(0, len(name_list), 1000):
        batch_names = name_list[i:i+1000]
        query = "SELECT name, id FROM herb WHERE name IN (" + ",".join(["?"] * len(batch_names)) + ")"
        for name, row_id in db.execute(query, batch_names).fetchall():
            herb_name_to_id[name] = row_id
    
    # 批量更新 Herb 属性
    batch = []
    for batch_data in _run_query_stream("MATCH (n:Herb) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            name = props.get("name:String", "")
            if name not in herb_name_to_id:
                continue
            batch.append((
                props.get("latinName:String", "") or "",
                props.get("category:String", "") or "",
                props.get("nature:String", "") or "",
                props.get("flavor:String", "") or "",
                props.get("meridian:String", "") or "",
                props.get("efficacy", "") or "",
                props.get("toxicity:String", "") or "",
                props.get("dosage:String", "") or "",
                (props.get("description:String", "") or "")[:500],
                props.get("pinyin:String", "") or "",
                props.get("englishName:String", "") or "",
                props.get("use_part:String", "") or "",
                props.get("indication:String", "") or "",
                props.get("therapeutic_cn_class:String", "") or "",
                props.get("id:ID(Herb)", "") or "",
                herb_name_to_id[name],
            ))
            if len(batch) >= 2000:
                db.executemany("""UPDATE herb SET latin_name=?, category=?, nature=?, taste=?, meridian=?,
                    efficacy=?, toxicity=?, dosage=?, description=?, pinyin_name=?, tcm_name_en=?,
                    use_part=?, indication=?, therapeutic_cn_class=?, tcmbank_id=? WHERE id=?""", batch)
                db.commit()
                batch = []
    if batch:
        db.executemany("""UPDATE herb SET latin_name=?, category=?, nature=?, taste=?, meridian=?,
            efficacy=?, toxicity=?, dosage=?, description=?, pinyin_name=?, tcm_name_en=?,
            use_part=?, indication=?, therapeutic_cn_class=?, tcmbank_id=? WHERE id=?""", batch)
        db.commit()
    
    stats["herb_nodes"] = len(herb_cloud_to_name)
    print(f"    Herb: {len(herb_cloud_to_name)}")

    # ========== 2. 同步 Disease 节点 ==========
    print("  同步 Disease 节点...")
    disease_cloud_to_name = {}
    disease_name_to_id = {}
    all_disease_names = set()
    
    for batch_data in _run_query_stream("MATCH (n:Disease) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            cloud_id = props.get("id:ID(Disease)", "")
            name = props.get("name:String", "")
            if cloud_id and name:
                disease_cloud_to_name[cloud_id] = name
                all_disease_names.add(name)
    
    db.executemany("INSERT OR IGNORE INTO disease (name) VALUES (?)", [(n,) for n in all_disease_names])
    db.commit()
    
    # 批量查询 disease id（分批避免参数过多）
    disease_name_to_id = {}
    name_list = list(all_disease_names)
    for i in range(0, len(name_list), 1000):
        batch_names = name_list[i:i+1000]
        query = "SELECT name, id FROM disease WHERE name IN (" + ",".join(["?"] * len(batch_names)) + ")"
        for name, row_id in db.execute(query, batch_names).fetchall():
            disease_name_to_id[name] = row_id
    
    # 批量更新 Disease 属性
    batch = []
    for batch_data in _run_query_stream("MATCH (n:Disease) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            name = props.get("name:String", "")
            if name not in disease_name_to_id:
                continue
            batch.append((
                props.get("category:String", "") or "",
                (props.get("description:String", "") or "")[:500],
                disease_name_to_id[name],
            ))
            if len(batch) >= 2000:
                db.executemany("UPDATE disease SET category=?, description=? WHERE id=?", batch)
                db.commit()
                batch = []
    if batch:
        db.executemany("UPDATE disease SET category=?, description=? WHERE id=?", batch)
        db.commit()
    
    stats["disease_nodes"] = len(disease_cloud_to_name)
    print(f"    Disease: {len(disease_cloud_to_name)}")

    # ========== 3. 同步 Ingredient (作为 ChemicalComponent) ==========
    print("  同步 ChemicalComponent (Ingredient) 节点...")
    comp_cloud_to_name = {}
    comp_name_to_id = {}
    all_comp_names = set()
    
    for batch_data in _run_query_stream("MATCH (n) WHERE 'Ingredient' IN labels(n) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            cloud_id = props.get("id:ID(Ingredient)", "")
            name = props.get("name:String", "")
            if cloud_id and name:
                comp_cloud_to_name[cloud_id] = name
                all_comp_names.add(name)
    
    db.executemany("INSERT OR IGNORE INTO chemical_component (name) VALUES (?)", [(n,) for n in all_comp_names])
    db.commit()
    
    # 批量查询 chemical_component id（分批避免参数过多）
    comp_name_to_id = {}
    name_list = list(all_comp_names)
    for i in range(0, len(name_list), 1000):
        batch_names = name_list[i:i+1000]
        query = "SELECT name, id FROM chemical_component WHERE name IN (" + ",".join(["?"] * len(batch_names)) + ")"
        for name, row_id in db.execute(query, batch_names).fetchall():
            comp_name_to_id[name] = row_id
    
    # 批量更新 Ingredient 属性
    batch = []
    for batch_data in _run_query_stream("MATCH (n) WHERE 'Ingredient' IN labels(n) RETURN properties(n) AS props", batch_size=5000):
        for rec in batch_data:
            props = rec["props"]
            name = props.get("name:String", "")
            if name not in comp_name_to_id:
                continue
            batch.append((
                props.get("molecularFormula:String", "") or "",
                props.get("casNumber:String", "") or "",
                comp_name_to_id[name],
            ))
            if len(batch) >= 2000:
                db.executemany("UPDATE chemical_component SET formula=?, cas_number=? WHERE id=?", batch)
                db.commit()
                batch = []
    if batch:
        db.executemany("UPDATE chemical_component SET formula=?, cas_number=? WHERE id=?", batch)
        db.commit()
    
    stats["component_nodes"] = len(comp_cloud_to_name)
    print(f"    ChemicalComponent: {len(comp_cloud_to_name)}")

    # ========== 4. 同步 herb_disease 关系 (TREATS) ==========
    print("  同步 TREATS 关系...")
    treat_set = set()
    for batch_data in _run_query_stream("MATCH (h)-[r:TREATS]->(d) RETURN h, d, r", batch_size=5000):
        for rec in batch_data:
            h = rec["h"]
            d = rec["d"]
            h_id = h.get("id:ID(Herb)", "")
            d_id = d.get("id:ID(Disease)", "")
            if h_id in herb_cloud_to_name and d_id in disease_cloud_to_name:
                herb_name = herb_cloud_to_name[h_id]
                disease_name = disease_cloud_to_name[d_id]
                if herb_name in herb_name_to_id and disease_name in disease_name_to_id:
                    indication = get_field(rec["r"], "indication:String", "")
                    treat_set.add((herb_name_to_id[herb_name], disease_name_to_id[disease_name], indication[:200]))
    
    treat_count = 0
    batch = []
    for herb_id, disease_id, indication in treat_set:
        batch.append((herb_id, disease_id, indication))
        if len(batch) >= 1000:
            db.executemany(
                "INSERT INTO herb_disease (herb_id, disease_id, relationship_type, evidence_level) VALUES (?, ?, 'TREATS', ?)",
                batch
            )
            db.commit()
            treat_count += len(batch)
            batch = []
    if batch:
        db.executemany(
            "INSERT INTO herb_disease (herb_id, disease_id, relationship_type, evidence_level) VALUES (?, ?, 'TREATS', ?)",
            batch
        )
        db.commit()
        treat_count += len(batch)
    
    stats["treats_edges"] = treat_count
    print(f"    TREATS: {treat_count}")

    # ========== 5. 同步 CONTAINS 关系 (FOUND_IN: Ingredient -> Herb) ==========
    print("  同步 FOUND_IN (CONTAINS) 关系...")
    contains_updates = set()
    for batch_data in _run_query_stream("MATCH (ing)-[r:FOUND_IN]->(h) RETURN ing, h, r", batch_size=5000):
        for rec in batch_data:
            ing = rec["ing"]
            h = rec["h"]
            ing_id = ing.get("id:ID(Ingredient)", "")
            h_id = h.get("id:ID(Herb)", "")
            if ing_id in comp_cloud_to_name and h_id in herb_cloud_to_name:
                comp_name = comp_cloud_to_name[ing_id]
                herb_name = herb_cloud_to_name[h_id]
                if comp_name in comp_name_to_id and herb_name in herb_name_to_id:
                    contains_updates.add((comp_name_to_id[comp_name], herb_name_to_id[herb_name]))
    
    contains_count = 0
    batch = []
    for comp_id, herb_id in contains_updates:
        batch.append((herb_id, comp_id))
        if len(batch) >= 1000:
            db.executemany("UPDATE chemical_component SET herb_id=? WHERE id=?", batch)
            db.commit()
            contains_count += len(batch)
            batch = []
    if batch:
        db.executemany("UPDATE chemical_component SET herb_id=? WHERE id=?", batch)
        db.commit()
        contains_count += len(batch)
    
    stats["contains_edges"] = contains_count
    print(f"    CONTAINS: {contains_count}")

    stats["completed_at"] = __import__("datetime").datetime.now().isoformat()
    db.close()
    return stats