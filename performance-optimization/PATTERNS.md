# Common Performance Bottleneck Patterns

## Pattern 1: N+1 Query Problem

**Symptoms:**
- Database operations scale linearly with data size
- Logs show many similar queries
- Each loop iteration makes a DB call

**Before (N+1 queries):**
```python
for item_id in item_ids:
    item = db.get_item(item_id)      # Query per item!
    related = db.get_related(item_id) # Another query per item!
    process(item, related)
```

**After (2 queries):**
```python
# Fetch all items in single query
items_map = db.get_items_by_ids(item_ids)
related_map = db.get_related_by_ids(item_ids)

for item_id in item_ids:
    item = items_map.get(item_id)
    related = related_map.get(item_id, [])
    process(item, related)
```

**Implementation:**
```python
def get_items_by_ids(self, ids: list[int]) -> dict[int, Item]:
    """Fetch multiple items in single query."""
    if not ids:
        return {}
    items = session.query(Item).filter(Item.id.in_(ids)).all()
    return {item.id: item for item in items}
```

---

## Pattern 2: O(n) Scan Instead of O(1) Lookup

**Symptoms:**
- Linear search through lists/arrays
- Searching for matches by iterating

**Before (O(n) per lookup):**
```python
def find_order(orders: list[Order], amount: int) -> Order | None:
    for order in orders:  # Scans all orders every time
        if order.amount == amount:
            return order
    return None
```

**After (O(1) lookup with index):**
```python
class OrderAmountIndex:
    def __init__(self, orders: list[Order]):
        self._by_amount: dict[int, list[Order]] = {}
        for order in orders:
            bucket = order.amount // 100  # Group by dollar
            self._by_amount.setdefault(bucket, []).append(order)

    def get_candidates(self, amount: int, tolerance: int) -> list[Order]:
        """O(1) lookup of candidate orders."""
        bucket = amount // 100
        candidates = []
        for b in range(bucket - 1, bucket + 2):
            candidates.extend(self._by_amount.get(b, []))
        return candidates
```

---

## Pattern 3: Per-Item Inserts Instead of Bulk

**Symptoms:**
- Loop with individual INSERT statements
- Transaction overhead multiplied by item count

**Before (N inserts):**
```python
for data in items_to_insert:
    item = Item(**data)
    session.add(item)
    session.flush()  # Forces DB round-trip each time
```

**After (1 bulk insert):**
```python
items = [Item(**data) for data in items_to_insert]
session.add_all(items)
session.flush()  # Single DB round-trip
```

**With related entity resolution:**
```python
def bulk_insert(self, data_list: list[dict]) -> list[int]:
    """Bulk insert with efficient foreign key resolution."""
    if not data_list:
        return []

    # Step 1: Collect unique foreign keys needed
    unique_keys = {d["foreign_key"] for d in data_list if d.get("foreign_key")}

    # Step 2: Fetch existing related entities in single query
    existing = session.query(Related).filter(Related.key.in_(unique_keys)).all()
    key_to_id = {r.key: r.id for r in existing}

    # Step 3: Create missing related entities in batch
    missing_keys = unique_keys - set(key_to_id.keys())
    if missing_keys:
        new_related = [Related(key=k) for k in missing_keys]
        session.add_all(new_related)
        session.flush()
        for r in new_related:
            key_to_id[r.key] = r.id

    # Step 4: Create all items with resolved foreign keys
    items = []
    for data in data_list:
        fk = data.get("foreign_key")
        items.append(Item(
            **data,
            related_id=key_to_id.get(fk) if fk else None
        ))

    session.add_all(items)
    session.flush()
    return [item.id for item in items]
```

---

## Pattern 4: Expensive Diagnostic Logging

**Symptoms:**
- Debug/diagnostic code runs even in production
- Expensive operations "just for logging"

**Before (always runs expensive scan):**
```python
def find_match(item, candidates):
    for c in candidates:
        if matches(item, c):
            return c

    # Expensive diagnostic scan runs EVERY time no match found
    near_misses = []
    for c in all_items:  # O(n) scan
        if is_close(item, c):
            near_misses.append(c)
    logger.info(f"Near misses: {near_misses}")

    return None
```

**After (skip expensive diagnostics in hot path):**
```python
def find_match(item, candidates, *, skip_diagnostics: bool = False):
    for c in candidates:
        if matches(item, c):
            return c

    # Skip expensive diagnostics during bulk operations
    if skip_diagnostics:
        return None

    # Only run diagnostics when explicitly requested
    near_misses = []
    for c in all_items:
        if is_close(item, c):
            near_misses.append(c)
    logger.info(f"Near misses: {near_misses}")

    return None
```

---

## Pattern 5: Sequential Operations That Could Be Batched

**Symptoms:**
- Multiple independent DB operations in sequence
- Each operation waits for previous to complete

**Before (3 sequential operations):**
```python
items = db.get_items(ids)           # Wait...
related = db.get_related(ids)       # Wait...
metadata = db.get_metadata(ids)     # Wait...
```

**After (operations combined or parallelized):**
```python
# Option A: Single query with joins
results = db.get_items_with_related_and_metadata(ids)

# Option B: Parallel fetches (if independent)
import asyncio

async def fetch_all(ids):
    items, related, metadata = await asyncio.gather(
        db.get_items_async(ids),
        db.get_related_async(ids),
        db.get_metadata_async(ids),
    )
    return items, related, metadata
```

---

## Pattern 6: Repeated Computation in Loop

**Symptoms:**
- Same calculation performed multiple times
- Expensive operation inside inner loop

**Before (repeated computation):**
```python
for item in items:
    config = load_config()  # Same config loaded every iteration!
    settings = parse_settings(config)  # Same parsing every time!
    process(item, settings)
```

**After (hoist out of loop):**
```python
config = load_config()  # Load once
settings = parse_settings(config)  # Parse once

for item in items:
    process(item, settings)
```

---

## Anti-Pattern: Premature Parallelization

**Don't parallelize before fixing algorithmic issues.**

If your code is O(n²), parallelizing across 8 cores gives you O(n²/8) - still quadratic.
Fix the algorithm first, then consider parallelization if still needed.

**Decision tree:**
```
Is it I/O bound? → Batch/reduce round-trips first
Is it CPU bound with bad algorithm? → Fix algorithm first
Is it CPU bound with good algorithm? → Consider parallelization
```

---

## Measuring Impact

After applying any pattern, measure the improvement:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total time | X ms | Y ms | (X-Y)/X % |
| DB queries | N | M | N/M x faster |
| Memory | X MB | Y MB | (X-Y)/X % |

Always verify tests still pass after optimization.
