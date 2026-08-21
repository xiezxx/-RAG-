"""
法条版本对照 — 新旧版本条文对比数据源（模块5 时效感知·法条版本管理）

从 statutes 原始文件中识别同一法律的多个版本（如劳动合同法 2008 版与 2012 修订版），
按条文号切分后提供新旧条文内容对比，支撑前端「修订对比」展示。
"""
import os
import re
from typing import Dict, List, Optional

from src.config import Config
from src.rag.loader import (
    LegalDocumentLoader,
    _read_file,
    _extract_law_name_base,
    _parse_date_from_filename,
    split_articles,
    cn_num_to_int,
)


def _norm_law_name(law: str) -> str:
    """法律名归一化：接受全称或简称（自动补'中华人民共和国'前缀）"""
    law = (law or "").strip().strip("《》")
    if law.startswith("中华人民共和国"):
        return law
    return "中华人民共和国" + law


class VersionIndex:
    """新旧版本条文索引（懒加载 + 进程内缓存）"""

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or Config.DATA_DIR
        self._laws: Optional[Dict[str, dict]] = None
        self._loader = LegalDocumentLoader(self.data_dir)

    def _build(self) -> Dict[str, dict]:
        """扫描 statutes 目录，找出存在多个版本的法律并切分条文"""
        statutes_dir = os.path.join(self.data_dir, "statutes")
        laws: Dict[str, dict] = {}
        if not os.path.exists(statutes_dir):
            return laws

        # 按法律基础名分组，找出多版本法律
        groups: Dict[str, List[str]] = {}
        for filename in os.listdir(statutes_dir):
            if not (filename.endswith(".txt") or filename.endswith(".docx")):
                continue
            filepath = os.path.join(statutes_dir, filename)
            if os.path.getsize(filepath) < 100:
                continue  # 跳过空存根
            groups.setdefault(_extract_law_name_base(filename), []).append(filename)

        for base, files in groups.items():
            if len(files) < 2:
                continue
            # 按文件名日期排序（无日期后缀的旧版排最前）
            files.sort(key=lambda f: _parse_date_from_filename(f) or "0000-00-00")
            versions = []
            for filename in files:
                filepath = os.path.join(statutes_dir, filename)
                content = _read_file(filepath)
                dates = self._loader._extract_dates(filepath, content)
                is_latest = filename == files[-1]
                versions.append({
                    "filename": filename,
                    "publish_date": dates.get("publish_date", ""),
                    "effective_date": dates.get("effective_date", ""),
                    "status": self._loader._infer_status(dates.get("effective_date"), is_latest),
                    "articles": {no: body for no, body in split_articles(content)},
                })
            laws[base] = {"law_name": base, "versions": versions}

        return laws

    def _ensure_built(self) -> Dict[str, dict]:
        if self._laws is None:
            self._laws = self._build()
        return self._laws

    def laws(self) -> List[dict]:
        """列出存在新旧版本的法律及其版本信息"""
        result = []
        for entry in self._ensure_built().values():
            result.append({
                "law_name": entry["law_name"],
                "versions": [
                    {
                        "publish_date": v["publish_date"],
                        "effective_date": v["effective_date"],
                        "status": v["status"],
                    }
                    for v in entry["versions"]
                ],
            })
        return result

    def compare(self, law: str, article: str) -> Optional[dict]:
        """对比某法律某条文的新旧版本内容。
        law 接受全称/简称；article 接受 46 / 第46条 / 第四十六条。
        Returns: {law_name, article, changed, old: {...}, new: {...}}，无多版本数据时 None
        """
        laws = self._ensure_built()
        norm = _norm_law_name(law)
        entry = laws.get(norm) or laws.get(_norm_law_name(norm))
        if not entry or len(entry["versions"]) < 2:
            return None

        # 归一化条文号
        m = re.search(r'第?([一二三四五六七八九十百千零\d]+)条?', article or "")
        if not m:
            return None
        raw = m.group(1)
        target = int(raw) if raw.isdigit() else cn_num_to_int(raw)
        if target is None:
            return None

        # 在各版本中查找该条文
        found = []
        for ver in entry["versions"]:
            for no, body in ver["articles"].items():
                if cn_num_to_int(no[1:-1]) == target:  # no 形如 第四十六条
                    found.append((ver, no, body))
                    break
        if not found:
            return None

        old_ver, old_no, old_text = found[0]
        new_ver, new_no, new_text = found[-1]

        def _meta(ver: dict, no: str, text: str) -> dict:
            return {
                "article": no,
                "text": text,
                "publish_date": ver["publish_date"],
                "effective_date": ver["effective_date"],
                "status": ver["status"],
            }

        changed = re.sub(r'\s+', '', old_text) != re.sub(r'\s+', '', new_text)
        return {
            "law_name": entry["law_name"],
            "article": new_no,
            "changed": changed,
            "old": _meta(old_ver, old_no, old_text),
            "new": _meta(new_ver, new_no, new_text),
        }


_index: Optional[VersionIndex] = None


def get_index() -> VersionIndex:
    """获取全局版本索引（懒加载）"""
    global _index
    if _index is None:
        _index = VersionIndex()
    return _index
