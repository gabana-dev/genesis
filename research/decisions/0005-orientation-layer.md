# DR0005 — Build the orientation layer; it reports, it does not decide

**Date:** 2026-08-13 (decided) · 2026-08-18 (recorded and ratified)
**Status: RATIFIED by the researcher**, 2026-08-18, on their instruction: *"ratify it and build
genesis status"*.
**Reversibility:** easy. Nothing it builds writes to the ledger, the contracts, or the canon.

> **Provenance note, stated plainly because it is the reason this file exists.**
> The decision was made verbally on 2026-08-13 and gated on EXEC-1 completing. It was never
> written down. Until 2026-08-18 the only record of it — including the whole argument for
> excluding the deciding half — lived in an AI assistant's private memory file and nowhere in
> this repository.
>
> That is exactly the failure `ai/collaboration.md` §Provenance was written to prevent: a
> commitment whose justification cannot be traced to research. This record closes the gap. The
> reasoning below is reconstructed by the assistant from that memory and is offered as a
> **proposal**; the researcher authors, edits or rejects it. Nothing here enters the canon
> until they do.

---

## Context

Genesis has outgrown what one person can hold in mind. On 2026-08-13 the researcher put it
directly: the project had become hard to *tell anything*, because orienting inside it —
what is running, what is outstanding, what is blocked — now takes a human or an assistant
reading a dozen files.

The substrate for answering those questions already exists, and is more complete than expected:

- the **trial ledger** knows every question ever asked and which are outstanding
- the **frozen contracts** carry sha256 digests, so drift is detectable
- **completeness labels**, validated by BAV-1 (p = 0.0165), mean the record knows what it does
  not know
- the **watchdog** and `caffeinate` have carried unattended recordings for days
- `PROGRAM-STATUS.md` and `ai/project_state.md` exist for navigation

**What is missing is orchestration only.** Nothing schedules itself except the recorder, and
the "where am I, and why" step is entirely manual.

## Decision

**Build the orientation layer.** A read-only program that reads the trial ledger, the frozen
contracts, `~/genesis-evidence/` and recorder state, and reports:

- what is running
- what is outstanding — with each outstanding trial's *actual declared question*
- what is blocked, and on what
- what data is missing or stale
- what the next declared step is, and what it would need to proceed

**It proposes. It does not decide.** Specifically it may not: declare a trial, record a
result, amend or author a contract, select a research direction, or write to the canon. It is
read-only with respect to the ledger and the contracts.

It is **infrastructure, not direction.** DR0002 closed the research programme and selected no
direction; this does not reopen it. Navigation over work already done is not a research step,
and must not be mistaken for one by a later reader.

## Why the deciding half is excluded — three reasons, each sufficient alone

**1. This repository already closed the question.**
[`../prior-art-and-opportunity-map.md`](../prior-art-and-opportunity-map.md) §Axiology finds
that every approach to installing goals relocates the evaluative premise and none removes it —
*"the install problem is the is/ought gap (Hume) in an engineering costume."* **Verdict E:
unresolved, possibly ill-posed.** A layer that "knows what it wants" would be proposing to
solve, by implementation, a problem this project has already judged may not be well formed.

**2. The discipline lives in the refusals, not the code.**
What has made Genesis's results defensible is a series of refusals: pre-registering before
running, counting abandoned trials, closing RDB-1 rather than opening the holdout, claiming the
minute-scale anomaly as nothing, writing kill conditions before seeing results. The ledger is
worth something *because a human declares first and cannot un-declare*. Automating the
declaring removes the constraint that gives the count its meaning.

**3. A live demonstration, on the day the decision was made.**
The assistant proposed writing the four EXEC-1 ledger declarations. They already existed.
Unchecked, that would have duplicated them and corrupted the family-size correction the ledger
exists to protect — an automated helper, acting sensibly, silently damaging the instrument.

**A constraint the assistant mislocated, and then wrongly declared absent — corrected
2026-08-18.**

The assistant's memory held that "the roadmap places agents at Phase 5, one at a time, each
justified by a measured decision the current system gets wrong — and the LLM is never the
signal," and offered it as binding.

The **first** version of this section said the claim "is not in this repository." **That was
wrong.** It is in [`../../ai/current_focus.md`](../../ai/current_focus.md):

> **LLM enters at Phase 5** for hypothesis generation, anomaly explanation, unstructured
> events and the research record. **Never the signal.** **Agents: none until Phase 5**, then
> one at a time, each justified by a measured decision the current system gets wrong.

The memory was right about the content and wrong only about the location — it said *roadmap*,
and the text lives in working memory. The assistant then searched `canon/` and `research/`,
**not `ai/`**, using paraphrases rather than the literal wording, found nothing, and recorded
"not found" as a finding. An incomplete search reported as an absence: the same failure this
project keeps naming, committed inside a decision record about reporting honestly. It was
caught by an outside reader of the public repository, not from within.

**What the episode actually exposes, and what needs deciding.** A binding research constraint —
*never the signal*, *no agents before Phase 5* — lives in a file that `ai/README.md` describes
as assistant-maintained working memory, which "describes state and activity, never project
substance." Substance is sitting in a form-only file that the assistant is licensed to edit.
The constraint should be in the canon, authored by the researcher. Recorded here as a decision
required, not resolved.

## Evidence from EXEC-1 that the reporting half is worth building

Recorded 2026-08-18, after the fact, as support rather than justification:

- E3 was first computed at the wrong horizon and the wrong offset, because a summary block was
  read instead of the declared question. The ledger caught it — but only because someone went
  and looked. A layer that prints *"3488b1e1 asks about the touch at 60 s"* beside the
  outstanding list catches it in one line.
- `market/evidence/q3-recording.checkpoint` recorded 3,673 events against an actual 580,658 for
  a week, with nothing announcing the drift.
- `health.py` — the documented integrity check — read nothing and exited 0 for months.

Each is a status claim the available evidence did not support. That is the failure this
project keeps finding, and it is the one the reporting half is aimed at.

## What was given up

A system that prompts itself, chooses its next question, and fetches what it needs without
being asked. That was the fuller version discussed on 2026-08-13, and it is deliberately not
built. The cost is that a human remains in the loop for every declaration. That cost **is the
feature**, per reason 2.

## What this does not decide

Nothing about market direction, no research question, no reopening of DR0002, and no
commitment to Phase 5 agents. It authorises one read-only reporting tool and its scope.
