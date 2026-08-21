# -*- coding: utf-8 -*-
"""临时验证脚本：经 Spring 8089/8090 代理验证科普新玩法端点 + JWT"""
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
    return r.json()


def get(path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    t0 = time.time()
    r = requests.get(BASE + path, headers=headers, timeout=30)
    print(f"\n== GET {path} -> {r.status_code} ({time.time()-t0:.0f}s) ==")
    if r.status_code != 200:
        print("  ", r.text[:300])
        return None
    return r.json()


def assert_ok(resp, name):
    ok = resp and resp.get("code") == 200
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if not ok:
        sys.exit(1)


def pick(resp, *keys):
    d = resp["data"]
    for k in keys:
        d = d[k] if isinstance(d, (dict, list)) and isinstance(k, str) else d
    return d


if __name__ == "__main__":
    # 1. 登录
    login = post("/api/auth/login", {"username": "admin", "password": "admin123"})
    assert_ok(login, "login")
    token = login["data"].get("token") or login["data"].get("jwt")
    if not token:
        print("FAIL: no token in", login["data"])
        sys.exit(1)
    print("token ok")

    # 2. 剧本库（GET 数组代理）
    r = get("/api/knowledge/stories", token)
    assert_ok(r, "stories")
    print("  stories:", [s.get("title") for s in r["data"]])

    # 3. 情景剧开场（POST 对象代理；Python 端已缓存该剧本，瞬时返回）
    r = post("/api/knowledge/scene/start", {"story_id": "overtime"}, token)
    assert_ok(r, "scene/start")
    d = r["data"]
    print("  scene_index:", d["scene_index"], "| options:", len(d["options"]),
          "| scene_text 长度:", len(d["scene_text"]))

    # 4. 剧情推进（第 1 幕选 A，缓存命中）
    r = post("/api/knowledge/scene/next",
             {"story_id": "overtime", "scene_index": 1, "choice": "A"}, token)
    assert_ok(r, "scene/next")
    d = r["data"]
    print("  verdict.correct:", d["verdict"]["correct"],
          "| next.scene_index:", d["next"]["scene_index"])

    # 5. 海报（未缓存，真实 LLM 调用 ~45s）
    r = post("/api/knowledge/poster", {"topic": "加班费怎么算"}, token)
    assert_ok(r, "poster")
    print("  title:", r["data"].get("title"), "| points:", len(r["data"].get("points") or []))

    # 6. 短片（未缓存，真实 LLM+TTS ~90s，验证大 payload 透传）
    r = post("/api/knowledge/video", {"topic": "加班费怎么算"}, token)
    assert_ok(r, "video")
    d = r["data"]
    print("  scenes:", len(d.get("scenes") or []),
          "| audio:", len(d.get("audio") or []),
          "| 首段音频字节:", len(d["audio"][0]) if d.get("audio") else 0)

    print("\nSPRING ALL PASS")
