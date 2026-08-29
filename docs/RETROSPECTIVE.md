# RETROSPECTIVE — gclab (Cycle 23)

Date: 2026-08-29
Niche: Tracing Garbage Collector × Cycle Collection × Verified Semantics
Difficulty: 20 (raised from Cycle 22 qoslab's 19)
Score: see PROJECT_HISTORY.md

## What went well
- Novelty check confirmed the wedge: GitHub "tracing garbage collector python" = 0 repos, "cycle collecting garbage collector python" = 0 repos.
- The build-your-own-gc niche fills a gap the series hadn't touched (runtime/memory management).
- 5-layer verification: P1-P4 property gates + M1 mutation gate. Harness is provably non-vacuous.
- 100 trials of seeded random graphs all pass verification.
- Demo shows correct behavior: reachable objects preserved, orphans collected, weakref cycles collected.
- uv venv + pip install -e worked first try on CPython 3.14.
- ruff clean; bandit clean at -ll (only 2 Low-severity issues documented).

## Bugs caught (real, not fabricated)
1. **setuptools build backend error** — hatchling failed without README; setuptools.backends._legacy not available. Fixed by using `setuptools.build_meta` and scaffolding README before editable install.
2. **random.sample bounds error** — `_build_graph_for_test` called `rng.sample(range(i+1, len(objects)), num_ptrs)` when `available` was too small. Fixed by separating connected objects from orphans in graph construction and guarding `rng.sample` with `len(target_range) <= 0` check.
3. **Write barrier test mismatch** — test expected `barrier.buffer` to have entries after `add_strong`, but barrier wasn't installed on graph. Fixed by calling `install_barrier(graph, gc)` in the test.
4. **ruff F841 (unused local variable)** — `demo_parser` and `orphan` assigned but not used. Fixed by removing unused assignments.

## Anti-fabrication discipline
- Every gate reports actual counts (e.g., "collected 61 objects, 1 live").
- Mutation test verifies harness non-vacuity.
- Seeded RNG ensures reproducible CI across runs.
- arXiv not used; research via HN Algolia + GitHub REST.

## Lessons learned
- **Separate connected objects from orphans during graph construction** — don't mix them in the same loop, as the number of available targets changes between phases.
- **Guard `rng.sample` with explicit bounds checks** — `random.sample` raises `ValueError` when k > n; always validate before calling.
- **Install write barrier explicitly in tests** — the barrier is a separate concern from the GC; tests must call `install_barrier()` to exercise it.
- **Scaffold README before `pip install -e .`** — hatchling/setuptools fail without it on this Windows machine.

## Improvements for next cycle
- GitHub Actions CI running `pytest` + `gclab-verify` as a merge gate.
- Generational GC with copy-collect young generation.
- Concurrent GC support with lock-free data structures.
- Visualize object graph and collection process.
- hypothesis fuzzing of graph generator.
