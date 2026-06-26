# -*- coding: utf-8 -*-
"""Agent 工作链式 QA 系统 v4 - 数据库优先 + 实时显示 + 流式输出"""
import json
import time
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.knowledge_service import QAService, AGNES_BASE_URL
from database import get_db
from services.neo4j_service import _run_query_stream, _run_query, _get_prop, _extract_node_props, _extract_rel_props


class AgentQA:
    """Agent 工作链式问答系统 v4 - 数据库优先 + 实时显示 + 流式输出"""
    
    # 线程锁保护 API 调用，避免并发
    _api_lock = threading.Lock()
    
    # 实时事件回调
    _event_callbacks = []
    
    @staticmethod
    def on_event(callback):
        """注册事件回调"""
        AgentQA._event_callbacks.append(callback)
    
    @staticmethod
    def _emit_event(event_type, data):
        """发送事件"""
        for callback in AgentQA._event_callbacks:
            try:
                callback(event_type, data)
            except Exception:
                pass
    
    @staticmethod
    def _call_llm(messages, model="agnes-2.0-flash", max_tokens=3000, timeout=60):
        """调用 LLM API（带锁保护）"""
        with AgentQA._api_lock:
            body = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": max_tokens,
            }
            return QAService._call_api("/chat/completions", body)
    
    # ========== Step 1: Router Agent ==========
    @staticmethod
    def route_query(query):
        """路由 Agent：分析问题，决定查询策略"""
        AgentQA._emit_event("status", {"agent": "router", "status": "running", "message": "正在分析问题..."})
        
        router_prompt = f"""分析用户问题，判断需要查询哪些数据源。

用户问题：{query}

可选数据源：
- local_db: 本地 SQLite 数据库（herb 药材、chemical_component 化学成分、disease 病症、herb_disease 关系）
- graph_db: 云端 Neo4j 图数据库（药材-病症关系、药材-成分关系）
- general: 通用中医药知识（AI 训练数据）

请严格按 JSON 格式输出：
{{
  "query_type": "herb_info|disease_info|relationship|component_info|general",
  "need_local_db": true,
  "need_graph_db": false,
  "need_general": false,
  "key_entities": ["实体1", "实体2"],
  "local_query": "本地查询关键词",
  "graph_query": "图查询关键词"
}}"""
        
        messages = [
            {"role": "system", "content": "你是专业的中医药查询路由器。只输出 JSON，不要输出其他内容。"},
            {"role": "user", "content": router_prompt},
        ]
        
        try:
            resp = AgentQA._call_llm(messages, max_tokens=500)
            answer = resp["choices"][0]["message"]["content"]
            start = answer.find("{")
            end = answer.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(answer[start:end])
                AgentQA._emit_event("status", {"agent": "router", "status": "complete", "message": "分析完成"})
                return result
        except Exception as e:
            print(f"    [Router 错误] {e}")
        
        # 默认策略
        return {
            "query_type": "general",
            "need_local_db": True,
            "need_graph_db": False,
            "need_general": True,
            "key_entities": [],
            "local_query": query,
            "graph_query": query,
        }
    
    # ========== Step 2: LocalDB Agent ==========
    @staticmethod
    def query_local_db(entities, query):
        """本地数据库查询 Agent - 使用正确的字段名"""
        AgentQA._emit_event("status", {"agent": "localdb", "status": "running", "message": "正在查询本地数据库..."})
        results = {"herbs": [], "diseases": [], "components": [], "relations": []}
        
        conn = get_db()
        
        # 构建搜索关键词
        search_terms = list(set(entities))[:3]
        if not search_terms:
            search_terms = [query]
        
        for entity in search_terms:
            # 搜索 herbs - 使用 tcmbank_id 作为主键
            rows = conn.execute(
                "SELECT tcmbank_id, name, latin_name, category, nature, taste, meridian, pinyin_name, tcm_name_en "
                "FROM herb WHERE name LIKE ? OR pinyin_name LIKE ? OR tcm_name_en LIKE ? LIMIT 5",
                (f"%{entity}%", f"%{entity}%", f"%{entity}%")
            ).fetchall()
            for r in rows:
                r_dict = dict(r)
                # 格式化详细信息
                detail_parts = []
                if r_dict.get('nature'):
                    detail_parts.append(f"性{r_dict['nature']}")
                if r_dict.get('taste'):
                    detail_parts.append(f"味{r_dict['taste']}")
                if r_dict.get('meridian'):
                    detail_parts.append(f"归{r_dict['meridian']}经")
                if r_dict.get('category'):
                    detail_parts.append(f"分类：{r_dict['category']}")
                r_dict['detail'] = '、'.join(detail_parts) if detail_parts else '无详细信息'
                results["herbs"].append(r_dict)
            
            # 搜索 diseases - 使用 cloud_id 作为主键
            rows = conn.execute(
                "SELECT cloud_id, name, category, description, tcm_syndrome "
                "FROM disease WHERE name LIKE ? OR description LIKE ? LIMIT 5",
                (f"%{entity}%", f"%{entity}%")
            ).fetchall()
            for r in rows:
                r_dict = dict(r)
                detail_parts = []
                if r_dict.get('category'):
                    detail_parts.append(f"分类：{r_dict['category']}")
                if r_dict.get('tcm_syndrome'):
                    detail_parts.append(f"中医证型：{r_dict['tcm_syndrome']}")
                if r_dict.get('description'):
                    detail_parts.append(r_dict['description'][:100])
                r_dict['detail'] = '、'.join(detail_parts) if detail_parts else '无详细信息'
                results["diseases"].append(r_dict)
            
            # 搜索 components - 使用 cloud_id 作为主键
            rows = conn.execute(
                "SELECT cloud_id, name, formula, cas_number, bioactivity, herb_id "
                "FROM chemical_component WHERE name LIKE ? LIMIT 5",
                (f"%{entity}%",)
            ).fetchall()
            for r in rows:
                r_dict = dict(r)
                detail_parts = []
                if r_dict.get('formula'):
                    detail_parts.append(f"分子式：{r_dict['formula']}")
                if r_dict.get('bioactivity'):
                    detail_parts.append(f"活性：{r_dict['bioactivity'][:100]}")
                if r_dict.get('herb_id'):
                    herb_row = conn.execute("SELECT name FROM herb WHERE tcmbank_id=?", (r_dict['herb_id'],)).fetchone()
                    if herb_row:
                        detail_parts.append(f"来源：{herb_row['name']}")
                r_dict['detail'] = '、'.join(detail_parts) if detail_parts else '无详细信息'
                results["components"].append(r_dict)
        
        # 搜索 herb-disease 关系
        for entity in search_terms[:2]:
            rows = conn.execute("""
                SELECT hd.id, h.name as herb_name, d.name as disease_name, hd.indication
                FROM herb_disease hd
                JOIN herb h ON hd.herb_tcmbank_id = h.tcmbank_id
                JOIN disease d ON hd.disease_cloud_id = d.cloud_id
                WHERE h.name LIKE ? OR d.name LIKE ?
                LIMIT 20
            """, (f"%{entity}%", f"%{entity}%")).fetchall()
            for r in rows:
                results["relations"].append({
                    "type": "TREATS",
                    "herb": r['herb_name'],
                    "disease": r['disease_name'],
                    "indication": r['indication']
                })
        
        # 去重
        for key in results:
            if key == "relations":
                results[key] = results[key][:20]
            else:
                results[key] = list({r.get('name') or r.get('herb_name') or r.get('disease_name'): r 
                                     for r in results[key]}.values())[:5]
        
        conn.close()
        AgentQA._emit_event("status", {"agent": "localdb", "status": "complete", "message": f"查询完成（{sum(len(v) for v in results.values())}条结果）"})
        
        return results
    
    # ========== Step 3: GraphDB Agent - 使用标准属性名 ==========
    @staticmethod
    def query_graph_db(entities):
        """云端图数据库查询 Agent - 使用标准 Neo4j 属性名（sync 后无 CSV 格式残留）"""
        AgentQA._emit_event("status", {"agent": "graphdb", "status": "running", "message": "正在查询云端图谱..."})
        results = {"treats": [], "contains": [], "herb_properties": []}
        
        try:
            for entity in entities[:3]:
                # 查询 TREATS 关系 - 使用标准属性名
                try:
                    records = _run_query(
                        "MATCH (h:Herb)-[r:TREATS]->(d:Disease) "
                        "WHERE h.name = $entity OR d.name = $entity "
                        "RETURN h, r, d LIMIT 50",
                        {"entity": entity}
                    )
                    for rec in records:
                        h_props = _extract_node_props(rec["h"])
                        d_props = _extract_node_props(rec["d"])
                        results["treats"].append({
                            "herb": h_props.get("name", ""),
                            "disease": d_props.get("name", ""),
                        })
                    AgentQA._emit_event("status", {"agent": "graphdb", "status": "running", "message": f"TREATS查询到{len(results['treats'])}条关系"})
                except Exception as e:
                    AgentQA._emit_event("status", {"agent": "graphdb", "status": "error", "message": f"TREATS查询失败: {str(e)[:50]}"})
                
                # 查询 DERIVED_FROM 关系 (ChemicalComponent -> Herb，替代旧的 FOUND_IN)
                try:
                    records = _run_query(
                        "MATCH (ing:ChemicalComponent)-[r:DERIVED_FROM]->(h:Herb) "
                        "WHERE ing.name = $entity OR h.name = $entity "
                        "RETURN ing, r, h LIMIT 50",
                        {"entity": entity}
                    )
                    for rec in records:
                        ing_props = _extract_node_props(rec["ing"])
                        h_props = _extract_node_props(rec["h"])
                        results["contains"].append({
                            "ingredient": ing_props.get("name", ""),
                            "herb": h_props.get("name", ""),
                        })
                    AgentQA._emit_event("status", {"agent": "graphdb", "status": "running", "message": f"DERIVED_FROM查询到{len(results['contains'])}条关系"})
                except Exception as e:
                    AgentQA._emit_event("status", {"agent": "graphdb", "status": "error", "message": f"DERIVED_FROM查询失败: {str(e)[:50]}"})
                
                # 查询 Herb 属性
                try:
                    records = _run_query(
                        "MATCH (h:Herb) WHERE h.name = $entity RETURN h LIMIT 10",
                        {"entity": entity}
                    )
                    for rec in records:
                        h_props = _extract_node_props(rec["h"])
                        results["herb_properties"].append({
                            "name": h_props.get("name", ""),
                            "nature": h_props.get("nature", ""),
                            "taste": h_props.get("taste", ""),
                            "meridian": h_props.get("meridian", ""),
                        })
                except Exception as e:
                    AgentQA._emit_event("status", {"agent": "graphdb", "status": "error", "message": f"Herb属性查询失败: {str(e)[:50]}"})
        except Exception as e:
            AgentQA._emit_event("status", {"agent": "graphdb", "status": "error", "message": f"图谱查询失败: {str(e)[:50]}"})
        
        AgentQA._emit_event("status", {"agent": "graphdb", "status": "complete", "message": f"查询完成（共{sum(len(v) for v in results.values())}条结果）"})
        
        return results
    
    # ========== Step 4: Synthesizer Agent ==========
    @staticmethod
    def synthesize_answer(query, route_result, local_results, graph_results):
        """汇总 Agent：整合所有查询结果，生成最终回答 - 强化数据库优先"""
        AgentQA._emit_event("status", {"agent": "synthesizer", "status": "running", "message": "正在生成回答..."})
        
        # 格式化本地数据库结果 - 更详细
        local_text = ""
        if local_results["herbs"]:
            local_text += "\n【📦 本地数据库 - 药材信息】\n"
            for herb in local_results["herbs"][:5]:
                local_text += f"\n• 【{herb['name']}】\n"
                local_text += f"  编码: {herb.get('tcmbank_id', 'N/A')}\n"
                if herb.get('latin_name'):
                    local_text += f"  拉丁名: {herb['latin_name']}\n"
                if herb.get('category'):
                    local_text += f"  分类: {herb['category']}\n"
                if herb.get('nature') or herb.get('taste') or herb.get('meridian'):
                    attrs = []
                    if herb.get('nature'):
                        attrs.append(f"性{herb['nature']}")
                    if herb.get('taste'):
                        attrs.append(f"味{herb['taste']}")
                    if herb.get('meridian'):
                        attrs.append(f"归{herb['meridian']}经")
                    local_text += f"  性味归经: {'、'.join(attrs)}\n"
                if herb.get('detail') and herb['detail'] != '无详细信息':
                    local_text += f"  备注: {herb['detail']}\n"
        
        if local_results["diseases"]:
            local_text += "\n【📦 本地数据库 - 病症信息】\n"
            for disease in local_results["diseases"][:5]:
                local_text += f"\n• 【{disease['name']}】\n"
                local_text += f"  编码: {disease.get('cloud_id', 'N/A')}\n"
                if disease.get('category'):
                    local_text += f"  分类: {disease['category']}\n"
                if disease.get('tcm_syndrome'):
                    local_text += f"  中医证型: {disease['tcm_syndrome']}\n"
                if disease.get('description'):
                    local_text += f"  描述: {disease['description'][:150]}\n"
        
        if local_results["components"]:
            local_text += "\n【📦 本地数据库 - 化学成分】\n"
            for comp in local_results["components"][:5]:
                local_text += f"\n• 【{comp['name']}】\n"
                local_text += f"  编码: {comp.get('cloud_id', 'N/A')}\n"
                if comp.get('formula'):
                    local_text += f"  分子式: {comp['formula']}\n"
                if comp.get('cas_number'):
                    local_text += f"  CAS号: {comp['cas_number']}\n"
                if comp.get('bioactivity'):
                    local_text += f"  生物活性: {comp['bioactivity'][:100]}\n"
                if comp.get('herb_id'):
                    local_text += f"  关联药材ID: {comp['herb_id']}\n"
        
        if local_results["relations"]:
            local_text += "\n【📦 本地数据库 - 疗效关系】\n"
            for rel in local_results["relations"][:10]:
                local_text += f"• {rel['herb']} → {rel['disease']}"
                if rel.get('indication'):
                    local_text += f" (适应症: {rel['indication'][:50]})"
                local_text += "\n"
        
        # 格式化图数据库结果
        graph_text = ""
        if graph_results["treats"]:
            graph_text += "\n【🌐 云端图谱 - 疗效关系】\n"
            for treat in graph_results["treats"][:10]:
                graph_text += f"• {treat['herb']} → {treat['disease']}\n"
        
        if graph_results["contains"]:
            graph_text += "\n【🌐 云端图谱 - 成分关系】\n"
            for contains in graph_results["contains"][:10]:
                graph_text += f"• {contains['ingredient']} ⊂ {contains['herb']}\n"
        
        if graph_results["herb_properties"]:
            graph_text += "\n【🌐 云端图谱 - 药材属性】\n"
            for herb in graph_results["herb_properties"][:5]:
                graph_text += f"• {herb['name']}: 性{herb.get('nature','')}, 味{herb.get('taste','')}\n"
        
        # 构建强调数据库优先的提示词
        synthesizer_prompt = f"""你是一位专业的中医药学专家助手。请根据以下【数据库查询结果】回答用户问题。

## ⚠️ 核心原则（必须严格遵守）

1. **【数据源优先级】** 回答时必须严格按照以下优先级使用数据：
   - **第一优先级：云端知识图谱** - 关系型问题（如"A治疗B"、"A含有B"）必须优先使用云端图谱数据，因为图谱专门存储关系信息
   - **第二优先级：本地数据库** - 属性型问题（如药材的性味归经、病症的描述、成分的分子式）使用本地数据库
   - **第三优先级：AI 训练数据** - 仅当两个数据库都无相关信息时才使用，且必须明确标注

2. **【禁止编造】** 如果数据库中没有任何相关信息，明确告知用户"数据库中未找到相关信息"，不要编造

3. **【来源标注】** 每条信息必须标注来源，格式如下：
   - 来自云端图谱：[云端图谱: 药材A -[关系名]-> 药材B/病症/成分]
   - 来自本地数据库：[本地数据库: 药材名/病症名/成分名]
   - 仅当数据库无信息时：[AI补充]

## 用户问题
{query}

## 查询策略
- 查询类型: {route_result.get('query_type', 'general')}
- 关键实体: {', '.join(route_result.get('key_entities', []))}

## 📦 本地数据库查询结果（属性型信息）
{local_text if local_text else "（无结果 - 本地数据库中未找到相关信息）"}

## 🌐 云端图谱查询结果（关系型信息）
{graph_text if graph_text else "（无结果 - 云端图谱中未找到相关信息）"}

## 回答格式要求

请按以下格式组织回答：

### 一、直接回答
用 2-3 句话直接回答用户问题，**关系型问题优先引用云端图谱**，属性型问题引用本地数据库

### 二、详细信息
分点详细说明，每点后标注来源：
- 如果是关系（如疗效、成分归属），优先使用云端图谱：[云端图谱: xxx]
- 如果是属性（如性味、归经、分类），使用本地数据库：[本地数据库: xxx]

### 三、知识来源
列出所有引用的数据源：
- [云端图谱] 关系1、关系2...
- [本地数据库] 条目1、条目2...

### 四、补充说明（可选）
仅当两个数据库都无信息时，可用 AI 训练数据补充，并明确标注"AI补充"

## 重要提醒
- **关系型问题**（如"金银花治疗什么"、"人参含有什么成分"）：云端图谱权重更高，必须优先使用
- **属性型问题**（如"金银花的性味是什么"）：本地数据库更准确，优先使用
- 如果两个数据库都无结果，请直接回答："数据库中暂未找到关于'{query}'的相关信息。"
- 不要编造任何数据库中没有的信息
- 每条信息必须标注来源"""
        
        messages = [
            {"role": "system", "content": "你是专业的中医药学专家助手，必须严格基于数据库信息回答。"},
            {"role": "user", "content": synthesizer_prompt},
        ]
        
        try:
            resp = AgentQA._call_llm(messages, max_tokens=4000)
            AgentQA._emit_event("status", {"agent": "synthesizer", "status": "complete", "message": "回答生成完成"})
            return resp["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  [Synthesizer 错误] {e}")
            AgentQA._emit_event("status", {"agent": "synthesizer", "status": "error", "message": f"生成失败: {str(e)}"})
            return f"回答生成失败: {str(e)}"
    
    # ========== 主流程 ==========
    @staticmethod
    def chat(query, model="agnes-2.0-flash"):
        """Agent 工作链式问答主流程"""
        print("\n" + "=" * 70)
        print(f"📝 用户问题: {query}")
        print("=" * 70)
        
        start_time = time.time()
        
        # Step 1: 路由
        print("\n[Step 1/4] 🔀 路由分析...")
        AgentQA._emit_event("progress", {"current": 1, "total": 4, "step": "routing"})
        route_result = AgentQA.route_query(query)
        
        # Step 2 & 3: 并行查询 LocalDB 和 GraphDB
        print("\n[Step 2/4] 🗄️  查询本地数据库...")
        AgentQA._emit_event("progress", {"current": 2, "total": 4, "step": "querying"})
        local_results = AgentQA.query_local_db(route_result.get("key_entities", []), query)
        
        print("\n[Step 3/4] 🌐 查询云端图数据库...")
        graph_results = AgentQA.query_graph_db(route_result.get("key_entities", []))
        
        # Step 4: 汇总
        print("\n[Step 4/4] ✍️  生成最终回答...")
        AgentQA._emit_event("progress", {"current": 3, "total": 4, "step": "synthesizing"})
        answer = AgentQA.synthesize_answer(query, route_result, local_results, graph_results)
        
        elapsed = time.time() - start_time
        
        return {
            "question": query,
            "answer": answer,
            "model": model,
            "source": "agent_chain_v4",
            "route": route_result,
            "local_results_count": sum(len(v) for v in local_results.values()),
            "graph_results_count": sum(len(v) for v in graph_results.values()),
            "elapsed_seconds": round(elapsed, 2),
        }
