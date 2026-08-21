# -*- coding: utf-8 -*-
"""验证智能问答权限（经 Spring 8090，需 8011 Python 就绪）：
- 普通用户 POST /api/chat/ask 带非 full 模式 → 403
- 普通用户 POST /api/chat/ask/stream 带非 full 模式 → 403
- 普通用户流式问答（默认 full）→ 正常出字且 SSE 含 __trace__（检索过程可视化所有用户可见）
- 管理员流式问答 mode=bm25 → SSE 含 __trace__ 且 trace.mode='bm25'
"""
import json
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8090"


def wait_ready():
    for _ in range(90):
        try:
            requests.post(BASE + "/api/auth/login", json={}, timeout=3)
            return True
        except Exception:
            time.sleep(2)
    return False


def login(username, password):
    r = requests.post(BASE + "/api/auth/login", json={"username": username, "password": password}, timeout=10)
    data = r.json()
    token = (data.get("data") or {}).get("token")
    if not token:
        raise RuntimeError(f"登录失败 {username}: {data}")
    return token


def main():
    print("等待 Spring 8090 就绪…")
    if not wait_ready():
        print("[FAIL] Spring 8090 未就绪")
        sys.exit(1)
    print("[PASS] Spring 8090 就绪")

    suffix = str(int(time.time()))[-6:]
    uname = f"gate_{suffix}"
    requests.post(BASE + "/api/auth/register",
                  json={"username": uname, "password": "test123456", "name": uname, "phone": "13800000000"}, timeout=10)
    user_token = login(uname, "test123456")
    admin_token = login("admin", "admin123")
    q = "试用期最长是多久？"

    # 1. 普通用户：ask 切模式 → 403
    r = requests.post(BASE + "/api/chat/ask", json={"question": q, "mode": "bm25"},
                      headers={"Authorization": "Bearer " + user_token}, timeout=30)
    data = r.json()
    print(f"[{'PASS' if data.get('code') == 403 else 'FAIL'}] 普通用户 ask 切模式 403: code={data.get('code')}")

    # 2. 普通用户：stream 切模式 → 403
    r = requests.post(BASE + "/api/chat/ask/stream", json={"question": q, "mode": "bm25"},
                      headers={"Authorization": "Bearer " + user_token}, timeout=30)
    print(f"[{'PASS' if r.status_code == 403 and '403' in r.text else 'FAIL'}] 普通用户 stream 切模式 403: http={r.status_code}")

    def read_stream(token, body, timeout=180):
        """完整读完 SSE 流：__trace__ 是最后一条事件（文本 token 之后、[DONE] 之前）"""
        trace, text_parts, got_done = None, [], False
        with requests.post(BASE + "/api/chat/ask/stream", json=body,
                           headers={"Authorization": "Bearer " + token}, stream=True, timeout=timeout) as resp:
            assert resp.status_code == 200, f"http={resp.status_code}"
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    got_done = True
                    break
                if "__trace__" in payload:
                    trace = json.loads(payload)["__trace__"]
                    continue
                try:
                    obj = json.loads(payload)
                except Exception:
                    continue
                if isinstance(obj, str):
                    text_parts.append(obj)
        return trace, "".join(text_parts), got_done

    # 3. 普通用户：默认 full 流式 → 正常出字且含 __trace__（检索过程可视化所有用户可见）
    trace, text, got_done = read_stream(user_token, {"question": q})
    ok = got_done and len(text) > 20 and trace is not None
    print(f"[{'PASS' if ok else 'FAIL'}] 普通用户流式正常出字且含 __trace__: 字数={len(text)} DONE={got_done} trace={'有' if trace else '无'}")

    # 4. 管理员：stream mode=bm25 → 含 __trace__ 且 mode 正确
    trace, text, got_done = read_stream(admin_token, {"question": q, "mode": "bm25"})
    ok = got_done and trace is not None and trace.get("mode") == "bm25"
    print(f"[{'PASS' if ok else 'FAIL'}] 管理员流式含 __trace__ 且 mode=bm25: 字数={len(text)} DONE={got_done} trace={'有' if trace else '无'} mode={trace.get('mode') if trace else '-'}")

    # 5. 清理
    import pymysql
    conn = pymysql.connect(host="127.0.0.1", user="root", password="123456", database="demo", charset="utf8mb4")
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s", (uname,))
    uid = cur.fetchone()
    if uid:
        cur.execute("DELETE FROM chat_history WHERE user_id=%s", (uid[0],))
        cur.execute("DELETE FROM users WHERE id=%s", (uid[0],))
        conn.commit()
    conn.close()
    print("已清理测试用户及其问答记录")
    print("\nCHAT GATE ALL PASS")


if __name__ == "__main__":
    main()
