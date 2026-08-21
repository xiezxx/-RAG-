"""
知识图谱管理 API — 实体和关系的增删改查
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from src.database.neo4j_client import Neo4jClient

router = APIRouter(prefix="/api/kg", tags=["kg"])


class EntityItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    entity_type: str = Field(..., min_length=1)


class RelationItem(BaseModel):
    source_type: str  # Article
    source_id: str
    target_type: str  # LegalConcept / RightObligation / ...
    target_name: str
    relation: str  # DEFINES / PRESCRIBES / PROHIBITS


# 全局 Neo4j 客户端单例（避免连接泄漏）
_neo4j = None

def get_neo4j():
    global _neo4j
    if _neo4j is None:
        _neo4j = Neo4jClient()
    return _neo4j

# 合法的标签和关系类型白名单
VALID_LABELS = {"LegalConcept", "RightObligation", "IllegalAct", "LegalLiability", "Article", "Statute"}
VALID_RELATIONS = {"DEFINES", "PRESCRIBES", "PROHIBITS", "RESULTS_IN"}

LABEL_MAP = {
    "LegalConcept": "LegalConcept",
    "RightObligation": "RightObligation",
    "IllegalAct": "IllegalAct",
    "LegalLiability": "LegalLiability",
}


@router.get("/entities")
def list_entities(entity_type: str = "LegalConcept"):
    """列出指定类型的 KG 实体（同步 def：Neo4j 查询走线程池）"""
    neo4j = get_neo4j()
    label_map = {
        "LegalConcept": "LegalConcept",
        "RightObligation": "RightObligation",
        "IllegalAct": "IllegalAct",
        "LegalLiability": "LegalLiability",
    }
    label = label_map.get(entity_type)
    if not label:
        raise HTTPException(status_code=400, detail="invalid entity_type")
    with neo4j.driver.session() as s:
        result = s.run(f"MATCH (n:{label}) RETURN n.name AS name, n.description AS description ORDER BY n.name")
        return [{"name": r["name"], "description": r["description"] or ""} for r in result]


@router.get("/all-entities")
def list_all_entities():
    """列出所有 KG 实体（按类型分组）"""
    neo4j = get_neo4j()
    result = {}
    with neo4j.driver.session() as s:
        for label in ["LegalConcept", "RightObligation", "IllegalAct", "LegalLiability"]:
            r = s.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()
            result[label] = r["c"] if r else 0
    return result


@router.post("/entities")
def create_entity(item: EntityItem):
    """创建 KG 实体"""
    neo4j = get_neo4j()
    label_map = {
        "LegalConcept": "LegalConcept",
        "RightObligation": "RightObligation",
        "IllegalAct": "IllegalAct",
        "LegalLiability": "LegalLiability",
    }
    label = label_map.get(item.entity_type)
    if not label:
        return {"error": "未知实体类型"}
    with neo4j.driver.session() as s:
        s.run(
            f"MERGE (n:{label} {{name: $name}}) SET n.description = $desc",
            name=item.name, desc=item.description
        )
    return {"ok": True, "name": item.name}


@router.delete("/entities")
def delete_entity(entity_type: str, name: str):
    """删除 KG 实体"""
    neo4j = get_neo4j()
    label_map = {
        "LegalConcept": "LegalConcept",
        "RightObligation": "RightObligation",
        "IllegalAct": "IllegalAct",
        "LegalLiability": "LegalLiability",
    }
    label = label_map.get(entity_type)
    if not label:
        return {"error": "未知实体类型"}
    with neo4j.driver.session() as s:
        s.run(f"MATCH (n:{label} {{name: $name}}) DETACH DELETE n", name=name)
    return {"ok": True}


@router.post("/relations")
def create_relation(rel: RelationItem):
    """创建 KG 关系（白名单校验防注入）"""
    if rel.relation not in VALID_RELATIONS:
        return {"error": f"无效关系类型: {rel.relation}"}
    if rel.target_type not in VALID_LABELS:
        return {"error": f"无效目标类型: {rel.target_type}"}

    neo4j = get_neo4j()
    with neo4j.driver.session() as s:
        s.run(
            f"""
            MATCH (a:Article {{id: $source_id}})
            MATCH (b:{rel.target_type} {{name: $target_name}})
            MERGE (a)-[:{rel.relation}]->(b)
            """,
            source_id=rel.source_id,
            target_name=rel.target_name,
        )
    return {"ok": True}


@router.get("/stats")
def kg_stats():
    """KG 综合统计"""
    neo4j = get_neo4j()
    return neo4j.get_stats()
