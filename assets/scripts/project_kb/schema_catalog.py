"""加载简化 JSON Schema 目录并验证知识元数据。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Mapping

from .model import Issue
from .json_schema import LocalSchemaRegistry, validate_instance
from .semantic_identity import semantic_id_matches


SELF_DESCRIBING_PROFILE = "self_describing/v1"
SELF_DESCRIBING_ENFORCEMENT = {
    "json_schema",
    "deterministic",
    "human_review",
    "advisory",
}


def _knowledge_root(path: Path) -> Path:
    """从知识文件向上定位清单；测试夹具没有清单时使用文件所在目录。"""

    current = path.resolve().parent
    for candidate in (current, *current.parents):
        if (candidate / "knowledge-base.yaml").is_file():
            return candidate
        if re.match(r"^\d+-", candidate.name):
            return candidate.parent
    return current


def _non_empty_strings(value: object) -> bool:
    """判断值是否为非空且成员均为非空字符串的列表。"""

    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


def _validate_self_describing_schema(kind: str, schema: dict[str, object], path: Path) -> None:
    """验证 opt-in 自描述 Schema 的最小语义完整性。"""

    extension = schema.get("x-context-atlas")
    if not isinstance(extension, dict) or extension.get("profile") != SELF_DESCRIBING_PROFILE:
        return

    failures: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        failures.append("$schema must select JSON Schema Draft 2020-12")
    expected_schema_id = f"https://context-atlas.dev/schemas/{path.name}"
    if schema.get("$id") != expected_schema_id:
        failures.append(f"$id must equal the stable local-registry URI: {expected_schema_id}")
    if schema.get("type") != "object":
        failures.append("type must be object")
    for field in ("title", "description"):
        if not isinstance(schema.get(field), str) or not str(schema[field]).strip():
            failures.append(f"{field} must be a non-empty string")
    if extension.get("knowledge_type") != kind:
        failures.append(f"knowledge_type must match catalog kind: {kind}")
    schema_version = extension.get("schema_version")
    if not isinstance(schema_version, str) or re.fullmatch(r"\d+\.\d+\.\d+", schema_version) is None:
        failures.append("x-context-atlas.schema_version must be semantic version")
    for field in ("purpose", "canonical_location"):
        if not isinstance(extension.get(field), str) or not str(extension[field]).strip():
            failures.append(f"x-context-atlas.{field} must be a non-empty string")
    for field in ("use_when", "do_not_use_when"):
        if not _non_empty_strings(extension.get(field)):
            failures.append(f"x-context-atlas.{field} must be a non-empty string list")
    for field in ("body_contract", "lifecycle", "compatibility"):
        if not isinstance(extension.get(field), dict):
            failures.append(f"x-context-atlas.{field} must be an object")
        elif not extension[field]:
            failures.append(f"x-context-atlas.{field} must not be empty")
    identity = extension.get("identity_contract")
    identity_fields = (
        "id_field", "filename_stem_equals_id", "semantic_name_field",
        "semantic_name_normalization", "semantic_identity", "date_capture_pattern", "maximum_length",
        "rename_policy", "collision_policy",
    )
    if not isinstance(identity, dict) or any(field not in identity for field in identity_fields):
        failures.append("x-context-atlas.identity_contract is incomplete")

    properties = schema.get("properties")
    if not isinstance(properties, dict) or not properties:
        failures.append("properties must be a non-empty object")
        properties = {}
    for field, definition in properties.items():
        if not isinstance(definition, dict):
            failures.append(f"properties.{field} must be an object")
            continue
        for attribute in ("title", "description"):
            if not isinstance(definition.get(attribute), str) or not str(definition[attribute]).strip():
                failures.append(f"properties.{field}.{attribute} must be a non-empty string")
        if not isinstance(definition.get("examples"), list) or not definition["examples"]:
            failures.append(f"properties.{field}.examples must be a non-empty list")

    required = schema.get("required")
    if not isinstance(required, list) or not required or len(required) != len(set(required)):
        failures.append("required must be a non-empty unique list")
    elif any(field not in properties for field in required):
        failures.append("every required field must have a documented property")

    legacy_enums = schema.get("enums", {})
    if isinstance(legacy_enums, dict):
        for field, allowed in legacy_enums.items():
            definition = properties.get(field)
            if not isinstance(definition, dict):
                failures.append(f"enum field {field} must have a documented property")
                continue
            branches = definition.get("oneOf")
            if not isinstance(branches, list):
                const = definition.get("const")
                branches = [{"const": const, "title": definition.get("title"), "description": definition.get("description"), "x-context-atlas": {"use_when": ["固定类型值"]}}]
            documented: list[object] = []
            for index, branch in enumerate(branches):
                if not isinstance(branch, dict) or "const" not in branch:
                    failures.append(f"properties.{field}.oneOf[{index}] must declare const")
                    continue
                documented.append(branch["const"])
                for attribute in ("title", "description"):
                    if not isinstance(branch.get(attribute), str) or not str(branch[attribute]).strip():
                        failures.append(f"properties.{field}.oneOf[{index}].{attribute} must be non-empty")
                branch_extension = branch.get("x-context-atlas")
                if not isinstance(branch_extension, dict) or not _non_empty_strings(branch_extension.get("use_when")):
                    failures.append(f"properties.{field}.oneOf[{index}] must explain x-context-atlas.use_when")
            if list(allowed) != documented:
                failures.append(f"legacy and documented enum values differ for {field}")

    rules = extension.get("rules")
    if not isinstance(rules, list):
        failures.append("x-context-atlas.rules must be a list")
    else:
        seen: set[str] = set()
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                failures.append(f"x-context-atlas.rules[{index}] must be an object")
                continue
            rule_id = rule.get("id")
            if not isinstance(rule_id, str) or not rule_id:
                failures.append(f"x-context-atlas.rules[{index}].id must be non-empty")
            elif rule_id in seen:
                failures.append(f"duplicate rule id: {rule_id}")
            else:
                seen.add(rule_id)
            if rule.get("enforcement") not in SELF_DESCRIBING_ENFORCEMENT:
                failures.append(f"invalid enforcement for rule {rule_id}")
            for field in ("description", "remediation"):
                if not isinstance(rule.get(field), str) or not str(rule[field]).strip():
                    failures.append(f"rule {rule_id} requires {field}")
            if rule.get("enforcement") == "deterministic" and not rule.get("diagnostic_code"):
                failures.append(f"deterministic rule {rule_id} requires diagnostic_code")

    rule_ids = {
        rule.get("id") for rule in rules or [] if isinstance(rule, dict) and isinstance(rule.get("id"), str)
    }
    invalid_examples = extension.get("invalid_examples")
    if not isinstance(invalid_examples, list) or not invalid_examples:
        failures.append("x-context-atlas.invalid_examples must be a non-empty list")
    else:
        for index, example in enumerate(invalid_examples):
            if not isinstance(example, dict) or not all(example.get(field) for field in ("case", "value", "expected_rule", "reason")):
                failures.append(f"invalid_examples[{index}] requires case, value, expected_rule and reason")
            elif example["expected_rule"] not in rule_ids:
                failures.append(f"invalid_examples[{index}] references unknown rule")

    lifecycle = extension.get("lifecycle")
    if isinstance(lifecycle, dict) and lifecycle:
        for field in ("field", "initial_states", "terminal_states", "transitions", "invalid_inferences"):
            if field not in lifecycle:
                failures.append(f"lifecycle requires {field}")
        state_field = lifecycle.get("field")
        allowed_states = legacy_enums.get(state_field, []) if isinstance(legacy_enums, dict) else []
        for group in ("initial_states", "terminal_states"):
            values = lifecycle.get(group, [])
            if not isinstance(values, list) or any(value not in allowed_states for value in values):
                failures.append(f"lifecycle.{group} must use values from enums.{state_field}")

    examples = schema.get("examples")
    if not isinstance(examples, list) or len(examples) < 2:
        failures.append("examples must contain minimal and recommended examples")

    if failures:
        raise ValueError(f"invalid self-describing schema {path}: " + "; ".join(failures))


@dataclass(frozen=True)
class SchemaCatalog:
    """保存按知识类型索引的受控 Schema 定义。"""

    root: Path
    schemas: dict[str, dict[str, object]]

    @classmethod
    def load(cls, root: Path) -> SchemaCatalog:
        """从目录文件加载所有已登记 Schema。"""

        resolved_root = root.resolve()
        catalog_path = resolved_root / "catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        if not isinstance(catalog, dict) or catalog.get("catalog_version") != 2:
            raise ValueError(f"schema catalog_version must be 2: {catalog_path}")
        entries = catalog.get("entries")
        if not isinstance(entries, dict):
            raise ValueError(f"schema catalog entries must be an object: {catalog_path}")

        schemas: dict[str, dict[str, object]] = {}
        for kind, entry in entries.items():
            if not isinstance(entry, dict) or not isinstance(entry.get("schema"), str):
                raise ValueError(f"invalid schema catalog entry: {kind}")
            for field in ("purpose",):
                if field in entry and (not isinstance(entry[field], str) or not entry[field].strip()):
                    raise ValueError(f"invalid {field} for schema catalog kind: {kind}")
            for field in ("use_when", "do_not_use_when"):
                value = entry.get(field)
                if value is not None and (
                    not isinstance(value, list)
                    or not value
                    or not all(isinstance(item, str) and item.strip() for item in value)
                ):
                    raise ValueError(f"invalid {field} for schema catalog kind: {kind}")
            if "status" in entry and entry["status"] != "active":
                raise ValueError(f"current schema catalog kind must be active: {kind}")
            relative = entry["schema"]
            candidate = (resolved_root / str(relative)).resolve()
            if resolved_root not in candidate.parents:
                raise ValueError(f"schema escapes root: {relative}")
            schema = json.loads(candidate.read_text(encoding="utf-8"))
            if not isinstance(schema, dict):
                raise ValueError(f"schema must be an object: {candidate}")
            _validate_self_describing_schema(str(kind), schema, candidate)
            if entry.get("schema_id") != schema.get("$id"):
                raise ValueError(f"schema_id mismatch for catalog kind: {kind}")
            schemas[str(kind)] = schema
        return cls(root=resolved_root, schemas=schemas)

    def validate(
        self,
        kind: str,
        metadata: Mapping[str, object],
        path: Path,
        *,
        execute_json_schema: bool = True,
    ) -> list[Issue]:
        """按必填、枚举、模式和列表约束验证元数据。"""

        schema = self.schemas.get(kind)
        if schema is None:
            return [Issue("KB_SCHEMA_KIND", path, f"unknown schema kind: {kind}")]

        issues: list[Issue] = []
        extension = schema.get("x-context-atlas")
        if execute_json_schema and isinstance(extension, dict) and extension.get("profile") == SELF_DESCRIBING_PROFILE:
            registry = LocalSchemaRegistry(self.root)
            for message in validate_instance(metadata, schema, registry, schema_path=self.root / f"{kind}.schema.json"):
                issues.append(Issue("KB_JSON_SCHEMA", path, message))
        identity = extension.get("identity_contract") if isinstance(extension, dict) else None
        if isinstance(identity, dict):
            identifier = metadata.get(str(identity.get("id_field", "id")))
            title = metadata.get(str(identity.get("semantic_name_field", "title")))
            if isinstance(identifier, str):
                maximum = identity.get("maximum_length")
                if isinstance(maximum, int) and len(identifier) > maximum:
                    issues.append(Issue("KB_SCHEMA_ID_LENGTH", path, f"identifier exceeds {maximum} characters"))
                if identity.get("filename_stem_equals_id") is True and path.stem != identifier:
                    issues.append(Issue("KB_SCHEMA_ID_FILENAME", path, "identifier must equal filename stem"))
                capture = identity.get("date_capture_pattern")
                match = re.search(str(capture), identifier) if capture else None
                if (
                    identity.get("semantic_identity") == "type_date_and_semantic_name"
                    and match is not None
                    and re.match(r"^[A-Z]+-\d{8}-", identifier) is not None
                    and "identity_created_at" not in metadata
                ):
                    issues.append(Issue(
                        "KB_SCHEMA_REQUIRED", path, "missing required field: identity_created_at"
                    ))
                if match is not None:
                    try:
                        datetime.strptime(match.group(1), "%Y%m%d")
                    except (ValueError, IndexError):
                        issues.append(Issue("KB_SCHEMA_ID_DATE", path, "identifier contains an invalid calendar date"))
                if (
                    identity.get("semantic_identity") == "type_date_and_semantic_name"
                    and "identity_created_at" in metadata
                ):
                    identity_created_at = metadata.get("identity_created_at")
                    expected_date = (
                        identity_created_at.replace("-", "")
                        if isinstance(identity_created_at, str) else None
                    )
                    captured_date = match.group(1) if match is not None else None
                    if expected_date is None or captured_date != expected_date:
                        issues.append(Issue(
                            "KB_SCHEMA_IDENTITY_DATE",
                            path,
                            "identifier date must equal identity_created_at",
                        ))
                if identity.get("semantic_identity") == "type_and_file_or_scope" and isinstance(title, str):
                    knowledge_type = metadata.get("type")
                    if isinstance(knowledge_type, str):
                        root = _knowledge_root(path)
                        last_updated = metadata.get("last_updated")
                        identity_created_at = metadata.get("identity_created_at")
                        if not semantic_id_matches(
                            identifier, knowledge_type, title, path, root,
                            identity_created_at=(
                                identity_created_at if isinstance(identity_created_at, str) else None
                            ),
                            last_updated=last_updated if isinstance(last_updated, str) else None,
                        ):
                            issues.append(Issue("KB_SCHEMA_ID_SEMANTIC", path, "identifier must express its type and file or README scope"))
        for field in schema.get("forbidden", []):
            if field in metadata:
                issues.append(
                    Issue("KB_SCHEMA_FORBIDDEN", path, f"forbidden field: {field}")
                )
        for field in schema.get("required", []):
            if field not in metadata:
                issues.append(
                    Issue("KB_SCHEMA_REQUIRED", path, f"missing required field: {field}")
                )
        for field, allowed in schema.get("enums", {}).items():
            if field in metadata and metadata[field] not in allowed:
                issues.append(
                    Issue("KB_SCHEMA_ENUM", path, f"invalid {field}: {metadata[field]!r}")
                )
        for field, allowed in schema.get("list_enums", {}).items():
            value = metadata.get(field)
            if field not in metadata:
                continue
            if not isinstance(value, list):
                issues.append(Issue("KB_SCHEMA_LIST", path, f"{field} must be a list"))
                continue
            invalid = [item for item in value if item not in allowed]
            if invalid:
                issues.append(
                    Issue(
                        "KB_SCHEMA_ENUM",
                        path,
                        f"invalid {field} values: {invalid!r}",
                    )
                )
        for field, pattern in schema.get("patterns", {}).items():
            value = metadata.get(field)
            if isinstance(value, str) and re.fullmatch(str(pattern), value) is None:
                issues.append(
                    Issue("KB_SCHEMA_PATTERN", path, f"invalid {field}: {value!r}")
                )
        for field in schema.get("non_empty_lists", []):
            value = metadata.get(field)
            if not isinstance(value, list) or not value:
                issues.append(
                    Issue("KB_SCHEMA_LIST", path, f"{field} must be a non-empty list")
                )
        for field in schema.get("unique_lists", []):
            value = metadata.get(field)
            if isinstance(value, list) and len(value) != len({json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value}):
                issues.append(
                    Issue("KB_SCHEMA_LIST", path, f"{field} must contain unique values")
                )
        return issues
