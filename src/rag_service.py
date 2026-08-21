"""
劳动法 RAG FastAPI 服务
供 Spring Boot 后端调用，独立运行
启动: python src/rag_service.py
端口: 8000
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 兼容 Windows 控制台（GBK）无法打印 emoji 的问题
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import json as _json

from src.config import Config
from src.database.neo4j_client import Neo4jClient
from src.rag.loader import LegalDocumentLoader
from src.rag.retriever import HybridRetriever
from src.rag.chain import LabourLawRAG, _source_from_doc
from src.rag.kg_api import router as kg_router
from src.rag import knowledge_api
from src.rag import diagnosis_api
from src.rag import version_api

# ── 初始化 ──
app = FastAPI(title="劳动法 RAG 引擎", version="1.0.0")
allowed_origins = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:8089,http://localhost:8080").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(kg_router)
app.include_router(knowledge_api.router)
app.include_router(diagnosis_api.router)
app.include_router(version_api.router)

print("🔌 连接 Neo4j ...")
neo4j = Neo4jClient()
if neo4j.check_connection():
    neo4j.init_schema()
else:
    print("Neo4j unavailable; graph retrieval will be disabled until it reconnects.")

print("📚 加载检索器 ...")
retriever = HybridRetriever(neo4j)
try:
    retriever.load_index()
    print("  ✅ 向量索引已加载")
except:
    loader = LegalDocumentLoader()
    docs = loader.load_all()
    if docs:
        retriever.build_index(docs)
        print(f"  ✅ 向量索引已构建，共 {len(docs)} 份文档")

rag = LabourLawRAG(retriever)
knowledge_api.set_rag(rag)
diagnosis_api.set_rag(rag)
print("✅ RAG 引擎就绪")


# ── 请求/响应模型 ──
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    history: List[dict] = Field(default_factory=list, description="对话历史 [{\"role\": \"user/assistant\", \"content\": \"...\"}]")
    top_k: int = Field(default=8, ge=1, le=Config.FINAL_TOP_K)
    mode: Optional[str] = Field(default=None, description="检索模式（消融演示）：full/bm25/vector/graph/bm25+vector/bm25+vector+kg/bm25+vector+kg+time")

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: Optional[str]) -> Optional[str]:
        from src.rag.retriever import RETRIEVAL_MODES
        if value and value not in RETRIEVAL_MODES:
            raise ValueError(f"未知检索模式: {value}")
        return value


class SourceItem(BaseModel):
    type: str
    title: str
    snippet: str
    status: str = ""
    article: str = ""
    law: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]


# ── API ──
@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """法律问答（含多轮对话记忆）。同步 def：LLM 阻塞调用由 FastAPI 线程池执行，不阻塞事件循环"""
    answer, docs = rag.query_with_documents(request.question, history=request.history, top_k=request.top_k, mode=request.mode)

    # 提取引用来源（含时效状态与条文号，供前端时效标记与修订对比）
    type_map = {
        "statute": "statute",
        "interpretation": "interpretation",
        "case": "case",
        "graph_article": "statute",
        "graph_case": "case",
    }
    sources = []
    for doc in docs[:5]:
        item = _source_from_doc(doc)
        item["type"] = type_map.get(item["type"], "unknown")
        sources.append(SourceItem(**item))

    return ChatResponse(answer=answer, sources=sources)


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    """流式法律问答（SSE，逐 token 推送）。同步 def：Starlette 在线程池中迭代同步生成器，不阻塞事件循环"""
    def generate():
        for token in rag.query_stream(request.question, history=request.history, top_k=request.top_k, mode=request.mode):
            if token.startswith('{"__'):
                # 控制消息：来源信息 / 检索过程明细，原样转发
                yield f"data: {token}\n\n"
            else:
                # 普通文本 token
                escaped = _json.dumps(token, ensure_ascii=False)
                yield f"data: {escaped}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",     # 禁用 nginx 缓冲
        }
    )


@app.get("/api/eval/ablation")
async def eval_ablation():
    """消融实验面板数据：读取 src/eval/ablation_results.json 并附测试题文本"""
    eval_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "eval")
    try:
        with open(os.path.join(eval_dir, "ablation_results.json"), "r", encoding="utf-8") as f:
            data = _json.load(f)
        questions = []
        try:
            with open(os.path.join(eval_dir, "test_questions.json"), "r", encoding="utf-8") as f:
                raw_questions = _json.load(f)
            questions = [
                {"id": q.get("id", f"Q{i+1:03d}"),
                 "question": q.get("question", ""),
                 "relevant_articles": q.get("relevant_articles", [])}
                for i, q in enumerate(raw_questions)
            ]
        except Exception:
            pass
        data["questions"] = questions
        return data
    except Exception:
        return {"configs": [], "per_question": {}, "questions": []}


# ── 问答测试集管理（管理员/研究人员维护 test_questions.json） ──

_EVAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "eval")
_TEST_QUESTIONS_PATH = os.path.join(_EVAL_DIR, "test_questions.json")


def _load_test_questions():
    try:
        with open(_TEST_QUESTIONS_PATH, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return []


def _save_test_questions(questions):
    tmp = _TEST_QUESTIONS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        _json.dump(questions, f, ensure_ascii=False, indent=4)
    os.replace(tmp, _TEST_QUESTIONS_PATH)


class TestQuestionIn(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    category: str = ""
    relevant_articles: List[str] = Field(default_factory=list)
    note: str = ""


@app.get("/api/eval/testset")
async def eval_testset():
    """问答测试集：全部题目（供管理员/研究人员管理）"""
    return _load_test_questions()


@app.post("/api/eval/testset")
async def eval_testset_add(item: TestQuestionIn):
    """新增测试题（id 自动顺延 Qxxx）"""
    questions = _load_test_questions()
    max_num = 0
    for q in questions:
        try:
            num = int(str(q.get("id", "")).lstrip("Q") or 0)
            max_num = max(max_num, num)
        except Exception:
            pass
    new_q = {
        "id": f"Q{max_num + 1:03d}",
        "category": item.category or "其他",
        "question": item.question.strip(),
        "relevant_articles": item.relevant_articles,
        "note": item.note,
    }
    questions.append(new_q)
    _save_test_questions(questions)
    return new_q


@app.delete("/api/eval/testset/{qid}")
async def eval_testset_delete(qid: str):
    """删除测试题"""
    questions = _load_test_questions()
    remaining = [q for q in questions if str(q.get("id", "")) != qid]
    if len(remaining) == len(questions):
        raise HTTPException(status_code=404, detail="题目不存在")
    _save_test_questions(remaining)
    return {"ok": True}


@app.get("/api/stats")
def stats():
    """知识库统计（同步 def：Neo4j 查询走线程池）"""
    return {
        "neo4j": neo4j.get_stats(),
        "vector_store": retriever.is_ready()
    }


@app.get("/health")
async def health():
    neo4j_ok = neo4j.check_connection()
    return {"status": "ok" if neo4j_ok and retriever.is_ready() else "degraded", "neo4j": neo4j_ok, "retriever": retriever.is_ready()}


if __name__ == "__main__":
    import uvicorn
    Config.validate()
    uvicorn.run(app, host="0.0.0.0", port=8001)
