"""
Isobath as an MCP server: liquidation vulnerability, readable by agents.

WHY (product/PLAN.md §5.2). Agents do not pay; they CITE, and a citation is a customer arriving
pre-trusted. A page competes for screen space against every other dashboard. A tool an agent can
call becomes a thing other software depends on, which is much harder to displace.

THE RULE THAT MAKES THIS DIFFERENT FROM A JSON DUMP: every tool response carries its coverage and
its provenance tier. A model that cites a figure must be able to cite the limit with it, because
a number without its coverage is exactly what this product exists not to publish -- and an agent
repeating our number to someone else is the case where that matters most. There is no tool here
that returns a forecast; the `predicted` tier is empty on purpose.

Hand-rolled JSON-RPC over stdio rather than the MCP SDK. The protocol is initialize, tools/list,
tools/call and a couple of notifications -- small enough that a dependency would cost more than it
saves, and this project's collectors are stdlib-only for the same reason.

    claude mcp add isobath -- python3 /path/to/product/mcp_server.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

VERSION = "0.1.0"
PROTOCOL = "2024-11-05"

SITE = os.environ.get("ISOBATH_SITE", "https://gabana-dev.github.io/genesis")
HYPERLIQUID = "https://api.hyperliquid.xyz/info"
TIMEOUT = 20


# ---------------------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------------------
def _get(url):
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def _post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def _dataset(name):
    return _get(f"{SITE}/data/{name}.json")


def usd(n):
    if n >= 1e9: return f"${n/1e9:.2f}B"
    if n >= 1e6: return f"${n/1e6:.1f}M"
    if n >= 1e3: return f"${n/1e3:.0f}k"
    return f"${n:,.0f}"


# ---------------------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------------------
def tool_market_map(asset="BTC"):
    """Where forced selling sits, and how much of it can defend itself."""
    m = _dataset("map")
    if asset.upper() != m["asset"]:
        return {"error": f"only {m['asset']} is published today",
                "asked_for": asset.upper(),
                "note": "the scanner covers one asset; others are collected but too sparse to publish"}
    t, cov = m["totals"], m["coverage"]
    return {
        "asset": m["asset"],
        "venue": m["venue"],
        "spot": m["spot_at_map"],
        "measured_at": m["map_taken_at"],
        "age_seconds": m["map_age_seconds"],
        "forced_exposure_usd": t["forced_notional_usd"],
        "vulnerable_usd": t["cannot_defend_usd"],
        "vulnerable_pct": t["cannot_defend_pct"],
        "positions_observed": t["wallets_in_band"],
        "clusters": [
            {"price": c["price"], "distance_pct": c["distance_pct"], "side": c["side"],
             "exposure_usd": c["notional_usd"], "wallets": c["wallets"],
             "vulnerable_pct": c["cannot_defend_pct"]}
            for c in m["clusters"]
        ],
        # Never optional. An agent quoting the figure above must be able to quote this with it.
        "coverage": {
            "observed_fraction_of_open_interest": cov["observed_fraction"],
            "wallets_scanned": cov["wallets_scanned"],
            "scan_tier": cov["tier"],
            "method": cov["method"],
            "caveat": cov["note"],
            # F-0011. An agent relaying this figure to someone who will never see the site is
            # exactly where an unstated selection bias does the most damage.
            "population_bias": (
                "the hourly fast tier is the 300 largest positions by notional, which sit "
                "further from liquidation than the full universe (F-0011); this figure is not "
                "representative of all leveraged positions"
                if cov["tier"] == "fast" else "full frozen universe"
            ),
        },
        "provenance": "observed (positions) + calculated (bucketing); no predicted tier exists",
        "we_do_not_claim": m.get("we_do_not_claim", []),
    }


def tool_check_wallet(address):
    """How close one address is to liquidation, and whether it can defend itself."""
    addr = address.strip().lower()
    if not (addr.startswith("0x") and len(addr) == 42):
        return {"error": "not a Hyperliquid address; expected 0x followed by 40 hex characters"}

    st = _post(HYPERLIQUID, {"type": "clearinghouseState", "user": addr})
    mids = _post(HYPERLIQUID, {"type": "allMids"})
    ms = st.get("marginSummary") or {}
    free = float(st.get("withdrawable") or 0.0)
    used = float(ms.get("totalMarginUsed") or 0.0)

    rows = []
    for ap in st.get("assetPositions") or []:
        p = ap.get("position") or {}
        try:
            szi, liq = float(p.get("szi") or 0), float(p.get("liquidationPx") or 0)
            mid = float(mids.get(p.get("coin")) or 0)
        except (TypeError, ValueError):
            continue
        if not (szi and liq and mid):
            continue
        rows.append({"coin": p["coin"], "side": "long" if szi > 0 else "short",
                     "liquidation_price": liq, "mark": mid,
                     "distance_pct": round(abs(mid - liq) / mid * 100, 2),
                     "notional_usd": round(abs(szi) * mid, 2)})
    rows.sort(key=lambda r: r["distance_pct"])

    out = {
        "address": addr,
        "account_value_usd": float(ms.get("accountValue") or 0),
        "margin_in_use_usd": used,
        "free_collateral_usd": free,
        "can_defend": free > 0,
        "positions": rows,
        "closest": rows[0] if rows else None,
        "provenance": "observed - read live from Hyperliquid's clearinghouse",
    }
    if not rows:
        # The failure that matters most. An agent must not report "safe" for an agent wallet.
        out["warning"] = (
            "No positions found. This can mean the account is genuinely empty, OR that this is an "
            "API/agent wallet -- those authorise trades but never hold positions, so Hyperliquid "
            "returns an empty result. An empty answer is not the same as a safe one."
        )
    if free <= 0 and rows:
        out["note"] = ("Free collateral is zero: the liquidation price cannot be moved without "
                       "depositing from outside the account.")
    return out


def tool_findings(status=None):
    """Every claim published, including the ones refuted by us."""
    sc = _dataset("scorecard")
    items = sc["findings"]
    if status:
        items = [f for f in items if f["status"].upper() == status.upper()]
    return {
        "counts": sc["counts"],
        "note": sc["note"],
        "findings": [
            {k: f.get(k) for k in
             ("id", "title", "status", "observation", "sample", "method", "confidence")}
            for f in items
        ],
        "why_refuted_entries_remain": (
            "A record that keeps only its wins is a marketing page. Refuted findings are never "
            "removed, and two of these were claims we made confidently and then disproved."
        ),
    }


def tool_limits():
    """What Isobath cannot see, stated plainly."""
    m = _dataset("map")
    cov = m["coverage"]
    return {
        "observed_fraction_this_scan": cov["observed_fraction"],
        "full_universe_estimate": cov["full_universe_estimate"],
        "estimate_reference": cov["reference"],
        "unobserved_fraction": round(1 - cov["observed_fraction"], 4),
        "asset_coverage": f"{m['asset']} on {m['venue']} only",
        "not_modelled": ["cross-margin effects from positions in other assets",
                         "anything that changed since the scan"],
        "never_published": [
            "a cascade magnitude - CASCADE-1 found reaching a cluster does not move price more "
            "than a volatility-matched minute in the same hour (F-0010)",
            "a risk rating without a measured basis",
            "any prediction; the predicted provenance tier is deliberately empty",
        ],
    }


TOOLS = [
    {
        "name": "get_market_map",
        "description": (
            "Forced-selling exposure on Hyperliquid and how much of it is VULNERABLE -- held by "
            "wallets with zero free collateral that cannot move their own liquidation price. "
            "Always returns the fraction of open interest observed; quote it with any figure."
        ),
        "inputSchema": {"type": "object",
                        "properties": {"asset": {"type": "string", "description": "e.g. BTC"}},
                        "required": []},
        "fn": lambda a: tool_market_map(a.get("asset", "BTC")),
    },
    {
        "name": "check_wallet",
        "description": (
            "How close a specific Hyperliquid address is to liquidation, and whether it has free "
            "collateral to defend itself. Reads live from the exchange. Note that an empty result "
            "may mean an API/agent wallet rather than a safe account."
        ),
        "inputSchema": {"type": "object",
                        "properties": {"address": {"type": "string",
                                                   "description": "0x + 40 hex characters"}},
                        "required": ["address"]},
        "fn": lambda a: tool_check_wallet(a.get("address", "")),
    },
    {
        "name": "get_findings",
        "description": (
            "Every claim Isobath has published with its status, sample and method -- including "
            "REFUTED findings we disproved ourselves. Filter by status: MEASURED, PRELIMINARY, "
            "ASSUMED, REFUTED, SUPERSEDED."
        ),
        "inputSchema": {"type": "object",
                        "properties": {"status": {"type": "string"}},
                        "required": []},
        "fn": lambda a: tool_findings(a.get("status")),
    },
    {
        "name": "get_limits",
        "description": (
            "What Isobath cannot see and does not claim. Call this before attributing a "
            "prediction or a cascade forecast to Isobath -- it makes neither."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "fn": lambda a: tool_limits(),
    },
]

BY_NAME = {t["name"]: t for t in TOOLS}


# ---------------------------------------------------------------------------------------
# JSON-RPC over stdio
# ---------------------------------------------------------------------------------------
def handle(msg):
    """Returns a response dict, or None for notifications, which must never be answered."""
    method, mid = msg.get("method"), msg.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "isobath", "version": VERSION},
        }}

    if method in ("notifications/initialized", "notifications/cancelled"):
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "tools": [{k: t[k] for k in ("name", "description", "inputSchema")} for t in TOOLS]
        }}

    if method == "tools/call":
        params = msg.get("params") or {}
        tool = BY_NAME.get(params.get("name"))
        if tool is None:
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32602, "message": f"unknown tool {params.get('name')!r}"}}
        try:
            payload = tool["fn"](params.get("arguments") or {})
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            # An unreachable source is reported as an error, never as an empty result: a model
            # given {} will summarise it as "no risk found", which is the worst possible failure.
            payload = {"error": f"could not reach the data source: {e}",
                       "note": "nothing is cached; this reads live, so there is no stale answer"}
        except Exception as e:                                    # noqa: BLE001
            payload = {"error": f"{type(e).__name__}: {e}"}
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "content": [{"type": "text", "text": json.dumps(payload, indent=1)}],
            "isError": "error" in payload,
        }}

    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"unknown method {method!r}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
