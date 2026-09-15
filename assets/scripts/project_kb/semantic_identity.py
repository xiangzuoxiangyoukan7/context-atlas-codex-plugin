"""生成并校验见名知意的知识身份。

本模块用于初始化、维护、迁移和结构校验。它把知识类型映射为稳定类型前缀，
把标题规范化为身份中的语义名称，并为没有独立文件名的 README 分类节点加入
目录作用域。调用方仍须负责冲突检测，不能用追加序号掩盖命名冲突。
"""

from __future__ import annotations

from pathlib import Path
import re


SEMANTIC_ID_PREFIXES: dict[str, str] = {
    "acceptance": "AC", "acceptance_evidence": "EVID", "architecture": "ARCH",
    "data_asset": "DATA", "data_source": "DS", "database_table": "TABLE",
    "feature": "FEATURE", "governance_document": "GOV", "governance_task": "TASK",
    "interface": "INTERFACE", "knowledge_index": "IDX", "knowledge_item": "ITEM",
    "knowledge_proposal": "PROP", "managed_source": "SOURCE", "module": "MOD",
    "overview_document": "OVERVIEW", "requirement": "REQ",
    "specification_change": "CHG", "specification_delta": "DELTA", "task": "TASK",
}

SEMANTIC_NAME_PATTERN = re.compile(r"[0-9A-Za-z\u4e00-\u9fff]+")
SEMANTIC_ID_PATTERN = re.compile(
    r"^[0-9A-Za-z\u4e00-\u9fff]+(?:-[0-9A-Za-z\u4e00-\u9fff]+)*$"
)


def normalize_semantic_name(value: str) -> str:
    """把阅读名称转换为可安全用于文件和链接的语义名称。"""

    return "-".join(SEMANTIC_NAME_PATTERN.findall(value.strip()))


def _hierarchy_parts(path: Path, root: Path) -> list[str]:
    """提取去掉排序数字的知识库相对目录层级。"""

    relative_parent = path.resolve().parent.relative_to(root.resolve())
    parts: list[str] = []
    for raw in relative_parent.parts:
        name = re.sub(r"^\d+-", "", raw)
        normalized = normalize_semantic_name(name)
        if normalized:
            parts.append(normalized)
    return parts


def semantic_scope(path: Path, root: Path, title: str) -> str:
    """返回 README 的目录作用域，普通文件优先使用已有语义文件名。"""

    title_name = normalize_semantic_name(title)
    parts = _hierarchy_parts(path, root)
    compact_title = title_name.replace("-", "")
    last_compact = parts[-1].replace("-", "") if parts else ""
    if path.name.lower() != "readme.md":
        if title_name and (not parts or not last_compact.endswith(compact_title)):
            parts.append(title_name)
        return "-".join(parts)
    if not parts:
        return title_name or "知识库"
    if title_name and not last_compact.endswith(compact_title):
        parts.append(title_name)
    return "-".join(parts)


def build_semantic_id(
    kind: str,
    title: str,
    path: Path,
    root: Path,
    *,
    current_id: str | None = None,
    last_updated: str | None = None,
) -> str:
    """根据知识类型、标题和文件作用域构造语义 ID。"""

    if kind == "data_source" and path.name.lower() == "readme.md":
        directory_scope = normalize_semantic_name(path.parent.name)
        if directory_scope:
            return directory_scope
    if kind == "architecture" and path.parent.resolve() == (root / "02-技术基线").resolve():
        return "ARCH-技术基线-系统架构"
    prefix = SEMANTIC_ID_PREFIXES.get(kind)
    if prefix is None:
        raise ValueError(f"缺少知识类型的语义 ID 前缀：{kind}")
    if kind == "requirement":
        match = re.match(r"^REQ-([A-Z0-9]+)-(?:(\d{8})-|\d{3}$)", current_id or "")
        domain = match.group(1) if match else "GENERAL"
        captured_date = match.group(2) if match else None
        date_text = captured_date or (last_updated or "").replace("-", "")
        if re.fullmatch(r"\d{8}", date_text) is None:
            raise ValueError("需求缺少可用于身份的有效日期")
        name = normalize_semantic_name(title)
        if not name:
            raise ValueError("需求标题不能生成语义名称")
        return f"REQ-{domain}-{date_text}-{name}"
    scope = semantic_scope(path, root, title)
    if not scope:
        raise ValueError("标题不能生成语义 ID")
    return f"{prefix}-{scope}"


def semantic_id_matches(identifier: str, kind: str, title: str, path: Path, root: Path, *, last_updated: str | None = None) -> bool:
    """判断 ID 是否精确表达当前文件或 README 目录作用域。"""

    if SEMANTIC_ID_PATTERN.fullmatch(identifier) is None:
        return False
    try:
        if path.name.lower() != "readme.md" and path.stem != identifier:
            return False
        # 归档只改变生命周期位置，不改写知识原始领域身份；文件名仍必须等于 ID。
        if any(part.startswith("90-") for part in path.parts):
            return path.name.lower() != "readme.md"
        return identifier == build_semantic_id(
            kind, title, path, root, current_id=identifier, last_updated=last_updated
        )
    except ValueError:
        return False
