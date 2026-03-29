---
name: subagent-dev
description: "TDD implementation of a single plan task using RED-GREEN-REFACTOR protocol"
---

# Subagent Dev

Implement a single task from `docs/plan.md` using strict test-driven development. Each task is executed in isolation: read the task, write a failing test, make it pass with minimal code, refactor, commit. The subagent operates within tight boundaries — only touching files relevant to the assigned task.

---

## 1. Input

### Required

| Input | Location | Description |
|-------|----------|-------------|
| Task number | `docs/plan.md` | The specific task row (e.g., `#4`) to implement. Must have status `TODO` or `IN_PROGRESS`. |
| `plan.md` | `docs/` | Full delivery plan with task table, dependencies, and acceptance criteria. |
| `architecture.md` | `docs/` | System architecture — component boundaries, data flow, conventions. |
| `CLAUDE.md` | Project root | Tech stack, coding standards, project conventions. |

### Optional

| Input | Location | Description |
|-------|----------|-------------|
| Existing source files | `src/` | Files that the task modifies or depends on. |
| Existing test files | `tests/` | Tests that must continue passing after implementation. |
| Previous task commits | Git history | Context for how dependencies were implemented. |

### Input Validation

Before starting implementation:
- [ ] Task number exists in plan.md
- [ ] Task status is `TODO` (not `DONE`, not `BLOCKED`)
- [ ] All dependency tasks (from the Deps column) have status `DONE`
- [ ] Acceptance criteria are present and testable
- [ ] architecture.md exists (if missing, escalate — do not proceed)

If any dependency is not `DONE`, report the blocker and stop:
```
BLOCKED: Task #4 depends on Task #2 (status: IN_PROGRESS).
Cannot proceed until dependency is complete.
```

---

## 2. Thinking Frameworks

### RED-GREEN-REFACTOR Cycle

The core protocol. Every implementation follows this exact loop:

```
RED    → Write a test that expresses the desired behavior. Run it. It MUST fail.
         If it passes, either the behavior already exists or the test is wrong.

GREEN  → Write the MINIMUM code to make the test pass. No more.
         Resist the urge to add "while I'm here" code. That's a different task.

REFACTOR → With all tests green, improve code quality.
           Rename, extract, simplify. Tests must stay green throughout.
```

**Why RED first matters:** Writing the test first forces you to think about the interface before the implementation. It catches design problems early — if a test is hard to write, the interface is wrong.

### Minimal Implementation Principle

At the GREEN step, write the least code that makes the test pass. This means:
- Hard-code return values if only one test case exists
- Use the simplest data structure that works
- Skip optimizations, caching, error handling UNLESS the test demands it
- Let subsequent RED steps drive out generality

This feels wrong but is correct. Over-engineering at GREEN creates untested code paths.

### Isolation Rules

The subagent receives ONLY:
- The task description and acceptance criteria
- Architecture constraints relevant to this task
- Source files the task directly modifies or depends on
- Existing tests for the affected files

The subagent does NOT:
- Modify files outside the task scope
- Refactor unrelated code ("while I'm here" syndrome)
- Add features not in the acceptance criteria
- Change architecture without escalating

### Test-First Design Questions

Before writing any test, answer these:
1. **What is the function/component signature?** (Name, parameters, return type)
2. **What does success look like?** (The happy path assertion)
3. **What are the edge cases?** (Null, empty, boundary values)
4. **What errors can occur?** (Invalid input, missing dependencies, network failures)
5. **How does this integrate with existing code?** (Imports, data flow)

### Refactor Triggers

After GREEN, check for these refactor signals:
- **Duplication:** Same logic appears in 2+ places → extract to a shared function
- **Unclear naming:** Variable or function name doesn't communicate intent → rename
- **Long function:** Function exceeds 20 lines → extract sub-functions
- **Magic values:** Hard-coded strings or numbers → extract to constants
- **Deep nesting:** More than 2 levels of if/else → use early returns or extract
- **Mixed concerns:** Function does I/O AND computation → separate them

### Two-Stage Review Gate

Each task goes through two quality gates:
1. **Self-review (automated):** All tests pass, no linting errors, acceptance criteria met
2. **Code review (via /review skill):** Style, architecture alignment, edge cases

Both must pass before the task is marked `DONE`.

---

## 3. Expected Output

### Primary Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Implementation files | `src/` | New or modified source files for the task |
| Unit test files | `tests/unit/` | Tests written during RED phases |
| Updated plan.md | `docs/plan.md` | Task status changed to `DONE` |

### Git Commits

Each GREEN step produces a commit:
```
feat(#4): add user validation endpoint

- RED: test expects POST /users/validate to return 200 for valid input
- GREEN: implement validation with schema check
- All tests passing (14 pass, 0 fail)
```

Commit message format:
```
{type}(#{task_number}): {short description}

{optional body with RED/GREEN/REFACTOR context}
```

Types: `feat` (new functionality), `fix` (bug fix), `refactor` (no behavior change), `test` (test-only changes)

### Secondary Outputs

