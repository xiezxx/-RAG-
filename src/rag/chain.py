"""
RAG 问答链 — LangChain 构建的法律问答链路
"""

import json
import re
import time

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import httpx

from src.config import Config
from src.rag.retriever import HybridRetriever
from src.rag.loader import first_article_no


def _source_from_doc(doc) -> dict:
    """从检索文档构建来源项（含时效状态与条文号，供前端时效标记与修订对比）
    - 图谱法条文档元数据无 law_name，从正文头部【法律名 第X条】提取
    - 条文号优先取 article_id（图谱文档），否则从正文中识别第一个条文号
    """
    m = doc.metadata
    doc_type = m.get("doc_type", "unknown")
    law = m.get("law_name") or ""
    if not law and doc_type == "graph_article":
        mm = re.match(r'^【(.+?)\s*第[一二三四五六七八九十百千零]+条】', doc.page_content)
        law = mm.group(1) if mm else ""
    return {
        "type": doc_type,
        "title": law or m.get("case_number") or m.get("title") or "未知来源",
        "snippet": doc.page_content[:200],
        "status": m.get("status", ""),
        "article": m.get("article_id", "") or first_article_no(doc.page_content),
        "law": law,
    }


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
1. **开场引导**：回答的第一句话固定为——好的，作为中国劳动法专家助手，我将基于您提供的检索资料，针对「关键词1、关键词2、关键词3」这几个关键词进行专业的法律分析。其中「」内填入 3-5 个从用户问题中提炼的核心法律关键词，用顿号分隔（例如用户问"孕期被公司降薪调岗是否违法？"，应写：针对「孕期、降薪、调岗、违法」这几个关键词）。开场引导后另起一行再写正文，不要在此之外添加其他寒暄
2. **结论摘要**（一句话）
3. **法律依据**（引用具体法条，注明时效状态）
4. **详细分析**（结合司法解释和案例）
5. **实操建议**（如适用）
6. **风险提示**（含时效风险——如引用的法条可能已修订）

---

{chat_history}
当前检索到的法律资料（含时效标注）：

{context}

---

用户问题：{question}

请提供专业、准确的法律分析："""


ARTICLE_PROMPT = """你是一位劳动法普法专栏作者。请根据下方检索到的法律资料，为普通劳动者撰写一篇通俗易懂的普法文章。

## 写作要求

1. 主题：{topic}
2. 风格：面向普通劳动者的科普文章，语言通俗、少用法言法语，重要概念配生活化小例子说明
3. 篇幅：1000-1500 字，使用 Markdown 格式
4. 结构（用 ## 二级标题）：
   - 开头一段：一句话点明核心结论
   - ## 一、法律规定是怎么说的 —— 引用法条并标注条文号（如《劳动合同法》第47条）与时效状态
   - ## 二、实务中常见的几个问题 —— 结合资料解答 2-4 个高频问题
   - ## 三、劳动者该怎么做 —— 3-5 条实操建议（证据收集、仲裁时效、维权途径）
   - ## 四、特别提醒 —— 风险提示与时效提示
5. 时效规则：优先依据 🟢现行有效 条文；若引用了 🟡已被修订 或 🔴已废止 的内容，必须明确写出「该条文已被修订/废止，请以最新版本为准」；绝不引用检索资料中未出现的法条编号
6. 禁止编造：所有法条、案号必须来自下方检索资料；资料不足时如实说明
7. 文末不要写来源列表（来源由系统单独展示）

## 检索到的法律资料（含时效标注）

{context}

请撰写主题为「{topic}」的普法文章："""


SCENE_START_PROMPT = """你是一位劳动法情景剧编剧。请根据下方检索到的法律资料，为「{story}」编写互动普法情景剧的第 {scene_index} 幕。

## 创作要求

1. 主角：普通劳动者「小李」，场景贴近真实职场，冲突自然、有代入感
2. 本幕以第二人称「你」叙述剧情，结尾给出 3 个应对选项（A/B/C）：
   - 一个明显合法合理（正确答案），一个明显违法或吃亏，一个看似合理但有隐患
3. 严格只输出 JSON 对象（不要 markdown 代码块、不要任何解释文字），格式如下：
{{"scene_text": "本幕剧情，80-150字", "options": [{{"key": "A", "text": "选项内容，≤20字"}}, {{"key": "B", "text": "选项内容，≤20字"}}, {{"key": "C", "text": "选项内容，≤20字"}}], "correct_key": "正确选项的key"}}
4. 剧情中的法律冲突必须在下方检索资料中有依据，法条号只允许使用资料中出现的

