#!/usr/bin/env python3
"""
Patrol-segment energy budget, computed from results/ — nothing hard-coded.

The device is carried, not installed. An operator walks to a tree, photographs
it, waits for an answer, and moves on, so inference occupies a few hundred
milliseconds of a per-tree cycle measured in tens of seconds. Per-image energy
is therefore not what a patrol spends; this script converts the measured idle
and active power into the quantity that is.

    energy per tree = P_idle x (cycle - t_inference) + P_active x t_inference

Workflow parameters come from a structured interview with the grower operating
the study site: roughly 700 trees over 20 acres at 35-40 ft spacing, patrolled
once a week in two segments. Per-tree cycle time is not logged; it is swept
across a defensible range and the conclusion is checked for sensitivity to it.

Usage:  python scripts/session_budget.py
"""

import os
import csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

CONFIGS = [
    ("Unified  @640", "cachebench_combined_640.csv"),
    ("Separate @640", "cachebench_separate_640.csv"),
    ("Unified  @1280", "cachebench_combined_1280.csv"),
    ("Separate @1280", "cachebench_separate_1280.csv"),
]

# From the grower interview. Spacing 35-40 ft = 10.7-12.2 m.
TREES_TOTAL = 700
SEGMENTS_PER_PATROL = 2
TREES_PER_SEGMENT = TREES_TOTAL // SEGMENTS_PER_PATROL
PACK_WH = 72.0                      # 4S 21700, nominal
CYCLES_S = [30, 45, 60]             # per-tree cycle, swept
CYCLE_HEADLINE = 45
IMAGES_PER_TREE = 1

# Published board-level figures practitioners budget from (Tom's Hardware,
# CNX Software), both with the official Active Cooler fitted. Representative
# of the numbers in circulation, not a calibrated reference.
PUBLISHED_IDLE_W = (2.6, 3.0)
PUBLISHED_ACTIVE_W = (6.8, 8.8)


def load(fname):
    path = os.path.join(RESULTS, fname)
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    n = len(rows)
    mean = lambda k: sum(float(r[k]) for r in rows) / n
    return {
        "n": n,
        "p_idle": mean("p_idle_w"),
        "p_active": mean("p_active_w"),
        "lat_s": mean("lat_mean") / 1000.0,
        "e_img": mean("energy_per_img_j"),
    }


def per_tree_j(m, cycle_s, images):
    t_inf = m["lat_s"] * images
    return m["p_idle"] * (cycle_s - t_inf) + m["p_active"] * t_inf


