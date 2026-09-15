"""离线执行 Context Atlas 使用的 JSON Schema Draft 2020-12 关键字。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import re
from urllib.parse import urlparse


class SchemaValidationError(ValueError):
    """表示实例不满足 Schema，并携带稳定的 JSON 路径。"""


class LocalSchemaRegistry:
    """按稳定 `$id` 和文件名加载本地 Schema，禁止网络解析。"""

    def __init__(self, root: Path) -> None:
        """扫描本地目录并建立逻辑 ID 与文件路径索引。"""
        self.root = root.resolve()
        self.by_id: dict[str, dict[str, object]] = {}
        self.by_path: dict[Path, dict[str, object]] = {}
        for path in self.root.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                self.by_path[path.resolve()] = payload
                schema_id = payload.get("$id")
                if isinstance(schema_id, str):
                    self.by_id[schema_id] = payload

    def load(self, name_or_id: str) -> tuple[dict[str, object], Path]:
        """从本地注册表解析文件名或稳定逻辑 ID。"""

        if name_or_id in self.by_id:
            schema = self.by_id[name_or_id]
            return schema, next(path for path, value in self.by_path.items() if value is schema)
        parsed = urlparse(name_or_id)
        if parsed.scheme and parsed.scheme not in {""}:
            raise SchemaValidationError(f"remote schema resolution is forbidden: {name_or_id}")
        path = (self.root / name_or_id).resolve()
        if self.root not in path.parents or path not in self.by_path:
            raise SchemaValidationError(f"schema is not registered locally: {name_or_id}")
        return self.by_path[path], path


def _pointer(root: object, fragment: str) -> object:
    """解析当前 Schema 内的 JSON Pointer。"""
    value = root
    for part in fragment.removeprefix("#/").split("/") if fragment != "#" else []:
        token = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or token not in value:
            raise SchemaValidationError(f"unresolved local pointer: {fragment}")
        value = value[token]
    return value


def _type_matches(value: object, expected: str) -> bool:
    """判断 Python 值是否符合 JSON Schema 基础类型。"""
    return {"object": isinstance(value, dict), "array": isinstance(value, list),
            "string": isinstance(value, str), "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": isinstance(value, bool), "null": value is None}.get(expected, False)


def validate_instance(instance: object, schema: dict[str, object], registry: LocalSchemaRegistry,
                      *, schema_path: Path, instance_path: str = "$") -> list[str]:
    """验证一个实例并返回全部确定性错误；解析仅限本地注册表。"""

    errors: list[str] = []

    def visit(value: object, node: object, current_schema: dict[str, object], current_file: Path, path: str) -> None:
        """递归执行当前 Schema 节点并收集全部错误。"""
        if not isinstance(node, dict):
            return
        ref = node.get("$ref")
        if isinstance(ref, str):
            if ref.startswith("#"):
                visit(value, _pointer(current_schema, ref), current_schema, current_file, path)
            else:
                target, target_file = registry.load(ref)
                visit(value, target, target, target_file, path)
            return
        expected = node.get("type")
        if isinstance(expected, str) and not _type_matches(value, expected):
            errors.append(f"{path}: expected {expected}"); return
        if isinstance(expected, list) and not any(isinstance(item, str) and _type_matches(value, item) for item in expected):
            errors.append(f"{path}: expected one of {expected}"); return
        if "const" in node and value != node["const"]: errors.append(f"{path}: must equal {node['const']!r}")
        if isinstance(node.get("enum"), list) and value not in node["enum"]: errors.append(f"{path}: value is outside enum")
        if isinstance(value, str):
            if isinstance(node.get("minLength"), int) and len(value) < node["minLength"]: errors.append(f"{path}: string is too short")
            if isinstance(node.get("pattern"), str) and re.search(node["pattern"], value) is None: errors.append(f"{path}: pattern mismatch")
            fmt=node.get("format")
            try:
                if fmt == "date": datetime.strptime(value, "%Y-%m-%d")
                elif fmt == "date-time": datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif fmt == "uri" and not urlparse(value).scheme: raise ValueError
            except ValueError: errors.append(f"{path}: invalid {fmt}")
        if isinstance(value, (int,float)) and not isinstance(value,bool):
            if isinstance(node.get("minimum"),(int,float)) and value < node["minimum"]: errors.append(f"{path}: below minimum")
            if isinstance(node.get("maximum"),(int,float)) and value > node["maximum"]: errors.append(f"{path}: above maximum")
        if isinstance(value, list):
            if isinstance(node.get("minItems"),int) and len(value)<node["minItems"]: errors.append(f"{path}: too few items")
            if isinstance(node.get("maxItems"),int) and len(value)>node["maxItems"]: errors.append(f"{path}: too many items")
            if node.get("uniqueItems") is True and len({json.dumps(x,ensure_ascii=False,sort_keys=True) for x in value}) != len(value): errors.append(f"{path}: items must be unique")
            for i,item in enumerate(value): visit(item,node.get("items",{}),current_schema,current_file,f"{path}[{i}]")
        if isinstance(value, dict):
            required=node.get("required",[])
            if isinstance(required,list):
                for field in required:
                    if field not in value: errors.append(f"{path}: missing required property {field}")
            properties=node.get("properties",{})
            if isinstance(properties,dict):
                for field,child in properties.items():
                    if field in value: visit(value[field],child,current_schema,current_file,f"{path}.{field}")
                if node.get("additionalProperties") is False:
                    for field in value.keys()-properties.keys(): errors.append(f"{path}: additional property {field}")
        branches=node.get("allOf")
        if isinstance(branches,list):
            for child in branches: visit(value,child,current_schema,current_file,path)
        branches=node.get("oneOf")
        if isinstance(branches,list):
            matches=0
            for child in branches:
                before=len(errors); visit(value,child,current_schema,current_file,path)
                if len(errors)==before: matches+=1
                else: del errors[before:]
            if matches != 1: errors.append(f"{path}: must match exactly one oneOf branch")
        condition=node.get("if")
        if isinstance(condition,dict):
            probe=[]; original=errors; errors_local=probe
            # 使用独立验证避免条件失败污染正式错误。
            condition_errors=validate_instance(value,condition,registry,schema_path=current_file,instance_path=path)
            branch=node.get("then" if not condition_errors else "else")
            if isinstance(branch,dict): visit(value,branch,current_schema,current_file,path)

    visit(instance,schema,schema,schema_path.resolve(),instance_path)
    return errors
