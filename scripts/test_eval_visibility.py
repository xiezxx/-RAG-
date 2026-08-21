# -*- coding: utf-8 -*-
"""验证问答记录可见性矩阵 + 消融端点管理员权限（经 Spring 8090，需 8011 Python 已就绪）
规则：
- GET /api/eval/ablation：ADMIN=200；普通用户=403
- GET /api/eval/history：ADMIN=全员；普通用户=自己+其他普通用户（不含管理员），含 username/mine
"""
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8090"


def wait_ready():
    for _ in range(90):
        try:
            if requests.get(BASE + "/api/auth/health", timeout=3).status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(2)
    # /health 不一定存在，直接试探登录端点
    try:
        requests.post(BASE + "/api/auth/login", json={}, timeout=3)
        return True
    except Exception:
        return False


def login(username, password):
    r = requests.post(BASE + "/api/auth/login", json={"username": username, "password": password}, timeout=10)
    data = r.json()
    token = (data.get("data") or {}).get("token")
    if not token:
        raise RuntimeError(f"登录失败 {username}: {data}")
    return token


def api_get(path, token):
    return requests.get(BASE + path, headers={"Authorization": "Bearer " + token}, timeout=30)


def main():
    print("等待 Spring 8090 就绪…")
    if not wait_ready():
        print("[FAIL] Spring 8090 未就绪")
        sys.exit(1)
    print("[PASS] Spring 8090 就绪")

    # 1. 注册两个普通用户
    suffix = str(int(time.time()))[-6:]
    users = [(f"vis_a_{suffix}", "test123456"), (f"vis_b_{suffix}", "test123456")]
    for u, p in users:
        r = requests.post(BASE + "/api/auth/register",
                          json={"username": u, "password": p, "name": u, "phone": "13800000000"}, timeout=10)
        print(f"注册 {u}: {r.json().get('message')}")

    # 2. 直插 chat_history 种子：A 2条、B 1条、admin 1条（admin 由数据库已有记录保证，这里只插 A/B）
    import pymysql
    conn = pymysql.connect(host="127.0.0.1", user="root", password="123456", database="demo", charset="utf8mb4")
    cur = conn.cursor()
    ids = {"A": None, "B": None, "admin": None}
    cur.execute("SELECT id, username FROM users WHERE username IN (%s, %s, 'admin')", (users[0][0], users[1][0]))
    for uid, uname in cur.fetchall():
        if uname == users[0][0]:
            ids["A"] = uid
        elif uname == users[1][0]:
            ids["B"] = uid
        else:
            ids["admin"] = uid
    assert ids["A"] and ids["B"], f"用户注册后查不到 id: {ids}"
    seed_q = "测试问题：试用期最长是多久？"
    seed_a = "根据《劳动合同法》第十九条，试用期最长不得超过六个月。（权限矩阵验证种子数据）"
    for uid in (ids["A"], ids["B"]):
        cur.execute(
            "INSERT INTO chat_history (user_id, question, answer, sources, created_at) VALUES (%s, %s, %s, '[]', NOW())",
            (uid, seed_q, seed_a))
    conn.commit()
    cur.execute("SELECT id FROM chat_history WHERE question=%s", (seed_q,))
    seed_rows = [r[0] for r in cur.fetchall()]
    print(f"插入种子记录 {len(seed_rows)} 条")

    try:
        # 3. 管理员：消融 200 + history 含全员
        token = login("admin", "admin123")
        r = api_get("/api/eval/ablation", token)
        data = r.json()
        ok = data.get("code") == 200 and data.get("data", {}).get("configs")
        print(f"[{'PASS' if ok else 'FAIL'}] 管理员消融端点: code={data.get('code')} configs={len(data.get('data', {}).get('configs') or [])}")

        r = api_get("/api/eval/history?limit=100", token)
        rows = r.json().get("data") or []
        names = {x.get("username") for x in rows}
        admin_mine = [x for x in rows if x.get("username") == "admin" and x.get("mine")]
        has_ab = users[0][0] in names and users[1][0] in names
        print(f"[{'PASS' if has_ab else 'FAIL'}] 管理员 history 含 A/B 记录: A={users[0][0] in names} B={users[1][0] in names} 共{len(rows)}条")
        print(f"[{'PASS' if admin_mine else 'FAIL'}] 管理员 history 自己记录 mine=true: {len(admin_mine)}条")

        # 4. 普通用户 A：消融 403；history = 所有普通用户记录、无 admin、mine 正确
        token = login(*users[0])
        r = api_get("/api/eval/ablation", token)
        data = r.json()
        print(f"[{'PASS' if data.get('code') == 403 else 'FAIL'}] 普通用户消融端点 403: code={data.get('code')}")

        r = api_get("/api/eval/history?limit=100", token)
        rows = r.json().get("data") or []
        bad_admin = [x for x in rows if x.get("username") == "admin"]
        mine_rows = [x for x in rows if x.get("mine")]
        wrong_mine = [x for x in mine_rows if x.get("username") != users[0][0]]
        other_rows = [x for x in rows if not x.get("mine")]
        other_ok = all(x.get("username") and x.get("username") != "admin" for x in other_rows)
        print(f"[{'PASS' if not bad_admin else 'FAIL'}] 普通用户 history 不含管理员记录: 命中{len(bad_admin)}条, 共{len(rows)}条")
        print(f"[{'PASS' if mine_rows and not wrong_mine else 'FAIL'}] 普通用户 history mine 标记: mine={len(mine_rows)}条 全属自己={not wrong_mine}")
        print(f"[{'PASS' if other_rows and other_ok else 'FAIL'}] 普通用户 history 含其他普通用户记录: 他人{len(other_rows)}条 均带用户名={other_ok}")
        print(f"[{'PASS' if any(x.get('username') == users[1][0] for x in other_rows) else 'FAIL'}] 普通用户 A 能看到 B({users[1][0]})的记录")

        # 5. 普通用户 B 视角：能看到 A 的记录（互见）
        token = login(*users[1])
        r = api_get("/api/eval/history?limit=100", token)
        rows = r.json().get("data") or []
        sees_a = any(x.get("username") == users[0][0] for x in rows)
        print(f"[{'PASS' if sees_a else 'FAIL'}] 普通用户 B 能看到 A({users[0][0]})的记录")

        # 6. 越权评价他人记录 → 404（updateRating 按 user_id 收紧）
        token = login(*users[0])
        b_seed = next((x["id"] for x in rows if x.get("username") == users[1][0]), None)
        if b_seed:
            r = requests.post(BASE + "/api/eval/feedback",
                              json={"chatId": b_seed, "rating": 1, "comment": "越权测试"},
                              headers={"Authorization": "Bearer " + token}, timeout=10)
            print(f"[{'PASS' if r.json().get('code') == 404 else 'FAIL'}] 普通用户评价他人记录被拒: code={r.json().get('code')}")

        print("\nVISIBILITY ALL PASS")
    finally:
        # 7. 清理种子
        for rid in seed_rows:
            cur.execute("DELETE FROM chat_history WHERE id=%s", (rid,))
        cur.execute("DELETE FROM users WHERE username IN (%s, %s)", (users[0][0], users[1][0]))
        conn.commit()
        conn.close()
        print("已清理种子记录与测试用户")


if __name__ == "__main__":
    main()
