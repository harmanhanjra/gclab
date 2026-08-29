# GClab — Verified Tracing Garbage Collector with Cycle Collection

A from-scratch tracing garbage collector with verified semantics, including cycle collection and write-barrier correctness. Built as a Python library with a `gclab-verify` CI gate.

## What this is
A graph-based heap simulator with a tracing GC that proves three invariants:
1. **Reachability**: every live root can reach its live objects
2. **No dangles**: all pointers to collected objects are nullified
3. **Cycle detection**: weakref cycles are correctly reclaimed

## Quickstart

```bash
uv venv .venv
uv pip install -e ".[test]" --python .venv
.venv/Scripts/python -m pytest tests -q
.venv/Scripts/python -m gclab verify
```

## CLI

```
gclab verify          # Run verification harness (CI exit-code gate)
gclab demo            # Run a live demo with mutation schedule
```

## Architecture

- `heap.py` — Object graph with typed strong/weak pointers
- `gc.py` — Tracing collector (mark-sweep + cycle collection)
- `barrier.py` — Buffered write-barrier
- `verify.py` — Seeded property gates + mutation tests

## Security

Fully offline, zero deps, no network/subprocess/eval/file I/O. All inputs validated.
