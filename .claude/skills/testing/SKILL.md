---
name: testing
description: "Design and execute unit tests (Vitest) and e2e tests (Playwright) from acceptance criteria"
---

# Testing

Design and execute comprehensive tests for features and components. Covers unit tests with Vitest and end-to-end tests with Playwright. Tests are derived from acceptance criteria and spec requirements, following the test pyramid principle: many fast unit tests, few slow e2e tests.

---

## 1. Input

### Required

| Input | Location | Description |
|-------|----------|-------------|
| Acceptance criteria | `docs/plan.md` task row or `docs/specs/*.md` | What "done" looks like — the behaviors to verify. |
| Component/page under test | `src/` | The source code to be tested. Must exist before tests are written (unless using TDD via subagent-dev). |
| `CLAUDE.md` | Project root | Tech stack, testing conventions, project rules. |

### Optional

| Input | Location | Description |
|-------|----------|-------------|
| Existing test files | `tests/` | Existing patterns to follow for consistency. |
| Test configuration | `vitest.config.ts`, `playwright.config.ts` | Framework setup, paths, timeouts. |
| Fixtures/factories | `tests/fixtures/` | Shared test data and factory functions. |

### Input Validation

Before writing tests:
- [ ] Acceptance criteria exist and are testable (binary pass/fail)
- [ ] Source code under test exists and is importable
- [ ] Test framework is configured (vitest.config.ts exists)
- [ ] For e2e tests: Playwright is installed and configured
- [ ] Existing test patterns reviewed for naming and structure conventions

---

## 2. Thinking Frameworks

### Test Pyramid

```
         /  E2E  \          Few — slow, expensive, high confidence
        /----------\
       / Integration \      Some — medium speed, moderate confidence
      /----------------\
     /    Unit Tests     \   Many — fast, cheap, focused confidence
    /______________________\
```

**Unit tests** verify isolated functions, components, and modules. They run in milliseconds, have no external dependencies, and should comprise 70-80% of the test suite.

**E2E tests** verify complete user flows through the real application. They are slow, can be flaky, and should only cover critical paths. Use them to verify that the system works as a whole, not to test logic.

**Rule of thumb:** If the behavior can be tested with a unit test, it MUST be a unit test. Only use e2e when testing requires a real browser, real navigation, or real system integration.

### Boundary Value Analysis

For any input with a range, test:
- **Minimum valid value** (e.g., 1 character, 0 items)
- **Maximum valid value** (e.g., 255 characters, max int)
- **Just below minimum** (e.g., 0 characters, -1)
- **Just above maximum** (e.g., 256 characters, max int + 1)
- **Typical value** (e.g., 50 characters, mid-range number)

```typescript
// Example: password validation with min length 8, max length 64
describe('validatePassword', () => {
  it('should accept exactly 8 characters (minimum)', () => { /* ... */ });
  it('should accept exactly 64 characters (maximum)', () => { /* ... */ });
  it('should reject 7 characters (below minimum)', () => { /* ... */ });
  it('should reject 65 characters (above maximum)', () => { /* ... */ });
  it('should accept 32 characters (typical)', () => { /* ... */ });
});
```

### Equivalence Partitioning

Group inputs into classes that should produce the same behavior. Test ONE representative from each class, not every possible value.

| Partition | Example Inputs | Expected Behavior |
|-----------|---------------|-------------------|
| Valid email | user@example.com, a@b.co | Accepted |
| Missing @ | userexample.com | Rejected with "invalid format" |
| Missing domain | user@ | Rejected with "invalid format" |
| Empty string | "" | Rejected with "required" |
| Null/undefined | null, undefined | Rejected with "required" |

### Error Path Coverage

For every function, ask: **"What happens when things go wrong?"**

- What if the input is null/undefined?
- What if the network request fails?
- What if the database returns no results?
- What if the user is not authenticated?
- What if the data is malformed?
- What if a dependency throws?

