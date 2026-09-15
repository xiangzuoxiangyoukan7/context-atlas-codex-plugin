"""读取插件兼容声明并对目标知识库执行只读格式诊断。"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import TypeAlias


FormatVersion: TypeAlias = int | str
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def parse_format_version(value: object) -> FormatVersion:
    """读取旧整数格式或与产品发布一致的 SemVer 格式。"""

    if isinstance(value, int) and value >= 1:
        return value
    if isinstance(value, str):
        stripped = value.strip().strip('"\'')
        if stripped.isdigit() and int(stripped) >= 1:
            return int(stripped)
        if SEMVER_PATTERN.fullmatch(stripped):
            return stripped
    raise ValueError("format_version must be a positive legacy integer or SemVer")


def format_generation(version: FormatVersion) -> int:
    """把 SemVer 当前格式映射到迁移规则代际，供遗留结构判断使用。"""

    if isinstance(version, int):
        return version
    major, minor, patch = (int(part) for part in version.split("."))
    if (major, minor, patch) >= (0, 20, 0):
        return 17
    return 16 if (major, minor, patch) >= (0, 19, 0) else 15


@dataclass(frozen=True)
class FormatConversion:
    """描述一个已实现的旧格式到新格式等价转换。"""

    source_version: FormatVersion
    target_version: FormatVersion
    identifier: str


@dataclass(frozen=True)
class CompatibilityResult:
    """描述知识库格式是否可读、可写以及是否存在转换器。"""

    format_version: FormatVersion
    status: str
    write_blocked: bool
    conversion_available: bool
    created_format_version: FormatVersion
    validation_issue_count: int = 0
    health_finding_count: int = 0
    blocking_health_finding_count: int = 0

    @property
    def creates_format_version(self) -> FormatVersion:
        """兼容旧调用方；新代码应读取 created_format_version。"""

        return self.created_format_version


@dataclass(frozen=True)
class CompatibilityPolicy:
    """保存兼容清单结构、可读格式、新建格式和单向转换声明。"""

    manifest_version: int
    supported_format_versions: frozenset[FormatVersion]
    created_format_version: FormatVersion
    conversions: tuple[FormatConversion, ...]

    @property
    def reads_format_versions(self) -> frozenset[FormatVersion]:
        """兼容旧调用方；新代码应读取 supported_format_versions。"""

        return self.supported_format_versions

    @property
    def creates_format_version(self) -> FormatVersion:
        """兼容旧调用方；新代码应读取 created_format_version。"""

        return self.created_format_version

    @classmethod
    def load(cls, path: Path) -> CompatibilityPolicy:
        """加载兼容声明并拒绝无法执行或相互矛盾的转换范围。"""

        payload = json.loads(path.resolve().read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("manifest_version") != 1:
            raise ValueError("compatibility manifest_version must be 1")
        for field in ("title", "description", "read_policy", "write_policy", "unknown_version_policy"):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                raise ValueError(f"compatibility {field} must be a non-empty string")
        raw_reads = payload.get("supported_format_versions")
        creates = payload.get("created_format_version")
        raw_conversions = payload.get("conversions")
        if not isinstance(raw_reads, list) or not raw_reads:
            raise ValueError("supported_format_versions must not be empty")
        reads = tuple(parse_format_version(item) for item in raw_reads)
        if len(reads) != len(set(reads)):
            raise ValueError("supported_format_versions must contain unique versions")
        creates = parse_format_version(creates)
        if creates not in reads:
            raise ValueError("created_format_version must be supported")
        if not isinstance(raw_conversions, list):
            raise ValueError("conversions must be a list")
        conversions: list[FormatConversion] = []
        for raw in raw_conversions:
            if not isinstance(raw, dict):
                raise ValueError("conversion must be an object")
            if not isinstance(raw.get("description"), str) or not raw["description"].strip():
                raise ValueError("conversion description must be non-empty")
            if raw.get("output_policy") != "convert_only_no_legacy_coexistence":
                raise ValueError("conversion must forbid legacy coexistence")
            source = parse_format_version(raw.get("from"))
            target = parse_format_version(raw.get("to"))
            identifier = raw.get("id")
            if (
                source not in reads
                or target != creates
                or source == target
                or not isinstance(identifier, str)
                or not identifier
            ):
                raise ValueError("invalid conversion declaration")
            conversions.append(FormatConversion(source, target, identifier))
        return cls(
            manifest_version=1,
            supported_format_versions=frozenset(reads),
            created_format_version=creates,
            conversions=tuple(conversions),
        )

    def diagnose(self, root: Path) -> CompatibilityResult:
        """只读解析目标清单，并返回兼容、可转换或不支持状态。"""

        manifest = root.resolve() / "knowledge-base.yaml"
        lines = manifest.read_text(encoding="utf-8").splitlines()
        format_version: FormatVersion = 1
        for line in lines:
            if line.startswith("format_version:"):
                raw_value = line.split(":", maxsplit=1)[1].strip()
                format_version = parse_format_version(raw_value)
                break
        conversion = next(
            (
                item
                for item in self.conversions
                if item.source_version == format_version
                and item.target_version == self.creates_format_version
            ),
            None,
        )
        if format_version not in self.reads_format_versions:
            return CompatibilityResult(
                format_version,
                "unsupported",
                True,
                conversion is not None,
                self.creates_format_version,
            )
        if format_version == self.creates_format_version:
            return CompatibilityResult(
                format_version,
                "compatible",
                False,
                False,
                self.creates_format_version,
            )
        return CompatibilityResult(
            format_version,
            "conversion_available" if conversion is not None else "compatible",
            False,
            conversion is not None,
            self.creates_format_version,
        )
