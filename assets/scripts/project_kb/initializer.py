"""以暂存目录和原子替换方式安全初始化知识库。"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re
import shutil
import tempfile
from .validator import ValidationConfig, validate


MARKER_PATTERN = re.compile(r"{{[A-Z][A-Z0-9_]*}}")


def _safe_project_name(name: str) -> str:
    """验证项目名只能形成一个安全目录段。"""

    normalized = name.strip()
    if not normalized or normalized in {".", ".."} or "/" in normalized or "\\" in normalized:
        raise ValueError("project name must be one safe directory segment")
    return normalized


def _replace_markers(root: Path, values: dict[str, str]) -> None:
    """替换模板变量并拒绝任何未解析标记。"""

    unresolved: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker, value in values.items():
            content = content.replace(marker, value)
        unresolved.extend(f"{path}: {marker}" for marker in MARKER_PATTERN.findall(content))
        path.write_text(content, encoding="utf-8", newline="\n")
    if unresolved:
        raise ValueError("unresolved template markers: " + ", ".join(unresolved))


def initialize_from_assets(
    project_root: Path,
    project_name: str | None = None,
    assets_root: Path = Path("assets"),
    initialized_at: str | None = None,
) -> Path:
    """从 Skill 资产创建自包含且已验证的新知识库。"""

    project_root = project_root.resolve()
    if not project_root.is_dir():
        raise ValueError("project root must be an existing directory")
    name = _safe_project_name(project_name or project_root.name)
    target = project_root / f"doc-{name}"
    if target.exists():
        raise FileExistsError(f"knowledge-base target already exists: {target}")

    assets_root = assets_root.resolve()
    template = assets_root / "templates" / "core" / "doc-project"
    schema_root = assets_root / "schemas"
    if not template.is_dir() or not schema_root.is_dir():
        raise ValueError("Skill assets are incomplete")

    # 先在同一文件系统完成复制和验证，最后原子改名，避免暴露半成品目标。
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.initializing-", dir=project_root))
    try:
        shutil.copytree(template, staging, dirs_exist_ok=True)
        _replace_markers(
            staging,
            {
                "{{PROJECT_ID}}": name,
                "{{PROJECT_NAME}}": name,
                "{{KNOWLEDGE_BASE_NAME}}": target.name,
                "{{INITIALIZED_AT}}": initialized_at or date.today().isoformat(),
            },
        )
        shutil.copytree(assets_root / "scripts", staging / ".project-kb" / "scripts")
        shutil.copytree(schema_root, staging / ".project-kb" / "schemas")
        shutil.copy2(
            assets_root / "compatibility.json",
            staging / ".project-kb" / "compatibility.json",
        )
        issues = validate(staging, ValidationConfig(schema_root=staging / ".project-kb" / "schemas"))
        if issues:
            codes = ", ".join(issue.code for issue in issues)
            raise ValueError(f"materialized knowledge base is invalid: {codes}")
        if target.exists():
            raise FileExistsError(f"knowledge-base target appeared during initialization: {target}")
        staging.replace(target)
        return target
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
