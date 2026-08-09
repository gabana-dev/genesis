"""
Append-only event log with hash chaining.

Storage is JSONL: one event per line, opened in append mode, flushed and fsync'd on write.
Nothing in this module can modify or delete an existing line — the only write operation is
append.

The chain detects later alteration of any individual event or removal of any event from the
middle. It does not defend against wholesale rewriting of the entire file by someone able to
recompute every subsequent hash, and it establishes no external time anchor. Both limits are
stated in SPEC.md §7 rather than papered over.
"""

import json
import os
import uuid
from pathlib import Path

from events import GENESIS_HASH, event_hash, make_event, now


class EventLog:
    def __init__(self, path, recorder_run=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.recorder_run = recorder_run or str(uuid.uuid4())
        self._fh = None
        self._index, self._prev_hash = self._resume()

    @property
    def checkpoint_path(self):
        return Path(str(self.path) + ".checkpoint")

    def _resume(self):
        """Continue an existing chain rather than starting a second one beside it."""
        if not self.path.exists():
            return 0, GENESIS_HASH
        last = None
        for last in read(self.path):
            pass
        if last is None:
            return 0, GENESIS_HASH
        return last["event_index"] + 1, last["hash"]

    def _write_checkpoint(self):
        """
        Length-and-head anchor, updated after every append.

        A hash chain alone cannot detect its own tail being cut: the remaining prefix is
        internally consistent. The checkpoint records how many events the chain is supposed to
        have and what its head hash is, so a truncated log no longer agrees with it.
        """
        tmp = Path(str(self.checkpoint_path) + ".tmp")
        payload = {"event_count": self._index, "last_index": self._index - 1,
                   "last_hash": self._prev_hash, "updated_at": now()}
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.checkpoint_path)

    def __enter__(self):
        self._fh = open(self.path, "a", encoding="utf-8")
        return self

    def __exit__(self, *exc):
        if self._fh:
            self._fh.close()
            self._fh = None

    def append(self, event_class, event_type, body) -> dict:
        ev = make_event(event_class, event_type, body,
                        self._index, self._prev_hash, self.recorder_run)
        line = json.dumps(ev, ensure_ascii=False)
        if self._fh is None:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        else:
            self._fh.write(line + "\n")
            self._fh.flush()
            os.fsync(self._fh.fileno())
        self._index += 1
        self._prev_hash = ev["hash"]
        self._write_checkpoint()
        return ev


def read(path):
    """Yield events in file order. Malformed lines raise rather than being skipped silently."""
    p = Path(path)
    if not p.exists():
        return
    with open(p, encoding="utf-8") as fh:
        for n, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"corrupt log line {n} in {p}: {e}") from e


def verify(path):
    """
    Walk the chain and reconcile it against the checkpoint.

    Returns (ok, problems). The chain detects modification, insertion, deletion and
    reordering; the checkpoint additionally detects a truncated tail. A missing checkpoint is
    itself a problem -- without it the log's length is unattested, so it cannot be declared
    verified.
    """
    problems = []
    prev_hash = GENESIS_HASH
    expected_index = 0
    count = 0
    for ev in read(path):
        count += 1
        if ev.get("event_index") != expected_index:
            problems.append({"index": expected_index, "kind": "index_out_of_order",
                             "found": ev.get("event_index")})
            return False, problems
        if ev.get("prev_hash") != prev_hash:
            problems.append({"index": ev["event_index"], "kind": "broken_link"})
            return False, problems
        if event_hash(ev, prev_hash) != ev.get("hash"):
            problems.append({"index": ev["event_index"], "kind": "hash_mismatch"})
            return False, problems
        prev_hash = ev["hash"]
        expected_index += 1

    cp_path = Path(str(path) + ".checkpoint")
    if not cp_path.exists():
        problems.append({"index": count, "kind": "checkpoint_missing",
                         "detail": "log length is unattested; a truncated tail would be "
                                   "undetectable"})
        return False, problems

    try:
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        problems.append({"index": count, "kind": "checkpoint_unreadable", "detail": str(e)})
        return False, problems

    if count < cp.get("event_count", 0):
        problems.append({"index": count, "kind": "truncated_tail",
                         "expected_events": cp["event_count"], "found_events": count,
                         "missing": cp["event_count"] - count})
        return False, problems
    if count > cp.get("event_count", 0):
        problems.append({"index": count, "kind": "checkpoint_behind_log",
                         "expected_events": cp["event_count"], "found_events": count})
        return False, problems
    if prev_hash != cp.get("last_hash"):
        problems.append({"index": count, "kind": "head_hash_mismatch"})
        return False, problems

    return True, []
