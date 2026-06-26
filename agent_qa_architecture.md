# 基于 Agent 工作链的智能问答系统架构设计

本项目的智能问答系统采用 **Agent 工作链式架构**，将复杂的问答任务分解为多个专业化 Agent，通过流水线协作完成从问题分析到最终回答的全过程。系统核心文件为 `services/agent_qa.py`。

---

## 一、系统架构总览

```
                        智能问答系统架构

  用户问题 ---> [Step 1] Router Agent ---> 查询策略决策
                    |
                    v
           ┌──────────┬──────────┐
           v          v          │
    [Step 2]     [Step 3]        │   并行执行
    LocalDB      GraphDB         │
    Agent(本地)  Agent(云端)     │
           │          │         │
           └────┬─────┴─────────┘
                v
    [Step 4] Synthesizer Agent ---> 整合结果 ---> LLM 生成最终回答

                   数据源层 (双数据库架构)
   ┌──────────────────────┐  ┌─────────────────────────┐
   │  SQLite (本地)       │  │  Neo4j Aura Cloud       │
   │  - herb 药材表       │  │  - Herb 节点            │
   │  - disease 病症表    │  │  - Disease 节点         │
   │  - chemical_component│  │  - ChemicalComponent    │
   │  - herb_disease 关系 │  │  - Prescription 节点    │
   │  - prescription 方剂 │  │  - Pharmacology 节点    │
   │  - pharmacology 药理 │  │  - TREATS 关系          │
   │                      │  │  - DERIVED_FROM 关系    │
   │                      │  │  - CONTAINS_HERB 关系   │
   │                      │  │  - HAS_PHARMACOLOGY 关系│
   └──────────────────────┘  └─────────────────────────┘

                    LLM 接口层 (Agnes AI)
   - 调用 API: apihub.agnes-ai.com/v1/chat/completions
   - 模型: agnes-2.0-flash
   - API Key 轮询机制
```

---

## 二、四层 Agent 工作链详解

### Step 1: Router Agent（路由分析器）

**文件位置**: `services/agent_qa.py` 第 54-105 行

**职责**：分析用户问题，决定查询策略和数据源选择

**核心流程**：
1. **输入**：用户问题（如"金银花治疗什么病？"）
2. **LLM 调用**：发送问题到 Agnes AI，要求输出 JSON 格式的查询策略
3. **输出**：结构化路由结果，包含：
   - `query_type`: 查询类型（herb_info / disease_info / relationship / component_info / general）
   - `need_local_db`: 是否需要查询本地数据库
   - `need_graph_db`: 是否需要查询云端图数据库
   - `key_entities`: 提取的关键实体列表
   - `local_query`: 本地查询关键词
   - `graph_query`: 图查询关键词

**设计意图**：通过 LLM 的语义理解能力，自动识别问题类型和关键实体，实现**智能路由**。

---

### Step 2: LocalDB Agent（本地数据库查询器）

**文件位置**: `services/agent_qa.py` 第 107-210 行

**职责**：查询本地 SQLite 数据库，获取属性型信息

**查询范围**：

| 数据表 | 查询内容 | 主键 |
|--------|----------|------|
| herb | 药材名称、拉丁名、分类、性味归经 | tcmbank_id |
| disease | 病症名称、分类、中医证型、描述 | cloud_id |
| chemical_component | 成分名称、分子式、CAS号、生物活性 | cloud_id |
| herb_disease | 药材-病症治疗关系（TREATS） | 联合主键 |

**设计意图**：本地数据库存储**结构化属性数据**，适合回答"药材的性味是什么"这类属性型问题。

---

### Step 3: GraphDB Agent（云端图谱查询器）

**文件位置**: `services/agent_qa.py` 第 212-280 行

**职责**：查询云端 Neo4j 图数据库，获取关系型信息

**查询范围**：

| 查询类型 | Cypher 查询 | 返回内容 |
|----------|-------------|----------|
| TREATS | `MATCH (h:Herb)-[r:TREATS]->(d:Disease)` | 药材-病症治疗关系 |
| FOUND_IN | `MATCH (ing:Ingredient)-[r:FOUND_IN]->(h:Herb)` | 成分-药材包含关系 |
| Herb 属性 | `MATCH (h:Herb) WHERE h.name = $entity` | 药材详细属性 |

**设计意图**：图数据库存储**关系型数据**，适合回答"金银花治疗什么病"、"人参含有什么成分"这类关系型问题。

---

### Step 4: Synthesizer Agent（汇总生成器）

**文件位置**: `services/agent_qa.py` 第 282-431 行

**职责**：整合所有查询结果，生成最终回答

**核心流程**：
1. **格式化为上下文**：将 LocalDB 和 GraphDB 的查询结果格式化为结构化文本
2. **构建提示词**：生成包含数据源优先级规则的详细提示词
3. **LLM 生成**：调用 Agnes AI 生成最终回答

**数据源优先级规则**（关键设计）：

| 优先级 | 数据源 | 适用场景 | 标注格式 |
|--------|--------|----------|----------|
| 1 | 云端图谱 | 关系型问题（A治疗B、A含有B） | `[云端图谱: xxx]` |
| 2 | 本地数据库 | 属性型问题（性味归经、描述） | `[本地数据库: xxx]` |
| 3 | AI 训练数据 | 仅当数据库无信息时 | `[AI补充]` |

