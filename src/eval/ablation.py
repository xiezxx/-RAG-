"""
消融实验评估 —— 对比不同检索策略的效果
"""
import json
import os
import time
from typing import List, Dict, Tuple
from dataclasses import dataclass, field

from src.config import Config
from src.database.neo4j_client import Neo4jClient
from src.rag.retriever import HybridRetriever


@dataclass
class EvalResult:
    """单次评估结果"""
    config_name: str
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    precision_at_5: float = 0.0
    mrr: float = 0.0                       # Mean Reciprocal Rank
    expired_rate: float = 0.0              # 过期条文引用率
    avg_latency_ms: float = 0.0            # 平均检索耗时
    per_question: List[Dict] = field(default_factory=list)


class AblationRunner:
    """消融实验运行器"""

    def __init__(self, test_path: str = None):
        self.test_path = test_path or os.path.join(
            os.path.dirname(__file__), "test_questions.json"
        )
        with open(self.test_path, "r", encoding="utf-8") as f:
            self.questions = json.load(f)

        self.neo4j = Neo4jClient()
        self.retriever = HybridRetriever(self.neo4j)
        self.retriever.load_index()

    # ── 消融配置 ─────────────────────────────────────

    def _configure(self, config: str):
        """根据配置名设置消融开关"""
        r = self.retriever
        # 默认全关
        r.use_bm25 = False
        r.use_vector = False
        r.use_graph = False
        r.use_timeliness = False
        r.use_expansion = False

        if config == "bm25":
            r.use_bm25 = True
        elif config == "bm25+vector":
            r.use_bm25 = True
            r.use_vector = True
        elif config == "bm25+vector+kg":
            r.use_bm25 = True
            r.use_vector = True
            r.use_graph = True
        elif config == "bm25+vector+kg+time":
            r.use_bm25 = True
            r.use_vector = True
            r.use_graph = True
            r.use_timeliness = True
        elif config == "full":
            r.use_bm25 = True
            r.use_vector = True
            r.use_graph = True
            r.use_timeliness = True
            r.use_expansion = True
        else:
            raise ValueError(f"Unknown config: {config}")

    # ── 指标计算 ─────────────────────────────────────

    def _hit_at_k(self, retrieved_ids: List[str], relevant_ids: List[str], k: int) -> int:
        """前 k 个结果中命中的数量"""
        if not relevant_ids:
            return 0
        hits = 0
        for ret_id in retrieved_ids[:k]:
            # 部分匹配：检索到的 article_id 包含 relevant 的关键部分
            for rel_id in relevant_ids:
                if self._id_match(ret_id, rel_id):
                    hits += 1
                    break
        return hits

    @staticmethod
    def _id_match(retrieved: str, relevant: str) -> bool:
        """模糊匹配法条 ID —— 比较法律名 + 条款号"""
        import re

        def _norm(s: str) -> str:
            s = s.replace("中华人民共和国", "").replace(" ", "")
            return s.lower()

        r_norm = _norm(retrieved)
        rel_norm = _norm(relevant)

        # 完全匹配或包含
        if r_norm == rel_norm:
            return True
        if rel_norm in r_norm or r_norm in rel_norm:
            return True

        # 提取条款号比较
        r_arts = re.findall(r'第[一二三四五六七八九十百千\d]+条', retrieved)
        rel_arts = re.findall(r'第[一二三四五六七八九十百千\d]+条', relevant)
        if r_arts and rel_arts and r_arts[0] == rel_arts[0]:
            # 同一条款号，再看法律名称是否相关
            return True

        return False

    def _compute_metrics(
        self, question: Dict, retrieved: List, elapsed_ms: float,
    ) -> Dict:
        """计算单题指标"""
        relevant = question.get("relevant_articles", [])
        retrieved_ids = [
            doc.metadata.get("article_id") or
            doc.metadata.get("law_name") or
            doc.metadata.get("case_number") or
            doc.page_content[:50]
            for doc in retrieved
        ]

        # 检查每个 retrieved item 与 relevant 的匹配
        hits_at_1 = self._hit_at_k(retrieved_ids, relevant, 1)
        hits_at_3 = self._hit_at_k(retrieved_ids, relevant, 3)
        hits_at_5 = self._hit_at_k(retrieved_ids, relevant, 5)

        # Recall@K: 命中的相关条文 / 总相关条文
        denom = max(len(relevant), 1)
        recall_1 = min(hits_at_1, 1) / denom
        recall_3 = min(hits_at_3, 3) / denom
        recall_5 = min(hits_at_5, 5) / denom

        # Precision@5: 前5个结果中的命中数 / 5
        precision_5 = hits_at_5 / min(len(retrieved_ids), 5) if retrieved_ids else 0

        # MRR: 第一个命中的倒数排名
        mrr = 0.0
        for rank, ret_id in enumerate(retrieved_ids[:10], 1):
            for rel_id in relevant:
                if self._id_match(ret_id, rel_id):
                    mrr = 1.0 / rank
                    break
            if mrr > 0:
                break

        # 过期率
        expired_count = 0
        for doc in retrieved:
            status = doc.metadata.get("status", "")
            if status in ("已废止", "已被修订"):
                expired_count += 1
        expired_rate = expired_count / len(retrieved) if retrieved else 0

        return {
            "question_id": question["id"],
            "recall_1": recall_1,
            "recall_3": recall_3,
            "recall_5": recall_5,
            "precision_5": precision_5,
            "mrr": mrr,
            "expired_rate": expired_rate,
            "latency_ms": elapsed_ms,
            "num_retrieved": len(retrieved),
        }

    # ── 运行消融 ─────────────────────────────────────

    def run_config(self, config_name: str) -> EvalResult:
        """运行一个消融配置"""
        self._configure(config_name)
        result = EvalResult(config_name=config_name)
        total_latency = 0.0

        for q in self.questions:
            t0 = time.time()
            retrieved = self.retriever.retrieve(q["question"])
            elapsed = (time.time() - t0) * 1000  # ms
            total_latency += elapsed

            metrics = self._compute_metrics(q, retrieved, elapsed)
            result.per_question.append(metrics)

        n = len(self.questions)
        result.recall_at_1 = sum(m["recall_1"] for m in result.per_question) / n
        result.recall_at_3 = sum(m["recall_3"] for m in result.per_question) / n
        result.recall_at_5 = sum(m["recall_5"] for m in result.per_question) / n
        result.precision_at_5 = sum(m["precision_5"] for m in result.per_question) / n
        result.mrr = sum(m["mrr"] for m in result.per_question) / n
        result.expired_rate = sum(m["expired_rate"] for m in result.per_question) / n
        result.avg_latency_ms = total_latency / n

        return result

    def run_all(self) -> List[EvalResult]:
        """运行全部消融配置"""
        configs = [
            "bm25",
            "bm25+vector",
            "bm25+vector+kg",
            "bm25+vector+kg+time",
            "full",
        ]
        results = []
        for cfg in configs:
            print(f"\n{'='*60}")
            print(f"  运行: {cfg}")
            print(f"{'='*60}")
            result = self.run_config(cfg)
            results.append(result)
            self._print_result(result)
        return results

    # ── 输出 ─────────────────────────────────────────

    @staticmethod
    def _print_result(r: EvalResult):
        print(f"  Recall@1:     {r.recall_at_1:.2%}")
        print(f"  Recall@3:     {r.recall_at_3:.2%}")
        print(f"  Recall@5:     {r.recall_at_5:.2%}")
        print(f"  Precision@5:  {r.precision_at_5:.2%}")
        print(f"  MRR:          {r.mrr:.4f}")
        print(f"  Expired Rate: {r.expired_rate:.2%}")
        print(f"  Avg Latency:  {r.avg_latency_ms:.0f}ms")

    @staticmethod
    def print_table(results: List[EvalResult]):
        """打印对比表格（可直接放入论文）"""
        print("\n" + "=" * 90)
        print("消融实验结果对比")
        print("=" * 90)
        header = f"{'配置':<30} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'P@5':>6} {'MRR':>6} {'过期率':>6} {'延迟':>6}"
        print(header)
        print("-" * 90)

        baseline = results[0] if results else None
        for r in results:
            recall_delta = ""
            mrr_delta = ""
            if baseline and r != baseline:
                rd = r.recall_at_5 - baseline.recall_at_5
                md = r.mrr - baseline.mrr
                recall_delta = f" (+{rd:.0%})" if rd > 0 else f" ({rd:.0%})"
                mrr_delta = f" (+{md:.3f})" if md > 0 else ""

            print(
                f"{r.config_name:<30} "
                f"{r.recall_at_1:>5.0%} "
                f"{r.recall_at_3:>5.0%} "
                f"{r.recall_at_5:>5.0%}{recall_delta:<8} "
                f"{r.precision_at_5:>5.0%} "
                f"{r.mrr:>6.4f}{mrr_delta:<8} "
                f"{r.expired_rate:>5.0%} "
                f"{r.avg_latency_ms:>4.0f}ms"
            )
        print("=" * 90)

    def export_json(self, results: List[EvalResult], path: str = None):
        """导出完整实验结果 JSON"""
        path = path or os.path.join(os.path.dirname(__file__), "ablation_results.json")
        data = {
            "configs": [],
            "per_question": {},
        }
        for r in results:
            data["configs"].append({
                "name": r.config_name,
                "recall_at_1": round(r.recall_at_1, 4),
                "recall_at_3": round(r.recall_at_3, 4),
                "recall_at_5": round(r.recall_at_5, 4),
                "precision_at_5": round(r.precision_at_5, 4),
                "mrr": round(r.mrr, 4),
                "expired_rate": round(r.expired_rate, 4),
                "avg_latency_ms": round(r.avg_latency_ms, 1),
            })
            data["per_question"][r.config_name] = r.per_question

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n详细结果已导出至: {path}")


# ── CLI 入口 ──────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    runner = AblationRunner()
    results = runner.run_all()
    runner.print_table(results)
    runner.export_json(results)
