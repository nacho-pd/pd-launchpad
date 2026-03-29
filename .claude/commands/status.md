# /status — Show Work Items from Supabase

Query and display work_items assigned to this repo.

## When to Use

- To see what tasks are pending, in progress, or completed.
- To check the current state of the delivery pipeline.
- At the start of a work session.

## Execution

1. Run: `python scripts/supabase_client.py list`
2. Display results in a formatted table.
3. Highlight any items with status `blocked` or `needs_review`.

## Output Format

```
## Work Items — [repo-name]

| Status          | Count |
|-----------------|-------|
| pending         | X     |
| in_progress     | X     |
| needs_review    | X     |
| deployed        | X     |

### Active Items
| ID | Title | Status | Priority | Assigned |
|----|-------|--------|----------|----------|
| ...| ...   | ...    | ...      | ...      |

### Blocked Items (if any)
| ID | Title | Blocker Reason |
|----|-------|----------------|
```

## Options

- `/status --pending` — Show only pending items.
- `/status --mine` — Show items assigned to current agent.
- `/status [work_item_id]` — Show details for a specific item.
