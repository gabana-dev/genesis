"""
Milestone 2 — sparse observations: does maintaining a belief change what the agent DOES?

Milestone 1 established integration validity (the closed loop tracks a state the agent is
itself moving) and found NO behavioral advantage: an observation arrived every step, so the
freshest reading was always an adequate decision input. M2 removes exactly that sufficiency
condition and nothing else.

CONTRACT (pre-registered before the run — research/experiments/0005-...md):
  A. PRIMARY, behavioral: declaration accuracy of the belief agent vs the STALE-OBSERVATION
     agent, paired, with 95% CI. Margin ~0 at p=1 (M1 replication control), growing with the
     observation period p. Monotonicity is predicted of the MECHANISM, not required of finite
     samples; intervals are reported and no result is called monotonic if it is not.
  B. SECONDARY, mechanism: posterior on the true position and MAP error bucketed by gap age
     (steps since last observation), full filter vs the frozen-belief ablation.
  C. Wall contamination, threshold fixed in advance: a condition is CONTAMINATED (primary
     comparison inconclusive) if >25% of any agent's correct declarations were clamp-assisted.

  All four agents run the IDENTICAL policy pi(p_hat). Only the state estimate differs, so any
  behavioral difference is attributable to the estimate and nothing else:
    belief  — action-conditioned filter, Predict every step (the capability under test)
    stale   — last observation, held through the gap (LOAD-BEARING baseline: memory, no
              propagation, which is what isolates Predict from "having memory at all")
    null    — acts only on observation steps, holds still otherwise (weak reference)
    frozen  — Update on observations, no Predict (ablation, for B)

  The agent owns termination: the environment does NOT detect arrival. Auto-termination would
  hand every agent an oracle arrival signal and destroy the discrimination being measured.

  IMPORT: filtering under intermittent observations (Sinopoli et al. 2004; POMDP with null
  observations; dead reckoning between fixes, Thrun-Burgard-Fox 2005). BUILD: this harness.
  No research component, no novelty claim.

  s=0 is the primary condition. There the predicted belief is analytically exact during a gap,
  so it is a clean demonstration of the decision mechanism, not a difficult research test.
  s=0.1 is secondary: does the advantage survive when the belief is genuinely uncertain?

Standard library only. Run: python3 src/sparse_loop.py
"""

import math
import random

K = 7
TARGET = 3
MAX_STEPS = 40
STOP = "stop"


def clamp(i):
    return max(0, min(K - 1, i))


def policy(p_hat):
    """The one policy every agent runs. Only p_hat differs between agents."""
    if p_hat < TARGET:
        return 1
    if p_hat > TARGET:
        return -1
    return STOP


def likelihood(cell, obs, noise):
    return (1 - noise) if obs == cell else noise / (K - 1)


def update(belief, obs, noise):
    post = [belief[c] * likelihood(c, obs, noise) for c in range(K)]
    z = sum(post)
    return [p / z for p in post]


def predict(belief, action, slip):
    """Action-conditioned motion model, including the known slip probability."""
    nb = [0.0] * K
    for c in range(K):
        nb[clamp(c + action)] += belief[c] * (1 - slip)
        nb[c] += belief[c] * slip
    return nb


def map_pos(belief):
    return max(range(K), key=lambda c: belief[c])


class Draws:
    """Per-episode randomness, shared across all agents (common random numbers).

    Pre-generated so that every agent faces the same start, the same sensor coins and the same
    slip coins at the same step index. Without this the comparison is unpaired and the
    difference estimates are inflated or masked by sampling noise.
    """

    def __init__(self, rng):
        self.start = rng.choice([c for c in range(K) if c != TARGET])
        self.obs_coin = [rng.random() for _ in range(MAX_STEPS)]
        self.alt_pick = [rng.random() for _ in range(MAX_STEPS)]
        self.slip_coin = [rng.random() for _ in range(MAX_STEPS)]

    def observe(self, pos, t, noise):
        if self.obs_coin[t] < 1 - noise:
            return pos
        others = [c for c in range(K) if c != pos]
        return others[int(self.alt_pick[t] * (K - 1))]


def run_episode(agent, draws, noise, period, slip):
    pos = draws.start
    belief = [1.0 / K] * K
    last_obs = None
    declared_at = None
    clamped = False
    quality = []                       # (gap_age, posterior at true pos, |MAP - true|)
    last_obs_step = 0

    for t in range(MAX_STEPS):
        observed = (t % period == 0)
        obs = draws.observe(pos, t, noise) if observed else None
        if observed:
            last_obs = obs
            last_obs_step = t

        if agent == "stale":
            p_hat = last_obs
        elif agent == "null":
            p_hat = obs if observed else None
        else:                          # belief | frozen
            if observed:
                belief = update(belief, obs, noise)
            p_hat = map_pos(belief)
            quality.append((t - last_obs_step, belief[pos], abs(p_hat - pos)))

        action = 0 if p_hat is None else policy(p_hat)

        if action == STOP:
            declared_at = t
            break

        if action != 0:
            nxt = pos if draws.slip_coin[t] < slip else clamp(pos + action)
            if clamp(pos + action) == pos:
                clamped = True
            pos = nxt

        if agent == "belief":
            belief = predict(belief, action, slip)

    declared = declared_at is not None
    return {
        "declared": declared,
        "correct": declared and pos == TARGET,
        "steps": declared_at if declared else MAX_STEPS,
        "miss_distance": abs(pos - TARGET) if declared else None,
        "clamped": clamped,
        "quality": quality,
    }


