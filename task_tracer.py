"""Reverius Task Tracer

Lightweight, innovative task tracer for AI 'reverius'. Features:
- hierarchical tasks (parent/child)
- timing and durations
- annotations, tags, metadata
- simple in-memory store and JSON/CSV export
"""

from __future__ import annotations
import time
import json
import csv
from typing import Optional, List, Dict, Any, Set


class Task:
    __slots__ = ("name", "parent", "children", "start_ns", "end_ns", "annotations", "tags", "meta")

    def __init__(self, name: str, parent: Optional["Task"] = None, **meta: Any):
        self.name = name
        self.parent = parent
        self.children: List[Task] = []
        # use nanosecond integer timestamps to reduce float overhead and improve precision
        self.start_ns = time.time_ns()
        self.end_ns: Optional[int] = None
        self.annotations: List[str] = []
        # use set for tags (faster membership, less duplicates); expose as list in exports
        self.tags: Set[str] = set()
        self.meta: Dict[str, Any] = meta
        if parent:
            parent.children.append(self)

    def finish(self):
        self.end_ns = time.time_ns()

    @property
    def duration(self) -> Optional[float]:
        if self.end_ns is None:
            return None
        # return seconds as float (derived from ns)
        return (self.end_ns - self.start_ns) / 1e9

    def annotate(self, note: str):
        self.annotations.append(note)

    def add_tag(self, tag: str):
        self.tags.add(tag)

    def to_dict(self, compact: bool = False) -> Dict[str, Any]:
        """Return a serializable dict. In compact mode omit heavy fields like raw meta and full child trees.

        - compact=False: full tree for convenience (still uses ns->seconds conversion)
        - compact=True: minimal fields to reduce size (no child details, no full meta by default)
        """
        base = {
            "name": self.name,
            "start_ns": self.start_ns,
            "end_ns": self.end_ns,
            "duration": self.duration,
            "annotations": self.annotations,
            "tags": list(self.tags),
        }
        if not compact:
            base["meta"] = self.meta
            base["children"] = [c.to_dict(compact=False) for c in self.children]
        else:
            # include only a small meta summary when compact
            if self.meta:
                base["meta_summary"] = {k: str(self.meta[k]) for k in list(self.meta)[:3]}
            base["child_count"] = len(self.children)
        return base


class TaskTracer:
    __slots__ = ("tasks", "current")

    def __init__(self):
        # store only root tasks here; children are linked from parents
        self.tasks: List[Task] = []
        self.current: Optional[Task] = None

    def start(self, name: str, **meta) -> Task:
        """Start a new task. If a task is active it becomes the parent."""
        task = Task(name, parent=self.current, **meta)
        if self.current is None:
            self.tasks.append(task)
        self.current = task
        return task

    def end(self) -> Optional[Task]:
        """Finish the current task and move focus to its parent."""
        if not self.current:
            return None
        self.current.finish()
        finished = self.current
        self.current = self.current.parent
        return finished

    def annotate(self, note: str):
        if self.current:
            self.current.annotate(note)

    def tag(self, tag: str):
        if self.current:
            self.current.add_tag(tag)

    def export_json(self, path: str):
        # default to streaming NDJSON to avoid building a large list in memory
        self.export_json(path, ndjson=True)

    def export_json(self, path: str, ndjson: bool = True, compact: bool = True):
        """Export tasks to JSON.

        - ndjson=True: one JSON object per line (streaming, low memory)
        - compact=True: smaller per-task payloads
        """
        if ndjson:
            with open(path, "w", encoding="utf-8") as f:
                for root in self.tasks:
                    # stream root and its subtree as a single object per line
                    json.dump(root.to_dict(compact=compact), f, ensure_ascii=False)
                    f.write("\n")
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([t.to_dict(compact=compact) for t in self.tasks], f, indent=2)

    def export_csv(self, path: str, compact: bool = True):
        """Stream a flattened CSV without building all rows in memory.

        - compact=True: omit heavy meta fields
        """
        def row_generator():
            def walk(t: Task, parent_path: str = ""):
                path_name = f"{parent_path}/{t.name}" if parent_path else t.name
                yield {
                    "path": path_name,
                    "name": t.name,
                    "start_ns": t.start_ns,
                    "end_ns": t.end_ns,
                    "duration_s": t.duration,
                    "annotations": "; ".join(t.annotations),
                    "tags": ",".join(sorted(t.tags)),
                    "meta": json.dumps(t.meta, ensure_ascii=False) if not compact else (json.dumps({k: str(t.meta[k]) for k in list(t.meta)[:2]}, ensure_ascii=False) if t.meta else ""),
                }
                for c in t.children:
                    yield from walk(c, path_name)

            for root in self.tasks:
                yield from walk(root)

        gen = row_generator()
        try:
            first = next(gen)
        except StopIteration:
            return
        fieldnames = list(first.keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(first)
            for r in gen:
                writer.writerow(r)


if __name__ == "__main__":
    tracer = TaskTracer()
    t1 = tracer.start("plan", priority="high")
    tracer.annotate("thinking about objectives")
    t1a = tracer.start("draft prompt")
    tracer.annotate("first draft")
    tracer.end()
    tracer.tag("iteration-1")
    tracer.end()
    tracer.export_json("reverius_tasks.json")
    tracer.export_csv("reverius_tasks.csv")
