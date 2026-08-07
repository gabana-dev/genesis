"""
Genesis Laboratory 2 -- variation test: learn the observation model.

Laboratory 1 handed the agent its observation model (the noise). The postmortem
identified that model as the one piece of reality-generated architecture the theory
had no slot for. Laboratory 2 removes the gift: the agent must LEARN its observation
model from experience, via a second Update loop over labelled observations.

This laboratory serves two purposes at once:
  Production  -- attacks research/questions/observation-model-provenance.md: is the
                 observation model itself the state of a second Update loop? (If the
                 learned noise converges to the truth, yes.)
  Governance  -- it is a *variation* of Laboratory 1 (different representation: a
                 learned rather than given model). If the belief-state invariant
                 survives this variation, belief-necessity has earned stability, not
                 just a single successful implementation.

Run:  python3 src/laboratory2.py
"""

import random
from environment import PartiallyObservableBit
from agents import MemorylessAgent, BeliefAgent, LearningBeliefAgent


def run(episodes, noise, horizon, seed):
    rng = random.Random(seed)
    env = PartiallyObservableBit(noise=noise, horizon=horizon, rng=rng)
    learner = LearningBeliefAgent()   # persists across episodes; accumulates the model

    per_episode = []   # (memoryless, given-model, learned-model) correctness per episode
    for _ in range(episodes):
        memoryless = MemorylessAgent()
        given = BeliefAgent(noise=noise)   # Lab 1 agent, given the true model

        obs = env.reset()
        while obs is not None:
            memoryless.observe(obs)
            given.observe(obs)
            learner.observe(obs)
            obs = env.step()

        per_episode.append((
            env.reward(memoryless.guess()),
            env.reward(given.guess()),
            env.reward(learner.guess()),
        ))
        learner.learn(env.reveal())

    return per_episode, learner.noise_estimate()


def _accuracy(rows, index, lo, hi):
    window = rows[lo:hi]
    return sum(r[index] for r in window) / len(window)


if __name__ == "__main__":
    EPISODES = 8000
    NOISE = 0.30
    HORIZON = 12
    SEED = 7
    WINDOW = 2000   # compare the first and last WINDOW episodes for the learner

    rows, learned_noise = run(EPISODES, NOISE, HORIZON, SEED)

    mem = _accuracy(rows, 0, 0, EPISODES)
    given = _accuracy(rows, 1, 0, EPISODES)
    learn_early = _accuracy(rows, 2, 0, WINDOW)
    learn_late = _accuracy(rows, 2, EPISODES - WINDOW, EPISODES)

    print("Genesis Laboratory 2 -- learned observation model (variation of Lab 1)")
    print(f"  episodes={EPISODES}  true_noise={NOISE}  horizon={HORIZON}  seed={SEED}")
    print(f"  memoryless accuracy           : {mem:.3f}")
    print(f"  belief, GIVEN model           : {given:.3f}")
    print(f"  belief, LEARNED model (early) : {learn_early:.3f}   (first {WINDOW} episodes)")
    print(f"  belief, LEARNED model (late)  : {learn_late:.3f}   (last {WINDOW} episodes)")
    print(f"  learned noise estimate        : {learned_noise:.3f}   (true {NOISE})")
