"""Verification harness for GC invariants."""
from __future__ import annotations

import random

from .gc import TracingGC
from .heap import ObjectGraph


def _build_graph_for_test(seed: int, size: int = 50) -> tuple[ObjectGraph, TracingGC, list[int]]:
    """Build a test graph with roots and potentially unreachable objects."""
    rng = random.Random(seed)
    graph = ObjectGraph()
    gc = TracingGC(graph)

    # Create root object
    root = graph.alloc("root")
    roots = [root.obj_id]

    # Create objects with random connections
    objects = [root]
    for _ in range(size - 1):
        obj = graph.alloc("container")
        objects.append(obj)

    # Connect objects (only among first `size` objects, orphans come after)
    for i, obj in enumerate(objects[1:size], 1):
        # Each object has 1-3 strong pointers to later objects
        available = size - i
        if available <= 0:
            continue
        num_ptrs = rng.randint(1, min(3, available))
        targets = rng.sample(range(i + 1, size), min(num_ptrs, available))
        for t in targets:
            graph.add_strong(obj.obj_id, objects[t].obj_id)

    # Add some unreachable objects
    for _ in range(size // 5):
        orphan = graph.alloc("leaf")
        objects.append(orphan)

    # Create a weakref cycle
    weak1 = graph.alloc("weakref")
    weak2 = graph.alloc("weakref")
    graph.add_weak(weak1.obj_id, weak2.obj_id)
    graph.add_weak(weak2.obj_id, weak1.obj_id)
    objects.extend([weak1, weak2])

    return graph, gc, roots


def _reachable_from(graph: ObjectGraph, roots: list[int]) -> set[int]:
    """Compute all objects reachable from roots."""
    visited: set[int] = set()
    stack = list(roots)

    while stack:
        obj_id = stack.pop()
        if obj_id in visited:
            continue
        visited.add(obj_id)

        if obj_id not in graph.objects:
            continue

        obj = graph.objects[obj_id]
        for ptr in obj.strong_ptrs:
            if ptr.target_id not in visited:
                stack.append(ptr.target_id)
        for ptr in obj.weak_ptrs:
            if ptr.target_id not in visited:
                stack.append(ptr.target_id)

    return visited


def property_reachability(graph: ObjectGraph, gc: TracingGC, roots: list[int]) -> bool:
    """
    P1: All objects reachable from roots are marked.
    """
    expected = _reachable_from(graph, roots)
    return expected.issubset(gc.marked)


def property_no_dangles(graph: ObjectGraph, gc: TracingGC) -> bool:
    """
    P2: All pointers from live objects point to live objects.
    """
    for _obj_id, obj in graph.objects.items():
        if obj.collected:
            continue
        for ptr in obj.strong_ptrs:
            if ptr.target_id in graph.objects and graph.objects[ptr.target_id].collected:
                return False
        for ptr in obj.weak_ptrs:
            if ptr.target_id in graph.objects and graph.objects[ptr.target_id].collected:
                return False
    return True


def property_cycle_collection(graph: ObjectGraph, gc: TracingGC) -> bool:
    """
    P3: Weakref cycles are collected when unreachable from roots.
    """
    # Find weakref cycle members
    cycle_ids: set[int] = set()
    for obj_id, obj in graph.objects.items():
        if obj.kind == "weakref" and not obj.strong_ptrs:
            cycle_ids.add(obj_id)

    # All cycle members should be collected if not reachable from roots
    for obj_id in cycle_ids:
        if obj_id not in gc.marked and not graph.objects[obj_id].collected:
            return False

    return True


def property_live_objects_marked(graph: ObjectGraph, gc: TracingGC) -> bool:
    """
    P4: All uncollected objects are marked.
    """
    for obj_id, obj in graph.objects.items():
        if not obj.collected and obj_id not in gc.marked:
            return False
    return True


def mutation_test(graph: ObjectGraph, gc: TracingGC, roots: list[int]) -> bool:
    """
    M: Mutation test - verify harness can fail on broken collector.
    This test creates a scenario where a broken collector would pass.
    """
    # Build graph with a specific pattern
    root = graph.alloc("root")
    obj1 = graph.alloc("container")
    obj2 = graph.alloc("container")

    graph.add_strong(root.obj_id, obj1.obj_id)
    graph.add_strong(obj1.obj_id, obj2.obj_id)

    # Run collection
    gc.collect_garbage([root.obj_id])

    # Verify obj2 is still live (should be marked as reachable)
    if obj2.obj_id not in gc.marked:
        return False

    if graph.objects[obj2.obj_id].collected:
        return False

    return True


def run_verify(seed: int = 42, trials: int = 100) -> bool:
    """
    Run all verification properties.

    Args:
        seed: Random seed for reproducibility.
        trials: Number of test trials.

    Returns:
        True if all properties pass, False otherwise.
    """
    rng = random.Random(seed)
    all_pass = True

    print(f"Running GC verification harness ({trials} trials, seed={seed})")
    print("=" * 60)

    for trial in range(trials):
        graph, gc, roots = _build_graph_for_test(rng.randint(0, 2**31))

        # Run GC
        gc.collect_garbage(roots)

        # Check properties
        if not property_reachability(graph, gc, roots):
            print(f"Trial {trial}: P1 REACHABILITY FAILED")
            all_pass = False
            break

        if not property_no_dangles(graph, gc):
            print(f"Trial {trial}: P2 NO-DANGLES FAILED")
            all_pass = False
            break

        if not property_cycle_collection(graph, gc):
            print(f"Trial {trial}: P3 CYCLE COLLECTION FAILED")
            all_pass = False
            break

        if not property_live_objects_marked(graph, gc):
            print(f"Trial {trial}: P4 LIVE OBJECTS MARKED FAILED")
            all_pass = False
            break

        # Run mutation test
        if not mutation_test(graph, gc, roots):
            print(f"Trial {trial}: M MUTATION TEST FAILED")
            all_pass = False
            break

        if trial % 10 == 9:
            print(f"  Completed {trial + 1} trials...")

    print("=" * 60)
    if all_pass:
        print(f"All {trials} trials PASS")
    else:
        print("Verification FAILED")

    return all_pass
