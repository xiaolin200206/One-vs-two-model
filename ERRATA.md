# Errata and verification log

Every system number in the manuscript was recomputed from the released CSVs and
checked against both the manuscript and the previous README. This file records
what did not match and what changed.

**Summary.** All headline results hold. Every latency, cache, energy, and
statistical figure reproduces from `results/` to the precision reported. Five
discrepancies were found; one is substantive and is corrected below, four are
rounding or wording inconsistencies.

---

## 1. Thermal headroom was overstated — substantive

**What was claimed.** Manuscript §IV-D and the previous README both stated that
the hottest single trial reached 79.3 °C against an 80 °C throttling onset,
giving "0.7 °C of headroom, indoors."

**What the released data shows.** That figure is the maximum over the *reported*
session only. This repository also releases a replication session, and in it:

| session | hottest trial | vs. 80 °C onset | throttle_bits |
|---|---|---|---|
| reported (n = 32) | 79.30 °C | −0.70 °C | 0 |
| replication (n = 32) | **80.40 °C** | **+0.40 °C** | **0** |

Ten of the 64 trials recorded ≥ 79 °C. One **crossed** the nominal onset with
the live throttling nibble still reading 0.

The coincidence that made this easy to miss: 79.30 °C is simultaneously the
hottest *trial* in the reported session and the mean peak of `Unified @1280` in
the replication session. The two are unrelated quantities that happen to share a
value.

**Why it matters.** A reviewer who opens
`results/session_replication/cachebench_combined_1280.csv` finds an 80.4 °C
trial in the eighth row. Claiming 0.7 °C of margin while releasing data showing
the margin was crossed is the kind of discrepancy that costs more credibility
than the underlying finding is worth — particularly since the corrected version
is a *stronger* result.

**Corrected statement.** There is no usable thermal headroom on this platform.
The reported session peaked 0.7 °C below the nominal onset and the replication
session crossed it, in both cases without the live throttling flag being raised.

**Second-order finding.** That a trial crossed 80 °C without raising the flag is
itself informative: the vendor's 80–85 °C band is a firmware threshold and is
not exposed as a kernel thermal-zone trip point, so `vcgencmd get_throttled`
need not report a crossing the way a trip-point breach would.

**Fixed in:** `README.md`, `scripts/reproduce_paper.py` (now scans both sessions
and lists every trial ≥ 79 °C). **Requires a manuscript edit in §IV-D.**

---

## 2. Peak temperature and throttle count are sampled, not exhaustive — limitation

`sample_env()` in `scripts/cache_benchmark.py` fires once per 20 inferences:

```python
if len(lat) % 20 == 0:
    sample_env()
```

At the measured latencies that is roughly every 7 s at 640 and every 31 s at
1280 — about 15 samples per 300-inference trial. So:

- `peak_temp` is a **sampled** maximum; the true peak may be higher.
- `throttle_bits` is a **sampled** OR; a throttling event shorter than the
  sampling interval would not be recorded.

"Zero throttling in 64 trials" is therefore a lower bound on thermal stress, not
an exhaustive observation. This was not disclosed before and now is, in the
README and in `reproduce_paper.py`.

**Not a defect in the results** — the latency data show no drift within
sessions, which is the outcome a throttling event would disturb. But the
protocol claim needs the qualifier, especially given item 1.

**Suggested fix for a future run** (not applied, as it would invalidate
comparability with the released trials): move the temperature and throttle poll
into the power-sampler thread, which already runs continuously at 2 Hz in the
parent process and does not contaminate the `perf`-counted region.

---

## 3. Board-level power ratio: 1.4–1.8× vs 1.3–1.8× — corrected

The previous README said the measured draw is **1.4–1.8×** the published
board-level figure; the manuscript says **1.3–1.8×**.

Measured active power spans 11.84–12.26 W against a published 6.8–8.8 W:

```
11.84 / 8.8 = 1.35        12.26 / 6.8 = 1.80
```

The manuscript is right. README corrected to **1.3–1.8×**.

---

## 4. Two rounding disagreements — the manuscript should change, not the data

| quantity | exact value from CSV | manuscript | README | correct |
|---|---|---|---|---|
| Separate @1280, gross E/img | 26.19455 J | 26.20 | 26.19 | **26.19** |
| Unified @1280, *P*_idle | 4.694625 W | 4.70 | — | **4.69** |

Both are the manuscript rounding up a value that rounds down. Trivial in
isolation, but they are in a table a reviewer may recompute from the released
CSVs, and the whole argument of this repository is that the numbers can be
checked. **Requires a manuscript edit in Table IV.**

---

## 5. Second-model cache overhead at 1280: 32% vs 33% — pick one

The exact ratio is 0.3438 / 0.2594 = 1.325, i.e. **+32.5%**. The manuscript
rounds the range to "20–33%", the README to "+32%". Both are defensible
roundings of the same number, but they should agree. Recommend "20–33%" in the
manuscript prose and "+32%" in the per-configuration table, with a note, or
simply "+33%" in both.

---

## What was checked and found correct

Recomputed independently from `results/` and confirmed to the last reported
digit:

- All four configurations' latency, LLC read misses, L2 refills, peak
  temperature, gross energy, and their standard deviations (Tables III, IV)
- Latency SD as a fraction of the mean: 0.54% / 0.26% / 0.53% / 0.21%
- Reductions: latency −30.0% / −29.5%; LLC −26.2% / −28.4%; L2 refill
  −27.5% / −28.1%; gross energy −28.8% / −29.0%; net energy −27.9% / −27.6%
- Welch tests, all metrics, both resolutions (largest *p* over the four headline
  contrasts is 2.5 × 10⁻¹⁴, so "all *p* < 10⁻¹³" holds)
- Second-model subtraction: 153.1 ms / 6.4 GFLOPs and 652.4 ms / 25.8 GFLOPs
  against FLOP-proportional predictions of 106.0 ms and 466.8 ms (+44%, +40%)
- FLOP throughput 60.4 / 41.8 GFLOPS (69%) and 55.3 / 39.5 GFLOPS (72%)
- LLC misses per GFLOP 0.210 / 0.252 and 0.259 / 0.344
- Capacity-matched bound: 18.86 M params, 43.2 GFLOPs, 2.00×, ≈715 ms
- Resolution scaling: arithmetic 3.995×, LLC 4.935×, latency 4.365×,
  energy 4.259×
- Endurance conversions against 72 Wh: 59,323 / 42,245 / 13,930 / 9,895
- Replication deviations: cache within 0.47%, latency within 0.82%
- On-battery witnesses: `on_battery == 1` and `vbus_mw_max == 0` on every row
  of all 32 reported trials; governor `performance` and `ort_threads` 4 on every
  row
- Accuracy: the 12-class, 10-class, and instance-weighted aggregations; the
  B2 gap decomposition at 640 (leafhopper_damage contributes 0.0265 of 0.030;
  the remaining eleven average +0.004); the 1280 reversal carried by weevil
  (−0.202) and Pink_disease (−0.135), with the unified detector leading in
  seven of the remaining ten classes
- Spearman ρ = −0.720 (*p* = 0.0082) over twelve classes, −0.700 (*p* = 0.0165)
  excluding weevil
- Gaining-class mean area 4,016 px² vs losing-class 76,794 px², a 19.1× ratio
- Instance-weighted group areas: foliar 25,809 px², pest 2,854 px², 9.0× ratio

`python scripts/reproduce_paper.py` regenerates all of the system figures above
from the CSVs, with nothing hard-coded.
