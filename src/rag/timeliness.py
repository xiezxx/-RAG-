"""
时效感知模块 — 时间表达式解析、版本匹配、结果过滤与标注
"""
import re
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from langchain_core.documents import Document


# ── 时间表达式解析 ────────────────────────────────────

# 常见的时效相关时间词
TIME_PATTERNS = [
    (r'(\d{4})年(?:\d{1,2}月)?(?:\d{1,2}日)?', 'absolute'),   # 2020年 / 2020年6月
    (r'(\d{4})-(\d{2})(?:-(\d{2}))?', 'absolute'),               # 2020-06 / 2020-06-15
    (r'现在|当前|目前|最新|现行|如今', 'now'),
    (r'去年', 'last_year'),
    (r'今年', 'this_year'),
    (r'前年', 'year_before_last'),
    (r'(\d+)年前', 'years_ago'),
    (r'(\d+)个月前', 'months_ago'),
    (r'最近|近期|近来', 'recent'),
    (r'过去|以往|以前|之前|原来|原', 'past'),
    (r'旧法|旧版|老法|原法|修订前', 'old_version'),
    (r'新法|新版|修订后|修正后|现行法', 'new_version'),
]

STATUS_LABELS = {
    "现行有效": "🟢 现行有效",
    "已被修订": "🟡 已被修订",
    "已废止": "🔴 已废止",
    "尚未生效": "🔵 尚未生效",
    "效力未知": "⚪ 效力未知",
}

STATUS_PRIORITY = {
    "现行有效": 0,
    "尚未生效": 1,
    "效力未知": 2,
    "已被修订": 3,
    "已废止": 4,
}


def parse_time_reference(query: str) -> Tuple[Optional[str], Optional[str]]:
    """从用户问题中解析时间参考
    Returns: (reference_date: YYYY-MM-DD, time_hint: str)
    """
    # 1. 检查绝对日期
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', query)
    if m:
        return (f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}",
                f"{m.group(1)}年{m.group(2)}月{m.group(3)}日")

    m = re.search(r'(\d{4})年(\d{1,2})月', query)
    if m:
        return (f"{m.group(1)}-{int(m.group(2)):02d}-01",
                f"{m.group(1)}年{m.group(2)}月")

    m = re.search(r'(\d{4})年', query)
    if m:
        return (f"{m.group(1)}-01-01", f"{m.group(1)}年")

    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', query)
    if m:
        return (f"{m.group(1)}-{m.group(2)}-{m.group(3)}",
                f"{m.group(1)}年{int(m.group(2))}月{int(m.group(3))}日")

    # 2. 相对时间
    now = datetime.now()
    if any(w in query for w in ["去年"]):
        ref = now.replace(year=now.year - 1)
        return (ref.strftime("%Y-%m-%d"), "去年")
    if any(w in query for w in ["前年"]):
        ref = now.replace(year=now.year - 2)
        return (ref.strftime("%Y-%m-%d"), "前年")

    m = re.search(r'(\d+)年前', query)
    if m:
        ref = now.replace(year=now.year - int(m.group(1)))
        return (ref.strftime("%Y-%m-%d"), f"{m.group(1)}年前")

    m = re.search(r'(\d+)个月前', query)
    if m:
        ref = now - timedelta(days=int(m.group(1)) * 30)
        return (ref.strftime("%Y-%m-%d"), f"{m.group(1)}个月前")

    # 3. 偏好信号
    if any(w in query for w in ["最新", "现行", "当前", "现在", "目前"]):
        return (now.strftime("%Y-%m-%d"), "当前")

    if any(w in query for w in ["旧法", "旧版", "老法", "原法", "修订前", "修正前"]):
        return ("1900-01-01", "历史版本")

    if any(w in query for w in ["新法", "新版", "修订后", "修正后", "现行法"]):
        return (now.strftime("%Y-%m-%d"), "现行版本")

    # 4. 默认：当前
    return (None, None)


def is_effective(doc: Document, reference_date: Optional[str] = None) -> Tuple[bool, str]:
    """判断文档在当前（或指定日期）是否有效
    Returns: (is_effective: bool, reason: str)
    """
    meta = doc.metadata
    status = meta.get("status", "效力未知")
    eff_date = meta.get("effective_date", "")
    exp_date = meta.get("expiry_date", "")

    if not reference_date:
        # 默认：只看状态标签
        if status == "现行有效":
            return (True, "")
        elif status == "已被修订":
            return (True, "⚠️ 该条文已被修订，请核实最新版本")
        elif status == "已废止":
            return (False, "❌ 该条文已废止，仅供参考")
        elif status == "尚未生效":
            return (False, "🔵 该条文尚未生效")
        else:
            return (True, "⚪ 效力状态未知，请核实")

    # 有时效参考日期
    try:
        ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")
    except ValueError:
        return (True, "")

    if eff_date:
        try:
            eff_dt = datetime.strptime(eff_date, "%Y-%m-%d")
            if eff_dt > ref_dt:
                return (False, f"🔵 该条文于{eff_date}生效，在参考日期{reference_date}之后")
        except ValueError:
            pass

    if exp_date:
        try:
            exp_dt = datetime.strptime(exp_date, "%Y-%m-%d")
            if exp_dt < ref_dt:
                return (False, f"❌ 该条文已于{exp_date}失效")
        except ValueError:
            pass

    if status == "现行有效":
        return (True, "")
    elif status == "已被修订":
        return (True, "⚠️ 该条文已被修订")
    elif status == "已废止":
        return (False, "❌ 该条文已废止")

    return (True, "")


def filter_by_timeliness(
    docs: List[Document],
    reference_date: Optional[str] = None,
    prefer_current: bool = True,
) -> List[Document]:
    """根据时效过滤并标注文档
    - 现行有效：保留，标注 🟢
    - 已被修订：保留，标注 🟡
    - 已废止：降到底部/移除，标注 🔴
    - 尚未生效：保留但标注 🔵
    """
    if not docs:
        return docs

    scored: List[Tuple[Document, int, str]] = []

    for doc in docs:
        effective, reason = is_effective(doc, reference_date)
        status = doc.metadata.get("status", "效力未知")
        priority = STATUS_PRIORITY.get(status, 2)

        # 对失效文档：若不指定历史查询，则降级但不删除（保留参考价值）
        if not effective and prefer_current and not reference_date:
            priority += 10

        scored.append((doc, priority, reason))

    # 排序：优先级低的在前（现行有效优先）
    scored.sort(key=lambda x: x[1])

    # 附加时效标注
    result = []
    for doc, pri, reason in scored:
        status = doc.metadata.get("status", "")
        label = STATUS_LABELS.get(status, "")
        if label:
            doc.metadata["status_label"] = label
        if reason:
            doc.metadata["timeliness_note"] = reason
        result.append(doc)

    return result


def get_timeliness_context(docs: List[Document]) -> str:
    """生成时效上下文，用于在 LLM 回答中展示版本信息"""
    if not docs:
        return ""

    statuses = set()
    has_expired = False
    has_revised = False

    for doc in docs:
        s = doc.metadata.get("status", "")
        if s == "已废止":
            has_expired = True
        elif s == "已被修订":
            has_revised = True
        statuses.add(s)

    notes = []
    if has_expired:
        notes.append("检索结果中包含已废止条文，已标注仅供参考。")
    if has_revised:
        notes.append("部分条文已被修订，请以最新版本为准。")
    if "效力未知" in statuses and len(statuses) == 1:
        notes.append("部分条文效力状态不明，建议核实。")

    return " ".join(notes) if notes else ""
