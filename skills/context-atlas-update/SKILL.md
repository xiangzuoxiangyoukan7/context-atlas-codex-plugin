---
name: context-atlas-update
description: Update an existing self-contained Context Atlas project knowledge base. Use when the user explicitly invokes context-atlas-update to inspect changes, propose revisions, resolve conflicts, archive superseded knowledge, and validate an existing doc-* knowledge base.
---

# Context Atlas Update

<!-- context-atlas-rules: [[rules/知识治理规则#RULE-AGENT-001|RULE-AGENT-001]] [[rules/知识治理规则#RULE-IMPACT-001|RULE-IMPACT-001]] [[rules/知识治理规则#RULE-IMPACT-002|RULE-IMPACT-002]] [[rules/知识治理规则#RULE-REL-002|RULE-REL-002]] -->

Update an existing project knowledge base. Formal writes require explicit invocation of this Skill; natural-language requests may inspect and propose but must not update.

Read `../../references/执行状态机.md`, `../../references/知识采集与确认.md`, `../../references/更新冲突与归档.md`, and `../../references/验证与结果报告.md` before writing. Read the target knowledge base's root `README.md` and `knowledge-base.yaml` before proposing changes.

Follow `inspect -> propose -> await_confirmation -> apply -> validate -> report`. Present exact target paths and a revisioned Proposal, then obtain explicit confirmation of that revision. If no Context Atlas knowledge base exists, stop and direct the user to `$context-atlas-init`.

Use the structured executor under `../../assets/scripts/`; do not ask the user to provide low-level revision, file, or content parameters. Preserve approved history, resolve conflicts explicitly, archive or supersede knowledge according to the governance rules, validate the result, and report exact paths and unresolved items.

Keep repository evidence, AI inference, user approval, stored knowledge, and validator results distinct. Never store secrets or unredacted personal data. Never treat validator success as content approval.
