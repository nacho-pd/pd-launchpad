## Rule: Spec Compliance

Every line of code must trace back to a spec requirement. If it's not in the spec, don't build it.

### How to Apply

1. Before writing code, identify which spec requirement it satisfies.
2. If a requirement is ambiguous, flag it — don't interpret creatively.
3. If you discover a needed feature not in the spec, stop and create a work_item for it.

### Scope Creep Signals

- "While I'm here, I might as well..." — Stop. Is it in the spec?
- "This would be a nice improvement..." — Stop. Is it in the spec?
- "The user will probably also want..." — Stop. Is it in the spec?

### If You're Tempted to Skip

Open the spec. Find the requirement. If it's not there, don't build it. Create a work_item instead and let the PM decide.
