# -*- coding: utf-8 -*-
"""临时验证脚本：检索过程可视化 / 检索模式 / 消融数据 / 案情诊断（直测 Python）"""
import json
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8011"


def get(path):
    t0 = time.time()
    r = requests.get(BASE + path, timeout=60)
    print(f"\n== GET {path} -> {r.status_code} ({time.time()-t0:.0f}s) ==")
    return r.json() if r.status_code == 200 else r.text


def sse_post(path, payload, timeout=240):
    """POST 并解析 SSE 流，返回 (文本, sources, trace)"""
    t0 = time.time()
    r = requests.post(BASE + path, json=payload, stream=True, timeout=timeout)
    print(f"\n== POST {path} (mode={payload.get('mode')}) -> {r.status_code} ({time.time()-t0:.0f}s) ==")
    if r.status_code != 200:
        print("  ", r.text[:300])
        return None
    text_parts, sources, trace = [], None, None
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: ") or line == "data: [DONE]":
            continue
        payload_str = line[6:]
        try:
            obj = json.loads(payload_str)
        except Exception:
            text_parts.append(payload_str)
            continue
        if isinstance(obj, dict) and "__sources__" in obj:
            sources = obj["__sources__"]
        elif isinstance(obj, dict) and "__trace__" in obj:
            trace = obj["__trace__"]
        elif isinstance(obj, str):
            text_parts.append(obj)
    return "".join(text_parts), sources, trace


if __name__ == "__main__":
    # 1. 消融数据端点
    abl = get("/api/eval/ablation")
    if not isinstance(abl, dict) or "configs" not in abl:
        print("ABLATION FAILED:", str(abl)[:200])
        sys.exit(1)
    print("  configs:", [c["name"] for c in abl["configs"]])
    print("  per_question keys:", list(abl["per_question"].keys()))
    print("  questions:", len(abl.get("questions") or []),
          "| 首题:", (abl["questions"][0].get("question", "")[:30] if abl.get("questions") else "无"))

    # 2. 流式问答 + 检索过程 trace（完整混合模式）
    text, sources, trace = sse_post("/api/chat/stream", {"question": "公司突然辞退我，我能拿多少经济补偿？", "mode": "full"})
    if text is None or sources is None or trace is None:
        print("STREAM FULL FAILED")
        sys.exit(1)
    print("  answer 长度:", len(text), "| sources:", len(sources))
    print("  trace: mode=", trace.get("mode"), "| 改写查询:", trace.get("query", "")[:40])
    print("  trace: 通道:", [(c["name"], c["enabled"], c["hit_count"], str(c["latency_ms"])+"ms") for c in trace["channels"]])
    print("  trace: 融合行数:", len(trace["fusion"]["rows"]), "| 最终:", len(trace["final"]),
          "| 总耗时:", trace["timings"]["total_ms"], "ms | 改写耗时:", trace["timings"]["rewrite_ms"], "ms")
    row0 = trace["fusion"]["rows"][0]
    print("  trace: 融合第1行:", row0["title"][:30], "| rrf=", row0["rrf_score"],
          "| 通道:", row0["channels"], "| in_final:", row0.get("in_final", False))

    # 3. 检索模式切换：仅 BM25（消融演示）
    text2, sources2, trace2 = sse_post("/api/chat/stream", {"question": "公司突然辞退我，我能拿多少经济补偿？", "mode": "bm25"})
    if trace2 is None:
        print("STREAM BM25 FAILED")
        sys.exit(1)
    enabled2 = [(c["name"], c["enabled"]) for c in trace2["channels"]]
    print("  bm25 模式通道状态:", enabled2)
    if enabled2 != [("bm25", True), ("vector", False), ("graph", False)]:
        print("MODE BM25 TOGGLES WRONG")
        sys.exit(1)

    # 4. 检索模式切换：仅图谱
    text3, sources3, trace3 = sse_post("/api/chat/stream", {"question": "公司突然辞退我，经济补偿怎么算？", "mode": "graph"})
    if trace3 is None:
        print("STREAM GRAPH FAILED")
        sys.exit(1)
    enabled3 = [(c["name"], c["enabled"]) for c in trace3["channels"]]
    print("  graph 模式通道状态:", enabled3)

    # 5. 非法模式应 422
    r = requests.post(BASE + "/api/chat/stream", json={"question": "测试", "mode": "bad-mode"}, timeout=30)
    print(f"\n== 非法模式 -> {r.status_code} ==")
    if r.status_code != 422:
        print("MODE VALIDATION FAILED")
        sys.exit(1)

    # 6. 案情诊断（真实 LLM 调用 ~30-60s）
    d = requests.post(BASE + "/api/diagnosis", json={
        "description": "我在公司干了3年，月薪8000，签了合同。上周公司突然口头通知我被辞退了，没有给书面通知，也没有说原因。",
        "reason": "被辞退", "years": 3.0, "monthly_wage": 8000, "has_contract": True,
    }, timeout=240).json()
    print(f"\n== POST /api/diagnosis ->", "OK" if isinstance(d, dict) else "FAIL")
    if not isinstance(d, dict) or "issues" not in d:
        print("  ", str(d)[:300])
        sys.exit(1)
    print("  summary:", d.get("summary", "")[:50])
    print("  issues:", len(d.get("issues") or []), "| warnings:", len(d.get("warnings") or []),
          "| next_steps:", len(d.get("next_steps") or []))
    est = d.get("estimation") or {}
    print("  estimation: N=", est.get("N"), " N+1=", est.get("N_plus_1"), " 2N=", est.get("2N"))
    print("  sources:", len(d.get("sources") or []), "| 检索词:", d.get("search_query", "")[:40])

    print("\nALL PASS")
