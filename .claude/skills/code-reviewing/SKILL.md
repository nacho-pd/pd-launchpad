---
name: code-reviewing
description: "Two-stage code review: spec compliance first, then code quality"
---

# Code Reviewing

Two-stage structured code review that verifies spec compliance before evaluating code quality.
Stage 1 ensures every change traces to a requirement. Stage 2 catches quality, security, and
maintainability issues. The agent never modifies code — it produces a review report only.

---

## 1. Input

The agent requires the following inputs to perform a review:

| Input | Source | Required |
|---|---|---|
| PR diff or branch changes | `git diff main...HEAD` or GitHub PR diff | Yes |
| Spec document | `docs/specs/<feature>.md` or linked issue | Yes |
| Architecture document | `docs/architecture.md` | Yes |
| Test results | `npm test` / `npx vitest run` output | Yes |
| Previous review comments | GitHub PR comments (if re-review) | No |
| Lint/type-check output | `npm run lint` / `npx tsc --noEmit` | No |

### Input Validation

Before starting the review, verify:

1. The diff is non-empty (there are actual changes to review).
2. A spec document exists and is referenced in the PR description or can be inferred from the branch name.
3. Tests have been executed — do not review untested code without flagging it.
4. The architecture document is present and up to date (check last-modified vs. PR date).

If any required input is missing, stop and request it before proceeding.

---

## 2. Thinking Frameworks

### 2.1 Two-Stage Review Model

Reviews are split into two distinct stages to prevent quality concerns from overshadowing
compliance gaps. Stage 1 must complete before Stage 2 begins.

**Stage 1 — Spec Compliance:**
- Does every requirement in the spec have corresponding implementation?
- Does every code change trace back to a spec requirement?
- Are acceptance criteria met (not just "code exists" but "code satisfies")?
- Is test coverage aligned with spec requirements (each requirement has at least one test)?

**Stage 2 — Code Quality:**
- Readability: Can a new team member understand this code in 5 minutes?
- Maintainability: Will this code be easy to modify in 6 months?
- Performance: Are there obvious N+1 queries, unnecessary re-renders, or O(n^2) loops?
- Security: Does the code handle user input safely?

### 2.2 Severity Classification

Every finding must be tagged with exactly one severity level:

| Severity | Label | Meaning | Merge Gate |
|---|---|---|---|
| Critical | `BLOCKER` | Must fix before merge. Breaks functionality, security vulnerability, data loss risk, spec violation. | Blocks merge |
| Important | `WARNING` | Should fix before merge. Tech debt, performance concern, missing edge case. | Strongly recommended |
| Minor | `NIT` | Optional improvement. Style preference, alternative approach suggestion, naming improvement. | No gate |

**Rules for severity assignment:**
- A finding is a BLOCKER only if it causes incorrect behavior, a security vulnerability, or violates a spec requirement.
- Do not inflate severity. If unsure between WARNING and BLOCKER, choose WARNING and explain why it could be either.
- NITs must never exceed 30% of total findings. If they do, keep only the most impactful ones.

### 2.3 Spec Traceability Matrix

Build a traceability matrix mapping each spec requirement to its implementation:

```
| Req ID | Requirement Summary          | Files Changed        | Test Coverage | Status    |
|--------|------------------------------|----------------------|---------------|-----------|
| R-01   | User can create a project    | src/api/projects.ts  | create.test.ts| COVERED   |
| R-02   | Project names must be unique | src/api/projects.ts  | create.test.ts| COVERED   |
| R-03   | Soft delete with 30-day TTL  | —                    | —             | MISSING   |
```

Status values: `COVERED` (code + test), `PARTIAL` (code but incomplete test), `MISSING` (no implementation found), `EXTRA` (code exists without spec justification).

### 2.4 Code Quality Dimensions

Evaluate each changed file against these dimensions:

**Readability:**
- Function length (flag functions >40 lines)
- Nesting depth (flag >3 levels of nesting)
- Variable naming (descriptive, consistent casing)
- Comments explain "why" not "what"

**Maintainability:**
- Single responsibility (each function does one thing)
- DRY violations (duplicated logic across files)
- Coupling (changes in one module force changes in others)
- Configuration vs. hardcoding

**Performance:**
- Database query patterns (N+1 queries, missing indexes)
- React re-render patterns (missing memoization on expensive components)
- Bundle size impact (large imports that could be lazy-loaded)
- Unnecessary synchronous operations that could be async

**Security (OWASP Top 10 focus):**
- Injection: SQL injection via string concatenation, XSS via dangerouslySetInnerHTML
- Broken auth: Missing auth checks on API routes, token exposure in logs
- Sensitive data exposure: Secrets in code, PII in logs, credentials in URLs
- Broken access control: Missing RLS policies, IDOR vulnerabilities
- Security misconfiguration: Debug mode in production, permissive CORS
- Insecure deserialization: Unvalidated JSON parsing from external sources

