"""
Genesis dashboard — a static page of where things stand.

Part of the orientation layer authorised by DR0005: it reports, it does not decide. There is
no button here that declares a trial, starts a recording, or amends a contract, and there
never should be. Putting a decision surface on this layer would remove the constraint that
makes the ledger worth anything.

WHY A GENERATED SNAPSHOT AND NOT A SERVER
    A dashboard that needs a process running is a dashboard that is down when you check it.
    And a server is a write surface by default; a file cannot be one.

    More importantly, a snapshot carries the time it was true. `health.py` reports what it
    read; a checkpoint records when it was written; this page says "generated at" and means
    it. A page that silently implied it was current would be the one dishonest surface in the
    project.

WHY NO FRAMEWORK
    There is no interactivity here beyond reading. Adding a build step and a node_modules tree
    to a repository whose entire toolchain is one virtualenv is a permanent cost for a
    cosmetic gain — `ai/engineering-standards.md` §2, one implementation per idea.

Usage:  .venv/bin/python dashboard.py [--out PATH]
"""

import html
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(ROOT, ".venv", "bin", "python")
DEFAULT_OUT = os.path.join(ROOT, "dashboard.html")


def _json(script, *args):
    """Run one of the reporting tools and take its JSON. Never raises past a stated failure."""
    try:
        p = subprocess.run([PY, os.path.join(ROOT, script), *args, "--json"],
                           capture_output=True, text=True, timeout=300, cwd=ROOT)
        if p.returncode not in (0, 1):
            return {"error": f"{script} exited {p.returncode}: {p.stderr.strip()[:200]}"}
        return json.loads(p.stdout)
    except Exception as e:
        return {"error": f"{script} could not be read: {e!r}"}


def e(x):
    return html.escape(str(x))


def _card(title, body, tone="ok"):
    return f'<section class="card {tone}"><h2>{e(title)}</h2>{body}</section>'


def _kv(pairs):
    rows = "".join(f"<tr><th>{e(k)}</th><td>{v}</td></tr>" for k, v in pairs)
    return f"<table class='kv'>{rows}</table>"


def build(status, prov):
    parts = []

    # ---- ledger ----
    lg = status.get("ledger", {})
    if "error" in lg:
        parts.append(_card("Trial ledger", f"<p class='bad'>{e(lg['error'])}</p>", "bad"))
    else:
        out = lg.get("outstanding", [])
        ok = lg.get("verify", {}).get("ok")
        body = _kv([
            ("chain", "<span class='ok'>verified</span>" if ok
             else f"<span class='bad'>FAILED — {e(lg.get('verify'))}</span>"),
            ("declared", lg.get("declared")),
            ("recorded", lg.get("recorded")),
            ("outstanding", f"<strong>{len(out)}</strong>"),
        ])
        if out:
            body += "<h3>Outstanding — with the question as declared</h3><ul class='trials'>"
            for t in out:
                body += (f"<li><code>{e(t['trial_id'])}</code> <b>{e(t['family'])}</b>"
                         f"<div class='q'>{e(t['question'])}</div></li>")
            body += "</ul>"
        parts.append(_card("Trial ledger", body, "ok" if ok and not out else "warn"))

    # ---- recorder ----
    rc = status.get("recorder", {})
    if rc.get("running"):
        procs = "".join(f"<li><code>{e(p)}</code></li>" for p in rc.get("processes", []))
        parts.append(_card("Recorder", f"<p class='ok'>RUNNING</p><ul class='small'>{procs}</ul>"))
    else:
        parts.append(_card("Recorder", "<p class='muted'>not running</p>", "muted"))

    # ---- evidence ----
    ev = status.get("evidence", {})
    if "error" in ev:
        parts.append(_card("Evidence", f"<p class='bad'>{e(ev['error'])}</p>", "bad"))
    else:
        rows = ""
        for r in ev.get("live", []):
            size = (f"{r['size_bytes']/1e9:.2f} GB" if r["size_bytes"] > 1e9
                    else f"{r['size_bytes']/1e6:.1f} MB")
            warn = " <span class='bad'>checkpoint older than log</span>" if r.get(
                "checkpoint_behind_log") else ""
            rows += (f"<tr><td><code>{e(r['log'])}</code></td><td>{size}</td>"
                     f"<td>{e(r.get('events','?'))}</td>"
                     f"<td>{e(r.get('checkpoint_age') or r.get('checkpoint','?'))}{warn}</td></tr>")
        body = ("<table><thead><tr><th>log</th><th>size</th><th>events</th>"
                f"<th>checkpoint</th></tr></thead><tbody>{rows}</tbody></table>")
        stale = [c for c in ev.get("committed", []) if c.get("state") != "current"]
        body += "<h3>Committed checkpoints</h3><ul class='small'>"
        for c in ev.get("committed", []):
            cls = "ok" if c.get("state") == "current" else "bad"
            body += f"<li class='{cls}'><code>{e(c['file'])}</code> — {e(c.get('state'))}</li>"
        body += "</ul>"
        parts.append(_card("Evidence", body, "bad" if stale else "ok"))

    # ---- contracts ----
    cs = status.get("contracts", [])
    rows = "".join(
        f"<tr><td><code>{e(c['path'])}</code></td><td class='mono'>{e(c['sha256'][:16])}…</td>"
        f"<td>{'<span class=bad>MODIFIED</span>' if c['modified_since_commit'] else 'frozen'}</td></tr>"
        for c in cs)
    drift = any(c["modified_since_commit"] for c in cs)
    parts.append(_card("Contracts",
                       f"<table><tbody>{rows}</tbody></table>", "bad" if drift else "ok"))

    # ---- repository ----
    rp = status.get("repo", {})
    unc = rp.get("uncommitted", [])
    body = _kv([("last commit", f"<code>{e(rp.get('last_commit'))}</code>"),
                ("working tree", "clean" if not unc else
                 f"<span class='warn'>{len(unc)} uncommitted</span>")])
    if unc:
        body += "<ul class='small'>" + "".join(f"<li><code>{e(u)}</code></li>" for u in unc) + "</ul>"
    parts.append(_card("Repository", body, "warn" if unc else "ok"))

    # ---- provenance ----
    if "error" in prov:
        parts.append(_card("Provenance", f"<p class='bad'>{e(prov['error'])}</p>", "bad"))
    else:
        uns = prov.get("unsourced_canon", [])
        unres = prov.get("unresolved_links", [])
        body = _kv([("documents", prov.get("documents")),
                    ("links", prov.get("links")),
                    ("unresolved links", len(unres)),
                    ("orphans", len(prov.get("orphans", []))),
                    ("canon without a source", f"<strong>{len(uns)}</strong>")])
        if uns:
            body += ("<h3>Canon reaching no decision record or journal</h3><ul class='small'>"
                     + "".join(f"<li class='bad'><code>{e(u)}</code></li>" for u in uns)
                     + "</ul><p class='note'>Flagged, not resolved — the Guardian flags a "
                       "missing source and does not supply one.</p>")
        parts.append(_card("Provenance", body, "warn" if (uns or unres) else "ok"))

    # ---- records ----
    rec = status.get("records", {})
    parts.append(_card("Records", _kv([
        ("experiments", f"{len(rec.get('experiments', []))} "
                        f"(latest {e(rec.get('experiments', ['—'])[-1])})"),
        ("decisions", f"{len(rec.get('decisions', []))} "
                      f"(latest {e(rec.get('decisions', ['—'])[-1])})"),
    ])))

    return "\n".join(parts)


