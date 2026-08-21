---
name: context-atlas-ingest
description: Read exactly one located source and map it to add, revise, retire, conflict, or ignore candidates for an existing Context Atlas knowledge base. Use only when the user explicitly invokes context-atlas-ingest. This Skill is read-only and never writes formal knowledge or invokes maintenance Skills.
---

# Context Atlas Ingest

Analyze one source and return a read-only candidate map. Read `../../references/单来源摄取与路由.md`, `../../references/知识采集与确认.md`, `../../references/关系与影响分析.md`, and `../../references/验证与结果报告.md`. Read the target knowledge-base `README.md`, `knowledge-base.yaml`, collaboration rules, and only knowledge directly relevant to the source.

Require exactly one primary source with a type, precise locator, and observation time. A repository file, one versioned existing or external document, one user statement, or one located command output counts as one source. Reject multiple independent sources and never use `ai_inference` as the primary source.

If no knowledge base exists, return only a route to `$context-atlas-init`. If the format is unsupported, return only a route to `$context-atlas-upgrade`. Block unreadable, unlocatable, secret-bearing, or unredacted-personal-data sources without echoing sensitive values.

Discover relevant current knowledge progressively with `children -> neighbors -> bounded graph`; do not recursively read the whole knowledge base. Check stable identity, semantic duplication, current authority, and competing sources before classifying candidates.

Return a complete report conforming to `../../assets/schemas/ingest-report.schema.json` for every outcome. This includes all early-return and `blocked` outcomes such as multiple sources, missing knowledge base, unsupported format, unreadable input, or sensitive data; use empty arrays and explicit blocker values instead of omitting required fields. Candidate actions are only `add`, `revise`, `retire`, `conflict`, or `ignore`. Preserve facts, explicit inferences, unknowns, competing sources, candidate relations, impacts, routing rationale, and one aggregate `route_plan`.

The final response must be the complete JSON report itself, with every required top-level field present. Do not replace it with a prose summary, even when the analysis found a conflict or the next action needs user judgment.

Always report `writes_performed: false` and `confirmation_state: not_applicable`. Do not create a file, write the pending queue, produce a confirmed revision, call an executor, or invoke `$context-atlas-add`, `$context-atlas-revise`, or `$context-atlas-retire`. Recommend the smallest explicit maintenance-Skill combination as `next_action`; the later maintenance flow must reinspect current state and build one atomic Proposal.
