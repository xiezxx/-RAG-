"""
混合检索器 — BM25 关键词 + 向量语义 + Neo4j 图谱，RRF 融合 + 时效感知
"""
import re
import pickle
import os
from typing import List, Tuple, Dict
import numpy as np
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

from src.config import Config
from src.database.neo4j_client import Neo4jClient
from src.rag.vector_store import VectorStore
from src.rag.timeliness import (
    parse_time_reference,
    filter_by_timeliness,
    get_timeliness_context,
    STATUS_LABELS,
)


# 劳动法领域关键词库
LAW_KEYWORDS = [
    "解除", "辞退", "开除", "加班", "工资", "工伤", "赔偿",
    "合同", "补偿金", "赔偿金", "社保", "竞业限制", "产假",
    "年休假", "试用期", "违约金", "职业病", "女职工", "劳动报酬",
    "违法解除", "经济补偿", "劳动关系", "劳动合同", "拖欠工资",
    "确认劳动关系", "竞业限制补偿", "服务期", "培训费", "社会保险",
    "平台用工", "事实劳动关系", "就业歧视", "三期女职工",
]

# RRF 常数，控制排名对最终分数的影响
RRF_K = 60


def _tokenize(text: str) -> List[str]:
    """简单中文分词：按标点 + 空格切分，同时保留 2-4 字词组"""
    text = re.sub(r'[^一-鿿]', ' ', text)
    tokens = [t.strip() for t in text.split() if len(t.strip()) >= 1]
    bigrams = []
    for t in tokens:
        for i in range(len(t) - 1):
            bigrams.append(t[i:i + 2])
    return tokens + bigrams


# ── RRF 融合 ──────────────────────────────────────────

def _rrf_fusion(
    ranked_lists: List[List[Tuple[Document, float]]],
    weights: List[float],
    k: int = RRF_K,
    final_top_k: int = None,
) -> List[Document]:
    """
    Reciprocal Rank Fusion — 融合多路检索结果。

    ranked_lists: 每路检索的 [(doc, score), ...] 列表，已按分数降序排列
    weights:      每路检索的权重
    k:            RRF 平滑常数（默认 60）
    final_top_k:  返回的文档数（默认 Config.FINAL_TOP_K）
    """
    if not ranked_lists:
        return []

    final_top_k = final_top_k or Config.FINAL_TOP_K
    scores: Dict[str, float] = {}          # doc_id -> RRF 累积分数
    doc_map: Dict[str, Document] = {}       # doc_id -> Document

    for path_idx, ranked in enumerate(ranked_lists):
        w = weights[path_idx] if path_idx < len(weights) else 1.0
        for rank, (doc, _score) in enumerate(ranked):
            # 用 page_content 的前 200 字符作为去重 key
            doc_id = doc.page_content[:200]
            rrf_score = w / (k + rank + 1)
            if doc_id in scores:
                scores[doc_id] += rrf_score
            else:
                scores[doc_id] = rrf_score
                doc_map[doc_id] = doc

    # 按 RRF 分数降序排列
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [doc_map[doc_id] for doc_id in sorted_ids[:final_top_k]]


# ── BM25 检索器 ───────────────────────────────────────

class BM25Retriever:
    """纯本地 BM25 检索器"""

    def __init__(self, index_path: str = None):
        self.bm25: BM25Okapi = None
        self.documents: List[Document] = []
        self.tokenized_corpus: List[List[str]] = []
        self._index_path = index_path or Config.BM25_INDEX_DIR

    def build_index(self, documents: List[Document]):
        """构建 BM25 索引"""
        self.documents = documents
        self.tokenized_corpus = [_tokenize(d.page_content) for d in documents]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search(self, query: str, top_k: int = None) -> List[Tuple[Document, float]]:
        """BM25 检索，返回 [(doc, score), ...]"""
        if not self.bm25:
            return []
        top_k = top_k or Config.BM25_SEARCH_TOP_K
        tokenized_query = _tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.documents[idx], float(scores[idx])))
        return results

    def is_ready(self) -> bool:
        return self.bm25 is not None and len(self.documents) > 0

    def save(self):
        """保存索引到磁盘"""
        os.makedirs(self._index_path, exist_ok=True)
        with open(os.path.join(self._index_path, "documents.pkl"), "wb") as f:
            pickle.dump(self.documents, f)
        with open(os.path.join(self._index_path, "corpus.pkl"), "wb") as f:
            pickle.dump(self.tokenized_corpus, f)

    def load(self) -> bool:
        """从磁盘加载索引"""
        doc_path = os.path.join(self._index_path, "documents.pkl")
        if os.path.exists(doc_path):
            with open(doc_path, "rb") as f:
                self.documents = pickle.load(f)
            with open(os.path.join(self._index_path, "corpus.pkl"), "rb") as f:
                self.tokenized_corpus = pickle.load(f)
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            return True
        return False


