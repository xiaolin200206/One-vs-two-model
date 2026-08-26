# Update, 2026-08-26

Six items added to `ERRATA.md` (16–21) after a line-by-line audit of the
manuscript against this repository. One earlier item was amended.

## Substantive

- **19 — the split asymmetry now answers the resolution claim.** `Algal` is one
  of the six classes that gain from 1280 and is the one class whose training
  data differs between the two resolutions. Excluding it, the instance-weighted
  gain rises from **+19.2% to +20.6%** and ρ from −0.720 to −0.727. The confound
  runs in the paper's favour; it is now stated rather than left to be found.

## Corrections

- **16 — reference [19] middle author.** `Cheema, A.` → **`Cheema, M.A.`**
  (Muhammad Aamir Cheema). The initial came from the arXiv preprint; the
  citation is to the published LNCS chapter. **Item 9's blanket claim that all
  28 references were correct is withdrawn** and amended in place.
- **17 — the second-model FLOP subtraction was not reconstructable.** The tables
  gave 112.0 and 86.3, from which a reader computes 25.7, while the text says
  25.8. The subtraction is against the **leaf** model at 86.2. A leaf-model row
  is added to the subtraction table.
- **18 — "one model, one backbone, one thread count."** The 640 and 1280 unified
  detectors are two separately trained models with identical topology and
  parameter count. Reworded to "one architecture … with no capacity difference
  between the two conditions," in the README, the caption, and inside the
  figure.
- **20 — the novelty claim needed a boundary against Kong et al.**, who do
  report power–energy measurements. The two qualifiers that make the claim true
  — hardware counters on the executing core, and energy upstream of the node's
  regulator — are now explicit. Manuscript only.
- **21 — figure filenames did not match figure numbers.** Item 13 renumbered the
  figures and updated `CAPTIONS.md` but not the filenames, so all four
  disagreed with their own captions. Renamed, and
  `scripts/make_paper_figures.py` now writes the new names so the mapping is
  generated rather than maintained.

## Files changed

```
ERRATA.md                        items 16–21 appended; item 9 amended
README.md                        items 17, 18, 19
figures/CAPTIONS.md              item 18 wording; filename note
figures/Fig1_memory_traffic.*    renamed from Fig3_scaling_decomposition, re-rendered
figures/Fig2_latency_energy.*    renamed from Fig4_latency_energy, re-rendered
figures/Fig3_ap_gain_vs_area.*   renamed from Fig2_ap_gain_vs_area, re-rendered
figures/Fig4_measurement_chain.* renamed from Fig1_measurement_chain, re-rendered
scripts/make_paper_figures.py    output names; scaling-figure subtitle
```

No result changed. Every figure was re-rendered from `results/`;
`scripts/reproduce_paper.py` runs clean and its output is unchanged.
