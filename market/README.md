# market/ — MEASURE-1

Phase 2 of the market direction: **measure the environment, do not trade it.**

Contract: [`CONTRACT-measurement.md`](CONTRACT-measurement.md), frozen 2026-08-10,
`sha256 f74e8cf28f48fdd636b8ed0189a3522bdad136c8283fe222ef6a7c0e46b395d2`.
Checks: [`../tests/test_market.py`](../tests/test_market.py) (16).

No strategy code, no optimisation, no backtest, no orders, no paper trading. Every method is
imported and cited; nothing here is claimed as novel.

| File | What it does |
|---|---|
| `data.py` | Binance public kline archives → verified 1-minute series, halt-segmented |
| `stats.py` | variance ratio (Lo & MacKinlay), Roll spread, Amihud, block bootstrap, break-even |
| `book.py` | spread and slippage by walking Genesis's own recorded order books |
| `measure.py` | measurements A–J in contract order, Q1 before Q2 |

```sh
.venv/bin/python market/measure.py out.json ~/genesis-evidence/bav-1/bav3.jsonl
```

## Three data facts, each found by verification and none assumed

The contract required verifying kline timestamp semantics against the raw bytes rather than
assuming them. Doing so surfaced three properties of the source, all of which produced a wrong
answer before they were found:

1. **Halt-truncated bars.** Binance publishes a short final kline at the instant trading stops,
   then a gap. 2019-06-07 21:13 spans 13,524 ms with zero volume and zero trades, followed by
   61 missing bars. 22 halts across the history, 4,089 missing bars, 0.10% of the series.
2. **`close_time` is unreliable** in the bulk archives. 2021-12-24 04:59 spans 54,362 ms with
   1,124 trades and *no* following gap. The field is simply wrong there, so it cannot be the
   evidence for interval alignment. Boundary alignment is used instead.
3. **A silent unit change.** Binance switched the archives from millisecond to **microsecond**
   timestamps during 2025. Concatenating both unconverted would place every 2025+ bar roughly
   50,000 years in the future.

A fourth test was **tried and discarded as invalid**: `open[i] == close[i-1]` fails for 51.8%
of adjacent bars, because the first trade of a minute is not generally at the last trade price
of the previous minute. That is ordinary microstructure, not misalignment.

## Halts are never aggregated across

Aggregating across a halt would manufacture a "1-hour return" spanning six real hours and label
it an ordinary observation — an invented observation. `contiguous_segments` splits at every
halt and aggregation runs within segments only. The cost is small and measured: 11 of 2,766
daily blocks, 0.4%. Gaps are reported, never interpolated.

## One defect worth recording

The Lo-MacKinlay heteroskedasticity-robust statistic initially carried an extra factor of `n`
in `theta`, which made `z2` too small by `sqrt(n)`. A synthetic series with VR = 0.38
(theoretical 0.31) went **unrejected at p = 0.86**. On 4M real observations this would have
returned "no rejection at any horizon" — the exact result P6 predicts — and it would have been
indistinguishable from the truth. Found by testing against series with known answers, which is
why those tests exist.
