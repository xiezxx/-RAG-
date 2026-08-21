# -*- coding: utf-8 -*-
"""临时验证脚本：经 Spring 8090 验证 检索模式/消融数据/案情诊断 三模块（含 JWT）"""
import json
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8090"


def post(path, payload, token=None, timeout=240, stream=False):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    t0 = time.time()
    r = requests.post(BASE + path, json=payload, headers=headers, timeout=timeout, stream=stream)
    print(f"\n== POST {path} -> {r.status_code} ({time.time()-t0:.0f}s) ==")
    if r.status_code != 200:
        print("  ", r.text[:300])
        return None
    return r


def get(path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    t0 = time.time()
    r = requests.get(BASE + path, headers=headers, timeout=60)
    print(f"\n== GET {path} -> {r.status_code} ({time.time()-t0:.0f}s) ==")
    if r.status_code != 200:
        print("  ", r.text[:300])
        return None
    return r.json()


def assert_ok(resp, name):
    ok = resp is not None and resp.get("code") == 200
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    # 1. 登录
    r = post("/api/auth/login", {"username": "admin", "password": "admin123"})
    login = r.json() if r is not None else None
    assert_ok(login, "login")
    token = login["data"].get("token") or login["data"].get("jwt")
    if not token:
        print("FAIL: no token")
        sys.exit(1)
    print("token ok")

    # 2. 消融实验数据（Spring 代理 Python）
    abl = get("/api/eval/ablation", token)
    assert_ok(abl, "eval/ablation")
    d = abl["data"]
    print("  configs:", [c["name"] for c in d["configs"]], "| questions:", len(d.get("questions") or []))
    if len(d["configs"]) != 5:
        print("FAIL: 应有 5 组配置")
        sys.exit(1)

    # 3. 流式问答 + 检索模式 + trace 透传（经 Spring SSE 直通）
    r = post("/api/chat/ask/stream",
             {"question": "公司突然辞退我，我能拿多少经济补偿？", "mode": "bm25+vector"}, token, stream=True)
    if r is None:
        sys.exit(1)
    text_parts, trace, sources = [], None, None
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: ") or line == "data: [DONE]":
            continue
        payload = line[6:]
        try:
            obj = json.loads(payload)
        except Exception:
            text_parts.append(payload)
            continue
        if isinstance(obj, dict) and "__trace__" in obj:
            trace = obj["__trace__"]
        elif isinstance(obj, dict) and "__sources__" in obj:
            sources = obj["__sources__"]
        elif isinstance(obj, str):
            text_parts.append(obj)
    print("  answer 长度:", len("".join(text_parts)), "| sources:", len(sources or []))
    if trace is None:
        print("FAIL: SSE 未透传 __trace__")
        sys.exit(1)
    enabled = [(c["name"], c["enabled"]) for c in trace["channels"]]
    print("  trace.mode:", trace.get("mode"), "| 通道状态:", enabled)
    if enabled != [("bm25", True), ("vector", True), ("graph", False)]:
        print("FAIL: bm25+vector 模式开关错误")
        sys.exit(1)

    # 4. 案情诊断（真实 LLM 调用 ~30-60s，验证大 payload 透传）
    r = post("/api/diagnosis", {
        "description": "我在公司干了3年，月薪8000，签了合同。上周公司突然口头通知我被辞退了，没有给书面通知，也没有说原因。",
        "reason": "被辞退", "years": 3.0, "monthly_wage": 8000, "has_contract": True,
    }, token, timeout=240)
    assert_ok(r.json() if r is not None else None, "diagnosis")
    rd = r.json()["data"]
    print("  summary:", rd.get("summary", "")[:50])
    print("  issues:", len(rd.get("issues") or []), "| warnings:", len(rd.get("warnings") or []),
          "| next_steps:", len(rd.get("next_steps") or []))
    print("  estimation:", {k: rd["estimation"][k] for k in ("N", "N_plus_1", "2N") if k in rd.get("estimation", {})})
    print("  sources:", len(rd.get("sources") or []))

    # 5. 诊断参数校验（描述过短）
    r = post("/api/diagnosis", {"description": "短"}, token)
    body5 = r.json() if r is not None else {}
    print("  短描述返回: code =", body5.get("code"), "->", body5.get("message"))
    if body5.get("code") != 400:
        print("FAIL: 短描述应返回 400")
        sys.exit(1)

    print("\nSPRING ALL PASS")
