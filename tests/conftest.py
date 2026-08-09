"""
This project does not support pytest. This file makes that fail loudly.

The suites here use their own runners, and each check returns a description string that is
printed as part of the result -- "gap 3..6 recorded; no deltas fabricated". That output is
evidence, not decoration, and it is quoted in commit messages and reports.

Without this file, `pytest` produces a MISLEADING GREEN. Measured, before it was added:

    31 collected -> 19 passed, 12 errors

    tests/test_recorder.py            12 collected, all ERROR (fixture 'tmp' not found)
    tests/test_recorder_audit.py       0 collected  (17 real checks, silently skipped)
    tests/test_recorder_decimal_qty.py 0 collected  ( 9 real checks, silently skipped)
    tests/test_recorder_validity.py    0 collected  (11 real checks, silently skipped)

pytest reported "19 passed" while silently omitting 37 of the recorder's 49 checks -- every
audit regression from F1-F3, NF-1 and D1-D5 among them. That is the recorder's own failure
mode reproduced in its tooling: a green summary asserting completeness it has not earned,
with the incompleteness unmarked.

An error is better than a false pass.
"""


def pytest_collection(session):
    import pytest
    raise pytest.UsageError(
        "\n"
        "  Genesis does not support pytest.\n"
        "\n"
        "  Run the suite with its own runner instead:\n"
        "      .venv/bin/python tests/run_all.py\n"
        "      .venv/bin/python tests/run_all.py recorder     # subset\n"
        "\n"
        "  Reason: the check functions return printed descriptions that are part of the\n"
        "  evidence, and pytest collects only 12 of 49 recorder checks -- reporting a green\n"
        "  summary while silently skipping every audit regression. See tests/README.md.\n"
    )