Each error path needs at least one test.

### Test Isolation Rules

Each test must be fully independent:
- **No shared mutable state** — each test sets up its own data
- **No order dependency** — tests pass in any order
- **No external calls** — mock network, database, filesystem
- **Clean up after yourself** — reset mocks, clear timers, remove DOM elements

```typescript
// BAD: Shared state between tests
let user: User;
beforeAll(() => { user = createUser(); });

it('should update name', () => {
  user.name = 'Alice';        // Mutates shared state
  expect(user.name).toBe('Alice');
});

it('should have default name', () => {
  expect(user.name).toBe('default'); // FAILS — previous test changed it
});

// GOOD: Each test creates its own state
it('should update name', () => {
  const user = createUser();
  user.name = 'Alice';
  expect(user.name).toBe('Alice');
});

it('should have default name', () => {
  const user = createUser();
  expect(user.name).toBe('default');
});
```

### Naming Convention

Follow the **describe-it** pattern: `"ComponentName > when condition > should behavior"`

```typescript
describe('LoginForm', () => {
  describe('when credentials are valid', () => {
    it('should redirect to dashboard', () => { /* ... */ });
    it('should store the auth token', () => { /* ... */ });
  });

  describe('when credentials are invalid', () => {
    it('should display an error message', () => { /* ... */ });
    it('should not redirect', () => { /* ... */ });
  });

  describe('when network is unavailable', () => {
    it('should display a connection error', () => { /* ... */ });
    it('should allow retry', () => { /* ... */ });
  });
});
```

Tests named this way read as living documentation. Running the test suite produces a readable spec.

### The "One Assert Per Concept" Rule

Each test should verify ONE behavior. Multiple `expect` calls are fine if they all verify the SAME concept:

```typescript
// GOOD: One concept (user creation), multiple aspects
it('should create a user with all required fields', () => {
  const user = createUser({ name: 'Alice', email: 'a@b.com' });
  expect(user.name).toBe('Alice');
  expect(user.email).toBe('a@b.com');
  expect(user.id).toBeDefined();
  expect(user.createdAt).toBeInstanceOf(Date);
});

// BAD: Multiple concepts in one test
it('should create and validate and save user', () => {
  const user = createUser({ name: 'Alice' });
  expect(user.name).toBe('Alice');          // Creation
  expect(validateUser(user)).toBe(true);     // Validation (different concept)
  expect(saveUser(user)).resolves.toBe(true);// Persistence (different concept)
});
```

### Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| **Testing implementation details** | Test breaks when refactoring even though behavior is unchanged | Test the public API, not internal methods |
| **Brittle selectors (e2e)** | `.nav > ul > li:nth-child(3) > a` breaks on any DOM change | Use `data-testid` attributes |
| **Sleep-based waits (e2e)** | `await page.waitForTimeout(3000)` — flaky and slow | Use `page.waitForSelector()` or `expect(locator).toBeVisible()` |
| **Testing framework code** | Testing that React renders, that Express routes, that Vitest mocks | Test YOUR code, not the framework |
| **Copy-paste tests** | 20 tests that differ by one value | Use `it.each` or parameterized tests |
| **Snapshot overuse** | Large snapshot tests that nobody reads when they fail | Use targeted assertions instead; save snapshots for stable output |
| **Conditional logic in tests** | `if/else` in test body | Each branch should be a separate test |
| **Catching expected errors incorrectly** | `try { fn(); } catch (e) { expect(e)... }` | Use `expect(() => fn()).toThrow()` |

### Fixture Patterns

Use factory functions over raw data objects:

