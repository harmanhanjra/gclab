"""Main package."""
from .gc import TracingGC, WriteBarrier
from .heap import HeapObject, ObjectGraph, Pointer

__version__ = "0.1.0"
__all__ = ["HeapObject", "ObjectGraph", "Pointer", "TracingGC", "WriteBarrier"]
