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


def _sec(title, body, tone="v"):
    """One instrument section. `tone` drives the status LED: v verified, a attention, f failure."""
    return (f'<section><div class="label"><span class="led {tone}"></span>'
            f'<h2>{e(title)}</h2></div>{body}</section>')


def _rows(pairs):
    return "<dl class='rows'>" + "".join(
        f"<dt>{e(k)}</dt><dd>{v}</dd>" for k, v in pairs) + "</dl>"


def _chip(label, value, tone):
    return f'<span class="chip {tone}">{e(label)} <b>{e(value)}</b></span>'


def strip(status, prov):
    """
    What needs attention, before any detail. A dashboard is scanned, not read.
    """
    c = []
    lg = status.get("ledger", {})
    if "error" in lg:
        c.append(_chip("ledger", "unreadable", "f"))
    else:
        ok = lg.get("verify", {}).get("ok")
        out = len(lg.get("outstanding", []))
        c.append(_chip("chain", "verified" if ok else "FAILED", "v" if ok else "f"))
        c.append(_chip("outstanding trials", out, "v" if out == 0 else "a"))

    rc = status.get("recorder", {})
    c.append(_chip("recorder", "running" if rc.get("running") else "idle",
                   "v" if rc.get("running") else ""))

    ev = status.get("evidence", {})
    if "error" not in ev:
        stale = [x for x in ev.get("committed", []) if x.get("state") != "current"]
        behind = [x for x in ev.get("live", []) if x.get("checkpoint_behind_log")]
        n = len(stale) + len(behind)
        c.append(_chip("checkpoint drift", n, "v" if n == 0 else "f"))

    drift = [x for x in status.get("contracts", []) if x["modified_since_commit"]]
    c.append(_chip("contracts drifted", len(drift), "v" if not drift else "f"))

    unc = status.get("repo", {}).get("uncommitted", [])
    c.append(_chip("uncommitted", len(unc), "v" if not unc else "a"))

    if "error" not in prov:
        uns = len(prov.get("unsourced_canon", []))
        c.append(_chip("canon without source", uns, "v" if uns == 0 else "a"))

    return '<div class="strip">' + "".join(c) + "</div>"


