"""
Laboratory 2 checks -- the variation test for belief-necessity.

Two falsifiable predictions:
  1. The observation model is learnable as the state of a second Update loop -- the
     learned noise estimate converges to the true noise.
  2. Belief-necessity survives the variation -- once the model is learned, the belief
     agent (with a LEARNED model) still clearly beats the memoryless agent, and
     approaches the belief agent given the true model.

If either fails, we learn something more valuable than confirmation.

Run:  python3 tests/test_laboratory2.py   (prints PASS/FAIL, exits non-zero on failure)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lab"))

from laboratory2 import run, _accuracy


def test_model_is_learnable_and_belief_necessity_survives_variation():
    episodes, window = 8000, 2000
    rows, learned_noise = run(episodes=episodes, noise=0.30, horizon=12, seed=7)

    mem = _accuracy(rows, 0, 0, episodes)
    given = _accuracy(rows, 1, 0, episodes)
    learn_late = _accuracy(rows, 2, episodes - window, episodes)

    # 1. the observation model converges to the truth (second Update loop works)
    assert abs(learned_noise - 0.30) < 0.03, f"learned noise off: {learned_noise}"
    # 2a. belief-necessity survives the variation: learned-model belief beats memoryless
    assert learn_late > mem + 0.10, f"learned belief no better than memoryless: {learn_late} vs {mem}"
    # 2b. and approaches the given-model ceiling
    assert learn_late > given - 0.03, f"learned belief far below given-model: {learn_late} vs {given}"


if __name__ == "__main__":
    test_model_is_learnable_and_belief_necessity_survives_variation()
    print("PASS -- model learnable; belief-necessity survives the learned-model variation")
