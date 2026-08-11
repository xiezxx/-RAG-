"""
批量导入裁判文书 — 从 D:\case_txt .txt 文件提取字段写入 CSV
v2: 拆分文档为 案例内容/法院认为/判决结果 三部分
"""
import csv
import os
import re

TXT_DIR = r"D:\case_txt"
OUTPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "cases", "all_cases.csv")

CATEGORY_MAP = {}

def _scan_categories():
    """从 TXT_DIR 文件名推断类别"""
    cats = {}
    if not os.path.exists(TXT_DIR):
        return cats
    for f in os.listdir(TXT_DIR):
        if not f.endswith('.txt'): continue
        for kw in ['劳动合同解除','劳动报酬','工伤赔偿','确认劳动关系','女职工权益','社会保险','竞业限制','其他']:
            if kw in f:
                cats[f] = kw
                break
        if f not in cats:
            cats[f] = '其他'
    return cats

CATEGORY_MAP = _scan_categories()

KW_MAP = {
    "劳动合同解除": "违法解除;赔偿金;经济补偿;解除劳动合同;辞退;开除",
    "劳动报酬": "劳动报酬;加班费;工资;拖欠工资;年终奖",
    "工伤赔偿": "工伤;工伤保险;工伤认定;工伤赔偿",
    "确认劳动关系": "确认劳动关系;事实劳动关系;劳动关系",
    "女职工权益": "女职工;孕期;产假;就业歧视;女职工权益",
    "社会保险": "社会保险;社保;养老保险;失业保险;医疗保险",
    "竞业限制": "竞业限制;竞业限制补偿;商业秘密",
    "其他": "劳动争议;劳动纠纷",
}


def _read_text(filepath):
    for enc in ["gbk", "utf-8", "gb18030"]:
        try:
            with open(filepath, "r", encoding=enc) as f:
                text = f.read()
            if len(text.strip()) > 100:
                return text.strip()
        except:
            continue
    return ""


def _chinese_to_num(cn: str) -> str:
    """二〇二五年十一月二十六日 → 2025-11-26"""
    dmap = {'〇':'0','O':'0','o':'0','一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9','零':'0'}

    def _parse_num(s):
        """十一→11, 十三→13, 五→05"""
        s = s.replace('十', '')
        for k,v in dmap.items(): s = s.replace(k, v)
        if not s: s = '10'
        if len(s) == 1: s = '0' + s
        return s

    result = cn
    m = re.match(r'([二〇O一二三四五六七八九十\d]{4})年', result)
    if m:
        y = m.group(1)
        for k,v in dmap.items(): y = y.replace(k, v)
        result = result.replace(m.group(0), y + '-')
    m = re.search(r'([一二三四五六七八九十\d]+)月', result)
    if m:
        result = result.replace(m.group(0), _parse_num(m.group(1)) + '-')
    m = re.search(r'([一二三四五六七八九十\d]+)日', result)
    if m:
        result = result.replace(m.group(0), _parse_num(m.group(1)))
    return result


