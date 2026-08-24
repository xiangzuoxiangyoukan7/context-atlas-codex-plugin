# Context Atlas for Codex

这是由 [`context-atlas`](https://github.com/xiangzuoxiangyoukan7/context-atlas) 源码仓库自动生成的
Codex 发布仓库。请勿直接修改本仓库中的生成文件。

## 项目级安装

在需要使用 Context Atlas 的目标项目中执行：

```powershell
$env:CODEX_HOME = (Join-Path $PWD ".codex")
codex plugin marketplace add https://github.com/xiangzuoxiangyoukan7/context-atlas-codex-plugin.git
codex plugin add context-atlas@context-atlas
codex
```

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

向已有知识库新增业务知识：

```text
$context-atlas-add
```

修订、同步或替代已有业务知识：

```text
$context-atlas-revise
```

通过替代、归档或受控删除退役业务知识：

```text
$context-atlas-retire
```

升级已有知识库格式和结构：

```text
$context-atlas-upgrade
```

没有明确调用对应 Skill 的自然语言不能触发正式知识写入。

## 升级插件

回到安装插件的目标项目，保持相同的项目级 `CODEX_HOME`。`marketplace add` 不会刷新已经登记的 Marketplace；必须执行：

```powershell
$env:CODEX_HOME = (Join-Path $PWD ".codex")
codex plugin marketplace upgrade context-atlas
codex plugin remove context-atlas@context-atlas
codex plugin add context-atlas@context-atlas
codex plugin list
```

以 `codex plugin list` 显示的实际版本为准。升级后新建 Codex 会话，使新版 Skill 生效。

## 项目级卸载

回到安装插件时使用的目标项目目录，使用相同的项目级 `CODEX_HOME`，先卸载插件，再移除 Marketplace：

```powershell
$env:CODEX_HOME = (Join-Path $PWD ".codex")
codex plugin remove context-atlas@context-atlas
codex plugin marketplace remove context-atlas
```

不要直接删除整个 `.codex/` 目录，其中可能还有该项目的其他配置和插件。