AGENTS = ("belief", "stale", "null", "frozen")


def run_condition(episodes, noise, period, slip, seed):
    per_agent = {a: {"correct": 0, "declared": 0, "steps": 0, "miss": 0,
                     "clamp_correct": 0, "tp": 0.0, "me": 0.0, "n_q": 0,
                     "by_gap": {}} for a in AGENTS}
    paired = []                        # belief - stale, per episode

    for i in range(episodes):
        draws = Draws(random.Random(f"{seed}:{i}"))
        results = {a: run_episode(a, draws, noise, period, slip) for a in AGENTS}
        for a, r in results.items():
            s = per_agent[a]
            s["correct"] += r["correct"]
            s["declared"] += r["declared"]
            s["steps"] += r["steps"]
            s["miss"] += r["miss_distance"] or 0
            if r["correct"] and r["clamped"]:
                s["clamp_correct"] += 1
            for gap, tp, me in r["quality"]:
                s["tp"] += tp
                s["me"] += me
                s["n_q"] += 1
                b = s["by_gap"].setdefault(gap, [0.0, 0.0, 0])
                b[0] += tp
                b[1] += me
                b[2] += 1
        paired.append(results["belief"]["correct"] - results["stale"]["correct"])

    out = {}
    for a, s in per_agent.items():
        out[a] = {
            "accuracy": s["correct"] / episodes,
            "declared_rate": s["declared"] / episodes,
            "avg_steps": s["steps"] / episodes,
            "avg_miss": s["miss"] / episodes,
            # share of this agent's CORRECT declarations that were clamp-assisted
            "clamp_share": (s["clamp_correct"] / s["correct"]) if s["correct"] else 0.0,
            "true_post": (s["tp"] / s["n_q"]) if s["n_q"] else None,
            "map_err": (s["me"] / s["n_q"]) if s["n_q"] else None,
            "by_gap": {g: (v[0] / v[2], v[1] / v[2]) for g, v in sorted(s["by_gap"].items())},
        }

    mean = sum(paired) / episodes
    var = sum((d - mean) ** 2 for d in paired) / (episodes - 1)
    half = 1.96 * math.sqrt(var / episodes)
    out["paired_belief_minus_stale"] = (mean, mean - half, mean + half)
    out["contaminated"] = any(out[a]["clamp_share"] > 0.25 for a in AGENTS)
    return out


def report(episodes=3000, seed=7):
    print("Milestone 2 -- sparse observations (K=7, target=3, max_steps=40, "
          f"{episodes} episodes/condition, agent-declared STOP)")
    for slip in (0.0, 0.1):
        label = "PRIMARY (deterministic -- clean demonstration)" if slip == 0 else \
                "SECONDARY (action slip 0.1 -- belief genuinely uncertain)"
        print(f"\n================ {label} ================")
        for noise in (0.2, 0.5):
            print(f"\nnoise = {noise}")
            print("  p | belief | stale  | null   | frozen |  paired belief-stale [95% CI]"
                  " | clamp-share(max) | contam")
            for period in (1, 2, 3, 5):
                r = run_condition(episodes, noise, period, slip, seed)
                m, lo, hi = r["paired_belief_minus_stale"]
                cmax = max(r[a]["clamp_share"] for a in AGENTS)
                print(f"  {period} |  {r['belief']['accuracy']:.3f} |  {r['stale']['accuracy']:.3f} "
                      f"|  {r['null']['accuracy']:.3f} |  {r['frozen']['accuracy']:.3f} "
                      f"|  {m:+.3f} [{lo:+.3f}, {hi:+.3f}] |      {cmax:.3f}      "
                      f"| {'YES' if r['contaminated'] else 'no'}")

    print("\n\n================ B. MECHANISM: belief quality by gap age ================")
    print("(full filter vs frozen-belief ablation; posterior on the true cell / MAP error)")
    for slip in (0.0, 0.1):
        for noise in (0.2, 0.5):
            for period in (3, 5):
                r = run_condition(episodes, noise, period, slip, seed)
                print(f"\nslip={slip} noise={noise} p={period}")
                for gap in sorted(r["belief"]["by_gap"]):
                    btp, bme = r["belief"]["by_gap"][gap]
                    ftp, fme = r["frozen"]["by_gap"].get(gap, (float('nan'), float('nan')))
                    print(f"  gap {gap}: belief {btp:.3f}/{bme:.3f}   frozen {ftp:.3f}/{fme:.3f}")

    print("\n\n================ Diagnostics (declaration behavior) ================")
    for slip in (0.0, 0.1):
        for noise in (0.2, 0.5):
            for period in (1, 5):
                r = run_condition(episodes, noise, period, slip, seed)
                print(f"\nslip={slip} noise={noise} p={period}")
                for a in AGENTS:
                    s = r[a]
                    print(f"  {a:7s}: acc {s['accuracy']:.3f}  declared {s['declared_rate']:.3f}"
                          f"  steps {s['avg_steps']:.2f}  avg-miss {s['avg_miss']:.3f}"
                          f"  clamp-share {s['clamp_share']:.3f}")


if __name__ == "__main__":
    report()
