"""
Genesis Laboratory 3 -- the first introduction of CHOICE over information.

Experimental contract (pre-registered):

  Hypothesis: observation selection -- the agent choosing which channel to receive
    next -- can be expressed using only the earned machinery (belief-state + Update +
    reads), or agency exposes a genuinely new operation.

  Interpretations (binding, not to be retrofitted):
    I1  pure-read suffices: selection expressible as a function of the current belief.
    I2  simulation necessary: selection needs reapplied Update on imagined observations.
    I3  neither suffices: a genuinely new mechanism is required (candidate 3rd primitive).

  Environment: static hidden state = 2 bits (b1, b2), uniform per episode.
    Channel A observes b1 with noise.
    Channel B observes b1 XOR b2 with the SAME noise (the intended entanglement).
    Budget of N single-channel observations, then guess the joint (b1, b2).

  Agents (identical except the channel-selection policy):
    passive     -- random channel.
    pure_read   -- rank channels by the marginal entropy of their target under the
                   current belief (a pure read; no imagined observations).
    simulation  -- rank channels by expected posterior entropy, computed by applying
                   Update to imagined observations (== the one-step optimum / oracle).

  Controls: identical prior, channel models, Update, budget, hidden-state distribution;
    only the selection policy differs. Compute reported separately. Thresholds n/a
    (we report the full accuracy-vs-budget curve).

  Validation (point 5, run FIRST): does the pure-read ranking ever disagree with the
    optimal (info-gain) ranking? If not, the environment cannot discriminate the
    interpretations and collapses toward the trivial case -- and the agent comparison
    must NOT be read as evidence about I2/I3.

Self-contained by design (no framework), standard library only.
Run:  python3 src/laboratory3.py
"""

import math
import random

STATES = [(0, 0), (0, 1), (1, 0), (1, 1)]   # (b1, b2)


def target(state, channel):
    b1, b2 = state
    return b1 if channel == "A" else (b1 ^ b2)


def binary_entropy(p):
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def entropy(belief):
    return -sum(p * math.log2(p) for p in belief if p > 0.0)


# --- earned machinery, generalized to a 4-state joint belief ----------------

def initial_belief():
    return [0.25, 0.25, 0.25, 0.25]


def update(belief, channel, obs, noise):
    post = []
    for i, s in enumerate(STATES):
        t = target(s, channel)
        lik = (1 - noise) if obs == t else noise
        post.append(belief[i] * lik)
    z = sum(post)
    return [p / z for p in post]


def marginal_target_is_one(belief, channel):
    return sum(belief[i] for i, s in enumerate(STATES) if target(s, channel) == 1)


# --- selection policies -----------------------------------------------------

def pure_read_choice(belief, noise):
    # Pure read: marginal entropy of each channel's target. No imagined observations.
    hA = binary_entropy(marginal_target_is_one(belief, "A"))
    hB = binary_entropy(marginal_target_is_one(belief, "B"))
    return "A" if hA >= hB else "B", (hA, hB)


def expected_posterior_entropy(belief, channel, noise):
    total = 0.0
    for obs in (0, 1):
        p_obs = 0.0
        for i, s in enumerate(STATES):
            t = target(s, channel)
            p_obs += belief[i] * ((1 - noise) if obs == t else noise)
        if p_obs > 0.0:
            total += p_obs * entropy(update(belief, channel, obs, noise))
    return total


def simulation_choice(belief, noise):
    # Reapplies Update to imagined observations. This is the one-step optimum (oracle).
    eA = expected_posterior_entropy(belief, "A", noise)
    eB = expected_posterior_entropy(belief, "B", noise)
    return ("A" if eA <= eB else "B"), (eA, eB)


# --- environment validation (run before interpreting agents) ----------------

def validate_environment(noise, samples, seed):
    rng = random.Random(seed)
    disagreements = 0
    checked = 0
    for _ in range(samples):
        raw = [rng.random() for _ in range(4)]
        z = sum(raw)
        belief = [r / z for r in raw]
        pr, (hA, hB) = pure_read_choice(belief, noise)
        sim, (eA, eB) = simulation_choice(belief, noise)
        if abs(hA - hB) < 1e-9:
            continue  # genuine tie for pure-read; skip
        checked += 1
        if pr != sim:
            disagreements += 1
    return checked, disagreements


# --- the agent experiment ---------------------------------------------------

def observe(true_state, channel, noise, rng):
    t = target(true_state, channel)
    return t if rng.random() > noise else (1 - t)


def run_agent(policy, episodes, noise, budget, seed):
    rng = random.Random(seed)
    correct = 0
    imagined_updates = 0
    for _ in range(episodes):
        true_state = (rng.randint(0, 1), rng.randint(0, 1))
        belief = initial_belief()
        for _ in range(budget):
            if policy == "passive":
                channel = rng.choice(["A", "B"])
            elif policy == "pure_read":
                channel, _ = pure_read_choice(belief, noise)
            elif policy == "simulation":
                channel, _ = simulation_choice(belief, noise)
                imagined_updates += 4  # 2 channels x 2 imagined observations
            obs = observe(true_state, channel, noise, rng)
            belief = update(belief, channel, obs, noise)
        guess = STATES[max(range(4), key=lambda i: belief[i])]
        if guess == true_state:
            correct += 1
    return correct / episodes, imagined_updates / (episodes * budget) if episodes and budget else 0


if __name__ == "__main__":
    NOISE = 0.20
    EPISODES = 4000
    SEED = 7
    BUDGETS = [2, 4, 6, 8, 10]

    print("Genesis Laboratory 3 -- choice over information")
    print(f"  noise={NOISE}  episodes={EPISODES}  seed={SEED}")
    print()
    checked, dis = validate_environment(NOISE, samples=20000, seed=SEED)
    print("ENVIRONMENT VALIDATION (does pure-read ever disagree with the optimum?)")
    print(f"  non-tie belief states checked : {checked}")
    print(f"  pure-read vs optimum disagreements : {dis}")
    verdict = ("DISCRIMINATING" if dis > 0 else "COLLAPSED (cannot discriminate I1/I2/I3)")
    print(f"  verdict : {verdict}")
    print()

    print("AGENTS (accuracy on the joint state vs observation budget)")
    print(f"  {'budget':>6} | {'passive':>8} | {'pure_read':>9} | {'simulation':>10} | sim imagined-Updates/step")
    for b in BUDGETS:
        pa, _ = run_agent("passive", EPISODES, NOISE, b, SEED)
        pr, _ = run_agent("pure_read", EPISODES, NOISE, b, SEED)
        si, ic = run_agent("simulation", EPISODES, NOISE, b, SEED)
        print(f"  {b:>6} | {pa:>8.3f} | {pr:>9.3f} | {si:>10.3f} | {ic:>6.1f}")
