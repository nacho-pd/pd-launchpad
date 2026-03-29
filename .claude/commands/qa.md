# /qa — Full Test Suite Execution

Run the complete test suite and report results.

## When to Use

- After implementation is complete and review is approved.
- Before creating a PR.
- When you need confidence that nothing is broken.

## Execution

1. Invoke the **qa** agent.
2. The qa agent runs the `/testing` skill:
   - **Unit tests**: `npm run test:unit` (Vitest)
   - **E2E tests**: `npm run test:e2e` (Playwright)
3. Results are collected and summarized.

## Output Format

```
## QA Report — [branch-name]

### Unit Tests
- Total: X | Passed: X | Failed: X | Skipped: X
- Duration: Xs
- Failed tests: (list if any)

### E2E Tests
- Total: X | Passed: X | Failed: X | Skipped: X
- Duration: Xs
- Failed tests: (list if any)

### Coverage Gaps
- (any acceptance criteria not covered by tests)

### Verdict: [PASS | FAIL]
```

## After QA

- **PASS**: Proceed to PR creation or `/ship`.
- **FAIL**: Fix failures, then re-run `/qa`.
