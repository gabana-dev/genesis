"""
The alert state machine, tested without touching the network or the real watchlist.

The thing worth testing here is not the arithmetic, it is the SILENCE: an alarm that fires twice
for one event is worse than one that fires late, because the customer turns it off. Most of these
cases assert that nothing was sent.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "product"))
import alerts


def pos(dist, coin="ETH", side="short"):
    """A position list with one entry at the given distance. Prices are consistent with it so a
    composed message is never nonsense: a short liquidates above the mark."""
    mid = 2000.0
    liq = mid * (1 + dist / 100.0) if side == "short" else mid * (1 - dist / 100.0)
    return [{"coin": coin, "side": side, "liq": liq, "mid": mid,
             "dist": dist, "notional": 100_000.0}]


def cush(ratio, used=1_000_000.0):
    return (ratio, ratio * used, used) if ratio is not None else (None, 0.0, 0.0)


HEALTHY = cush(0.5)
kinds = lambda a: [k for k, _ in a]


def step(state, dist, c=HEALTHY):
    a, state = alerts.evaluate(state, pos(dist), c)
    return kinds(a), state


def test_first_crossing_fires_once():
    fired, st = step({}, 9.9)
    assert fired == ["proximity"] and st["band"] == 10, (fired, st)
    fired, st = step(st, 9.8)
    assert fired == [], fired          # still inside the same band: silence


def test_tightening_fires_again():
    _, st = step({}, 9.9)
    fired, st = step(st, 4.5)
    assert fired == ["proximity"] and st["band"] == 5, (fired, st)


def test_oscillation_at_the_boundary_is_silent():
    """The case that would spam a customer: price crossing 10% back and forth.
    Re-arm needs 10 * 1.25 = 12.5%, so 10.5 does not re-arm and 9.8 cannot re-fire."""
    _, st = step({}, 9.9)
    for d in (10.5, 9.8, 11.0, 9.5, 12.4):
        fired, st = step(st, d)
        assert fired == [], (d, fired)
    assert st["band"] == 10


def test_rearm_then_refire():
    _, st = step({}, 9.9)
    fired, st = step(st, 13.0)         # past 12.5: re-arms into the 15% band, no alert
    assert fired == [] and st["band"] == 15, (fired, st)
    fired, st = step(st, 9.9)
    assert fired == ["proximity"], fired


def test_stand_down_only_after_being_close():
    _, st = step({}, 9.9)
    fired, st = step(st, 30.0)
    assert fired == ["stand_down"] and st["band"] is None, (fired, st)
    fired, st = step(st, 31.0)
    assert fired == [], fired          # clear stays clear, silently


def test_no_stand_down_from_a_wide_band():
    """25% was never frightening, so leaving it is not news."""
    fired, st = step({}, 24.0)
    assert fired == ["proximity"] and st["band"] == 25
    fired, st = step(st, 40.0)
    assert fired == [], fired


def test_cannot_defend_fires_once():
    _, st = step({}, 9.9)              # proximity already reported
    fired, st = step(st, 9.8, cush(0.01))
    assert fired == ["cannot_defend"] and st["cushion"] == "trapped", (fired, st)
    fired, st = step(st, 9.7, cush(0.0))
    assert fired == [], fired


def test_trapped_rearms_above_the_upper_threshold():
    _, st = step({}, 9.9)
    _, st = step(st, 9.8, cush(0.01))
    fired, st = step(st, 9.8, cush(0.07))     # between trip and re-arm: still trapped, silent
    assert fired == [] and st["cushion"] == "trapped", (fired, st)
    fired, st = step(st, 9.8, cush(0.20))
    assert fired == [] and st["cushion"] == "ok", (fired, st)
    fired, st = step(st, 9.8, cush(0.01))
    assert fired == ["cannot_defend"], fired


def test_one_event_is_one_message():
    """A wallet first seen close AND trapped gets the proximity alert only -- it already carries
    the free-collateral line."""
    fired, st = step({}, 4.0, cush(0.0))
    assert fired == ["proximity"] and st["cushion"] == "trapped", (fired, st)


def test_trapped_far_away_is_not_an_alert():
    fired, st = step({}, 60.0, cush(0.0))
    assert fired == [] and st == {}, (fired, st)


def test_closed_position_forgets_everything():
    _, st = step({}, 4.0)
    a, st = alerts.evaluate(st, [], HEALTHY)
    assert a == [] and st == {}, (a, st)


def test_messages_compose():
    p = pos(4.2)[0]
    for kind in ("proximity", "cannot_defend", "stand_down"):
        m = alerts.compose(kind, p, "0x" + "ab" * 20, free=0.0, used=1e6)
        assert "ETH" in m and "0xabab" in m and len(m) < 4096, kind
    m = alerts.compose("proximity", p, "0x" + "ab" * 20, free=0.0, used=1e6)
    assert "nothing to defend with" in m
    m = alerts.compose("proximity", p, "0x" + "ab" * 20, free=12_500.0, used=1e6)
    assert "$12.5k" in m


def test_bands():
    assert alerts.band(26) is None
    assert alerts.band(25) == 25
    assert alerts.band(10.0) == 10
    assert alerts.band(0.4) == 2


def test_the_real_watchlist_is_never_touched():
    """These tests run against no files at all. If that ever stops being true, this catches it
    before a test writes into a paying subscriber's state."""
    before = [os.path.getmtime(p) if os.path.exists(p) else None
              for p in (alerts.WATCHLIST, alerts.STATE)]
    test_first_crossing_fires_once()
    after = [os.path.getmtime(p) if os.path.exists(p) else None
             for p in (alerts.WATCHLIST, alerts.STATE)]
    assert before == after


def main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for f in fns:
        try:
            f()
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {f.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR {f.__name__}: {type(e).__name__}: {e}")
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(fns) - failed}/{len(fns)} "
          f"alert state-machine checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