def main():
    data = [(label, load(f)) for label, f in CONFIGS]

    print("=" * 78)
    print("PATROL-SEGMENT ENERGY BUDGET")
    print("=" * 78)
    print(f"  {TREES_TOTAL} trees, {SEGMENTS_PER_PATROL} segments per weekly patrol"
          f" -> {TREES_PER_SEGMENT} trees per segment")
    print(f"  {IMAGES_PER_TREE} image per tree, {PACK_WH:.0f} Wh pack\n")

    print(f"  {'configuration':<15} {'wait':>9} {'E/img':>9} "
          f"{'E/tree':>9} {'segment':>9} {'% pack':>8} {'segments':>9}")
    print(f"  {'':15} {'(ms)':>9} {'(J)':>9} {'(J)':>9} {'(Wh)':>9} "
          f"{'':8} {'/charge':>9}")
    print("  " + "-" * 74)
    for label, m in data:
        e_tree = per_tree_j(m, CYCLE_HEADLINE, IMAGES_PER_TREE)
        seg_j = e_tree * TREES_PER_SEGMENT
        seg_wh = seg_j / 3600.0
        print(f"  {label:<15} {m['lat_s']*1000:9.0f} {m['e_img']:9.2f} "
              f"{e_tree:9.1f} {seg_wh:9.1f} {100*seg_wh/PACK_WH:7.1f}% "
              f"{PACK_WH/seg_wh:9.1f}")

    print(f"\n  Sensitivity to per-tree cycle time (segment, Wh):")
    print(f"  {'configuration':<15}" + "".join(f"{c:>9}s" for c in CYCLES_S))
    for label, m in data:
        row = "".join(
            f"{per_tree_j(m, c, IMAGES_PER_TREE)*TREES_PER_SEGMENT/3600.0:>10.1f}"
            for c in CYCLES_S
        )
        print(f"  {label:<15}{row}")

    # --- what fraction of a patrol is idle ---
    print("\n" + "=" * 78)
    print("WHAT THE ENERGY IS ACTUALLY SPENT ON")
    print("=" * 78)
    for label, m in data:
        t_inf = m["lat_s"] * IMAGES_PER_TREE
        e_tree = per_tree_j(m, CYCLE_HEADLINE, IMAGES_PER_TREE)
        incremental = (m["p_active"] - m["p_idle"]) * t_inf
        gross = m["p_active"] * t_inf
        print(f"  {label:<15} inference adds {incremental:6.2f} J of "
              f"{e_tree:6.1f} J per tree = {100*incremental/e_tree:4.1f}%"
              f"   idle floor: {100 - 100*incremental/e_tree:5.1f}% (incremental)"
              f"  {100 - 100*gross/e_tree:5.1f}% (full active draw)")

    # --- architecture and resolution, at the segment level ---
    print("\n" + "=" * 78)
    print("PER-IMAGE DIFFERENCES VERSUS SEGMENT DIFFERENCES")
    print("=" * 78)
    d = dict(data)
    pairs = [
        ("architecture @640", "Unified  @640", "Separate @640"),
        ("architecture @1280", "Unified  @1280", "Separate @1280"),
        ("resolution, unified", "Unified  @640", "Unified  @1280"),
    ]
    for name, a, b in pairs:
        ma, mb = d[a], d[b]
        per_img = 100 * (mb["e_img"] - ma["e_img"]) / ma["e_img"]
        ea = per_tree_j(ma, CYCLE_HEADLINE, IMAGES_PER_TREE)
        eb = per_tree_j(mb, CYCLE_HEADLINE, IMAGES_PER_TREE)
        per_seg = 100 * (eb - ea) / ea
        lat = 100 * (mb["lat_s"] - ma["lat_s"]) / ma["lat_s"]
        print(f"  {name:<21} per-image energy {per_img:+7.1f}%   "
              f"per-segment {per_seg:+6.1f}%   wait {lat:+7.1f}%")

    # --- the idle floor is the term published figures get most wrong ---
    print("\n" + "=" * 78)
    print("MEASUREMENT NODE: THE IDLE FLOOR IS THE TERM THAT CARRIES THE BUDGET")
    print("=" * 78)
    idle_lo = min(m["p_idle"] for _, m in data)
    idle_hi = max(m["p_idle"] for _, m in data)
    act_lo = min(m["p_active"] for _, m in data)
    act_hi = max(m["p_active"] for _, m in data)
    print(f"  idle    measured at pack {idle_lo:5.2f}-{idle_hi:5.2f} W   "
          f"published at board {PUBLISHED_IDLE_W[0]:.1f}-{PUBLISHED_IDLE_W[1]:.1f} W"
          f"   ratio {idle_lo/PUBLISHED_IDLE_W[1]:.2f}-{idle_hi/PUBLISHED_IDLE_W[0]:.2f}x")
    print(f"  active  measured at pack {act_lo:5.2f}-{act_hi:5.2f} W   "
          f"published at board {PUBLISHED_ACTIVE_W[0]:.1f}-{PUBLISHED_ACTIVE_W[1]:.1f} W"
          f"   ratio {act_lo/PUBLISHED_ACTIVE_W[1]:.2f}-{act_hi/PUBLISHED_ACTIVE_W[0]:.2f}x")
    print("\n  The idle floor carries almost all of a patrol, and it is the term")
    print("  the published figures understate most. A session budget built from")
    print("  board-level numbers is wrong on the quantity that decides it.")

    # --- pack sizing ---
    seg_wh = [per_tree_j(m, CYCLE_HEADLINE, IMAGES_PER_TREE)
              * TREES_PER_SEGMENT / 3600.0 for _, m in data]
    print(f"\n  One segment costs {min(seg_wh):.1f}-{max(seg_wh):.1f} Wh, so the "
          f"{PACK_WH:.0f} Wh pack fitted here")
    print(f"  carries {PACK_WH/max(seg_wh):.1f}-{PACK_WH/min(seg_wh):.1f} segments. "
          f"Sized to one segment with a doubling for")
    print(f"  margin, {2*max(seg_wh):.0f} Wh would do; the surplus is weight an "
          f"operator carries.")
    print()


if __name__ == "__main__":
    main()
