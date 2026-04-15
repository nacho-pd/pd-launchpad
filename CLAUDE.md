# [PROJECT_NAME]

[PROJECT_DESCRIPTION]

---

## Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Next.js 15 + React 19 | App Router, TypeScript strict |
| Backend | Supabase | Auth, database, edge functions |
| Database | PostgreSQL (via Supabase) | RLS enabled on all tables |
| Testing | Vitest + Playwright | Unit + E2E |
| Hosting | Vercel | Preview on PR, production on main |
| State Coordination | Supabase `work_items` table | Shared with PD-OS |

See `docs/architecture.md` for detailed architecture decisions (ADRs).

---

## Agent System

This repo uses a 4-agent development system coordinated via Supabase.

| Agent | Model | Role | Primary Skills |
|-------|-------|------|---------------|
| **architect** | opus | Stack decisions, data modeling, ADRs | /choose-stack, /supabase-setup |
| **developer** | sonnet | TDD implementation (primary workhorse) | /plan-from-spec, /subagent-dev, /testing |
| **reviewer** | sonnet | Two-stage code review (read-only) | /code-reviewing |
| **qa** | sonnet | Test execution, acceptance validation | /testing, /deploy-preview |

### Agent Workflow

```
PM (PD-OS) → spec → architect (if new) → plan-from-spec → developer (TDD) → reviewer → qa → /ship
```

---

## Skills

| Skill | Purpose | Invoked By |
|-------|---------|-----------|
| `/plan-from-spec` | Spec → numbered tasks + dependency graph | developer |
| `/subagent-dev` | TDD per task (RED-GREEN-REFACTOR) | developer |
| `/testing` | Unit (Vitest) + E2E (Playwright) design | developer, qa |
| `/code-reviewing` | Two-stage review (compliance + quality) | reviewer |
| `/choose-stack` | Decision tree → ADR | architect |
| `/deploy-preview` | Vercel preview + smoke tests | qa |
| `/supabase-setup` | Schema, migrations, RLS, auth | architect |

---

## Commands

| Command | Purpose |
|---------|---------|
| `/review` | Trigger two-stage code review on current branch |
| `/qa` | Run full test suite (unit + e2e) |
| `/ship` | Production deploy with human gates |
| `/status` | Show work_items from Supabase for this repo |

---

## Rules (Always Active)

- **TDD First** — Tests before implementation. RED-GREEN-REFACTOR. Never delete a test to pass CI.
- **No Direct Deploy** — Agents deploy to preview/staging only. Production = `/ship` only.
- **Evidence Over Claims** — "Done" = tests pass + review approved + preview verified.
- **Spec Compliance** — Every line of code traces to a spec requirement. No scope creep.
- **Respect Agent Role Boundaries** — When a plan assigns phases or tasks to specific agents (architect, developer, qa, reviewer), only execute work assigned to your role. After completing your phase, STOP and hand off to the next agent. If running as the main session and a plan has role-assigned phases, ask which agent role to assume before starting. The architect does NOT write application code. The developer does NOT make architecture decisions. The reviewer does NOT modify code.

---

## Spec Workflow

1. PM in PD-OS creates a `work_item` with `target_repo = [PROJECT_NAME]`.
2. n8n syncs the spec to `docs/specs/{work_item_id}.md`.
3. Architect evaluates stack needs (first spec only or architecture change).
4. Developer runs `/plan-from-spec` → creates `docs/plan.md`.
5. Developer implements tasks via `/subagent-dev` (TDD).
6. Reviewer runs `/review` (two-stage).
7. QA runs `/qa` (full test suite).
8. Developer updates Supabase: `status=needs_review`, `pr_url`, `preview_url`.
9. Human reviews in Slack.
10. If approved → `/ship` for production deploy.

---

## Conventions

- **TypeScript**: Strict mode. No `any` types. Prefer interfaces over types for objects.
- **Testing**: TDD always. Vitest for unit, Playwright for e2e. `data-testid` for selectors.
- **Branches**: `feat/description`, `fix/description`, `chore/description`.
- **Commits**: Imperative mood, reference task number. E.g., `feat: add user auth (task-003)`.
- **Path aliases**: `@/*` maps to `src/*`.
- **Supabase**: All queries via `@supabase/supabase-js`. RLS on all tables.
