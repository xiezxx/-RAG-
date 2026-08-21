"""
法律知识科普 API — 普法文章 + 名词卡片 + 互动情景剧 + 海报 + 短片
"""
import asyncio
import base64
import io
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from src.database.neo4j_client import Neo4jClient
from src.rag.kg_builder import (
    CORE_CONCEPTS,
    CORE_RIGHTS_OBLIGATIONS,
    CORE_ILLEGAL_ACTS,
    CORE_LIABILITIES,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# 预置内容目录（scripts/build_knowledge_presets.py 提前生成，秒开不等待 LLM）
_PRESETS_DIR = Path(__file__).resolve().parent.parent / "data" / "presets"

# 由 rag_service.py 启动时注入（避免重复加载索引）
_rag = None

def set_rag(rag_instance):
    global _rag
    _rag = rag_instance


class ArticleRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=100)
    search_query: Optional[str] = Field(default=None, max_length=300)


@router.post("/article")
def generate_article(request: ArticleRequest):
    """按主题检索语料并生成普法文章（markdown + 来源）。同步 def：LLM 调用走线程池"""
    if _rag is None:
        raise HTTPException(status_code=503, detail="RAG 引擎未初始化")
    try:
        content, sources = _rag.generate_article(request.topic, request.search_query)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"topic": request.topic, "content": content, "sources": sources}


# ── 名词卡片 ──

# 全局 Neo4j 客户端单例（与 kg_api 相同模式）
_neo4j = None

def get_neo4j():
    global _neo4j
    if _neo4j is None:
        _neo4j = Neo4jClient()
    return _neo4j


def _build_seed_terms() -> List[Dict]:
    """组装种子术语（KG 为空时兜底，保证非空返回）"""
    terms = []
    for name, desc in CORE_CONCEPTS.items():
        terms.append({"name": name, "description": desc, "type": "LegalConcept"})
    for name, desc in CORE_RIGHTS_OBLIGATIONS.items():
        terms.append({"name": name, "description": desc, "type": "RightObligation"})
    for name, desc in CORE_ILLEGAL_ACTS.items():
        terms.append({"name": name, "description": desc, "type": "IllegalAct"})
    for name, data in CORE_LIABILITIES.items():
        # CORE_LIABILITIES 值为 (description, illegal_act) 元组
        desc = data[0] if isinstance(data, tuple) else data
        terms.append({"name": name, "description": desc, "type": "LegalLiability"})
    return terms


@router.get("/terms")
def list_terms():
    """名词卡片：4 类 KG 实体，Neo4j 为空/不可用时回退种子数据（同步 def：Neo4j 查询走线程池）"""
    seeds = _build_seed_terms()
    merged: Dict[str, Dict] = {}
    for t in seeds:
        merged[(t["name"], t["type"])] = t

    # Neo4j 查询（失败静默降级为种子数据）
    try:
        neo4j = get_neo4j()
        if neo4j.check_connection():
            with neo4j.driver.session() as s:
                for label in ["LegalConcept", "RightObligation", "IllegalAct", "LegalLiability"]:
                    result = s.run(
                        f"MATCH (n:{label}) RETURN n.name AS name, n.description AS description"
                    )
                    for r in result:
                        name = r["name"] or ""
                        desc = r["description"] or ""
                        if not name:
                            continue
                        key = (name, label)
                        if key in merged:
                            # 非空描述覆盖种子；空描述保留种子描述
                            if desc:
                                merged[key]["description"] = desc
                        else:
                            merged[key] = {"name": name, "description": desc, "type": label}
    except Exception:
        pass  # KG 不可用时仅用种子数据

    return sorted(merged.values(), key=lambda t: (t["type"], t["name"]))


# ── 互动情景剧「打工人小剧场」 ──

TOTAL_SCENES = 3

