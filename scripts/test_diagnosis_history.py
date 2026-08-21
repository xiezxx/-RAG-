# -*- coding: utf-8 -*-
"""临时验证脚本：诊断报告历史记录（经 Spring 8090 + JWT）——落库 + 列表 + 详情"""
import json
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8090"


def post(path, payload, token=None, timeout=240):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    t0 = time.time()
    r = requests.post(BASE + path, json=payload, headers=headers, timeout=timeout)
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


def fail(name):
    print(f"[FAIL] {name}")
    sys.exit(1)


if __name__ == "__main__":
    # 1. 登录
    r = post("/api/auth/login", {"username": "admin", "password": "admin123"})
    if r is None:
        fail("login")
    login = r.json()
    token = login["data"].get("token") or login["data"].get("jwt")
    print("[PASS] login")

    # 2. 生成一次诊断（真实 LLM ~60s）
    r = post("/api/diagnosis", {
        "description": "我在公司干了3年，月薪8000，签了合同。上周公司突然口头通知我被辞退了，没有给书面通知，也没有说明原因。",
        "reason": "被辞退", "years": 3.0, "monthly_wage": 8000, "has_contract": True,
    }, token, timeout=240)
    if r is None:
        fail("diagnosis")
    rd = r.json()
    if rd.get("code") != 200:
        fail("diagnosis code != 200")
    print("[PASS] diagnosis 生成:", rd["data"].get("summary", "")[:40])

    # 3. 历史列表（应含刚才这条）
    hist = get("/api/diagnosis/history", token)
    if hist is None or hist.get("code") != 200:
        fail("history list")
    items = hist["data"]
    print("[PASS] history list, 共", len(items), "条")
    if not items:
        fail("history list 为空（落库失败？）")
    first = items[0]
    print("  最新一条:", first["id"], first["reason"], "| 工龄", first["years"],
          "| 月薪", first["monthlyWage"], "| 合同", first["hasContract"], "|", first["createdAt"])
    print("  summary:", first["summary"][:50])
    print("  estimation:", json.dumps(first["estimation"], ensure_ascii=False)[:120])
    print("  description(截断):", first["description"][:40], "...")

    # 4. 详情（JSON 字段应为对象）
    rid = first["id"]
    detail = get(f"/api/diagnosis/history/{rid}", token)
    if detail is None or detail.get("code") != 200:
        fail("history detail")
    d = detail["data"]
    ok_types = (isinstance(d.get("issues"), list) and isinstance(d.get("warnings"), list)
                and isinstance(d.get("next_steps"), list) and isinstance(d.get("sources"), list)
                and isinstance(d.get("estimation"), dict))
    print("[PASS] history detail:", len(d.get("issues") or []), "个问题 |",
          len(d.get("next_steps") or []), "条建议 |", len(d.get("sources") or []), "个来源 |",
          "JSON字段类型正确" if ok_types else "JSON字段类型错误")
    if not ok_types:
        fail("详情 JSON 字段类型")
    print("  estimation:", {k: d["estimation"][k] for k in ("N", "N_plus_1", "2N") if k in d.get("estimation", {})})
    print("  description 完整长度:", len(d.get("description") or ""), "| createdAt:", d.get("createdAt"))

    # 5. 不存在的 id → 404
    r404 = requests.get(BASE + "/api/diagnosis/history/999999",
                        headers={"Authorization": f"Bearer {token}"}, timeout=30)
    body404 = r404.json()
    print(f"\n== GET /history/999999 -> {r404.status_code}, code={body404.get('code')}")
    if r404.status_code != 200 or body404.get("code") != 404:
        fail("不存在 id 应返回 code=404")

    print("\nDIAGNOSIS-HISTORY ALL PASS")
