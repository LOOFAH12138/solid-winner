# -*- coding: utf-8 -*-
"""知识库与图谱服务层 —— RAG 知识块管理 + 图谱查询 + Agnes AI 问答"""
import json
import urllib.request
import urllib.error
import threading
from database import get_db

# Agnes AI API 配置
AGNES_API_KEYS = [
    "sk-eW7wbOicj8Hen8wkWFMz5uPmSV8l8BQWuRVNiKI5dLzDiIDa",
    "cpk-9MLPKnhyqkDNapPXEgb31oHFBZyPb45sWKpEdjF1EGJDravM",
]
AGNES_BASE_URL = "https://apihub.agnes-ai.com/v1"

# API Key 轮询计数器
_api_key_index = 0
_api_key_lock = threading.Lock()


def _get_next_api_key():
    """获取下一个 API Key（轮询）"""
    global _api_key_index
    with _api_key_lock:
        key = AGNES_API_KEYS[_api_key_index % len(AGNES_API_KEYS)]
        _api_key_index += 1
        return key

# 内置已知模型列表（作为 fallback）
DEFAULT_MODELS = [
    {"id": "agnes-1.5-flash", "name": "Agnes-1.5-Flash", "description": "快速响应模型"},
    {"id": "agnes-2.0-flash", "name": "Agnes-2.0-Flash", "description": "高性能模型"},
]


