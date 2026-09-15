"""生成并校验带类型、身份建立日期和语义名称的知识身份。"""

from __future__ import annotations

from pathlib import Path
import re


SEMANTIC_ID_PREFIXES: dict[str, str] = {
    "acceptance": "AC", "acceptance_evidence": "EVID", "architecture": "ARCH",
    "data_asset": "DATA", "data_source": "DS", "database_table": "TABLE",
    "feature": "FEAT", "governance_document": "GOV", "governance_task": "TASK",
    "interface": "IFACE", "knowledge_index": "IDX", "knowledge_item": "ITEM",
    "knowledge_proposal": "PROP", "managed_source": "SOURCE", "module": "MOD",
    "overview_document": "OVERVIEW", "requirement": "REQ",
    "specification_change": "CHG", "specification_delta": "DELTA", "task": "TASK",
}
DATED_FILE_IDENTITY_TYPES = frozenset({
    "acceptance", "acceptance_evidence", "data_asset", "database_table",
    "feature", "governance_task", "interface", "knowledge_item",
    "knowledge_proposal", "module", "requirement", "specification_change",
    "specification_delta", "task",
})

SEMANTIC_NAME_PATTERN = re.compile(r"[0-9A-Za-z\u4e00-\u9fff]+")
SEMANTIC_ID_PATTERN = re.compile(
    r"^[0-9A-Za-z\u4e00-\u9fff]+(?:-[0-9A-Za-z\u4e00-\u9fff]+)*$"
)
IDENTITY_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
    identity_created_at: str | None = None,
    last_updated: str | None = None,
) -> str:
    """根据类型、身份建立日期和最小语义名称构造稳定 ID。

    ``last_updated`` 仅供旧格式迁移兼容；新写入必须显式提供
    ``identity_created_at``，且后续内容修订不得改变该日期。
    """

    if kind == "data_source" and path.name.lower() == "readme.md":
        directory_scope = normalize_semantic_name(path.parent.name)
        if directory_scope:
            return directory_scope
    prefix = SEMANTIC_ID_PREFIXES.get(kind)
    if prefix is None:
        raise ValueError(f"缺少知识类型的语义 ID 前缀：{kind}")
    if path.name.lower() == "readme.md":
        scope = semantic_scope(path, root, title)
        if not scope:
            raise ValueError("README 标题不能生成目录身份")
        return f"{prefix}-{scope}"
    if kind not in DATED_FILE_IDENTITY_TYPES:
        if kind == "architecture" and path.parent.resolve() == (root / "02-技术基线").resolve():
            return "ARCH-技术基线-系统架构"
        scope = semantic_scope(path, root, title)
        if not scope:
            raise ValueError("标题不能生成语义 ID")
        return f"{prefix}-{scope}"
    captured = re.match(rf"^{re.escape(prefix)}-(\d{{8}})-", current_id or "")
    date_source = identity_created_at or (
        f"{captured.group(1)[:4]}-{captured.group(1)[4:6]}-{captured.group(1)[6:]}"
        if captured else None
    ) or last_updated
    if not isinstance(date_source, str) or IDENTITY_DATE_PATTERN.fullmatch(date_source) is None:
        raise ValueError("知识缺少有效的 identity_created_at")
    date_text = date_source.replace("-", "")
    name = normalize_semantic_name(title)
    if not name:
        raise ValueError("知识标题不能生成语义名称")
    return f"{prefix}-{date_text}-{name}"


def semantic_id_matches(
    identifier: str,
    kind: str,
    title: str,
    path: Path,
    root: Path,
    *,
    identity_created_at: str | None = None,
    last_updated: str | None = None,
) -> bool:
    """判断 ID 是否精确表达当前文件或 README 目录作用域。"""

    if SEMANTIC_ID_PATTERN.fullmatch(identifier) is None:
        return False
    try:
        if path.name.lower() != "readme.md" and path.stem != identifier:
            return False
        # 归档只改变生命周期位置，不改写知识原始领域身份；文件名仍必须等于 ID。
        if any(part.startswith("90-") for part in path.parts):
            return path.name.lower() != "readme.md"
        if path.name.lower() == "readme.md":
            return identifier == build_semantic_id(
                kind, title, path, root, current_id=identifier,
                identity_created_at=identity_created_at, last_updated=last_updated,
            )
        if kind not in DATED_FILE_IDENTITY_TYPES:
            return identifier == build_semantic_id(
                kind, title, path, root, current_id=identifier,
                identity_created_at=identity_created_at, last_updated=last_updated,
            )
        prefix = SEMANTIC_ID_PREFIXES.get(kind)
        if prefix is None or identity_created_at is None:
            return False
        expected_start = f"{prefix}-{identity_created_at.replace('-', '')}-"
        return identifier.startswith(expected_start) and path.stem == identifier
    except ValueError:
        return False