```typescript
// tests/fixtures/user-factory.ts
interface UserOverrides {
  name?: string;
  email?: string;
  role?: 'admin' | 'user';
}

export function createTestUser(overrides: UserOverrides = {}) {
  return {
    id: crypto.randomUUID(),
    name: overrides.name ?? 'Test User',
    email: overrides.email ?? `test-${Date.now()}@example.com`,
    role: overrides.role ?? 'user',
    createdAt: new Date(),
  };
}

// Usage in tests
it('should grant admin access', () => {
  const admin = createTestUser({ role: 'admin' });
  expect(hasAdminAccess(admin)).toBe(true);
});
```

Factories are better than raw objects because:
- Default values mean tests only specify what they care about
- Unique IDs/emails prevent collision between tests
- Single source of truth when the schema changes

---

## 3. Expected Output

### Primary Artifacts

| Artifact | Location | Convention |
|----------|----------|------------|
| Unit test files | `tests/unit/{module-name}.test.ts` | Mirror `src/` structure |
| E2E test files | `tests/e2e/{flow-name}.spec.ts` | Named by user flow, not component |
| Test fixtures | `tests/fixtures/` | Factory functions, shared test data |

### Unit Test File Template

```typescript
// tests/unit/{module-name}.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { functionUnderTest } from '../../src/{module-path}';

describe('functionUnderTest', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('when input is valid', () => {
    it('should return expected result', () => {
      const result = functionUnderTest(validInput);
      expect(result).toEqual(expectedOutput);
    });
  });

  describe('when input is invalid', () => {
    it('should throw a descriptive error', () => {
      expect(() => functionUnderTest(invalidInput))
        .toThrow('Expected error message');
    });
  });

  describe('edge cases', () => {
    it('should handle empty input', () => {
      const result = functionUnderTest('');
      expect(result).toEqual(emptyResult);
    });

    it('should handle null input', () => {
      expect(() => functionUnderTest(null))
        .toThrow('Input is required');
    });
  });
});
```

### E2E Test File Template

```typescript
// tests/e2e/{flow-name}.spec.ts
import { test, expect } from '@playwright/test';

test.describe('User Registration Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('should complete registration with valid data', async ({ page }) => {
    await page.getByTestId('name-input').fill('Alice Smith');
    await page.getByTestId('email-input').fill('alice@example.com');
    await page.getByTestId('password-input').fill('SecurePass123!');
    await page.getByTestId('submit-button').click();

    await expect(page.getByTestId('success-message')).toBeVisible();
    await expect(page).toHaveURL('/dashboard');
  });

  test('should show validation errors for invalid email', async ({ page }) => {
    await page.getByTestId('email-input').fill('not-an-email');
    await page.getByTestId('submit-button').click();

    await expect(page.getByTestId('email-error')).toContainText('Invalid email');
  });
});
```

### Test Report Summary

After running tests, produce a summary:

```
## Test Report

- Unit tests: 24 passed, 0 failed (0.8s)
- E2E tests: 3 passed, 0 failed (12.4s)
- Coverage: 87% lines, 82% branches

### New tests added: 8
- tests/unit/user-validation.test.ts (5 tests)
- tests/e2e/registration.spec.ts (3 tests)

### Coverage gaps:
- src/utils/date-format.ts: 0% (no tests exist)
- src/api/webhooks.ts: 45% (error paths untested)
```

---

## 4. Review / Rubric

### Test Coverage Criteria

| Criterion | Check | Severity |
|-----------|-------|----------|
| Happy path covered | At least one test for the main success scenario | BLOCKER |
| Error paths covered | At least one test per error/failure mode | WARNING |
| Boundary values tested | Min, max, and edge cases for ranged inputs | WARNING |
| No flaky tests | No `sleep`, no order dependencies, no time-sensitive logic without mocking | BLOCKER |
| Tests are readable as docs | Running `vitest --reporter=verbose` reads like a spec | WARNING |
| E2E tests use `data-testid` | No CSS class or DOM structure selectors | BLOCKER (e2e) |
| Each test is independent | No shared mutable state between tests | BLOCKER |
| Mocks are restored | `vi.restoreAllMocks()` in `beforeEach` or `afterEach` | WARNING |

