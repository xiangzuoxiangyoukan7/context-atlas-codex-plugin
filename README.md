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
$context-atlas init
```

更新已有知识库：

```text
$context-atlas update
```

没有 `init` 或 `update` 固定操作符的自然语言不能触发正式知识写入。

## 项目级卸载

回到安装插件时使用的目标项目目录，使用相同的项目级 `CODEX_HOME`，先卸载插件，再移除 Marketplace：

```powershell
$env:CODEX_HOME = (Join-Path $PWD ".codex")
codex plugin remove context-atlas@context-atlas
codex plugin marketplace remove context-atlas
```

不要直接删除整个 `.codex/` 目录，其中可能还有该项目的其他配置和插件。
