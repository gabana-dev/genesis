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

import events as E

SNAPSHOT = "orderbook_snapshot"
DELTA = "orderbook_delta"

# A venue timestamp further from receipt than this is recorded as an anomaly, not corrected.
CLOCK_ANOMALY_MS = 60_000


class Ingestor:
    def __init__(self, log, connection_id=None):
        self.log = log
        self.connection_id = connection_id or "unknown"
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
            key = self._seq_key(raw, world.get("channel") or "unknown",
                                world.get("market_ticker"))
            self._last_seq[key] = seq
            self._remember(key, seq, E.content_hash(raw.get("msg") or {}))

    def _remember(self, key, seq, digest):
        seen = self._seen.setdefault(key, {})
        seen[seq] = digest
        if len(seen) > self.SEEN_LIMIT:
            for old in sorted(seen)[:len(seen) - self.SEEN_LIMIT]:
                seen.pop(old, None)

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
        return self.log.append(E.RECORDER, "ERROR", {"kind": kind, "detail": str(detail)})

    def malformed(self, payload, detail):
        return self.log.append(E.RECORDER, "MALFORMED_MESSAGE",
                               {"payload": str(payload)[:4000], "detail": str(detail),
                                "connection_id": self.connection_id})

    # ---- observation --------------------------------------------------------------

    def _seq_key(self, raw, channel, market_ticker):
        sid = raw.get("sid")
        return ("sid", sid) if sid is not None else ("cm", channel, market_ticker)

    def observe(self, raw, received_at=None):
        """
        Record one inbound venue message. Emits a SEQUENCE_GAP first when the sequence
        skips -- the gap is never repaired and the missing deltas are never synthesised.
        """
        received_at = received_at or E.now()
        if not isinstance(raw, dict):
            return self.malformed(raw, "not a JSON object")
        if E.has_non_finite(raw):
            return self.malformed(raw, "payload contains NaN or Infinity; not valid JSON")

        channel = raw.get("type") or "unknown"
        msg = raw.get("msg") if isinstance(raw.get("msg"), dict) else {}
        market_ticker = msg.get("market_ticker")
        seq = raw.get("seq")

        if seq is not None:
            key = self._seq_key(raw, channel, market_ticker)
            last = self._last_seq.get(key)
            digest = E.content_hash(msg)
            prior = self._seen.get(key, {}).get(seq)

            if prior is not None:
                # A repeat of a sequence already recorded. It is not appended as an
                # observation -- applying it twice would corrupt the book -- but the payload
                # is preserved inside the anomaly, so nothing is hidden.
                return self.log.append(
                    E.RECORDER, "DUPLICATE_MESSAGE",
                    {"channel": channel, "market_ticker": market_ticker, "seq": seq,
                     "conflict": prior != digest,
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
            self._last_seq[key] = seq if last is None else max(last, seq)
            self._remember(key, seq, digest)

        self._check_clock(msg.get("ts_ms"), received_at, market_ticker, channel)

        body = E.observation_body(raw, received_at, self.connection_id, channel)
        ev = self.log.append(E.WORLD, channel, body)

        # A field the recorder cannot interpret is recorded, never dropped and never
        # defaulted. The observation stands -- we did see the message -- but the anomaly
        # makes the projection incomplete rather than plausibly wrong.
        invalid = (body.get("world", {}).get("canonical") or {}).get("invalid")
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
