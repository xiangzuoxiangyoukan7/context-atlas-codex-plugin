---
name: context-atlas-init
description: Initialize a new self-contained Context Atlas project knowledge base. Use when the user explicitly invokes context-atlas-init for a project that does not yet contain its doc-* knowledge-base directory.
---

# Context Atlas Init

<!-- context-atlas-rules: [[rules/知识治理规则#RULE-AGENT-001|RULE-AGENT-001]] [[rules/知识治理规则#RULE-IMPACT-001|RULE-IMPACT-001]] [[rules/知识治理规则#RULE-IMPACT-002|RULE-IMPACT-002]] [[rules/知识治理规则#RULE-REL-002|RULE-REL-002]] -->

Initialize a new project knowledge base. Formal writes require explicit invocation of this Skill; natural-language requests may inspect and propose but must not initialize.

Read `../../references/执行状态机.md`, `../../references/初始化协议.md`, and `../../references/知识采集与确认.md` before writing.

Follow `inspect -> propose -> await_confirmation -> apply -> validate -> report`. Obtain the user's 显式确认 for the exact Proposal revision before applying it. Derive the default target as `doc-<项目目录名>`. If the 目标已存在, stop and direct the user to `$context-atlas-update`; never overwrite or reinitialize it.

Use `../../assets/templates/core/doc-project/` as the only template source. After approval, invoke the structured executor under `../../assets/scripts/`; do not ask the user to provide low-level revision, file, or content parameters. Copy the bundled schemas and validation scripts into the target `.project-kb/` bundle, validate the result, and report exact paths and unresolved items.

Keep repository evidence, AI inference, user approval, stored knowledge, and validator results distinct. Never store secrets or unredacted personal data. Never create or maintain `AGENTS.md`, `CLAUDE.md`, or another Agent-specific adapter.
