import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """全局配置"""

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")

    # LLM（支持 OpenAI / DeepSeek 等兼容 API）
    LLM_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("OPENAI_MODEL", "deepseek")
    LLM_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")

    # Embedding（本地模型，无需 API）
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "shibing624/text2vec-base-chinese"
    )
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")

    # 数据路径
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR: str = os.getenv("DATA_DIR", str(PROJECT_ROOT / "src" / "data" / "raw"))
    VECTOR_INDEX_DIR: str = os.getenv("VECTOR_INDEX_DIR", str(PROJECT_ROOT / "vector_index"))
    BM25_INDEX_DIR: str = os.getenv("BM25_INDEX_DIR", str(PROJECT_ROOT / "bm25_index"))

    # 检索参数
    BM25_SEARCH_TOP_K: int = 8
    VECTOR_SEARCH_TOP_K: int = 8
    GRAPH_SEARCH_TOP_K: int = 3
    FINAL_TOP_K: int = 10  # 融合后最终返回的文档数

    # 多策略融合权重（RRF 中各路径的相对权重）
    BM25_WEIGHT: float = 1.0
    VECTOR_WEIGHT: float = 1.0
    GRAPH_WEIGHT: float = 0.5

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    @classmethod
    def validate(cls) -> bool:
        """检查必要配置是否齐全"""
        missing = []
        if not cls.LLM_API_KEY or cls.LLM_API_KEY == "your-openai-api-key-here":
            missing.append("OPENAI_API_KEY")
        if not cls.NEO4J_PASSWORD:
            missing.append("NEO4J_PASSWORD")
        if missing:
            raise ValueError(f"请在 .env 文件中填写: {', '.join(missing)}")
        return True
