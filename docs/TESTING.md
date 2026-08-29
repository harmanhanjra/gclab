# GClab - Testing Strategy

## Test Layers

1. **Unit tests**: Individual component testing
   - ObjectGraph: allocation, pointer operations, validation
   - TracingGC: mark, sweep, cycle detection
   - WriteBarrier: buffer management

2. **Property tests**: Formal verification
   - P1: Reachability (all reachable objects are marked)
   - P2: No dangles (live objects only point to live objects)
   - P3: Cycle collection (weakref cycles are collected)
   - P4: Live objects marked (no false positives in sweep)

3. **Mutation tests**: Verify harness is non-vacuous
   - M: Broken collector should fail properties

4. **Integration tests**: Full harness execution
   - Seeded reproducibility
   - Multiple trials

## Test Data

- Random graphs with varying density
- Weakref cycles of different sizes
- Mixed strong/weak pointer scenarios
- Unreachable objects (orphans)