STORY_TEMPLATES = [
    {"id": "onboard", "title": "入职第一天", "topic": "试用期与劳动合同签订",
     "search_query": "试用期 劳动合同 签订 书面劳动合同"},
    {"id": "overtime", "title": "加不完的班", "topic": "加班与加班费",
     "search_query": "加班费 加班工资 延长工作时间 加班"},
    {"id": "fired", "title": "突然被辞退", "topic": "违法解除与经济补偿",
     "search_query": "辞退 解除劳动合同 经济补偿 赔偿金"},
    {"id": "injury", "title": "上班受伤之后", "topic": "工伤认定与赔偿",
     "search_query": "工伤 认定 工伤保险 赔偿"},
    {"id": "maternity", "title": "怀孕之后", "topic": "女职工特殊保护",
     "search_query": "女职工 怀孕 产假 特殊保护"},
]

# 进程内缓存（重启丢失，可接受）：scenes[(story_id, scene_index)] 存含 correct_key 的完整场景
_scenes: Dict = {}
_next_cache: Dict = {}


class SceneStartRequest(BaseModel):
    story_id: str = Field(..., min_length=1, max_length=50)


class SceneNextRequest(BaseModel):
    story_id: str = Field(..., min_length=1, max_length=50)
    scene_index: int = Field(..., ge=1, le=TOTAL_SCENES)
    choice: str = Field(..., min_length=1, max_length=5)


class TopicRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=100)
    search_query: Optional[str] = Field(default=None, max_length=300)


def _get_story(story_id: str):
    for s in STORY_TEMPLATES:
        if s["id"] == story_id:
            return s
    return None


@router.get("/stories")
def list_stories():
    """互动情景剧剧本库"""
    return [{"id": s["id"], "title": s["title"], "topic": s["topic"]} for s in STORY_TEMPLATES]


@router.post("/scene/start")
def scene_start(req: SceneStartRequest):
    """开场：生成第 1 幕（含 3 个选项，正确答案不下发）。同步 def：LLM 调用走线程池"""
    if _rag is None:
        raise HTTPException(status_code=503, detail="RAG 引擎未初始化")
    story = _get_story(req.story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="剧本不存在")
    key = (req.story_id, 1)
    if key not in _scenes:
        try:
            data = _rag.generate_scene_start(story["topic"], story["search_query"])
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        _scenes[key] = data
    scene = _scenes[key]
    return {"story_id": req.story_id, "scene_index": 1, "total_scenes": TOTAL_SCENES,
            "scene_text": scene["scene_text"], "options": scene["options"]}


@router.post("/scene/next")
def scene_next(req: SceneNextRequest):
    """判定本次选择 + 推进下一幕；最后一幕之后返回结局（避坑笔记）。同步 def：LLM 调用走线程池"""
    if _rag is None:
        raise HTTPException(status_code=503, detail="RAG 引擎未初始化")
    story = _get_story(req.story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="剧本不存在")
    prev = _scenes.get((req.story_id, req.scene_index))
    if prev is None:
        raise HTTPException(status_code=404, detail="场景已失效，请重新开始")
    ck = (req.story_id, req.scene_index, req.choice)
    if ck in _next_cache:
        return _next_cache[ck]

    is_ending = req.scene_index >= TOTAL_SCENES
    try:
        data = _rag.generate_scene_next(
            story["topic"], story["search_query"],
            prev["scene_text"], prev["options"], prev.get("correct_key", ""),
            req.choice, is_ending=is_ending)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 对错以程序比对为准，解释由 LLM 生成
    verdict = data.get("verdict") or {}
    verdict["correct"] = (req.choice == prev.get("correct_key", ""))
    result = {"story_id": req.story_id, "verdict": verdict}

    if is_ending:
        ending = data.get("ending") or {}
        result["next"] = {"scene_index": req.scene_index + 1, "is_ending": True,
                          "summary": ending.get("summary", ""),
                          "lessons": ending.get("lessons", [])}
    else:
        nxt = data.get("next") or {}
        if not nxt.get("scene_text") or not isinstance(nxt.get("options"), list) or len(nxt["options"]) != 3:
            raise HTTPException(status_code=502, detail="剧本生成结果不完整，请重试")
        _scenes[(req.story_id, req.scene_index + 1)] = nxt  # 含 correct_key，供下一轮判定
        result["next"] = {"scene_index": req.scene_index + 1, "is_ending": False,
                          "scene_text": nxt["scene_text"], "options": nxt["options"]}
    _next_cache[ck] = result
    return result


