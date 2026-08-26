# Figure captions

Legends as they appear in the manuscript, reproduced verbatim so the two cannot
drift apart. Each figure has a `.pdf` (vector — use this for submission) and a
`.png` (600 dpi, for preview or Word).

Figures are numbered in order of first citation in the text, and the filenames match that numbering (see `ERRATA.md` item 21; they did not until 2026-08-26). Every plotted value
is computed from `results/` by `scripts/make_paper_figures.py`; nothing is typed
in. See `ERRATA.md` items 12–13 for what changed and why.

---

**Fig. 1. Memory traffic, not arithmetic, governs latency on this platform.** Ratios of 1280 to 640 for the unified detector — one architecture, one backbone, one thread count, with no capacity difference between the two conditions. Quadrupling the input area scales arithmetic exactly (4.00×), but last-level cache read misses grow 4.94× and measured wall-clock latency lands at 4.37×, between the two.

---

**Fig. 2. Per-image latency and energy, unified versus separate.** Mean ± SD over eight trials per configuration, consecutive within one battery session, on battery under the performance governor with four ONNX Runtime intra-op threads. For the separate configuration, per-image latency is the sum of the leaf and pest passes. Because cross-model NMS adds computation on top of two full passes, these figures understate the unified detector's advantage at the fair operating point.

---

**Fig. 3. The classes that gain from higher input resolution are the smaller ones, and they carry most of the data.** Change in AP@0.5 from 640 to 1280 for the unified detector, against mean bounding-box area (log scale). Six classes gain and six lose; the gaining set has a mean target area of 4,016 px² against 76,794 px² for the losing set, and carries 1,527 of the 1,765 validation instances against 238. Squares mark the two classes declared under-sampled in validation a priori; they are plotted for completeness and not interpreted individually. Excluding both, the area ratio falls from 19× to 9.7× and the rank correlation from ρ = −0.72 to ρ = −0.60 (p = 0.067).

---

**Fig. 4. Instrumentation and measurement node.** Power is sampled at the battery pack (13.6–16.7 V), upstream of the HAT's 5 V buck converter, so the reported draw includes the SoC, the Active Cooler, the HAT's quiescent consumption, and buck conversion loss. This is the node that sets field endurance, and it is not the node at which published bare-board figures are measured.

---
