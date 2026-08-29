"""Write barrier for the GC."""
from .config import GC_WRITE_BUFFER_SIZE
from .heap import ObjectGraph


def install_barrier(graph: ObjectGraph, gc: object) -> None:
    """Install write barrier on object graph mutations."""
    original_add_strong = graph.add_strong
    original_add_weak = graph.add_weak

    def patched_add_strong(from_id: int, to_id: int) -> None:
        original_add_strong(from_id, to_id)
        gc.barrier.on_write(from_id, to_id)

    def patched_add_weak(from_id: int, to_id: int) -> None:
        original_add_weak(from_id, to_id)
        gc.barrier.on_write(from_id, to_id)

    graph.add_strong = patched_add_strong
    graph.add_weak = patched_add_weak