CSS = """
:root{--bg:#faf9f7;--fg:#1c1b19;--muted:#6b6862;--line:#e2ded7;--card:#fff;
--ok:#1f6f43;--warn:#8a5a00;--bad:#a02020;--accent:#7a4a1e}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141312;--fg:#e8e5e0;
--muted:#8f8a82;--line:#2c2a27;--card:#1b1a18;--ok:#5bb98a;--warn:#d9a441;--bad:#e06c6c;
--accent:#c99b6a}}
:root[data-theme=dark]{--bg:#141312;--fg:#e8e5e0;--muted:#8f8a82;--line:#2c2a27;--card:#1b1a18;
--ok:#5bb98a;--warn:#d9a441;--bad:#e06c6c;--accent:#c99b6a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,
BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:28px 20px 60px}
.wrap{max-width:940px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:13px;margin:0 0 26px}
.card{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--line);
border-radius:6px;padding:16px 18px;margin:0 0 14px}
.card.ok{border-left-color:var(--ok)}.card.warn{border-left-color:var(--warn)}
.card.bad{border-left-color:var(--bad)}.card.muted{border-left-color:var(--line)}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
margin:0 0 12px;font-weight:600}
h3{font-size:13px;margin:16px 0 8px;color:var(--fg)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
td,th{text-align:left;padding:5px 8px 5px 0;border-bottom:1px solid var(--line);
vertical-align:top}
table.kv th{width:190px;color:var(--muted);font-weight:400}
thead th{color:var(--muted);font-weight:600;font-size:12px}
code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
ul{margin:6px 0;padding-left:18px}ul.small{font-size:13px}
ul.trials{list-style:none;padding:0}
ul.trials li{border:1px solid var(--line);border-radius:5px;padding:9px 11px;margin:0 0 8px}
.q{color:var(--muted);font-size:13px;margin-top:4px}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}.muted{color:var(--muted)}
.note{color:var(--muted);font-size:12.5px;font-style:italic;margin:8px 0 0}
footer{color:var(--muted);font-size:12.5px;margin-top:28px;border-top:1px solid var(--line);
padding-top:14px}
.tablewrap{overflow-x:auto}
"""


def page(status, prov):
    gen = status.get("generated_at") or datetime.now(timezone.utc).isoformat()
    commit = status.get("repo", {}).get("last_commit", "—")
    return f"""<title>Genesis — where things stand</title>
<style>{CSS}</style>
<div class="wrap">
<h1>Genesis — where things stand</h1>
<p class="sub">generated {e(gen)} · {e(commit)}</p>
{build(status, prov)}
<footer>
A snapshot, not a live view: it says what was true when it was generated, which is the same
claim <code>health.py</code> and every checkpoint make. Regenerate with
<code>.venv/bin/python dashboard.py</code>.<br><br>
This layer reports. It does not decide — DR0005. There is no control here that declares a
trial, starts a recording, or amends a contract, by design.
</footer>
</div>"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = DEFAULT_OUT
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 >= len(argv):
            print("dashboard.py: --out needs a path", file=sys.stderr)
            return 2
        out = argv[i + 1]

    status = _json("status.py")
    prov = _json("provenance.py")
    open(out, "w").write(page(status, prov))
    print(f"written: {out}  ({os.path.getsize(out):,} bytes)")
    if "error" in status or "error" in prov:
        print("  note: at least one source reported an error; the page says so", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
