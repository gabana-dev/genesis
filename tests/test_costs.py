"""
Checks for the cost model.

The point of these is not that arithmetic works. It is that the two questions the module
separates STAY separated, and that the separation survives someone later reaching for the
convenient number.

Run: .venv/bin/python tests/test_costs.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import costs  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


BPS = 1e-4

# EXEC-1's measured values, so these checks are anchored to real numbers and not to invented
# ones. Adverse selection at 60 s, certain pool, 291 ms arm.
EXEC1_ADVERSE_SELECTION = 1.1871 * BPS
# MEASURE-1, bav-1 recording, 2042 samples: median full spread as a fraction of price.
MEASURED_SPREAD = 1.5364247123600758e-07


@check
def exec1_number_is_reproduced():
    """The module must reproduce EXEC-1's published result from its own inputs, or it is
    modelling something other than what was measured."""
    r = costs.execution_saving(EXEC1_ADVERSE_SELECTION, "futures_vip0")
    assert abs(r["maker_advantage"] - 3.0 * BPS) < 1e-12, r
    assert abs(r["net_saving_per_side"] - 1.8129 * BPS) < 1e-8, r["net_saving_per_side"]
    assert 0.60 < r["surviving_fraction"] < 0.61, r["surviving_fraction"]
    return f"{r['net_saving_per_side']/BPS:.4f} bps per side survives, matching EXEC-1"


@check
def market_making_on_the_measured_spread_is_not_close():
    """
    THE CHECK THIS MODULE WAS WRITTEN FOR. The 1.83 bps execution saving has been read as
    though quoting were profitable. On the measured spread it is not, and not marginally.
    """
    r = costs.market_making_pnl(MEASURED_SPREAD, EXEC1_ADVERSE_SELECTION, "futures_vip0")
    assert not r["viable"], r
    assert r["net"] < 0
    # Costs exceed the entire captured spread by more than three orders of magnitude.
    assert r["cost_to_spread_ratio"] > 1000, r["cost_to_spread_ratio"]
    return (f"net {r['net']/BPS:.3f} bps per round trip; costs are "
            f"{r['cost_to_spread_ratio']:.0f}x the spread")


@check
def zero_maker_fee_does_not_rescue_it():
    """
    The obvious hope is a VIP tier. The best publicly listed maker fee is zero, not negative,
    so the fee term vanishes and adverse selection alone still buries it. Worth checking
    rather than assuming, because it closes the escape route explicitly.
    """
    r = costs.market_making_pnl(MEASURED_SPREAD, EXEC1_ADVERSE_SELECTION, "futures_vip9")
    assert r["maker_fees_round_trip"] == 0.0, r
    assert not r["viable"], r
    return f"even at 0 bps maker fee, net {r['net']/BPS:.4f} bps -- adverse selection alone"


@check
def breakeven_spread_is_reported_against_the_measured_one():
    """The useful form of the answer: how wide would the spread have to be?"""
    need = costs.breakeven_spread(EXEC1_ADVERSE_SELECTION, "futures_vip0")
    ratio = need / MEASURED_SPREAD
    assert need > MEASURED_SPREAD
    assert ratio > 1000, ratio
    return f"needs {need/BPS:.3f} bps, measured {MEASURED_SPREAD/BPS:.5f} bps -- {ratio:.0f}x wider"


@check
def funding_can_be_earned_not_only_paid():
    """
    Funding is signed. A short under positive funding RECEIVES, so omitting the term is not
    conservative -- it discards a real credit as readily as a real charge.
    """
    long_pays = costs.funding_cost(0.0001, 24.0, "long")
    short_earns = costs.funding_cost(0.0001, 24.0, "short")
    assert long_pays > 0 and short_earns < 0
    assert abs(long_pays + short_earns) < 1e-15
    assert abs(long_pays - 0.0003) < 1e-15, long_pays        # three intervals in 24h
    return "24h at 1 bps/interval: long pays 3 bps, short receives 3 bps"


@check
def funding_only_charges_whole_intervals():
    """Funding is exchanged at a timestamp or not at all. A position closed at 7h59m pays
    nothing, and a model that pro-rates it would invent a cost the venue never charged."""
    assert costs.funding_cost(0.0001, 7.9, "long") == 0.0
    assert costs.funding_cost(0.0001, 8.0, "long") == 0.0001
    assert costs.funding_cost(0.0001, 15.9, "long") == 0.0001
    return "no pro-rating: 7.9h pays nothing, 8.0h pays one interval"


@check
def funding_is_material_at_reported_magnitudes():
    """
    Sanity-check the imported claim rather than repeating it. Pindza & Bambe Moutsinga report
    annualised funding impact exceeding 10% in stressed periods; confirm that such a rate is
    large beside every other term in this model.
    """
    stressed = 0.0001              # 1 bp per interval
    ann = costs.annualised_funding(stressed)
    assert ann > 0.10, ann
    daily = costs.funding_cost(stressed, 24.0, "long")
    assert daily > 20 * MEASURED_SPREAD
    return f"1 bp/interval = {ann*100:.1f}% annualised, dwarfing the spread"


@check
def risk_aversion_must_be_chosen_not_defaulted():
    """Gamma is a preference, not a measurement. A default would smuggle one in."""
    try:
        costs.inventory_cost(1000.0, 0.01, 1.0)          # no risk_aversion
    except TypeError:
        return "inventory_cost refuses to run without an explicit risk aversion"
    raise AssertionError("inventory_cost accepted a missing risk_aversion")


@check
def bnb_discount_applies_to_futures_only():
    m_f, _ = costs.fees("futures_vip0", bnb=True)
    m_s, _ = costs.fees("spot_vip0", bnb=True)
    assert abs(m_f - 0.00018) < 1e-12, m_f
    assert abs(m_s - 0.00100) < 1e-12, m_s
    return "10% off futures; spot unaffected"


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
          f"cost-model checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
