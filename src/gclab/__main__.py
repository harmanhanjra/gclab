"""CLI entry point."""
import argparse
import sys
import logging

from .gc import TracingGC
from .heap import ObjectGraph
from .verify import run_verify

logging.basicConfig(level=logging.INFO)


def main() -> int:
    parser = argparse.ArgumentParser(description="GC Lab - Verified Tracing Garbage Collector")
    subparsers = parser.add_subparsers(dest="command")

    verify_parser = subparsers.add_parser("verify", help="Run verification harness")
    verify_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    verify_parser.add_argument("--trials", type=int, default=100, help="Number of trials")

    demo_parser = subparsers.add_parser("demo", help="Run a live demo")

    args = parser.parse_args()

    if args.command == "verify":
        return 0 if run_verify(args.seed, args.trials) else 1
    elif args.command == "demo":
        return run_demo()
    else:
        parser.print_help()
        return 1


def run_demo() -> int:
    """Run a demo with a simple object graph."""
    print("GC Lab Demo")
    print("=" * 40)

    graph = ObjectGraph()
    gc = TracingGC(graph)

    # Create objects
    root = graph.alloc("root")
    obj1 = graph.alloc("container")
    obj2 = graph.alloc("container")
    leaf = graph.alloc("leaf")

    # Link them
    graph.add_strong(root.obj_id, obj1.obj_id)
    graph.add_strong(obj1.obj_id, obj2.obj_id)
    graph.add_strong(obj2.obj_id, leaf.obj_id)

    print(f"Created 4 objects, all reachable from root")
    print(f"Live before GC: {graph.live_count()}")

    # Collect garbage (none should be collected)
    gc.collect_garbage([root.obj_id])
    print(f"Live after GC: {graph.live_count()}")

    # Create an unreachable object
    orphan = graph.alloc("leaf")
    print(f"Created orphan object")
    print(f"Live before GC: {graph.live_count()}")

    # Collect garbage (orphan should be collected)
    gc.collect_garbage([root.obj_id])
    print(f"Live after GC: {graph.live_count()}")

    # Create a weakref cycle
    weak1 = graph.alloc("weakref")
    weak2 = graph.alloc("weakref")
    graph.add_weak(weak1.obj_id, weak2.obj_id)
    graph.add_weak(weak2.obj_id, weak1.obj_id)

    print(f"Created weakref cycle")
    print(f"Live before GC: {graph.live_count()}")

    # Collect garbage (cycle should be collected)
    gc.collect_garbage([root.obj_id])
    print(f"Live after GC: {graph.live_count()}")

    print("\nDemo complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
