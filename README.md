# Genesis

> **One-line definition — authored by the researchers.**
> _(What Genesis is, in a sentence. Unwritten.)_

---

## This repository is the laboratory, not the system.

There is no cognitive architecture here yet, and that is deliberate. We are preparing
the laboratory: the structure, memory, and working discipline that a long research
effort needs before the first line of the system is written.

**The one rule right now:** do not implement cognitive architecture. `src/` and `tests/`
stay empty until the foundations in `canon/` and `research/` are ready.

---

## Structure

| Path | What it holds | Change rate |
|------|---------------|-------------|
| `canon/` | The canon. Stable, shared, authoritative — what we currently believe and how we've agreed to work. | Slow |
| `research/` | The living record. Everything thought, tried, decided, and questioned — append-mostly, chronological. | Fast |
| `ai/` | Working memory for AI collaborators — the state that must survive a session boundary. | Every session |
| `src/` | The implementation. Empty by design. | Not yet |
| `tests/` | Validation of the implementation. Empty by design. | Not yet |

### Where to start reading

1. [`canon/vision.md`](canon/vision.md) — the thesis. Why Genesis exists.
2. [`canon/philosophical-foundations.md`](canon/philosophical-foundations.md) — the ground
   the vision stands on.
3. [`canon/constitution.md`](canon/constitution.md) — the invariants that govern the project.
4. [`canon/roadmap.md`](canon/roadmap.md) — where we are and what comes next.
5. [`ai/current_focus.md`](ai/current_focus.md) — what is actually being worked on today.

The rest of the canon: [`ontology.md`](canon/ontology.md),
[`architecture.md`](canon/architecture.md), and
[`research-methodology.md`](canon/research-methodology.md).

If you are an AI collaborator opening this repo cold, start at
[`ai/README.md`](ai/README.md), and read [`ai/collaboration.md`](ai/collaboration.md)
before touching anything.

---

## Who writes what

The researchers author all substance — vision, principles, ontology, direction. AI
maintains form — structure, clarity, formatting, links. The full contract is in
[`ai/collaboration.md`](ai/collaboration.md).

---

*Status: Phase 0 — building the laboratory. Started 2026-08-06.*
