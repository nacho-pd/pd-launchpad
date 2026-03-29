## Rule: No Direct Deploy

Agents can deploy to preview and staging environments only. Production deployments require the `/ship` command, which includes human approval gates.

### Why This Matters

Production deployments affect real users. No automated system should push to production without a human explicitly approving the release. Preview and staging exist so humans can verify before committing.

### Allowed

- Deploy to Vercel preview branches (automatic on PR).
- Deploy to staging environments for testing.

### Forbidden

- Any agent running `vercel --prod` or equivalent.
- Bypassing the `/ship` checklist.
- Merging to main without review approval.

### If You're Tempted to Skip

Stop. Use `/ship`. It exists for a reason.
