# -*- coding: utf-8 -*-
"""临时验证脚本：互动情景剧 / 海报 / 短片 四个新端点直测"""
import json
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"


def post(path, payload, timeout=240):
    t0 = time.time()
    r = requests.post(BASE + path, json=payload, timeout=timeout)
    print(f"\n== POST {path} -> {r.status_code} ({time.time()-t0:.0f}s) ==")
    try:
        data = r.json()
    except Exception:
        print("  (非 JSON 响应)", r.text[:200])
        return None
    return data


def get(path):
    t0 = time.time()
    r = requests.get(BASE + path, timeout=30)
    print(f"\n== GET {path} -> {r.status_code} ({time.time()-t0:.0f}s) ==")
    return r.json() if r.status_code == 200 else r.text


def summarize(d, depth=0, indent="  "):
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                print(f"{indent}{k}: {type(v).__name__} (len={len(v)})")
                summarize(v, depth + 1, indent + "  ")
            else:
                s = str(v)
                print(f"{indent}{k}: {s[:80]}{'...' if len(s) > 80 else ''}")
    elif isinstance(d, list):
        for i, v in enumerate(d[:4]):
            if isinstance(v, dict):
                print(f"{indent}[{i}]")
                summarize(v, depth + 1, indent + "  ")
            else:
                print(f"{indent}[{i}] {str(v)[:60]}")


if __name__ == "__main__":
    # 1. 剧本库
    stories = get("/api/knowledge/stories")
    if not isinstance(stories, list):
        print("STORIES FAILED:", stories)
        sys.exit(1)
    print("stories count:", len(stories))

    # 2. 开场（第 1 幕）
    s0 = post("/api/knowledge/scene/start", {"story_id": "overtime"})
    if not s0 or "scene_text" not in s0:
        print("SCENE START FAILED")
        sys.exit(1)
    summarize(s0)

    # 3. 选一个选项推进（第 1 幕 → 判决 + 第 2 幕）
    choice = s0["options"][0]["key"]
    n1 = post("/api/knowledge/scene/next",
              {"story_id": "overtime", "scene_index": 1, "choice": choice})
    if not n1 or "verdict" not in n1:
        print("SCENE NEXT FAILED")
        sys.exit(1)
    summarize(n1)

    # 4. 第 2 幕再推一回合
    n2 = post("/api/knowledge/scene/next",
              {"story_id": "overtime", "scene_index": 2,
               "choice": n1["next"]["options"][1]["key"]})
    if not n2 or "verdict" not in n2:
        print("SCENE NEXT2 FAILED")
        sys.exit(1)
    summarize(n2)

    # 5. 第 3 幕 → 结局
    n3 = post("/api/knowledge/scene/next",
              {"story_id": "overtime", "scene_index": 3,
               "choice": n2["next"]["options"][0]["key"]})
    if not n3 or "verdict" not in n3 or "next" not in n3 or not n3["next"].get("is_ending"):
        print("SCENE ENDING FAILED")
        sys.exit(1)
    summarize(n3)

    # 6. 海报
    p = post("/api/knowledge/poster", {"topic": "加班费怎么算"})
    if not p or "points" not in p:
        print("POSTER FAILED")
        sys.exit(1)
    summarize(p)

    # 7. 短片（含配音）
    v = post("/api/knowledge/video", {"topic": "加班费怎么算"})
    if not v or "scenes" not in v:
        print("VIDEO FAILED")
        sys.exit(1)
    print("\nvideo scenes:", len(v["scenes"]), "| audio entries:", len(v.get("audio") or []))
    if v.get("audio"):
        print("first audio dataURI length:", len(v["audio"][0]))
    for i, sc in enumerate(v["scenes"]):
        print(f"  分镜{i+1} visual={sc.get('visual','')[:30]} | subtitle={sc.get('subtitle','')[:40]}")

    print("\nALL PASS")
