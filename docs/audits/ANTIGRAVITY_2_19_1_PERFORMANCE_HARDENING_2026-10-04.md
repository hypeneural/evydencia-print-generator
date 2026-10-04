# AntiGravity 2.19.1 / UI Performance Hardening Audit — 2026-10-04

## Official baseline
- Download page exposes Antigravity 2.0 v2.19.1.
- Official changelog lists v2.19.1 as Latest (2026-09-30): direct subagent messaging and fix for custom agents ignoring global/project Rules.
- Rules are cumulative and directory-scoped; AGENTS.md is always-on.
- Skills use progressive disclosure.
- Subagents have isolated context and can use isolated branch/worktree workspaces.
- Request Review is the recommended artifact policy.
- /plan is the preferred workflow for non-trivial multi-file work.
- Workflows retire 2026-11-01 in favor of Skills.

## Repository findings
1. Root AGENTS loaded more documents than necessary.
2. Status claimed 100% despite remote CI failure.
3. Renderer/output correctness was being treated as evidence for UI correctness.
4. Fabric hot-path rules were insufficiently explicit.
5. Double-click requirements conflicted between docs and current product intent.
6. No dedicated visual-validation Skill existed.
7. Current UI needs a production-vs-preview coordinate boundary.

## Changes
- reduced always-on context;
- added completion-evidence Rule;
- added ui-visual-validation Skill;
- hardened canvas/performance/UX agents and skills;
- added UI runtime architecture and quality gates;
- corrected Antigravity version documentation;
- changed STATUS/PLAN to evidence-based state.

## Official sources
https://www.antigravity.google/download
https://www.antigravity.google/docs/rules/
https://www.antigravity.google/docs/skills
https://www.antigravity.google/docs/subagents
https://www.antigravity.google/docs/slash-commands/
https://www.antigravity.google/docs/artifact-review
https://www.antigravity.google/docs/migration/workflows-to-skills
https://www.fabricjs.com/api/classes/canvas/#setDimensions
https://www.fabricjs.com/api/interfaces/canvasevents/#mousedblclick
https://www.fabricjs.com/docs/fabric-object-caching/
