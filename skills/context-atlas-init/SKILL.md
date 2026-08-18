---
name: context-atlas-init
description: Initialize a new self-contained Context Atlas project knowledge base. Use when the user explicitly invokes context-atlas-init for a project that does not yet contain its doc-* knowledge-base directory.
---

# Context Atlas Init

<!-- context-atlas-rules: [[rules/知识治理规则#RULE-AGENT-001|RULE-AGENT-001]] [[rules/知识治理规则#RULE-IMPACT-001|RULE-IMPACT-001]] [[rules/知识治理规则#RULE-IMPACT-002|RULE-IMPACT-002]] [[rules/知识治理规则#RULE-REL-002|RULE-REL-002]] -->

Initialize a new project knowledge base. Formal writes require explicit invocation of this Skill; natural-language requests may inspect and propose but must not initialize.

Read `../../references/执行状态机.md`, `../../references/初始化协议.md`, `../../references/知识采集与确认.md`, and `../../references/宿主执行与运行时探测.md` before writing.

Follow `inspect -> propose -> await_confirmation -> apply -> validate -> report`. Obtain the user's 显式确认 for the exact Proposal revision before applying it. Derive the default target as `doc-<项目目录名>`. If the 目标已存在, stop and direct the user to `$context-atlas-update`; never overwrite or reinitialize it.

Build an initialization Proposal that conforms to `../../assets/schemas/initialization-proposal.schema.json`. Compute `proposal_revision` from canonical JSON excluding that field, display the same revision with the human-readable Proposal, and require confirmation of that exact revision. Do not ask the user to write JSON or provide low-level file parameters.

Use `../../assets/templates/core/doc-project/` as the only template source. After approval, follow the runtime detection contract. When Python 3 is available, pass the Proposal through standard input to `../../assets/scripts/agent_kb_operation.py initialize --proposal - --confirmed-revision <revision>`. When Python 3 is unavailable but the Agent host passes the required capability preflight, use the isolated staging, scope checks, host validation, and atomic rename procedure in `../../references/宿主执行与运行时探测.md`; never write directly to the final target. Treat only a report conforming to `../../assets/schemas/initialization-report.schema.json` with `operation: initialized` and `validation.result: passed` as success.

Before apply, resolve and verify Python 3 exactly as defined by the runtime detection contract. A failing Windows Store `python` alias (including exit code 9009) does not prove Python is unavailable until all platform candidates have been checked. If no Python 3 interpreter works, select `agent_host` only when its capability preflight passes; otherwise stop with zero formal writes and report every checked capability and interpreter command.

Copy the bundled schemas and validation scripts into the target `.project-kb/` bundle, validate the result, and report exact paths and unresolved items.

Keep repository evidence, AI inference, user approval, stored knowledge, and validator results distinct. Never store secrets or unredacted personal data. Never create or maintain `AGENTS.md`, `CLAUDE.md`, or another Agent-specific adapter.
