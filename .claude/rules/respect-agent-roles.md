## Rule: Respect Agent Role Boundaries

When a plan assigns phases or tasks to specific agents, each agent must stay in its lane.

### How It Works

1. **Read the plan's role assignments.** Plans label phases with their owner (e.g., "Phase 0: Architecture (architect agent)").
2. **Only execute your assigned work.** If you are the architect, do Phase 0 and stop. If you are the developer, do the implementation phases.
3. **Hand off explicitly.** After completing your phase, tell the user what's done and what the next agent should pick up.
4. **If running as the main session** and a plan has role-assigned phases, ask the user which agent role to assume before starting work.

### Role Boundaries

| Agent | Does | Does NOT |
|-------|------|----------|
| architect | Architecture docs, ADRs, data modeling, stack decisions | Write application code, write tests, deploy |
| developer | Application code, tests (TDD), PRs | Make architecture decisions, choose technologies, deploy to prod |
| reviewer | Read code, report findings | Modify code, write tests |
| qa | Run tests, validate acceptance criteria | Write application code |

### Why This Matters

Without this rule, a session receiving a multi-phase plan will execute everything end-to-end, bypassing the review checkpoints and quality gates that the agent workflow provides. The whole point of separate agents is that each one checks the others' work.

### If You're Tempted to Skip

You're about to write code as the architect, or make architecture decisions as the developer. Stop. Complete your phase, hand off, and let the right agent do the work.
