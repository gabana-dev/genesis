"""
Step 1-3 of the harness: deterministic download, checksum snapshotting, schema validation.

Nothing here knows anything about models. Ingestion defects are the failure mode most
likely to invalidate everything downstream, so this stage is built and checked first.

Source: AEMO NEM public price & demand (see config.ATTRIBUTION).
"""

import hashlib
import json
import subprocess
from datetime import date

from config import (DEV_END, DEV_START, EXPECTED_COLUMNS, HOLDOUT_END, HOLDOUT_START,
                    MANIFEST, RAW_DEV, RAW_HOLDOUT, REGION, URL, require_holdout_unlocked)


def months(start, end):
    """Inclusive YYYY-MM range."""
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_month(ym, dest_dir):
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{ym}_{REGION}.csv"
    if dest.exists():
        return dest, False
    url = URL.format(ym=ym, region=REGION)
    tmp = dest.with_suffix(".part")
    # curl rather than urllib: the system Python's trust store rejects the AEMO chain.
    subprocess.run(
        ["curl", "-sSLf", "--max-time", "90", "-A", "genesis-rdb1/1.0", "-o", str(tmp), url],
        check=True,
    )
    tmp.rename(dest)
    return dest, True


def validate_schema(path):
    """Header must match the contract exactly; PERIODTYPE values are recorded, not assumed."""
    with open(path, encoding="utf-8") as fh:
        header = fh.readline().strip().split(",")
        if header != EXPECTED_COLUMNS:
            raise ValueError(f"{path.name}: unexpected header {header}")
        rows = 0
        periodtypes = set()
        regions = set()
        for line in fh:
            parts = line.rstrip("\n").split(",")
            if len(parts) != 5:
                raise ValueError(f"{path.name}: malformed row: {line!r}")
            regions.add(parts[0])
            periodtypes.add(parts[4])
            rows += 1
    if regions != {REGION}:
        raise ValueError(f"{path.name}: unexpected regions {regions}")
    return {"rows": rows, "periodtypes": sorted(periodtypes)}


def ingest(period="dev"):
    if period == "dev":
        yms, dest_dir = months(DEV_START, DEV_END), RAW_DEV
    elif period == "holdout":
        require_holdout_unlocked()
        yms, dest_dir = months(HOLDOUT_START, HOLDOUT_END), RAW_HOLDOUT
    else:
        raise ValueError(period)

    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    entry = manifest.setdefault(period, {})
    downloaded = 0
    for ym in yms:
        path, fresh = fetch_month(ym, dest_dir)
        downloaded += fresh
        info = validate_schema(path)
        info["sha256"] = sha256(path)
        info["bytes"] = path.stat().st_size
        entry[ym] = info
    manifest["_attribution"] = "Source: AEMO"
    manifest[f"_{period}_snapshot_date"] = date.today().isoformat()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {"months": len(yms), "downloaded": downloaded, "dir": str(dest_dir)}


if __name__ == "__main__":
    import sys
    print(ingest(sys.argv[1] if len(sys.argv) > 1 else "dev"))
