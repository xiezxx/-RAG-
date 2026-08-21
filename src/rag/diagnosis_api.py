"""
智能案情诊断 API
用户输入案情要素（纠纷类型/工龄/月工资/合同情况/描述）→ RAG 检索相关法条
→ LLM 生成结构化诊断报告（问题清单/法律依据/风险等级/行动建议）+ 程序化赔偿估算
赔偿金额由 Python 按《劳动合同法》规则计算后注入 Prompt，避免 LLM 算术错误。
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])

# 由 rag_service 启动时注入
_rag = None


def set_rag(rag):
    global _rag
    _rag = rag


# ── 纠纷类型 → 检索关键词 ──
REASON_KEYWORDS = {
    "被辞退": "辞退 解除劳动合同 经济补偿 赔偿金",
    "协商解除": "协商解除劳动合同 经济补偿",
    "被迫离职": "被迫解除劳动合同 未足额支付劳动报酬 经济补偿",
    "主动离职": "劳动者解除劳动合同 经济补偿",
    "拖欠工资": "拖欠工资 劳动报酬 克扣工资 赔偿",
    "加班纠纷": "加班费 加班工资 延长工作时间",
    "工伤": "工伤认定 工伤保险 赔偿",
    "试用期纠纷": "试用期 解除劳动合同 不符合录用条件",
    "孕期纠纷": "女职工 怀孕 产假 解除劳动合同 保护",
    "未签合同": "未签订劳动合同 双倍工资",
    "其他": "劳动纠纷 劳动者权益 赔偿",
}

DIAGNOSIS_PROMPT = """你是一名资深劳动法律师，正在为普通劳动者做免费案情初诊。请基于用户提供的案情要素和检索到的法律资料，输出一份**结构化诊断报告**。

## 案情要素
- 纠纷类型：{reason}
- 工龄：{years} 年
- 月工资：{monthly_wage} 元
- 是否签订书面劳动合同：{has_contract}
- 案情描述：{description}

## 检索到的法律资料（RAG 检索结果，引用条文必须出自这里或《劳动合同法》《劳动法》等公开现行法律）
{context}

## 系统已按《劳动合同法》第47条等规则计算的赔偿估算（金额只引用这些数字，不要自己重算）
- 经济补偿金 N ≈ {est_N} 元（工龄每满一年计一个月工资，六个月以上不满一年按一年计，不满六个月计半个月，上限12年）
- 代通知金情形 N+1 ≈ {est_N1} 元（用人单位未提前30日书面通知解除）
- 违法解除赔偿金 2N ≈ {est_2N} 元（违法解除/终止劳动合同的双倍赔偿）

## 输出要求
只输出一个 JSON 对象（不要 Markdown 代码块围栏，不要任何解释文字），结构如下：
{{
  "summary": "一句话案情摘要",
  "issues": [
    {{
      "issue": "问题点名称（如：解除是否违法）",
      "risk": "高/中/低",
      "analysis": "结合法条的法律分析，80-150字，必须写明依据的条文号",
      "basis": ["《劳动合同法》第X条"],
      "suggestion": "针对该问题点的具体建议"
    }}
  ],
  "warnings": ["风险提示1", "风险提示2"],
  "next_steps": ["第一步行动建议", "第二步行动建议", "第三步行动建议"]
}}

规则：
1. issues 2-5 条，按重要性排序；risk 只能是 高/中/低 三档
2. basis 中的条文必须真实存在（优先引用检索资料中出现的条文）；资料中没有相关条文时，可引用《劳动合同法》《劳动法》等现行法律中你确信存在的条文，严禁编造不存在的条号
3. analysis 中涉及赔偿金额时，只使用上面给出的 N/N+1/2N 估算数字
4. next_steps 给出可执行的具体步骤（如"保留哪些证据""向哪里投诉""仲裁时效提醒"）
5. 语气客观中立，结尾提醒仅供参考，不构成正式法律意见
"""


# ── 程序化赔偿估算 ──
def _compute_estimate(years: float, monthly_wage: float) -> Dict:
    """按《劳动合同法》第47条计算经济补偿月数（工龄×月工资）"""
    y = max(0.0, float(years))
    wage = max(0.0, float(monthly_wage))
    if y <= 0 or wage <= 0:
        return {
            "N": 0.0, "N_plus_1": 0.0, "2N": 0.0,
            "months": 0.0,
            "note": "工龄与月工资均为 0，无法估算，请完善信息",
        }
    if y >= 1:
        full = int(y)
        frac = y - full
        months = full + (1.0 if frac >= 0.5 else (0.5 if frac > 0 else 0.0))
    else:
        months = 1.0 if y >= 0.5 else 0.5
    months = min(months, 12.0)  # 经济补偿年限上限 12 年（高收入者另有社平工资3倍封顶，此处简化）
    n = round(months * wage, 2)
    return {
        "N": n,
        "N_plus_1": round(n + wage, 2),
        "2N": round(2 * n, 2),
        "months": months,
        "note": "估算基于工龄×月工资（未计入社平工资3倍封顶等特殊情形），实际金额以仲裁/法院认定为准",
    }


# ── 请求/响应模型 ──
class DiagnosisRequest(BaseModel):
    description: str = Field(..., min_length=5, max_length=2000, description="案情自由描述")
    reason: str = Field(default="被辞退", max_length=20, description="纠纷类型")
    years: float = Field(default=1.0, ge=0, le=50, description="工龄（年，支持小数）")
    monthly_wage: float = Field(default=5000.0, ge=0, le=1000000, description="月工资（元）")
    has_contract: bool = Field(default=True, description="是否签订书面劳动合同")


# ── API ──
@router.post("")
def diagnose(request: DiagnosisRequest):
    # 同步 def：LLM 阻塞调用由 FastAPI 线程池执行，不阻塞事件循环
    if _rag is None:
        raise HTTPException(status_code=503, detail="RAG 引擎未就绪")

    # 1. 程序化赔偿估算
    estimation = _compute_estimate(request.years, request.monthly_wage)

    # 2. RAG 检索相关法条
    search_query = f"{REASON_KEYWORDS.get(request.reason, '劳动纠纷')} {request.description[:80]}"
    docs = []
    context = "未检索到相关法律资料。"
    try:
        docs = _rag.retriever.retrieve(search_query, final_top_k=6)
        if docs:
            context = _rag.retriever.documents_as_context(docs)
    except Exception:
        pass

    # 3. LLM 生成结构化诊断报告
    prompt = DIAGNOSIS_PROMPT.format(
        reason=request.reason,
        years=request.years,
        monthly_wage=request.monthly_wage,
        has_contract="已签订" if request.has_contract else "未签订",
        description=request.description,
        context=context,
        est_N=estimation["N"],
        est_N1=estimation["N_plus_1"],
        est_2N=estimation["2N"],
    )
    report = _rag._invoke_json(prompt, retries=1)
    if not report:
        raise HTTPException(status_code=502, detail="诊断报告生成失败，请稍后重试")

    # 4. 组装来源
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
        sources.append({
            "type": type_map.get(doc_type, "unknown"),
            "title": doc.metadata.get("law_name",
                     doc.metadata.get("case_number",
                     doc.metadata.get("title", "未知来源"))),
            "snippet": doc.page_content[:200],
            "status": doc.metadata.get("status", "") or doc.metadata.get("status_label", ""),
        })

    return {
        "summary": report.get("summary", ""),
        "issues": report.get("issues") or [],
        "warnings": report.get("warnings") or [],
        "next_steps": report.get("next_steps") or [],
        "estimation": estimation,
        "search_query": search_query,
        "sources": sources,
    }
