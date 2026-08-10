"""
The trial ledger. Every statistical test Genesis runs is counted here, before it is run.

WHY THIS EXISTS, AND WHY NOW
    Two hundred tests produce several brilliant-looking accidents. The only defence is an
    honest count of how many were run -- and a count assembled after the searching has begun
    is a fiction, because by then the tests that were quietly abandoned are unrecoverable.
    This is built before any hypothesis search starts, which is the only moment at which it
    can be built credibly.

TWO PHASES, AND THE REASON FOR THEM
    `declare()` is called BEFORE a test is run and writes an immutable record of the intent.
    `record()` is called after, with the outcome. A declared trial with no result stays visible
    forever as OUTSTANDING.

    This is the whole anti-gaming mechanism. Without it, the natural failure is to run twenty
    tests, report the two that worked, and count two. Here, running twenty means twenty
    declarations exist, and the eighteen abandoned ones are as permanent as the two reported.
    You cannot un-declare.

WHY THE HASH-CHAINED LOG
    A trial counter that can be quietly edited is worth nothing at all. This reuses the
    recorder's append-only hash-chained EventLog, so any deletion or alteration of a past
    declaration breaks the chain and fails `verify`. The tamper-evidence machinery already
    exists and this is exactly what it is for.

WHAT COUNTS AS A TRIAL
    Any test that could have produced a number Genesis might act on: a hypothesis test, a
    fitted model evaluated on data, a threshold comparison, a strategy backtest. Descriptive
    statistics with no accept/reject decision are not trials, and are recorded as CONTEXT so
    that the boundary itself is auditable rather than remembered.

REFERENCES
    Bailey, D. & Lopez de Prado, M. (2014). The deflated Sharpe ratio: correcting for selection
        bias, backtest overfitting and non-normality. Journal of Portfolio Management 40(5).
    Benjamini, Y. & Hochberg, Y. (1995). Controlling the false discovery rate. JRSS-B 57(1).
"""

import math
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

from events import CLASSES  # noqa: E402
from log import EventLog, read, verify  # noqa: E402

DEFAULT_PATH = os.path.expanduser("~/genesis-evidence/ledger/trials.jsonl")

RESEARCH = "RESEARCH"
DECLARED, RESULT, CONTEXT = "TRIAL_DECLARED", "TRIAL_RESULT", "CONTEXT"
EULER = 0.5772156649015329


