"""
批量清洗案例数据 — LLM生成标准化案情简述
"""
import csv
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from langchain_openai import ChatOpenAI

INPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "cases", "all_cases.csv")
OUTPUT_CSV = INPUT_CSV  # 原地覆盖


def summarize_case(llm, case):
    """用 LLM 生成标准化的案情简述"""
    raw_text = f"""
案号: {case.get('case_number', '')}
法院: {case.get('court', '')}
日期: {case.get('judge_date', '')}
原文内容: {case.get('case_content', '')[:1500]}
法院认为: {case.get('reasoning', '')[:500]}
判决结果: {case.get('judgment', '')[:300]}
"""

    prompt = f"""你是中国劳动法专家。请根据以下裁判文书内容，用 150-200 字简洁、清晰地概括本案的案情。只输出案情简述（不要编号、不要'案情简述：'前缀、不要换行），格式参考：

"劳动者XX自XX年XX月起在XX公司工作，担任XX职务。XX年XX月，公司以XX为由解除劳动合同（或拖欠工资/未签合同/工伤等）。劳动者申请劳动仲裁，请求XX。仲裁裁决XX。劳动者不服诉至法院。一审法院判决XX。公司/劳动者不服提起上诉/申请再审。"

请概括以下案件：
{raw_text}
"""

    try:
        resp = llm.invoke(prompt, max_tokens=300, temperature=0.1)
        summary = resp.content.strip() if hasattr(resp, 'content') else str(resp).strip()
        if len(summary) < 30:
            return None
        return summary
    except Exception as e:
        print(f"  LLM error: {e}")
        return None


def main():
    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    print(f"Loading {len(rows)} cases...")

    llm_kwargs = dict(
        model=Config.LLM_MODEL,
        api_key=Config.LLM_API_KEY,
        temperature=0.1,
        max_tokens=300,
    )
    if Config.LLM_BASE_URL:
        llm_kwargs["base_url"] = Config.LLM_BASE_URL
    llm = ChatOpenAI(**llm_kwargs)

    updated = 0
    for i, row in enumerate(rows, 1):
        # 跳过已有好数据的（case_content 以正常中文开头且长度合适）
        current = row.get('case_content', '')
        if len(current) > 100 and len(current) < 600 and not current.startswith('为，'):
            continue

        summary = summarize_case(llm, row)
        if summary:
            row['case_content'] = summary
            updated += 1
            preview = summary[:80]
            print(f"  [{i}/{len(rows)}] {preview}...")
        else:
            print(f"  [{i}/{len(rows)}] SKIP (LLM failed)")

    # 写回 CSV
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone: {updated}/{len(rows)} cases summarized")


if __name__ == "__main__":
    main()
