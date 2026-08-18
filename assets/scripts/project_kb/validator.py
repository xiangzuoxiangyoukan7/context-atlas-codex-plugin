"""编排元数据、链接、追溯和安全验证器。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .discovery import discover_records
from .database import validate_database_fields, validate_database_relations
from .links import validate_links
from .identity import validate_people
from .model import Issue
from .relation_catalog import RelationCatalog
from .relations import RelationIndex
from .schema_catalog import SchemaCatalog
from .security import validate_security
from .traceability import validate_traceability


@dataclass(frozen=True)
class ValidationConfig:
    """保存 Schema 位置和知识发现排除目录。"""

    schema_root: Path
    relation_catalog_path: Path | None = None
    excluded_directories: frozenset[str] = frozenset(
        {".obsidian", "Excalidraw", "90-历史归档"}
    )


def validate(root: Path, config: ValidationConfig) -> list[Issue]:
    """执行全部确定性检查并返回稳定排序的问题。"""

    resolved_root = root.resolve()
    if not resolved_root.exists():
        return [Issue("KB_ROOT_MISSING", resolved_root, "knowledge-base root does not exist")]

    records, issues = discover_records(resolved_root, config.excluded_directories)
    catalog = SchemaCatalog.load(config.schema_root)
    for record in records:
        kind = record.metadata.get("type")
        if isinstance(kind, str) and kind in catalog.schemas:
            issues.extend(catalog.validate(kind, record.metadata, record.path))
    relation_catalog_path = (
        config.relation_catalog_path
        if config.relation_catalog_path is not None
        else config.schema_root / "relation-catalog.json"
    )
    try:
        relation_catalog = RelationCatalog.load(relation_catalog_path)
    except (OSError, ValueError) as error:
        issues.append(
            Issue(
                "KB_REL_CATALOG",
                relation_catalog_path,
                f"关系目录不可用：{error}",
            )
        )
    else:
        relation_index, relation_issues = RelationIndex.build(
            resolved_root, records, relation_catalog
        )
        issues.extend(relation_issues)
        issues.extend(validate_database_relations(resolved_root, records, relation_index))
    issues.extend(validate_database_fields(records))
    issues.extend(validate_people(resolved_root))
    issues.extend(validate_links(resolved_root, config.excluded_directories))
    issues.extend(validate_traceability(resolved_root, records))
    issues.extend(validate_security(records))
    return sorted(issues, key=lambda issue: (str(issue.path), issue.code, issue.message))
