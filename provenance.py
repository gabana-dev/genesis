"""
Genesis provenance graph — what rests on what, read-only.

Authorised by DR0005 as part of the orientation layer: it reports, it does not decide. Every
path here is a read, and it may not edit a link, supply a missing source, or resolve anything
it finds.

WHY IT EXISTS
    The provenance rule in `ai/collaboration.md` requires every conclusion in the canon to
    carry a Source link back to the reasoning that earned it. That structure has existed since
    the beginning as *links in markdown* — and nothing could walk it.

    The cost of that showed on 2026-08-18. MEASURE-1 §7 asserted that structure and
    affordability do not overlap; §8 withdrew it once a power analysis showed the test was
    blind at ≥4h. **Nothing flagged what depended on the retracted claim.** It was found by
    reading. A retraction that cannot enumerate its dependents is a retraction you have to
    trust someone to have chased.

    Two ratified rules were also mislaid in files nothing pointed at — the Phase-5 constraint
    and the named-consumer requirement (DR0005, DR0006). Both existed. Neither was findable.

WHAT IT ANSWERS
    rests-on   what would be affected if this document changed or was retracted
    depends    what this document rests on
    orphans    documents nothing links to — the Guardian's "orphan" finding, mechanised
    unsourced  canon documents with no link into research/decisions or research/journal,
               which is the provenance rule's own failure condition

WHAT IT DOES NOT DO
    It works at FILE granularity, and section anchors are captured but not resolved. The
    MEASURE-1 case was section-level (§7 retracted, §8 standing), so this tool would have
    named the dependent files and left the section question to a human. That is a real limit,
    stated rather than hidden.

    It also does not decide. Per `ai/collaboration.md`, when a canon entry has no source the
    Guardian **flags it and does not supply one**.

Usage:  .venv/bin/python provenance.py [--rests-on PATH | --depends PATH | --orphans
                                        | --unsourced | --json]
"""

import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {".git", ".venv", "__pycache__", ".pytest_cache"}

# A canon document's source must reach the reasoning that earned it. Those are the two places
# reasoning is recorded; `ai/collaboration.md` names both.
SOURCE_DIRS = ("research/decisions", "research/journal")

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _walk():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f.endswith(".md"):
                yield os.path.relpath(os.path.join(base, f), ROOT)


def build():
    """
    Returns (edges, anchors, unresolved).

    `edges[a]` is the set of documents `a` links to. `anchors[(a, b)]` keeps the section
    fragments a used when citing b — captured because a retraction is usually sectional, and
    dropping them would silently overstate what this tool can resolve.
    """
    edges, anchors, unresolved = defaultdict(set), defaultdict(set), []
    for src in _walk():
        base = os.path.dirname(src)
        try:
            text = open(os.path.join(ROOT, src), errors="ignore").read()
        except OSError:
            continue
        for m in LINK.finditer(text):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path, _, frag = target.partition("#")
            if not path:
                continue
            dest = os.path.normpath(os.path.join(base, path))
            if not os.path.exists(os.path.join(ROOT, dest)):
                unresolved.append((src, target))
                continue
            if os.path.isdir(os.path.join(ROOT, dest)):
                continue
            edges[src].add(dest)
            if frag:
                anchors[(src, dest)].add(frag)
    return dict(edges), dict(anchors), unresolved


def reverse(edges):
    rev = defaultdict(set)
    for a, targets in edges.items():
        for b in targets:
            rev[b].add(a)
    return dict(rev)


