"""
Size-aware fill model, checked against hand-computed answers.

The bar these have to clear is set by the defect they exist to prevent. `fills.py` was
size-blind and nothing in its output said so — a 1,000x size range produced identical reach and
identical fill counts, and CAP-1 would have reported that as "no capacity constraint detected".

So the first and most important check is simply: **does size change the answer?**

Run: .venv/bin/python tests/test_sized_fills.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import sized_fills as S  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def order(size, price=100.0, side=S.BUY):
    return S.SizedOrder(order_id=f"o{size}", side=side, size=size, price=price)


def feed(o, sizes):
    """Arrive into the first observation, then observe the rest."""
    for s in sizes:
        o.observe_level(s)
    return o


@check
def size_changes_the_answer():
    """
    THE CHECK THIS MODULE EXISTS FOR. Under fills.py a 1,000x size range produced identical
    reach and identical fill counts. Here the same book evolution must give different answers
    for different sizes.
    """
    # Queue of 10 in front of us; only 8 ever leaves. Nobody fills, at any size.
    short = [10.0, 6.0, 2.0]
    got = {sz: feed(order(sz), short).optimistic_fill() for sz in (1.0, 5.0, 100.0)}
    assert got == {1.0: 0.0, 5.0: 0.0, 100.0: 0.0}, got

    # Queue of 10, and 13 leaves in total -- 3 units past the queue, so size now decides.
    through = [10.0, 6.0, 0.0, 3.0, 0.0]
    got2 = {sz: feed(order(sz), through).optimistic_fill() for sz in (1.0, 5.0, 100.0)}
    assert got2 == {1.0: 1.0, 5.0: 3.0, 100.0: 3.0}, got2
    assert len(set(got2.values())) > 1, "size still does not change the answer"
    return "13 consumed against a queue of 10: 1 fills fully, 5 and 100 fill 3"


@check
def a_full_fill_requires_the_queue_plus_our_own_size():
    """The single `+ our_size` that fills.py lacked."""
    o = feed(order(4.0), [10.0, 0.0, 4.0, 0.0])     # 10 then 4 more = 14 consumed
    assert o.queue_ahead == 10.0
    assert o.consumed == 14.0
    assert o.optimistic_fill() == 4.0
    o2 = feed(order(4.0), [10.0, 0.0, 2.0, 0.0])    # 12 consumed: queue clears, 2 of ours
    assert o2.optimistic_fill() == 2.0
    assert o2.bracket()["partial"] is True
    return "queue 10 + size 4: 14 consumed fills fully, 12 fills 2 and reports partial"


@check
def partial_fills_exist_at_all():
    o = feed(order(10.0), [5.0, 0.0, 3.0, 0.0])     # 8 consumed, 3 past a queue of 5
    b = o.bracket()
    assert b["optimistic_fill"] == 3.0
    assert b["partial"] is True
    assert b["fully_filled_optimistic"] is False
    return "a partially consumed level yields a partial fill, not a binary"


@check
def a_level_that_trades_through_fills_everything():
    o = order(1_000_000.0)
    o.observe_level(5.0)
    o.level_cleared()
    b = o.bracket()
    assert b["certain_fill"] == 1_000_000.0
    assert b["pessimistic_fill"] == 1_000_000.0
    assert b["ambiguity"] == 0.0
    return "trading through the level removes the queue assumption entirely"


@check
def queue_joiners_behind_us_are_not_counted_as_consumption():
    """
    Measuring against the original anchor rather than the last observation would read a
    queue joiner as negative consumption and silently credit a fill.
    """
    o = feed(order(2.0), [10.0, 14.0, 12.0])   # +4 joined, then 2 left
    assert o.consumed == 2.0, o.consumed
    assert o.optimistic_fill() == 0.0
    return "size arriving behind us adds 0 to consumption; only decreases count"


@check
def the_ambiguity_bracket_widens_with_size():
    """
    C5 of CAP-1 predicted this. A bigger order depends more on queue position, and the
    depth-only recording cannot resolve it -- so the honest uncertainty grows.
    """
    book = [10.0, 6.0, 0.0, 4.0, 0.0]        # 14 consumed against a queue of 10
    fracs = {}
    for sz in (1.0, 4.0, 20.0):
        b = feed(order(sz), book).bracket()
        fracs[sz] = b["ambiguity_fraction"]
    assert fracs[1.0] == 1.0, fracs          # 1 of 1 uncertain
    assert fracs[4.0] == 1.0, fracs
    assert fracs[20.0] == 4.0 / 20.0, fracs  # only 4 of 20 could have filled at all
    assert fracs[20.0] < fracs[1.0]
    return f"ambiguity as a fraction of requested size: {fracs}"


@check
def pessimistic_is_zero_unless_the_level_cleared():
    o = feed(order(5.0), [10.0, 0.0, 5.0, 0.0])
    assert o.optimistic_fill() == 5.0
    assert o.pessimistic_fill() == 0.0
    assert o.bracket()["ambiguity"] == 5.0
    return "every decrease read as a cancellation from behind fills nothing"


@check
def depth_relative_classification():
    assert S.classify_size(1.0, 100.0) == "small"
    assert S.classify_size(50.0, 100.0) == "material"
    assert S.classify_size(500.0, 100.0) == "dominant"
    assert S.classify_size(1.0, 0.0) == "unknown_depth"
    assert S.depth_ratio(5.0, 100.0) == 0.05
    assert S.depth_ratio(5.0, 0.0) is None
    return "10% and 100% of displayed depth are the declared boundaries"


@check
def fill_rate_is_in_base_units_not_order_counts():
    """
    With partial fills an order is no longer a yes/no. Counting orders would score a 1% fill
    and a 100% fill identically, which is the blindness this module removes.
    """
    a = feed(order(10.0), [5.0, 0.0, 1.0, 0.0])   # 6 consumed, 1 of ours
    b = order(10.0)
    b.observe_level(5.0)
    b.level_cleared()                              # full 10
    s = S.summarise([a, b])
    assert s["requested_size"] == 20.0
    assert s["optimistic_filled_size"] == 11.0
    assert abs(s["fill_rate_upper_bound"] - 0.55) < 1e-12, s
    assert s["n_partial_optimistic"] == 1
    assert s["n_traded_through"] == 1
    return "1 of 10 plus 10 of 10 is a 55% fill rate, not a 50% one"


@check
def an_unarrived_order_fills_nothing():
    o = order(5.0)
    b = o.bracket()
    assert b["optimistic_fill"] == 0.0 and b["pessimistic_fill"] == 0.0
    assert b["queue_ahead"] is None
    return "an order that never saw the book has no queue and no fill"


def main():
    failed = 0
    for fn in _checks:
        try:
            print(f"  ok  {fn.__name__}  --  {fn()}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"size-aware fill checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