### Test Quality Checklist

| Quality Signal | How to Check |
|---------------|-------------|
| Test names describe behavior, not implementation | Read test names without code — do they make sense? |
| No conditional logic in tests | Search for `if`, `else`, `switch` in test files |
| No duplicate test logic | Look for copy-pasted test bodies |
| Factories used over raw data | Check for inline object literals with many properties |
| Assertions are specific | `toBe`/`toEqual` preferred over `toBeTruthy` |
| Error messages are verified | `toThrow('specific message')` not just `toThrow()` |

### Anti-Pattern Detection

Run these checks before declaring tests complete:

```bash
# Check for sleeps in e2e tests
grep -r "waitForTimeout\|sleep\|setTimeout" tests/e2e/

# Check for implementation-detail testing
grep -r "\.state\.\|\.setState\|\.render\(\)" tests/unit/

# Check for brittle selectors in e2e
grep -r "nth-child\|:first\|:last\|\.class-name" tests/e2e/

# Check for missing mock cleanup
grep -L "restoreAllMocks\|resetAllMocks\|clearAllMocks" tests/unit/*.test.ts
```

---

## 5. Skill Definition (Orchestration)

### Sub-Tasks

**Step 1: Read acceptance criteria**
Read the task in `docs/plan.md` or the spec in `docs/specs/`. Extract every testable behavior. Number them (AC1, AC2, AC3...) for traceability.

**Step 2: Identify test type needed**
For each acceptance criterion, decide: unit test or e2e test?

| If the AC involves... | Test type | Reasoning |
|----------------------|-----------|-----------|
| A function returning a value | Unit | Pure logic, no browser needed |
| A component rendering correctly | Unit | Vitest + testing-library |
| Form validation logic | Unit | Pure logic |
| A complete user flow | E2E | Requires browser navigation |
| Visual appearance | E2E | Requires rendering in real browser |
| API integration with UI | E2E | Requires running server + browser |

**Step 3: Check existing test patterns**
Read 2-3 existing test files in `tests/` to learn:
- Import conventions
- Naming patterns
- Setup/teardown approach
- Mock patterns
- File organization
If no existing tests exist, use the templates from this skill.

**Step 4: Design test cases**
For each AC, design test cases covering:
- **Happy path:** The expected behavior when everything is correct
- **Error paths:** Each way the operation can fail
- **Boundary values:** Edge cases for inputs with ranges

Document the test design before writing code:
```
AC1: "User can register with valid email"
  - Happy: valid email → success
  - Error: invalid email → error message
  - Error: duplicate email → error message
  - Boundary: email at max length (254 chars) → success
  - Boundary: empty email → required error
```

**Step 5: Set up test fixtures**
Create or update factory functions in `tests/fixtures/` for any test data needed. Reuse existing factories when available. Each factory should produce valid data by default, with overrides for specific test scenarios.

**Step 6: Write unit tests with Vitest**
For each unit test case designed in Step 4:
1. Create the test file following naming convention: `tests/unit/{module-name}.test.ts`
2. Write the describe/it structure
3. Write assertions
4. Run the test to verify it behaves correctly

```bash
npx vitest run tests/unit/{test-file}.test.ts
```

**Step 7: Write e2e tests with Playwright (if needed)**
For each e2e test case designed in Step 4:
1. Create the test file: `tests/e2e/{flow-name}.spec.ts`
2. Use `data-testid` selectors exclusively
3. Use Playwright's built-in waiting (never `waitForTimeout`)
4. Keep each test focused on one flow

```bash
npx playwright test tests/e2e/{test-file}.spec.ts
```

**Step 8: Run all tests**
Run the complete test suite to catch regressions:

```bash
npx vitest run
npx playwright test
```

