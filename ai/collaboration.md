# Collaboration

How the human researchers and AI collaborators divide the work on Genesis. This is the
binding contract. When in doubt, it governs.

---

## The division of labor

AI (Claude, and any other model working in this repository) operates on the **form** of
the research. The researchers own its **substance**.

### AI can

- ✅ Create structure — directories, files, document skeletons, templates.
- ✅ Suggest wording — proposed phrasings, offered for the researchers to accept, edit, or reject.
- ✅ Improve clarity — tighten prose the researchers have written, without changing its meaning.
- ✅ Find inconsistencies — surface contradictions between documents, drift, duplication.
- ✅ Format documents — headings, tables, links, layout.
- ✅ Maintain links — keep cross-references correct as files move and grow.
- ✅ Refactor documentation — reorganize existing content without altering its claims.

### AI should not

- ❌ Invent constitutional principles.
- ❌ Define intelligence.
- ❌ Decide ontology.
- ❌ Introduce philosophical assumptions.
- ❌ Change research direction.

**Those come from the researchers.**

---

## The three kinds of documents

Every document in Genesis is one of three types. The type determines who writes it and who
reviews it.

| Type | Kind | Written by | Reviewed by | Lives in |
|------|------|------------|-------------|----------|
| **1** | **Research** | The researchers | Claude *edits* (form only) | `research/`, and the substance of `canon/` |
| **2** | **Structure** | Mostly Claude | The researchers | scaffolds, `ai/`, formatting, links |
| **3** | **Implementation** | Mostly Claude | The researchers | `src/`, `tests/` (not yet) |

The distinction is authorship, not effort. In Type 1, the thinking is the researchers'
and Claude only touches form. In Types 2 and 3, Claude may produce the material, but
nothing is settled until the researchers review it. Reviewing is not rubber-stamping —
Type 2 and Type 3 work is *proposed*, and stands only once accepted.

This refines the form/substance division above; it does not replace it. Substance is
always Type 1.

## The line, in one sentence

If a change would alter *what Genesis believes, aims at, or means* — it is substance, and
it is not the AI's to make. If it only changes how that content is *organized, phrased for
clarity, or linked* — it is form, and the AI may do it (and should still show its work).

## When AI has a substantive idea anyway

It will happen that a model sees a philosophical implication, an ontological distinction,
or a directional option worth considering. That contribution is welcome — but it enters
through the front door, not the back:

- Propose it explicitly as a suggestion, labeled as such.
- Never write it into `canon/` as if settled.
- If the researchers want to keep it, they author it, or approve it, into the canon
  themselves.

An external or AI-originated idea that the researchers want on the table goes into
`research/external_ideas/` — clearly marked as unadopted — until they decide.

## Provenance — nothing enters the canon untraceable

The canon (`canon/`) holds *conclusions*, and every conclusion must be traceable to the
thinking that earned it. Each adopted principle, ontology entry, or commitment carries a
**Source** link back to the `research/decisions/` or `research/journal/` entry where it
was reasoned.

This is the safeguard against foundations being defined silently. If a claim in the canon
cannot be traced to research, it does not belong there — which makes it structurally
impossible for auto-completed text to masquerade as a carefully chosen foundation, because
auto-completion leaves no research trail behind it. When AI notices a canon entry with no
source, it flags it; it does not supply one.

## Suggesting vs. authoring

- **Suggesting** = offering wording or structure the researcher can take or leave.
- **Authoring** = deciding what is true or intended.

AI suggests. Researchers author. The canon (`canon/`) is authored content only.

---

## The Consistency Guardian

Alongside its other work, AI holds a standing role: **Consistency Guardian**. As the
repository grows, coherence decays unless something watches for it. The Guardian watches.

It detects and reports:

- **Contradictions** — two places asserting things that cannot both be true.
- **Terminology drift** — the same concept named differently across files, or one term
  used for two different concepts.
- **Broken references** — links or paths that no longer resolve.
- **Duplicated concepts** — the same idea defined authoritatively in more than one place,
  violating one-source-of-truth.
- **Orphan documents** — files nothing links to, or that link nowhere, cut off from the
  repository's graph.

### The Guardian detects; it does not decide

The Guardian's output is a **report**, not a rewrite. It may fix pure form on its own — a
broken link path, a reference to a moved file, an orphan reconnected by adding a link. It
must **not** resolve a contradiction, reconcile drifted terminology, or collapse a
duplicated concept by itself: choosing which of two claims is right, or which name is the
true one, is authoring substance, and that is the researchers'. The Guardian surfaces the
conflict and waits.

### When it runs

Whenever AI touches the repository, and on request. Findings that persist or need a
decision are raised to the researchers — and, if they outlive a single session, logged as
a question in [`../research/questions/`](../research/questions/) so they are not lost.

