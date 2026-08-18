"""生成并执行旧知识来源关系到当前格式的轻量等价转换。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import tempfile
from typing import Iterable

from .compatibility import CompatibilityPolicy
from .model import DocumentRecord


@dataclass(frozen=True)
class MigrationChange:
    """描述一个文件需要补充的统一来源关系及原内容摘要。"""

    path: Path
    links: tuple[str, ...]
    original_digest: str


@dataclass(frozen=True)
class MigrationUnresolved:
    """描述无法唯一定位、必须由用户确认的旧来源编号。"""

    path: Path
    source_id: str
    reason: str


@dataclass(frozen=True)
class MigrationProposal:
    """保存只读分析产生的不可变转换范围和确认修订号。"""

    proposal_revision: str
    source_version: int
    target_version: int
    changes: tuple[MigrationChange, ...]
    unresolved: tuple[MigrationUnresolved, ...]


@dataclass(frozen=True)
class MigrationReport:
    """保存已确认迁移实际修改的文件和最终格式版本。"""

    status: str
    changed_files: tuple[str, ...]
    format_version: int


def _digest(data: bytes) -> str:
    """返回文件内容摘要，用于拒绝提案生成后的并发变化。"""

    return hashlib.sha256(data).hexdigest()


def _source_paths(records: Iterable[DocumentRecord]) -> dict[str, list[Path]]:
    """按来源稳定编号建立可能包含重复项的文件索引。"""

    index: dict[str, list[Path]] = {}
    for record in records:
        if record.metadata.get("type") != "source":
            continue
        identifier = record.metadata.get("id")
        if isinstance(identifier, str):
            index.setdefault(identifier, []).append(record.path.resolve())
    return index


def _revision(
    source_version: int,
    target_version: int,
    changes: Iterable[MigrationChange],
    unresolved: Iterable[MigrationUnresolved],
) -> str:
    """根据完整提案内容生成稳定且不可猜测的短修订号。"""

    parts = [f"{source_version}->{target_version}"]
    parts.extend(
        f"change:{change.path}:{change.original_digest}:{','.join(change.links)}"
        for change in changes
    )
    parts.extend(
        f"unresolved:{item.path}:{item.source_id}:{item.reason}"
        for item in unresolved
    )
    return "migration-" + hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]


def build_migration_proposal(
    root: Path,
    records: Iterable[DocumentRecord],
    policy: CompatibilityPolicy,
) -> MigrationProposal:
    """只读分析旧裸来源编号并生成可确认的一对一转换提案。

    先诊断格式兼容性并建立来源编号索引，再逐份扫描旧记录，把可唯一解析的来源构造成
    正式关系；歧义项保留为 unresolved，最后根据文件摘要构造稳定提案修订号。
    """

    resolved_root = root.resolve()
    result = policy.diagnose(resolved_root)
    if not result.conversion_available:
        raise ValueError("current format has no applicable conversion")
    record_list = list(records)
    sources = _source_paths(record_list)
    changes: list[MigrationChange] = []
    unresolved: list[MigrationUnresolved] = []
    for record in record_list:
        raw_sources = record.metadata.get("sources")
        if not isinstance(raw_sources, list) or "rel_supported_by" in record.metadata:
            continue
        links: list[str] = []
        record_unresolved: list[MigrationUnresolved] = []
        for raw_source in raw_sources:
            source_id = str(raw_source)
            candidates = sources.get(source_id, [])
            if len(candidates) != 1:
                reason = "来源不存在" if not candidates else "来源编号不唯一"
                record_unresolved.append(
                    MigrationUnresolved(record.path.resolve(), source_id, reason)
                )
                continue
            relative = candidates[0].relative_to(resolved_root).with_suffix("").as_posix()
            links.append(f"[[{relative}|{source_id}]]")
        if record_unresolved:
            unresolved.extend(record_unresolved)
            continue
        if links:
            data = record.path.read_bytes()
            changes.append(
                MigrationChange(
                    record.path.resolve(), tuple(sorted(set(links))), _digest(data)
                )
            )
    ordered_changes = tuple(sorted(changes, key=lambda item: str(item.path)))
    ordered_unresolved = tuple(
        sorted(unresolved, key=lambda item: (str(item.path), item.source_id))
    )
    return MigrationProposal(
        proposal_revision=_revision(
            result.format_version,
            result.creates_format_version,
            ordered_changes,
            ordered_unresolved,
        ),
        source_version=result.format_version,
        target_version=result.creates_format_version,
        changes=ordered_changes,
        unresolved=ordered_unresolved,
    )


def _add_supported_by(content: str, links: tuple[str, ...]) -> str:
    """在保留原文的前提下向 Front Matter 末尾补充统一来源关系。"""

    lines = content.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ValueError("migration target lacks front matter")
    closing: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.rstrip("\r\n") == "---":
            closing = index
            break
    if closing is None:
        raise ValueError("migration target has incomplete front matter")
    addition = ["rel_supported_by:\n"] + [f'  - "{link}"\n' for link in links]
    return "".join(lines[:closing] + addition + lines[closing:])


def _set_format_version(content: str, target_version: int) -> str:
    """更新或补充内部格式版本，同时保持项目业务版本原值。"""

    lines = content.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("format_version:"):
            lines[index] = f"format_version: {target_version}\n"
            return "".join(lines)
    insertion = next(
        (index + 1 for index, line in enumerate(lines) if line.startswith("project_version:")),
        len(lines),
    )
    lines.insert(insertion, f"format_version: {target_version}\n")
    return "".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    """在目标目录写入临时文件并原子替换单个知识文件。"""

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".migrating",
        delete=False,
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def apply_migration(
    root: Path,
    proposal: MigrationProposal,
    confirmed_revision: str,
) -> MigrationReport:
    """在修订一致且无歧义时执行转换，并拒绝提案后的文件变化。

    先校验确认修订、未决项、目标边界和原文件摘要，再准备全部新内容；所有目标均未漂移后
    才逐项原子替换，并返回实际迁移文件及原格式版本。
    """

    if not confirmed_revision or confirmed_revision != proposal.proposal_revision:
        raise PermissionError("confirmed revision does not match migration proposal")
    if proposal.unresolved:
        raise ValueError("migration proposal contains unresolved source references")
    resolved_root = root.resolve()
    prepared: list[tuple[Path, str]] = []
    for change in proposal.changes:
        try:
            change.path.relative_to(resolved_root)
        except ValueError as error:
            raise ValueError("migration target escapes knowledge-base root") from error
        data = change.path.read_bytes()
        if _digest(data) != change.original_digest:
            raise ValueError(f"migration target changed after proposal: {change.path.name}")
        prepared.append(
            (change.path, _add_supported_by(data.decode("utf-8"), change.links))
        )
    manifest = resolved_root / "knowledge-base.yaml"
    manifest_content = _set_format_version(
        manifest.read_text(encoding="utf-8"), proposal.target_version
    )
    # 所有输入先完成安全检查和内存转换，再开始替换，避免可预见错误造成部分写入。
    for path, content in prepared:
        _atomic_write(path, content)
    _atomic_write(manifest, manifest_content)
    changed = tuple(
        [path.relative_to(resolved_root).as_posix() for path, _ in prepared]
        + ["knowledge-base.yaml"]
    )
    return MigrationReport("migrated", changed, proposal.target_version)