### 2.5 Anti-Pattern Detection

Actively scan for these anti-patterns:

- **Dead code:** Unused imports, unreachable branches, commented-out code blocks
- **Magic numbers:** Numeric literals without named constants (`if (status === 3)`)
- **God functions:** Functions exceeding 60 lines or accepting >5 parameters
- **Excessive complexity:** Cyclomatic complexity >10 in a single function
- **Missing error handling:** try/catch without meaningful error handling, unhandled promise rejections
- **Console statements:** `console.log` left in production code (use structured logging)
- **Any types:** TypeScript `any` usage that bypasses type safety
- **Hardcoded URLs/keys:** Environment-specific values not using env vars
- **Missing input validation:** API endpoints accepting user input without schema validation (use zod)
- **Inconsistent patterns:** Mixing async/await with .then(), mixing named and default exports

---

## 3. Expected Output

### Review Report Template

```markdown
# Code Review Report

**PR:** #<number> — <title>
**Reviewer:** code-reviewing agent
**Date:** <ISO date>
**Verdict:** APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION

---

## Stage 1: Spec Compliance

**Spec:** docs/specs/<feature>.md
**Requirements coverage:** X/Y requirements covered

### Traceability Matrix

| Req ID | Requirement | Implementation | Tests | Status |
|--------|------------|----------------|-------|--------|
| ... | ... | ... | ... | ... |

### Compliance Findings

#### [BLOCKER] R-03: Soft delete not implemented
**File:** —
**Details:** The spec requires soft delete with a 30-day TTL. No implementation
found in the diff. The DELETE endpoint performs a hard delete.
**Suggested fix:** Add a `deleted_at` timestamp column. Change DELETE to set
this field. Add a scheduled job or database trigger for TTL cleanup.

#### [WARNING] R-02: Uniqueness check is case-sensitive
**File:** src/api/projects.ts:42
**Details:** The unique name check uses exact match. Spec says "names should be
unique regardless of case." Users could create "My Project" and "my project."
**Suggested fix:** Use `.toLowerCase()` comparison or a case-insensitive
database constraint.

---

## Stage 2: Code Quality

### Quality Summary

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Readability | Good | Clear naming, reasonable function lengths |
| Maintainability | Needs Work | Some DRY violations between create/update |
| Performance | Good | No obvious issues |
| Security | Warning | Missing input validation on POST /projects |

### Quality Findings

#### [WARNING] Missing input validation
**File:** src/api/projects.ts:28
**Details:** The POST endpoint reads `req.body.name` without validation.
**Suggested fix:** Add a zod schema for request body validation.

#### [NIT] Consider extracting shared logic
**File:** src/api/projects.ts:42, src/api/projects.ts:78
**Details:** Create and update handlers duplicate the name normalization logic.
**Suggested fix:** Extract to a `normalizeProjectName()` helper.

---

## Summary

- **Blockers:** 1
- **Warnings:** 2
- **Nits:** 1
- **Verdict:** REQUEST_CHANGES — 1 blocker must be resolved before merge.
```

---

## 4. Review / Rubric

### Report Quality Checklist

| Criterion | Pass/Fail |
|---|---|
| Every spec requirement appears in the traceability matrix | |
| All findings have a file reference and line number (where applicable) | |
| All BLOCKERs cite a concrete correctness, security, or spec violation | |
| No false positives in security findings (verified against actual code) | |
| Every finding includes a suggested fix (not just a complaint) | |
| Tone is constructive and professional (no sarcasm, no "obviously") | |
| NITs do not exceed 30% of total findings | |
| Verdict matches findings (REQUEST_CHANGES only if BLOCKERs exist) | |
| Stage 1 findings are separate from Stage 2 findings | |
| Report is under 500 lines (concise, not exhaustive) | |

### Verdict Rules

- `APPROVE`: Zero BLOCKERs. Warnings are present but non-critical.
- `REQUEST_CHANGES`: One or more BLOCKERs exist. Cannot merge until resolved.
- `NEEDS_DISCUSSION`: Findings are ambiguous. Spec is unclear on a requirement.
  The reviewer cannot determine correctness without human input.

---

## 5. Skill Definition (Orchestration)

### Sub-Tasks

