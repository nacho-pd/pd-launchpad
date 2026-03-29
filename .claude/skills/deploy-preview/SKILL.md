---
name: deploy-preview
description: "Vercel preview deployment with smoke test verification"
---

# Deploy Preview

Deploys a Vercel preview environment for a PR branch and runs automated smoke tests
to verify the deployment is functional. Reports results back to the PR as a comment.
No human review required for preview deploys — the preview URL is the review artifact.

---

## 1. Input

| Input | Source | Required |
|---|---|---|
| Branch name | Current git branch (`git branch --show-current`) | Yes |
| PR number | GitHub PR number (from `gh pr view --json number`) | Yes |
| Build output | `npm run build` stdout/stderr | Yes |
| Environment variables | `.env.example` + Vercel project settings | Yes |
| Smoke test config | `tests/smoke.config.ts` (if exists) | No |
| Previous deploy report | PR comments from prior deploys | No |

### Environment Variable Safety Check

Before deploying, verify:
- No secrets are hardcoded in source code (scan for patterns: `sk_`, `pk_`, `secret`, API keys)
- `.env` files are in `.gitignore`
- `.env.example` exists and contains only placeholder values
- All required env vars are configured in Vercel project settings (not just locally)

---

## 2. Thinking Frameworks

### 2.1 Pre-Deploy Checklist

Run through this checklist before triggering any deployment:

```
PRE-DEPLOY CHECKLIST
====================

Build Health:
  [ ] `npm run build` exits with code 0
  [ ] No TypeScript errors (`npx tsc --noEmit` passes)
  [ ] No ESLint errors (`npm run lint` passes)
  [ ] No "console.error" or "console.warn" in build output
  [ ] Build output size is reasonable (no >5MB single chunks)

Test Health:
  [ ] Unit tests pass (`npm test`)
  [ ] No skipped tests that were previously passing
  [ ] Test coverage has not decreased (if tracked)

Security:
  [ ] No secrets in source code (grep for common patterns)
  [ ] .env files are gitignored
  [ ] No new dependencies with known vulnerabilities (`npm audit --production`)
  [ ] No hardcoded URLs pointing to production (should use env vars)

Configuration:
  [ ] All env vars from .env.example are set in Vercel project
  [ ] Environment-specific configs (API URLs, feature flags) are correct for preview
  [ ] Database connection points to preview/staging, NOT production
```

### 2.2 Smoke Test Protocol

Smoke tests verify the deployment is alive and functional. They are NOT comprehensive
tests — they check critical paths only.

**Tier 1 — Availability (must pass):**
- Homepage returns HTTP 200
- No server-side errors (500) on key routes
- Static assets load (CSS, JS bundles)
- Favicon and meta tags are present

**Tier 2 — Functionality (should pass):**
- Key routes render correctly (check for expected HTML elements)
- API routes respond (authenticated and unauthenticated)
- Database connectivity works (a simple query returns data)
- Auth flow works (login page renders, redirect configured correctly)

**Tier 3 — Integration (nice to have):**
- External service connections work (payment provider, email, etc.)
- Real-time features connect (WebSocket handshake succeeds)
- File upload/download works (if applicable)
- Third-party widgets load (analytics, chat, etc.)

### 2.3 Deployment Verification

After deployment completes, verify:

```
DEPLOYMENT VERIFICATION
=======================

Infrastructure:
  [ ] Preview URL responds (HTTP 200 on /)
  [ ] Correct branch is deployed (check x-vercel-deployment-url header or deployment metadata)
  [ ] SSL certificate is valid (HTTPS works)
  [ ] Response time is < 3 seconds for homepage

Environment:
  [ ] Environment variables are injected correctly
  [ ] Preview environment is isolated (not sharing state with production)
  [ ] API endpoints point to correct backend (preview/staging)

Content:
  [ ] No "Error" or "Something went wrong" visible on page
  [ ] No broken images (all images load)
  [ ] No layout shifts or broken styling
  [ ] JavaScript bundle loads without errors
```

### 2.4 Rollback Awareness

Preview deployments have minimal rollback risk:
- Preview URLs are ephemeral and auto-expire when the PR is closed
- Each push to the branch creates a new preview (old previews remain accessible)
- Preview environments share no state with production
- If a preview is broken, the fix is simply pushing a new commit

No manual rollback procedure is needed for preview deployments.

### 2.5 Failure Classification

When issues are detected, classify them:

| Category | Severity | Action |
|---|---|---|
| Build failure | CRITICAL | Cannot deploy. Fix build errors first. |
| Missing env var | CRITICAL | Deploy will fail or app will crash. Configure in Vercel. |
| Smoke test Tier 1 fail | CRITICAL | Deployment is broken. Investigate immediately. |
| Smoke test Tier 2 fail | WARNING | Functionality issue. Fix before requesting review. |
| Smoke test Tier 3 fail | INFO | Non-critical. Note in deploy report. |
| Slow response (>5s) | WARNING | Performance issue. Investigate. |
| Console JS errors | WARNING | Frontend issue. Fix before requesting review. |
| npm audit warnings | INFO | Note in report. Fix if high/critical severity. |

