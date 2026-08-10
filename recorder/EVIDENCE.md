# Evidence

Raw recorder logs are large — 92 MB for BAV-1's three runs — and they are append-only
hash-chained files. Committing them would bloat the repository to preserve a property the
chain already provides.

**What is committed:** the checkpoint sidecar and the derived report for every run, plus the
SHA-256 of the raw log below.
**What is archived outside the repository:** the raw logs, at `~/genesis-evidence/`.

The committed checkpoint records the chain head. Any modification to an archived log —
insertion, deletion, truncation, or an edited byte — breaks the chain and fails verification
against it. That is what the chain was built for, and it is the reason splitting evidence this
way loses nothing.

**Nothing is deleted.** Failed runs are archived exactly like successful ones; runs 1 and 2 of
BAV-1 failed to answer the pre-registered question and are the most instructive records the
project holds.

## Verifying an archived log

```sh
shasum -a 256 ~/genesis-evidence/bav-1/bav3.jsonl     # compare with the digest below
.venv/bin/python recorder/health.py ~/genesis-evidence/bav-1/bav3.jsonl
```

`health.py` re-derives the chain and reports `integrity_verified`. The digest catches
substitution of the whole file; the chain catches everything inside it.

---

## BAV-1 — Book Agreement Validation, 2026-08-10

Contract `sha256 4b71c2a6272dbf8306b506f1661684e7c0813fe7ab7b9df6ca64e430dc06b530`,
byte-identical across all three runs.
Record: [`../research/experiments/0007-bav-1-book-agreement-validation.md`](../research/experiments/0007-bav-1-book-agreement-validation.md).

| Run | Log SHA-256 | Size | Outcome |
|---|---|---|---|
| 1 | `4972cb5db3845584a3300cec1de396bff2332024107d3473809ff498c3fc015b` | 32.7 MB | Question B unanswerable — defects D-A, D-B |
| 2 | `72d048f859fa793f8694ab2f0e1b2c02ddf59de50d8f53f4971354b8c45fc140` | 32.6 MB | Question B unanswerable — defect D-C |
| 3 | `9926ac199484ea97f718bb7550ce14e4dbc81b3865ced60605d5da7a9fce4bc9` | 30.7 MB | **Question B answered** — p = 0.0165 in the pre-registered stratum |

Archive location: `~/genesis-evidence/bav-1/`.
Committed alongside: `evidence/bav-1/bav{1,2,3}.jsonl.checkpoint`,
`evidence/bav-1/bav{1,2,3}_report.json`.

The archive is on one machine. It is not backed up, and that is a known and accepted gap —
the derived reports and the integrity record are what the project's claims rest on, and those
are in git.
