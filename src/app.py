"""
劳动法 RAG 智能咨询系统 — Gradio 主入口

启动方式：
    cd D:/My wordl four/thesis-rag-labour-law
    .venv/Scripts/activate
    python src/app.py
"""

import gradio as gr

from src.config import Config
from src.database.neo4j_client import Neo4jClient
from src.rag.loader import LegalDocumentLoader
from src.rag.retriever import HybridRetriever
from src.rag.chain import LabourLawRAG


# ── 全局初始化（启动时执行一次）──────────────────────

print("🔌 连接 Neo4j ...")
neo4j = Neo4jClient()
stats = {"statutes": 0, "articles": 0, "cases": 0, "issues": 0, "courts": 0}
loader = None
if neo4j.check_connection():
    print("  ✅ Neo4j 连接成功")
    neo4j.init_schema()
    stats = neo4j.get_stats()
    print(f"  📊 图谱: {stats['statutes']} 部法律, {stats['articles']} 条条文, "
          f"{stats['cases']} 个案例, {stats['issues']} 个争议焦点")
else:
    print("  ⚠️ Neo4j 连接失败，图谱检索功能不可用。请确认 Neo4j 已启动。")

print("📚 初始化检索器 ...")
retriever = HybridRetriever(neo4j)

# 尝试加载已有向量库，否则从文件构建
try:
    retriever.load_index()
    print("  ✅ 向量索引已加载")
except Exception:
    print("  ⚠️ 向量索引不存在，从数据文件构建 ...")
    loader = LegalDocumentLoader()
    docs = loader.load_all()
    if docs:
        retriever.build_index(docs)
        print(f"  ✅ 向量索引已构建，共 {len(docs)} 份文档")
    else:
        print("  ⚠️ data/raw 目录为空，请先添加法律文本和案例数据。")
        print("     WK1 数据收集完成后，将 txt 和 json 文件放入 src/data/raw/ 对应子目录")

# ── 自动导入法条到 Neo4j ──
print("🔗 检查 Neo4j 法条数据 ...")
if neo4j.check_connection() and stats['statutes'] == 0:
    loader = LegalDocumentLoader()
    docs = loader.load_all()
    statute_docs = [d for d in docs if d.metadata.get("doc_type") == "statute"]
    if statute_docs:
        print(f"  📥 正在将 {len(statute_docs)} 部法律导入 Neo4j ...")
        for doc in statute_docs:
            law_name = doc.metadata.get("law_name", "未知法律")
            content = doc.page_content
            # 简单按 "第X条" 拆分条文
            import re
            parts = re.split(r'(第[一二三四五六七八九十百千\d]+条)', content)
            articles = []
            for i in range(1, len(parts) - 1, 2):
                article_id = parts[i]
                article_content = parts[i + 1].strip()[:500] if i + 1 < len(parts) else ""
                articles.append({"id": article_id, "content": article_content})
            if articles:
                try:
                    neo4j.import_statute(
                        law_name, articles,
                        publish_date=doc.metadata.get("publish_date", ""),
                        effective_date=doc.metadata.get("effective_date", ""),
                        status=doc.metadata.get("status", "现行有效"),
                    )
                    print(f"    ✅ {law_name}: {len(articles)} 条")
                except Exception as e:
                    print(f"    ⚠️ {law_name} 导入失败: {e}")
        stats = neo4j.get_stats()
        print(f"  📊 图谱更新: {stats['statutes']} 部法律, {stats['articles']} 条条文")

# ── 自动导入案例到 Neo4j ──
if neo4j.check_connection() and stats['cases'] == 0:
    if loader is None:
        loader = LegalDocumentLoader()
    case_data = loader.load_cases_json()
    if case_data:
        print(f"  📥 正在将 {len(case_data)} 个案例导入 Neo4j ...")
        for i, case in enumerate(case_data, 1):
            case.setdefault("court", "未知法院")
            case.setdefault("judge_date", "")
            case.setdefault("case_content", "")
            case.setdefault("issues", case.get("keywords", "劳动争议"))
            case.setdefault("reasoning", "")
            case.setdefault("judgment", "")
            case.setdefault("legal_basis", "")
            case.setdefault("keywords", case.get("keywords", "劳动争议"))
            for key in ["issues", "legal_basis", "keywords"]:
                val = case.get(key, "")
                if isinstance(val, str) and ";" in val:
                    case[key] = [v.strip() for v in val.split(";") if v.strip()]
                elif isinstance(val, str) and val:
                    case[key] = [val.strip()]
                else:
                    case[key] = val if isinstance(val, list) else []
            try:
                neo4j.import_case(case)
                if i % 10 == 0:
                    print(f"    ... {i}/{len(case_data)}")
            except Exception as e:
                print(f"    ⚠️ {case.get('case_number', '?')} 导入失败: {e}")
        stats = neo4j.get_stats()
        print(f"  📊 图谱更新: {stats['statutes']} 部法律, {stats['articles']} 条条文, {stats['cases']} 个案例")

print("🧠 初始化 RAG 问答链 ...")
rag = LabourLawRAG(retriever)
print("  ✅ 问答链就绪")

print("=" * 60)
print("🚀 启动 Gradio 界面 ...")


# ── 对话处理 ─────────────────────────────────────────