# ── 普法海报（图片科普：LLM 文案 + 前端渲染） ──

@router.post("/poster")
def make_poster(req: TopicRequest):
    """生成普法海报文案 {title, slogan, points, tip, law_basis}。同步 def：LLM 调用走线程池"""
    if _rag is None:
        raise HTTPException(status_code=503, detail="RAG 引擎未初始化")
    try:
        return _rag.generate_poster(req.topic, req.search_query)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── 普法短片（视频科普：LLM 分镜 + edge-tts 配音，可降级为无声） ──

_TTS_VOICE = "zh-CN-XiaoxiaoNeural"


@router.post("/video")
def make_video(req: TopicRequest):
    """生成分镜脚本 {title, scenes:[{visual, subtitle}]} + audio: [dataURI, ...]。同步 def：LLM 调用走线程池"""
    if _rag is None:
        raise HTTPException(status_code=503, detail="RAG 引擎未初始化")
    try:
        data = _rag.generate_video(req.topic, req.search_query)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # 线程池线程中无运行中的事件循环，用 asyncio.run 跑 edge-tts 异步合成
    data["audio"] = asyncio.run(_synthesize_audio(data.get("scenes") or []))
    return data


# ── 预置内容（已生成的海报/短片，打开即看，无需等待 LLM） ──

def _load_presets(filename: str) -> list:
    """读取预置 JSON 文件；缺失/损坏时返回空列表（前端展示空态提示）"""
    try:
        return json.loads((_PRESETS_DIR / filename).read_text(encoding="utf-8"))
    except Exception:
        return []


@router.get("/poster/presets")
def poster_presets():
    """已生成的普法海报（全量：文案 JSON 体积小）"""
    return _load_presets("preset_posters.json")


@router.get("/video/presets")
def video_presets():
    """已生成的普法短片列表（轻量：不含配音 base64）"""
    items = []
    for v in _load_presets("preset_videos.json"):
        items.append({
            "id": v.get("id"),
            "topic": v.get("topic", ""),
            "title": v.get("title", ""),
            "scene_count": len(v.get("scenes") or []),
            "has_audio": any(v.get("audio") or []),
        })
    return items


@router.get("/video/presets/{preset_id}")
def video_preset_detail(preset_id: int):
    """单部预置短片全文（含配音 dataURI，体量大故按需拉取）"""
    for v in _load_presets("preset_videos.json"):
        if v.get("id") == preset_id:
            return v
    raise HTTPException(status_code=404, detail="该预置短片不存在")


async def _synthesize_audio(scenes: list) -> list:
    """为每个分镜旁白合成语音（edge-tts），未安装/失败时静默降级为空列表"""
    try:
        import edge_tts
    except ImportError:
        return []
    audio = []
    try:
        for sc in scenes:
            text = (sc.get("subtitle") or "").strip()
            if not text:
                audio.append("")
                continue
            buf = io.BytesIO()
            comm = edge_tts.Communicate(text, voice=_TTS_VOICE)
            async for chunk in comm.stream():
                if chunk.get("type") == "audio":
                    buf.write(chunk["data"])
            mp3 = buf.getvalue()
            if mp3:
                audio.append("data:audio/mpeg;base64," + base64.b64encode(mp3).decode())
            else:
                audio.append("")
    except Exception:
        return []
    return audio
