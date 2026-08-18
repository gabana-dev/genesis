# Genesis

> **One-line definition — authored by the researchers.**
> _(What Genesis is, in a sentence. Unwritten.)_

---

## This repository is the laboratory, not the system.

**Superseded 2026-08-09.** The original framing below — "there is no cognitive architecture
here yet, and that is deliberate" — described the first three days. The cognitive-architecture
thesis was retired by
[DR0002](research/decisions/0002-close-the-genesis-research-program.md) as established science,
and the project now does disciplined engineering against real recorded environments
([DR0003](research/decisions/0003-engineering-posture-real-data.md)), claiming no novelty.

**What is actually here:** a market event recorder with a hash-chained log and completeness
labels *validated to carry information* (p = 0.0165); measurement and execution machinery; a
trial ledger where every test is declared before it is run and cannot be un-declared; four
completed experiments; and ~11,000 lines of Python under 19 passing test suites.

Start with [`research/CURRENT-STATE-2026-08-18.md`](research/CURRENT-STATE-2026-08-18.md) —
what is established, what is falsified, what is unknown, and nine contradictions this
repository has recorded against itself.

---

## Structure

| Path | What it holds | Change rate |
|------|---------------|-------------|
| `canon/` | The canon. Stable, shared, authoritative — what we currently believe and how we've agreed to work. | Slow |
| `research/` | The living record. Everything thought, tried, decided, and questioned — append-mostly, chronological. | Fast |
| `ai/` | Working memory for AI collaborators — the state that must survive a session boundary. | Every session |
| `recorder/` | The event recorder — hash-chained log, completeness labels, venue dialects. | Active |
| `market/` | Measurement and execution — estimators, fill simulator, trial ledger. | Active |
| `rdb/` | The RDB-1 real-data bridge. Closed ([DR0004](research/decisions/0004-close-rdb-1.md)). | Closed |
| `lab/` | Retired cognitive-architecture laboratories, kept runnable. Was `src/`. | Historical |
| `tests/` | 19 suites, all passing. | Active |
| `status.py` | The orientation layer — reports, never decides ([DR0005](research/decisions/0005-orientation-layer.md)). | Active |

### Where to start reading

**If you want to know what this project actually does, start here:**
[`research/CURRENT-STATE-2026-08-18.md`](research/CURRENT-STATE-2026-08-18.md) — what is
established, falsified and unknown — and [`canon/operations.md`](canon/operations.md), which is
how research is conducted here: frozen contracts, the trial ledger, kill conditions declared
before the data, and what may not be claimed.

The reading order below is the original one, written before the market line opened.

1. [`canon/vision.md`](canon/vision.md) — the thesis. Why Genesis exists.
2. [`canon/philosophical-foundations.md`](canon/philosophical-foundations.md) — the ground
   the vision stands on.
3. [`canon/constitution.md`](canon/constitution.md) — the invariants that govern the project.
4. [`canon/roadmap.md`](canon/roadmap.md) — where we are and what comes next.
5. [`ai/current_focus.md`](ai/current_focus.md) — what is actually being worked on today.
6. [`research/PROGRAM-STATUS.md`](research/PROGRAM-STATUS.md) — the milestone tracker.

The rest of the canon: [`operations.md`](canon/operations.md) — **the working method**,
[`epistemology.md`](canon/epistemology.md), [`ontology.md`](canon/ontology.md),
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