**回答格式**：
- 一、直接回答（2-3 句话）
- 二、详细信息（分点说明 + 来源标注）
- 三、知识来源（列出所有引用的数据源）
- 四、补充说明（仅当数据库无信息时）

**设计意图**：确保回答**有据可查**，禁止编造信息，每条数据都标注来源。

---

## 三、辅助服务层

### KnowledgeService（RAG 知识块管理）

**文件位置**: `services/knowledge_service.py` 第 36-384 行

**职责**：管理 RAG 知识块，支持全文搜索和扩展搜索

**核心功能**：
- `add_chunk()`: 添加知识块
- `add_entity_chunks()`: 对实体描述进行分块存储
- `search_chunks_extended()`: 扩展搜索（覆盖所有数据库表 + Neo4j 图谱）
- `rebuild_all_entity_chunks()`: 重建所有实体的知识块

**扩展搜索范围**（7 个数据源）：
1. knowledge_chunk 表（基础搜索）
2. herb 表
3. disease 表
4. chemical_component 表
5. herb_disease 关系表
6. prescription 表
7. Neo4j 云端图谱

---

### QAService（Agnes AI 问答服务）

**文件位置**: `services/knowledge_service.py` 第 468-624 行

**职责**：封装 Agnes AI API 调用，支持模型切换和问答流程

**核心功能**：
- `_call_api()`: 调用 Agnes AI API（带 API Key 轮询）
- `chat()`: 调用 LLM 进行问答（带上下文注入）
- `qa_search()`: RAG 问答流程（检索 + 生成）
- `save_qa()`: 保存问答记录
- `rate_qa()`: 用户评价问答

**API 配置**：
- 基础 URL: `https://apihub.agnes-ai.com/v1`
- 支持模型: agnes-1.5-flash, agnes-2.0-flash
- API Key 轮询: 支持多个 Key 自动切换

---

### GraphService（图谱查询服务）

**文件位置**: `services/knowledge_service.py` 第 387-465 行

**职责**：SQLite 层面的图谱查询（作为 Neo4j 的 fallback）

**核心功能**：
- `query_entity_graph()`: 查询实体为中心的子图
- `get_statistics()`: 获取图谱统计信息

---

## 四、主流程入口

**文件位置**: `services/agent_qa.py` 第 433-472 行

```python
AgentQA.chat(query, model="agnes-2.0-flash")
```

**执行流程**：
```
Step 1/4: 路由分析      -> route_query()
Step 2/4: 查询本地数据库 -> query_local_db()
Step 3/4: 查询云端图谱  -> query_graph_db()
Step 4/4: 生成最终回答  -> synthesize_answer()
```

**返回结果**：
```python
{
    "question": "金银花治疗什么病？",
    "answer": "...",
    "model": "agnes-2.0-flash",
    "source": "agent_chain_v4",
    "route": {...},
    "local_results_count": 5,
    "graph_results_count": 10,
    "elapsed_seconds": 8.52
}
```

---

## 五、关键设计特点

| 设计特点 | 实现方式 | 优势 |
|----------|----------|------|
| **数据库优先** | 所有回答必须基于数据库，禁止编造 | 保证信息准确性和可追溯性 |
| **数据源标注** | 每条信息标注来源（本地/云端/AI补充） | 用户可验证信息可信度 |
| **双数据库架构** | SQLite 存属性，Neo4j 存关系 | 各司其职，查询效率高 |
| **并行查询** | LocalDB 和 GraphDB 可并行执行 | 减少总响应时间 |
| **实时事件通知** | `_emit_event()` 回调机制 | 前端可实时显示查询进度 |
| **API Key 轮询** | 多 Key 自动切换 | 避免单 Key 限流 |
| **线程安全** | `_api_lock` 互斥锁 | 防止并发调用冲突 |

---

## 六、数据流示例

**用户问题**："金银花治疗什么病？"

```
1. Router Agent 分析：
   - query_type: relationship
   - key_entities: ["金银花"]
   - need_local_db: True (获取属性)
   - need_graph_db: True (获取关系)

2. LocalDB Agent 查询：
   - 药材表: 金银花 -> 性微寒、味甘、归肺心胃经

3. GraphDB Agent 查询：
   - TREATS 关系: 金银花 -> 风热感冒、咽喉肿痛、痈肿疮疡

4. Synthesizer Agent 生成回答：
   - 优先使用云端图谱的关系数据
   - 标注来源: [云端图谱: 金银花 -[TREATS]-> 风热感冒]
```

---

## 七、文件结构

```
.
├── services/
│   ├── agent_qa.py          # Agent 工作链式问答系统（核心）
│   ├── knowledge_service.py # RAG 知识块 + Agnes AI 问答服务
│   └── neo4j_service.py     # Neo4j 图数据库服务
├── database.py              # SQLite 数据库初始化与连接
├── server.py                # HTTP 服务器与 API 接口
└── agent_qa_architecture.md # 本文档
```

---

**文档版本**: v1.0
**生成时间**: 2026-06-17
**基于代码**: 中医药科学大数据管理平台 v2.0
