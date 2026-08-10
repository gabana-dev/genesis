"""
The single source of truth for order-book completeness.

The governing question, and the only one this module answers:

    "Can Genesis legitimately claim that this specific reconstructed book contains every
     venue-published change up to time T?"

Completeness is invalidated whenever the evidence means Genesis **cannot rule out** an
unobserved, ambiguous, uninterpretable or unreconstructable change.

This module exists because the rule was previously written twice -- once in `replay`, once in
`health` -- and the two drifted. `replay` ignored CONNECTION_CLOSED, so BAV-1 run 2 reported
`complete` through fourteen deliberate disconnections the recorder had announced itself. Five
further divergences of the same class were latent and had never fired. Two implementations of
one idea will always drift; there is now one.

WHAT THIS IS NOT ABOUT
    Reconstruction accuracy. BAV-1 run 2 measured high fidelity (M3 ~= 0.98, M4 and M6
    exactly zero) while the completeness label was wrong for every controlled probe. A stale
    book can be accurate; an incomplete record can still reconstruct well. Completeness is a
    claim about the RECORD, never about the numbers in it.

    Also not: transport health in general, account/execution resolution, probe status, or
    timestamp anomalies.
"""

# Errors are fail-safe by decision of the researcher (2026-08-10): any ERROR in the
# observation/reconstruction path invalidates completeness unless explicitly exempted.
# The exemption list is deliberately EMPTY. Exemptions require a positive demonstration
# that the error is unrelated to book observation or reconstruction, documented here.
ERROR_KIND_EXEMPTIONS = frozenset()

ALL = "*"                        # invalidates every market

_ANCHOR_TYPES = ("orderbook_snapshot", "depthSnapshot")


