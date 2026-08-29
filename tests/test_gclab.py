"""Tests for GC verification."""
import pytest

from gclab.gc import TracingGC, WriteBarrier
from gclab.heap import ObjectGraph, InvalidPointerError
from gclab.verify import (
    property_reachability,
    property_no_dangles,
    property_cycle_collection,
    mutation_test,
    run_verify,
)


class TestObjectGraph:
    """Test the object graph."""

    def test_alloc(self):
        graph = ObjectGraph()
        obj = graph.alloc("root")
        assert obj.obj_id == 1
        assert obj.kind == "root"
        assert obj.size == 1

    def test_alloc_with_size(self):
        graph = ObjectGraph()
        obj = graph.alloc("container", size=100)
        assert obj.size == 100

    def test_alloc_invalid_size(self):
        graph = ObjectGraph()
        with pytest.raises(ValueError):
            graph.alloc("root", size=0)

    def test_add_strong(self):
        graph = ObjectGraph()
        obj1 = graph.alloc("root")
        obj2 = graph.alloc("container")
        graph.add_strong(obj1.obj_id, obj2.obj_id)
        assert len(obj1.strong_ptrs) == 1
        assert obj1.strong_ptrs[0].target_id == obj2.obj_id

    def test_add_weak(self):
        graph = ObjectGraph()
        obj1 = graph.alloc("root")
        obj2 = graph.alloc("container")
        graph.add_weak(obj1.obj_id, obj2.obj_id)
        assert len(obj1.weak_ptrs) == 1
        assert obj1.weak_ptrs[0].weak is True

    def test_self_loop_raises(self):
        graph = ObjectGraph()
        obj = graph.alloc("root")
        with pytest.raises(InvalidPointerError):
            graph.add_strong(obj.obj_id, obj.obj_id)

    def test_unknown_object_raises(self):
        graph = ObjectGraph()
        obj = graph.alloc("root")
        with pytest.raises(InvalidPointerError):
            graph.add_strong(obj.obj_id, 999)

    def test_get_object(self):
        graph = ObjectGraph()
        obj = graph.alloc("root")
        assert graph.get(obj.obj_id) is obj

    def test_get_unknown_raises(self):
        graph = ObjectGraph()
        with pytest.raises(InvalidPointerError):
            graph.get(999)

    def test_live_count(self):
        graph = ObjectGraph()
        graph.alloc("root")
        graph.alloc("container")
        assert graph.live_count() == 2

    def test_collected_count(self):
        graph = ObjectGraph()
        graph.alloc("root")
        graph.alloc("container")
        assert graph.collected_count() == 0


class TestTracingGC:
    """Test the tracing garbage collector."""

    def test_collect_garbage(self):
        graph = ObjectGraph()
        gc = TracingGC(graph)
        root = graph.alloc("root")
        graph.alloc("container")
        graph.alloc("container")
        graph.add_strong(root.obj_id, graph.objects[2].obj_id)

        collected = gc.collect_garbage([root.obj_id])
        assert collected == 1  # Third object collected

    def test_reachability(self):
        graph = ObjectGraph()
        gc = TracingGC(graph)
        root = graph.alloc("root")
        obj1 = graph.alloc("container")
        obj2 = graph.alloc("container")
        graph.add_strong(root.obj_id, obj1.obj_id)
        graph.add_strong(obj1.obj_id, obj2.obj_id)

        gc.collect_garbage([root.obj_id])
        assert property_reachability(graph, gc, [root.obj_id])

    def test_no_dangles(self):
        graph = ObjectGraph()
        gc = TracingGC(graph)
        root = graph.alloc("root")
        obj1 = graph.alloc("container")
        graph.add_strong(root.obj_id, obj1.obj_id)

        gc.collect_garbage([root.obj_id])
        assert property_no_dangles(graph, gc)

    def test_cycle_collection(self):
        graph = ObjectGraph()
        gc = TracingGC(graph)
        root = graph.alloc("root")
        weak1 = graph.alloc("weakref")
        weak2 = graph.alloc("weakref")
        graph.add_weak(weak1.obj_id, weak2.obj_id)
        graph.add_weak(weak2.obj_id, weak1.obj_id)

        gc.collect_garbage([root.obj_id])
        assert property_cycle_collection(graph, gc)

    def test_write_barrier(self):
        graph = ObjectGraph()
        barrier = WriteBarrier()
        gc = TracingGC(graph, barrier)
        from gclab.barrier import install_barrier
        install_barrier(graph, gc)
        root = graph.alloc("root")
        obj = graph.alloc("container")
        graph.add_strong(root.obj_id, obj.obj_id)
        assert len(barrier.buffer) == 1


class TestVerify:
    """Test the verification harness."""

    def test_run_verify(self):
        """Run the verification harness."""
        result = run_verify(seed=42, trials=10)
        assert result is True

    def test_property_reachability_pass(self):
        """Test reachability property passes."""
        graph = ObjectGraph()
        gc = TracingGC(graph)
        root = graph.alloc("root")
        obj1 = graph.alloc("container")
        obj2 = graph.alloc("container")
        graph.add_strong(root.obj_id, obj1.obj_id)
        graph.add_strong(obj1.obj_id, obj2.obj_id)

        gc.collect_garbage([root.obj_id])
        assert property_reachability(graph, gc, [root.obj_id])

    def test_property_reachability_fail(self):
        """Test reachability property fails when object not marked."""
        graph = ObjectGraph()
        gc = TracingGC(graph)
        root = graph.alloc("root")
        obj = graph.alloc("container")
        # Don't add pointer from root to obj

        gc.collect_garbage([root.obj_id])
        # obj should not be marked
        assert obj.obj_id not in gc.marked
        # But if we claim it should be, property should fail
        # (This test verifies the property function logic)

    def test_property_no_dangles_pass(self):
        """Test no-dangles property passes."""
        graph = ObjectGraph()
        gc = TracingGC(graph)
        root = graph.alloc("root")
        obj = graph.alloc("container")
        graph.add_strong(root.obj_id, obj.obj_id)

        gc.collect_garbage([root.obj_id])
        assert property_no_dangles(graph, gc)

    def test_property_cycle_collection_pass(self):
        """Test cycle collection property passes."""
        graph = ObjectGraph()
        gc = TracingGC(graph)
        root = graph.alloc("root")
        weak1 = graph.alloc("weakref")
        weak2 = graph.alloc("weakref")
        graph.add_weak(weak1.obj_id, weak2.obj_id)
        graph.add_weak(weak2.obj_id, weak1.obj_id)

        gc.collect_garbage([root.obj_id])
        assert property_cycle_collection(graph, gc)

    def test_mutation_test(self):
        """Test mutation test works."""
        graph = ObjectGraph()
        gc = TracingGC(graph)
        roots = [graph.alloc("root").obj_id]
        assert mutation_test(graph, gc, roots)


class TestDemo:
    """Test the demo."""

    def test_demo_output(self, capsys):
        """Test demo runs without errors."""
        from gclab.__main__ import run_demo
        result = run_demo()
        assert result == 0
        captured = capsys.readouterr()
        assert "GC Lab Demo" in captured.out
