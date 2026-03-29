# /review — Two-Stage Code Review

Trigger a comprehensive code review on the current branch.

## When to Use

- After completing implementation of one or more tasks.
- Before creating a PR.
- When you want spec compliance + code quality validation.

## Execution

1. Invoke the **reviewer** agent.
2. The reviewer runs the `/code-reviewing` skill with two stages:
   - **Stage 1 — Spec Compliance**: Every change maps to a spec requirement.
   - **Stage 2 — Code Quality**: Readability, security, performance, anti-patterns.
3. Findings are tagged by severity: `BLOCKER`, `WARNING`, `NIT`.
4. Verdict: `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_DISCUSSION`.

## Output Format

```
## Review Report — [branch-name]

### Stage 1: Spec Compliance
- [SEVERITY] Finding description (spec ref: requirement X)

### Stage 2: Code Quality
- [SEVERITY] Finding description

### Verdict: [APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION]
```

## After Review

- **APPROVE**: Proceed to PR creation or `/ship`.
- **REQUEST_CHANGES**: Fix blockers, then re-run `/review`.
- **NEEDS_DISCUSSION**: Escalate to human for decision.