def _reach(graph, start):
    """Transitive closure from `start`, excluding `start`. Cycles terminate on the seen set."""
    seen, stack = set(), [start]
    while stack:
        n = stack.pop()
        for nxt in graph.get(n, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    seen.discard(start)
    return seen


def rests_on(path, edges=None, anchors=None):
    """
    What would be affected if `path` changed. Direct citers, then everything reaching them.

    This is the query that did not exist when MEASURE-1 §7 was retracted.
    """
    edges = edges if edges is not None else build()[0]
    anchors = anchors if anchors is not None else build()[1]
    rev = reverse(edges)
    direct = sorted(rev.get(path, ()))
    return {
        "document": path,
        "direct": [{"file": d, "sections_cited": sorted(anchors.get((d, path), ())) or None}
                   for d in direct],
        "transitive": sorted(_reach(rev, path) - set(direct)),
    }


def depends(path, edges=None):
    edges = edges if edges is not None else build()[0]
    direct = sorted(edges.get(path, ()))
    return {"document": path, "direct": direct,
            "transitive": sorted(_reach(edges, path) - set(direct))}


def orphans(edges):
    """Documents nothing links to. READMEs are entry points and are not orphans."""
    rev = reverse(edges)
    out = []
    for f in _walk():
        if os.path.basename(f) == "README.md":
            continue
        if not rev.get(f):
            out.append(f)
    return sorted(out)


def unsourced(edges):
    """
    Canon documents that reach no decision record or journal entry.

    `ai/collaboration.md`: a conclusion in the canon must trace to the reasoning that earned
    it, and when the AI notices one that does not, **it flags it and does not supply one.**
    """
    out = []
    for f in sorted(f for f in _walk() if f.startswith("canon/")):
        if os.path.basename(f) == "README.md":
            continue
        reachable = _reach(edges, f) | edges.get(f, set())
        if not any(r.startswith(SOURCE_DIRS) for r in reachable):
            out.append(f)
    return out


def report():
    edges, anchors, unres = build()
    docs = list(_walk())
    return {
        "documents": len(docs),
        "links": sum(len(v) for v in edges.values()),
        "unresolved_links": [{"from": a, "target": b} for a, b in unres],
        "orphans": orphans(edges),
        "unsourced_canon": unsourced(edges),
    }


def render(r):
    L = ["GENESIS — PROVENANCE GRAPH", "=" * 64,
         f"documents {r['documents']}   links {r['links']}", ""]
    L.append(f"unresolved links      {len(r['unresolved_links'])}")
    for u in r["unresolved_links"][:20]:
        L.append(f"   {u['from']} -> {u['target']}")
    L.append("")
    L.append(f"orphans               {len(r['orphans'])}   (nothing links to these)")
    for o in r["orphans"][:20]:
        L.append(f"   {o}")
    L.append("")
    L.append(f"canon without source  {len(r['unsourced_canon'])}")
    for c in r["unsourced_canon"]:
        L.append(f"   {c}")
    if r["unsourced_canon"]:
        L += ["", "   A canon document reaching no decision record or journal entry is the",
              "   provenance rule's own failure condition. Flagged, not resolved --",
              "   ai/collaboration.md: the Guardian flags a missing source and does not",
              "   supply one."]
    L += ["", "This layer reports. It does not decide — DR0005."]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]

    def emit(obj, text):
        print(json.dumps(obj, indent=1, default=str) if as_json else text)

    if argv and argv[0] in ("--rests-on", "--depends"):
        if len(argv) < 2:
            print(f"provenance.py: {argv[0]} needs a path", file=sys.stderr)
            return 2
        path = os.path.normpath(argv[1])
        if not os.path.exists(os.path.join(ROOT, path)):
            print(f"provenance.py: no such document: {path}", file=sys.stderr)
            return 2
        edges, anchors, _ = build()
        if argv[0] == "--rests-on":
            r = rests_on(path, edges, anchors)
            lines = [f"WHAT RESTS ON  {path}", "=" * 64,
                     f"direct citers ({len(r['direct'])}):"]
            for d in r["direct"]:
                sec = f"  [cites {', '.join(d['sections_cited'])}]" if d["sections_cited"] else ""
                lines.append(f"   {d['file']}{sec}")
            lines += ["", f"reached transitively ({len(r['transitive'])}):"]
            lines += [f"   {t}" for t in r["transitive"]]
            lines += ["", "Section anchors are captured, not resolved — a sectional retraction",
                      "names these files and leaves the section question to a human."]
            emit(r, "\n".join(lines))
        else:
            r = depends(path, edges)
            lines = [f"WHAT {path} RESTS ON", "=" * 64,
                     f"direct ({len(r['direct'])}):"] + [f"   {d}" for d in r["direct"]]
            lines += ["", f"transitive ({len(r['transitive'])}):"]
            lines += [f"   {t}" for t in r["transitive"]]
            emit(r, "\n".join(lines))
        return 0

    if argv and argv[0] == "--orphans":
        edges, _, _ = build()
        o = orphans(edges)
        emit({"orphans": o}, "ORPHANS (nothing links to these)\n" + "=" * 64 + "\n" +
             "\n".join(f"   {x}" for x in o))
        return 0

    if argv and argv[0] == "--unsourced":
        edges, _, _ = build()
        u = unsourced(edges)
        emit({"unsourced_canon": u}, "CANON WITHOUT A SOURCE\n" + "=" * 64 + "\n" +
             "\n".join(f"   {x}" for x in u))
        return 0

    if argv:
        print(f"provenance.py: unknown option {argv[0]}", file=sys.stderr)
        return 2

    r = report()
    emit(r, render(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
