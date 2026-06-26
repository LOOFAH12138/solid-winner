# 中医药科学大数据管理平台 v2.0

基于双数据库架构（SQLite + Neo4j）的中医药知识管理与智能问答系统，集成 **Agent 工作链式 LLM 问答**，支持药材、方剂、药理、化学成分、病症的图谱化查询与 RAG 增强检索。

## 系统架构

```
用户问题 → Router Agent(路由) ──→ LocalDB Agent(本地SQLite) ──→ Synthesizer → 回答
                           └──→ GraphDB Agent(云端Neo4j) ──┘        ↑
                                                                 Agnes AI
数据源层:
  SQLite(本地)          Neo4j Aura Cloud(云端图谱)
  - herb               - Herb / Disease
  - prescription       - Prescription / Pharmacology
  - pharmacology       - ChemicalComponent
  - chemical_component  - TREATS / DERIVED_FROM
  - disease            - CONTAINS_HERB / HAS_PHARMACOLOGY
```

## 技术栈

- **后端**: Python 标准库 HTTP Server（零外部依赖）
- **数据库**: SQLite（属性数据）+ Neo4j Aura Cloud（图谱关系）
- **LLM**: Agnes AI (`agnes-2.0-flash`)，API Key 轮询机制
- **前端**: 原生 HTML/CSS/JS SPA

## 快速启动

```bash
# 1. 安装依赖（可选，核心功能无需外部包）
pip install -r requirements.txt

# 2. 初始化数据库并启动服务
python server.py

# 3. 打开浏览器访问
# http://127.0.0.1:5000
```

Windows 用户也可双击 `启动平台.bat` 一键启动。

## 数据导入

```bash
# 从 CSV 导入数据到 SQLite
python import_csv_to_sqlite.py

# 同步 SQLite 到 Neo4j（需先配置 Neo4j 连接）
# 调用 POST /api/neo4j/sync
```

CSV 数据文件位于 `neo4j_import/` 目录（已加入 `.gitignore`）。

## API 接口

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/herbs` | GET | 药材列表（分页/搜索） |
| `/api/herbs/{id}` | GET/PUT/DELETE | 药材 CRUD |
| `/api/diseases` | GET/POST | 病症列表 |
| `/api/prescriptions` | GET | 方剂列表 |
| `/api/pharmacology` | GET | 药理学列表 |
| `/api/components` | GET/POST/PUT/DELETE | 化学成分 CRUD |
| `/api/graph/query` | GET | 图谱子图查询（`entity_type`, `entity_id`） |
| `/api/graph/stats` | GET | 图谱统计信息 |
| `/api/neo4j/sync` | POST | 同步数据到 Neo4j |
| `/api/neo4j/health` | GET | Neo4j 连接检查 |
| `/api/knowledge/search` | GET | 知识库全文搜索 |
| `/api/knowledge/rebuild` | POST | 重建知识块 |
| `/api/qa/search` | POST | RAG 问答（`question`） |
| `/api/qa/models` | GET | 可用 LLM 模型列表 |
| `/api/qa/history` | GET | 问答历史记录 |
| `/api/qa/rate` | POST | 评价问答结果 |
| `/api/import/preview` | POST | CSV 导入预览 |
| `/api/import/confirm` | POST | 确认导入 |

## 项目结构

```
.
├── server.py                  # HTTP 服务器与 API 接口（核心入口）
├── database.py                # SQLite 数据库初始化与连接
├── import_csv_to_sqlite.py    # CSV 数据导入到 SQLite
├── services/
│   ├── agent_qa.py            # Agent 工作链式问答系统
│   ├── knowledge_service.py   # RAG 知识块 + Agnes AI 问答 + GraphService
│   ├── neo4j_service.py       # Neo4j 图数据库同步与查询
│   ├── herb_service.py        # 药材数据服务
│   ├── component_service.py   # 化学成分数据服务
│   └── import_service.py      # 数据导入服务
├── routes/                    # 模块化路由处理器
├── static/                    # 前端静态资源 (CSS/JS)
│   ├── css/style.css
│   └── js/*.js
├── templates/
│   └── index.html             # 前端入口页面
├── test_queries.py            # 端到端查询验证脚本
├── agent_qa_architecture.md   # Agent 问答系统架构文档
└── requirements.txt
```

## 核心功能

### 1. Agent 工作链式问答
- **Router Agent**: LLM 驱动的智能路由，自动识别问题类型与关键实体
- **LocalDB Agent**: 查询本地 SQLite，获取属性数据（药性、归经、功效等）
- **GraphDB Agent**: 查询云端 Neo4j 图谱，获取关系数据（TREATS、DERIVED_FROM 等）
- **Synthesizer Agent**: 整合双数据库结果，生成最终回答

### 2. RAG 增强检索（7 数据源扩展搜索）
同步检索：知识块表、herb、disease、prescription、pharmacology、chemical_component、Neo4j 图谱

### 3. 知识图谱可视化
实体中心的图谱子图查询，前端 D3.js 可视化渲染

### 4. 双数据库架构
- SQLite: 快速本地查询，属性数据存储
- Neo4j: 云端图谱，关系推理与可视化

## 验证测试

```bash
python test_queries.py
```

覆盖 SQLite 查询、Neo4j 图谱、KnowledgeService 搜索、AgentQA 工作链全部路径。

## 数据规模

| 实体 | 数量 |
|------|------|
| 药材 (Herb) | 9,191 |
| 病症 (Disease) | 32,529 |
| 化学成分 (ChemicalComponent) | 61,965 |
| 方剂 (Prescription) | 84,294 |
| 药理学 (Pharmacology) | 920 |
| 关系 (Edges) | 337,813+ |

## License

MIT