def extract(text, filename):
    """从裁判文书文本提取字段 — v2: 案例内容/法院认为/判决结果 三分法"""
    text = re.sub(r'[\t ]+', ' ', text).strip()
    # 去掉末尾的法律条文附录（通常是原文照搬法条）
    category = CATEGORY_MAP.get(filename, '其他')

    # ══════ 1. 案号 ══════
    case_number = ""
    for pat in [r'[（(]\d{4}[）)][^。,\n]{0,30}号', r'案\s*号[：:]\s*(\S+)']:
        m = re.search(pat, text)
        if m:
            case_number = m.group(0)
            break

    # ══════ 2. 法院 ══════
    court = ""
    m = re.search(r'([^，。,　\s]{2,20}(?:人民法院|中级人民法院|高级人民法院|最高人民法院))', text)
    if m:
        court = m.group(1)

    # ══════ 3. 日期 ══════
    judge_date = ""
    cn_date_pat = r'[二〇O一二三四五六七八九十\d]{4}年[一二三四五六七八九十\d]+月[一二三四五六七八九十\d]+日'

    for end_marker in ['书记员', '法官助理', '审判员', '审判长']:
        idx = text.rfind(end_marker)
        if idx > 0:
            tail = text[idx:idx+200]
            m = re.search(cn_date_pat, tail)
            if m:
                judge_date = _chinese_to_num(m.group(0))
                break

    if not judge_date:
        all_dates = re.findall(cn_date_pat, text)
        if all_dates:
            judge_date = _chinese_to_num(all_dates[-1])

    # ══════ 4. 法院认为 (reasoning) ══════
    reasoning = ""
    reasoning_start = -1
    reasoning_end = -1

    # 找"本院认为"的起始位置
    for pat in [
        r'本院认为[：:,，]?',
        r'本院经审查认为[：:,，]?',
        r'本院经审理认为[：:,，]?',
        r'本院再审认为[：:,，]?',
        r'本院审理认为[：:,，]?',
        r'本院综合审查认为[：:,，]?',
    ]:
        m = re.search(pat, text)
        if m:
            reasoning_start = m.start()
            break

    # 找"判决如下/裁定如下"的位置（作为法院认为的结束标记）
    judgment_keyword = ""
    m_judge = re.search(r'(判决如下|裁定如下)[：:]?', text)
    if m_judge:
        reasoning_end = m_judge.start()
        judgment_keyword = m_judge.group(1)

    if reasoning_start > 0:
        if reasoning_end > reasoning_start:
            raw_reasoning = text[reasoning_start:reasoning_end].strip()
        else:
            # 没有明确的"判决如下"，取"本院认为"之后到文末前800字
            raw_reasoning = text[reasoning_start:].strip()
            # 截断在判决结果前（如果有"驳回"、"维持"、"撤销"等判决特征在末尾）
            # 尝试找 "依照...判决如下" 模式
            m2 = re.search(r'(依照|综上|据此)[^。]{0,50}(判决如下|裁定如下)', raw_reasoning)
            if m2:
                raw_reasoning = raw_reasoning[:m2.start()].strip()

        # 清理：去掉开头重复的"本院认为"标记
        reasoning = re.sub(r'^本院(?:经(?:审查|审理)|再审|综合审查)?认为[：:,，]?\s*', '', raw_reasoning)
        # 不截断，保留完整法院认为
    else:
        reasoning = ""

    # ══════ 5. 判决结果 (judgment) ══════
    judgment = ""
    if judgment_keyword and reasoning_end > 0:
        # 从"判决如下/裁定如下"之后开始提取
        after_keyword = text[m_judge.end():]

        # 找到判决结果的结束位置（审判长/审判员/书记员/本判决/本裁定/如不服）
        end_patterns = [
            r'\n\s*(?:审\s*判\s*长|审\s*判\s*员|书\s*记\s*员|法\s*官\s*助\s*理)',
            r'本判决[^书]', r'本裁定[^书]',
            r'如不服本', r'逾期本',
            r'本案案件受理费', r'一审案件受理费',
        ]
        min_end = len(after_keyword)
        for ep in end_patterns:
            m_end = re.search(ep, after_keyword)
            if m_end and m_end.start() < min_end:
                min_end = m_end.start()

        if min_end > 50:
            judgment = after_keyword[:min_end].strip()
        else:
            judgment = after_keyword[:1500].strip()

        # 清理多余空白
        judgment = re.sub(r'\s+', ' ', judgment).strip()
        judgment = judgment[:2000]

    if len(judgment) < 15:
        # 兜底：尝试从文末提取
        tail = text[-2000:]
        m_tail = re.search(r'((?:判决如下|裁定如下)[：:]?.+)', tail, re.DOTALL)
        if m_tail:
            judgment = m_tail.group(1).strip()[:1500]

    # ══════ 6. 案例内容 (case_content) = 全文 - 法院认为 - 判决结果 ══════
    case_content = ""

    if reasoning_start > 0 and reasoning_end > reasoning_start:
        # 正常情况：有三段
        before_reasoning = text[:reasoning_start].strip()
        after_judgment = text[m_judge.end():].strip() if m_judge else ""

        # after_judgment 中去除判决主文（已在judgment中提取），只保留尾部程序性内容
        # 找到审判人员标记，之前的内容如果没在judgment中则保留
        tail_start = -1
        for ep in [r'\n\s*审\s*判\s*长', r'\n\s*审\s*判\s*员', r'\n\s*书\s*记\s*员']:
            m_t = re.search(ep, after_judgment)
            if m_t:
                tail_start = m_t.start()
                break
        if tail_start > 0:
            # 取从 "判决如下" 之后到 审判人员之前 作为 judgment（上面已处理）
            # 保留审判人员及日期信息放入案例内容尾部
            case_tail = after_judgment[tail_start:].strip()
        else:
            case_tail = ""

        case_content = before_reasoning
        if case_tail:
            case_content = case_content + "\n\n" + case_tail

    elif reasoning_start > 0:
        # 有"本院认为"但没找到"判决如下"
        case_content = text[:reasoning_start].strip()
    else:
        # 完全找不到"本院认为"和"判决如下"
        case_content = text

    # 清理案例内容
    case_content = case_content.strip()

    # ══════ 7. 引用法条 ══════
    law_refs = re.findall(
        r'《[^》]+》\s*第[一二三四五六七八九十百千\d]+条'
        r'(?:(?:[、，,及和]|以及)\s*第[一二三四五六七八九十百千\d]+条)*',
        text
    )
    legal_basis = "; ".join(law_refs[:15]) if law_refs else ""

    keywords = KW_MAP.get(category, "劳动争议")

    return {
        "case_number": case_number or filename[:50].replace(".txt",""),
        "court": court or "未知法院",
        "judge_date": judge_date or "",
        "case_content": case_content,
        "issues": keywords,
        "reasoning": reasoning or "",
        "judgment": judgment or "",
        "legal_basis": legal_basis,
        "keywords": keywords,
    }


