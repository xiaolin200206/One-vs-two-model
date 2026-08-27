# Update, 2026-08-26

Nine items added to `ERRATA.md` (16–24) after two line-by-line audits of the
manuscript against this repository, and a reframing of the deployment. One
earlier item was amended.

## The reframing (item 22)

The device is **carried, not installed**. A grower walks a weekly patrol split
into two segments of ~350 trees, stopping at each tree to inspect, photograph
and wait. Earlier text described an unattended continuous-inference node. The
correction changes two headline numbers by more than an order of magnitude:

| | per-image | **per-segment** |
|---|---|---|
| architecture, @640 | +40.4% energy | **+0.4%** |
| resolution, unified | +325.9% energy | **+1.9%** |

**98.8% of a patrol's energy is the platform idle floor.** What binds instead is
the wait at the tree (358 ms vs. 511 ms) and the accuracy of the classes that
carry the decision. Higher resolution buys pest accuracy and loses the large
disease targets, and it is the diseases that kill trees — so the operating point
is the unified detector at 640, on latency and consequential accuracy rather
than on energy.

New: `scripts/session_budget.py`, which computes the patrol budget from
`results/` with nothing hard-coded.

## Post-reframing audit (item 24)

An independent recomputation of every figure in the reframed text found four
numeric inconsistencies, all traceable to one scripted find-and-replace whose
target string silently failed to match: the segment effect of architecture read
0.8% in the Results and 0.4% in the Conclusions; energy per tree was 220.2 J
against 218.5 J in the table; the segment effect of resolution was 4.4% rather
than 1.9%; and an idle-floor range of "94%–99%" could not be reproduced at its
low end. The manuscript now quotes one configuration with the basis stated, and
`scripts/session_budget.py` prints both the incremental and the full-active-draw
framing. `4.4x` — the wait ratio — was correct and is unrelated.

Two self-citations that the reframing had reintroduced were removed. The
lesion-level annotation point is now supported by Barbedo (2019),
*Biosystems Engineering* **180**, 96–107, and the fielded two-model
configuration is described rather than cited. No claim in the paper now depends
on unpublished work; both manuscripts remain disclosed in the cover letter.

## Corrections (items 16–21, 23)

- **16** — reference [19] middle author: `Cheema, A.` → **`Cheema, M.A.`** Item
  9's blanket claim that all 28 references were correct is withdrawn.
- **17** — the second-model FLOP subtraction was not reconstructable from the
  published tables (112.0 − 86.3 = 25.7, but the text says 25.8; the subtraction
  is against the **leaf** model at 86.2). A leaf-model row was added.
- **18** — "one model, one backbone, one thread count": the 640 and 1280 unified
  detectors are two separately trained models with identical topology.
- **19** — the split asymmetry now answers the resolution claim. Excluding
  `Algal`, the instance-weighted gain **rises** from +19.2% to +20.6%.
- **20** — the novelty claim needed a boundary against Kong et al., who do
  report power–energy measurements. Manuscript only.
- **21, 23** — figure filenames did not match figure numbers, and the numbering
  changed again with the reframing. `make_paper_figures.py` now writes the
  numbered names so the mapping is generated.

## Files changed

```
ERRATA.md                        items 16–23 appended; item 9 amended
README.md                        new deployment section; new session-budget
                                 section; resolution conclusion; citation
CHANGELOG_2026-08-26.md          this file
scripts/session_budget.py        NEW
scripts/make_paper_figures.py    output names
figures/CAPTIONS.md              renumbering
figures/Fig1..Fig4_*             renamed and re-rendered from results/
```

No measurement changed. `scripts/reproduce_paper.py` runs clean and its output
is unchanged; every figure was re-rendered from `results/`.
