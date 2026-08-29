# Why This Project

## Motivation

Garbage collection is taught in computer science, but implementations are rarely verified.
This project fills the gap by providing a from-scratch tracing GC with formal correctness
guarantees.

## Value

1. **Educational**: Demonstrates GC internals with verified correctness
2. **Research**: Provides a testbed for GC algorithm experimentation
3. **Verification**: Proves invariants that real GCs rely on

## Differentiation

Unlike toy GC implementations, this project:
- Provides formal verification gates (not just unit tests)
- Handles cycle collection explicitly
- Includes write barrier for mutation tracking
- Has mutation testing to prove harness non-vacuity
