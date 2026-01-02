# Performance Optimization Checklists

## Pre-Optimization Checklist

Complete these steps BEFORE making any performance changes:

```
Pre-Optimization:
- [ ] Tests exist that verify correctness of code being optimized
- [ ] All existing tests pass
- [ ] Baseline performance measured with specific metrics
- [ ] Bottleneck identified through profiling (not guessing)
- [ ] Root cause understood (complexity class identified)
- [ ] Solution approach decided
```

### Test Coverage Questions

Before optimizing, ask:

1. **Are there unit tests for this code?**
   - If NO: Write tests first or ask user for permission to proceed
   - If YES: Run them to confirm they pass

2. **Do tests cover the hot path being optimized?**
   - If NO: Add tests for the specific code path
   - If YES: These become your correctness invariants

3. **Are there integration tests that exercise the full flow?**
   - If NO: Consider adding at least one end-to-end test
   - If YES: Run after each optimization

### Profiling Checklist

```
Profiling:
- [ ] Identified which operation is slow (not assumed)
- [ ] Measured time spent in each phase/component
- [ ] Counted DB queries (look for N+1)
- [ ] Identified algorithmic complexity
- [ ] Documented baseline metrics
```

**Questions to answer:**
- How long does the operation take? (ms/s)
- How many DB queries are executed?
- How does time scale with data size? (O(n)? O(n²)?)
- What percentage of time is I/O vs CPU?

---

## Per-Optimization Checklist

For EACH optimization change:

```
Optimization #___:
- [ ] Single, focused change (not combined with others)
- [ ] Tests still pass after change
- [ ] Performance improved as expected
- [ ] Code remains readable/maintainable
- [ ] Change committed with descriptive message
```

### Commit Template

```
perf: <brief description> (<before metric> → <after metric>)

<What was changed>
<Why it improves performance>
<Measured improvement>
```

---

## Post-Optimization Checklist

After completing all optimizations:

```
Post-Optimization:
- [ ] All tests pass
- [ ] Performance meets requirements
- [ ] No regressions in other areas
- [ ] Changes are documented
- [ ] Code reviewed (if applicable)
```

### Final Verification

1. **Run full test suite**
   ```bash
   pytest -q  # All tests should pass
   ```

2. **Re-measure performance**
   - Compare against baseline
   - Document improvement

3. **Check for regressions**
   - Memory usage still acceptable?
   - Other operations still fast?
   - Edge cases still handled?

---

## Decision Checklist: Should I Optimize?

Before starting optimization work:

```
Should I Optimize?
- [ ] Performance is actually a problem (not premature optimization)
- [ ] User has reported slowness OR metrics show issue
- [ ] I know WHERE the time is being spent
- [ ] The optimization is worth the complexity cost
```

### When NOT to Optimize

- "It might be slow someday" (premature)
- "This looks inefficient" (without measurement)
- "I can make this faster" (without need)
- Tests don't exist and user doesn't want them written

### When to Stop Optimizing

- [ ] Target performance achieved
- [ ] Bottleneck has moved elsewhere
- [ ] Remaining gains are marginal
- [ ] Additional optimization adds significant complexity
- [ ] Parallelization is "last resort" territory

---

## Quick Reference: Common Fixes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Time scales with N | N+1 queries | Batch fetch |
| Time scales with N² | Nested loops | Add index/hash map |
| Many similar DB queries | Per-item queries | Single bulk query |
| Many INSERT statements | Per-item inserts | Bulk insert |
| Expensive debug logging | Diagnostic in hot path | Skip in bulk mode |
