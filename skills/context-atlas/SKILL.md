---
name: context-atlas
description: Use when a user asks an AI Agent to initialize, inspect, explain, update, migrate, or validate a self-contained project knowledge base, including doc-* directories and optional Java or Python project knowledge.
---

<!-- context-atlas-rules: [[rules/知识治理规则#RULE-AGENT-001|RULE-AGENT-001]] [[rules/知识治理规则#RULE-IMPACT-001|RULE-IMPACT-001]] [[rules/知识治理规则#RULE-IMPACT-002|RULE-IMPACT-002]] [[rules/知识治理规则#RULE-REL-002|RULE-REL-002]] -->

# Context Atlas

## Overview

Operate a tool-neutral project knowledge base on the user's behalf. Treat repository evidence, AI inference, user approval, stored knowledge, and structural validation as distinct things.

## Choose the operation

正式写入只接受以下平台命令：

| Platform | Initialize | Update |
| --- | --- | --- |
| Codex | `$context-atlas init` | `$context-atlas update` |
| Claude Code | `/context-atlas:init` | `/context-atlas:update` |

将 `init` 和 `update` 视为固定操作符，而不是自然语言。没有固定操作符的自然语言只能用于检查、补充需求和
确认内容，不得触发正式写入。不得要求用户手填底层 revision、文件或 content 参数；Skill 在确认后调用内置
结构化执行器。未知操作符必须停止并列出上述有效命令，不得猜测或降级为写入操作。

| Request | Required references |
| --- | --- |
| Any operation that can write formal knowledge | Read [执行状态机](references/执行状态机.md) first. |
| Initialize a knowledge base | Read [初始化协议](references/初始化协议.md) and [知识采集与确认](references/知识采集与确认.md). |
| Inspect or explain one | Read its root README and `knowledge-base.yaml`, then [知识采集与确认](references/知识采集与确认.md). |
| Update, resolve conflict, or supersede knowledge | Read [知识采集与确认](references/知识采集与确认.md) and [更新冲突与归档](references/更新冲突与归档.md). |
| Diagnose or convert an older knowledge-base format | Read [兼容与迁移](references/兼容与迁移.md). |
| Identify a contributor or capture knowledge at a natural checkpoint | Read [身份与主动采集](references/身份与主动采集.md) and [知识采集与确认](references/知识采集与确认.md). |
| Validate or report results | Read [验证与结果报告](references/验证与结果报告.md). |
| Add relations, find consumers, or analyze change impact | Read [关系与影响分析](references/关系与影响分析.md). |
| Record data sources, database hierarchy, tables, field domains, or logical foreign keys | Read [数据库知识](references/数据库知识.md) and [关系与影响分析](references/关系与影响分析.md). |

For combined requests, read every referenced file before writing.

## Core workflow

Follow `inspect -> propose -> await_confirmation -> apply -> validate -> report` from [执行状态机](references/执行状态机.md). Present exact target paths and a revisioned Proposal; obtain explicit confirmation（显式确认）of that revision before formal writes. Return the report contract from [验证与结果报告](references/验证与结果报告.md).

## Non-negotiable boundaries

- Derive the default target as `doc-<项目目录名>`; accept a safe single-directory override only when the user states it.
- If the target already exists（目标已存在）, stop initialization and use the update workflow. Never overwrite or reinitialize it.
- Technology stacks are project facts. Record every confirmed stack in the shared technology document; never ask the user to select a stack-specific template.
- Never create or maintain `AGENTS.md`, `CLAUDE.md`, or another Agent-specific adapter. Explain this knowledge base so each Agent can create its own adapter if needed.
- Never store passwords, tokens, private keys, or unredacted personal data.
- Never treat validator success as content approval.
- Govern knowledge writes only. Never use the knowledge base to decide whether another plugin's development task may execute.
- At natural checkpoints, capture new project knowledge as a deduplicated `proposed` queue item; never silently promote it to formal knowledge.

## Assets

Use `assets/templates/core/doc-project/` as the only source. Discover and record every confirmed technology in the shared `技术栈与版本.md`; do not ask the user to select a language or stack-specific template. Read the generated rule copy under `assets/rules/` and standard operations under `assets/operations/` as needed. Copy `assets/scripts/` and `assets/schemas/` into the target `.project-kb/` validation bundle during initialization. Do not use undeclared assets.
