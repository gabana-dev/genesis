"""
The MCP surface, tested without a network and without a client.

Two classes of thing are pinned here.

PROTOCOL: a malformed handshake means the server is simply invisible -- no agent ever reaches the
tools, and nothing errors loudly enough to notice. Notifications in particular MUST NOT be
answered; replying to one is a protocol violation that some clients treat as fatal.

CONTRACT: every tool response carries coverage and provenance. That is the whole reason this
exists rather than a JSON dump. A model repeating our number to a third party is the case where a
missing limit does the most damage, so the tests treat a missing coverage field as a failure.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "product"))
import mcp_server as M

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


# Fixtures shaped like the real datasets, so no test touches the network.
MAP = {
    "asset": "BTC", "venue": "hyperliquid", "spot_at_map": 77000.0,
    "map_taken_at": "2026-08-21T12:00:00+00:00", "map_age_seconds": 600,
    "coverage": {"observed_fraction": 0.305, "tier": "fast", "wallets_scanned": 300,
                 "method": "scanned notional / open interest", "note": "lower bound",
                 "full_universe_estimate": 0.533, "reference": "F-0003"},
    "totals": {"wallets_with_positions": 260, "wallets_in_band": 62,
               "forced_notional_usd": 49_555_333.0, "cannot_defend_usd": 47_900_000.0,
               "cannot_defend_pct": 96.8},
    "clusters": [{"distance_pct": 2.5, "price": 78961.0, "side": "buy",
                  "notional_usd": 22_820_900.0, "wallets": 1,
                  "cannot_defend_pct": 100.0, "thinly_defended_pct": 100.0}],
    "we_do_not_claim": ["no cascade magnitude"],
}
SCORECARD = {
    "counts": {"MEASURED": 6, "REFUTED": 2}, "note": "every claim",
    "findings": [
        {"id": "F-0001", "title": "a", "status": "MEASURED", "observation": "x",
         "sample": "s", "method": "m", "confidence": "c"},
        {"id": "F-0004", "title": "b", "status": "REFUTED", "observation": "y",
         "sample": "s", "method": "m", "confidence": "c"},
    ],
}


def _offline():
    M._dataset = lambda name: MAP if name == "map" else SCORECARD


def call(name, args=None):
    r = M.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                  "params": {"name": name, "arguments": args or {}}})
    return json.loads(r["result"]["content"][0]["text"]), r["result"]


@check
def test_handshake():
    r = M.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert r["result"]["protocolVersion"] == M.PROTOCOL, r
    assert r["result"]["serverInfo"]["name"] == "isobath", r
    assert "tools" in r["result"]["capabilities"], r
    return "initialize returns protocol, capabilities and server identity"


@check
def test_notifications_are_never_answered():
    """Replying to a notification is a protocol violation; some clients treat it as fatal."""
    for m in ("notifications/initialized", "notifications/cancelled"):
        assert M.handle({"jsonrpc": "2.0", "method": m}) is None, m
    # Anything else without an id is still a notification and still gets silence.
    assert M.handle({"jsonrpc": "2.0", "method": "whatever"}) is None
    # But an unknown method WITH an id is a request and must get an error back.
    r = M.handle({"jsonrpc": "2.0", "id": 7, "method": "whatever"})
    assert r["error"]["code"] == -32601, r
    return "notifications silent, unknown requests answered with an error"


@check
def test_tools_list_is_well_formed():
    r = M.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = r["result"]["tools"]
    assert len(tools) == 4, tools
    for t in tools:
        assert set(t) == {"name", "description", "inputSchema"}, t
        assert t["inputSchema"]["type"] == "object", t
        # The callable must not leak into the wire format.
        assert "fn" not in t, t
    return f"{len(tools)} tools, schemas clean, no internals leaked"


@check
def test_every_figure_carries_its_coverage():
    """The whole reason this is not a JSON dump."""
    _offline()
    out, _ = call("get_market_map")
    assert out["vulnerable_pct"] == 96.8, out
    cov = out["coverage"]
    assert cov["observed_fraction_of_open_interest"] == 0.305, cov
    assert cov["scan_tier"] == "fast" and cov["wallets_scanned"] == 300, cov
    assert "provenance" in out and "predicted" in out["provenance"], out
    return "market map carries coverage, tier and provenance"


@check
def test_unpublished_asset_is_refused_not_faked():
    _offline()
    out, _ = call("get_market_map", {"asset": "ETH"})
    assert "error" in out and out["asked_for"] == "ETH", out
    assert "forced_exposure_usd" not in out, out
    return "an asset we do not publish returns an error, never an empty map"


@check
def test_findings_include_refutations():
    _offline()
    out, _ = call("get_findings")
    assert {f["status"] for f in out["findings"]} == {"MEASURED", "REFUTED"}, out
    out, _ = call("get_findings", {"status": "refuted"})
    assert len(out["findings"]) == 1 and out["findings"][0]["id"] == "F-0004", out
    return "refuted findings are returned, and filterable, not hidden"


@check
def test_limits_names_what_we_never_publish():
    _offline()
    out, _ = call("get_limits")
    joined = " ".join(out["never_published"]).lower()
    assert "cascade" in joined and "predict" in joined, out
    assert out["unobserved_fraction"] == round(1 - 0.305, 4), out
    return "limits tool names the cascade refutation and the empty predicted tier"


@check
def test_unreachable_source_is_an_error_not_an_empty_result():
    """A model handed {} will summarise it as 'no risk found'. That is the worst failure here."""
    import urllib.error

    def boom(_name):
        raise urllib.error.URLError("down")

    M._dataset = boom
    out, result = call("get_market_map")
    assert "error" in out and "could not reach" in out["error"], out
    assert result["isError"] is True, result
    return "an unreachable source surfaces as isError, never as empty data"


@check
def test_bad_address_is_rejected_before_the_network():
    out, _ = call("check_wallet", {"address": "not-an-address"})
    assert "error" in out and "40 hex" in out["error"], out
    return "malformed addresses rejected without a request"


@check
def test_unknown_tool():
    r = M.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                  "params": {"name": "nope", "arguments": {}}})
    assert r["error"]["code"] == -32602, r
    return "unknown tool returns an invalid-params error"


def main():
    failed = 0
    for fn in _checks:
        try:
            detail = fn()
            print(f"  ok   {fn.__name__}: {detail}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
        except Exception as e:                                    # noqa: BLE001
            failed += 1
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} MCP checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
