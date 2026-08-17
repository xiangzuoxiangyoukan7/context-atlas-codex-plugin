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
