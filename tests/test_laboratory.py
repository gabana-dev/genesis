"""
The one quantitative check for Laboratory 1.

Falsifiable prediction from the belief-necessity result: under partial
observability, an agent that maintains a belief-state via Update outperforms a
memoryless agent that acts on the latest observation alone.

If this fails, either the theory or its implementation contains an error --
which is exactly the kind of contact with reality Laboratory 1 exists to produce.

Run:  python3 tests/test_laboratory.py   (prints PASS/FAIL, exits non-zero on failure)
      or with pytest.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from laboratory import run


def test_belief_beats_memoryless_under_partial_observability():
    m_acc, b_acc = run(episodes=5000, noise=0.30, horizon=12, seed=7)

    # Memoryless is capped near the per-observation accuracy (1 - noise = 0.70).
    assert m_acc < 0.75, f"memoryless unexpectedly high: {m_acc}"
    # Belief integrates 12 observations and should sit well above that ceiling.
    assert b_acc > 0.88, f"belief agent failed to clear the ceiling: {b_acc}"
    # The whole point: integrating beats not integrating, by a wide margin.
    assert b_acc > m_acc + 0.10, f"belief advantage too small: {b_acc - m_acc}"


if __name__ == "__main__":
    test_belief_beats_memoryless_under_partial_observability()
    print("PASS -- belief-state beats memoryless under partial observability")
