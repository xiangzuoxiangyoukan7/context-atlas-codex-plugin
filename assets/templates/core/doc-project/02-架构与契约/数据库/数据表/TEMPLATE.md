---
id: TABLE-EXAMPLE
type: database_table
title: 示例业务表
status: proposed
version: 1.0.0
physical_name: example_table
owner: missing
sensitivity: missing
sources: [SRC-000]
ddl_sources: [missing]
rel_belongs_to:
  - "[[02-架构与契约/数据库/数据命名空间/NS-EXAMPLE|NS-EXAMPLE]]"
last_updated: {{INITIALIZED_AT}}
---
# TABLE-EXAMPLE 示例业务表

## 字段定义

| 字段编号 | 字段名 | 数据类型 | 可空 | 默认值 | 中文含义 | 值域类型 | 允许值或最小值 | 最大值或格式 | 允许其他值 | 约束执行位置 | 来源 | 锚点 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FIELD-EXAMPLE-001 | id | bigint | 否 | — | 示例主键 | 任意 | — | 任意整数 | 否 | 数据库约束 | [[00-项目总览/知识来源#SRC-000 待登记来源|SRC-000]] | ^FIELD-EXAMPLE-001 |

## 主子表关系

没有主表关系时保留空表；存在业务主子表引用时同时增加 `rel_logical_parent`。

| 关系编号 | 子字段编号 | 主表与字段 | 物理约束 | 约束名称 |
| --- | --- | --- | --- | --- |