## 检索到的法律资料（含时效标注）

{context}

请输出第 {scene_index} 幕 JSON："""


SCENE_NEXT_PROMPT = """你是一位劳动法情景剧编剧兼普法老师。读者正在体验「{story}」互动情景剧，刚在本幕做出选择，请你先给出法律点评，再推进剧情。

## 本幕剧情

{prev_scene}

## 本幕选项

{prev_options}

读者选择了：{choice}
（本幕正确答案是：{prev_correct_key}）

## 要求

1. 先「判决」：点评读者的选择对错，用下方检索资料中的法条口语化解释为什么
2. 再推进剧情：下一幕要承接读者选择带来的后果（选错了就要演出麻烦后果，选对了也要自然推进）
3. 严格只输出 JSON 对象（不要 markdown 代码块、不要任何解释文字），格式如下：
{{"verdict": {{"correct": true或false, "correct_key": "本幕正确选项key", "explanation": "点评与法条解释，80-150字", "law_refs": ["《法律名》第X条", "..."]}}, {next_json}}}
4. 法条号只允许使用下方检索资料中出现的，禁止编造

## 检索到的法律资料（含时效标注）

{context}

请输出 JSON："""


SCENE_ENDING_PROMPT = """你是一位劳动法情景剧编剧兼普法老师。读者完成了「{story}」互动情景剧最后一幕的选择，请给出全剧总结。

## 最后一幕剧情

{prev_scene}

## 最后一幕选项

{prev_options}

读者选择了：{choice}
（本幕正确答案是：{prev_correct_key}）

## 要求

1. 先「判决」：点评读者最后一幕的选择对错，用下方检索资料中的法条口语化解释
2. 再总结全剧：基于整个故事给出「避坑笔记」——3 条劳动者实操要点
3. 严格只输出 JSON 对象（不要 markdown 代码块、不要任何解释文字），格式如下：
{{"verdict": {{"correct": true或false, "correct_key": "本幕正确选项key", "explanation": "点评与法条解释，80-150字", "law_refs": ["《法律名》第X条"]}}, "ending": {{"summary": "全剧总结，80-120字", "lessons": ["避坑要点1，≤30字", "避坑要点2，≤30字", "避坑要点3，≤30字"]}}}}
4. 法条号只允许使用下方检索资料中出现的，禁止编造

## 检索到的法律资料（含时效标注）

{context}

请输出 JSON："""


POSTER_PROMPT = """你是一位劳动法普法海报设计师。请根据下方检索到的法律资料，为「{topic}」提炼一张普法海报的文案内容。

## 要求

1. 面向普通劳动者，语言通俗有力，避免法言法语堆砌
2. 严格只输出 JSON 对象（不要 markdown 代码块、不要任何解释文字），格式如下：
{{"title": "海报标题，≤14字", "slogan": "一句话标语，≤20字", "points": [{{"headline": "要点标题，≤12字", "detail": "要点解释，≤40字"}}（共4条）], "tip": "底部温馨提示，≤30字", "law_basis": "核心法条依据，如《劳动合同法》第44条"}}
3. 所有内容必须基于下方检索资料，法条号只允许使用资料中出现的，禁止编造

## 检索到的法律资料（含时效标注）

{context}

请输出 JSON："""


VIDEO_PROMPT = """你是一位劳动法普法短片导演。请根据下方检索到的法律资料，为「{topic}」创作一支 30 秒科普短片的完整分镜脚本。

## 要求

1. 共 5 个分镜，节奏为：开场提问 → 法律怎么说 → 常见误区 → 怎么办 → 总结提醒
2. 每个分镜两行文案：visual 是画面大字（冲击力强、≤15字），subtitle 是旁白（口语化、1-2句、≤60字）
3. 严格只输出 JSON 对象（不要 markdown 代码块、不要任何解释文字），格式如下：
{{"title": "短片标题，≤15字", "scenes": [{{"visual": "画面大字", "subtitle": "旁白文案"}}（共5个）]}}
4. 所有内容必须基于下方检索资料，法条号只允许使用资料中出现的，禁止编造

## 检索到的法律资料（含时效标注）

{context}

