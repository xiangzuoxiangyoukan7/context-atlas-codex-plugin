"""集中生成并质检 Context Atlas 管理的 Obsidian 类型颜色组。"""

from __future__ import annotations

import json
from pathlib import Path


TYPE_COLORS: dict[str, int] = {
    "knowledge_index": 10027212,
    "overview_document": 14069084,
    "requirement": 14701138,
    "feature": 4360181,
    "architecture": 14048348,
    "module": 39423,
    "interface": 16753920,
    "database_table": 3447003,
    "data_source": 3447003,
    "data_asset": 16766720,
    "specification_change": 10040012,
    "specification_delta": 10040012,
    "acceptance": 6084269,
    "acceptance_evidence": 6084269,
    "knowledge_proposal": 10040012,
    "knowledge_item": 10027212,
    "managed_source": 11392604,
    "governance_document": 6073814,
    "governance_task": 6073814,
    "task": 6073814,
}

# README 分类节点统一使用蓝色系，并按目录深度由深到浅排列，便于在图谱中
# 快速识别根节点及其下级分类。Obsidian 按首个匹配颜色组着色，因此这些
# 查询必须位于通用的 type 查询之前。
README_LEVEL_COLORS: tuple[tuple[str, int], ...] = (
    (r"path:/^README\.md$/", 0x1E3A5F),
    (r"path:/^[^/]+\/README\.md$/", 0x2F5D8C),
    (r"path:/^(?:[^/]+\/){2}README\.md$/", 0x4A79A8),
    (r"path:/^(?:[^/]+\/){3}README\.md$/", 0x6D98BF),
    (r"path:/^(?:[^/]+\/){4,}README\.md$/", 0x93B7D5),
)


def type_query(document_type: str) -> str:
    """返回一个知识类型的稳定 Obsidian 属性查询。"""

    return f"[type:{document_type}]"


def managed_color_groups() -> list[dict[str, object]]:
    """先返回 README 层级色，再按稳定类型顺序返回其余受管颜色组。"""

    readme_groups = [
        {"query": query, "color": {"a": 1, "rgb": rgb}}
        for query, rgb in README_LEVEL_COLORS
    ]
    type_groups = [
        {"query": type_query(document_type), "color": {"a": 1, "rgb": rgb}}
        for document_type, rgb in TYPE_COLORS.items()
    ]
    return [*readme_groups, *type_groups]


def default_graph_settings() -> dict[str, object]:
    """返回不含个人工作区状态的最小图谱配置。"""

    return {
        "collapse-filter": False,
        "search": "",
        "showTags": True,
        "showAttachments": True,
        "hideUnresolved": True,
        "showOrphans": True,
        "collapse-color-groups": True,
        "colorGroups": managed_color_groups(),
        "collapse-display": True,
        "showArrow": True,
        "textFadeMultiplier": 0,
        "nodeSizeMultiplier": 1,
        "lineSizeMultiplier": 1,
        "collapse-forces": True,
        "centerStrength": 0.5,
        "repelStrength": 10,
        "linkStrength": 1,
        "linkDistance": 250,
        "scale": 1,
        "close": True,
    }


def merge_graph_settings(current: dict[str, object]) -> dict[str, object]:
    """更新受管类型颜色，保留用户颜色组和其他 Obsidian 设置。"""

    managed_queries = {
        *(type_query(document_type) for document_type in TYPE_COLORS),
        *(query for query, _ in README_LEVEL_COLORS),
    }
    raw_groups = current.get("colorGroups", [])
    custom_groups = [
        group for group in raw_groups
        if isinstance(group, dict) and group.get("query") not in managed_queries
    ] if isinstance(raw_groups, list) else []
    merged = dict(current)
    merged["colorGroups"] = [*managed_color_groups(), *custom_groups]
    return merged


def graph_text(current: dict[str, object] | None = None) -> str:
    """序列化新建或合并后的图谱配置。"""

    payload = default_graph_settings() if current is None else merge_graph_settings(current)
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def read_graph(path: Path) -> dict[str, object]:
    """读取并要求 graph.json 的根节点为对象。"""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Obsidian graph.json root must be an object")
    return payload
