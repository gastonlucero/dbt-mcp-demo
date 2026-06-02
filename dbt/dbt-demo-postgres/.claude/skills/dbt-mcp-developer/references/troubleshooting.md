# Quick Troubleshooting

## Getting Help (Start Here)

If stuck:

1. **Show the error** to agent (copy-paste exact message)
2. **Describe what you expected** vs. what happened
3. **Ask for specific fix**: "Fix this SQL", "Add an intermediate layer", "Update the test"

Agent will debug and iterate.

---

## Common Issues

### Issue: `dbt compile` Fails

**Show:** Error message to agent  
**Solution:** Agent fixes SQL and recompiles  
**Time:** 1-2 iterations

Example: `column "fire_month" does not exist` → Agent should use `extract(year-month from data_hora_gmt) as fire_month`

### Issue: `dbt test` Fails

**Show:** Failed test name and error  
**Solutions:**

- Fix SQL to exclude nulls: `where fire_count is not null`
- Remove test if nulls are valid
- Update test logic

Agent fixes and retests.

### Issue: Agent Doesn't Run `explain_query`

**Ask:** "Validate SQL performance with explain_query"  
**Agent will:** Run it and report findings  
**You decide:** Apply optimization or proceed

### Issue: Agent Skips a Layer

**Problem:** Should be stg→int→fct but generated stg→fct  
**Ask:** "This needs an intermediate layer to handle the join"  
**Agent:** Redesigns and regenerates

### Issue: Files in Wrong Directory

**Expected:** `models/marts/fires/fct_*.sql`  
**Got:** `models/fires/fct_*.sql`  
**Ask:** "Put fact tables in models/marts/fires/"  
**Agent:** Moves files

### Issue: Acceptance Test Wrong

**Example:** Test should verify "≤10 rows" but verifies "1-1000 rows"  
**Ask:** "Test should verify exactly 10 or fewer rows"  
**Agent:** Updates test

### Issue: Too Many/Few Layers

**Simple request got 3 layers:** "Can we do stg → fct instead?"  
**Complex request got 2 layers:** "Add intermediate for the join logic"  
**Agent:** Redesigns

### Issue: Table Not Found

**Check:**

1. Is it `schema.table` or just `table`?
2. Does table exist? (check database)
3. Provide full path: `raw_data.monthly_fires`

**If MCP available:** Agent runs `list_tables`  
**If MCP unavailable:** You provide exact name

### Issue: Query Returns 0 Rows

**Ask agent:** "Why is it empty?"  
**Agent checks:** Source data, filter logic, joins  
**Then fixes:** Date range, conditions, joins

---

## When MCP is Unavailable

See `references/mcp-integration.md` for full details.

**Quick:** Provide table name, columns, row count. Agent continues normally. Skip `explain_query` (you run `dbt compile` locally).

---

## Edge Cases

| Case | What to do |
|------|-----------|
| Table has 100M+ rows, slow | Agent reports via explain_query; discuss optimization (indexes, partitions, incremental) |
| Multiple tables match | Agent asks "which is source of truth?"; you clarify |
| Model with 0 rows | Ask agent why; fix filter logic, date range, or joins |
| Models already exist | Agent asks "overwrite or rename?"; you decide |
