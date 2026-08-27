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
roundings of the same number, but they should agree.

**Resolved in item 9.** The exact ratios are +20.07% and +32.48%, so the range
is **20–32%**. The manuscript and the README now both use it.

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

---

## 6. Aggregate accuracy: the resolution claim was aggregation-dependent — substantive

**What was claimed.** Manuscript and README both stated that raising the input
resolution from 640 to 1280 *"does not add accuracy"* and only *"redistributes"*
it, on the strength of the 12-class macro-average moving by +0.007.

**What the released data shows.** The same predictions, on the same images,
under the other two aggregations this repository already reports:

| Aggregation | 640 | 1280 | Δ |
|---|---|---|---|
| 12-class macro (primary) | 0.483 | 0.490 | +0.007 |
| 10-class macro | 0.482 | 0.515 | +0.033 |
| **Instance-weighted** | **0.436** | **0.520** | **+0.084 (+19.2%)** |

**1,527 of the 1,765 validation instances (86.5%) sit on classes that gain**;
238 sit on classes that lose. `Psyllid` (539 inst., +0.159) and
`Psyllid_damage` (418 inst., +0.113) account for 957 instances between them.
Six-gain/six-lose "cancellation" is a property of equal class weighting only.

**Why it matters.** The two robustness aggregations were used elsewhere in the
paper to defend the unified detector in the architectural comparison, and then
not applied to the resolution claim — where they point the other way. Reporting
+0.007 as "no accuracy gain" while releasing the data that gives +0.084 is the
same class of discrepancy as item 1.

**Corrected statement.** Higher resolution *does* buy accuracy on this
workload, concentrated on the small-target classes that carry most of the
annotated instances. The recommendation of 640 stands on cost — 4.4× latency,
4.3× energy, a quarter of the endurance, no thermal headroom — and not on the
claim that 1280 buys nothing.

**Fixed in:** `README.md`, `scripts/make_paper_figures.py` (Fig. 2 title and
annotation boxes). **Applied to the manuscript** in the Summary, Bigger
Picture, Introduction, Results, Discussion, Conclusion, and Limitations.

---

## 7. The Spearman correlation was reported at its strongest form only — substantive

**What was claimed.** ρ = −0.72 (p = 0.008) over twelve classes, and ρ = −0.70
(p = 0.017) excluding `weevil`.

**What the released data shows.** Two classes are declared under-sampled and
non-interpretable *a priori* — `weevil` (4 instances) and `Pink_disease` (20).
Only the first was ever excluded from the reported correlation:

| Aggregation | n | ρ | p |
|---|---|---|---|
| All twelve classes | 12 | −0.720 | 0.008 |
| Excluding `weevil` | 11 | −0.700 | 0.017 |
| **Excluding both pre-declared classes** | **10** | **−0.600** | **0.067** |

`Pink_disease` is the extreme point of the area axis at 291,112 px² and carries
a large share of the rank correlation. Excluding both also reduces the
losing/gaining mean-area ratio from **19× to 9.7×** (4,016 vs. 39,111 px²).

**Why it matters.** Declaring two classes non-interpretable in the Methods and
then reporting a correlation that excludes only one of them is an asymmetry the
paper's own protocol makes visible. The correlation does not reach
significance at n = 10.

**Corrected statement.** The size–benefit relationship is reported as
directional evidence consistent with the mechanism, with all three ρ values and
their sensitivity stated, and not as an independently significant finding.
Twelve classes are too few to establish one.

**Fixed in:** `README.md`, `scripts/make_paper_figures.py` (Fig. 2 now prints
all three ρ values). **Applied to the manuscript** in the Results, the Fig. 2
caption, and the Limitations.

---

## 8. Welch p-values replaced by confidence intervals — reporting change

Reported *t* statistics ran to *t* = −185.1, *p* = 8.4 × 10⁻²³, with Hedges' *g*
between 34 and 92. These describe a deterministic apparatus, not evidence about
a population: within-configuration dispersion is under 0.6% of the mean, and the
eight trials of a configuration are **consecutive within a single battery
session** with the unified configuration always running first — block order
confounded with time-on-battery, as the Methods already disclose. They are not
independent in the sense a t-test assumes.

