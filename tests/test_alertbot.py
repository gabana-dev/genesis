"""
The subscription commands, tested without Telegram, the network or the real watchlist.

This is the surface a stranger touches first. Every check here is something a real person can do
by typing into a chat window -- shouting the address, pasting it with the group suffix, sending
/watch with nothing after it, subscribing twice, or trying to hold four addresses on a plan that
allows three.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "product"))
import alertbot
import alerts

CHAT = 4242
ADDR_A = "0x" + "ab" * 20
ADDR_B = "0x" + "cd" * 20
ADDR_C = "0x" + "ef" * 20
ADDR_D = "0x" + "12" * 20

# status_line() would hit the exchange. The bot's replies are what is under test, not the
# exchange's answer, so it is replaced for the duration.
alertbot.status_line = lambda addr, mids, budget: "STATUS"


def say(text, wl=None, chat=CHAT):
    wl = {} if wl is None else wl
    reply, changed = alertbot.handle(text, chat, wl, {}, {})
    return reply, changed, wl


def watched(wl, chat=CHAT):
    return wl.get(str(chat), {}).get("addresses", [])


def test_watch_accepts_an_address():
    reply, changed, wl = say(f"/watch {ADDR_A}")
    assert changed and watched(wl) == [ADDR_A], (reply, wl)
    assert "STATUS" in reply, reply


def test_watch_is_case_insensitive():
    """People paste addresses from block explorers, which checksum-case them."""
    _, changed, wl = say(f"/WATCH {ADDR_A.upper().replace('0X', '0x')}")
    assert changed and watched(wl) == [ADDR_A], wl


def test_watch_tolerates_the_group_suffix():
    """In a group chat Telegram delivers /watch@genesis_bot, not /watch."""
    _, changed, wl = say(f"/watch@some_bot {ADDR_A}")
    assert changed and watched(wl) == [ADDR_A], wl


def test_watch_rejects_rubbish():
    for bad in ("", "0x123", "my wallet", ADDR_A + "ff", "0xzz" + "ab" * 19):
        reply, changed, wl = say(f"/watch {bad}")
        assert not changed and watched(wl) == [], (bad, reply)
        assert "40 hex characters" in reply, bad


def test_watching_twice_does_not_duplicate():
    _, _, wl = say(f"/watch {ADDR_A}")
    reply, changed, _ = say(f"/watch {ADDR_A}", wl)
    assert not changed and watched(wl) == [ADDR_A], (reply, wl)
    assert "Already watching" in reply


def test_the_free_limit_holds():
    wl = {}
    for a in (ADDR_A, ADDR_B, ADDR_C):
        _, changed, _ = say(f"/watch {a}", wl)
        assert changed
    reply, changed, _ = say(f"/watch {ADDR_D}", wl)
    assert not changed and len(watched(wl)) == alerts.MAX_WATCHED, wl
    assert "/unwatch" in reply, reply


def test_unwatch_removes_and_frees_a_slot():
    wl = {}
    for a in (ADDR_A, ADDR_B, ADDR_C):
        say(f"/watch {a}", wl)
    _, changed, _ = say(f"/unwatch {ADDR_B}", wl)
    assert changed and watched(wl) == [ADDR_A, ADDR_C], wl
    _, changed, _ = say(f"/watch {ADDR_D}", wl)
    assert changed and ADDR_D in watched(wl), wl


def test_unwatch_something_untracked_is_not_a_change():
    _, changed, wl = say(f"/unwatch {ADDR_A}")
    assert not changed, wl


def test_list_before_and_after():
    reply, _, wl = say("/list")
    assert "/watch" in reply, reply
    say(f"/watch {ADDR_A}", wl)
    reply, _, _ = say("/list", wl)
    assert ADDR_A in reply, reply


def test_stop_forgets_the_chat_entirely():
    wl = {}
    say(f"/watch {ADDR_A}", wl)
    _, changed, _ = say("/stop", wl)
    assert changed and str(CHAT) not in wl, wl


def test_chats_do_not_see_each_other():
    wl = {}
    say(f"/watch {ADDR_A}", wl, chat=1)
    say(f"/watch {ADDR_B}", wl, chat=2)
    assert watched(wl, 1) == [ADDR_A] and watched(wl, 2) == [ADDR_B], wl
    say("/stop", wl, chat=1)
    assert watched(wl, 2) == [ADDR_B], wl


def test_help_and_unknown_commands_explain_themselves():
    for text in ("/start", "/help", "hello", "/nonsense"):
        reply, changed, wl = say(text)
        assert not changed and "/watch" in reply, text


def test_idle_chatter_does_not_create_a_record():
    """A chat id is personal data. Someone who only ever said hello must not end up stored.

    The first version called setdefault before dispatching, so /help created an empty record that
    a later save would persist -- holding an identifier for a person who never subscribed.
    """
    for text in ("/help", "/list", "hello", f"/unwatch {ADDR_A}", "/watch nonsense"):
        _, _, wl = say(text)
        assert wl == {}, (text, wl)


def test_the_real_watchlist_is_never_touched():
    before = os.path.getmtime(alerts.WATCHLIST) if os.path.exists(alerts.WATCHLIST) else None
    test_watch_accepts_an_address()
    test_stop_forgets_the_chat_entirely()
    after = os.path.getmtime(alerts.WATCHLIST) if os.path.exists(alerts.WATCHLIST) else None
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
          f"subscription-command checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