def chat(message: str, history: list) -> str:
    """处理用户提问"""
    if not message.strip():
        return "请输入您的劳动法问题。"
    return rag.query(message)


# ── 数据导入接口 ─────────────────────────────────────

def import_case_to_neo4j(case_json: str) -> str:
    """通过界面手动录入案例"""
    import json
    try:
        case = json.loads(case_json)
        required = ["case_number", "case_content", "judgment"]
        missing = [k for k in required if k not in case]
        if missing:
            return f"❌ 缺少必填字段：{', '.join(missing)}"

        case.setdefault("court", "未知法院")
        case.setdefault("judge_date", "")
        case.setdefault("issues", [])
        case.setdefault("reasoning", "")
        case.setdefault("legal_basis", [])
        case.setdefault("keywords", [])

        neo4j.import_case(case)
        return f"✅ 案例 {case['case_number']} 已成功导入 Neo4j！"
    except json.JSONDecodeError as e:
        return f"❌ JSON 格式错误：{e}"
    except Exception as e:
        return f"❌ 导入失败：{e}"


def rebuild_index() -> str:
    """重建向量索引"""
    try:
        loader = LegalDocumentLoader()
        docs = loader.load_all()
        if not docs:
            return "⚠️ data/raw 目录为空，没有可索引的文档。"
        retriever.build_index(docs)
        return f"✅ 向量索引已重建，共索引 {len(docs)} 份文档。"
    except Exception as e:
        return f"❌ 索引重建失败：{e}"


# ── Gradio 界面 ──────────────────────────────────────

EXAMPLE_QUESTIONS = [
    "公司无故辞退员工，应该怎么维权？",
    "工伤认定的标准和流程是什么？",
    "竞业限制协议不给补偿金，是否有效？",
    "加班费的计算基数怎么确定？加班费追索时效是多久？",
    "试用期最长可以约定多久？试用期工资有什么规定？",
    "公司拖欠工资，员工可以立即解除合同并要求赔偿吗？",
    "孕期被公司降薪调岗，是否违法？",
    "未签劳动合同，如何确认劳动关系？",
]

with gr.Blocks(title="劳动法 RAG 智能咨询系统") as demo:

    gr.Markdown("""
    # ⚖️ 劳动法 RAG 智能咨询系统
    ### 基于检索增强生成（RAG）+ 知识图谱的劳动法专业问答

    支持：**法律法规解读** · **司法解释理解** · **劳动争议案例分析** · **法律适用建议**
    """)

    with gr.Tab("💬 法律咨询"):
        with gr.Row():
            with gr.Column(scale=2):
                gr.ChatInterface(
                    fn=chat,
                    title="劳动法智能问答",
                    examples=EXAMPLE_QUESTIONS,
                )

            with gr.Column(scale=1):
                gr.Markdown("""
                ### 📊 知识库状态
                """)
                stats_md = gr.Markdown("正在加载统计信息...")
                refresh_btn = gr.Button("🔄 刷新统计", variant="secondary", size="sm")

                gr.Markdown("""
                ---
                ### 🔍 支持的功能
                - ✅ 法条原文检索（向量语义匹配）
                - ✅ 司法解释关联引用
                - ✅ 相似案例图谱查询
                - ✅ 争议焦点定性分析
                - ✅ 多来源混合检索融合
                """)

                gr.Markdown("""
                ---
                ### ⚠️ 免责声明
                本系统仅供学习研究参考，**不构成法律意见**。
                如需法律帮助，请咨询专业律师。
                """)

    with gr.Tab("📝 数据管理"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 手动录入案例（JSON 格式）")
                gr.Markdown("""
                必填字段：`case_number`、`case_content`、`judgment`
                可选字段：`court`、`judge_date`、`issues`、`reasoning`、`legal_basis`、`keywords`
                """)
                case_input = gr.Textbox(
                    label="案例 JSON",
                    placeholder='{"case_number": "(2024)京0105民初888号", "case_content": "...", "judgment": "...", "court": "...", "keywords": ["..."]}',
                    lines=10,
                )
                import_btn = gr.Button("📥 导入 Neo4j", variant="primary")
                import_output = gr.Textbox(label="导入结果", lines=3)

            with gr.Column():
                gr.Markdown("### 向量索引管理")
                gr.Markdown("数据文件更新后，点击重建索引。")
                rebuild_btn = gr.Button("🔄 重建向量索引", variant="secondary")
                rebuild_output = gr.Textbox(label="操作结果", lines=3)

    # ── 事件绑定 ──

    def get_stats_text():
        try:
            s = neo4j.get_stats()
            return f"""
            - 📜 法律法规：**{s['statutes']}** 部
            - 📄 条文：**{s['articles']}** 条
            - 📝 案例：**{s['cases']}** 个
            - 🏛️ 法院：**{s['courts']}** 家
            - 🏷️ 争议焦点：**{s['issues']}** 个
            """
        except Exception:
            return "⚠️ Neo4j 未连接"

    refresh_btn.click(fn=get_stats_text, outputs=stats_md)
    import_btn.click(fn=import_case_to_neo4j, inputs=case_input, outputs=import_output)
    rebuild_btn.click(fn=rebuild_index, outputs=rebuild_output)

    # 页面加载时自动刷新统计
    demo.load(fn=get_stats_text, outputs=stats_md)


if __name__ == "__main__":
    Config.validate()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),
    )
