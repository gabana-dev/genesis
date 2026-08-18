"""
Genesis Laboratory 1 -- first contact between theory and reality.

Runs many episodes of the partially observable environment, lets both agents
observe the same observation stream each episode, and compares final-guess
accuracy.

Its purpose is NOT to produce an impressive result. The claim under test is
already known in the POMDP literature. The purpose is architectural validation:
can Reception, Update, and a belief-state be implemented cleanly from the canon,
and does the implementation behave as the theory predicts?

Run:  python3 src/laboratory.py
"""

import random
from environment import PartiallyObservableBit
from agents import MemorylessAgent, BeliefAgent


def run(episodes, noise, horizon, seed):
    rng = random.Random(seed)
    env = PartiallyObservableBit(noise=noise, horizon=horizon, rng=rng)

    memoryless_correct = 0
    belief_correct = 0

    for _ in range(episodes):
        memoryless = MemorylessAgent()
        belief = BeliefAgent(noise=noise)

        obs = env.reset()
        while obs is not None:
            memoryless.observe(obs)
            belief.observe(obs)
            obs = env.step()

        memoryless_correct += env.reward(memoryless.guess())
        belief_correct += env.reward(belief.guess())

    return memoryless_correct / episodes, belief_correct / episodes


if __name__ == "__main__":
    EPISODES = 5000
    NOISE = 0.30      # each observation is 70% informative
    HORIZON = 12      # observations integrated per episode
    SEED = 7

    m_acc, b_acc = run(EPISODES, NOISE, HORIZON, SEED)

    print("Genesis Laboratory 1 -- belief-state vs memoryless under partial observability")
    print(f"  episodes={EPISODES}  noise={NOISE}  horizon={HORIZON}  seed={SEED}")
    print(f"  memoryless accuracy : {m_acc:.3f}   (per-observation ceiling ~ {1 - NOISE:.2f})")
    print(f"  belief accuracy     : {b_acc:.3f}")
    print(f"  belief advantage    : {b_acc - m_acc:+.3f}")
