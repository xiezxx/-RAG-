"""
法条版本对照 API（模块5 时效感知·法条版本管理）
"""
from fastapi import APIRouter, Query

from src.rag.version_compare import get_index

router = APIRouter(prefix="/api/version", tags=["version"])


@router.get("/laws")
def list_laws():
    """列出存在新旧版本的法律及版本信息"""
    return get_index().laws()


@router.get("/compare")
def compare(law: str = Query(..., description="法律名（全称或简称）"),
            article: str = Query(..., description="条文号（46 / 第46条 / 第四十六条）")):
    """对比某部法律某条文的新旧版本内容"""
    result = get_index().compare(law, article)
    if not result:
        return {"found": False, "message": "该法律或条文暂无多版本修订数据"}
    result["found"] = True
    return result