- Console log of test results at each RED/GREEN/REFACTOR step
- List of files modified
- Any escalation notes (ambiguities found, architecture concerns)

### Example RED-GREEN-REFACTOR Sequence

```
Task #4: "Validate user email format on registration"

--- RED ---
// tests/unit/user-validation.test.ts
describe('validateUserEmail', () => {
  it('should return valid for a correct email', () => {
    expect(validateUserEmail('user@example.com')).toEqual({ valid: true });
  });

  it('should return invalid for missing @ symbol', () => {
    expect(validateUserEmail('userexample.com')).toEqual({
      valid: false,
      error: 'Invalid email format',
    });
  });

  it('should return invalid for empty string', () => {
    expect(validateUserEmail('')).toEqual({
      valid: false,
      error: 'Email is required',
    });
  });
});

> Run: npx vitest run tests/unit/user-validation.test.ts
> Result: 3 FAILED (function not found) ✓ Tests correctly fail

--- GREEN ---
// src/validators/user-validation.ts
export function validateUserEmail(email: string) {
  if (!email) return { valid: false, error: 'Email is required' };
  if (!email.includes('@')) return { valid: false, error: 'Invalid email format' };
  return { valid: true };
}

> Run: npx vitest run tests/unit/user-validation.test.ts
> Result: 3 PASSED ✓

--- REFACTOR ---
// Extract email regex to constant, improve readability
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateUserEmail(email: string) {
  if (!email) {
    return { valid: false, error: 'Email is required' };
  }

  if (!EMAIL_PATTERN.test(email)) {
    return { valid: false, error: 'Invalid email format' };
  }

  return { valid: true };
}

> Run: npx vitest run tests/unit/user-validation.test.ts
> Result: 3 PASSED ✓ (behavior unchanged, code improved)

> git commit -m "feat(#4): add email validation for user registration"
```

---

## 4. Review / Rubric

### Automated Checks (Self-Review)

| Criterion | Check | Severity |
|-----------|-------|----------|
| All new tests pass | `npx vitest run` exits 0 | BLOCKER |
| No existing tests broken | Full test suite passes | BLOCKER |
| Test was RED before GREEN | Verified test failure before implementation | BLOCKER |
| Code traces to spec requirement | Task AC maps to spec via plan.md | BLOCKER |
| No TODO/FIXME without tracking | Grep for TODO/FIXME, each must reference a task # | WARNING |
| Commit messages reference task | Commit includes `(#{task_number})` | WARNING |
| No files modified outside task scope | Diff only touches expected files | WARNING |
| Linting passes | `npx eslint` or project linter exits 0 | WARNING |

### Code Quality Checks

| Criterion | Check | Severity |
|-----------|-------|----------|
| Functions under 30 lines | Manual review of new functions | WARNING |
| No magic values | Grep for unexplained numbers/strings | WARNING |
| Consistent naming with project | Compare to existing code conventions | WARNING |
| Error cases handled | Each function that can fail has error paths | WARNING |
| Types/interfaces defined | No `any` types in TypeScript | WARNING |

### Test Quality Checks

| Criterion | Check | Severity |
|-----------|-------|----------|
| Tests cover happy path | At least one test for expected behavior | BLOCKER |
| Tests cover error paths | At least one test for failure mode | WARNING |
| Tests are independent | No test relies on another test's state | BLOCKER |
| Test names describe behavior | `should {verb} when {condition}` format | WARNING |
| No implementation-detail testing | Tests assert behavior, not internals | WARNING |

---

## 5. Skill Definition (Orchestration)

### Sub-Tasks

**Step 1: Read and validate the task**
Read `docs/plan.md`. Find the assigned task row. Verify status is `TODO`. Verify all dependencies are `DONE`. Extract the acceptance criteria. If validation fails, stop and report.

**Step 2: Update task status to IN_PROGRESS**
Change the task status in `docs/plan.md` from `TODO` to `IN_PROGRESS`. This signals to other subagents (or the human) that work is underway.

**Step 3: Identify affected files**
From the task description, determine which source files and test files will be created or modified. Check if they already exist. Read their current content to understand the starting state.

**Step 4: Read architecture constraints**
Read `docs/architecture.md` for rules that apply to this task — component boundaries, data flow direction, naming patterns, module structure. Note any constraints that affect implementation decisions.

**Step 5: Read project conventions**
Read `CLAUDE.md` for tech stack details, import conventions, file organization rules. Check existing code in `src/` for patterns to follow (e.g., how other similar functions/components are structured).

**Step 6: Design test cases**
Based on the acceptance criteria, design test cases covering:
- Happy path (the main success scenario)
- Error paths (what happens when inputs are wrong)
- Boundary values (empty, null, max values)
Write test case descriptions BEFORE writing test code.

