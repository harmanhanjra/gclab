# GClab - Verified Tracing Garbage Collector

## Threat Model

### Assets
- Object graph integrity (no dangling pointers)
- Memory safety (no use-after-free)
- Collection correctness (no memory leaks)

### Threats
1. **Invalid pointers**: Malformed graph structure
   - Mitigation: Input validation in add_strong/add_weak
2. **Cycle corruption**: Weakref cycles with dangling pointers
   - Mitigation: Cycle detection with proper weakref handling
3. **Buffer overflow**: Write barrier buffer overflow
   - Mitigation: Fixed buffer size, automatic flush

### Assumptions
- Single-threaded execution (no concurrency)
- All pointers are valid at time of creation
- No external modification of object graph during GC

### Security Measures
- All object IDs validated before use
- Buffer sizes bounded by config constants
- No eval, subprocess, or file I/O in core GC logic
- Deterministic behavior with seeded RNG
