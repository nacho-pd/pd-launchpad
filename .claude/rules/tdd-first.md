## Rule: TDD First

Write tests before implementation. Always.

### The Protocol

1. **RED** — Write a failing test that defines the expected behavior.
2. **GREEN** — Write the minimum code to make the test pass.
3. **REFACTOR** — Clean up without changing behavior. Tests must still pass.

### Why This Matters

Code without tests is a liability. Tests written after the fact confirm what you built, not what you should have built. TDD forces you to think about the interface before the implementation.

### If You're Tempted to Skip

- "This is too simple to test" — Simple code becomes complex code. Write the test.
- "I'll add tests later" — You won't. Write the test now.
- "The test is hard to write" — That means the design needs work. Simplify the interface.
- **Never delete a test to make CI pass.** Fix the code instead.
