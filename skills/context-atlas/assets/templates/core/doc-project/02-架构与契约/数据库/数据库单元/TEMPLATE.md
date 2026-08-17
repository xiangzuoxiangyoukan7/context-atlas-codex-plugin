---
id: DB-EXAMPLE
type: database_unit
title: 示例数据库单元
status: proposed
version: 1.0.0
unit_kind: database
physical_name: example_db
owner: missing
sources: [SRC-000]
rel_belongs_to:
  - "[[02-架构与契约/数据库/数据源/DS-EXAMPLE|DS-EXAMPLE]]"
last_updated: {{INITIALIZED_AT}}
---
# DB-EXAMPLE 示例数据库单元

记录数据库中的真实名称、用途、迁移方式和权限边界。Oracle 可使用 `pdb`；PostgreSQL、KingbaseES、MySQL 通常使用 `database`。