# ── 混合检索器 ────────────────────────────────────────

class HybridRetriever:
    """三路混合检索：BM25 + 向量语义 + Neo4j 图谱，RRF 融合"""

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client
        self.bm25 = BM25Retriever()
        self.vector = VectorStore()
        self._chunks: List[Document] = []  # 用于 BM25 的切分后文档

        # 消融实验开关
        self.use_bm25: bool = True
        self.use_vector: bool = True
        self.use_graph: bool = True
        self.use_timeliness: bool = True
        self.use_expansion: bool = True  # KG 关系扩展

    # ── 索引构建 ─────────────────────────────────────

    def build_index(self, documents: List[Document]):
        """从原始文档构建全部索引"""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        print("📝 切分文档 ...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        )
        self._chunks = splitter.split_documents(documents)
        print(f"  📄 共 {len(self._chunks)} 个文档块")

        # 1. BM25 索引
        print("🔤 构建 BM25 索引 ...")
        self.bm25.build_index(self._chunks)
        self.bm25.save()
        print("  ✅ BM25 索引已构建并保存")

        # 2. 向量索引
        print("🧠 构建向量索引 ...")
        self.vector.build_index(self._chunks)
        self.vector.save()
        print("  ✅ 向量索引已构建并保存")

    def load_index(self):
        """加载已有索引"""
        bm25_ok = self.bm25.load()
        vec_ok = self.vector.load()

        if not bm25_ok and not vec_ok:
            raise FileNotFoundError("BM25 和向量索引均不存在，请先运行 build_index()")

        # 从 BM25 恢复 chunks（用于后续检索）
        if bm25_ok:
            self._chunks = list(self.bm25.documents)
        elif vec_ok:
            self._chunks = list(self.vector._documents)

        print(f"  📊 索引已加载：BM25={'✅' if bm25_ok else '❌'}，向量={'✅' if vec_ok else '❌'}")

    def is_ready(self) -> bool:
        return self.bm25.is_ready() or self.vector.is_ready()

    # ── 核心检索 ─────────────────────────────────────

    def retrieve(self, query: str, final_top_k: int = None) -> List[Document]:
        """
        三路混合检索 + RRF 融合 + 时效过滤 + 自动策略选择
        """
        ranked_lists: List[List[Tuple[Document, float]]] = []
        weights: List[float] = []

        # 自动检测问题类型，动态调整权重
        strategy = self._detect_strategy(query)

        # 解析时间参考（消融时可关闭）
        reference_date, time_hint = None, None
        if self.use_timeliness:
            reference_date, time_hint = parse_time_reference(query)

        # ── 路径 1：BM25 关键词检索 ──
        if self.use_bm25 and self.bm25.is_ready():
            bm25_results = self.bm25.search(query, top_k=Config.BM25_SEARCH_TOP_K)
            ranked_lists.append(bm25_results)
            weights.append(strategy["bm25_weight"])

        # ── 路径 2：向量语义检索 ──
        if self.use_vector and self.vector.is_ready():
            vec_results = self.vector.search(query, top_k=Config.VECTOR_SEARCH_TOP_K)
            ranked_lists.append(vec_results)
            weights.append(strategy["vector_weight"])

        # ── 路径 3：Neo4j 图谱检索（含时效）──
        if self.use_graph:
            graph_results = self._graph_search(query, reference_date)
            if graph_results:
                ranked_lists.append([(doc, 1.0) for doc in graph_results])
                weights.append(strategy["graph_weight"])

        # ── RRF 融合 ──
        if not ranked_lists:
            return []

        merged = _rrf_fusion(
            ranked_lists,
            weights,
            final_top_k=final_top_k or Config.FINAL_TOP_K,
        )

        # ── 时效过滤与标注 ──
        if self.use_timeliness:
            prefer_current = reference_date is None
            merged = filter_by_timeliness(merged, reference_date, prefer_current)

        return merged

    def retrieve_as_context(self, query: str) -> str:
        """检索并格式化为 LLM 上下文（含时效标注）"""
        docs = self.retrieve(query)
        return self.documents_as_context(docs)

    def documents_as_context(self, docs: List[Document]) -> str:
        """格式化既有检索结果，避免回答和引用重复检索产生不一致。"""
        if not docs:
            return "未检索到相关法律资料。"

        # 时效总览
        timeliness_note = get_timeliness_context(docs)

        parts = []
        for doc in docs[:Config.FINAL_TOP_K]:
            doc_type = doc.metadata.get("doc_type", "unknown")
            labels = {
                "statute": "📜 法律条文",
                "interpretation": "⚖️ 司法解释",
                "case": "📝 案例",
                "graph_article": "🔗 关联法条",
                "graph_case": "🔗 相似案例",
            }
            label = labels.get(doc_type, "📄 资料")

            # 附加时效标签
            status_label = doc.metadata.get("status_label", "")
            eff_date = doc.metadata.get("effective_date", "")
            date_info = f" (生效: {eff_date})" if eff_date else ""

            header = f"[{label} {status_label}{date_info}]"
            parts.append(f"{header} {doc.page_content}")

        context = "\n\n---\n\n".join(parts)
        if timeliness_note:
            context = f"⚠️ 时效提示：{timeliness_note}\n\n{context}"

        return context

    # ── 图谱检索 ─────────────────────────────────────

    def _graph_search(self, query: str, reference_date: str = None) -> List[Document]:
        """Neo4j 图谱关联检索 + KG 关系扩展"""
        results = []
        if not self.neo4j.check_connection():
            return results
        keywords = self._extract_keywords(query)

        if keywords:
            # 基础关键词检索
            if reference_date:
                articles = self.neo4j.find_articles_by_time(
                    keywords, reference_date, limit=Config.GRAPH_SEARCH_TOP_K
                )
            else:
                articles = self.neo4j.find_related_articles(
                    keywords, limit=Config.GRAPH_SEARCH_TOP_K, prefer_current=True
                )

            for art in articles:
                status = art.get("status", "")
                eff_date = art.get("effective_date", "")
                results.append(Document(
                    page_content=f"【{art.get('statute', '')} {art['article_id']}】{art['content']}",
                    metadata={
                        "doc_type": "graph_article",
                        "article_id": art["article_id"],
                        "status": status,
                        "effective_date": eff_date,
                    },
                ))

            # KG 关系扩展检索（消融时可关闭）
            if self.use_expansion:
                expanded = self.neo4j.expand_by_graph(
                    keywords, limit=Config.GRAPH_SEARCH_TOP_K,
                )
                for exp in expanded:
                    if exp.get("article_id"):
                        results.append(Document(
                            page_content=(
                                f"【{exp.get('statute', '')} {exp['article_id']}】"
                                f"{exp.get('content', '')}"
                            ),
                            metadata={
                                "doc_type": "graph_article",
                                "article_id": exp["article_id"],
                                "status": exp.get("status", ""),
                                "effective_date": exp.get("effective_date", ""),
                                "via_entity": exp.get("via_entity", ""),
                            },
                        ))

            # 相似案例检索
            similar_cases = self.neo4j.find_similar_cases(
                keywords, limit=Config.GRAPH_SEARCH_TOP_K
            )
            for case in similar_cases:
                results.append(Document(
                    page_content=(
                        f"【参考案例 {case['case_number']}】\n"
                        f"案例内容：{case.get('case_content', '')}\n"
                        f"判决：{case.get('judgment', '')}"
                    ),
                    metadata={"doc_type": "graph_case", "case_number": case["case_number"]},
                ))

        return results

    def _extract_keywords(self, query: str) -> List[str]:
        return [kw for kw in LAW_KEYWORDS if kw in query]

    def _detect_strategy(self, query: str) -> Dict[str, float]:
        """自动检测问题类型，返回动态权重
        - 包含法条编号 → BM25 加权
        - 描述性/口语化 → 向量加权
        - 涉及主体/行为/责任 → KG 加权
        """
        bm25_w = Config.BM25_WEIGHT
        vec_w = Config.VECTOR_WEIGHT
        graph_w = Config.GRAPH_WEIGHT

        # 检测法条编号（如"第47条"、"第四十七条"）
        import re
        has_article_ref = bool(re.search(r'第[一二三四五六七八九十百千\d]+条', query))
        # 检测法律名称
        has_law_name = any(name in query for name in ['劳动法', '劳动合同法', '社会保险法', '工伤保险', '仲裁法'])

        if has_article_ref or has_law_name:
            bm25_w *= 1.5   # 精确查询加重关键词
            vec_w *= 0.7     # 减弱语义

        # 检测关系类查询（涉及主体、行为、责任）
        relation_words = ['用人单位', '劳动者', '公司', '员工', '赔偿', '责任', '应当', '不得', '禁止']
        if sum(1 for w in relation_words if w in query) >= 2:
            graph_w *= 1.5  # 加重图谱检索

        # 检测口语化描述（长度 > 15 且无法条引用）
        if len(query) > 15 and not has_article_ref:
            vec_w *= 1.3    # 加重语义匹配

        return {"bm25_weight": bm25_w, "vector_weight": vec_w, "graph_weight": graph_w}
