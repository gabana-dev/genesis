"""
Telegram transport. Shared by the subscription bot and the alert engine.

Chosen because it costs nothing and needs nothing: no domain, no sending reputation, no inbound
endpoint. getUpdates long-polls OUTWARD, so the whole subscription system runs from wherever the
scanner already runs. See product/ALERTS.md for the argument.

The token is read from the environment, never from a file in this repo -- the repo is public.
"""
import json, os, time, urllib.request, urllib.error

API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 65          # must exceed the long-poll timeout below, or every poll looks like a failure
POLL = 50


class NoToken(Exception):
    """Raised rather than returning None, so a missing token can never look like 'no messages'."""


def token():
    t = os.environ.get("GENESIS_TG_TOKEN", "").strip()
    if not t:
        raise NoToken("GENESIS_TG_TOKEN is not set")
    return t


def call(method, **params):
    """One API call. Returns the `result` payload, or None on failure.

    Telegram answers HTTP 200 with ok:false for application errors (blocked bot, bad chat), so
    the status code alone is not a success test.
    """
    url = API.format(token=token(), method=method)
    req = urllib.request.Request(url, data=json.dumps(params).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            out = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            out = json.loads(e.read())
        except Exception:
            return None
    except Exception:
        return None
    return out.get("result") if out.get("ok") else None


def send(chat_id, text, preview=False):
    """A message. HTML parse mode -- every interpolated value is escaped at the call site."""
    r = call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
             link_preview_options={"is_disabled": not preview})
    return r is not None


def updates(offset):
    """Long-poll. Returns (messages, next_offset). next_offset is unchanged on failure, so a
    dropped poll re-reads rather than skipping a subscriber's command."""
    r = call("getUpdates", offset=offset, timeout=POLL,
             allowed_updates=["message"])
    if not r:
        time.sleep(3)
        return [], offset
    msgs = [u["message"] for u in r if "message" in u]
    return msgs, max(u["update_id"] for u in r) + 1
