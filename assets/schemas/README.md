# 核心 Schema

`catalog.json` 是检查器读取的唯一 Schema 目录。各 Schema 使用 JSON，确保 Python 标准库即可解析；知识库 Markdown 使用受控 YAML Front Matter，只支持字符串和一维字符串列表。

- [目录](./catalog.json)
- [项目清单](./project-manifest.schema.json)
- [通用知识项](./knowledge-item.schema.json)
- [数据资产](./data-asset.schema.json)
- [功能](./feature.schema.json)
- [产品任务](./task.schema.json)
- [治理任务](./governance-task.schema.json)
- [验收](./acceptance.schema.json)
- [知识来源](./source.schema.json)

技术栈记录只增加项目事实，不能改变核心状态、权威来源、确认规则或验收结果。

除 `required`、`enums`、`patterns`、`non_empty_lists`、`unique_lists` 外，Schema 还支持 `list_enums`，用于约束字符串列表中的每个成员必须来自预定义枚举。

