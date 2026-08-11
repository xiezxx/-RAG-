# 劳动法律条文智能问答系统

> **融合知识图谱、时效感知与多策略检索增强的劳动法 RAG 系统**
>
> 三路混合检索（BM25 + FAISS 向量 + Neo4j 知识图谱）+ RRF 融合 + 时效过滤 + 流式 SSE 输出

---

## 架构总览

```
┌──────────────────────────────────────────────────────────────────┐
│                         Vue 3 前端 (8081)                         │
│  ChatView · KgView · HistoryView · Dashboard · 12 页面             │
│  Element Plus · ECharts · marked · Web Speech TTS/STT             │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP/SSE (JWT)
┌────────────────────────────▼─────────────────────────────────────┐
│                    Spring Boot 2.7 后端 (8089)                     │
│  JWT 认证 · RBAC 权限 · MyBatis 数据层 · 流式 SSE 代理              │
│  Statute/Case CRUD · 操作日志 · 问答记录 · 评估反馈                  │
└──────────┬──────────────────────────────────┬────────────────────┘
           │ RestTemplate                     │ JDBC/MyBatis
┌──────────▼──────────────────────┐  ┌───────▼──────────┐
│   Python FastAPI RAG (8001)     │  │   MySQL 8.x (3306) │
│  ┌───────────────────────────┐  │  │  users · cases    │
│  │    三路混合检索 + RRF 融合  │  │  │  statutes · chat  │
│  │  BM25 → FAISS → Neo4j KG  │  │  │  history          │
│  │  动态权重 · 查询改写 · 拒答  │  │  └──────────────────┘
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │  ┌──────────────────┐
│  │   DeepSeek API (云端 LLM)  │  │  │  Neo4j (7687)     │
│  │   LangChain · 流式 SSE     │  │  │  9 实体 · 8 关系   │
│  │   Prompt 证据约束          │  │  │  4 路径 KG 扩展   │
│  └───────────────────────────┘  │  └──────────────────┘
└────────────────────────────────┘
```

## 消融实验结果

> 50 道标注劳动法问题，5 组消融配置，测试日期 2026-08-11

| 配置 | R@1 | R@3 | R@5 | P@5 | MRR | 延迟 |
|------|-----|-----|-----|-----|-----|------|
| BM25 (基线) | 6.3% | 26.0% | 47.3% | 16.4% | 0.250 | 3ms |
| + 向量检索 | 14.7% | 45.0% | **61.0%** | 21.2% | 0.372 | 1222ms |
| + 知识图谱 | 14.7% | 45.0% | **61.0%** | 21.2% | 0.372 | 75ms |
| + 时效感知 | **25.7%** | **69.3%** | **89.3%** | **30.4%** | **0.519** | 89ms |
| **全模块** | **25.7%** | **69.3%** | **89.3%** | **30.4%** | **0.519** | 203ms |

### 关键发现

| 模块 | 增量贡献 |
|------|---------|
| 向量检索 (+BM25) | R@5 +13.7%↑, MRR +0.122, 语义理解补强关键词盲区 |
| 知识图谱扩展 | 延迟 **-93.9%**（1222→75ms），KG 扩展用更少候选集达到相同精度 |
| 时效感知 | R@1 +11%↑, R@5 **+28.3%**↑, MRR +0.147, **最大单模块提升** |

## 技术栈

| 层 | 技术 | 核心作用 |
|---|------|---------|
| **前端** | Vue 3 · Element Plus · ECharts · marked · Web Speech API | 12 页面 SPA，KG 力导向图，流式渲染，TTS 语音 |
| **业务后端** | Spring Boot 2.7 · MyBatis · MySQL · Redis · JWT | 认证/权限/CRUD/日志/SSE 代理 |
| **RAG 引擎** | Python FastAPI · LangChain · DeepSeek API | 三路检索 + RRF 融合 + Prompt 约束 |
| **向量检索** | FAISS IndexFlatIP · text2vec-base-chinese (384d) | 语义相似度检索 |
| **关键词检索** | rank-bm25 · Okapi BM25 · 中文 Bigram 分词 | 精确术语匹配 |
| **知识图谱** | Neo4j Community · 9 实体 · 8 关系 · 4 路径扩展 | 结构化关联推理 |
| **语音** | SpeechRecognition · SpeechSynthesis · 中文 TTS/STT | 语音输入 + 回答播报 |
| **LLM** | DeepSeek v4 · 流式 SSE · Prompt 证据约束 | 生成有据可查的回答 |

