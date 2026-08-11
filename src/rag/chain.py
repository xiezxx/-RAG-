"""
RAG 问答链 — LangChain 构建的法律问答链路
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import httpx

from src.config import Config
from src.rag.retriever import HybridRetriever


SYSTEM_PROMPT = """你是一位专业的中国劳动法专家助手。你的回答必须基于检索到的法律资料，严格遵守以下规则：

## 回答规则

1. **有法可依**：优先引用具体的法律法规条文，标注出处（如「《劳动合同法》第47条」）
2. **司法解释**：如有相关司法解释，一并引用并说明其含义
3. **案例参考**：如检索到相似案例，简述案例情况辅助理解，但明确告知"个案情况不同，仅供参考"
4. **时效判断**：注意每条法条的时效状态标记（🟢现行有效 / 🟡已被修订 / 🔴已废止 / 🔵尚未生效）。优先依据 🟢现行有效 的法条作答，若引用了 🟡已被修订 或 🔴已废止 的条文，必须明确提示用户"该条文已被修订/废止，请以最新版本为准"
5. **诚实边界**：如果检索资料不足以回答，或法律没有明确规定，如实告知"当前检索资料范围内无法找到明确依据"
6. **禁止臆造**：绝对不能编造不存在的法条、案号或司法解释

## 回答结构

对于咨询类问题，按以下结构组织：
1. **结论摘要**（一句话）
2. **法律依据**（引用具体法条，注明时效状态）
3. **详细分析**（结合司法解释和案例）
4. **实操建议**（如适用）
5. **风险提示**（含时效风险——如引用的法条可能已修订）

---

{chat_history}
当前检索到的法律资料（含时效标注）：

{context}

---

用户问题：{question}

请提供专业、准确的法律分析："""


class LabourLawRAG:
    """劳动法 RAG 问答系统"""

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever

        llm_kwargs = dict(
            model=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
            temperature=0.1,
            max_tokens=2000,
            streaming=True,
            http_client=httpx.Client(trust_env=False),
        )
        # DeepSeek / 兼容 OpenAI 的自定义地址
        if Config.LLM_BASE_URL:
            llm_kwargs["base_url"] = Config.LLM_BASE_URL

        self.llm = ChatOpenAI(**llm_kwargs)
        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

        self.chain = self.prompt | self.llm | StrOutputParser()

    def query(self, question: str, history: list = None) -> str:
        """查询法律问题，返回分析结果"""
        if not isinstance(question, str) or not question.strip():
            return "请输入您的劳动法问题。"
        try:
            answer, _ = self.query_with_documents(question, history)
            return answer
        except Exception:
            return "系统暂时无法完成检索，请稍后重试。"

    def query_with_documents(self, question: str, history: list = None, top_k: int = None):
        """使用改写词检索，但始终用用户原问题作答，并返回实际引用文档。
        Args:
            question: 用户当前问题
            history: 对话历史，格式 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        rewritten = self._rewrite_query(question)
        docs = self.retriever.retrieve(rewritten, final_top_k=top_k)

        # 程序化门控：检索证据不足时直接拒答，不调用 LLM
        if not docs or len(docs) == 0:
            return (
                "抱歉，在当前劳动法律知识库中未检索到与您问题相关的法律条文。\n\n"
                "建议：\n"
                "1. 尝试使用更具体的法律术语重新提问\n"
                "2. 提供法条编号（如「劳动合同法第47条」）以获得更精确的结果\n"
                "3. 如需专业法律意见，请咨询执业律师",
                []
            )

        # 格式化对话历史
        chat_history = self._format_history(history)

        context = self.retriever.documents_as_context(docs)
        answer = self.chain.invoke({
            "chat_history": chat_history,
            "context": context,
            "question": question,
        })
        return answer, docs

    def query_stream(self, question: str, history: list = None, top_k: int = None):
        """流式法律问答（生成器，逐 token yield）
        使用 OpenAI 原生客户端直连 DeepSeek，绕过 LangChain 流式兼容问题。
        Yields:
            str: 文本 token
            最后一条: '{"__sources__": [...]}' 格式的来源 JSON
        """
        import json as _json
        from openai import OpenAI

        if not isinstance(question, str) or not question.strip():
            yield "请输入您的劳动法问题。"
            yield _json.dumps({"__sources__": []})
            return

        rewritten = self._rewrite_query(question)
        docs = self.retriever.retrieve(rewritten, final_top_k=top_k)

        # 门控
        if not docs or len(docs) == 0:
            yield ("抱歉，在当前劳动法律知识库中未检索到与您问题相关的法律条文。\n\n"
                   "建议：\n"
                   "1. 尝试使用更具体的法律术语重新提问\n"
                   "2. 提供法条编号（如「劳动合同法第47条」）以获得更精确的结果\n"
                   "3. 如需专业法律意见，请咨询执业律师")
            yield _json.dumps({"__sources__": []})
            return

        chat_history = self._format_history(history)
        context = self.retriever.documents_as_context(docs)

        # 收集来源
        sources = []
        for doc in docs[:5]:
            sources.append({
                "type": doc.metadata.get("doc_type", "unknown"),
                "title": doc.metadata.get("law_name",
                         doc.metadata.get("case_number",
                         doc.metadata.get("title", "未知来源"))),
                "snippet": doc.page_content[:200]
            })

        # 构建完整 Prompt（填充占位符）
        full_prompt = (SYSTEM_PROMPT
            .replace("{chat_history}", chat_history)
            .replace("{context}", context)
            .replace("{question}", question))

        # 使用 OpenAI 原生客户端流式调用 DeepSeek
        client = OpenAI(
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL,
        )
        stream = client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.1,
            max_tokens=2000,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

        # 最后一条：来源信息
        yield _json.dumps({"__sources__": sources})

    @staticmethod
    def _format_history(history: list) -> str:
        """将对话历史格式化为 Prompt 文本（保留最近 3 轮共 6 条）"""
        if not history:
            return ""
        recent = history[-6:]  # 最多保留最近 3 轮对话
        lines = ["## 对话历史（用于理解上下文）"]
        for msg in recent:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"👤 用户：{content}")
            elif role == "assistant":
                # 截断过长回答，避免 Prompt 超限
                short = content[:1200] + ("…" if len(content) > 1200 else "")
                lines.append(f"🤖 助手：{short}")
        lines.append("")
        return "\n".join(lines)

    def _rewrite_query(self, question: str) -> str:
        """将口语化问题改写为法律术语查询（轻量级 LLM 调用）"""
        rewrite_prompt = f"""将以下用户的劳动法问题改写为适合法律检索的关键词组合。
只输出改写后的查询文本（不要解释，不要额外文字）。

用户问题：{question}
改写查询："""

        try:
            # 用小 token 量快速改写
            response = self.llm.invoke(rewrite_prompt)
            rewritten = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            # 改写失败或太短则用原文
            if len(rewritten) < 4:
                return question
            return rewritten
        except Exception:
            return question  # 改写失败则用原文兜底
