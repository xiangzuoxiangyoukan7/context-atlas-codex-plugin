# Context Atlas for Codex

这是由 [`context-atlas`](https://github.com/xiangzuoxiangyoukan7/context-atlas) 源码仓库自动生成的
Codex 发布仓库。请勿直接修改本仓库中的生成文件。

## 用户级安装、项目级启用

保持默认用户级 `CODEX_HOME`，安装 Marketplace 和插件。不要把 `CODEX_HOME` 指向项目的 `.codex/`：

```powershell
codex plugin marketplace add https://github.com/xiangzuoxiangyoukan7/context-atlas-codex-plugin.git
codex plugin add context-atlas@context-atlas
cd D:\你的目标项目
codex
```

若只希望在指定项目使用，在用户级 `~/.codex/config.toml` 中把 `[plugins."context-atlas@context-atlas"]` 的 `enabled` 设为 `false`，再在受信任目标项目的 `.codex/config.toml` 中将同一项设为 `true`。插件实体和运行缓存全局共享，项目知识仍保存在各自的 `doc-<项目名>/` 中。

新建会话后初始化知识库：

```text
$context-atlas-work
$context-atlas-init
```

逐层发现知识目录、查询节点邻接关系或按需分析受限关系图：

```text
$context-atlas-navigate
$context-atlas-review
```

只读摄取一个可定位来源并生成知识维护路由：

```text
$context-atlas-ingest
```

向已有知识库新增项目知识：

```text
$context-atlas-add
```

修订现有项目知识或建立明确后继项：

```text
$context-atlas-revise
```

撤销无后继项的当前权威，或归档已替代知识：

```text
$context-atlas-retire
```

升级已有知识库格式和结构：

```text
$context-atlas-upgrade
```

没有明确调用对应 Skill 的自然语言不能触发正式知识写入。

## 升级插件

升级用户级共享安装。`marketplace add` 不会刷新已经登记的 Marketplace；必须执行：

```powershell
codex plugin marketplace upgrade context-atlas
codex plugin remove context-atlas@context-atlas
codex plugin add context-atlas@context-atlas
codex plugin list
```

以 `codex plugin list` 显示的实际版本为准。重新安装后确认用户级默认禁用、目标项目启用，并新建 Codex 会话，使新版 Skill 生效。

## 卸载

卸载用户级插件会影响该用户的所有项目：

```powershell
codex plugin remove context-atlas@context-atlas
codex plugin marketplace remove context-atlas
```

只需停止某个项目使用时，删除项目 `.codex/config.toml` 中的启用项或将其设为 `false`。不要直接删除整个 `.codex/` 目录，其中可能还有该项目的其他配置。
