"""
Milestone 1 — the minimal closed agent loop (integration, not discovery).

The first CLOSED loop Genesis has built:
  hidden state -> observation -> Update -> belief -> decision -> action ->
  Predict(action) -> new hidden state -> new observation -> ...
New capability vs Labs 1-3: belief -> action -> changed world -> new evidence ->
updated belief. The agent moves the very state it must track.

CONTRACT (pre-registered), per the approved amendment:
  A. Integration validity (PRIMARY): the action-conditioned Predict step incorporates the
     agent's action, so the belief stays aligned with the true state while the agent moves
     it. Made observable by an ablation -- an Update-only agent (no Predict) -- which should
     lose alignment as it moves. This is a diagnostic, not new machinery.
  B. Behavioral utility (SECONDARY, reported not load-bearing): acting from the belief beats
     a memoryless agent acting on the raw observation.

  Belief quality is recorded separately from task performance:
  true position, posterior on the true position, MAP error, reached, steps.

  IMPORT: action-conditioned recursive Bayes filter (predict with motion model given action;
  correct with sensor model) -- Thrun, Burgard & Fox, Probabilistic Robotics (2005);
  Astrom 1965. Policy: certainty-equivalent greedy toward a fixed target (trivial).

  EXCLUDED (scope): RL, learned policy, planning, model learning, causal inference, markets,
  reflexivity, self-improvement, axiology work, novelty claims.

Standard library only. Run: python3 src/closed_loop.py
"""

import random

K = 7           # corridor cells 0..K-1
TARGET = 3
MAX_STEPS = 30


def clamp(i):
    return max(0, min(K - 1, i))


def transition(pos, action):        # action in {-1, 0, +1}
    return clamp(pos + action)


def observe(pos, noise, rng):
    if rng.random() < 1 - noise:
        return pos
    return rng.choice([c for c in range(K) if c != pos])   # uniform over the others


def likelihood(cell, obs, noise):
    return (1 - noise) if obs == cell else noise / (K - 1)


def uniform_belief():
    return [1.0 / K] * K


def update(belief, obs, noise):
    post = [belief[c] * likelihood(c, obs, noise) for c in range(K)]
    z = sum(post)
    return [p / z for p in post]


def predict(belief, action):
    nb = [0.0] * K
    for c in range(K):
        nb[transition(c, action)] += belief[c]
    return nb


def map_pos(belief):
    return max(range(K), key=lambda c: belief[c])


def greedy(p):                       # certainty-equivalent: move toward TARGET
    return 1 if p < TARGET else (-1 if p > TARGET else 0)


def run_episode(mode, noise, rng):
    """mode in {full, no_predict, memoryless}. Returns metrics for one episode."""
    pos = rng.choice([c for c in range(K) if c != TARGET])
    belief = uniform_belief()
    true_posts, map_errs = [], []
    reached_step = None

    for step in range(MAX_STEPS):
        if pos == TARGET:
            reached_step = step
            break
        obs = observe(pos, noise, rng)

        if mode == "memoryless":
            action = greedy(obs)
        else:                        # full or no_predict
            belief = update(belief, obs, noise)
            true_posts.append(belief[pos])          # belief quality AT the true position
            map_errs.append(abs(map_pos(belief) - pos))
            action = greedy(map_pos(belief))

        pos = transition(pos, action)
        if mode == "full":
            belief = predict(belief, action)         # incorporate the agent's own action

    if reached_step is None and pos == TARGET:
        reached_step = MAX_STEPS

    reached = reached_step is not None
    steps = reached_step if reached else MAX_STEPS
    avg_true_post = sum(true_posts) / len(true_posts) if true_posts else None
    avg_map_err = sum(map_errs) / len(map_errs) if map_errs else None
    return reached, steps, avg_true_post, avg_map_err


def run(mode, episodes, noise, seed):
    rng = random.Random(seed)
    reached = 0
    steps_sum = 0
    tp_sum = 0.0
    me_sum = 0.0
    tp_n = 0
    for _ in range(episodes):
        r, s, tp, me = run_episode(mode, noise, rng)
        reached += 1 if r else 0
        steps_sum += s
        if tp is not None:
            tp_sum += tp
            me_sum += me
            tp_n += 1
    return {
        "reached_rate": reached / episodes,
        "avg_steps": steps_sum / episodes,
        "avg_true_posterior": (tp_sum / tp_n) if tp_n else None,
        "avg_map_error": (me_sum / tp_n) if tp_n else None,
    }


if __name__ == "__main__":
    EPISODES = 3000
    SEED = 7
    print("Milestone 1 -- minimal closed agent loop (K=7, target=3, max_steps=30)")
    for noise in (0.2, 0.5, 0.7):
        full = run("full", EPISODES, noise, SEED)
        nop = run("no_predict", EPISODES, noise, SEED)
        mem = run("memoryless", EPISODES, noise, SEED)
        print(f"\nnoise = {noise}")
        print("  A. INTEGRATION (belief quality, primary)")
        print(f"     full      : true-posterior {full['avg_true_posterior']:.3f}  MAP-error {full['avg_map_error']:.3f}")
        print(f"     no_predict: true-posterior {nop['avg_true_posterior']:.3f}  MAP-error {nop['avg_map_error']:.3f}   (ablation: should be worse)")
        print("  B. BEHAVIOR (task, secondary)")
        print(f"     full      : reached {full['reached_rate']:.3f}  avg_steps {full['avg_steps']:.2f}")
        print(f"     memoryless: reached {mem['reached_rate']:.3f}  avg_steps {mem['avg_steps']:.2f}")