class CompletenessRule:
    """
    Fed events in log order; reports what each one does to completeness.

    Stateful only where the rule genuinely requires history: which markets have been
    subscribed (so a newly added market does not invalidate an unaffected one) and which
    recorder_run is current.
    """

    def __init__(self):
        self._subscribed = set()
        self._run = None

    def observe(self, ev) -> dict:
        """
        Returns {"invalidates": ALL | market | None,
                 "restores":    market | None,
                 "reason":      str | None}
        """
        cls = ev.get("event_class")
        typ = ev.get("event_type")
        body = ev.get("body") or {}
        none = {"invalidates": None, "restores": None, "reason": None}

        # Class 3 -- a change of recorder_run is a real hole whether or not the venue's
        # sequence numbers reveal it. Noted first, but it must NOT pre-empt the event's own
        # classification: the first event of a new run is often a SEQUENCE_GAP, and that
        # reason is the more specific and more useful of the two.
        run = ev.get("recorder_run")
        run_changed = self._run is not None and run != self._run
        self._run = run

        if cls == "RECORDER":
            own = self._recorder_event(typ, body)
        elif cls == "OBSERVATION" and typ in _ANCHOR_TYPES:
            own = self._anchor(ev, typ, body)
        else:
            # DECISION, INTENT, EXECUTION and ordinary observations never bear on whether
            # the record is complete.
            own = None

        if own and own.get("invalidates"):
            return own                      # specific reason wins over the generic one
        if run_changed:
            return {"invalidates": ALL, "restores": None,
                    "reason": "recorder run changed: observation was interrupted"}
        return own or none

    # ---- class 1, 2, 3 ---------------------------------------------------------------

    def _recorder_event(self, typ, body):
        market = body.get("market_ticker")
        scope = market if market else ALL

        # Class 1 -- known missing information.
        if typ == "SEQUENCE_GAP":
            return {"invalidates": scope, "restores": None,
                    "reason": f"sequence gap {body.get('missing_from')}-{body.get('missing_to')}"}

        # Class 2 -- a change we know occurred and cannot reconstruct.
        if typ == "UNINTERPRETABLE_FIELD":
            fields = ", ".join(f.get("field", "?") for f in body.get("fields") or [])
            return {"invalidates": scope, "restores": None,
                    "reason": f"uninterpretable field(s): {fields}"}
        if typ == "MALFORMED_MESSAGE":
            # Worse than uninterpretable: we cannot even read what it claimed.
            return {"invalidates": ALL, "restores": None,
                    "reason": "malformed message: payload could not be parsed"}
        if typ == "DUPLICATE_MESSAGE":
            if body.get("conflict"):
                return {"invalidates": scope, "restores": None,
                        "reason": (f"conflicting duplicate at seq {body.get('seq')}: two "
                                   "different payloads share one sequence number")}
            return None          # a byte-identical repeat loses nothing

        # Class 2/3 -- errors, fail-safe.
        if typ == "ERROR":
            kind = body.get("kind") or "unknown"
            if kind in ERROR_KIND_EXEMPTIONS:
                return None
            return {"invalidates": scope, "restores": None,
                    "reason": f"error in the observation path: {kind}"}

        # Class 3 -- periods during which Genesis was not continuously observing.
        if typ in ("CONNECTION_CLOSED", "CONNECTION_OPENED",
                   "RECORDER_STARTED", "RECORDER_STOPPED"):
            return {"invalidates": ALL, "restores": None, "reason": _WHY[typ]}

        # Class 4 -- failure to establish a trustworthy starting state.
        if typ == "ANCHOR_INVALID":
            return {"invalidates": scope, "restores": None,
                    "reason": ("anchor received but INVALID: "
                               f"{body.get('canonicalised_bids')} bids / "
                               f"{body.get('canonicalised_asks')} asks")}

        # Scoped to newly affected markets only: adding a market says nothing about a
        # market already being observed.
        if typ == "SUBSCRIPTION_CHANGED":
            new = [m for m in (body.get("market_tickers") or []) if m not in self._subscribed]
            self._subscribed.update(body.get("market_tickers") or [])
            if new:
                return {"invalidates": new[0] if len(new) == 1 else ALL, "restores": None,
                        "reason": f"newly subscribed: {', '.join(new)}; no prior history"}
            return None

        # RECONNECT_FORCED is an announcement of intent; the CONNECTION_CLOSED that follows
        # carries the epistemic content. ANCHOR_RECEIVED is bookkeeping -- received is not
        # valid is not applied. TIMESTAMP_ANOMALY concerns when, not whether. PROBE_FAILED
        # is evidence-only and excluded from reconstruction.
        return None

    # ---- class 4 ---------------------------------------------------------------------

    def _anchor(self, ev, typ, body):
        """A valid anchor is the only thing that restores completeness."""
        request = (body.get("observation") or {}).get("request") or {}

        # ANTI-CIRCULARITY. A comparison probe is evidence only: it is excluded from
        # reconstruction, so it must not restore a completeness claim about a book it never
        # contributed to. Without this a probe fired during a deliberate disconnection would
        # silently re-establish the very claim the disconnection invalidated.
        if request.get("probe_id"):
            return None

        world = body.get("world") or {}
        market = world.get("market_ticker")
        if market is None:
            market = request.get("symbol")
        canon = world.get("canonical") or {}

        if canon.get("invalid"):
            fields = ", ".join(f.get("field", "?") for f in canon["invalid"])
            return {"invalidates": market or ALL, "restores": None,
                    "reason": f"uninterpretable field(s) in {typ}: {fields}"}

        if typ == "depthSnapshot":
            # Invariant 17: at least one bid and one ask, or it establishes nothing.
            if not (canon.get("bids") and canon.get("asks")):
                return {"invalidates": market or ALL, "restores": None,
                        "reason": ("anchor received but INVALID: canonicalised to "
                                   f"{len(canon.get('bids') or [])} bids / "
                                   f"{len(canon.get('asks') or [])} asks")}

        return {"invalidates": None, "restores": market or ALL, "reason": None}


_WHY = {
    "CONNECTION_CLOSED": ("connection closed: Genesis was not observing the venue, so it "
                          "cannot claim every published change was captured"),
    "CONNECTION_OPENED": "connection opened: sequence continuity not established",
    "RECORDER_STARTED": "recorder started: no anchor yet, nothing established",
    "RECORDER_STOPPED": "recorder stopped: observation ceased",
}


def affects(outcome, market_ticker) -> bool:
    """Does this outcome's scope cover the market being reconstructed?"""
    scope = outcome.get("invalidates")
    return scope == ALL or scope == market_ticker
