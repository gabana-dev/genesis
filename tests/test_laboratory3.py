"""
Laboratory 3 checks. These encode the ACTUAL finding, not the hoped-for one:

1. The environment is non-discriminating: pure-read never disagrees with the optimal
   (info-gain) ranking on non-tie belief states. (If this ever fails, the environment
   has become discriminating and the I1/I2/I3 interpretation is back in play.)
2. Empirically, pure_read and simulation are functionally identical (simulation buys
   nothing), and both beat passive.

Run:  python3 tests/test_laboratory3.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lab"))

from laboratory3 import validate_environment, run_agent


def test_environment_is_non_discriminating():
    checked, disagreements = validate_environment(noise=0.20, samples=20000, seed=7)
    assert checked > 1000, f"too few non-tie states checked: {checked}"
    assert disagreements == 0, (
        f"environment unexpectedly DISCRIMINATES ({disagreements} disagreements) — "
        "the I1/I2/I3 interpretation is back in play and must be re-run"
    )


def test_simulation_buys_nothing_and_selection_beats_passive():
    budget = 10
    passive, _ = run_agent("passive", 4000, 0.20, budget, 7)
    pure_read, _ = run_agent("pure_read", 4000, 0.20, budget, 7)
    simulation, sim_imagined = run_agent("simulation", 4000, 0.20, budget, 7)

    # selection (a read) beats passive
    assert pure_read > passive + 0.03, f"pure-read did not beat passive: {pure_read} vs {passive}"
    # simulation buys nothing over the pure read (functionally identical)
    assert abs(simulation - pure_read) < 0.01, f"simulation diverged from pure-read: {simulation} vs {pure_read}"
    # and it paid real compute for that nothing
    assert sim_imagined > 0, "simulation should have performed imagined Updates"


if __name__ == "__main__":
    test_environment_is_non_discriminating()
    test_simulation_buys_nothing_and_selection_beats_passive()
    print("PASS -- environment non-discriminating; simulation buys nothing; selection beats passive")
