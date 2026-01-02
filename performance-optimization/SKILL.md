---
name: optimizing-performance
description: Systematically diagnose and fix performance bottlenecks in code. Use when the user reports slow operations, asks to speed up code, mentions performance issues, or when logs/profiling data shows unexpectedly long execution times.
---

# Performance Optimization

Systematic approach to diagnosing and fixing performance bottlenecks.

## Quick Start

**Before optimizing anything:**

1. **Establish test coverage** - Ensure unit tests exist that verify correctness
2. **Measure first** - Profile to identify actual bottlenecks
3. **Optimize incrementally** - One change at a time, test after each

## The Optimization Process

### Phase 1: Establish Invariants

Before any optimization, confirm tests exist that verify correctness:

```bash
# Run existing tests to establish baseline
pytest -q  # or equivalent test command
```

If tests don't exist for the code being optimized:
1. **Stop** - Ask the user if you should write tests first
2. Create tests that capture current correct behavior
3. These tests become invariants that must pass after optimization

### Phase 2: Measure and Profile

**Never optimize without data.** Identify WHERE time is spent:

```python
import time

start = time.monotonic()
# ... operation ...
elapsed_ms = (time.monotonic() - start) * 1000
print(f"Operation took {elapsed_ms:.1f}ms")
```

For database operations, count queries:
- Log each query or use ORM query logging
- Look for N+1 patterns (queries scaling with data size)

**Key question**: What is the algorithmic complexity?
- O(1) - constant time
- O(n) - linear (acceptable for most cases)
- O(n²) - quadratic (usually the problem)
- O(n) repeated n times = O(n²) (N+1 query pattern)

### Phase 3: Identify Root Cause

See [PATTERNS.md](PATTERNS.md) for common bottleneck patterns:
- N+1 queries (most common in database code)
- O(n) scans that could be O(1) with indexing
- Per-item operations that could be batched
- Synchronous operations that could be parallel

### Phase 4: Implement Fix

1. **One optimization at a time** - Don't combine multiple changes
2. **Run tests after each change** - Verify correctness preserved
3. **Commit after each successful optimization** - Enable easy rollback

```bash
# After each optimization:
pytest -q                    # Verify tests pass
git add -A && git commit -m "perf: <description of optimization>"
```

### Phase 5: Verify Improvement

Re-run the same measurement from Phase 2:
- Did the metric improve as expected?
- Are all tests still passing?
- Is the code still readable/maintainable?

### Phase 6: Know When to Stop

Stop optimizing when:
- The bottleneck has shifted elsewhere
- Remaining gains are marginal vs. complexity added
- You've achieved acceptable performance

**Parallelization is usually last resort** - fix algorithmic issues first.

## Optimization Decision Tree

```
Is it slow?
├── No → Don't optimize
└── Yes → Do tests exist?
    ├── No → Write tests first (or ask user)
    └── Yes → Profile to find bottleneck
        └── Is it I/O bound? (DB, network, disk)
            ├── Yes → Batch operations, reduce round-trips
            └── No → Is it O(n²) or worse?
                ├── Yes → Add index, change algorithm
                └── No → Consider caching or parallelization
```

## Commit Message Format

Use conventional commits for optimization changes:

```
perf: <short description> (<before> → <after>)

<Longer explanation of what was changed and why>
```

Examples:
- `perf: Batch DB reads (N queries → 2 queries)`
- `perf: Add amount index for O(1) lookup`
- `perf: Bulk insert transactions (N inserts → 1)`

## Detailed Resources

- [PATTERNS.md](PATTERNS.md) - Common bottleneck patterns and fixes
- [CHECKLIST.md](CHECKLIST.md) - Pre-optimization and post-optimization checklists
