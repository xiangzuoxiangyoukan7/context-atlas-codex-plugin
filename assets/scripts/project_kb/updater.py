"""Apply explicitly confirmed knowledge-base file updates atomically."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

from .agent_operation import OperationIssue, OperationReport, _relative_text
from .validator import ValidationConfig, validate


@dataclass(frozen=True)
class UpdateChange:
    """One repository-relative file replacement from a confirmed proposal."""

    path: str
    content_file: Path


def execute_update(
    knowledge_base_root: Path,
    proposal_revision: str,
    confirmed_revision: str,
    changes: tuple[UpdateChange, ...],
) -> OperationReport:
    """Apply confirmed replacements, validate, and roll back invalid results."""

    if not proposal_revision or proposal_revision != confirmed_revision:
        raise PermissionError("confirmed revision does not match current proposal")
    root = knowledge_base_root.resolve()
    if not root.is_dir() or not (root / "knowledge-base.yaml").is_file():
        raise ValueError("knowledge-base root must contain knowledge-base.yaml")
    if not changes:
        raise ValueError("update requires at least one file change")

    replacements: list[tuple[Path, bytes | None, bytes]] = []
    seen: set[Path] = set()
    for change in changes:
        target = (root / change.path).resolve()
        try:
            target.relative_to(root)
        except ValueError as error:
            raise ValueError(f"update path escapes knowledge-base root: {change.path}") from error
        if target in seen or target.name == "knowledge-base.yaml" or ".project-kb" in target.relative_to(root).parts:
            raise ValueError(f"unsupported or duplicate update path: {change.path}")
        if not change.content_file.is_file():
            raise ValueError(f"content file does not exist: {change.content_file}")
        seen.add(target)
        replacements.append((target, target.read_bytes() if target.exists() else None, change.content_file.read_bytes()))

    for target, _, content in replacements:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        temporary.replace(target)

    issues = validate(root, ValidationConfig(schema_root=root / ".project-kb" / "schemas"))
    if issues:
        for target, previous, _ in replacements:
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(previous)
    operation_issues = tuple(
        OperationIssue(issue.code, _relative_text(issue.path, root), issue.message)
        for issue in issues
    )
    changed_files = tuple(
        target.relative_to(root).as_posix() for target, _, _ in replacements
    ) if not issues else ()
    return OperationReport(
        operation="updated",
        target=root,
        changed_files=changed_files,
        validator_exit_code=0 if not issues else 1,
        issues=operation_issues,
    )
