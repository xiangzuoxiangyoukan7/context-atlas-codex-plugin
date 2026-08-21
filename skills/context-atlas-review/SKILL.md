---
name: context-atlas-review
description: Review Context Atlas requirements, features, designs, changes, or delivery readiness for clarity, completeness, testability, conflicts, and traceability. This Skill is read-only and never approves or writes formal knowledge.
---

# Context Atlas Review

Review project specifications without changing formal knowledge. Read `../../references/规格审查与SDD适配.md`, `../../references/关系与影响分析.md`, and `../../references/验证与结果报告.md`. Read the target knowledge-base `README.md`, `knowledge-base.yaml`, collaboration rules, and only directly relevant knowledge.

Select one or more modes: `requirement`, `feature`, `design`, `change`, `implementation_readiness`, or `acceptance_readiness`. Separate confirmed facts, repository observations, external artifacts, unresolved questions, and AI inferences. Do not fill gaps with plausible behavior.

When deterministic assets are available, run the checker with `--level spec` or `--level readiness`. For OpenSpec or Spec Kit sources, use the bundled read-only SDD inspector and retain source paths and versions. External approval, task completion, archive, branch, or test state never becomes Context Atlas approval.

Return reviewed IDs and paths, mode, `ready` or `blocked`, deterministic issues, human-review findings, blocking questions, traceability gaps, and the next smallest action. Never create, edit, archive, approve, or migrate knowledge. To preserve findings, route formal maintenance through `$context-atlas-add`, `$context-atlas-revise`, or `$context-atlas-retire` and its exact Proposal confirmation gate.