---

## 3. Expected Output

### Deploy Report Template

```markdown
# Deploy Preview Report

**PR:** #<number> — <title>
**Branch:** <branch-name>
**Preview URL:** <https://project-branch-name.vercel.app>
**Deploy Time:** <duration in seconds>
**Date:** <ISO date>

---

## Pre-Deploy Checklist

| Check | Status | Notes |
|---|---|---|
| Build passes | PASS | Built in 42s, 3 pages |
| TypeScript clean | PASS | No errors |
| Lint clean | PASS | — |
| Tests pass | PASS | 47/47 tests passed |
| No secrets in code | PASS | — |
| Env vars configured | PASS | 8/8 vars set in Vercel |
| No console.error in build | PASS | — |
| npm audit clean | WARN | 1 moderate vulnerability in dev dependency |

---

## Smoke Test Results

### Tier 1: Availability

| Test | Status | Response Time |
|---|---|---|
| Homepage (/) | PASS | 320ms |
| Static assets load | PASS | — |
| Favicon present | PASS | — |
| No 500 errors on key routes | PASS | — |

### Tier 2: Functionality

| Test | Status | Notes |
|---|---|---|
| /dashboard renders | PASS | Shows empty state correctly |
| /api/health responds | PASS | `{"status": "ok"}` |
| Database connected | PASS | Query returned in 45ms |
| Auth page renders | PASS | Login form visible |

### Tier 3: Integration

| Test | Status | Notes |
|---|---|---|
| Supabase Realtime | PASS | WebSocket connected |
| Email service | SKIP | Not configured for preview |

---

## Browser Console

- No JavaScript errors detected
- 1 warning: "React DevTools is not installed" (expected in preview)

---

## Summary

- **Pre-deploy:** 7/8 PASS, 1 WARN (non-critical)
- **Smoke tests:** 10/11 PASS, 1 SKIP
- **Console:** Clean
- **Status:** READY FOR REVIEW

Preview URL: <https://project-branch-name.vercel.app>
```

---

## 4. Review / Rubric

### Deploy Report Quality Checklist

| Criterion | Pass/Fail |
|---|---|
| Build succeeded before deploy was triggered | |
| Preview URL is accessible and responds with HTTP 200 | |
| All Tier 1 smoke tests pass | |
| Tier 2 failures are documented with details | |
| No JavaScript console errors in the browser | |
| Environment variables are confirmed set (not just assumed) | |
| PR is commented with the preview URL and smoke test summary | |
| Deploy time is documented (for performance tracking) | |
| Any warnings or issues are clearly noted with severity | |
| Report uses the standard template format | |

### Pass/Fail Criteria

- **PASS:** All Tier 1 tests pass, no CRITICAL issues, preview URL accessible.
- **WARN:** Tier 2 failures exist but Tier 1 passes. Deploy is up but has issues.
- **FAIL:** Build failed, Tier 1 test failed, or preview URL is inaccessible.

---

## 5. Skill Definition (Orchestration)

### Sub-Tasks

```yaml
tasks:
  - id: dp-01
    name: verify-build
    action: "Run `npm run build` and capture output. Check for errors and warnings."
    output: "Build status (pass/fail), duration, warnings"

  - id: dp-02
    name: run-typecheck
    action: "Run `npx tsc --noEmit` to verify TypeScript compilation"
    output: "TypeScript status (pass/fail), error count"

  - id: dp-03
    name: run-lint
    action: "Run `npm run lint` to check code style"
    output: "Lint status (pass/fail), warning count"

  - id: dp-04
    name: run-tests
    action: "Run `npm test` and capture results"
    output: "Test status (pass/fail), pass/fail/skip counts"

  - id: dp-05
    name: check-env-vars
    action: "Compare .env.example with Vercel project env vars. Flag any missing."
    output: "Env var status, list of missing vars"

  - id: dp-06
    name: scan-secrets
    action: "Grep source code for secret patterns (API keys, tokens, passwords)"
    output: "Secrets scan status (clean/found), details if found"

  - id: dp-07
    name: trigger-vercel-deploy
    action: "Push branch to trigger Vercel preview build, or run `vercel` CLI"
    depends_on: [dp-01, dp-02, dp-03, dp-04, dp-05, dp-06]
    output: "Deployment ID, build URL"
    gate: "All pre-deploy checks must pass (no CRITICAL failures)"

  - id: dp-08
    name: wait-for-deployment
    action: "Poll Vercel deployment status until 'READY' or 'ERROR'"
    depends_on: [dp-07]
    output: "Preview URL or error details"
    timeout: "300 seconds"

  - id: dp-09
    name: smoke-test-tier1
    action: "Check homepage returns 200, assets load, no 500 errors"
    depends_on: [dp-08]
    output: "Tier 1 results table"

  - id: dp-10
    name: smoke-test-tier2
    action: "Check key routes render, API responds, DB connected, auth page works"
    depends_on: [dp-08]
    output: "Tier 2 results table"

  - id: dp-11
    name: smoke-test-tier3
    action: "Check external integrations, real-time, file operations"
    depends_on: [dp-08]
    output: "Tier 3 results table"

  - id: dp-12
    name: check-console-errors
    action: "Load preview URL in headless browser, capture console errors"
    depends_on: [dp-08]
    output: "Console error list (if any)"

  - id: dp-13
    name: generate-report
    action: "Compile all results into the deploy report template"
    depends_on: [dp-09, dp-10, dp-11, dp-12]
    output: "Complete deploy report markdown"

  - id: dp-14
    name: comment-on-pr
    action: "Post deploy report as PR comment via `gh pr comment <number> --body <report>`"
    depends_on: [dp-13]
    output: "PR comment URL"

  - id: dp-15
    name: update-work-item
    action: "If a work_item is linked, update it with the preview_url field"
    depends_on: [dp-08]
    output: "Work item updated confirmation"
```