class KnowledgeService:
    """RAG 知识块管理"""

    @staticmethod
    def add_chunk(title, content, entity_type=None, entity_id=None, chunk_index=0,
                  source_type="manual", metadata=None, embedding_model=None):
        """添加知识块"""
        conn = get_db()
        conn.execute("""
            INSERT INTO knowledge_chunk (title, content, chunk_index, source_type, entity_type, entity_id, metadata, embedding_model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, content, chunk_index, source_type, entity_type, entity_id,
              json.dumps(metadata or {}, ensure_ascii=False), embedding_model))
        conn.commit()
        conn.close()

    @staticmethod
    def add_entity_chunks(entity_type, entity_id, title, text_content, chunk_size=500):
        """对实体描述进行分块存储"""
        conn = get_db()
        # 先删除旧分块
        conn.execute("DELETE FROM knowledge_chunk WHERE entity_type=? AND entity_id=?", (entity_type, entity_id))

        chunks = KnowledgeService._split_text(text_content, chunk_size)
        for i, chunk in enumerate(chunks):
            conn.execute("""
                INSERT INTO knowledge_chunk (title, content, chunk_index, source_type, entity_type, entity_id, metadata)
                VALUES (?, ?, ?, 'entity', ?, ?, ?)
            """, (title, chunk, i, entity_type, entity_id, json.dumps({"chunk_of": len(chunks)}, ensure_ascii=False)))
        conn.commit()
        conn.close()
        return len(chunks)

    @staticmethod
    def _split_text(text, size=500):
        """简单文本分块（按句子边界）"""
        if not text:
            return []
        sentences = text.replace("。", "。\n").replace("；", "；\n").split("\n")
        chunks = []
        current = ""
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if len(current) + len(s) > size and current:
                chunks.append(current.strip())
                current = s
            else:
                current += s
        if current.strip():
            chunks.append(current.strip())
        return chunks if chunks else [text]

    @staticmethod
    def search_chunks(query, entity_type=None, limit=10):
        """全文搜索知识块"""
        conn = get_db()
        conditions = ["(title LIKE ? OR content LIKE ?)"]
        params = ["%" + query + "%", "%" + query + "%"]

        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type)

        where = " WHERE " + " AND ".join(conditions)
        rows = conn.execute(
            "SELECT * FROM knowledge_chunk" + where + " ORDER BY id LIMIT ?",
            params + [limit]
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def search_chunks_extended(query, limit=20):
        """全库扩展搜索：覆盖所有数据库表和知识图谱关系"""
        conn = get_db()
        all_chunks = []

        # 1. 从知识块表搜索（基础搜索）
        conditions = ["(title LIKE ? OR content LIKE ?)"]
        params = ["%" + query + "%", "%" + query + "%"]
        where = " WHERE " + " AND ".join(conditions)
        rows = conn.execute(
            "SELECT * FROM knowledge_chunk" + where + " LIMIT ?",
            params + [limit]
        ).fetchall()
        all_chunks.extend([dict(r) for r in rows])

        # 2. 搜索药材表 (herb) - 使用 tcmbank_id 作为主键
        herb_conditions = [
            "name LIKE ?", "latin_name LIKE ?", "category LIKE ?",
            "nature LIKE ?", "taste LIKE ?", "meridian LIKE ?",
            "pinyin_name LIKE ?", "tcm_name_en LIKE ?"
        ]
        herb_params = ["%" + query + "%"] * len(herb_conditions)
        if herb_conditions:
            herb_where = " WHERE " + " OR ".join(herb_conditions)
            herb_rows = conn.execute(
                f"SELECT tcmbank_id AS id, name, latin_name, category, nature, taste, meridian, "
                f"pinyin_name, tcm_name_en FROM herb{herb_where}", herb_params
            ).fetchall()
            for h in [dict(r) for r in herb_rows]:
                content_parts = []
                content_parts.append(f"药材名称：{h['name']}")
                if h.get('latin_name'):
                    content_parts.append(f"拉丁名：{h['latin_name']}")
                if h.get('category'):
                    content_parts.append(f"分类：{h['category']}")
                if h.get('nature'):
                    content_parts.append(f"性：{h['nature']}")
                if h.get('taste'):
                    content_parts.append(f"味：{h['taste']}")
                if h.get('meridian'):
                    content_parts.append(f"归经：{h['meridian']}")
                if h.get('pinyin_name'):
                    content_parts.append(f"拼音：{h['pinyin_name']}")
                if h.get('tcm_name_en'):
                    content_parts.append(f"英文名：{h['tcm_name_en']}")

                all_chunks.append({
                    'id': 'herb_' + str(h['id']),
                    'title': h['name'],
                    'content': '。'.join(content_parts),
                    'entity_type': 'herb',
                    'source': 'herb'
                })

        # 3. 搜索病症表 (disease) - 使用 cloud_id 作为主键
        disease_conditions = [
            "name LIKE ?", "description LIKE ?", "tcm_syndrome LIKE ?", "category LIKE ?"
        ]
        disease_params = ["%" + query + "%"] * len(disease_conditions)
        if disease_conditions:
            disease_where = " WHERE " + " OR ".join(disease_conditions)
            disease_rows = conn.execute(
                f"SELECT cloud_id AS id, name, category, description, tcm_syndrome, mesh_class FROM disease"
                f"{disease_where}", disease_params
            ).fetchall()
            for d in [dict(r) for r in disease_rows]:
                content_parts = []
                content_parts.append(f"病症名称：{d['name']}")
                if d.get('category'):
                    content_parts.append(f"分类：{d['category']}")
                if d.get('description'):
                    content_parts.append(f"描述：{d['description']}")
                if d.get('tcm_syndrome'):
                    content_parts.append(f"中医证型：{d['tcm_syndrome']}")
                if d.get('mesh_class'):
                    content_parts.append(f"MeSH分类：{d['mesh_class']}")

                all_chunks.append({
                    'id': 'disease_' + str(d['id']),
                    'title': d['name'],
                    'content': '。'.join(content_parts),
                    'entity_type': 'disease',
                    'source': 'disease'
                })

        # 4. 搜索化学成分表 (chemical_component) - 使用 cloud_id 作为主键
        comp_conditions = [
            "name LIKE ?", "formula LIKE ?", "bioactivity LIKE ?"
        ]
        comp_params = ["%" + query + "%"] * len(comp_conditions)
        if comp_conditions:
            comp_where = " WHERE " + " OR ".join(comp_conditions)
            comp_rows = conn.execute(
                f"SELECT cloud_id AS id, name, formula, cas_number, bioactivity, herb_id FROM chemical_component"
                f"{comp_where}", comp_params
            ).fetchall()
            for c in [dict(r) for r in comp_rows]:
                # 获取药材名称
                herb_name = ""
                if c.get('herb_id'):
                    herb_row = conn.execute("SELECT name FROM herb WHERE tcmbank_id=?", (c['herb_id'],)).fetchone()
                    if herb_row:
                        herb_name = herb_row['name']
                
                content_parts = []
                content_parts.append(f"成分名称：{c['name']}")
                if herb_name:
                    content_parts.append(f"来源药材：{herb_name}")
                if c.get('formula'):
                    content_parts.append(f"分子式：{c['formula']}")
                if c.get('cas_number'):
                    content_parts.append(f"CAS号：{c['cas_number']}")
                if c.get('bioactivity'):
                    content_parts.append(f"生物活性：{c['bioactivity']}")

                all_chunks.append({
                    'id': 'comp_' + str(c['id']),
                    'title': c['name'],
                    'content': '。'.join(content_parts),
                    'entity_type': 'component',
                    'source': 'chemical_component'
                })

        # 5. 搜索 Herb-Disease 关系表 (herb_disease)
        if query:
            # 查找包含 query 的药材-病症关系
            treat_conditions = ["indication LIKE ?"]
            treat_params = ["%" + query + "%"]
            treat_where = " WHERE " + " OR ".join(treat_conditions)
            treat_rows = conn.execute(
                f"SELECT id, herb_tcmbank_id, disease_cloud_id, relationship_type, indication FROM herb_disease"
                f"{treat_where}", treat_params
            ).fetchall()
            for t in [dict(r) for r in treat_rows]:
                herb_row = conn.execute("SELECT name FROM herb WHERE tcmbank_id=?", (t['herb_tcmbank_id'],)).fetchone()
                disease_row = conn.execute("SELECT name FROM disease WHERE cloud_id=?", (t['disease_cloud_id'],)).fetchone()
                
                herb_name = herb_row['name'] if herb_row else "未知药材"
                disease_name = disease_row['name'] if disease_row else "未知病症"
                
                content_parts = []
                content_parts.append(f"关系：{herb_name} 治疗 {disease_name}")
                if t.get('indication'):
                    content_parts.append(f"适应症：{t['indication']}")

                all_chunks.append({
                    'id': 'treat_' + str(t['id']),
                    'title': f"{herb_name} - {disease_name}",
                    'content': '。'.join(content_parts),
                    'entity_type': 'herb_disease_relation',
                    'source': 'herb_disease'
                })

        # 6. 从 Neo4j 图谱获取关联知识（如果 Neo4j 可用）
        try:
            from .neo4j_service import _run_query, _get_prop, _extract_node_props, _extract_rel_props
            # 搜索 Neo4j 中与 query 相关的节点和关系 - 使用标准属性名
            cypher_query = """
                MATCH (n)
                WHERE toString(n.name) CONTAINS $query 
                   OR toString(n.title) CONTAINS $query
                   OR toString(n.latin_name) CONTAINS $query
                   OR toString(n.description) CONTAINS $query
                   OR toString(n.efficacy) CONTAINS $query
                   OR toString(n.indications) CONTAINS $query
                   OR toString(n.tcm_syndrome) CONTAINS $query
                OPTIONAL MATCH (n)-[r]-(m)
                RETURN n, r, m, type(r) AS rel_type
            """
            neo4j_results = _run_query(cypher_query, {"query": query})
            
            # 按节点分组，收集其关系
            node_relations = {}
            for rec in neo4j_results:
                n_props = _extract_node_props(rec["n"])
                n_id = _get_prop(n_props, "id", default="")
                n_name = _get_prop(n_props, "name", default="Unknown")
                n_labels = n_props.get(":LABEL", "")
                if not n_labels:
                    # 从别的途径获取 label 信息
                    n_labels = rec.get("n_labels", "")
                
                if n_id not in node_relations:
                    node_relations[n_id] = {
                        "id": n_id,
                        "name": n_name,
                        "labels": n_labels,
                        "properties": n_props,
                        "relations": []
                    }
                
                if rec["r"] is not None:
                    m_props = _extract_node_props(rec["m"])
                    rel_type = rec["rel_type"]
                    m_name = _get_prop(m_props, "name", default="Unknown")
                    
                    node_relations[n_id]["relations"].append({
                        "relationship": rel_type,
                        "target_name": m_name,
                        "target_props": m_props,
                        "props": _extract_rel_props(rec["r"]),
                    })
            
            # 将图谱关系转化为知识块
            for nid, node_info in node_relations.items():
                content_parts = []
                content_parts.append(f"图谱节点：{node_info['name']} ({node_info['labels']})")
                
                props = node_info['properties']
                for key_plain, label in [
                    ("latin_name", "latin_name"),
                    ("category", "category"),
                    ("nature", "nature"),
                    ("taste", "taste"),
                    ("efficacy", "efficacy"),
                    ("description", "description"),
                    ("indications", "indications"),
                    ("tcm_syndrome", "tcm_syndrome"),
                ]:
                    val = _get_prop(props, key_plain, default=None)
                    if val:
                        content_parts.append(f"{label}: {val}")
                
                for rel in node_info['relations']:
                    content_parts.append(f"{node_info['name']} -[{rel['relationship']}]-> {rel['target_name']}")
                
                all_chunks.append({
                    'id': 'neo4j_' + str(nid),
                    'title': node_info['name'],
                    'content': '。'.join(content_parts),
                    'entity_type': 'neo4j_graph',
                    'source': 'neo4j'
                })
        except Exception:
            pass  # Neo4j 不可用时跳过

        # 7. 去重并限制数量
        seen = set()
        unique_chunks = []
        for chunk in all_chunks:
            key = str(chunk.get('id', '')) + chunk.get('title', '')
            if key not in seen:
                seen.add(key)
                unique_chunks.append(chunk)
                if len(unique_chunks) >= limit:
                    break

        conn.close()
        
        # 8. 按优先级排序：Neo4j 图谱优先，数据库表在后
        priority_order = {
            'neo4j': 1,
            'herb': 2,
            'herb_disease_relation': 3,
            'disease': 4,
            'component': 5,
        }
        unique_chunks.sort(key=lambda c: (priority_order.get(c.get('entity_type', ''), 99), c.get('title', '')))
        
        return unique_chunks[:limit]

    @staticmethod
    def rebuild_all_entity_chunks():
        """重建所有实体的知识块"""
        conn = get_db()
        total = 0

        # 药材描述分块
        herbs = conn.execute("SELECT tcmbank_id AS id, name, nature, taste, meridian FROM herb LIMIT 100").fetchall()
        for h in herbs:
            text = f"药材名称：{h['name']}。性味：{h['nature'] or ''}。归经：{h['meridian'] or ''}"
            total += KnowledgeService.add_entity_chunks("herb", h["id"], h["name"], text)

        conn.close()
        return total


class GraphService:
    """图谱查询服务"""

    @staticmethod
    def query_entity_graph(entity_type, entity_id, depth=1):
        """查询实体为中心的图谱子图"""
        conn = get_db()
        nodes = set()
        edges = []

        # 起始节点信息
        if entity_type == "herb":
            node_row = conn.execute("SELECT tcmbank_id AS id, name FROM herb WHERE tcmbank_id=?", (entity_id,)).fetchone()
        elif entity_type == "disease":
            node_row = conn.execute("SELECT cloud_id AS id, name FROM disease WHERE cloud_id=?", (entity_id,)).fetchone()
        elif entity_type == "component":
            node_row = conn.execute("SELECT cloud_id AS id, name FROM chemical_component WHERE cloud_id=?", (entity_id,)).fetchone()
        else:
            conn.close()
            return {"nodes": [], "edges": []}

        if not node_row:
            conn.close()
            return {"nodes": [], "edges": []}

        nodes.add((entity_type, entity_id, node_row["name"]))

        # 查询 Herb-Disease 关系
        if entity_type == "herb":
            rels = conn.execute("""
                SELECT herb_tcmbank_id, disease_cloud_id, indication FROM herb_disease WHERE herb_tcmbank_id=?
            """, (entity_id,)).fetchall()
            for r in rels:
                disease_row = conn.execute("SELECT name FROM disease WHERE cloud_id=?", (r['disease_cloud_id'],)).fetchone()
                disease_name = disease_row['name'] if disease_row else "未知"
                edges.append({
                    "source": f"herb_{entity_id}",
                    "target": f"disease_{r['disease_cloud_id']}",
                    "relationship": "TREATS",
                    "properties": {"indication": r['indication']},
                })
                nodes.add(("disease", r['disease_cloud_id'], disease_name))
        
        elif entity_type == "disease":
            rels = conn.execute("""
                SELECT herb_tcmbank_id, disease_cloud_id, indication FROM herb_disease WHERE disease_cloud_id=?
            """, (entity_id,)).fetchall()
            for r in rels:
                herb_row = conn.execute("SELECT name FROM herb WHERE tcmbank_id=?", (r['herb_tcmbank_id'],)).fetchone()
                herb_name = herb_row['name'] if herb_row else "未知"
                edges.append({
                    "source": f"herb_{r['herb_tcmbank_id']}",
                    "target": f"disease_{entity_id}",
                    "relationship": "TREATS",
                    "properties": {"indication": r['indication']},
                })
                nodes.add(("herb", r['herb_tcmbank_id'], herb_name))

        conn.close()

        return {
            "nodes": [{"type": n[0], "id": n[1], "name": n[2]} for n in nodes],
            "edges": edges
        }

    @staticmethod
    def get_statistics():
        """获取图谱统计信息"""
        conn = get_db()
        node_counts = {}
        for table in ['herb', 'disease', 'chemical_component']:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            node_counts[table] = count
        
        treat_count = conn.execute("SELECT COUNT(*) FROM herb_disease").fetchone()[0]
        node_counts['herb_disease_relations'] = treat_count

        conn.close()
        return {"nodes": node_counts}


class QAService:
    """Agnes AI 问答服务 - 支持模型切换"""

    @staticmethod
    def _call_api(endpoint, body):
        """调用 Agnes AI API（使用轮询 API Key）"""
        url = AGNES_BASE_URL + endpoint
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", "Bearer " + _get_next_api_key())
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                err_msg = err_body[:300]
            raise RuntimeError(f"API 错误 (HTTP {e.code}): {err_msg}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"网络错误: {e.reason}")

    @staticmethod
    def fetch_models():
        """返回可用模型列表"""
        return DEFAULT_MODELS

    @staticmethod
    def chat(query, context_chunks, model="agnes-2.0-flash"):
        """调用 Agnes AI 进行问答"""
        system_prompt = (
            "你是一位专业的中医药学专家助手，精通中药学、方剂学、中药化学和药理学。\n\n"
            "【核心原则 - 必须严格执行】\n"
            "1. 你必须首先严格基于提供的【知识库内容】进行回答，这些信息来自本项目数据库。\n"
            "2. 数据库中的信息具有最高优先级，必须以数据库为准。\n"
            "3. 仅当知识库完全没有相关信息时，才可以使用你的训练数据进行补充说明。\n"
            "4. 如果知识库信息与你的训练数据有冲突，以知识库为准。\n\n"
            "【来源标注 - 必须严格执行】\n"
            "回答每个要点时，必须标注信息来源。按以下优先级标注：\n\n"
            "【第一优先级 - 数据库条目名称】\n"
            "- 如果信息来自本项目数据库（herb、disease、chemical_component 等表），\n"
            "  必须使用数据库中的条目名称作为来源。\n"
            "- 格式：[数据库条目：xxx]\n"
            "- 示例：\n"
            "  - 金银花具有清热解毒功效[数据库条目：金银花]\n"
            "  - 绿原酸是金银花的主要化学成分[数据库条目：绿原酸]\n\n"
            "【第二优先级 - 知识图谱关系】\n"
            "- 如果信息来自 Herb-Disease 关系表（如 TREATS 关系），标注为：\n"
            "- 格式：[图谱关系：xxx -[TREATS]-> yyy]\n"
            "- 示例：\n"
            "  - 人参可用于治疗关节炎[图谱关系：人参 -[TREATS]-> 关节炎]\n\n"
            "【第三优先级 - 外部文献】\n"
            "- 仅当知识库和数据库都没有对应信息，使用训练数据补充时，才引用外部文献。\n"
            "- 格式：[文献：研究标题，期刊/作者，年份]\n\n"
            "【回答要求】\n"
            "- 用专业但易懂的中文回答\n"
            "- 每个论点后必须标注来源\n"
            "- 优先使用数据库条目名称作为来源\n"
            "- 在回答末尾添加「知识来源」部分，列出所有引用的条目\n"
            "- 如果知识库完全无法回答问题，请如实告知"
        )

        if context_chunks:
            knowledge_text = "\n\n---\n\n".join([
                f"【{c['title']}】(类型:{c.get('entity_type','未知')})\n{c['content'][:800]}"
                for c in context_chunks
            ])
            user_message = (
                "请严格根据以下【知识库内容】回答问题。这些内容来自本项目数据库。\n\n"
                "【知识库内容】：\n"
                f"{knowledge_text}\n\n"
                "用户问题：{query}\n\n"
                "【重要】请使用数据库条目名称作为来源标注，格式为[数据库条目：xxx]。"
            ).format(query=query)
        else:
            user_message = (
                "本项目知识库为空。请仅使用你的训练数据回答，并给出具体文献出处。\n\n"
                "用户问题：{query}"
            ).format(query=query)

        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        resp = QAService._call_api("/chat/completions", body)
        return {
            "answer": resp["choices"][0]["message"]["content"],
            "model": model,
            "usage": resp.get("usage", {}),
        }

    @staticmethod
    def qa_search(query, top_k=5, model="agnes-2.0-flash"):
        """RAG 问答流程：扩展检索 + LLM 生成"""
        # 使用扩展搜索，同时搜索所有数据库表
        chunks = KnowledgeService.search_chunks_extended(query, limit=top_k * 2)

        try:
            result = QAService.chat(query, chunks, model=model)
            return {
                "question": query,
                "answer": result["answer"],
                "context": [{"title": c["title"], "content": c["content"][:300], "entity_type": c["entity_type"]} for c in chunks],
                "model": result["model"],
                "usage": result.get("usage", {}),
                "source": "agnes-ai",
            }
        except Exception as e:
            if chunks:
                context_text = "\n".join([f"[{c['title']}]: {c['content'][:200]}" for c in chunks])
                fallback_answer = f"⚠️ LLM 调用失败（{str(e)}），以下为知识库检索结果：\n\n{context_text}"
            else:
                fallback_answer = f"⚠️ LLM 调用失败且未找到相关知识。错误: {str(e)}"
            return {
                "question": query,
                "answer": fallback_answer,
                "context": [{"title": c["title"], "content": c["content"][:300], "entity_type": c["entity_type"]} for c in chunks],
                "model": model,
                "source": "fallback",
            }

    @staticmethod
    def save_qa(question, answer, context_chunks=None, model_name=None):
        """保存问答记录"""
        conn = get_db()
        conn.execute("""
            INSERT INTO qa_record (question, answer, context_chunks, model_name) VALUES (?, ?, ?, ?)
        """, (question, answer, json.dumps(context_chunks or [], ensure_ascii=False), model_name))
        conn.commit()
        qa_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return qa_id

    @staticmethod
    def get_recent_qa(limit=20):
        """获取最近问答记录"""
        conn = get_db()
        rows = conn.execute("SELECT * FROM qa_record ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def rate_qa(qa_id, rating, feedback=None):
        """评价问答"""
        conn = get_db()
        conn.execute("UPDATE qa_record SET rating=?, feedback=? WHERE id=?", (rating, feedback, qa_id))
        conn.commit()
        conn.close()
