"""
向量存储 — 基于 FAISS + sentence-transformers 的语义检索
"""
import os
import pickle
import numpy as np
from typing import List, Tuple, Optional
from langchain_core.documents import Document

from src.config import Config


class VectorStore:
    """本地 FAISS 向量索引 + sentence-transformers 嵌入模型"""

    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or Config.EMBEDDING_MODEL_NAME
        self.device = device or Config.EMBEDDING_DEVICE
        self._model = None
        self._index = None          # FAISS IndexFlatIP（内积=余弦相似度，归一化后）
        self._documents: List[Document] = []
        self._dimension: int = 0

    # ── 懒加载模型 ────────────────────────────────────

    @property
    def model(self):
        """懒加载 embedding 模型，避免启动时立即消耗内存"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            print(f"  📥 加载 Embedding 模型: {self.model_name} (device={self.device}) ...")

            # 优先使用本地缓存，避免 HuggingFace 连接超时
            # 如果设置了 HF_ENDPOINT 镜像，则走镜像
            model_kwargs = dict(device=self.device)
            hf_endpoint = os.getenv("HF_ENDPOINT", "")
            if hf_endpoint:
                model_kwargs["local_files_only"] = False
            else:
                # 无镜像时先尝试纯本地加载，避免超时重试
                try:
                    self._model = SentenceTransformer(
                        self.model_name, local_files_only=True, **model_kwargs
                    )
                except Exception:
                    print("  ⚠️ 本地文件不全，尝试联网下载（可能较慢）...")
                    self._model = SentenceTransformer(self.model_name, **model_kwargs)

            if self._model is None:
                self._model = SentenceTransformer(self.model_name, **model_kwargs)

            self._dimension = self._model.get_embedding_dimension()
            print(f"  ✅ Embedding 模型就绪，维度: {self._dimension}")
        return self._model

    @property
    def index(self):
        """获取 FAISS 索引（若未构建则为 None）"""
        return self._index

    # ── 索引构建 ──────────────────────────────────────

    def build_index(self, documents: List[Document], batch_size: int = 32):
        """对文档列表编码并构建 FAISS 索引"""
        if not documents:
            print("  ⚠️ 无文档，跳过向量索引构建")
            return

        self._documents = list(documents)
        texts = [d.page_content for d in documents]

        print(f"  🔤 正在向量化 {len(texts)} 个文档块 ...")

        # 分批编码以显示进度
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,  # L2 归一化，使内积等价于余弦相似度
        )

        self._dimension = embeddings.shape[1]

        # 构建 FAISS 索引（内积搜索 = 归一化后的余弦相似度）
        import faiss
        self._index = faiss.IndexFlatIP(self._dimension)
        self._index.add(embeddings.astype(np.float32))

        print(f"  ✅ 向量索引构建完成：{self._index.ntotal} 个向量，维度 {self._dimension}")

    def search(self, query: str, top_k: int = None) -> List[Tuple[Document, float]]:
        """语义检索，返回 (文档, 相似度分数) 列表"""
        if self._index is None or not self._documents:
            return []

        top_k = top_k or Config.VECTOR_SEARCH_TOP_K
        actual_k = min(top_k, len(self._documents))

        # 编码查询
        query_vec = self.model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)

        # FAISS 检索
        scores, indices = self._index.search(query_vec, actual_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._documents):
                results.append((self._documents[idx], float(score)))

        return results

    def is_ready(self) -> bool:
        return self._index is not None and len(self._documents) > 0

    # ── 持久化 ────────────────────────────────────────

    def save(self, path: str = None):
        """保存 FAISS 索引和文档到磁盘"""
        import faiss

        path = path or Config.VECTOR_INDEX_DIR
        os.makedirs(path, exist_ok=True)

        # 保存 FAISS 索引
        if self._index is not None:
            faiss.write_index(self._index, os.path.join(path, "faiss.index"))

        # 保存文档和元数据
        with open(os.path.join(path, "documents.pkl"), "wb") as f:
            pickle.dump(self._documents, f)

        # 保存配置
        meta = {
            "model_name": self.model_name,
            "dimension": self._dimension,
        }
        with open(os.path.join(path, "meta.pkl"), "wb") as f:
            pickle.dump(meta, f)

        print(f"  💾 向量索引已保存至: {path}")

    def load(self, path: str = None) -> bool:
        """从磁盘加载 FAISS 索引和文档"""
        import faiss

        path = path or Config.VECTOR_INDEX_DIR

        index_path = os.path.join(path, "faiss.index")
        docs_path = os.path.join(path, "documents.pkl")
        meta_path = os.path.join(path, "meta.pkl")

        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            return False

        # 加载元数据
        if os.path.exists(meta_path):
            with open(meta_path, "rb") as f:
                meta = pickle.load(f)
                self._dimension = meta.get("dimension", 0)

        # 加载 FAISS 索引
        self._index = faiss.read_index(index_path)

        # 加载文档
        with open(docs_path, "rb") as f:
            self._documents = pickle.load(f)

        print(f"  ✅ 向量索引已加载：{self._index.ntotal} 个向量")
        return True