### Execution Flow

```
dp-01 (build) ──┐
dp-02 (tsc)   ──┤
dp-03 (lint)  ──┤──> dp-07 (trigger deploy) ──> dp-08 (wait)
dp-04 (tests) ──┤                                  |
dp-05 (envs)  ──┤                            ┌─────┼─────┐
dp-06 (secrets)─┘                            v     v     v
                                          dp-09  dp-10  dp-11
                                          (T1)   (T2)   (T3)
                                            |     |      |
                                            v     v      v
                                   dp-12 (console) ──> dp-13 (report)
                                                          |
                                                    dp-14 (PR comment)
                                                    dp-15 (work item)
```

### Smoke Test Implementation

When no `tests/smoke.config.ts` exists, the agent uses `curl` and basic checks:

```bash
# Tier 1: Availability
PREVIEW_URL="https://project-branch.vercel.app"

# Homepage returns 200
curl -s -o /dev/null -w "%{http_code}" "$PREVIEW_URL" | grep -q "200"

# Static assets load (check for CSS/JS in HTML)
curl -s "$PREVIEW_URL" | grep -q '<link rel="stylesheet"'
curl -s "$PREVIEW_URL" | grep -q '<script'

# Key routes return 200 (not 500)
for route in "/dashboard" "/api/health" "/login"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$PREVIEW_URL$route")
  echo "$route: $STATUS"
done
```

When `tests/smoke.config.ts` exists, run with Playwright:

```bash
PREVIEW_URL="$PREVIEW_URL" npx playwright test tests/smoke/ --reporter=json
```

---

## 6. HITL Build

### Agent Autonomy

The deploy preview agent operates **autonomously** for standard deployments. Preview
deployments are low-risk (ephemeral, isolated, no production impact).

**Autonomous actions:**
- Run all pre-deploy checks (build, tests, lint, typecheck)
- Scan for secrets in source code
- Verify environment variables are configured
- Trigger Vercel preview deployment
- Run all smoke tests
- Post deploy report to PR
- Update work item with preview URL

**Escalation triggers (agent stops and asks for help):**
- Build fails — report the error and suggest fixes, but do not attempt auto-fix
- Missing environment variables — list which vars are needed, ask human to configure
- Smoke tests Tier 1 fail — deployment is broken, escalate for investigation
- Secrets detected in source code — STOP immediately, alert human, do not deploy
- Vercel deployment times out (>5 minutes) — escalate, may be infrastructure issue
- npm audit finds critical vulnerability in production dependency — escalate before deploy

### Safety Constraints

- The agent MUST NOT deploy to production (only preview environments)
- The agent MUST NOT create or modify environment variables in Vercel
- The agent MUST NOT expose secrets in PR comments or deploy reports
- The agent MUST NOT bypass failing pre-deploy checks (no `--force` deploys)
- The agent MUST stop if secrets are detected in the codebase
- The agent MUST NOT modify source code to fix build errors (that is the developer's job)

---

## 7. HITL Review

### No Formal Review Required

Preview deployments do not require formal human review of the deploy report. The purpose
of the preview is to BE the review — humans review the application by visiting the URL.

### What the Human Does

After receiving the deploy report PR comment:

1. **Click the preview URL** and manually explore the deployed application.
2. **Check the smoke test results** in the report for any warnings.
3. **Test the specific feature** implemented in the PR.
4. **Leave feedback** as PR review comments on specific code or behavior.

### When Human Intervention IS Needed

- **Build failures:** The developer must fix the code. The agent provides the error output.
- **Missing env vars:** A project admin must configure them in Vercel settings.
- **Tier 1 smoke failures:** Something is fundamentally wrong. Developer must investigate.
- **Security findings:** A senior developer must review any flagged security issues.

### Re-Deploy Flow

When the developer pushes fixes after a failed deploy:

1. The agent automatically re-runs the full pipeline (no manual trigger needed).
2. A new deploy report replaces the old one in the PR comments.
3. The previous preview URL remains accessible (Vercel keeps old deployments).
4. Smoke tests run again against the new preview URL.

### Deploy Report Retention

- Deploy reports are kept as PR comments for the lifetime of the PR.
- When the PR is merged, the preview URL expires (Vercel default behavior).
- The deploy report in the PR comments serves as a historical record.
- No separate archival is needed — GitHub preserves PR comment history.