def main():
    if not os.path.exists(TXT_DIR):
        print(f"TXT not found: {TXT_DIR}")
        return

    txt_files = [f for f in os.listdir(TXT_DIR) if f.endswith(".txt")]
    print(f"源文档: {len(txt_files)} 个")
    print()

    rows = []
    stats = {"total": 0, "has_reasoning": 0, "has_judgment": 0, "has_content": 0}

    for i, filename in enumerate(txt_files, 1):
        filepath = os.path.join(TXT_DIR, filename)
        text = _read_text(filepath)
        if not text:
            print(f"  [{i}] {filename[:50]}... EMPTY")
            continue
        row = extract(text, filename)
        rows.append(row)
        stats["total"] += 1
        if row['reasoning']: stats["has_reasoning"] += 1
        if row['judgment']: stats["has_judgment"] += 1
        if row['case_content']: stats["has_content"] += 1

        cn_short = row['case_number'][:25]
        r_len = len(row['reasoning'])
        j_len = len(row['judgment'])
        c_len = len(row['case_content'])
        print(f"  [{i:2d}] {cn_short:<26} | 内容{c_len:>5}字 | 认为{r_len:>5}字 | 判决{j_len:>5}字")

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "case_number", "court", "judge_date",
            "case_content", "issues", "reasoning", "judgment",
            "legal_basis", "keywords"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone: {stats['total']} cases -> {OUTPUT_CSV}")
    print(f"   has_reasoning: {stats['has_reasoning']}/{stats['total']}")
    print(f"   has_judgment: {stats['has_judgment']}/{stats['total']}")
    print(f"   has_content: {stats['has_content']}/{stats['total']}")


if __name__ == "__main__":
    main()
