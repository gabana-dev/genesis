"""
Transport-agnostic ingestion: raw venue messages in, events out.

Deliberately knows nothing about WebSockets. It accepts already-received messages, which is
what makes the whole core testable without a network or credentials, and keeps the venue
adapter to one thin module.

Sequence scope is an ASSUMPTION. The Kalshi documentation states that `seq` is
"Sequential number that should be checked if you want to guarantee you received all the
messages. Used for snapshot/delta consistency," but does not state the scope over which it
increments. This module tracks it per subscription id where one is present, falling back to
(channel, market_ticker). If live observation shows a different scope, this is the one place
that changes -- and until it is confirmed against a live feed it stays marked ASSUMED in the
health report.
"""

from datetime import datetime

import dialects
import events as E

SNAPSHOT = "orderbook_snapshot"
DELTA = "orderbook_delta"

# A venue timestamp further from receipt than this is recorded as an anomaly, not corrected.
CLOCK_ANOMALY_MS = 60_000


class Ingestor:
    def __init__(self, log, connection_id=None, dialect=None, instrument=None):
        """
        ONE INGESTOR PER CONNECTION. Several may share a single EventLog -- that is how two
        venues are recorded on one clock in one hash chain -- but they must not share an
        Ingestor, because per-connection state lives here.

        D-4, found while building T0.2 and demonstrated in a real recording. When two
        connections shared one Ingestor:

          * `connection_opened` clears `_last_seq` for EVERY stream, so a reconnect on the
            liquidation feed silently disabled gap detection on the depth feed for its next
            message. Loss of detection, reported as health.
          * `connection_id` is a single field, so lifecycle events were attributed to
            whichever connection opened most recently. A 90-second futures recording logged
            BOTH closes against the depth connection and none against the liquidation
            connection -- a log saying one connection closed twice and the other never closed.

        `instrument` disambiguates venues that reuse a symbol. Binance spot and USD-M futures
        both say `BTCUSDT`, with unrelated sequence number spaces, so merging them into one
        log without it would collide on the sequence key and emit a gap on nearly every
        message. It is None for single-venue recordings, which keeps their keys and their
        event bodies exactly as they were.
        """
        self.log = log
        self.connection_id = connection_id or "unknown"
        self.instrument = instrument
        # A dialect only reads a payload; it never rewrites one. Default is Kalshi, the
        # venue this recorder was written for.
        self.dialect = dialect or dialects.KALSHI
        self._last_seq = {}
        self._seen = {}
        self._resume_sequences()

    # Bounded per-stream memory of seen sequence numbers. Enough to recognise a replayed
    # message; not so much that a long-running recorder grows without limit.
    SEEN_LIMIT = 8192

    def _resume_sequences(self):
        """
        Rebuild per-stream sequence state from the existing log.

        Without this, restarting the process resets sequence tracking to empty and the first
        message after a restart can never be seen as a gap -- the record would look continuous
        across an interval the recorder did not observe. Resuming restores detection where the
        venue's numbering allows it; `replay` independently treats any change of recorder_run
        as a continuity break, because a restart is a real hole whether or not seq reveals it.
        """
        from log import read
        for ev in read(self.log.path):
            if ev.get("event_class") != E.WORLD:
                continue
            world = ev.get("body", {}).get("world", {})
            seq = world.get("venue_seq")
            if seq is None:
                continue
            raw = world.get("raw") or {}
            # subscription_id lives under `observation`, not `world` -- reading it from the
            # wrong place silently orphans all resumed sequence state, because the live key
            # is ("sid", n) while the resumed key falls back to ("cm", channel, market).
            obs = ev.get("body", {}).get("observation", {})
            # In a shared log this Ingestor must resume ONLY its own instrument's state.
            # Without this filter it would key another venue's sequence numbers under its
            # own label -- the exact collision `instrument` exists to prevent, reintroduced
            # at startup.
            if obs.get("instrument") != self.instrument:
                continue
            sid = obs.get("subscription_id")
            key = self._seq_key(sid, world.get("channel") or "unknown",
                                world.get("market_ticker"))
            self._last_seq[key] = world.get("venue_seq_last") or seq
            self._remember(key, seq, E.content_hash(raw))

    def _remember(self, key, seq, digest):
        """
        Bounded window of recently seen sequence numbers, for duplicate detection.

        EVICTION IS O(1) AND USED TO BE O(n log n) PER EVENT. The previous version called
        `sorted(seen)` on every insert once the window was full, to drop a single entry:
        161 microseconds per event, measured. Live that is invisible at ~38 events/sec, and it
        made RESTARTS quadratic in log size -- `_resume_sequences` replays the whole log, so q5
        at 4.1M events cost ~11 minutes per Ingestor and spot-perp runs three of them. Measured
        2026-08-19 when a restart took over an hour before opening a socket, and it would have
        grown to ~1.6 hours at the recording's declared length.

        Dicts preserve insertion order, so the first key IS the oldest inserted. Sequences
        arrive monotonically in normal operation, which makes that the same entry `sorted`
        would have dropped. Where they do not -- out-of-order arrival, which is separately
        logged as SEQUENCE_GAP or sequence_regression -- forgetting the least recently seen is
        the better behaviour for a duplicate window anyway.
        """
        seen = self._seen.setdefault(key, {})
        seen[seq] = digest
        while len(seen) > self.SEEN_LIMIT:
            seen.pop(next(iter(seen)))

    # ---- lifecycle ----------------------------------------------------------------

    def started(self, config: dict):
        return self.log.append(E.RECORDER, "RECORDER_STARTED",
                               {"config": config, "recorder_run": self.log.recorder_run})

    def stopped(self, reason: str):
        return self.log.append(E.RECORDER, "RECORDER_STOPPED", {"reason": reason})

    def connection_opened(self, connection_id: str, url: str):
        self.connection_id = connection_id
        # A new connection invalidates sequence continuity: the venue may resume numbering.
        self._last_seq.clear()
        return self.log.append(E.RECORDER, "CONNECTION_OPENED",
                               {"connection_id": connection_id, "url": url})

    def connection_closed(self, reason: str):
        return self.log.append(E.RECORDER, "CONNECTION_CLOSED",
                               {"connection_id": self.connection_id, "reason": reason})

    def subscription_changed(self, channels, market_tickers, sid=None):
        return self.log.append(E.RECORDER, "SUBSCRIPTION_CHANGED",
                               {"channels": list(channels),
                                "market_tickers": list(market_tickers),
                                "sid": sid,
                                "connection_id": self.connection_id})

    def error(self, kind: str, detail):
        # connection_id is recorded so an error can be attributed to the link it came from.
        # It does NOT currently narrow completeness: errors remain fail-safe and global by
        # the researcher's decision of 2026-08-10, whose exemption list is deliberately
        # empty. Attribution is a prerequisite for that question being ASKABLE, not an
        # answer to it.
        return self.log.append(E.RECORDER, "ERROR",
                               {"kind": kind, "detail": str(detail),
                                "connection_id": self.connection_id})

    def malformed(self, payload, detail):
        return self.log.append(E.RECORDER, "MALFORMED_MESSAGE",
                               {"payload": str(payload)[:4000], "detail": str(detail),
                                "connection_id": self.connection_id})

    # ---- observation --------------------------------------------------------------

    def _seq_key(self, sid, channel, market_ticker):
        base = ("sid", sid) if sid is not None else ("cm", channel, market_ticker)
        # Prefixed only when set, so every key written before instruments existed is
        # unchanged and every prior log resumes exactly as it did.
        return base if self.instrument is None else (self.instrument, *base)

    def observe(self, raw, received_at=None, request=None):
        """
        Record one inbound venue message. Emits a SEQUENCE_GAP first when the sequence
        skips -- the gap is never repaired and the missing deltas are never synthesised.
        """
        received_at = received_at or E.now()
        if not isinstance(raw, dict):
            return self.malformed(raw, "not a JSON object")
        if E.has_non_finite(raw):
            return self.malformed(raw, "payload contains NaN or Infinity; not valid JSON")

        ex = self.dialect["extract"](raw)
        channel = ex["channel"]
        market_ticker = ex["market"]
        seq = ex["seq_first"]
        seq_last = ex["seq_last"] if ex["seq_last"] is not None else seq

        if seq is not None:
            key = self._seq_key(ex.get("subscription_id"), channel, market_ticker)
            last = self._last_seq.get(key)
            digest = E.content_hash(raw)
            prior = self._seen.get(key, {}).get(seq)

            if prior is not None:
                # A repeat of a sequence already recorded. It is not appended as an
                # observation -- applying it twice would corrupt the book -- but the payload
                # is preserved inside the anomaly, so nothing is hidden.
                return self.log.append(
                    E.RECORDER, "DUPLICATE_MESSAGE",
                    {"channel": channel, "market_ticker": market_ticker, "seq": seq,
                     "seq_last": seq_last, "conflict": prior != digest,
                     "first_content_hash": prior, "repeat_content_hash": digest,
                     "received_at": received_at, "raw": raw})

            if last is not None and seq != last + 1:
                if seq > last + 1:
                    self.log.append(E.RECORDER, "SEQUENCE_GAP",
                                    E.gap_body(channel, market_ticker, last, seq,
                                               received_at=received_at))
                else:
                    self.log.append(E.RECORDER, "ERROR",
                                    {"kind": "sequence_regression",
                                     "detail": f"last={last} received={seq}",
                                     "market_ticker": market_ticker, "channel": channel})
            self._last_seq[key] = seq_last if last is None else max(last, seq_last)
            self._remember(key, seq, digest)

        self._check_clock(ex.get("venue_ts_ms"), received_at, market_ticker, channel)

        body = E.observation_body(raw, received_at, self.connection_id, ex, request,
                                  instrument=self.instrument)
        ev = self.log.append(E.WORLD, channel, body)

        # A field the recorder cannot interpret is recorded, never dropped and never
        # defaulted. The observation stands -- we did see the message -- but the anomaly
        # makes the projection incomplete rather than plausibly wrong.
        canon = body.get("world", {}).get("canonical") or {}
        if channel == "depthSnapshot":
            n_b, n_a = len(canon.get("bids") or []), len(canon.get("asks") or [])
            self.log.append(E.RECORDER, "ANCHOR_RECEIVED",
                            {"market_ticker": market_ticker, "seq": seq,
                             "canonicalised_bids": n_b, "canonicalised_asks": n_a,
                             "anchor_valid": bool(n_b and n_a),
                             "observation_event_id": ev["event_id"],
                             "received_at": received_at})
            if not (n_b and n_a):
                self.log.append(E.RECORDER, "ANCHOR_INVALID",
                                {"market_ticker": market_ticker, "seq": seq,
                                 "canonicalised_bids": n_b, "canonicalised_asks": n_a,
                                 "detail": "snapshot canonicalised to an empty or one-sided "
                                           "book; it establishes no completeness",
                                 "received_at": received_at})

        invalid = canon.get("invalid")
        if invalid:
            self.log.append(E.RECORDER, "UNINTERPRETABLE_FIELD",
                            {"channel": channel, "market_ticker": market_ticker,
                             "seq": seq, "observation_event_id": ev["event_id"],
                             "received_at": received_at, "fields": invalid})
        return ev

    def _check_clock(self, venue_ts_ms, received_at, market_ticker, channel):
        """Record disagreement between the clocks. Never reconcile them."""
        if venue_ts_ms is None:
            return
        try:
            received_ms = datetime.fromisoformat(received_at).timestamp() * 1000.0
        except ValueError:
            return
        drift = received_ms - float(venue_ts_ms)
        if abs(drift) > CLOCK_ANOMALY_MS:
            self.log.append(E.RECORDER, "TIMESTAMP_ANOMALY",
                            {"venue_ts_ms": venue_ts_ms, "received_at": received_at,
                             "drift_ms": drift, "market_ticker": market_ticker,
                             "channel": channel})

    # ---- Genesis-side ---------------------------------------------------------------

    def decision(self, **kw):
        return self.log.append(E.DECISION, "decision", E.decision_body(**kw))

    def intent(self, **kw):
        return self.log.append(E.INTENT, "order_intent", E.intent_body(**kw))

    def execution(self, **kw):
        return self.log.append(E.EXECUTION, kw.get("kind", "unknown"), E.execution_body(**kw))