def build(status, prov):
    parts = []

    # ---- ledger ----
    lg = status.get("ledger", {})
    if "error" in lg:
        parts.append(_sec("Trial ledger", f"<p class='f'>{e(lg['error'])}</p>", "f"))
    else:
        out = lg.get("outstanding", [])
        ok = lg.get("verify", {}).get("ok")
        body = _rows([
            ("chain", "<span class='v'>verified</span>" if ok
             else f"<span class='f'>FAILED — {e(lg.get('verify'))}</span>"),
            ("declared", lg.get("declared")),
            ("recorded", lg.get("recorded")),
            ("outstanding", len(out)),
        ])
        if out:
            body += "<h3>Outstanding — the question as declared, not the name</h3>"
            for t in out:
                body += (f"<div class='trial'><span class='id'>{e(t['trial_id'])}</span> "
                         f"{e(t['family'])}<div class='q'>{e(t['question'])}</div></div>")
        parts.append(_sec("Trial ledger", body, "v" if ok and not out else "a"))

    # ---- recorder ----
    rc = status.get("recorder", {})
    if rc.get("running"):
        procs = "".join(f"<li><code>{e(p)}</code></li>" for p in rc.get("processes", []))
        parts.append(_sec("Recorder",
                          f"<p class='v'>running</p><ul class='plain'>{procs}</ul>", "v"))
    else:
        parts.append(_sec("Recorder", "<p class='dim'>not running</p>", ""))

    # ---- evidence ----
    ev = status.get("evidence", {})
    if "error" in ev:
        parts.append(_sec("Evidence", f"<p class='f'>{e(ev['error'])}</p>", "f"))
    else:
        rows = ""
        for r in ev.get("live", []):
            size = (f"{r['size_bytes']/1e9:.2f} GB" if r["size_bytes"] > 1e9
                    else f"{r['size_bytes']/1e6:.1f} MB")
            warn = (" <span class='f'>checkpoint older than log</span>"
                    if r.get("checkpoint_behind_log") else "")
            ev_n = r.get("events", "?")
            ev_s = f"{ev_n:,}" if isinstance(ev_n, int) else e(ev_n)
            rows += (f"<tr><td><code>{e(r['log'])}</code></td><td class='n'>{size}</td>"
                     f"<td class='n'>{ev_s}</td>"
                     f"<td class='n'>{e(r.get('checkpoint_age') or r.get('checkpoint','?'))}"
                     f"{warn}</td></tr>")
        body = ("<div class='tablewrap'><table><thead><tr><th>log</th><th>size</th>"
                f"<th>events</th><th>checkpoint</th></tr></thead><tbody>{rows}"
                "</tbody></table></div>")
        stale = [c for c in ev.get("committed", []) if c.get("state") != "current"]
        body += "<h3>Committed checkpoints, matched to live logs by chain hash</h3><ul class='plain'>"
        for c in ev.get("committed", []):
            cls = "v" if c.get("state") == "current" else "f"
            body += (f"<li><code>{e(c['file'])}</code> — "
                     f"<span class='{cls}'>{e(c.get('state'))}</span></li>")
        body += "</ul>"
        parts.append(_sec("Evidence", body, "f" if stale else "v"))

    # ---- contracts ----
    cs = status.get("contracts", [])
    rows = "".join(
        f"<tr><td><code>{e(c['path'])}</code></td><td class='n'>{e(c['sha256'][:16])}…</td>"
        f"<td>{'<span class=f>MODIFIED</span>' if c['modified_since_commit'] else 'frozen'}"
        "</td></tr>" for c in cs)
    drift = any(c["modified_since_commit"] for c in cs)
    parts.append(_sec("Contracts",
                      f"<div class='tablewrap'><table><tbody>{rows}</tbody></table></div>",
                      "f" if drift else "v"))

    # ---- provenance ----
    if "error" in prov:
        parts.append(_sec("Provenance", f"<p class='f'>{e(prov['error'])}</p>", "f"))
    else:
        uns = prov.get("unsourced_canon", [])
        unres = prov.get("unresolved_links", [])
        body = _rows([("documents", prov.get("documents")),
                      ("links", prov.get("links")),
                      ("unresolved links", len(unres)),
                      ("orphans", len(prov.get("orphans", []))),
                      ("canon without a source", len(uns))])
        if uns:
            body += ("<h3>Canon reaching no decision record or journal</h3><ul class='plain'>"
                     + "".join(f"<li class='a'><code>{e(u)}</code></li>" for u in uns)
                     + "</ul><p class='note'>Flagged, not resolved. The Guardian flags a "
                       "missing source and does not supply one — a plausible source found "
                       "after the fact is indistinguishable from the real thing.</p>")
        parts.append(_sec("Provenance", body, "a" if (uns or unres) else "v"))

    # ---- repository ----
    rp = status.get("repo", {})
    unc = rp.get("uncommitted", [])
    body = _rows([("last commit", f"<code>{e(rp.get('last_commit'))}</code>"),
                  ("working tree", "clean" if not unc else f"{len(unc)} uncommitted")])
    if unc:
        body += "<ul class='plain'>" + "".join(
            f"<li><code>{e(u)}</code></li>" for u in unc) + "</ul>"
    parts.append(_sec("Repository", body, "v" if not unc else "a"))

    # ---- records ----
    rec = status.get("records", {})
    exps, decs = rec.get("experiments", []), rec.get("decisions", [])
    parts.append(_sec("Records", _rows([
        ("experiments", f"{len(exps)} — latest {e(exps[-1]) if exps else '—'}"),
        ("decisions", f"{len(decs)} — latest {e(decs[-1]) if decs else '—'}"),
    ]), "v"))

    return "\n".join(parts)


