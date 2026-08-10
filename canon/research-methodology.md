# Research Methodology

> **Type 1 · Research** — authored by the researchers. Claude maintains form only:
> proofreading, formatting, links. See [`../ai/collaboration.md`](../ai/collaboration.md).

## How Genesis Discovers Understanding

---

## Purpose

Genesis is a research program before it is an engineering project.

This document defines how Genesis acquires, evaluates, challenges, and preserves understanding.

Its purpose is not to accelerate implementation. Its purpose is to improve the quality of the ideas that eventually become implementation.

Every significant concept in Genesis should be traceable through this methodology.

---

## First Principles

### Reality Is The Final Authority

No idea becomes part of Genesis because it is elegant, persuasive, or intuitively appealing.

Reality has the final vote.

The role of research is to progressively reduce the distance between our internal models and the reality they attempt to describe.

Whenever reality contradicts our assumptions, reality wins.

---

### Understanding Before Implementation

Implementation is not discovery.

Code expresses understanding; it does not create it.

The purpose of engineering is to make explicit what research has already justified.

Whenever implementation exposes flaws in our understanding, research resumes.

---

### Every Claim Begins As Uncertainty

Genesis treats uncertainty as the natural starting point of inquiry.

Ideas are welcomed.

Beliefs are earned.

Confidence is accumulated.

Certainty is approached cautiously and always remains open to revision.

---

### The Goal Is Better Understanding

The objective of research is not to defend existing ideas.

The objective is to improve the quality of our understanding.

Sometimes this strengthens existing beliefs.

Sometimes it replaces them entirely.

Both outcomes represent progress.

---

### Architectural Compression Principle

When new phenomena are discovered, prefer explanations that derive them from existing primitives before introducing new primitives.

New primitives require demonstrating that no composition of existing primitives explains the phenomenon.

---

### Rediscovery Is Not Discovery

Before Genesis builds a laboratory around a capability, it identifies the established literature and asks whether the capability is already solved. If it is, Genesis imports it, names the prior art, implements the minimum needed as a dependency, and moves on.

First-principles derivation remains valuable for understanding, verification, and exposing hidden assumptions. But independently re-deriving established science is not research progress, and Genesis does not count it as a discovery.

**Source:** [`../research/prior-art-and-opportunity-map.md`](../research/prior-art-and-opportunity-map.md).

#### Standing on existing knowledge

The paragraphs above state when Genesis must *not* build a laboratory. This states how Genesis
is built.

> **Before reinventing a capability, Genesis should determine whether established knowledge
> already provides a suitable solution. If it does, Genesis should understand it, verify its
> applicability, and use it. If it does not, then developing or adapting something new remains
> possible. Novelty is not the objective; reliable capability is.**

Importing is not a concession or a fallback. It is the ordinary path. A capability Genesis
obtains from Kalman, from Bayes, or from a working library is worth exactly what one it derived
alone is worth, and more if the derivation would have cost time the project does not have. Who
reached a result first has no bearing on whether Genesis may build with it.

The rule is not "never invent". It is: do not spend effort rediscovering what is already known
when that knowledge can move Genesis forward. When the established work genuinely does not
cover the problem, building something new is legitimate, and the prior-art review is what
establishes that it does not.

**Genesis does not need to reinvent knowledge in order to build something new with it.**

#### Existing knowledge is a resource, not an authority

Importing is not deference. **Established does not mean automatically applicable.** A method
that has been found is not yet a method that works here. Five distinct steps lie between the
two, and skipping any of them turns "use prior art" into "trust whatever we found":

1. Find the established method.
2. Understand what it actually claims, rather than what it is reputed to claim.
3. Understand its assumptions and its stated limitations.
4. Determine whether those assumptions hold in Genesis's environment.
5. Test whether it actually works there, and record what the evidence says.

Step 5 is not optional, and its failure is informative rather than embarrassing. RDB-1 imported
a standard state-space model correctly and found it no better than persistence. That is a
result about the environment, not a defect in the import.

