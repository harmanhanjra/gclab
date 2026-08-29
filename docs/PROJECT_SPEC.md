# GClab - Project Specification

## Problem

Garbage collection is fundamental to managed languages, but educational implementations
rarely prove correctness. This project implements a tracing GC with formal verification.

## Solution

A from-scratch tracing garbage collector with:
1. Graph-based object model with strong/weak pointers
2. BFS reachability traversal (mark phase)
3. Cycle detection for weakref cycles
4. Buffered write barrier for mutation tracking
5. Formal verification harness (P1-P4 + M)

## Non-Goals

- Integration with actual Python runtime
- Concurrent GC
- Generational collection
- Real-time GC