Differences with 95% Welch confidence intervals are now reported instead:

| Contrast | Difference (separate − unified) | 95% CI |
|---|---|---|
| Latency @640 | +153.1 ms | 151.3 – 154.9 |
| Latency @1280 | +652.4 ms | 645.0 – 659.7 |
| Gross energy @640 | +1.77 J | 1.72 – 1.81 |
| Gross energy @1280 | +7.59 J | 7.42 – 7.75 |

Every interval half-width falls within 3% of its point estimate. **No result
changes**; only the way the evidence is characterised. The cross-session
replication remains the more meaningful check.

**Fixed in:** `README.md`, `scripts/make_paper_figures.py` (Fig. 4 footnote).


---

## 9. Full numerical and referencing audit — corrections

Every quantitative claim in the manuscript was checked against the released
CSVs and against `refair_eval_commonval.py` output, and every reference was
verified against its published record. The following were corrected.

> **Amended 2026-08-26.** This section originally read "All 28 references
> resolve correctly; none is misattributed in author, venue, volume, or
> identifier." That claim does not hold: reference [19] carries the wrong
> middle-author initial. The corrected count is 27 of 28 on first audit; see
> item 16.

**Substantive.**

- **A directional error.** The Discussion stated that the separate
  configuration "costs 30% more latency and 29% more energy." 30% and 29% are
  the *reductions* the unified configuration achieves; the corresponding
  increases are **+42.8% / +41.8%** latency and **+40.4% / +40.8%** energy.
  Corrected to 42% and 40%.
- **An accuracy overclaim in the Introduction.** It read that the unified
  detector "matches or exceeds" the separate configuration "at both
  resolutions." Table I gives 0.490 vs. 0.493 at 1280 under fusion, so this
  contradicted the paper's own data. Replaced with the claim the Results
  actually support: accuracy does not favour the separate configuration at
  either resolution.

**Numerical.**

- Instance shares: 1,527 / 1,765 = 86.52% and 238 / 1,765 = 13.48%, so **87%
  and 13%**, not 86% and 14% (which also failed to sum correctly).
- The 10-class macro delta is quoted as **+0.033**, consistent with Table II's
  rounded 0.482 → 0.515, in all three places it appears.
- Cache read misses per GFLOP for the second model: exact ratios are
  **+20.07%** and **+32.48%**, so the range is **20–32%**, not 20–33%.
- Table IV net energy at 1280 given to two decimals (11.29, 15.59) to match
  the rest of the column.
- The peak-temperature spread across configurations is ≈2 °C in range, so "±2
  °C" is replaced with "≈2 °C".

**Wording and scope.**

- "A script that recomputes every quantitative claim" → **every *system-level*
  quantitative claim.** The accuracy aggregations depend on per-class AP from
  `refair_eval_commonval.py`, which needs the unreleased weights; those inputs
  are reproduced verbatim in `reproduce_paper.py` so the aggregation claim
  itself remains checkable.
- The Methods described 2 Hz power samples as "independent" while the Results
  argue that trials are *not* independent in the t-test sense. The former is a
  claim about register staleness and is now worded as one.
- Reference [26] (Khanam and Hussain, a YOLO11 architectural overview) was
  cited as the source of the single-stage detection paradigm. It is now cited
  for YOLO11 specifically.
- Reference [14] (Samanta and Saha, a deployment-oriented review of low-cost
  edge AI for farming) sat in a group about compression and quantisation. Moved
  to the group on agricultural single-board deployment, where it belongs.
- Reference [18] (Mishra and Lone) was buried in a bundled citation despite
  reporting the same effect from the evaluation side — that benchmark-centric
  assessment overstates deployed edge performance, by 20–30% relative between
  static-image and continuous streaming operation. Now discussed rather than
  listed.


---

## 10. Dataset provenance was described more narrowly than the data supports

**What was stated.** The Methods described the imagery as "collected under
natural field conditions in Peninsular Malaysia," which implies a single
region and author collection throughout.