**Step 9: Fix any failures**
If tests fail:
- Read the error message carefully
- Determine if the failure is in the test or the source code
- If test is wrong, fix the test
- If source code has a bug, report it (tests reveal bugs — this is success, not failure)

**Step 10: Check coverage gaps**
Run coverage analysis to identify untested code:

```bash
npx vitest run --coverage
```

Review uncovered lines. Decide if they need tests:
- Critical logic without tests → write tests
- Generated code or boilerplate → acceptable gap
- Error handling without tests → write tests

**Step 11: Run anti-pattern detection**
Execute the anti-pattern checks from the rubric section. Fix any violations found.

**Step 12: Generate test report**
Produce the test report summary (format in Expected Output section). Include: test counts, pass/fail, coverage percentages, new tests added, gaps identified.

**Step 13: Flag untestable requirements**
If any acceptance criteria cannot be tested (e.g., "the UI should feel responsive", "the code should be clean"), flag them:

```
UNTESTABLE: AC5 "The dashboard should load quickly"
Suggestion: Rewrite as "Dashboard renders in under 2 seconds on 3G throttle"
```

---

## 6. HITL Build

### Agent Responsibilities (Autonomous)

- Reading acceptance criteria and designing test cases
- Writing all unit tests
- Writing all e2e tests
- Creating fixture factories
- Running tests and fixing test-level bugs
- Generating coverage reports
- Detecting anti-patterns

### Human Escalation Triggers

| Trigger | What to Present | Action |
|---------|----------------|--------|
| Acceptance criteria are untestable | Quote the AC, suggest testable rewording | STOP — wait for PM to clarify |
| Existing tests are flaky and blocking | Show the flaky test and its failure pattern | CONTINUE — document and flag |
| E2E infrastructure not set up | Playwright not installed or configured | STOP — request infrastructure setup |
| Source code has a bug revealed by tests | Show the failing test and the buggy code | CONTINUE — report bug, write the test anyway |
| Coverage is below project threshold | Show coverage report with gaps | CONTINUE — flag for review |
| Test requires real external service | E2e test needs live API, database, etc. | STOP — discuss mocking strategy vs. test environment |

### Agent Boundaries

- **DO:** Write tests, run tests, report results, create fixtures
- **DO NOT:** Modify source code to make tests pass (that's subagent-dev's job)
- **DO NOT:** Delete or skip existing tests
- **DO NOT:** Lower coverage thresholds
- **DO NOT:** Use `test.skip()` without documenting why and creating a follow-up task
- **DO NOT:** Write tests that depend on external services without mocking

---

## 7. HITL Review

### Review Level: NONE (tests are reviewed via code review)

Tests are committed alongside implementation code and reviewed as part of the PR review process. They do not require a separate review step.

### When Human Review IS Required

- First test file in the project (establishes conventions for all future tests)
- E2e test infrastructure setup (Playwright config, CI integration)
- Tests for security-critical features (auth, payments, data access)
- When test coverage drops below project threshold

### Presentation Format (when review is needed)

```
## Test Summary

### Tests Written
- Unit: {count} tests across {file_count} files
- E2E: {count} tests across {file_count} files

### Coverage Delta
- Before: {previous}% lines
- After: {current}% lines (+{delta}%)

### Test Design Decisions
- {Notable decision and rationale, e.g., "Mocked payment gateway because..."}

### Untestable Requirements
- {Any ACs that could not be tested, with suggested rewording}

### Anti-Pattern Check
- Sleeps: {0 found}
- Brittle selectors: {0 found}
- Missing mock cleanup: {0 found}
```

### CI Integration Notes

Tests should run in CI on every push. Expected configuration:

```yaml
# .github/workflows/test.yml (reference — not generated by this skill)
- name: Unit Tests
  run: npx vitest run --coverage

- name: E2E Tests
  run: npx playwright test
```

Unit tests run first (fast feedback). E2E tests run second (slower, higher confidence). If unit tests fail, e2e tests should not run (fail fast).
