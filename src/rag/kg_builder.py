"""
知识图谱构建器 — 规则 + LLM 辅助从法条中抽取法律概念、权利义务、违法行为与法律责任
"""
import re
import json
from typing import List, Dict, Set
from collections import defaultdict

# ── 规则模式 ──────────────────────────────────────────

# 模式: (正则, 实体类型, 关系类型)
EXTRACTION_RULES = [
    # 法律概念: "XX是指..."
    (r'(?:所称|所称的|本法所称|本条例所称)?\s*[""]([^""]+)[""].*?[，,]\s*(?:是指?|是指|指|即|系指)([^。；;]+)',
     'concept', 'DEFINES'),

    # 法律概念: "XX，是指..."  (with comma before)
    (r'([^，,。；;]{2,20})[，,]\s*(?:是指?|是指|指|即|系指)([^。；;]+)',
     'concept', 'DEFINES'),

    # 权利: "XX享有...权利" "XX有权..."
    (r'(劳动者|用人单位|职工|女职工|未成年工|工会)\s*(?:享有|依法享有|有权|可以)\s*([^。；;]{4,40}(?:权|利|假|休息|保护|安全|卫生|健康))',
     'right', 'PRESCRIBES'),

    # 义务: "XX应当..." "XX必须..." "XX不得..."
    (r'(用人单位|劳动者|职工)\s*(?:应当|必须|应该)\s*([^。；;]{4,50})',
     'obligation', 'PRESCRIBES'),

    # 禁止行为: "XX不得..." "禁止XX..."
    (r'(?:禁止|严禁)\s*([^。；;]{4,40})',
     'prohibition', 'PROHIBITS'),

    # 违法行为: "XX有下列情形之一的" "XX行为"
    (r'(?:有下列行为之一的|有下列情形之一的)[，,]?\s*(?:处|责令|给予|处以|罚款|赔偿|承担)([^。；;]+)',
     'illegal_act', 'PROHIBITS'),

    # 法律责任: "处XX罚款" "承担赔偿责任" "责令XX"
    (r'(?:处|处以|罚款|责令|承担|给予)\s*([^。；;]{2,30}(?:罚款|赔偿|责任|处分|处罚))',
     'liability', 'RESULTS_IN'),
]

# 已知的劳动法核心概念（作为种子，即使规则未命中也会创建）
CORE_CONCEPTS = {
    "劳动关系": "用人单位与劳动者之间的权利义务关系",
    "劳动合同": "劳动者与用人单位确立劳动关系、明确双方权利义务的协议",
    "经济补偿金": "用人单位依法解除或终止劳动合同时支付给劳动者的补偿",
    "赔偿金": "用人单位违法解除劳动合同应支付的赔偿",
    "竞业限制": "劳动者离职后一定期限内不得从事与原单位有竞争关系的业务",
    "试用期": "劳动合同当事人双方相互考察的期限",
    "工伤": "劳动者在工作过程中因工作原因受到的伤害",
    "职业病": "劳动者在职业活动中因接触有害因素引起的疾病",
    "加班": "劳动者在法定工作时间之外延长工作时间",
    "年休假": "劳动者依法享有的带薪年休假",
    "产假": "女职工生育享受的法定假期",
    "社会保险": "国家建立的养老、医疗、工伤、失业、生育等保险制度",
    "劳务派遣": "劳务派遣单位与被派遣劳动者建立劳动关系后将劳动者派往用工单位",
    "集体合同": "工会与企业签订的规范劳动关系的书面协议",
    "劳动争议": "劳动者与用人单位之间因劳动权利义务发生的争议",
    "最低工资": "劳动者在法定工作时间提供正常劳动的最低劳动报酬",
}

CORE_ILLEGAL_ACTS = {
    "违法解除劳动合同": "用人单位违反法律规定单方解除劳动合同",
    "拖欠劳动报酬": "用人单位未按时足额支付劳动者工资",
    "未签订书面劳动合同": "用人单位超过一个月未与劳动者签订书面劳动合同",
    "违法约定试用期": "用人单位违反法律规定约定试用期",
    "强迫劳动": "以暴力、威胁或非法限制人身自由的手段强迫劳动",
    "就业歧视": "基于性别、民族、年龄等因素的不公平用工对待",
    "未缴纳社会保险": "用人单位未依法为劳动者缴纳社会保险费",
}

CORE_LIABILITIES = {
    "支付赔偿金": ("违法解除或终止劳动合同应支付双倍经济补偿金", "违法解除劳动合同"),
    "支付经济补偿金": ("依法解除或终止劳动合同时应支付的补偿", ""),
    "支付双倍工资": ("超过一个月未签书面合同应支付双倍工资", "未签订书面劳动合同"),
    "行政处罚": ("劳动行政部门依法给予的警告、罚款等处罚", ""),
    "承担工伤赔偿责任": ("未参加工伤保险的用人单位承担工伤赔偿", "未缴纳社会保险"),
    "补缴社会保险费": ("用人单位补缴欠缴的社会保险费", "未缴纳社会保险"),
}


