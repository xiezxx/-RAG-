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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import json as _json

from src.config import Config
from src.database.neo4j_client import Neo4jClient
from src.rag.loader import LegalDocumentLoader
from src.rag.retriever import HybridRetriever
from src.rag.chain import LabourLawRAG
from src.rag.kg_api import router as kg_router

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
print("✅ RAG 引擎就绪")


# ── 请求/响应模型 ──
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    history: List[dict] = Field(default_factory=list, description="对话历史 [{\"role\": \"user/assistant\", \"content\": \"...\"}]")
    top_k: int = Field(default=8, ge=1, le=Config.FINAL_TOP_K)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class SourceItem(BaseModel):
    type: str
    title: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]


# ── API ──
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """法律问答（含多轮对话记忆）"""
    answer, docs = rag.query_with_documents(request.question, history=request.history, top_k=request.top_k)

    # 提取引用来源
    sources = []
    for doc in docs[:5]:
        doc_type = doc.metadata.get("doc_type", "unknown")
        type_map = {
            "statute": "statute",
            "interpretation": "interpretation",
            "case": "case",
            "graph_article": "statute",
            "graph_case": "case",
        }
        sources.append(SourceItem(
            type=type_map.get(doc_type, "unknown"),
            title=doc.metadata.get("law_name",
                   doc.metadata.get("case_number",
                   doc.metadata.get("title", "未知来源"))),
            snippet=doc.page_content[:200]
        ))

    return ChatResponse(answer=answer, sources=sources)


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式法律问答（SSE，逐 token 推送）"""
    def generate():
        for token in rag.query_stream(request.question, history=request.history, top_k=request.top_k):
            if token.startswith('{"__sources__":'):
                # 最后一条：来源信息
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


@app.get("/api/stats")
async def stats():
    """知识库统计"""
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
