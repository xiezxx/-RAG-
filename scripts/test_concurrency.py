# -*- coding: utf-8 -*-
"""临时验证脚本：长 LLM 调用不再阻塞事件循环（诊断进行中，其他端点应即时响应）"""
import sys
import threading
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8011"


def wait_ready():
    for _ in range(60):
        try:
            if requests.get(BASE + "/health", timeout=3).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def main():
    print("等待 RAG 服务就绪…")
    if not wait_ready():
        print("[FAIL] 服务未就绪")
        sys.exit(1)
    print("[PASS] 服务就绪")

    # 1. 后台线程发起诊断（阻塞式 LLM 调用 ~60-100s）
    result = {}

    def do_diagnosis():
        t0 = time.time()
        try:
            r = requests.post(BASE + "/api/diagnosis", json={
                "description": "我在公司干了3年，月薪8000，签了合同。上周公司突然口头通知我被辞退了，没有给书面通知，也没有说明原因。",
                "reason": "被辞退", "years": 3.0, "monthly_wage": 8000, "has_contract": True,
            }, timeout=240)
            result["ok"] = r.status_code == 200
            result["secs"] = time.time() - t0
        except Exception as e:
            result["ok"] = False
            result["err"] = str(e)

    t = threading.Thread(target=do_diagnosis, daemon=True)
    t.start()
    time.sleep(3)  # 确保诊断已进入 LLM 生成阶段

    # 2. 诊断进行中：消融端点必须立即响应（修复前会冻住直到诊断结束）
    t0 = time.time()
    try:
        r = requests.get(BASE + "/api/eval/ablation", timeout=10)
        dt = time.time() - t0
        n_configs = len(r.json().get("configs") or [])
        print(f"[{'PASS' if r.status_code == 200 and dt < 3 else 'FAIL'}] 消融端点并发响应 {dt:.2f}s（修复前应≈诊断时长） configs={n_configs}")
    except requests.Timeout:
        print(f"[FAIL] 消融端点超时 10s（事件循环仍被阻塞）")
        sys.exit(1)

    # 3. 诊断进行中：KG 端点也必须立即响应
    t0 = time.time()
    try:
        r = requests.get(BASE + "/api/kg/entities", params={"entity_type": "LegalConcept"}, timeout=10)
        dt = time.time() - t0
        ok = r.status_code == 200 and isinstance(r.json(), list)
        print(f"[{'PASS' if ok and dt < 3 else 'FAIL'}] KG 端点并发响应 {dt:.2f}s")
    except requests.Timeout:
        print("[FAIL] KG 端点超时 10s")
        sys.exit(1)

    # 4. 等诊断完成，确认同步 def 改造未破坏诊断功能
    t.join(300)
    if result.get("ok"):
        print(f"[PASS] 诊断正常完成 ({result['secs']:.0f}s)")
    else:
        print(f"[FAIL] 诊断失败: {result}")
        sys.exit(1)

    # 5. 流式问答（sync def + sync generator 走线程池，验证 SSE 仍正常）
    print("流式问答验证…")
    text_parts, trace, got_done = [], None, False
    with requests.post(BASE + "/api/chat/stream",
                       json={"question": "试用期最长是多久？", "mode": "full"},
                       stream=True, timeout=180) as resp:
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            if line == "data: [DONE]":
                got_done = True
                break
            payload = line[6:]
            import json
            try:
                obj = json.loads(payload)
            except Exception:
                text_parts.append(payload)
                continue
            if isinstance(obj, dict) and "__trace__" in obj:
                trace = obj["__trace__"]
            elif isinstance(obj, str):
                text_parts.append(obj)
    ok = got_done and len("".join(text_parts)) > 20 and trace is not None
    print(f"[{'PASS' if ok else 'FAIL'}] 流式问答 SSE：答案 {len(''.join(text_parts))} 字，trace={'有' if trace else '无'}，DONE={'有' if got_done else '无'}")
    if not ok:
        sys.exit(1)

    print("\nCONCURRENCY ALL PASS")


if __name__ == "__main__":
    main()
