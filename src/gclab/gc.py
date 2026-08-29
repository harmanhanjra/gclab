"""Tracing garbage collector with cycle collection."""
from __future__ import annotations

import logging
from collections import deque
from typing import Optional

from .heap import ObjectGraph

logger = logging.getLogger(__name__)


class WriteBarrier:
    """Buffered write barrier for tracking object mutations."""

    def __init__(self, buffer_size: int = 1000) -> None:
        self.buffer: list[tuple[int, int]] = []
        self.buffer_size = buffer_size

    def on_write(self, from_id: int, to_id: int) -> None:
        """Record a pointer write."""
        if len(self.buffer) >= self.buffer_size:
            self.flush()
        self.buffer.append((from_id, to_id))

    def flush(self) -> None:
        """Clear the write buffer."""
        self.buffer.clear()


class TracingGC:
    """
    Tracing garbage collector with cycle collection.

    Uses a mark-sweep algorithm with:
    - BFS reachability traversal (mark phase)
    - Cycle detection for weakref cycles
    - Write barrier for tracking mutations
    """

    def __init__(self, graph: ObjectGraph, barrier: Optional[WriteBarrier] = None) -> None:
        self.graph = graph
        self.barrier = barrier or WriteBarrier()
        self.marked: set[int] = set()
        self.gray: set[int] = set()  # For cycle detection
        self.black: set[int] = set()

    def collect_garbage(self, roots: list[int]) -> int:
        """
        Run GC collection cycle.

        Args:
            roots: List of root object IDs.

        Returns:
            Number of objects collected.
        """
        # Reset marking state
        self.marked.clear()
        self.gray.clear()
        self.black.clear()

        # Mark phase: traverse from roots
        self._mark(roots)

        # Cycle detection phase: check gray objects for cycles
        self._detect_cycles()

        # Sweep phase: collect unmarked objects
        collected = self._sweep()

        # Clear write buffer after collection
        self.barrier.flush()

        logger.info(f"GC: collected {collected} objects, {self.graph.live_count()} live")
        return collected

    def _mark(self, roots: list[int]) -> None:
        """Mark all objects reachable from roots."""
        queue: deque[int] = deque()

        for root_id in roots:
            if root_id not in self.graph.objects:
                continue
            obj = self.graph.objects[root_id]
            if root_id not in self.marked:
                self.marked.add(root_id)
                queue.append(root_id)

        while queue:
            current_id = queue.popleft()
            self.gray.add(current_id)

            obj = self.graph.objects[current_id]

            # Follow strong pointers
            for ptr in obj.strong_ptrs:
                if ptr.target_id not in self.marked:
                    self.marked.add(ptr.target_id)
                    queue.append(ptr.target_id)

            # Follow weak pointers (only if target is also weak)
            for ptr in obj.weak_ptrs:
                if ptr.target_id not in self.marked:
                    self.marked.add(ptr.target_id)
                    queue.append(ptr.target_id)

            self.gray.discard(current_id)
            self.black.add(current_id)

    def _detect_cycles(self) -> None:
        """Detect and handle weakref cycles."""
        # Find unmarked objects that form cycles
        to_process: list[int] = []

        for obj_id, obj in self.graph.objects.items():
            if obj_id in self.marked:
                continue
            # Check if this object is part of a weakref cycle
            if obj.weak_ptrs and not obj.strong_ptrs:
                to_process.append(obj_id)

        # For each unmarked object, check if it's part of a cycle
        for obj_id in to_process:
            if self._is_in_cycle(obj_id):
                # Mark the cycle for collection
                cycle_members = self._find_cycle_members(obj_id)
                for member_id in cycle_members:
                    self.marked.discard(member_id)

    def _is_in_cycle(self, obj_id: int) -> bool:
        """Check if object is part of a cycle via weakrefs."""
        visited: set[int] = set()
        stack = [obj_id]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            if current not in self.graph.objects:
                continue

            obj = self.graph.objects[current]
            for ptr in obj.weak_ptrs:
                if ptr.target_id == obj_id:
                    return True
                if ptr.target_id not in visited:
                    stack.append(ptr.target_id)

        return False

    def _find_cycle_members(self, obj_id: int) -> list[int]:
        """Find all objects in the same weakref cycle."""
        cycle: set[int] = {obj_id}
        queue: deque[int] = deque([obj_id])

        while queue:
            current = queue.popleft()
            if current not in self.graph.objects:
                continue

            obj = self.graph.objects[current]
            for ptr in obj.weak_ptrs:
                if ptr.target_id not in cycle and ptr.target_id in self.graph.objects:
                    cycle.add(ptr.target_id)
                    queue.append(ptr.target_id)

        return list(cycle)

    def _sweep(self) -> int:
        """Sweep unmarked objects and collect them."""
        collected = 0

        for obj_id, obj in list(self.graph.objects.items()):
            if obj_id not in self.marked:
                obj.collected = True
                collected += 1

        return collected

    def clear_all(self) -> None:
        """Clear all collected objects from the graph."""
        self.graph.objects = {
            obj_id: obj for obj_id, obj in self.graph.objects.items()
            if not obj.collected
        }
        self.graph.next_id = max(self.graph.objects.keys(), default=0) + 1