Where verification is the purpose, the classification is **Replication**. Where implementation
is the purpose, it is **Import** or **Engineering validation**. Those distinctions stand
unchanged.

#### What DR0002 retired, and what it did not

> **[`0002`](../research/decisions/0002-close-the-genesis-research-program.md) retired the
> claim that Genesis was discovering novel cognitive principles. It did not retire the use of
> established methods that may contribute to Genesis's capabilities.**

DR0002 did not mean "if someone has already discovered it, Genesis should not use it". It meant
that Genesis should not mistake independently rediscovering established science for discovering
something novel.

The constructive interpretation is the one intended: if someone has already solved part of a
problem, Genesis should be capable of finding that work, understanding it, verifying that it
applies, and building on it.

Belief states, recursive Bayesian updating, observation-model learning, filtering and
closed-loop agency remain available and may be used where they help. What DR0002 retired was
the claim that independently deriving such established methods constituted a novel
cognitive-architecture discovery by Genesis. **The methods were not rejected. The novelty claim
was rejected.**

#### Future direction: knowing what it needs to know

**Direction, not requirement.** Nothing in this subsection is to be implemented now, and no
autonomous research agent or literature-search system is being specified.

The capability intended here is broader than searching for papers. As Genesis develops, it
should become better at moving through a sequence of questions:

```
"I don't know how to solve this."
        |
"What exactly do I need to know, or be able to do?"
        |
"Has this already been solved somewhere?"
        |
"What existing knowledge, methods, mathematics, algorithms, experiments
 or engineering techniques could help?"
        |
"Do they actually apply to my environment?"
        |
test, adapt, retain, reject, or revise
```

**Recognising what must be known is itself part of knowing better.**

Today this sequence runs across the researchers, the AI collaborator, and this record. Whether
any part of it should eventually be performed by Genesis itself is an open design question, not
a commitment.

> Genesis does not need to discover everything itself. It needs to become increasingly good at
> figuring out what it needs, finding what humanity already knows, understanding the limits of
> that knowledge, testing whether it applies, and then building on it.

#### The research gate (mandatory)

Before any proposed laboratory enters the roadmap, perform a prior-art check and classify it:

1. **Import** — established result; use existing literature/machinery.
2. **Engineering validation** — implementation needed for Genesis; no research novelty claimed.
3. **Replication** — independently reproduce an established result for verification.
4. **Open question** — established literature does not settle the specific question.
5. **Potentially novel** — a concrete difference from prior art identified; still needs verification.
6. **Philosophical / open-ended** — unresolved, but not necessarily an engineering research target.

A laboratory cannot be justified merely because Genesis has not derived the capability before. If the prior-art review closes the question, that is a successful research outcome — do not manufacture a laboratory to preserve the roadmap. The sequence for any proposed lab is:
**prior art → unresolved gap → why Genesis is positioned to investigate → falsifiable question → smallest discriminating experiment.**

---

## The Lifecycle of Knowledge

Every meaningful concept within Genesis progresses through distinct stages.

### 1. Observation

Research begins with careful observation.

Observations may come from:

- experiments,
- literature,
- markets,
- software,
- cognitive science,
- philosophy,
- mathematics,
- conversations,
- failures,
- or any interaction with reality.

At this stage no explanation is assumed.

Only the phenomenon is recorded.

---

### 2. Question

Every observation should produce questions before it produces conclusions.

Good questions reduce ambiguity.

Poor questions prematurely narrow investigation.

Genesis values the quality of questions as highly as the quality of answers.

---

### 3. Hypothesis

A hypothesis proposes an explanation.

It is not treated as truth.

Every hypothesis should clearly state:

- the claim,
- the reasoning behind it,
- what evidence would support it,
- what evidence would weaken it,
- what evidence would falsify it.

A hypothesis that cannot, even in principle, be challenged provides little research value.

For a deeper discussion of what makes a hypothesis scientifically useful — including
challengeability, uncertainty reduction, and scope — see
[`research/explorations/what-makes-a-good-hypothesis.md`](../research/explorations/what-makes-a-good-hypothesis.md).

