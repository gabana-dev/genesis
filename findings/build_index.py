"""Regenerate findings/index.json from the .md files. The README says this file is generated and
never hand-written; until now no generator existed and the index had drifted four findings behind.

Stdlib only, like everything else in the data path.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def front_matter(path):
    text = open(path).read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).split("\n"):
        if not line.strip() or line.startswith(("#", " ")):
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[k.strip()] = v
    return out


def main():
    findings = []
    for fn in sorted(os.listdir(HERE)):
        if not (fn.startswith("F-") and fn.endswith(".md")):
            continue
        fm = front_matter(os.path.join(HERE, fn))
        if not fm:
            print(f"  SKIPPED (no front matter): {fn}")
            continue
        fm["path"] = f"findings/{fn}"
        findings.append(fm)
    doc = {"generated_from": "findings/*.md", "findings": findings}
    with open(os.path.join(HERE, "index.json"), "w") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")
    print(f"{len(findings)} findings: " + ", ".join(f["id"] for f in findings))


if __name__ == "__main__":
    main()