class Ledger:
    """
    Append-only trial record. Open it, declare, run, record.

    Nothing here decides whether a result is real. It counts, and it makes the count
    impossible to revise downward.
    """

    def __init__(self, path=DEFAULT_PATH):
        self.path = path
        self._log = None

    def __enter__(self):
        self._log = EventLog(self.path, classes=CLASSES + (RESEARCH,)).__enter__()
        return self

    def __exit__(self, *exc):
        return self._log.__exit__(*exc)

    # ---- writing -----------------------------------------------------------------------

    def declare(self, family, question, method, data, preregistered, contract=None,
                notes=None):
        """
        Record the intent to run one test. Call this BEFORE running it.

        `family` groups tests that share a multiple-comparison correction -- the set you would
        have been equally happy to find an effect in. Getting the family wrong is how a
        corrected p-value becomes decorative, so it is required and never inferred.

        `preregistered` is False for anything decided after seeing data. It is not a
        judgement of quality; an honest exploratory trial is fine, and an exploratory trial
        mislabelled as pre-registered is not.
        """
        if not family or not question or not method:
            raise ValueError("family, question and method are all required")
        trial_id = str(uuid.uuid4())[:8]
        self._log.append(RESEARCH, DECLARED, {
            "trial_id": trial_id, "family": family, "question": question, "method": method,
            "data": data, "preregistered": bool(preregistered), "contract": contract,
            "notes": notes})
        return trial_id

    def record(self, trial_id, statistic=None, p_value=None, effect=None, n=None,
               conclusion=None, notes=None):
        """Record the outcome of a declared trial. A trial may be recorded only once."""
        seen = {t["trial_id"] for t in self.results()}
        if trial_id in seen:
            raise ValueError(f"trial {trial_id} already has a result; the ledger is append-only")
        if trial_id not in {t["trial_id"] for t in self.declarations()}:
            raise ValueError(f"trial {trial_id} was never declared")
        self._log.append(RESEARCH, RESULT, {
            "trial_id": trial_id, "statistic": statistic, "p_value": p_value,
            "effect": effect, "n": n, "conclusion": conclusion, "notes": notes})

    def context(self, description, notes=None):
        """A descriptive measurement with no accept/reject decision. Not a trial."""
        self._log.append(RESEARCH, CONTEXT, {"description": description, "notes": notes})

    # ---- reading -----------------------------------------------------------------------

    def _bodies(self, kind):
        if not os.path.exists(self.path):
            return []
        return [ev["body"] for ev in read(self.path) if ev.get("event_type") == kind]

    def declarations(self, family=None):
        d = self._bodies(DECLARED)
        return [t for t in d if family is None or t["family"] == family]

    def results(self):
        return self._bodies(RESULT)

    def outstanding(self, family=None):
        """
        Declared but never recorded. These are the trials an honest count must not lose --
        the abandoned ones are exactly what selection bias is made of.
        """
        done = {t["trial_id"] for t in self.results()}
        return [t for t in self.declarations(family) if t["trial_id"] not in done]

    def count(self, family=None):
        return len(self.declarations(family))

    def summary(self, family=None):
        res = {t["trial_id"]: t for t in self.results()}
        decl = self.declarations(family)
        ps = [res[t["trial_id"]]["p_value"] for t in decl
              if t["trial_id"] in res and res[t["trial_id"]].get("p_value") is not None]
        return {
            "family": family or "ALL",
            "declared": len(decl),
            "recorded": sum(1 for t in decl if t["trial_id"] in res),
            "outstanding": len(self.outstanding(family)),
            "preregistered": sum(1 for t in decl if t["preregistered"]),
            "exploratory": sum(1 for t in decl if not t["preregistered"]),
            "p_values": sorted(ps),
            "bonferroni_alpha": 0.05 / len(decl) if decl else None,
            "survives_bonferroni": [p for p in ps if decl and p < 0.05 / len(decl)],
            "survives_bh": benjamini_hochberg(ps),
        }

    def verify(self):
        """
        Chain and checkpoint integrity. A ledger that cannot be verified is not evidence.
        Returns {"ok": bool, "problems": [...]}.
        """
        ok, problems = verify(self.path)
        return {"ok": ok, "problems": problems}


# ---- multiple-comparison machinery ------------------------------------------------------

def benjamini_hochberg(p_values, alpha=0.05):
    """
    Benjamini-Hochberg (1995). Returns the p-values that survive at FDR = alpha.

    Controls the expected proportion of false discoveries rather than the probability of any
    -- less brutal than Bonferroni when the family is large, which is the realistic case once
    a search begins.
    """
    ps = sorted(p for p in p_values if p is not None)
    m = len(ps)
    if not m:
        return []
    k = 0
    for i, p in enumerate(ps, start=1):
        if p <= alpha * i / m:
            k = i
    return ps[:k]


def expected_max_sharpe(n_trials, var_sr=1.0):
    """
    Expected maximum Sharpe under the null of zero true skill, across `n_trials` independent
    trials (Bailey & Lopez de Prado 2014). This is the bar a selected strategy must clear
    merely to be uninteresting -- it rises with the number of things tried.
    """
    if n_trials < 2:
        return 0.0
    e = math.sqrt(var_sr)
    a = _norm_ppf(1 - 1.0 / n_trials)
    b = _norm_ppf(1 - 1.0 / (n_trials * math.e))
    return e * ((1 - EULER) * a + EULER * b)


def deflated_sharpe(sr, n_trials, n_obs, skew=0.0, kurtosis=3.0, var_sr=1.0):
    """
    Deflated Sharpe ratio: the probability the observed Sharpe reflects real skill once the
    number of trials, the sample length, and non-normal returns are accounted for.

    Returns a probability. Below ~0.95 the result is not distinguishable from the best of
    `n_trials` coin flips.
    """
    sr0 = expected_max_sharpe(n_trials, var_sr)
    denom = 1.0 - skew * sr + (kurtosis - 1.0) / 4.0 * sr ** 2
    if denom <= 0 or n_obs < 2:
        return float("nan")
    z = (sr - sr0) * math.sqrt(n_obs - 1) / math.sqrt(denom)
    return _norm_cdf(z)


def _norm_cdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def _norm_ppf(p):
    """Acklam's rational approximation; accurate to ~1e-9, which is far beyond what is needed."""
    if not 0 < p < 1:
        raise ValueError(f"p must be in (0,1), got {p}")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > ph:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
