# SóClick Windows 11 Home — P0 readiness and local verification (2026-10-15)

## Exact scope
Base print generator: `702d2ff71d7145115f8486c42cccbd66e0662557`.
EvydFlow release candidate: `8dea9681a37d60c24ecabffac535f5e9b815b7fe` (PR #37, still draft).
This branch intentionally **does not** enable physical printing, boot workers, migrate customer databases or change print geometry.

## Changes
- Port discovery requires `GET /health` returning `{"ok":true}` **and** `GET /api/soclick/environment` returning a compatible typed environment, `enviar_blocked`, and `real_production_allowed`. A random process responding to /health is rejected.
- Only loopback HTTP URL hosts may be discovered via EVYDFLOW_PANEL_URL.
- Rendering modal now calls the action 'Gerar e preparar rascunho na SóClick', not 'Enviar', because handoff creates a local DRAFT only.
- Added contract tests for false positives, invalid ports, and valid/invalid environment shapes.

## Run locally (Antigravity 2.23.1 / Gemini 3.8 Flash, Windows 11 Home)
**Do not improvise commands or infer test results.** Verify branch and SHAs before executing.

1. Open the **print generator** checkout and inspect dirty work first:
   ```powershell
   git status --short --branch
   git fetch origin
   git branch --show-current
   git log -1 --oneline
   git diff --stat origin/feat/soclick-operator-handoff...origin/codex/soclick-operational-readiness-20261015
   ```
   If dirty, DO NOT reset, clean or overwrite; request reconciliation.
2. Checkout or make a fresh worktree on `origin/codex/soclick-operational-readiness-20261015` after verifying no active desktop instance holds that worktree. Avoid changing the current operational EvydFlow worktree.
3. Run Print Generator gates, recording actual console output:
   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/test_soclick_handoff.py -q
   .\.venv\Scripts\python.exe -m pytest -q
   .\.venv\Scripts\python.exe -m ruff check .
   npm --prefix apps/ui test -- --run
   npm --prefix apps/ui run build
   ```
   If the installed Python path or npm scripts differ, inspect README/pyproject.json/package.json and report exact differences. Never claim PASS from historical logs.
4. For the **EvydFlow** checkout, confirm current canonical PID, worktree, port 8095, SQLite paths, API and queue worker before any start/stop. The script `services/status-evydflow.ps1 -Port 8095` is observational; `GET /health` alone is *not* end-to-end readiness. Do **not** create another worker or enable real physical printing.
5. With operator approval, perform read-only tests against port 8095: `/health`, `/api/soclick/environment`, `/panel/soclick`. Confirm discovered process serves EvydFlow PR #37 route `POST /api/soclick/intake/print-generator` without issuing an actual POST until the user authorizes a synthetic/local draft.
6. In a hermetic staging sandbox (no real laboratory sends), test: foreign `/health` listener on 8090 rejected; legitimate 8095 accepted; fully offline shows recoverable error; successful handoff creates exactly ONE DRAFT; calling with identical rendered JPEG creates no duplicate; invalid filename/path/hash/format is rejected; open panel deep-link shows target job (not a new empty draft); browser opening failure does not invalidate durable job.
7. Do NOT use a previously submitted customer order (notably #5022), do not call `/enviar` or `/submit-production`, do not change `EVYDFLOW_ALLOW_REAL_PRODUCTION`, do not print or publish externally.
8. Capture precise: OS, active checkout, base/head SHAs, dependency versions, each command exit code, test counts, log paths, port owners, schema version, anonymous job ID, screenshots with customer details redacted. List observations as PASS / FAIL / NOT_RUN, never invented.

## Follow-on P0 (not implemented in this PR)
- Durable generator handoff outbox with immutable snapshot; current bridge rebuilds from mutable UI state.
- Unified credential-verified intake and true EvydFlow readiness API (API + worker identity and same SQLite DB).
- Safe controlled startup/recovery of the canonical API, avoiding duplicate workers.
- SSE snapshot plus cursor-based catch-up with access control; manager/operator exception UX and status freshness.
- Remote watchdog as authoritative periodic provider poller, not competing browser POST refresh loops.
- E2E Windows real-runtime evidence. Keep PR draft until passing all gates.

## Return to ChatGPT
Comment on this draft PR with each command/result, reason for any deviation, Windows and process health, no secrets or customer PII, and a precise follow-up patch plan. Never merge without explicit approval.