CSS = """
:root{
  --ground:#f6f7f8; --surface:#ffffff; --ink:#14171a; --muted:#646c74;
  --rule:#dfe3e7; --rule-strong:#c9d0d6;
  --verified:#0b6e4f; --attention:#8a5b00; --failure:#a3271b; --steel:#2e5d7d;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ground:#101214; --surface:#171a1d; --ink:#e6e9ec; --muted:#8a939c;
  --rule:#262b30; --rule-strong:#343b42;
  --verified:#4fb58b; --attention:#d9a441; --failure:#e0705f; --steel:#7faecb;
}}
:root[data-theme="dark"]{
  --ground:#101214; --surface:#171a1d; --ink:#e6e9ec; --muted:#8a939c;
  --rule:#262b30; --rule-strong:#343b42;
  --verified:#4fb58b; --attention:#d9a441; --failure:#e0705f; --steel:#7faecb;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font:14px/1.55 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  padding:32px 20px 72px;
}
.wrap{max-width:880px;margin:0 auto}

h1{font-size:19px;font-weight:600;letter-spacing:-.01em;margin:0 0 3px;text-wrap:balance}
.stamp{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:11.5px;color:var(--muted);margin:0 0 24px;
  font-variant-numeric:tabular-nums;
}

/* state strip — the summary before the detail */
.strip{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 30px}
.chip{
  display:inline-flex;align-items:baseline;gap:7px;
  border:1px solid var(--rule-strong);padding:5px 10px;
  font-size:11.5px;letter-spacing:.03em;
}
.chip b{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-variant-numeric:tabular-nums;font-weight:600;
}
.chip.v{border-color:var(--verified);color:var(--verified)}
.chip.a{border-color:var(--attention);color:var(--attention)}
.chip.f{border-color:var(--failure);color:var(--failure)}

section{border-top:1px solid var(--rule);padding:18px 0 6px}
.label{display:flex;align-items:center;gap:8px;margin:0 0 14px}
.led{width:7px;height:7px;flex:none;background:var(--muted)}
.led.v{background:var(--verified)}
.led.a{background:var(--attention)}
.led.f{background:var(--failure)}
h2{
  font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.11em;
  color:var(--muted);margin:0;
}
h3{font-size:12px;font-weight:600;margin:18px 0 8px;color:var(--ink)}

.rows{display:grid;grid-template-columns:auto 1fr;gap:5px 20px;font-size:13px}
.rows dt{color:var(--muted)}
.rows dd{
  margin:0;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-variant-numeric:tabular-nums;font-size:12.5px;
}

.tablewrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:6px 14px 6px 0;border-bottom:1px solid var(--rule);vertical-align:top}
thead th{
  font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;
  color:var(--muted);font-weight:600;border-bottom-color:var(--rule-strong);
}
td.n{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}

ul.plain{list-style:none;padding:0;margin:6px 0 0;font-size:12.5px}
ul.plain li{padding:3px 0;border-bottom:1px solid var(--rule)}
ul.plain li:last-child{border-bottom:0}

.trial{border:1px solid var(--rule-strong);padding:10px 12px;margin:0 0 8px}
.trial .id{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--steel)}
.trial .q{color:var(--muted);font-size:12.5px;margin-top:5px}

.v{color:var(--verified)}.a{color:var(--attention)}.f{color:var(--failure)}
.dim{color:var(--muted)}
.note{color:var(--muted);font-size:12px;font-style:italic;margin:10px 0 0;max-width:62ch}
footer{
  border-top:1px solid var(--rule-strong);margin-top:34px;padding-top:16px;
  color:var(--muted);font-size:12px;max-width:66ch;
}
a{color:var(--steel)}
:focus-visible{outline:2px solid var(--steel);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


def page(status, prov):
    gen = status.get("generated_at") or datetime.now(timezone.utc).isoformat()
    commit = status.get("repo", {}).get("last_commit", "—")
    return f"""<title>Genesis — where things stand</title>
<style>{CSS}</style>
<div class="wrap">
<h1>Genesis — where things stand</h1>
<p class="stamp">generated {e(gen)}<br>{e(commit)}</p>
{strip(status, prov)}
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
