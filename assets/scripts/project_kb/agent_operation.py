"""实现带提案修订门禁的确定性 Agent 操作。"""

from __future__ import annotations

# context-atlas-rules: [[rules/知识治理规则#RULE-AGENT-001|RULE-AGENT-001]]

from dataclasses import dataclass
from pathlib import Path

from .initializer import initialize_from_assets
from .validator import ValidationConfig, validate


@dataclass(frozen=True)
class OperationIssue:
    """保存操作后验证发现的单个结构问题。"""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class OperationReport:
    """保存 Agent 可安全返回的固定字段操作报告。"""

    operation: str
    target: Path
    changed_files: tuple[str, ...]
    validator_exit_code: int
    issues: tuple[OperationIssue, ...]


def _relative_text(path: Path, root: Path) -> str:
    """将问题路径限制为知识库内相对路径或安全文件名。"""

    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def execute_initialize(
    project_root: Path,
    project_name: str | None,
    proposal_revision: str,
    confirmed_revision: str,
    assets_root: Path,
) -> OperationReport:
    """在确认修订一致后初始化知识库并执行二次验证。"""

    # 修订门禁必须早于路径解析和目录创建，才能保证拒绝时真正零写入。
    if not proposal_revision or proposal_revision != confirmed_revision:
        raise PermissionError("confirmed revision does not match current proposal")

    target = initialize_from_assets(
        project_root=project_root,
        project_name=project_name,
        assets_root=assets_root,
    )
    schema_root = target / ".project-kb" / "schemas"
    validation_issues = validate(target, ValidationConfig(schema_root=schema_root))
    issues = tuple(
        OperationIssue(
            code=issue.code,
            path=_relative_text(issue.path, target),
            message=issue.message,
        )
        for issue in validation_issues
    )
    changed_files = tuple(
        path.relative_to(target).as_posix()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    )
    return OperationReport(
        operation="initialized",
        target=target,
        changed_files=changed_files,
        validator_exit_code=0 if not issues else 1,
        issues=issues,
    )
