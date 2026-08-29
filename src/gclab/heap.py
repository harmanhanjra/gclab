"""Typed object graph for the GC heap."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


class InvalidPointerError(Exception):
    """Pointer validation failed."""


@dataclass(frozen=True)
class Pointer:
    """Strong or weak reference to a heap object."""
    target_id: int
    weak: bool = False

    def __repr__(self) -> str:
        return f"Pointer(id={self.target_id}, weak={self.weak})"


@dataclass
class HeapObject:
    """A node in the object graph."""
    obj_id: int
    kind: str  # "root", "container", "leaf", "weakref"
    strong_ptrs: list[Pointer] = field(default_factory=list)
    weak_ptrs: list[Pointer] = field(default_factory=list)
    size: int = 1
    collected: bool = False

    def add_strong(self, ptr: Pointer) -> None:
        if ptr.target_id == self.obj_id:
            raise InvalidPointerError("Self-loop not allowed")
        self.strong_ptrs.append(ptr)

    def add_weak(self, ptr: Pointer) -> None:
        if ptr.target_id == self.obj_id:
            raise InvalidPointerError("Self-loop not allowed")
        self.weak_ptrs.append(ptr)

    def __repr__(self) -> str:
        return f"Obj({self.obj_id}, {self.kind}, strong={len(self.strong_ptrs)}, weak={len(self.weak_ptrs)})"


class ObjectGraph:
    """Heap object graph with typed pointers."""

    def __init__(self) -> None:
        self.objects: dict[int, HeapObject] = {}
        self.next_id: int = 1

    def alloc(self, kind: str, size: int = 1) -> HeapObject:
        if size <= 0:
            raise ValueError(f"size must be positive, got {size}")
        obj = HeapObject(obj_id=self.next_id, kind=kind, size=size)
        self.objects[self.next_id] = obj
        self.next_id += 1
        return obj

    def add_strong(self, from_id: int, to_id: int) -> None:
        self._check_valid(from_id, to_id)
        self.objects[from_id].add_strong(Pointer(to_id, weak=False))

    def add_weak(self, from_id: int, to_id: int) -> None:
        self._check_valid(from_id, to_id)
        self.objects[from_id].add_weak(Pointer(to_id, weak=True))

    def _check_valid(self, from_id: int, to_id: int) -> None:
        if from_id not in self.objects:
            raise InvalidPointerError(f"Unknown object {from_id}")
        if to_id not in self.objects:
            raise InvalidPointerError(f"Unknown target {to_id}")

    def get(self, obj_id: int) -> HeapObject:
        if obj_id not in self.objects:
            raise InvalidPointerError(f"Object {obj_id} not found")
        return self.objects[obj_id]

    def live_count(self) -> int:
        return sum(1 for obj in self.objects.values() if not obj.collected)

    def collected_count(self) -> int:
        return sum(1 for obj in self.objects.values() if obj.collected)