```yaml
tasks:
  - id: cr-01
    name: read-pr-diff
    action: "Run `git diff main...HEAD` or fetch PR diff via `gh pr diff <number>`"
    output: "Full diff text"

  - id: cr-02
    name: read-spec
    action: "Read the spec document referenced in the PR description or inferred from branch name"
    input: "PR description, branch name"
    output: "Parsed spec with numbered requirements"

  - id: cr-03
    name: read-architecture
    action: "Read docs/architecture.md for structural context"
    output: "Architecture constraints and patterns"

  - id: cr-04
    name: run-tests
    action: "Execute `npm test` and capture output"
    output: "Test results with pass/fail counts"

  - id: cr-05
    name: build-traceability-matrix
    action: "Map each spec requirement to changed files and test files"
    depends_on: [cr-01, cr-02]
    output: "Traceability matrix table"

  - id: cr-06
    name: check-spec-coverage
    action: "For each requirement, verify implementation exists in the diff"
    depends_on: [cr-05]
    output: "List of COVERED, PARTIAL, MISSING requirements"

  - id: cr-07
    name: check-extra-code
    action: "For each changed file, verify every change traces to a requirement"
    depends_on: [cr-05]
    output: "List of EXTRA code without spec justification"

  - id: cr-08
    name: check-test-coverage
    action: "Verify each requirement has at least one corresponding test"
    depends_on: [cr-04, cr-05]
    output: "Test coverage per requirement"

  - id: cr-09
    name: tag-compliance-findings
    action: "Compile Stage 1 findings with severity tags"
    depends_on: [cr-06, cr-07, cr-08]
    output: "Stage 1 findings list"

  - id: cr-10
    name: check-code-quality
    action: "Evaluate readability, maintainability, performance per changed file"
    depends_on: [cr-01, cr-03]
    output: "Quality dimension ratings and findings"

  - id: cr-11
    name: check-anti-patterns
    action: "Scan for anti-patterns: dead code, magic numbers, god functions, console.log, any types"
    depends_on: [cr-01]
    output: "Anti-pattern findings list"

  - id: cr-12
    name: check-security
    action: "Scan for OWASP top 10 issues relevant to the stack"
    depends_on: [cr-01, cr-03]
    output: "Security findings list"

  - id: cr-13
    name: check-naming-style
    action: "Verify naming conventions and code style consistency with existing codebase"
    depends_on: [cr-01, cr-03]
    output: "Style consistency findings"

  - id: cr-14
    name: generate-report
    action: "Compile all findings into the structured review report template"
    depends_on: [cr-09, cr-10, cr-11, cr-12, cr-13]
    output: "Complete review report markdown"

  - id: cr-15
    name: set-verdict
    action: "Determine verdict based on findings: APPROVE if 0 blockers, REQUEST_CHANGES if any blockers, NEEDS_DISCUSSION if spec ambiguity"
    depends_on: [cr-14]
    output: "Verdict with rationale"
```

### Execution Flow

```
cr-01 (diff) ──┬──> cr-05 (matrix) ──> cr-06 (coverage) ──┐
cr-02 (spec) ──┘                   ──> cr-07 (extra code) ─┤
cr-03 (arch) ──────> cr-10 (quality) ──────────────────────┤
cr-04 (tests) ─────> cr-08 (test cov) ────────────────────┤
               ────> cr-11 (anti-patterns) ────────────────┤
               ────> cr-12 (security) ─────────────────────┤
               ────> cr-13 (style) ────────────────────────┤
                                                           └──> cr-14 (report) ──> cr-15 (verdict)
```

---

## 6. HITL Build

### Agent Autonomy

The code review agent operates **READ-ONLY**. It never modifies source code, tests, or
configuration files. It produces a review report and posts it as a PR comment.

**Autonomous actions:**
- Read PR diff, spec, architecture, and test output
- Analyze code against all frameworks
- Generate the review report
- Post the report as a GitHub PR comment via `gh pr comment`

**Escalation triggers:**
- Spec document is missing or ambiguous — ask the developer to clarify before reviewing
- Architecture document is outdated (>30 days since last update) — flag but continue
- Test suite fails to run — report the failure and review code without test coverage data
- Conflicting requirements detected between spec and architecture — flag as NEEDS_DISCUSSION

### Safety Constraints

- The agent MUST NOT run `git push`, `git commit`, or any write operation
- The agent MUST NOT approve its own PRs or PRs from automated processes
- The agent MUST NOT modify `.env`, credentials, or deployment configuration
- The agent MUST flag but not attempt to fix security vulnerabilities

---

## 7. HITL Review

### Developer Response Flow

1. Agent posts the review report as a PR comment.
2. Developer reads the report and responds to each finding:
   - **BLOCKER:** Must be addressed. Developer fixes and pushes. Agent re-reviews.
   - **WARNING:** Should be addressed. Developer can push back with justification.
   - **NIT:** Optional. Developer may ignore without justification.
3. If the developer disagrees with a BLOCKER classification, they respond with rationale.
   The agent re-evaluates and may downgrade to WARNING if the rationale is sound.
4. Once all BLOCKERs are resolved, the agent updates the verdict to APPROVE.

### Re-Review Protocol

When the developer pushes fixes:
- The agent re-runs only the affected sub-tasks (not the full review).
- Previously approved findings are not re-checked unless the fix introduced new changes.
- The updated report replaces the original PR comment (edit, not new comment).

### Dispute Resolution

If a developer disputes a finding and the agent cannot resolve it:
- The finding is tagged as `NEEDS_DISCUSSION`.
- The verdict becomes `NEEDS_DISCUSSION`.
- A human reviewer is requested to make the final call.
