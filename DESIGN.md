# DESIGN: Triage Queue

## 1) Data Structure Choice

### Selected structure
The queue uses `heapq` with entries shaped as:

- `(triage_level, arrived_at, monotonic_counter, patient)`

Priority is naturally enforced because lower tuple values are popped first.

1. `triage_level` ensures `1` before `2` before `3`.
2. `arrived_at` ensures older patients in the same level are attended first.
3. `monotonic_counter` preserves deterministic FIFO when timestamps are equal.

### Why this structure
Compared to a single sorted list:

- Sorted list insertion is `O(n)` (must shift elements).
- Heap insertion and extraction are both `O(log n)`.

Compared to multi-`deque` by level:

- Multi-`deque` gives `O(1)` enqueue/dequeue when arrivals are always appended in true order.
- Heap is more robust when `arrived_at` can be supplied externally or ties occur, because global ordering remains correct without manual reordering.

### Complexity summary

- `enqueue`: `O(log n)`
- `dequeue`: `O(log n)`
- `peek`: `O(1)`
- `list_queue`: `O(n log n)` (sorted snapshot)
- `stats`: `O(1)` using maintained counters

## 2) Concurrency and Race Conditions

Current implementation is in-memory and single-process. If multiple workers are introduced, queue mutation must be synchronized.

### Risks

- Two workers dequeue at the same time and both try to process the same top patient.
- One worker reads queue state while another mutates heap internals.
- Stats become inconsistent if enqueue/dequeue updates are not atomic.

### Mitigation strategy

Use a lock around every state mutation and every read that must be strongly consistent:

1. Acquire lock.
2. Validate preconditions (for example, queue not empty).
3. Mutate both heap and counters in one critical section.
4. Release lock.

In Python, `threading.Lock` (or `RLock`) can protect `enqueue`, `dequeue`, `peek`, `stats`, and snapshot building for `list_queue`.

For multi-process or distributed workers, move the queue to a shared durable backend (for example, Redis sorted sets or a database with row-level locking and transactions), then use atomic pop/claim semantics to prevent double processing.
