# Three defects in Binance's public kline archives, and what they do to standard statistics

**Date:** 2026-08-13
**Status:** CLOSED — a factual finding about a public data source.
**Scope:** `https://data.binance.vision/` monthly kline archives, spot and USD-M futures.
**Verified against:** BTCUSDT 1m, 2019-01-01 → 2026-07-31, **3,983,271 bars**, zero duplicate
timestamps. Reproduction code: [`../market/data.py`](../market/data.py).

---

## Summary

Three properties of Binance's bulk kline archives are undocumented, silent, and each produces a
wrong answer rather than an error. All three were found by a contract requirement to verify
timestamp semantics against the raw bytes instead of assuming them, and each had already
produced a wrong answer before it was found.

| # | Defect | Effect if unhandled |
|---|---|---|
| 1 | **Halt-truncated bars** | Returns computed across trading halts, spanning up to hours of missing data |
| 2 | **`close_time` is unreliable** | Alignment checks that use it reject valid files or accept misaligned ones |
| 3 | **Silent millisecond → microsecond switch** | 2025+ spot bars land ~50,000 years in the future |

Defect 3 is the dangerous one, because it is invisible in any single file and only appears when
history is concatenated across the boundary — which is exactly what a research pipeline does.

## 1. Halt-truncated bars

When trading stops, Binance publishes a **short final kline at the instant of the halt**, then
a gap until trading resumes. The bar is not marked as truncated; it looks like an ordinary bar
with an unusual span.

**Example.** `2019-06-07 21:13` spans **13,524 ms** instead of 60,000, carries **zero volume
and zero trades**, and is followed by **61 missing bars**.

**Prevalence over the full series:** 22 halts, **4,089 missing bars, 0.10%** of 3,983,271.

**Why it matters.** A naive `diff` over the close series computes a return across the entire
halt as though it were one minute. At an aggregation step — 1m into 15m or 1h — a single halt
contaminates every window overlapping it. The correct handling is to aggregate only inside
contiguous segments and report the discarded remainder rather than interpolate it: MEASURE-1
measured that cost at **11 of 2,766 daily blocks, 0.4%**.

## 2. `close_time` is unreliable

The natural way to verify interval semantics is `close_time == open_time + interval − 1`. In
these archives that field is sometimes simply wrong, with no halt to explain it.

**Example.** `2021-12-24 04:59` spans **54,362 ms** and carries **1,124 trades** — so it is not
a halt — and is followed immediately by an on-schedule `05:00` bar. Nothing is missing. The
field is incorrect.

**Why it matters.** An earlier version of our verification tested opening-versus-closing
semantics through `close_time` and **rejected the file as malformed**. The data was fine; the
test rested on a field the publisher does not maintain reliably.

**What to use instead — boundary alignment**, which depends on neither quirk:

1. every `open_time` is an exact multiple of the interval, and
2. `close_time == open_time + interval − 1` for the overwhelming majority of bars.

Together these say the two columns bracket exactly one interval beginning at `open_time`. Under
interval-*closing* semantics, (2) would have to read `open_time − interval + 1`.

## 3. The silent unit change — and it is not uniform across markets

Binance switched the **spot** archives from millisecond to **microsecond** timestamps. The
change is undocumented in the files themselves: same column layout, same format, three more
digits.

**The boundary is exact, and it is venue-wide, not symbol-specific:**

| Symbol | 2024-12 first `open_time` | 2025-01 first `open_time` |
|---|---|---|
| BTCUSDT | `1733011200000` (ms) | `1735689600000000` (µs) |
| ETHUSDT | `1733011200000` (ms) | `1735689600000000` (µs) |
| SOLUSDT | `1733011200000` (ms) | `1735689600000000` (µs) |

**The USD-M futures archives did not switch.** Probed at 2025-01, 2025-04, 2025-06, 2025-07,
2025-08, 2025-12, 2026-01, 2026-06 and 2026-07 — all still milliseconds.

So as of this writing the two archives **use different time units for the same period**. Anyone
joining spot and futures history after 2024-12 without checking will align series that are a
factor of 1,000 apart.

**Why it matters.** Concatenating raw across the 2024/2025 spot boundary introduces a ~1,000×
jump in the time axis, placing every 2025+ bar roughly fifty thousand years ahead of its
predecessor. Nothing raises an error. Any time-indexed computation — resampling, alignment,
rolling windows, event studies — silently produces nonsense.

**Detection is easy once you know:** ms since epoch is ~1.7 × 10¹² for the 2020s, µs is
~1.7 × 10¹⁵. Normalise by magnitude, and floor rather than divide — a µs `close_time` ending
`…59999999` becomes `…59999.999`, and that fractional millisecond is not real precision.

```python
if open_time > 1e14:                       # microseconds
    open_time  = math.floor(open_time  / 1000)
    close_time = math.floor(close_time / 1000)
```

## A fourth test that looks reasonable and is invalid

`open[i] == close[i−1]` fails for **51.8%** of adjacent bars. That is not misalignment: the
first trade of a minute is generally not at the last trade price of the previous minute. It is
ordinary microstructure — a real price jump at the boundary — and using it as a validity check
would reject every correct file. Recorded because it is also a fact about minute-to-minute
price changes, and it bears directly on Roll-estimator results.

## Reproduction

```bash
python - <<'PY'
import io, zipfile, urllib.request
B = "https://data.binance.vision/data/{m}/monthly/klines"
def first_open_time(market, sym, y, mo, interval="1d"):
    url = f"{B.format(m=market)}/{sym}/{interval}/{sym}-{interval}-{y}-{mo:02d}.zip"
    with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(url).read())) as z:
        for line in z.read(z.namelist()[0]).decode().splitlines():
            if line[:1].isdigit():
                return int(line.split(",")[0])
for market in ("spot", "futures/um"):
    for y, mo in ((2024, 12), (2025, 1)):
        v = first_open_time(market, "BTCUSDT", y, mo)
        print(market, y, mo, v, "us" if v > 1e14 else "ms")
PY
```

Halt and `close_time` checks: [`verify_timestamp_semantics()`](../market/data.py), which runs
on every ingest rather than once.

## Scope and honesty about what this is

This is a **data-quality finding about a public archive**, not a discovery about markets. It
claims nothing about prices, predictability or trading. It is confined to the bulk archives at
`data.binance.vision`; the REST endpoint has not been checked and may differ.

The prevalence figures are BTCUSDT-specific. The unit switch was confirmed across three symbols
and both markets; halt counts were not.

Verified 2026-08-13. Archives can change, and a finding about a live data source has a
shelf life.

## Why it is recorded

Genesis's own results depended on getting these right — the halt handling alone changes the
aggregation on which every variance ratio in
[`experiments/0008-measure-1-cost-of-being-right.md`](experiments/0008-measure-1-cost-of-being-right.md)
rests. But the finding is independent of Genesis's research direction and useful to anyone
using the same source, which is a large number of people.

It is also a small instance of a claim made in
[`journal/2026-08-10-two-arguments-against-the-same-target.md`](journal/2026-08-10-two-arguments-against-the-same-target.md):
what a venue publishes freely marks where the competition is not. The edge available in public
data is **operational correctness**, not information.
