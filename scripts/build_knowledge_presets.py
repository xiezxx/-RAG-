# -*- coding: utf-8 -*-
"""生成普法海报/短片预置内容：调用运行中的 RAG 服务（默认 8011 测试实例）
POST /api/knowledge/poster ×6 主题、/api/knowledge/video ×4 主题（含 edge-tts 配音），
结果写入 src/data/presets/preset_posters.json / preset_videos.json。
生成后再修改主题时重跑本脚本即可。"""
import json
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8011"
OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "data" / "presets"

POSTER_TOPICS = ["加班费怎么算", "被辞退的经济补偿", "工伤认定与赔偿", "试用期红线", "竞业限制", "女职工特殊保护"]
VIDEO_TOPICS = ["加班费怎么算", "工伤认定与赔偿", "被辞退的经济补偿", "女职工特殊保护"]


def call(path, payload):
    r = requests.post(BASE + path, json=payload, timeout=300)
    r.raise_for_status()
    return r.json()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    posters = []
    print("=== 生成海报 ===")
    for t in POSTER_TOPICS:
        try:
            data = call("/api/knowledge/poster", {"topic": t})
            data["topic"] = t
            posters.append(data)
            print(f"[OK] 海报「{t}」-> {data.get('title')}（要点 {len(data.get('points') or [])} 条）")
        except Exception as e:
            print(f"[FAIL] 海报「{t}」: {e}")
    (OUT_DIR / "preset_posters.json").write_text(
        json.dumps(posters, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SAVED] {len(posters)} 张海报 -> preset_posters.json")

    videos = []
    print("=== 生成短片 ===")
    for i, t in enumerate(VIDEO_TOPICS):
        try:
            data = call("/api/knowledge/video", {"topic": t})
            data["id"] = i
            data["topic"] = t
            videos.append(data)
            n_audio = sum(1 for u in data.get("audio") or [] if u)
            print(f"[OK] 短片「{t}」-> {data.get('title')}（分镜 {len(data.get('scenes') or [])} 个，配音 {n_audio} 段）")
        except Exception as e:
            print(f"[FAIL] 短片「{t}」: {e}")
    (OUT_DIR / "preset_videos.json").write_text(
        json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SAVED] {len(videos)} 部短片 -> preset_videos.json")


if __name__ == "__main__":
    main()
