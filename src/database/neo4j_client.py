"""
Neo4j 数据库客户端 — 连接管理、Schema 初始化、数据导入（含时效属性）
"""
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from typing import List, Dict, Optional
from src.config import Config


class Neo4jClient:
    """Neo4j 图数据库客户端"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD),
        )

    # ── 连接检查 ──────────────────────────────────────

    def check_connection(self) -> bool:
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    # ── Schema 初始化 ──────────────────────────────────

    def init_schema(self):
        """创建约束和索引（含扩展 KG 实体）"""
        constraints = [
            "CREATE CONSTRAINT statute_name IF NOT EXISTS FOR (s:Statute) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT case_number IF NOT EXISTS FOR (c:Case) REQUIRE c.case_number IS UNIQUE",
            "CREATE CONSTRAINT issue_name IF NOT EXISTS FOR (i:Issue) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT court_name IF NOT EXISTS FOR (ct:Court) REQUIRE ct.name IS UNIQUE",
            # 扩展 KG：法律概念、权利义务、违法行为、法律责任
            "CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (lc:LegalConcept) REQUIRE lc.name IS UNIQUE",
            "CREATE CONSTRAINT rob_name IF NOT EXISTS FOR (ro:RightObligation) REQUIRE ro.name IS UNIQUE",
            "CREATE CONSTRAINT act_name IF NOT EXISTS FOR (ia:IllegalAct) REQUIRE ia.name IS UNIQUE",
            "CREATE CONSTRAINT liability_name IF NOT EXISTS FOR (ll:LegalLiability) REQUIRE ll.name IS UNIQUE",
        ]
        indexes = [
            "CREATE INDEX statute_status IF NOT EXISTS FOR (s:Statute) ON (s.status)",
            "CREATE INDEX article_status IF NOT EXISTS FOR (a:Article) ON (a.status)",
        ]
        with self.driver.session() as session:
            for stmt in constraints:
                try:
                    session.run(stmt)
                except Exception:
                    pass
            for stmt in indexes:
                try:
                    session.run(stmt)
                except Exception:
                    pass

    # ── 法律法规导入（含时效属性）──────────────────────

    def import_statute(
        self,
        name: str,
        articles: List[Dict[str, str]],
        publish_date: str = "",
        effective_date: str = "",
        expiry_date: str = "",
        status: str = "现行有效",
    ):
        """导入一部法律及其条文
        Args:
            name: 法律名称
            articles: [{"id": "第1条", "content": "..."}, ...]
            publish_date: 发布日期 YYYY-MM-DD
            effective_date: 生效日期 YYYY-MM-DD
            expiry_date: 失效日期 YYYY-MM-DD（空=未失效）
            status: 现行有效/已被修订/已废止/尚未生效/效力未知
        """
        with self.driver.session() as session:
            session.run(
                """
                MERGE (s:Statute {name: $name})
                SET s.publish_date = $publish_date,
                    s.effective_date = $effective_date,
                    s.expiry_date = $expiry_date,
                    s.status = $status
                WITH s
                UNWIND $articles AS art
                MERGE (a:Article {id: $name + ' ' + art.id})
                SET a.content = art.content,
                    a.statute = $name,
                    a.effective_date = $effective_date,
                    a.status = $status
                MERGE (a)-[:BELONGS_TO]->(s)
                """,
                name=name,
                articles=articles,
                publish_date=publish_date,
                effective_date=effective_date,
                expiry_date=expiry_date,
                status=status,
            )

    # ── 案例导入 ──────────────────────────────────────

    def import_case(self, case: Dict):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (c:Case {case_number: $case_number})
                SET c.court = $court,
                    c.judge_date = $judge_date,
                    c.case_content = $case_content,
                    c.reasoning = $reasoning,
                    c.judgment = $judgment,
                    c.keywords = $keywords

                MERGE (ct:Court {name: $court})
                MERGE (c)-[:TRIED_AT]->(ct)

                FOREACH (issue_name IN $issues |
                    MERGE (i:Issue {name: issue_name})
                    MERGE (c)-[:INVOLVES]->(i)
                )

                FOREACH (law_ref IN $legal_basis |
                    MERGE (a:Article {id: law_ref})
                    MERGE (c)-[:CITES]->(a)
                )
                """,
                **case,
            )

    # ── 图谱检索 ──────────────────────────────────────

    def find_related_articles(
        self, keywords: List[str], limit: int = 5,
        prefer_current: bool = True,
    ) -> List[Dict]:
        """根据关键词查找相关法条，可选优先返回现行有效条文"""
        with self.driver.session() as session:
            query = """
                MATCH (a:Article)
                WHERE (any(kw IN $keywords WHERE a.content CONTAINS kw)
                   OR any(kw IN $keywords WHERE a.id CONTAINS kw))
            """
            if prefer_current:
                query += """
                WITH a, CASE WHEN a.status = '现行有效' THEN 0 ELSE 1 END AS priority
                RETURN a.id AS article_id, a.content AS content, a.statute AS statute,
                       a.effective_date AS effective_date, a.status AS status
                ORDER BY priority, a.effective_date DESC
                LIMIT $limit
                """
            else:
                query += """
                RETURN a.id AS article_id, a.content AS content, a.statute AS statute,
                       a.effective_date AS effective_date, a.status AS status
                ORDER BY a.effective_date DESC
                LIMIT $limit
                """

            result = session.run(query, keywords=keywords, limit=limit)
            return [record.data() for record in result]

    def find_similar_cases(
        self, keywords: List[str], limit: int = 3,
    ) -> List[Dict]:
        """多路径检索相似案例：关键词 + 争议点图谱（INVOLVES）"""
        with self.driver.session() as session:
            result = session.run(
                """
                // 路径1: 关键词直接匹配案例
                MATCH (c:Case)
                WHERE any(kw IN $keywords WHERE kw IN c.keywords)
                OPTIONAL MATCH (c)-[:TRIED_AT]->(ct:Court)
                OPTIONAL MATCH (c)-[:INVOLVES]->(i:Issue)
                WITH c, ct, COLLECT(DISTINCT i.name) AS issues
                RETURN c.case_number AS case_number,
                       c.facts AS case_content,
                       c.judgment AS judgment,
                       c.keywords AS keywords,
                       ct.name AS court,
                       issues,
                       'keyword_match' AS match_type,
                       1 AS priority

                UNION

                // 路径2: 通过争议点(INVOLVES)匹配 → 更广的案例覆盖
                MATCH (c:Case)-[:INVOLVES]->(i:Issue)
                WHERE any(kw IN $keywords WHERE i.name CONTAINS kw)
                OPTIONAL MATCH (c)-[:TRIED_AT]->(ct:Court)
                OPTIONAL MATCH (c)-[:INVOLVES]->(i2:Issue)
                WITH c, ct, COLLECT(DISTINCT i2.name) AS issues
                RETURN c.case_number AS case_number,
                       c.facts AS case_content,
                       c.judgment AS judgment,
                       c.keywords AS keywords,
                       ct.name AS court,
                       issues,
                       'issue_graph' AS match_type,
                       2 AS priority

                ORDER BY priority
                LIMIT $limit
                """,
                keywords=keywords,
                limit=limit,
            )
            return [record.data() for record in result]

    def find_case_by_issue(self, issue: str, limit: int = 5) -> List[Dict]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Case)-[:INVOLVES]->(i:Issue)
                WHERE i.name CONTAINS $issue
                RETURN c.case_number AS case_number,
                       c.case_content AS case_content,
                       c.judgment AS judgment,
                       c.keywords AS keywords
                LIMIT $limit
                """,
                issue=issue,
                limit=limit,
            )
            return [record.data() for record in result]

    def find_articles_by_time(
        self, keywords: List[str], reference_date: str, limit: int = 5,
    ) -> List[Dict]:
        """按时间基准检索：返回 reference_date 时有效的条文
        Args:
            reference_date: 参考日期 YYYY-MM-DD，如 '2020-06-01'
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Article)
                WHERE (any(kw IN $keywords WHERE a.content CONTAINS kw)
                   OR any(kw IN $keywords WHERE a.id CONTAINS kw))
                  AND (a.effective_date <= $ref_date OR a.effective_date = '')
                  AND (a.expiry_date = '' OR a.expiry_date >= $ref_date)
                RETURN a.id AS article_id, a.content AS content, a.statute AS statute,
                       a.effective_date AS effective_date, a.status AS status
                ORDER BY a.effective_date DESC
                LIMIT $limit
                """,
                keywords=keywords,
                ref_date=reference_date,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_statute_versions(self, law_name: str) -> List[Dict]:
        """获取某部法律的所有版本"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Statute)
                WHERE s.name CONTAINS $name
                OPTIONAL MATCH (s)<-[:BELONGS_TO]-(a:Article)
                RETURN s.name AS name, s.publish_date AS publish_date,
                       s.effective_date AS effective_date, s.expiry_date AS expiry_date,
                       s.status AS status, count(a) AS article_count
                ORDER BY s.effective_date DESC
                """,
                name=law_name,
            )
            return [record.data() for record in result]

    # ── KG 扩展实体导入 ────────────────────────────────

    def import_kg_entities(self, entities: Dict):
        """导入 KG 扩展实体和关系
        Args:
            entities: {
                "concepts": [{"name": "经济补偿金", "description": "..."}, ...],
                "rights_obligations": [{"name": "取得劳动报酬的权利", "type": "right", "article_id": "..."}],
                "illegal_acts": [{"name": "违法解除劳动合同", "article_id": "..."}],
                "liabilities": [{"name": "支付赔偿金", "description": "...", "illegal_act": "..."}],
            }
        """
        with self.driver.session() as session:
            # 法律概念
            for c in entities.get("concepts", []):
                session.run(
                    """
                    MERGE (lc:LegalConcept {name: $name})
                    SET lc.description = $desc
                    WITH lc
                    MATCH (a:Article {id: $article_id})
                    MERGE (a)-[:DEFINES]->(lc)
                    """,
                    name=c["name"], desc=c.get("description", ""),
                    article_id=c.get("article_id", ""),
                )

            # 权利与义务
            for r in entities.get("rights_obligations", []):
                session.run(
                    """
                    MERGE (ro:RightObligation {name: $name})
                    SET ro.type = $type
                    WITH ro
                    MATCH (a:Article {id: $article_id})
                    MERGE (a)-[:PRESCRIBES]->(ro)
                    """,
                    name=r["name"], type=r.get("type", "obligation"),
                    article_id=r.get("article_id", ""),
                )

            # 违法行为
            for act in entities.get("illegal_acts", []):
                session.run(
                    """
                    MERGE (ia:IllegalAct {name: $name})
                    SET ia.description = $desc
                    WITH ia
                    MATCH (a:Article {id: $article_id})
                    MERGE (a)-[:PROHIBITS]->(ia)
                    """,
                    name=act["name"], desc=act.get("description", ""),
                    article_id=act.get("article_id", ""),
                )

            # 法律责任
            for liab in entities.get("liabilities", []):
                session.run(
                    """
                    MERGE (ll:LegalLiability {name: $name})
                    SET ll.description = $desc
                    """,
                    name=liab["name"], desc=liab.get("description", ""),
                )
                if liab.get("illegal_act"):
                    session.run(
                        """
                        MATCH (ia:IllegalAct {name: $act_name})
                        MATCH (ll:LegalLiability {name: $liab_name})
                        MERGE (ia)-[:RESULTS_IN]->(ll)
                        """,
                        act_name=liab["illegal_act"], liab_name=liab["name"],
                    )

    def expand_by_graph(
        self, keywords: List[str], limit: int = 5,
    ) -> List[Dict]:
        """图关系扩展检索：多路径从种子法条找关联法条
        路径1: 同部法律关联（种子附近条文 + 同法其他条文）
        路径2: 实体名反向查找（LegalConcept/IllegalAct → 法条）
        路径3: kg_entity 图扩展
        路径4: 法条互引
        """
        seen_ids = set()
        records = []
        LABOUR_STATUTES = ['劳动', '劳动合同', '社会保险', '工伤', '就业', '劳务']

        with self.driver.session() as session:
            # ── 路径1: 同部法律扩展（最可靠，717条边）──
            # 找到匹配关键词的种子法条，返回同法中相邻的条文
            r1 = session.run(
                """
                MATCH (seed:Article)
                WHERE any(kw IN $keywords WHERE seed.content CONTAINS kw)
                   OR any(kw IN $keywords WHERE seed.id CONTAINS kw)
                WITH seed,
                     CASE WHEN any(ls IN $labour_stats WHERE seed.statute CONTAINS ls)
                          THEN 0 ELSE 1 END AS priority
                ORDER BY priority, seed.id
                LIMIT 3

                // 找到同部法律且 id 相邻的条文
                MATCH (seed)-[:BELONGS_TO]->(st:Statute)<-[:BELONGS_TO]-(related:Article)
                WHERE related <> seed
                WITH related, seed, st
                // 优先选择与种子 id 接近的条文（编号相邻说明内容相关）
                ORDER BY
                    CASE WHEN any(ls IN $labour_stats WHERE st.name CONTAINS ls) THEN 0 ELSE 1 END,
                    abs(toInteger(split(related.id, '_')[size(split(related.id, '_'))-1]) -
                        toInteger(split(seed.id, '_')[size(split(seed.id, '_'))-1]))
                RETURN DISTINCT
                    related.id AS article_id, related.content AS content,
                    related.statute AS statute, related.effective_date AS effective_date,
                    related.status AS status, '同部法律关联' AS via_entity,
                    ['BELONGS_TO'] AS via_type, 'same_statute' AS path
                LIMIT $limit
                """, keywords=keywords, labour_stats=LABOUR_STATUTES, limit=limit,
            )
            for rec in r1:
                data = self._clean_record(rec)
                aid = data.get("article_id")
                if aid and aid not in seen_ids:
                    seen_ids.add(aid)
                    records.append(data)

            # ── 路径2: 实体名反向查找 ──
            if len(records) < limit:
                r2 = session.run(
                    """
                    MATCH (entity)<-[:DEFINES|PRESCRIBES|PROHIBITS]-(related:Article)
                    WHERE (entity:LegalConcept OR entity:IllegalAct)
                    AND any(kw IN $keywords WHERE entity.name CONTAINS kw)
                    RETURN DISTINCT
                        related.id AS article_id, related.content AS content,
                        related.statute AS statute, related.effective_date AS effective_date,
                        related.status AS status, entity.name AS via_entity,
                        labels(entity) AS via_type, 'entity_reverse' AS path
                    LIMIT $limit
                    """, keywords=keywords, limit=limit - len(records),
                )
                for rec in r2:
                    data = self._clean_record(rec)
                    aid = data.get("article_id")
                    if aid and aid not in seen_ids:
                        seen_ids.add(aid)
                        records.append(data)

            # ── 路径3: KG 实体往返扩展 ──
            if len(records) < limit:
                r3 = session.run(
                    """
                    MATCH (seed:Article)
                    WHERE any(kw IN $keywords WHERE seed.content CONTAINS kw)
                       OR any(kw IN $keywords WHERE seed.id CONTAINS kw)
                    WITH seed,
                         CASE WHEN any(ls IN $labour_stats WHERE seed.statute CONTAINS ls)
                              THEN 0 ELSE 1 END AS priority
                    ORDER BY priority
                    LIMIT 5
                    MATCH (seed)-[:DEFINES|PRESCRIBES|PROHIBITS]->(entity)
                    WHERE entity:LegalConcept OR entity:RightObligation OR entity:IllegalAct
                    MATCH (entity)<-[:DEFINES|PRESCRIBES|PROHIBITS]-(related:Article)
                    WHERE related <> seed
                    RETURN DISTINCT
                        related.id AS article_id, related.content AS content,
                        related.statute AS statute, related.effective_date AS effective_date,
                        related.status AS status, entity.name AS via_entity,
                        labels(entity) AS via_type, 'kg_entity' AS path
                    LIMIT $limit
                    """, keywords=keywords, labour_stats=LABOUR_STATUTES,
                    limit=limit - len(records),
                )
                for rec in r3:
                    data = self._clean_record(rec)
                    aid = data.get("article_id")
                    if aid and aid not in seen_ids:
                        seen_ids.add(aid)
                        records.append(data)

            # ── 路径4: 法条引用扩展 ──
            if len(records) < limit:
                r4 = session.run(
                    """
                    MATCH (seed:Article)
                    WHERE any(kw IN $keywords WHERE seed.content CONTAINS kw)
                       OR any(kw IN $keywords WHERE seed.id CONTAINS kw)
                    WITH seed,
                         CASE WHEN any(ls IN $labour_stats WHERE seed.statute CONTAINS ls)
                              THEN 0 ELSE 1 END AS priority
                    ORDER BY priority
                    LIMIT 5
                    MATCH (seed)-[:CITES]->(related:Article)
                    WHERE related <> seed
                    RETURN DISTINCT
                        related.id AS article_id, related.content AS content,
                        related.statute AS statute, related.effective_date AS effective_date,
                        related.status AS status, '法条互引' AS via_entity,
                        ['CITES'] AS via_type, 'citation' AS path
                    LIMIT $limit
                    """, keywords=keywords, labour_stats=LABOUR_STATUTES,
                    limit=limit - len(records),
                )
                for rec in r4:
                    data = self._clean_record(rec)
                    aid = data.get("article_id")
                    if aid and aid not in seen_ids:
                        seen_ids.add(aid)
                        records.append(data)

        return records

    @staticmethod
    def _clean_record(record):
        """清洗 Neo4j 返回记录：去 None、扁平化列表"""
        data = {}
        for k, v in record.data().items():
            if v is None:
                continue
            if isinstance(v, list):
                # 扁平化标签列表
                filtered = [x for x in v if x and not str(x).startswith('_')]
                data[k] = filtered[0] if len(filtered) == 1 else '/'.join(filtered) if filtered else ''
            else:
                data[k] = v
        return data

    # ── 统计信息 ──────────────────────────────────────

    def get_stats(self) -> Dict[str, int]:
        with self.driver.session() as session:
            result = session.run(
                """
                OPTIONAL MATCH (s:Statute)
                OPTIONAL MATCH (a:Article)
                OPTIONAL MATCH (c:Case)
                OPTIONAL MATCH (i:Issue)
                OPTIONAL MATCH (ct:Court)
                RETURN
                    count(DISTINCT s) AS statutes,
                    count(DISTINCT a) AS articles,
                    count(DISTINCT c) AS cases,
                    count(DISTINCT i) AS issues,
                    count(DISTINCT ct) AS courts
                """
            )
            data = result.single().data()
            return {k: v for k, v in data.items()}

    def get_timeliness_stats(self) -> Dict[str, int]:
        """获取时效统计：各状态的条文数量"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Article)
                RETURN a.status AS status, count(a) AS count
                ORDER BY count DESC
                """
            )
            stats = {}
            for record in result:
                s = record["status"] or "未知"
                stats[s] = record["count"]
            return stats

    def close(self):
        self.driver.close()
