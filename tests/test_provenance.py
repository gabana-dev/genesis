"""
Checks for the provenance graph walker.

WHY THESE
    The tool exists because MEASURE-1 §7 was retracted and nothing enumerated what depended on
    it. So the checks that matter assert it FINDS things — a dependent, a canon document with
    no source, an orphan, a broken link — because a walker that silently found nothing would
    look identical to a clean repository.

    One check asserts the opposite direction: a canon document WITH a source must not be
    flagged. A detector that fires on everything is noise, and it would train a reader to
    ignore it, which is worse than not having it.

    And one asserts the DR0005 constraint directly: it reports, it does not decide — so it must
    not create or modify a single file.

Fixtures are SYNTHETIC, built in a temp directory.

Run: .venv/bin/python tests/test_provenance.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import provenance as P

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def make(tmp, path, text=""):
    full = os.path.join(tmp, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w").write(text)
    return path


def with_root(tmp, fn, *a, **k):
    old = P.ROOT
    P.ROOT = tmp
    try:
        return fn(*a, **k)
    finally:
        P.ROOT = old


# ---- the query that did not exist ------------------------------------------------------

@check
def rests_on_finds_a_dependent(tmp):
    """THE MEASURE-1 CASE. A retracted document must be able to name what cites it."""
    make(tmp, "research/experiments/0008.md", "a measurement")
    make(tmp, "canon/operations.md", "see [M1](../research/experiments/0008.md) §8")
    make(tmp, "market/EVIDENCE.md", "per [M1](../research/experiments/0008.md)")

    r = with_root(tmp, P.rests_on, "research/experiments/0008.md")
    files = {d["file"] for d in r["direct"]}
    assert files == {"canon/operations.md", "market/EVIDENCE.md"}, files
    return f"a retracted document names its {len(files)} direct dependents"


@check
def rests_on_reaches_transitively(tmp):
    make(tmp, "a.md", "leaf")
    make(tmp, "b.md", "[a](a.md)")
    make(tmp, "c.md", "[b](b.md)")
    r = with_root(tmp, P.rests_on, "a.md")
    assert [d["file"] for d in r["direct"]] == ["b.md"], r["direct"]
    assert r["transitive"] == ["c.md"], r["transitive"]
    return "a two-hop dependent is reached and reported separately from direct citers"


@check
def section_anchors_are_captured(tmp):
    make(tmp, "src.md", "x")
    make(tmp, "dep.md", "[s](src.md#section-7) and [s](src.md#section-8)")
    r = with_root(tmp, P.rests_on, "src.md")
    secs = r["direct"][0]["sections_cited"]
    assert secs == ["section-7", "section-8"], secs
    return "section fragments are captured so a sectional retraction can be narrowed by hand"


@check
def a_cycle_terminates(tmp):
    make(tmp, "x.md", "[y](y.md)")
    make(tmp, "y.md", "[x](x.md)")
    r = with_root(tmp, P.rests_on, "x.md")
    assert [d["file"] for d in r["direct"]] == ["y.md"]
    return "mutual citation terminates instead of looping"


# ---- the provenance rule ---------------------------------------------------------------

@check
def canon_without_a_source_is_flagged(tmp):
    make(tmp, "canon/ontology.md", "a conclusion, citing nothing")
    make(tmp, "research/decisions/0001-x.md", "reasoning")
    out = with_root(tmp, lambda: P.unsourced(P.build()[0]))
    assert out == ["canon/ontology.md"], out
    return "a canon document reaching no decision record or journal is flagged"


@check
def canon_with_a_source_is_not_flagged(tmp):
    """
    The other direction. A detector that fires on everything trains the reader to ignore it.
    """
    make(tmp, "research/decisions/0001-x.md", "reasoning")
    make(tmp, "canon/vision.md", "per [DR0001](../research/decisions/0001-x.md)")
    out = with_root(tmp, lambda: P.unsourced(P.build()[0]))
    assert out == [], out
    return "a canon document that reaches a decision record is not flagged"


@check
def a_source_reached_indirectly_still_counts(tmp):
    make(tmp, "research/journal/2026-01-01-thinking.md", "reasoning")
    make(tmp, "canon/mid.md", "[j](../research/journal/2026-01-01-thinking.md)")
    make(tmp, "canon/top.md", "[mid](mid.md)")
    out = with_root(tmp, lambda: P.unsourced(P.build()[0]))
    assert out == [], out
    return "a source reached through another canon document counts — the graph is walked"


# ---- the Guardian's other findings ------------------------------------------------------

@check
def orphans_are_found_and_readmes_are_not_orphans(tmp):
    make(tmp, "linked.md", "x")
    make(tmp, "hub.md", "[l](linked.md)")
    make(tmp, "lonely.md", "nothing points here")
    make(tmp, "docs/README.md", "an entry point, not an orphan")
    out = with_root(tmp, lambda: P.orphans(P.build()[0]))
    assert "lonely.md" in out, out
    assert "docs/README.md" not in out, out
    assert "linked.md" not in out, out
    return "unreferenced documents are found; READMEs are entry points, not orphans"


@check
def a_broken_link_is_reported_not_dropped(tmp):
    make(tmp, "a.md", "[gone](missing.md)")
    _, _, unres = with_root(tmp, P.build)
    assert unres == [("a.md", "missing.md")], unres
    return "a link to a nonexistent file is reported rather than silently skipped"


@check
def external_and_bare_anchors_are_ignored(tmp):
    make(tmp, "a.md", "[w](https://example.com) [s](#section) [m](mailto:x@y.z)")
    edges, _, unres = with_root(tmp, P.build)
    assert not edges.get("a.md"), edges
    assert unres == [], unres
    return "http, bare anchors and mailto are not treated as repository edges"


# ---- DR0005 ------------------------------------------------------------------------------

@check
def the_walker_writes_nothing(tmp):
    make(tmp, "a.md", "[b](b.md)")
    make(tmp, "b.md", "leaf")
    before = {p: os.stat(os.path.join(tmp, p)).st_mtime_ns for p in ("a.md", "b.md")}
    listing = sorted(os.listdir(tmp))

    with_root(tmp, P.report)
    with_root(tmp, P.rests_on, "b.md")

    after = {p: os.stat(os.path.join(tmp, p)).st_mtime_ns for p in before}
    assert before == after, "provenance.py modified a file it read"
    assert sorted(os.listdir(tmp)) == listing, "provenance.py created a file"
    return "report() and rests_on() mutate nothing and create nothing"


def main():
    failed = 0
    for fn in _checks:
        tmp = tempfile.mkdtemp(prefix="prov-")
        try:
            print(f"  ok  {fn.__name__}  --  {fn(tmp)}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"provenance checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
