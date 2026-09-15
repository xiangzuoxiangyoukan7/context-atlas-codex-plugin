---
id: IDX-功能基线-需求
type: knowledge_index
title: 需求
rel_classified_under:
  - "[[01-功能基线/README|IDX-功能基线]]"
---
# 需求

## 目录契约

本目录只保存需求，不保存功能设计、实现任务或实际证据。需求按下文规则命名，并以 `rel_classified_under` 指向本 README。使用 `children` 查看目录内容、`neighbors` 查询直接成员；普通 `graph` 到达本 README 后停止，只有显式分类成员查询才继续展开。

每项需求使用 `.project-kb/templates/knowledge/requirement.md` 创建独立文件，稳定 ID 与文件名主体相同，格式为 `REQ-<领域>-<YYYYMMDD>-<名称>`，文件名在末尾增加 `.md`。名称使用中文、英文、数字或连字符，不含空格和路径字符。需求描述为什么做、解决什么问题、范围和约束，不描述具体代码实现。

需求与功能是多对多关系。功能使用 `rel_satisfies` 指向需求；需求文件不手工维护反向功能列表。候选需求在责任人确认前保持 `proposed`。
