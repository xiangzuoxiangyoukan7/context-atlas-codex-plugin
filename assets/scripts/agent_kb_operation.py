"""为 Agent 提供非交互式知识库结构化操作命令。"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.project_kb.agent_operation import execute_initialize
from scripts.project_kb.capture import CaptureCandidate, capture_candidate
from scripts.project_kb.compatibility import CompatibilityPolicy
from scripts.project_kb.discovery import discover_records
from scripts.project_kb.identity import discover_identity_match
from scripts.project_kb.migration import apply_migration, build_migration_proposal
from scripts.project_kb.updater import UpdateChange, execute_update


def _default_assets_root() -> Path:
    """根据脚本位于源码仓库还是发布资产中推导默认资源根目录。"""

    scripts_parent = Path(__file__).resolve().parents[1]
    if (scripts_parent / "templates" / "core" / "doc-project").is_dir():
        return scripts_parent
    return scripts_parent / "skills" / "context-atlas" / "assets"


def _default_compatibility() -> Path:
    """返回源码仓库或知识库内置工具中的默认兼容声明。"""

    return _default_assets_root() / "compatibility.json"


def _parser() -> argparse.ArgumentParser:
    """创建只接受已确认结构化参数的命令行解析器。"""

    parser = argparse.ArgumentParser(description="执行已确认的 Context Atlas 结构化操作")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    initialize = subparsers.add_parser("initialize", aliases=["init"])
    initialize.add_argument("project_root", type=Path)
    initialize.add_argument("--project-name")
    initialize.add_argument("--proposal-revision", required=True)
    initialize.add_argument("--confirmed-revision", required=True)
    initialize.add_argument("--assets-root", type=Path, default=_default_assets_root())

    update = subparsers.add_parser("update")
    update.add_argument("knowledge_base_root", type=Path)
    update.add_argument("--proposal-revision", required=True)
    update.add_argument("--confirmed-revision", required=True)
    update.add_argument("--file", action="append", required=True)
    update.add_argument("--content-file", action="append", required=True)

    diagnose = subparsers.add_parser("diagnose-format")
    diagnose.add_argument("knowledge_base_root", type=Path)
    diagnose.add_argument(
        "--compatibility", type=Path, default=_default_compatibility()
    )

    capture = subparsers.add_parser("capture")
    capture.add_argument("knowledge_base_root", type=Path)
    capture.add_argument("--checkpoint", required=True)
    capture.add_argument("--summary", required=True)
    capture.add_argument("--target-id", action="append", required=True)
    capture.add_argument("--source-type", required=True)
    capture.add_argument("--source-reference", required=True)
    capture.add_argument("--difference", action="append", default=[])
    capture.add_argument("--impact-id", action="append", default=[])
    capture.add_argument("--unknown", action="append", default=[])
    capture.add_argument("--conflict", action="append", default=[])
    capture.add_argument("--proposed-by", required=True)
    capture.add_argument("--operated-by", required=True)
    capture.add_argument("--project-version", required=True)
    capture.add_argument("--captured-at", required=True)

    identify = subparsers.add_parser("identify-contributor")
    identify.add_argument("repository_root", type=Path)
    identify.add_argument("knowledge_base_root", type=Path)

    for operation in ("migrate-propose", "migrate-apply"):
        migration = subparsers.add_parser(operation)
        migration.add_argument("knowledge_base_root", type=Path)
        migration.add_argument(
            "--compatibility", type=Path, default=_default_compatibility()
        )
        if operation == "migrate-apply":
            migration.add_argument("--proposal-revision", required=True)
            migration.add_argument("--confirmed-revision", required=True)
    return parser


def _migration_proposal(root: Path, compatibility: Path) -> object:
    """发现知识记录并建立当前文件状态对应的只读迁移提案。"""

    records, issues = discover_records(
        root.resolve(), frozenset({".obsidian", "Excalidraw", "90-历史归档"})
    )
    if issues:
        messages = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(f"knowledge discovery failed: {messages}")
    policy = CompatibilityPolicy.load(compatibility)
    return build_migration_proposal(root, records, policy)


def _execute(args: argparse.Namespace) -> tuple[object, int]:
    """按已解析操作执行并返回报告及进程退出码。"""

    if args.operation in {"initialize", "init"}:
        report = execute_initialize(
            project_root=args.project_root,
            project_name=args.project_name,
            proposal_revision=args.proposal_revision,
            confirmed_revision=args.confirmed_revision,
            assets_root=args.assets_root,
        )
        return report, report.validator_exit_code
    if args.operation == "update":
        if len(args.file) != len(args.content_file):
            raise ValueError("--file and --content-file must be supplied the same number of times")
        report = execute_update(
            knowledge_base_root=args.knowledge_base_root,
            proposal_revision=args.proposal_revision,
            confirmed_revision=args.confirmed_revision,
            changes=tuple(
                UpdateChange(path, Path(content_file))
                for path, content_file in zip(args.file, args.content_file)
            ),
        )
        return report, report.validator_exit_code
    if args.operation == "diagnose-format":
        result = CompatibilityPolicy.load(args.compatibility).diagnose(
            args.knowledge_base_root
        )
        return result, 2 if result.write_blocked else 0
    if args.operation == "capture":
        candidate = CaptureCandidate(
            checkpoint=args.checkpoint,
            summary=args.summary,
            target_ids=tuple(args.target_id),
            source_type=args.source_type,
            source_reference=args.source_reference,
            differences=tuple(args.difference),
            impact_ids=tuple(args.impact_id),
            unknowns=tuple(args.unknown),
            conflicts=tuple(args.conflict),
            proposed_by=args.proposed_by,
            operated_by=args.operated_by,
            project_version=args.project_version,
        )
        return (
            capture_candidate(
                args.knowledge_base_root, candidate, captured_at=args.captured_at
            ),
            0,
        )
    if args.operation == "identify-contributor":
        people_path = (
            args.knowledge_base_root.resolve() / "00-项目总览" / "协作人员.md"
        )
        return discover_identity_match(args.repository_root, people_path), 0
    proposal = _migration_proposal(
        args.knowledge_base_root, args.compatibility
    )
    if args.operation == "migrate-propose":
        # 未解析关系属于需要人工处理的有效分析结果，而不是程序崩溃。
        return proposal, 3 if proposal.unresolved else 0
    if args.proposal_revision != proposal.proposal_revision:
        raise PermissionError("proposal revision no longer matches current files")
    return (
        apply_migration(
            args.knowledge_base_root, proposal, args.confirmed_revision
        ),
        0,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """执行结构化知识操作并输出不含会话全文的 JSON 报告。"""

    parser = _parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        report, exit_code = _execute(args)
    except (OSError, ValueError, PermissionError) as error:
        print(
            json.dumps(
                {"ok": False, "error_type": type(error).__name__, "message": str(error)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    payload = asdict(report)
    payload["ok"] = exit_code == 0
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