**What is actually the case.** The collection was assembled from several
sources: photographs taken by the author at Peninsular Malaysian orchards,
images contributed by growers and collaborators through messaging
applications, and a smaller number obtained from growers in Vietnam. Per-image
provenance — orchard, tree, photographer, capture date — was not recorded at
collection time. An attempt to recover capture dates from EXIF on 2026-08-25
found metadata on 642 of 39,460 images in the project tree, all of them from a
later collection round belonging to a different study; none of the v1 images
retained any EXIF, the annotation-platform export having stripped it.

**Why it matters.** Without a site label there is no grouped split, so every
AP value in this paper is a pooled figure. Random splitting is known to
inflate pooled accuracy relative to site-aware splitting on datasets of this
kind, and nothing here rules out an effect of that kind.

**What it does not touch.** Both architectures are scored on the identical
validation split, so any sampling bias applies equally to each, and every
claim in the paper is a difference between configurations rather than an
absolute level. The resolution comparison is one model across two input sizes
and is likewise unaffected. What the pooled figures do not support is an
estimate of performance at an orchard outside this collection.

**Fixed in:** `README.md`. **Applied to the manuscript** in the Methods
(Dataset and integrity checks) and as a new Limitations entry. Stated
prominently in the Zenodo dataset record so that anyone downloading it is told
before they evaluate on it.


---

## 11. Data and weights released; withholding statements removed

The manuscript, the cover letter and this repository previously described the
imagery and trained weights as withheld assets of a commercialisation effort,
available only under a data-use agreement. That is no longer the case, and it
had also become inconsistent with the author's other deposit, which had already
placed overlapping imagery in the open.

Both are now deposited:

| | DOI | Licence |
|---|---|---|
| v1 dataset, 640 and 1280 exports | [10.5281/zenodo.22089067](https://doi.org/10.5281/zenodo.22089067) | CC BY-NC 4.0 |
| Six trained detectors, `.pt` and `.onnx` | [10.5281/zenodo.22089355](https://doi.org/10.5281/zenodo.22089355) | AGPL-3.0 |

Two records rather than one because the licences differ and a Zenodo record
carries a single licence: the imagery is the author's to license, while the
weights are derivatives of Ultralytics YOLO11 and inherit AGPL-3.0.

**Consequences.** The competing-interest statement no longer claims
confidentiality over any material; it declares an interest in the domain and
records that nothing is withheld. The data-availability statement now points at
both deposits. The paragraph explaining that system measurements could be
reproduced *without* the imagery is retained, because it remains true and is
useful to anyone who does not want to download 474 MB, but it is no longer
doing the work of an excuse.


---

## 12. Figures were hard-coded, and two values had drifted from the text

`scripts/make_paper_figures.py` typed its plotted values in by hand rather than
reading `results/`, while `scripts/reproduce_paper.py` computed everything from
the CSVs. Two of the typed values had drifted:

- **Fig. 3 (scaling), cache ratio.** The script computed `22.39 / 4.54` — the
  *rounded* Table III cells — giving 4.93. From the unrounded means the ratio is
  4.9355, i.e. **4.94**, which is what the text says. The figure and the text
  disagreed in the third significant figure, and the figure was the wrong one.
- **Fig. 4 (latency and energy), separate @1280 gross energy.** The script still
  carried **26.20**, the value corrected to 26.19 in item 2 of this log. The
  manuscript was fixed at the time; the figure script was not.

Both figures now read from `results/` and are regenerated from it, so a
divergence of this kind cannot recur silently. This also removes an
inconsistency with the repository's own claim that its numbers are generated
rather than transcribed: that claim held for `reproduce_paper.py` and did not
hold for the figures.

## 13. Figures renumbered to order of first citation

The manuscript contained no in-text figure citations at all: the figures
appeared only as captions. Callouts have been added — the scaling figure in the
latency section, the latency/energy figure in the energy section, the
target-size figure in the resolution section, and the measurement-chain figure
in the Methods — and the figures renumbered so that the order of first citation
runs 1, 2, 3, 4 as Cell Press requires. Old Fig. 3 is now Fig. 1, old Fig. 4 is
Fig. 2, old Fig. 2 is Fig. 3, and old Fig. 1 is Fig. 4.

## 14. Thermal significance was overstated

The manuscript stated that "both sessions yield nominally significant
*p*-values, in opposite directions." Three of the four session-by-resolution
contrasts are significant; the fourth, the replication session at 1280, gives
*p* = 0.13. `reproduce_paper.py` had printed this correctly all along. The claim
is now stated as three of four, which if anything supports the paper's position
more directly, since the paper's point is that peak temperature yields no stable
architectural ordering.

Also corrected in the same section: "no trial in any configuration throttled"
is now "no trial raised the throttling flag", since the same paragraph goes on
to explain that the flag is not a reliable witness.

## 15. Table IV, P_idle of separate @1280

Printed as 4.80; the measured mean is 4.7946, so **4.79**. `reproduce_paper.py`
prints 4.79.

---

## 16. Reference [19] is misattributed in the middle author — corrected

**What was claimed.** Item 9 of this log states that "all 28 references resolve
correctly; none is misattributed in author, venue, volume, or identifier." One
is.

**What the published record shows.** Reference [19] was cited as
*D. K. Alqahtani, A. Cheema, and A. N. Toosi*. The middle author is
**Muhammad Aamir Cheema**, cited by Springer and by every downstream citation of
the published chapter as **Cheema, M.A.** The initial "A." comes from the arXiv
preprint (arXiv:2409.16808), which lists the author as "Aamir Cheema"; the
citation here is to the published LNCS chapter, not the preprint, so the
published form governs.

The venue was also given only as "ICSOC". The chapter appeared in the
proceedings of **ICSOC 2024**, published by Springer Singapore in 2025:

> Alqahtani, D.K., Cheema, M.A., and Toosi, A.N. (2025). Benchmarking deep
> learning models for object detection on edge computing devices. In
> Service-Oriented Computing (ICSOC 2024), Lecture Notes in Computer Science,
> vol. 15404 (Springer Singapore), pp. 142–150.
> https://doi.org/10.1007/978-981-96-0805-8_11

**Why it matters.** A misattributed author initial is small in isolation. It is
not small when it sits under a blanket assurance that every reference was
verified — the assurance is what a reader relies on instead of checking, and one
counterexample retires it. Item 9's claim is amended accordingly: 27 of 28
references resolved correctly on the first audit; the twenty-eighth is corrected
here.

**Fixed in:** the manuscript reference list and `README.md`. **Item 9 of this log
is amended** to remove the blanket claim.

---

## 17. The second model's FLOP subtraction cannot be reconstructed from the published tables — corrected

**What was claimed.** The second model costs **652.4 ms for 25.8 GFLOPs** at
1280, against a FLOP-proportional prediction of 466.8 ms.

**What a reader can compute.** The complexity table reports the separate
configuration at **112.0 GFLOPs** and the unified detector at **86.3 GFLOPs**.
Subtracting those gives **25.7**, not 25.8. Nothing in the tables resolves the
difference.

The reported figure is correct. The subtraction is *separate total minus the
leaf model*, and the leaf model is **86.2 GFLOPs** — it shares the unified
model's backbone and input size and differs only in output class count, so the
two round differently at three significant figures. 112.0 − 86.2 = 25.8. At 640
the question does not arise, because leaf and unified both round to 21.6 and
28.0 − 21.6 = 6.4 either way.

**Why it matters.** The whole argument of this repository is that its numbers
can be recomputed. A reader who recomputes this one gets a different answer and
has no way to find out why. The 40% overshoot at 1280 rests on this subtraction.

**Corrected statement.** The leaf model's own arithmetic is now stated inline
wherever the subtraction appears — 21.6 versus 21.6 GFLOPs at 640, and 86.2
versus 86.3 at 1280 — so the derivation closes without external information.

**Fixed in:** the manuscript (latency section) and `README.md` (the second-model
subtraction table, which now carries a leaf-model row).

---

## 18. "One model" overstates what the resolution comparison holds fixed — corrected

**What was claimed.** The confound-free scaling result was introduced as holding
"one model, one backbone, one thread count."

**What is actually the case.** The unified detector at 640 and the unified
detector at 1280 are **two separately trained models**. They share an
architecture, a backbone, a class count, a hyperparameter set, and a seed, and
they have identical parameter counts — but they are not one model, and they were
not even trained on identical data (see item 19).

**Why it does not change the result.** The scaling claim is about arithmetic,
cache traffic, and wall time, all of which depend on the graph topology and the
input dimensions rather than on the values in the weight tensors. This is the
same property that makes the system measurements reproducible from the released
harness without the weights, stated elsewhere in this repository. There is no
capacity difference between the two conditions, which is what "no confound"
needs to mean here.

**Why it matters anyway.** The phrase claims something stronger than the
evidence, in a sentence whose entire purpose is to assert that nothing is
confounded. That is the worst possible place for a loose word.

**Corrected statement.** "One architecture, one backbone, one thread count, with
no capacity difference between the two conditions."

**Fixed in:** the manuscript (latency section, introduction) and `README.md`.

---

## 19. The split asymmetry was disclosed but never connected to the resolution claim — substantive, and the sensitivity favours the result

**What was disclosed.** Problem 6 records that the 640 and 1280 exports drew
different splits: 15 Algal-only images (159 instances) fall in validation for the
640 export and in training for the 1280 export. All four configurations are
scored on the common 1280 validation split, and the cross-export audit
establishes there is no leakage.

**What was never said.** `Algal` is **one of the six classes that gain** from
1280 (Δ +0.048, 275 validation instances, 18% of the gaining set's instances).
The 1280 model therefore had 159 Algal training instances the 640 model did not.
The instance-weighted resolution gain of **+19.2%** — the headline of the
corrected item 6 — is computed over a set that includes a class whose training
data differs between the two conditions. A reader who notices this has an
obvious objection: how much of the gain is extra training data rather than
resolution?

**What the released data shows.**

| | instance-weighted Δ | relative |
|---|---|---|
| All twelve classes | +0.0838 | **+19.2%** |
| Excluding `Algal` | +0.0904 | **+20.6%** |

The rank correlation is likewise unaffected: ρ = −0.727 (*p* = 0.011) excluding
`Algal`, against −0.720 (*p* = 0.008) over all twelve.

**Why it matters.** The confound runs the other way. Removing the only class
whose training data differs makes the resolution effect *larger*, not smaller,
so the reported figure is conservative with respect to this particular
objection. That is worth stating for the same reason item 1 was worth stating:
the objection is visible in the released data, and it is better answered than
discovered.

**Corrected statement.** The instance-weighted gain is reported as +19.2% with
the `Algal` sensitivity stated alongside it. The split asymmetry remains a
limitation for the absolute Algal figures; it does not carry the resolution
finding.

**Fixed in:** `README.md` and the manuscript (resolution section).

---

## 20. The novelty claim needs a sharper boundary against Kong et al. — wording

**What was claimed.** "No prior study, to our knowledge, measures accuracy,
latency, hardware cache counters, in-line battery-rail energy, and thermal
behavior together for the same architectural decision on the same node."

**What the cited work reports.** Kong et al. (reference [4]) explicitly include
**energy-per-inference behaviour and power–energy measurements** among the axes
of their benchmark, alongside latency, bandwidth sensitivity, and multi-core
behaviour. The sentence above remains true — their power figures are not taken
in line at a battery pack upstream of a regulator, and reading the Cortex-A76
performance monitoring unit is not available to them at all, since their models
execute on fixed-function Rockchip NPUs rather than on the general-purpose core.
But the claim as written leans on two unstated qualifiers to survive, and the
most likely reviewer of this manuscript is someone who knows that paper well.

**Why it matters.** A novelty claim that is technically true and reads as
overreaching costs more than it buys. The distinction here is real and easy to
name.

**Corrected statement.** The two qualifiers are now explicit: no prior study
measures these axes together for the same architectural decision on the same
node, and none reads hardware performance counters on the executing core or
measures energy upstream of the node's regulator.

**Fixed in:** the manuscript (introduction). No repository text is affected.

---

## 21. Figure filenames did not match the figure numbers — corrected

**What was the case.** Item 13 renumbered the figures to the order of first
citation, and `figures/CAPTIONS.md` was updated to match. The **filenames were
not**. From that point until 2026-08-26 the repository shipped:

| File | Actually contains | Caption number |
|---|---|---|
| `Fig1_measurement_chain.*` | instrumentation schematic | **Fig. 4** |
| `Fig2_ap_gain_vs_area.*` | AP gain versus target area | **Fig. 3** |
| `Fig3_scaling_decomposition.*` | memory-traffic scaling ratios | **Fig. 1** |
| `Fig4_latency_energy.*` | latency and energy | **Fig. 2** |

**Why it matters.** Every filename disagreed with its own caption, in a
directory whose `CAPTIONS.md` exists specifically so that figures and legends
cannot drift apart. Anyone assembling a submission package from these files —
including the author — would have mislabelled two of the four.

**Corrected.** The files are renamed to the citation order, and
`scripts/make_paper_figures.py` now writes them under the new names, so the
mapping is generated rather than maintained by hand:

```
Fig1_memory_traffic.*       (was Fig3_scaling_decomposition)
Fig2_latency_energy.*       (was Fig4_latency_energy)
Fig3_ap_gain_vs_area.*      (was Fig2_ap_gain_vs_area)
Fig4_measurement_chain.*    (was Fig1_measurement_chain)
```

The scaling figure's subtitle was regenerated at the same time to carry the
item 18 wording. All four figures were re-rendered from `results/`.

**Fixed in:** `figures/`, `scripts/make_paper_figures.py`, `figures/CAPTIONS.md`.

---

## 22. The deployment was described as an unattended continuous-inference node; it is a hand-carried intermittent one — substantive

**What was claimed.** The manuscript and this repository framed the work around
a sustained, unattended, battery- or solar-powered field node: "sustained
battery-powered inference," "any solar or battery budget," endurance quoted as
frames per charge under continuous inference, thermal margin argued against
tropical field ambient over long-duration operation.

**What the deployment actually is.** The device is carried, not installed. A
grower walks the orchard on a weekly patrol split into two segments of about
350 trees, stopping at each tree to inspect, photograph, wait for an answer and
move on. Inference occupies a few hundred milliseconds of a per-tree cycle
measured in tens of seconds. Workflow parameters were obtained from a
structured interview with the grower operating the study site.

**Why it matters.** It changes which conclusions bind, and it changes two of
them by more than an order of magnitude. At a 45 s per-tree cycle:

| | per-image energy | per-segment energy |
|---|---|---|
| architecture (unified vs. separate, @640) | +40.4% | **+0.4%** |
| resolution (640 → 1280, unified) | +325.9% | **+1.9%** |

**98.8% of a patrol's energy is the platform idle floor**, not inference. The
29% per-image energy advantage that the paper reported as a headline result is
worth 0.4% of a working day. Conversely the latency advantage, which a
continuous unattended node merely logs, is *experienced* — the operator waits
358 ms rather than 511 ms at every one of 350 trees.

Three further corrections follow:

- **The measurement-node finding becomes more important, not less.** The idle
  floor is understated by **1.56–1.84×** (4.7–4.8 W at the pack against
  2.6–3.0 W published at the board), and it is the term carrying almost the
  whole budget. A session budget built from board figures is wrong on the
  quantity that decides it.
- **The pack is over-specified.** One segment costs 21–23 Wh; the 72 Wh fitted
  here carries 3.2–3.4 segments. Sized to one segment with a doubling for
  margin, 45 Wh would do, and the surplus is weight carried for four hours.
- **The thermal characterisation measures a load the deployment never imposes.**
  Peak temperature was recorded under sustained 300-inference runs. A carried
  device is idle between trees. The "no usable thermal headroom" statement of
  item 1 stands as a conservative bound but does not describe field operation.

**A modelling error found while writing the script.** An intermediate draft
computed energy per tree as `P_idle x cycle + P_active x t_inference`, adding
the inference time on top of the cycle rather than placing it inside.
`scripts/session_budget.py` uses `P_idle x (cycle - t) + P_active x t`, which
is correct; the manuscript figures were corrected to match. The effect is
small (segment 21.4 -> 21.2 Wh for the unified detector at 640) but it moved
the architecture difference from 0.8% to 0.4%.

**Fixed in:** `README.md` (new deployment section, new session-budget section,
resolution conclusion), `scripts/session_budget.py` (new, computes the budget
from `results/` with nothing hard-coded), `figures/CAPTIONS.md`, and the
manuscript throughout — title, summary, highlights, bigger picture,
introduction, results, discussion, conclusions and limitations.

---

## 23. Figures renumbered again, to the order of first citation in the revised text

The reframing of item 22 moved the measurement-chain figure forward — it is now
cited in the Results, where the idle floor is discussed, rather than in the
Methods. Figures were renumbered accordingly and the files renamed with them:

```
Fig1_memory_traffic.*       unchanged
Fig2_latency_energy.*       unchanged
Fig3_measurement_chain.*    (was Fig4_measurement_chain)
Fig4_ap_gain_vs_area.*      (was Fig3_ap_gain_vs_area)
```

`scripts/make_paper_figures.py` writes the new names, so the mapping remains
generated rather than maintained by hand (item 21). All four were re-rendered
from `results/`.

---

## 24. Four numeric inconsistencies introduced by the reframing, and two self-citations removed

**How they arose.** The duty-cycle correction of item 22 was applied to the
manuscript by scripted find-and-replace. One target string did not match, the
script did not fail, and the paragraph it should have rewritten was left on the
old model while the paragraph after it was updated. The result was a manuscript
that contradicted itself. They were found by an independent recomputation of
every figure in the text against this repository, not by the author's own
review, and that is the relevant lesson: batch edits need a residue check, and
this log now records one.

**What was wrong.**

| | In the text | Correct | Source of the error |
|---|---|---|---|
| Segment effect of architecture | 0.8% in Results, 0.4% in Conclusions | **0.4%** (218.5 → 219.4 J/tree) | failed replacement; the two sections disagreed |
| Energy per tree | 220.2 J | **218.5 J** | old model `P_idle x cycle + P_active x t` |
| Segment effect of resolution | 4.4% | **1.9%** (21.24 → 21.64 Wh) | same old model |
| Idle-floor share | "94%–99%" | see below | range asserted without a stated basis |

The idle-floor range could not be reproduced at its low end. The share is
computed against the *incremental* draw of inference above the idle floor;
under that definition it is 98.8% for the unified detector at 640 at a 45 s
cycle. Charging the full active draw during inference instead gives 98.0% at
45 s and 97.0% at 30 s for the same configuration, and 88.7% and 83.6% for the
separate configuration at 1280 — the least favourable case, and below the 94%
that was claimed. The manuscript now quotes a single configuration with the
basis stated, and both framings are given in the table note and printed by
`scripts/session_budget.py`.

Note that `4.4x` — the ratio of the wait at 1280 to the wait at 640 — is
correct and unrelated; only `4.4%` was wrong.

**Two self-citations removed.** The reframed manuscript was expanded from the
original draft and reintroduced two references to the author's own
under-review work: one supporting the lesion-level annotation protocol, one
identifying the fielded two-model configuration.

- The annotation point is now supported by the published literature —
  Barbedo, J.G.A. (2019), *Biosystems Engineering* **180**, 96–107,
  doi:10.1016/j.biosystemseng.2019.02.002 — which is a stronger citation than
  an unpublished manuscript for a claim of that kind.
- The fielded configuration is now described as what it is, "the configuration
  this node actually ran before the comparison reported here," which needs no
  citation at all.

The reference list is 27 entries, with no orphaned entries and no dangling
citations. Both manuscripts remain disclosed in the cover letter, where the
disclosure belongs; the point of removing the citations is that no claim in the
paper depends on unpublished work.

**Fixed in:** the manuscript throughout, and `README.md` (idle-share basis,
annotation-protocol note).

