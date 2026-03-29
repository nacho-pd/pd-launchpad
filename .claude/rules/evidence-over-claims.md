## Rule: Evidence Over Claims

"Done" is not a status you declare. It's a status you prove.

### What Counts as Evidence

A task is done when ALL of these are true:
1. **Tests pass** — Unit and e2e tests green in CI.
2. **Review approved** — Code review completed with no blocking issues.
3. **Preview verified** — Deployed preview matches acceptance criteria.

### What Does NOT Count

- "I wrote the code" — Code without tests is not done.
- "It works on my machine" — CI must confirm.
- "I think it looks good" — Review must confirm.
- "I tested it manually" — Automated tests must confirm.

### If You're Tempted to Skip

Update the work_item with the evidence: test run URL, review approval, preview URL. If you can't provide all three, the task is not done.
