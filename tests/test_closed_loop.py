"""
Milestone 1 checks — encoding the ACTUAL findings, split by criterion.

A. Integration validity (PRIMARY): the action-conditioned Predict step keeps the belief
   aligned with a state the agent is moving. The Update-only ablation should be worse.
B. Behavioral utility (SECONDARY): reported, NOT asserted as a win — in this easy task the
   belief provided no behavioral advantage, and that is recorded honestly, not hidden.

Run: python3 tests/test_closed_loop.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from closed_loop import run


def test_integration_validity_predict_keeps_belief_aligned():
    full = run("full", 3000, 0.5, 7)
    nop = run("no_predict", 3000, 0.5, 7)
    # the closed loop tracks: full agent keeps meaningful posterior on the true position
    assert full["avg_true_posterior"] > nop["avg_true_posterior"] + 0.05, "predict did not help tracking"
    assert full["avg_map_error"] < nop["avg_map_error"] - 0.1, "predict did not reduce MAP error"
    # and the loop runs to completion reliably
    assert full["reached_rate"] > 0.99, f"full agent failed to reach target: {full['reached_rate']}"


def test_behavior_is_reported_not_claimed():
    # Honest record: the task is easy enough that a memoryless agent also succeeds, so the
    # belief provides no behavioral advantage here. This test documents that, it does not
    # assert belief superiority (which the data does not support).
    full = run("full", 3000, 0.5, 7)
    mem = run("memoryless", 3000, 0.5, 7)
    assert mem["reached_rate"] > 0.99, "baseline unexpectedly failed"
    assert full["reached_rate"] > 0.99, "belief agent unexpectedly failed"
    # no assertion that full beats memoryless — it does not, and that is the finding.


if __name__ == "__main__":
    test_integration_validity_predict_keeps_belief_aligned()
    test_behavior_is_reported_not_claimed()
    print("PASS -- integration valid (predict keeps belief aligned); behavior reported honestly (no belief advantage in this task)")
