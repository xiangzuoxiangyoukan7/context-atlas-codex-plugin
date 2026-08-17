# 数据库知识

<!-- context-atlas-rules: [[rules/知识治理规则#RULE-DB-001|RULE-DB-001]] -->

按项目真实结构使用“数据源 → 数据库单元 → 可选数据命名空间 → 数据表”：

- [数据源](./数据源/TEMPLATE.md)：实例、集群连接、只读副本或数据仓库，不保存凭据值。
- [数据库单元](./数据库单元/TEMPLATE.md)：Database、Oracle PDB 或逻辑数据库。
- [数据命名空间](./数据命名空间/TEMPLATE.md)：Schema、用户模式或 Namespace；产品没有独立层级时不创建空壳。
- [数据表](./数据表/TEMPLATE.md)：项目实际读写或依赖的业务表，一表一文件。

| 数据库产品 | 数据源 | 数据库单元 | 可选命名空间 | 数据对象 |
| --- | --- | --- | --- | --- |
| Oracle | 实例或集群连接 | PDB；CDB 可作为拓扑说明 | Schema/用户 | 表、视图 |
| PostgreSQL | 服务器或集群连接 | Database | Schema | 表、视图、外部表 |
| KingbaseES | 服务器或集群连接 | 数据库 | 模式 | 表、视图、外部表 |
| MySQL | 实例或集群连接 | Database/Schema | 不重复创建 | 表、视图 |

功能、接口和任务使用 `rel_reads`、`rel_writes` 或 `rel_depends_on` 引用数据表；表不反向维护业务消费者。子表使用 `rel_logical_parent` 引用主表，并在正文精确链接主字段块锚点。已有物理外键如实填写约束名；没有物理外键仍保存逻辑映射，但知识库不会要求数据库新增约束。
