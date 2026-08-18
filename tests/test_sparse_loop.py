"""
Milestone 2 checks — encoding the ACTUAL findings, including the unflattering one.

A. PRIMARY (behavioral): belief vs the stale-observation baseline, paired, in an
   uncontaminated condition. Large and CI-separated at p=5; ~flat at the p=1 null control.
B. SECONDARY (mechanism): the full filter holds its posterior across observation gaps; the
   frozen-belief ablation collapses.
C. The finding the experiment was NOT designed to produce and does not hide: the "weak"
   null agent — which simply waits for fresh evidence — is MORE accurate than the belief
   agent at p=5, because waiting costs nothing in this environment.

Run: python3 tests/test_sparse_loop.py   (~25s)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lab"))

from sparse_loop import run_condition

EPISODES = 3000
SEED = 7


def test_primary_belief_beats_stale_under_gaps():
    r = run_condition(EPISODES, 0.2, 5, 0.0, SEED)
    assert not r["contaminated"], "p=5 condition should be clean by the pre-registered rule"
    mean, lo, hi = r["paired_belief_minus_stale"]
    assert lo > 0.5, f"expected a large separated advantage, got [{lo}, {hi}]"
    # the mechanism: stale cannot detect arrival, so it mostly never declares correctly
    assert r["stale"]["accuracy"] < 0.01, "stale baseline unexpectedly succeeded"


def test_null_control_at_p1_is_near_flat():
    r = run_condition(EPISODES, 0.2, 1, 0.0, SEED)
    mean, lo, hi = r["paired_belief_minus_stale"]
    assert abs(mean) < 0.05, f"p=1 should replicate M1's no-advantage result, got {mean}"


def test_mechanism_predict_holds_belief_across_gaps():
    r = run_condition(EPISODES, 0.2, 5, 0.0, SEED)
    belief_gaps, frozen_gaps = r["belief"]["by_gap"], r["frozen"]["by_gap"]
    for gap in (1, 2, 3):
        assert belief_gaps[gap][0] > frozen_gaps[gap][0] + 0.3, f"gap {gap}: predict not load-bearing"
        assert belief_gaps[gap][1] < frozen_gaps[gap][1] - 1.0, f"gap {gap}: MAP error not reduced"
    # and the full filter does not degrade steeply with gap age
    assert belief_gaps[3][0] > 0.5 * belief_gaps[0][0]


def test_waiting_is_free_and_the_null_agent_exploits_it():
    # Recorded honestly: the reference agent that acts only on fresh evidence is MORE accurate
    # than the belief agent under large gaps -- at ~7x the steps. Nothing in this environment
    # penalises waiting. This is the limitation M2 actually exposed, not a bug to be tuned away.
    r = run_condition(EPISODES, 0.2, 5, 0.0, SEED)
    assert r["null"]["accuracy"] > r["belief"]["accuracy"], "null agent no longer dominates?"
    assert r["null"]["avg_steps"] > 5 * r["belief"]["avg_steps"], "null agent is not slow?"


def test_wall_threshold_flags_p3():
    # The pre-registered 25% clamp-assist threshold caught the artifact it was written for:
    # at p=3 the stale agent's "successes" are mostly wall-assisted repositioning.
    r = run_condition(EPISODES, 0.2, 3, 0.0, SEED)
    assert r["contaminated"], "p=3 should trip the pre-registered contamination rule"
    assert r["stale"]["clamp_share"] > 0.25


if __name__ == "__main__":
    test_primary_belief_beats_stale_under_gaps()
    test_null_control_at_p1_is_near_flat()
    test_mechanism_predict_holds_belief_across_gaps()
    test_waiting_is_free_and_the_null_agent_exploits_it()
    test_wall_threshold_flags_p3()
    print("PASS -- primary advantage confirmed vs stale under gaps; mechanism confirmed; "
          "waiting-is-free limitation and p=3 wall contamination both recorded")