---

### 4. Experiment

Ideas become useful only after interacting with reality.

Experiments may take many forms:

- software prototypes,
- simulations,
- historical analysis,
- paper trading,
- literature comparison,
- thought experiments,
- peer critique,
- implementation attempts.

The purpose is not confirmation.

The purpose is learning.

---

### 5. Evidence

Evidence modifies confidence.

Evidence should always be distinguished from interpretation.

Genesis records both.

Strong evidence increases confidence.

Contradictory evidence is preserved rather than discarded.

Unexpected outcomes often become the beginning of better questions.

---

### 6. Reflection

Research is incomplete without reflection.

Reflection asks:

- What did we learn?
- What assumptions were hidden?
- What surprised us?
- What remains unexplained?
- What new questions emerged?

Reflection transforms experiments into understanding.

---

### 7. Decision

Only after repeated reflection should significant ideas become decisions.

Every important decision should be recorded with:

- context,
- alternatives considered,
- reasoning,
- consequences,
- future review conditions.

Decisions remain revisable.

---

### 8. Canon

Only mature ideas enter the Canon.

The Canon represents Genesis' current best understanding.

It does not represent absolute truth.

Every canonical concept remains open to future revision through this same methodology.

---

## The Epistemic Lifecycle

Canon, Hypotheses, Experiments, and Decisions are often treated as folders.

They are not merely folders.

They are stages in the evolution of a claim's relationship to evidence.

The Canon asks what we currently believe.

The Hypotheses ask what we are trying to discover.

The Experiments ask what happened when reality answered.

The Decisions ask what changed because of that.

A claim does not skip these stages.

It cannot enter the Canon without having first been at risk as a Hypothesis.

It cannot become a Decision without having first been tested.

This is the epistemic lifecycle through which every claim in Genesis must pass before it is trusted.

---

## Confidence

Genesis distinguishes confidence from certainty.

Confidence should increase only when supported by evidence accumulated across multiple observations or experiments.

Confidence should decrease when evidence weakens a model.

The inability to revise confidence is considered a failure of learning.

---

## Failure

Failure is information.

Failed experiments are preserved because they define the boundaries of understanding.

Deleting failures destroys part of the reasoning process that produced later insight.

Genesis values unsuccessful experiments that improve understanding more than successful experiments whose success cannot be explained.

---

## Disagreement

Disagreement is an essential component of research.

Ideas should encounter thoughtful challenge before they encounter implementation.

The objective is not debate for its own sake.

The objective is refinement.

A belief that survives meaningful criticism becomes more trustworthy than one that never faced opposition.

---

## Time

Research unfolds across multiple timescales.

Some ideas can be evaluated quickly.

Others require months or years before sufficient evidence exists.

Genesis resists artificial deadlines that force premature conclusions.

The pace of understanding should be determined by the quality of evidence rather than by the desire for progress.

---

## Provenance

Every significant concept should preserve its intellectual history.

Future contributors should be able to understand:

- where an idea originated,
- how it evolved,
- what alternatives were considered,
- why competing explanations were rejected,
- and what evidence justified its current form.

Understanding without provenance is fragile.

---

## Artificial Intelligence Within The Research Process

AI collaborators participate as research assistants and engineering partners.

They may:

- organize knowledge,
- identify inconsistencies,
- summarize literature,
- suggest experiments,
- challenge assumptions,
- improve clarity,
- implement approved designs.

They do not determine the philosophical direction of Genesis.

They contribute to discovery but do not define the Canon.

---

## The Research Culture

Genesis values:

- curiosity over certainty,
- evidence over intuition,
- revision over attachment,
- clarity over complexity,
- understanding over output,
- long-term coherence over short-term speed.

The quality of Genesis will ultimately depend less on the intelligence of any individual contributor and more on the discipline of the research process that guides them all.

---

## Closing Principle

Every document, experiment, implementation, and discussion within Genesis should leave the project with a better understanding than it possessed before.

If our understanding has not improved, then regardless of how much work was completed, the research is unfinished.