## 核心特性

### 🔍 三路混合检索 + RRF 融合
```
用户问题 → LLM 改写 → ┬─ BM25 关键词（精确匹配）
                       ├─ FAISS 向量（语义理解）
                       └─ Neo4j KG（关系推理）
                    → RRF 加权融合 → 时效过滤 → LLM 回答
```

### ⏱ 时效感知
- 自动提取问题中的时间信息（绝对日期 / 相对时间 / "最新""现行"偏好词）
- 法条标注 🟢现行有效 / 🟡已被修订 / 🔴已废止 / 🔵尚未生效
- 废止条文降权，优先推荐当前有效版本

### 📚 证据约束回答
- Prompt 层 6 条约束规则（有法可依、诚实边界、禁止臆造）
- 程序化门控：检索结果为空时直接拒答，不调用 LLM
- 回答同步展示：法律名称、条款编号、原文依据、效力状态
- 低可信度 / 高可信度区分显示

### 🗣 流式输出 + 语音交互
- SSE 全链路流式（LLM → FastAPI → Spring Boot → Vue）
- 逐 token 渲染，< 100ms 首字延迟
- 法小鹰语音助手：Web Speech STT 输入 + TTS 播报回答

### 📊 知识图谱
- 9 种实体：Statute · Article · Case · LegalConcept · RightObligation · IllegalAct · LegalLiability · Court · Issue
- 8 种关系：BELONGS_TO · CITES · DEFINES · PRESCRIBES · PROHIBITS · RESULTS_IN · INVOLVES · TRIED_AT
- ECharts 力导向图可视化，支持全部 / 法律概念 / 违法与责任 分类筛选

## 快速启动

### 前置条件
- Python 3.12 · JDK 17 · Node.js 16+ · MySQL 8.x · Neo4j 2026.x

### 四窗口启动

```bash
# 窗口 1: Neo4j
set JAVA_HOME=D:\jdk21
bin\neo4j console

# 窗口 2: Python RAG 引擎 (8001)
cd thesis-rag-labour-law
.venv\Scripts\python src\rag_service.py

# 窗口 3: Spring Boot (8089) — IDEA Run

# 窗口 4: Vue 前端 (8081)
cd vue-frontend
npm run serve
```

访问 `http://localhost:8081` · 默认账号 `admin/admin123`

## 项目结构

```
thesis-rag-labour-law/
├── src/                     # Python RAG 引擎
│   ├── rag_service.py       # FastAPI 入口
│   ├── rag/
│   │   ├── chain.py         # LangChain 问答链 + 流式
│   │   ├── retriever.py     # BM25 + 向量 + KG 混合检索 + RRF
│   │   ├── vector_store.py  # FAISS 索引
│   │   ├── timeliness.py    # 时效解析与过滤
│   │   ├── loader.py        # 文档加载与分块
│   │   ├── kg_api.py        # KG CRUD API
│   │   └── kg_builder.py    # KG 构建器（规则 + LLM）
│   ├── database/
│   │   └── neo4j_client.py  # Neo4j 客户端（4 路径扩展）
│   └── eval/
│       ├── ablation.py      # 消融实验框架
│       └── test_questions.json  # 50 道标注测试题
├── spring-boot-backend/     # Java 业务后端
│   └── src/main/java/com/labourlaw/
│       ├── controller/      # 7 个 REST 控制器
│       ├── service/         # 业务逻辑层
│       ├── mapper/          # MyBatis Mapper
│       ├── entity/          # 数据实体
│       ├── config/          # JWT/Redis/CORS 配置
│       └── dto/             # 数据传输对象
├── vue-frontend/            # Vue 3 前端
│   └── src/views/           # 12 个页面组件
├── vector_index/            # FAISS 索引文件
├── bm25_index/              # BM25 索引文件
└── requirements.txt         # Python 依赖
```

## 技术亮点

- **三路检索融合**：BM25 + FAISS + Neo4j KG → RRF 加权 → 时效过滤，非简单调 API
- **4 路径 KG 扩展**：实体往返 / 实体名反向 / 同部法律 / 法条互引，7/7 关系全部接入检索
- **全链路流式 SSE**：LLM → FastAPI → Spring Boot → Vue，绕过 LangChain 流式兼容问题直接用 OpenAI 原生 client
- **消融实验**：50 题 5 配置，量化 BM25 / 向量 / KG / 时效 每个模块的增量贡献
- **程序化门控**：检索空结果 / 证据不足时直接拒答，不依赖 LLM 自觉性