请输出 JSON："""


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

        # 科普文章生成用 LLM（更高的 token 预算，稍高温度，非流式）
        article_kwargs = dict(
            model=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
            temperature=0.3,
            max_tokens=4096,
            streaming=False,
            http_client=httpx.Client(trust_env=False),
        )
        if Config.LLM_BASE_URL:
            article_kwargs["base_url"] = Config.LLM_BASE_URL
        self.article_llm = ChatOpenAI(**article_kwargs)

    def query(self, question: str, history: list = None) -> str:
        """查询法律问题，返回分析结果"""
        if not isinstance(question, str) or not question.strip():
            return "请输入您的劳动法问题。"
        try:
            answer, _ = self.query_with_documents(question, history)
            return answer
        except Exception:
            return "系统暂时无法完成检索，请稍后重试。"

    def query_with_documents(self, question: str, history: list = None, top_k: int = None, mode: str = None):
        """使用改写词检索，但始终用用户原问题作答，并返回实际引用文档。
        Args:
            question: 用户当前问题
            history: 对话历史，格式 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            mode: 检索模式（见 retriever.RETRIEVAL_MODES），None 表示完整混合
        """
        rewritten = self._rewrite_query(question)
        saved = self.retriever.apply_mode(mode) if mode else None
        try:
            docs = self.retriever.retrieve(rewritten, final_top_k=top_k)
        finally:
            if saved is not None:
                self.retriever.restore_mode(saved)

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

    def query_stream(self, question: str, history: list = None, top_k: int = None, mode: str = None):
        """流式法律问答（生成器，逐 token yield）
        使用 OpenAI 原生客户端直连 DeepSeek，绕过 LangChain 流式兼容问题。
        Yields:
            str: 文本 token
            倒数第二条: '{"__sources__": [...]}' 格式的来源 JSON
            最后一条:   '{"__trace__": {...}}' 检索过程明细（供前端可视化面板）
        """
        import json as _json
        from openai import OpenAI

        if not isinstance(question, str) or not question.strip():
            yield "请输入您的劳动法问题。"
            yield _json.dumps({"__sources__": []})
            yield _json.dumps({"__trace__": {"query": question, "channels": [], "final": []}})
            return

        t_rewrite = time.time()
        rewritten = self._rewrite_query(question)
        rewrite_ms = (time.time() - t_rewrite) * 1000

        saved = self.retriever.apply_mode(mode) if mode else None
        try:
            docs, trace = self.retriever.retrieve_with_trace(rewritten, final_top_k=top_k)
        finally:
            if saved is not None:
                self.retriever.restore_mode(saved)

        trace["mode"] = mode or "full"
        trace["original_question"] = question
        trace["timings"]["rewrite_ms"] = round(rewrite_ms, 1)

        # 门控
        if not docs or len(docs) == 0:
            yield ("抱歉，在当前劳动法律知识库中未检索到与您问题相关的法律条文。\n\n"
                   "建议：\n"
                   "1. 尝试使用更具体的法律术语重新提问\n"
                   "2. 提供法条编号（如「劳动合同法第47条」）以获得更精确的结果\n"
                   "3. 如需专业法律意见，请咨询执业律师")
            yield _json.dumps({"__sources__": []})
            yield _json.dumps({"__trace__": trace})
            return

        chat_history = self._format_history(history)
        context = self.retriever.documents_as_context(docs)

        # 收集来源（含时效状态与条文号，供前端时效标记与修订对比）
        sources = [_source_from_doc(doc) for doc in docs[:5]]
        # 历史问题可能前5全是现行版本：若最终候选含已被修订的历史版本，补一条最高排位的，
        # 使前端"修订对比"入口可见（模块5.3）
        if not any(s.get("status") == "已被修订" for s in sources):
            for doc in docs[5:]:
                if doc.metadata.get("status") == "已被修订":
                    sources.append(_source_from_doc(doc))
                    break

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

        # 最后两条：来源信息 + 检索过程明细
        yield _json.dumps({"__sources__": sources})
        yield _json.dumps({"__trace__": trace})

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

    def generate_article(self, topic: str, search_query: str = None):
        """检索语料并生成普法文章。

        Args:
            topic: 文章主题（用于标题与 Prompt）
            search_query: 检索查询，缺省用 topic

        Returns:
            (markdown_content, sources) — sources 为 [{type, title, snippet, status}]
        """
        query = (search_query or topic).strip()
        docs = self.retriever.retrieve(query, final_top_k=10)
        if not docs:
            raise ValueError("知识库中未检索到与该主题相关的资料")

        context = self.retriever.documents_as_context(docs)

        sources = []
        for doc in docs[:6]:
            sources.append({
                "type": doc.metadata.get("doc_type", "unknown"),
                "title": doc.metadata.get("law_name",
                         doc.metadata.get("case_number",
                         doc.metadata.get("title", "未知来源"))),
                "snippet": doc.page_content[:200],
                "status": doc.metadata.get("status", ""),
            })

        prompt = ARTICLE_PROMPT.format(topic=topic, context=context)
        resp = self.article_llm.invoke(prompt)
        content = resp.content if hasattr(resp, 'content') else str(resp)
        return content, sources

    # ── 互动式普法：情景剧 / 海报 / 短片 ──

    def _invoke_json(self, prompt: str, retries: int = 1) -> dict:
        """调用 LLM 并解析 JSON 输出（剥 markdown 围栏、失败重试一次）"""
        resp = self.article_llm.invoke(prompt)
        text = resp.content if hasattr(resp, 'content') else str(resp)
        for attempt in range(retries + 1):
            try:
                return json.loads(self._strip_json_fences(text))
            except Exception:
                if attempt >= retries:
                    raise ValueError("LLM 未返回合法 JSON，请重试")
                resp = self.article_llm.invoke(
                    prompt + "\n\n注意：你上次的输出不是合法 JSON。请直接输出一个合法 JSON 对象：")
                text = resp.content if hasattr(resp, 'content') else str(resp)

    @staticmethod
    def _strip_json_fences(text: str) -> str:
        """剥掉 ```json 围栏，截取首个 { 到末个 } 的片段"""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("响应中未找到 JSON 对象")
        return text[start:end + 1]

    def _retrieve_context(self, search_query: str) -> str:
        docs = self.retriever.retrieve(search_query.strip(), final_top_k=6)
        if not docs:
            raise ValueError("知识库中未检索到与该主题相关的资料")
        return self.retriever.documents_as_context(docs)

    @staticmethod
    def _format_options(options: list) -> str:
        return "\n".join(f"- {o.get('key', '?')}：{o.get('text', '')}" for o in options)

    @staticmethod
    def _choice_label(options: list, choice: str) -> str:
        for o in options:
            if o.get("key") == choice:
                return f"{choice}（{o.get('text', '')}）"
        return choice

    def generate_scene_start(self, story: str, search_query: str = None) -> dict:
        """生成情景剧第 1 幕，返回 {scene_text, options, correct_key}"""
        context = self._retrieve_context(search_query or story)
        prompt = SCENE_START_PROMPT.format(story=story, scene_index=1, context=context)
        data = self._invoke_json(prompt)
        opts = data.get("options")
        if not data.get("scene_text") or not isinstance(opts, list) or len(opts) != 3:
            raise ValueError("剧本生成结果不完整，请重试")
        return data

    def generate_scene_next(self, story: str, search_query: str, prev_scene: str,
                            prev_options: list, prev_correct_key: str, choice: str,
                            is_ending: bool = False) -> dict:
        """生成判定（verdict）+ 下一幕（next）或结局（ending）"""
        context = self._retrieve_context(search_query or story)
        common = dict(
            story=story,
            prev_scene=prev_scene,
            prev_options=self._format_options(prev_options),
            choice=self._choice_label(prev_options, choice),
            prev_correct_key=prev_correct_key or "无",
            context=context,
        )
        if is_ending:
            prompt = SCENE_ENDING_PROMPT.format(**common)
        else:
            next_json = ('"next": {"scene_text": "下一幕剧情，80-150字", '
                         '"options": [{"key": "A", "text": "选项内容，≤20字"}, '
                         '{"key": "B", "text": "选项内容，≤20字"}, '
                         '{"key": "C", "text": "选项内容，≤20字"}], '
                         '"correct_key": "正确选项的key"}')
            prompt = SCENE_NEXT_PROMPT.format(next_json=next_json, **common)
        data = self._invoke_json(prompt)
        if not data.get("verdict"):
            raise ValueError("剧本生成结果不完整，请重试")
        return data

    def generate_poster(self, topic: str, search_query: str = None) -> dict:
        """生成普法海报文案，返回 {title, slogan, points, tip, law_basis}"""
        context = self._retrieve_context(search_query or topic)
        prompt = POSTER_PROMPT.format(topic=topic, context=context)
        data = self._invoke_json(prompt)
        if not data.get("title") or not isinstance(data.get("points"), list) or not data["points"]:
            raise ValueError("海报文案生成结果不完整，请重试")
        return data

    def generate_video(self, topic: str, search_query: str = None) -> dict:
        """生成普法短片分镜脚本，返回 {title, scenes: [{visual, subtitle}]}"""
        context = self._retrieve_context(search_query or topic)
        prompt = VIDEO_PROMPT.format(topic=topic, context=context)
        data = self._invoke_json(prompt)
        if not data.get("scenes") or len(data["scenes"]) < 3:
            raise ValueError("分镜脚本生成结果不完整，请重试")
        return data