class KGBuilder:
    """劳动法知识图谱构建器"""

    def __init__(self, neo4j_client):
        self.neo4j = neo4j_client

    # ── 规则抽取 ─────────────────────────────────────

    def extract_from_articles(self, articles: List[Dict]) -> Dict:
        """从法条内容中抽取 KG 实体"""
        entities = {
            "concepts": [],
            "rights_obligations": [],
            "illegal_acts": [],
            "liabilities": [],
        }
        seen: Dict[str, Set[str]] = defaultdict(set)

        for art in articles:
            content = art.get("content", "") or ""
            article_id = art.get("id", "") or ""

            for pattern, etype, rel_type in EXTRACTION_RULES:
                for match in re.finditer(pattern, content):
                    if etype == 'concept':
                        name = match.group(1).strip()
                        desc = match.group(2).strip()[:200]
                        if 2 <= len(name) <= 30 and name not in seen["concepts"]:
                            seen["concepts"].add(name)
                            entities["concepts"].append({
                                "name": name, "description": desc,
                                "article_id": article_id,
                            })
                    elif etype == 'right':
                        name = match.group(2).strip()
                        if 2 <= len(name) <= 30 and name not in seen["rights_obligations"]:
                            seen["rights_obligations"].add(name)
                            entities["rights_obligations"].append({
                                "name": name, "type": "right",
                                "article_id": article_id,
                            })
                    elif etype == 'obligation':
                        name = match.group(2).strip()
                        if 3 <= len(name) <= 30 and name not in seen["rights_obligations"]:
                            seen["rights_obligations"].add(name)
                            entities["rights_obligations"].append({
                                "name": name, "type": "obligation",
                                "article_id": article_id,
                            })
                    elif etype in ('prohibition', 'illegal_act'):
                        name = match.group(1).strip()
                        if 3 <= len(name) <= 40 and name not in seen["illegal_acts"]:
                            seen["illegal_acts"].add(name)
                            entities["illegal_acts"].append({
                                "name": name, "description": "",
                                "article_id": article_id,
                            })
                    elif etype == 'liability':
                        name = match.group(1).strip()
                        if 2 <= len(name) <= 30 and name not in seen["liabilities"]:
                            seen["liabilities"].add(name)
                            entities["liabilities"].append({
                                "name": name, "description": "",
                                "illegal_act": "",
                            })

        return entities

    # ── 核心种子实体 ─────────────────────────────────

    @staticmethod
    def get_core_entities() -> Dict:
        """返回劳动法核心概念、违法行为、法律责任种子数据"""
        entities = {
            "concepts": [],
            "rights_obligations": [],
            "illegal_acts": [],
            "liabilities": [],
        }

        for name, desc in CORE_CONCEPTS.items():
            entities["concepts"].append({
                "name": name, "description": desc, "article_id": "",
            })
        for name, desc in CORE_ILLEGAL_ACTS.items():
            entities["illegal_acts"].append({
                "name": name, "description": desc, "article_id": "",
            })
        for name, data in CORE_LIABILITIES.items():
            desc, illegal_act = data if isinstance(data, tuple) else (data, "")
            entities["liabilities"].append({
                "name": name, "description": desc, "illegal_act": illegal_act,
            })

        return entities

    # ── 全量构建 ─────────────────────────────────────

    def build(self, articles: List[Dict], use_core: bool = True):
        """从法条列表构建 KG，包括规则抽取 + 核心种子 + LLM 增强"""
        print(f"🔧 从 {len(articles)} 条法条构建知识图谱...")

        # 1. 核心种子实体
        if use_core:
            core = self.get_core_entities()
            print(f"  📌 核心种子: {sum(len(v) for v in core.values())} 个实体")
            self.neo4j.import_kg_entities(core)

        # 2. 规则抽取
        extracted = self.extract_from_articles(articles)
        total = sum(len(v) for v in extracted.values())
        print(f"  🔍 规则抽取: {total} 个实体")
        if total > 0:
            self.neo4j.import_kg_entities(extracted)

        # 统计
        stats = self.neo4j.get_stats()
        print(f"  ✅ KG 构建完成: {stats}")

        return extracted

    # ── LLM 增强抽取（可选，用于关键法条）───────────────

    def llm_enhance(self, article_id: str, content: str, llm) -> Dict:
        """使用 LLM 从单条法条中抽取结构化实体关系"""
        prompt = f"""从以下中国劳动法条文中，提取法律概念、权利、义务、违法行为和法律责任。
以 JSON 格式返回（只返回 JSON，不要其他文字）：

{{
    "concepts": [{{"name": "概念名", "description": "简要说明"}}],
    "rights": [{{"name": "权利描述", "holder": "劳动者/用人单位"}}],
    "obligations": [{{"name": "义务描述", "bearer": "用人单位/劳动者"}}],
    "illegal_acts": [{{"name": "违法行为描述"}}],
    "liabilities": [{{"name": "法律责任描述"}}]
}}

法条内容：
{content}

只提取明确出现的实体，不要编造。若无某类实体返回空数组。"""

        try:
            from langchain_openai import ChatOpenAI
            from src.config import Config

            llm_instance = llm or ChatOpenAI(
                model=Config.LLM_MODEL,
                api_key=Config.LLM_API_KEY,
                base_url=Config.LLM_BASE_URL if Config.LLM_BASE_URL else None,
                temperature=0.0,
                max_tokens=1000,
            )
            resp = llm_instance.invoke(prompt)
            text = resp.content if hasattr(resp, 'content') else str(resp)

            # 清洗 JSON
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
            data = json.loads(text)
            return data
        except Exception as e:
            print(f"  ⚠️ LLM 抽取失败 [{article_id}]: {e}")
            return {}
