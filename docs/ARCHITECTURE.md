# GClab - Verified Tracing Garbage Collector

## Architecture

### Components

1. **ObjectGraph**: Manages the heap object graph
   - Typed pointers (strong/weak)
   - Object allocation and ID management
   - Pointer validation

2. **TracingGC**: The garbage collector
   - Mark phase: BFS traversal from roots
   - Cycle detection: Weakref cycle identification
   - Sweep phase: Collect unmarked objects

3. **WriteBarrier**: Buffered write barrier
   - Tracks pointer mutations
   - Automatic flushing

4. **Verify**: Verification harness
   - Property gates (P1-P4)
   - Mutation tests (M)
   - Seeded reproducibility

### Data Flow

```
ObjectGraph.alloc() → HeapObject
     ↓
ObjectGraph.add_strong/add_weak → WriteBarrier.on_write
     ↓
TracingGC.collect_garbage(roots)
     ↓
  ┌─ Mark phase (BFS from roots)
  ├─ Cycle detection (weakref graph)
  └─ Sweep phase (collect unmarked)
     ↓
  Verify properties
```

### Design Decisions

1. **Graph-based model**: Explicit object graph for deterministic testing
2. **Write barrier**: Buffered approach for mutation tracking
3. **Cycle detection**: Separate from mark phase for clarity
4. **Property-based verification**: Formal correctness guarantees