**Step 7: Write failing tests (RED)**
Write the test file(s) in `tests/unit/`. Import the function/component to test (even though it doesn't exist yet — this will cause the failure). Run the tests. Verify they fail. If they pass, investigate — either the behavior exists or the test is wrong.

```bash
npx vitest run tests/unit/{test-file}.test.ts
```

**Step 8: Write minimal implementation (GREEN)**
Create or modify source files in `src/` with the minimum code needed to make all tests pass. Follow architecture constraints and project conventions. Do not add anything beyond what the tests require.

```bash
npx vitest run tests/unit/{test-file}.test.ts
```

Verify all new tests pass.

**Step 9: Run full test suite**
Run the entire test suite to ensure nothing is broken:

```bash
npx vitest run
```

If existing tests fail, investigate. If the failure is caused by the new code, fix it. If the failure is pre-existing (flaky test), document it and escalate.

**Step 10: Refactor (REFACTOR)**
With all tests green, review the new code for refactor triggers: duplication, unclear naming, long functions, magic values, deep nesting. Apply refactoring. Run tests after each change to confirm they still pass.

**Step 11: Final test verification**
Run the full suite one more time after all refactoring:

```bash
npx vitest run
```

All tests must pass.

**Step 12: Lint check**
Run the project linter:

```bash
npx eslint src/{modified-files} tests/unit/{test-files}
```

Fix any linting issues. Re-run tests if code changed.

**Step 13: Commit with task reference**
Stage all modified files and commit with a message referencing the task number:

```bash
git add src/{files} tests/unit/{files}
git commit -m "feat(#N): {description of what was implemented}"
```

**Step 14: Check acceptance criteria**
Review each acceptance criterion from the task. Verify it is met by the implementation and covered by tests. If any criterion is not met, go back to Step 7 (RED) for the unmet criterion.

**Step 15: Update plan.md status**
Change the task status in `docs/plan.md` from `IN_PROGRESS` to `DONE`. Commit this change:

```bash
git add docs/plan.md
git commit -m "chore(#N): mark task #N as DONE"
```

**Step 16: Request code review**
Invoke the `/review` skill (or present for human review if /review is not available). Provide the diff of all commits for this task.

**Step 17: Handle review feedback**
If the review returns blockers:
1. Read the feedback
2. Write a failing test for the issue (RED)
3. Fix the issue (GREEN)
4. Run all tests
5. Commit the fix with reference: `fix(#N): address review feedback — {description}`
6. Re-request review

If the review passes, the task is complete.

---

## 6. HITL Build

### Agent Responsibilities (Autonomous)

- Reading and understanding the task
- Writing tests (RED)
- Writing implementation (GREEN)
- Refactoring (REFACTOR)
- Running tests and linter
- Committing code
- Updating plan status
- Self-reviewing against the rubric

### Human Escalation Triggers

| Trigger | What to Present | Action |
|---------|----------------|--------|
| Task requires architecture change | Describe what the task needs vs. what architecture.md allows | STOP — wait for architect |
| Spec is ambiguous for this task | Quote the ambiguous AC, offer interpretations | STOP — wait for PM |
| Existing tests conflict with new requirements | Show the conflicting test and the new requirement | STOP — human decides which is correct |
| Dependency task is not DONE | Show blocked status and dependency chain | STOP — cannot proceed |
| architecture.md is missing | Cannot proceed without knowing component boundaries | STOP — request architecture first |
| Pre-existing test failure (flaky) | Show the failing test and evidence it's not caused by new code | CONTINUE — document and flag |
| Task scope seems wrong | Task AC doesn't match spec requirement it claims to cover | STOP — wait for PM |

### Agent Boundaries

- **DO:** Write code, write tests, commit, update plan
- **DO NOT:** Modify architecture decisions
- **DO NOT:** Change task scope or acceptance criteria
- **DO NOT:** Touch files unrelated to the current task
- **DO NOT:** Skip the RED step (writing tests first)
- **DO NOT:** Skip the GREEN verification (running tests after implementation)
- **DO NOT:** Commit code with failing tests

---

## 7. HITL Review

### Review Level: NONE (for individual tasks)

Individual task implementations are reviewed automatically via the `/review` skill or the self-review rubric. Human review happens at the PR level, not the task level.

### When Human Review IS Required

- First task of the project (to validate the pattern)
- Tasks that introduced an escalation (even if resolved)
- Tasks touching auth, payments, or data deletion
- Any task where the agent had low confidence

### PR-Level Review

When all tasks in a phase are `DONE`, a PR is created for the phase. At that point:

1. **Agent prepares:**
   - PR description listing all tasks completed
   - Summary of any escalations and how they were resolved
   - Test coverage summary
   - Architecture compliance notes

2. **Human reviews:**
   - Overall approach and code quality
   - Architecture alignment
   - Test coverage adequacy
   - Edge cases and error handling

3. **Approval flow:**
   - **Approved** — merge the phase
   - **Changes requested** — agent creates fix tasks and executes them
   - **Rejected** — phase is reverted, root cause analyzed

### Post-Task Checklist

Before declaring a task complete, verify:
- [ ] All tests pass (new and existing)
- [ ] Lint passes
- [ ] Commits reference the task number
- [ ] plan.md status is `DONE`
- [ ] No files modified outside task scope
- [ ] No TODO/FIXME without a tracking reference
- [ ] Acceptance criteria are met
