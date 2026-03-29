# /ship — Production Deploy Checklist

Pre-flight checklist + production deployment with human approval gates.

## When to Use

- When all tasks are complete, reviewed, and QA-passed.
- Only a human can invoke this command.

## Pre-Flight Checklist

Before deploying, verify each item:

1. [ ] **All tests pass** — `npm run test` exits 0.
2. [ ] **Review approved** — No open blockers from `/review`.
3. [ ] **Preview verified** — Preview URL tested and accepted.
4. [ ] **No TODO/FIXME** — No unresolved items in changed files.
5. [ ] **Environment variables** — Production env vars set in Vercel.
6. [ ] **Database migrations** — Applied to production Supabase (if any).
7. [ ] **Changelog updated** — Summary of what's shipping.

## Execution

1. Run pre-flight checklist. Stop if any item fails.
2. **HUMAN GATE**: Present checklist results. Wait for explicit "proceed" confirmation.
3. Merge PR to main.
4. **HUMAN GATE**: Verify Vercel production build succeeds.
5. Run production smoke tests.
6. Update work_item status to `deployed`.
7. Post deployment summary.

## Output Format

```
## Ship Report — [version/PR]

### Pre-Flight
- [x] Tests pass
- [x] Review approved
- ...

### Deployment
- Production URL: [url]
- Build: [success/failure]
- Smoke tests: [pass/fail]

### Work Items Deployed
- [work_item_id]: [title]
```

## Rules

- **Never skip a human gate.** If in doubt, stop and ask.
- **Never deploy on Friday** unless explicitly approved.
- If anything fails, stop immediately and report.
