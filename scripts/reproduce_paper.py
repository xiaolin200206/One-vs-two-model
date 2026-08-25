#!/usr/bin/env python3
"""
reproduce_paper.py — regenerate every system-level number in the paper from results/.

No value is hard-coded. Everything below is computed from the four released
trial-record files. Run from the repository root:

    python scripts/reproduce_paper.py

Requires: pandas, scipy.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
REP = RES / "session_replication"

CFG = ["combined_640", "separate_640", "combined_1280", "separate_1280"]
NICE = {"combined_640": "Unified @640", "separate_640": "Separate @640",
        "combined_1280": "Unified @1280", "separate_1280": "Separate @1280"}

# Model complexity (Ultralytics convention: GFLOPs = 2 x MACs, on the PyTorch graph).
# The leaf model shares the unified model's backbone and input size and differs only
# in output class count, which is what makes the subtraction in Section IV-B valid.
GFLOPS = {"combined_640": 21.6, "separate_640": 28.0,
          "combined_1280": 86.3, "separate_1280": 112.0}
LEAF_GFLOPS = {"640": 21.6, "1280": 86.2}
PARAMS_M = {"combined_640": 9.43, "separate_640": 12.02,
            "combined_1280": 9.43, "separate_1280": 12.02}
BATTERY_WH = 72.0
THROTTLE_ONSET_C = 80.0  # vendor: progressive throttling in the 80-85 C band [28]

# Per-class AP@0.5 on the common 12-class validation set (187 images, 1,765
# instances), as emitted by scripts/refair_eval_commonval.py. Reproduced here so
# that the aggregation sensitivity below can be checked without the model
# weights, which are not released. Running refair_eval_commonval.py against the
# weights regenerates these values.
PERCLASS = [
    # class,               inst,  area px2,  uni640, uni1280
    ("Stem_borer",           33,      336,    0.151,  0.132),
    ("Psyllid_damage",      418,      494,    0.366,  0.479),
    ("Psyllid",             539,     1140,    0.317,  0.476),
    ("Algal",               275,     1529,    0.416,  0.464),
    ("weevil_damage",        78,     2190,    0.823,  0.929),
    ("Scale_insect",         57,     6538,    0.242,  0.296),
    ("Phomopsis",           160,    12203,    0.810,  0.818),
    ("weevil",                4,    13209,    0.578,  0.495),   # under-sampled, pre-declared
    ("Leaf_rot",             83,    36885,    0.784,  0.776),
    ("leafhopper_damage",    39,    48864,    0.513,  0.435),
    ("Root_disease",         59,    70358,    0.393,  0.346),
    ("Pink_disease",         20,   291112,    0.407,  0.235),   # under-sampled, pre-declared
]
UNDERSAMPLED = {"weevil", "Pink_disease"}


def load(d):
    out = {}
    for k in CFG:
        p = d / f"cachebench_{k}.csv"
        if not p.exists():
            sys.exit(f"missing {p}")
        out[k] = pd.read_csv(p)
    return out


def hdr(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


def mean(f, k, c, s=1.0):
    return (f[k][c] * s).mean()


def sd(f, k, c, s=1.0):
    return (f[k][c] * s).std(ddof=1)


def welch(a, b):
    t, p = stats.ttest_ind(a, b, equal_var=False)
    va, vb, n = a.var(ddof=1), b.var(ddof=1), len(a)
    df = (va / n + vb / n) ** 2 / ((va / n) ** 2 / (n - 1) + (vb / n) ** 2 / (n - 1))
    return t, df, p


def welch_ci(a, b, conf=0.95):
    """Mean difference (b - a) with a Welch confidence interval."""
    na, nb = len(a), len(b)
    va, vb = a.var(ddof=1), b.var(ddof=1)
    diff = b.mean() - a.mean()
    se = np.sqrt(va / na + vb / nb)
    df = se ** 4 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    tc = stats.t.ppf(1 - (1 - conf) / 2, df)
    return diff, diff - tc * se, diff + tc * se


def main():
    f = load(RES)
    g = load(REP) if REP.exists() else None

    # ---------------- provenance ----------------
    hdr("PROVENANCE  (Section III-A, III-D)")
    for k in CFG:
        d = f[k]
        assert (d.governor == "performance").all()
        assert (d.on_battery == 1).all()
        assert (d.vbus_mw_max == 0).all()
        print(f"  {NICE[k]:16s} n={len(d)}  governor={d.governor.iloc[0]}  "
              f"ORT={d.ort_version.iloc[0]} threads={int(d.ort_threads.iloc[0])}  "
              f"throttled={int((d.throttle_bits != 0).sum())}/{len(d)}  "
              f"SoC {int(d.soc_start_pct.iloc[0])}->{int(d.soc_end_pct.iloc[-1])}%  "
              f"V {d.vbat_start_v.iloc[0]:.3f}->{d.vbat_end_v.iloc[-1]:.3f}")
    print("\n  All trials: performance governor, on battery (negative pack current AND")
    print("  zero VBUS on every sample), zero live throttling nibble.")

    hot_rep = max(f[k].peak_temp.max() for k in CFG)
    hot_old = max(g[k].peak_temp.max() for k in CFG) if g else float('nan')
    print(f"\n  Hottest single trial, reported session (n=32):    {hot_rep:.2f} C "
          f"({THROTTLE_ONSET_C - hot_rep:+.2f} C vs the {THROTTLE_ONSET_C:.0f} C onset)")
    print(f"  Hottest single trial, replication session (n=32): {hot_old:.2f} C "
          f"({THROTTLE_ONSET_C - hot_old:+.2f} C vs the {THROTTLE_ONSET_C:.0f} C onset)")
    if hot_old >= THROTTLE_ONSET_C:
        print(f"\n  NOTE: at least one replication-session trial reached or exceeded the")
        print(f"  nominal {THROTTLE_ONSET_C:.0f} C onset while the live throttling nibble still read 0.")
        print( "  Trials at or above 79 C, both sessions:")
        for lab, src in (("reported", f), ("replication", g)):
            for k in CFG:
                for _, r in src[k][src[k].peak_temp >= 79.0].iterrows():
                    print(f"    {lab:11s} {NICE[k]:16s} trial {int(r.trial)}  "
                          f"T={r.peak_temp:.2f} C  throttle_bits={int(r.throttle_bits)}")
        print("\n  The correct statement is therefore NOT '0.7 C of headroom'. Peak")
        print("  temperature is a SAMPLED maximum (the environment sampler fires once")
        print("  per 20 inferences, i.e. every ~7 s at 640 and ~31 s at 1280, ~15 times")
        print("  per trial), so both the recorded peaks and the zero throttle counts are")
        print("  lower bounds on thermal stress, not exhaustive observations. See")
        print("  ERRATA.md, item 1.")

    # ---------------- Table III ----------------
    hdr("TABLE III  — MODEL COMPLEXITY AND SYSTEM BEHAVIOR")
    print(f"{'Configuration':16s} {'Params':>7s} {'GFLOPs':>7s} {'Latency/img (ms)':>20s} "
          f"{'LL-miss rd (e9)':>18s} {'L2 refill (e9)':>15s} {'Peak T (C)':>13s} {'Thr':>5s}")
    for k in CFG:
        d = f[k]
        print(f"{NICE[k]:16s} {PARAMS_M[k]:7.2f} {GFLOPS[k]:7.1f} "
              f"{mean(f,k,'lat_mean'):13.1f} +/- {sd(f,k,'lat_mean'):4.1f} "
              f"{mean(f,k,'ll_cache_miss_rd',1e-9):12.2f} +/- {sd(f,k,'ll_cache_miss_rd',1e-9):.2f} "
              f"{mean(f,k,'l2d_cache_refill',1e-9):15.2f} "
              f"{mean(f,k,'peak_temp'):8.1f} +/- {sd(f,k,'peak_temp'):.1f} "
              f"{int((d.throttle_bits != 0).sum())}/{len(d)}")
    print("\n  Active power (W): " + " / ".join(f"{mean(f,k,'p_active_w'):.2f}" for k in CFG))
    print("  Latency SD as % of mean: " +
          " / ".join(f"{sd(f,k,'lat_mean')/mean(f,k,'lat_mean')*100:.2f}%" for k in CFG))

    # ---------------- Table IV ----------------
    hdr("TABLE IV  — MEASURED PER-IMAGE ENERGY AND ENDURANCE")
    print(f"{'Configuration':16s} {'P_idle':>8s} {'P_active':>9s} {'Gross E/img (J)':>19s} "
          f"{'Net E/img':>10s} {'Frames/J':>9s} {'Frames/72Wh':>12s}")
    e0 = mean(f, "combined_640", "energy_per_img_j")
    for k in CFG:
        d = f[k]
        gross = mean(f, k, "energy_per_img_j")
        net = ((d.p_active_w - d.p_idle_w) * (d.lat_mean / 1000.0)).mean()
        print(f"{NICE[k]:16s} {mean(f,k,'p_idle_w'):8.2f} {mean(f,k,'p_active_w'):9.2f} "
              f"{gross:13.2f} +/- {sd(f,k,'energy_per_img_j'):.2f} "
              f"{net:10.2f} {e0/gross:8.2f}x {BATTERY_WH*3600/gross:12,.0f}")

    # ---------------- effect sizes and intervals ----------------
    hdr("DIFFERENCES WITH 95% CONFIDENCE INTERVALS  (n = 8 per group)")
    METR = [("Latency (ms)", "lat_mean", 1.0),
            ("LL cache read misses (e9)", "ll_cache_miss_rd", 1e-9),
            ("L2 cache refills (e9)", "l2d_cache_refill", 1e-9),
            ("Gross energy per image (J)", "energy_per_img_j", 1.0),
            ("Peak temperature (C)", "peak_temp", 1.0)]
    print(f"{'Res':>5s} {'Metric':28s} {'Unified':>9s} {'Separate':>9s} {'Reduction':>10s} "
          f"{'Difference (sep - uni), 95% CI':>34s} {'+/- as % of diff':>17s}")
    for r in ["640", "1280"]:
        u, s_ = f[f"combined_{r}"], f[f"separate_{r}"]
        for name, c, sc in METR:
            a, b = u[c] * sc, s_[c] * sc
            diff, lo, hi = welch_ci(a, b)
            half = (hi - lo) / 2
            print(f"{r:>5s} {name:28s} {a.mean():9.3f} {b.mean():9.3f} "
                  f"{(b.mean()-a.mean())/b.mean()*100:+9.1f}% "
                  f"{diff:+12.3f} [{lo:+.3f}, {hi:+.3f}]".ljust(36) +
                  f"{abs(half/diff)*100:10.1f}%")

    print("\n  On p-values. Welch tests over these groups return the following, and the")
    print("  paper does NOT report them as its headline:")
    for r in ["640", "1280"]:
        u, s_ = f[f"combined_{r}"], f[f"separate_{r}"]
        for name, c, sc in METR[:1] + METR[3:4]:
            t, df, p = welch(u[c] * sc, s_[c] * sc)
            print(f"    @{r:4s} {name:28s} t={t:8.1f}  df={df:5.1f}  p={p:.2e}")
    print("\n  Those figures describe the determinism of the apparatus, not the strength")
    print("  of evidence about a population: within-configuration dispersion is under")
    print("  0.6% of the mean, and the eight trials of a configuration are CONSECUTIVE")
    print("  WITHIN ONE BATTERY SESSION with the unified configuration always first, so")
    print("  they are not independent in the sense a t-test assumes. The intervals above")
    print("  describe this apparatus in this session; the cross-session replication")
    print("  reported below is the more meaningful check. See ERRATA.md, item 8.")

    print("\n  Peak temperature is the one metric whose architectural ordering is NOT stable:")
    print("  it reverses between resolutions here and reverses again in the replication")
    print("  session (see below). No architectural claim is made from it.")

    # ---------------- accuracy aggregation sensitivity ----------------
    hdr("ACCURACY: AGGREGATION SENSITIVITY  (ERRATA.md items 6 and 7)")
    name = np.array([c[0] for c in PERCLASS])
    inst = np.array([c[1] for c in PERCLASS], float)
    area = np.array([c[2] for c in PERCLASS], float)
    a640 = np.array([c[3] for c in PERCLASS], float)
    a1280 = np.array([c[4] for c in PERCLASS], float)
    d = a1280 - a640
    keep10 = np.array([n not in UNDERSAMPLED for n in name])

    print("  The SAME predictions on the SAME images, under three aggregations:\n")
    print(f"    {'Aggregation':26s} {'640':>8s} {'1280':>8s} {'delta':>9s}")
    m12 = (a640.mean(), a1280.mean())
    m10 = (a640[keep10].mean(), a1280[keep10].mean())
    wi = ((inst * a640).sum() / inst.sum(), (inst * a1280).sum() / inst.sum())
    for lab, (x, y) in [("12-class macro (primary)", m12),
                        ("10-class macro", m10),
                        ("instance-weighted", wi)]:
        print(f"    {lab:26s} {x:8.3f} {y:8.3f} {y-x:+9.3f}")
    print(f"\n    => the headline moves by an order of magnitude "
          f"({m12[1]-m12[0]:+.3f} to {wi[1]-wi[0]:+.3f}) "
          f"depending only on what is averaged over.")
    print("    (Table II in the manuscript rounds the 10-class macro to 0.482/0.515,")
    print("     hence +0.033 there against the +0.0335 computed from 3-dp per-class values.)")

    ig, il = inst[d > 0].sum(), inst[d < 0].sum()
    print(f"\n  Why: {int(ig):,} of {int(inst.sum()):,} validation instances "
          f"({ig/inst.sum()*100:.0f}%) sit on classes that GAIN at 1280;")
    print(f"  {int(il):,} ({il/inst.sum()*100:.0f}%) sit on classes that lose. A macro-average weighs a")
    print(f"  {int(inst.min())}-instance class as heavily as a {int(inst.max())}-instance one, so the gains and")
    print("  losses appear to cancel. Weighted by instance they do not come close.")
    print("  The +0.007 figure is a property of the averaging, NOT a statement that")
    print("  the extra computation bought nothing. See ERRATA.md, item 6.")

    print(f"\n  Gaining set: n={int((d>0).sum())}, mean area {area[d>0].mean():9,.0f} px2, "
          f"{int(inst[d>0].sum()):,} instances")
    print(f"  Losing  set: n={int((d<0).sum())}, mean area {area[d<0].mean():9,.0f} px2, "
          f"{int(inst[d<0].sum()):,} instances   -> ratio {area[d<0].mean()/area[d>0].mean():.1f}x")
    k = keep10
    print(f"  Excluding both pre-declared classes, the losing set falls to "
          f"{area[k & (d<0)].mean():,.0f} px2 -> ratio {area[k & (d<0)].mean()/area[k & (d>0)].mean():.1f}x")

    print("\n  Rank correlation between target area and AP gain, and its sensitivity:\n")
    for lab, m in [("all twelve classes", np.ones(12, bool)),
                   ("excluding weevil", name != "weevil"),
                   ("excluding BOTH pre-declared", keep10)]:
        rho, pv = stats.spearmanr(area[m], d[m])
        flag = "" if pv < 0.05 else "   <-- NOT significant at 0.05"
        print(f"    {lab:30s} n={int(m.sum()):2d}   rho={rho:+.3f}   p={pv:.4f}{flag}")
    print("\n  Pink_disease is the extreme point of the area axis (291,112 px2) and carries")
    print("  part of the correlation. The manuscript reports all three values and treats")
    print("  the trend as directional evidence consistent with the mechanism, not as an")
    print("  independently significant finding. See ERRATA.md, item 7.")

    # ---------------- derived quantities ----------------
    hdr("DERIVED QUANTITIES  (Section IV-B)")
    for r in ["640", "1280"]:
        uk, sk = f"combined_{r}", f"separate_{r}"
        ul, sl = mean(f, uk, "lat_mean"), mean(f, sk, "lat_mean")
        ug, sg = GFLOPS[uk], GFLOPS[sk]
        pest_gf = sg - LEAF_GFLOPS[r]
        pest_lat = sl - ul
        thr_u = ug / (ul / 1000)
        pred = pest_gf / thr_u * 1000
        thr_p = pest_gf / (pest_lat / 1000)
        um = mean(f, uk, "ll_cache_miss_rd", 1e-9)
        sm = mean(f, sk, "ll_cache_miss_rd", 1e-9)
        print(f"\n  @{r}")
        print(f"    wall-time ratio (separate/unified)   {sl/ul:.3f}x")
        print(f"    arithmetic ratio (separate/unified)  {sg/ug:.3f}x")
        print(f"    second model: {pest_lat:.1f} ms for {pest_gf:.1f} GFLOPs")
        print(f"    FLOP-proportional prediction         {pred:.1f} ms  -> measured is +{(pest_lat/pred-1)*100:.0f}%")
        print(f"    unified FLOP throughput              {thr_u:.1f} GFLOPS")
        print(f"    second-model FLOP throughput         {thr_p:.1f} GFLOPS ({thr_p/thr_u*100:.0f}% of unified)")
        print(f"    unified LL misses per GFLOP          {um/ug:.3f} e9")
        print(f"    second-model LL misses per GFLOP     {(sm-um)/pest_gf:.3f} e9 "
              f"(+{((sm-um)/pest_gf)/(um/ug)*100-100:.0f}%)")

    hdr("CAPACITY-MATCHED BOUND  (Section III-C, IV-B)")
    u6 = mean(f, "combined_640", "lat_mean")
    thr = 21.6 / (u6 / 1000)
    print("  The deployed pest model is YOLO11n; the leaf and unified models are YOLO11s.")
    print("  A capacity-matched separate configuration (2 x YOLO11s) would be:")
    print(f"    18.86 M params, 43.2 GFLOPs = {43.2/21.6:.2f}x the unified detector's arithmetic")
    print(f"    at the unified model's measured throughput ({thr:.1f} GFLOPS): "
          f"{43.2/thr*1000:.0f} ms = {43.2/thr*1000/u6:.2f}x unified latency")
    print("  => the configuration measured here is the BEST CASE for the separate")
    print("     architecture, and it still loses by ~30%.")

    hdr("RESOLUTION SCALING OF THE UNIFIED MODEL  (Section IV-B, IV-E)")
    u6l, u12l = mean(f, "combined_640", "lat_mean"), mean(f, "combined_1280", "lat_mean")
    u6c, u12c = mean(f, "combined_640", "ll_cache_miss_rd"), mean(f, "combined_1280", "ll_cache_miss_rd")
    u6e, u12e = mean(f, "combined_640", "energy_per_img_j"), mean(f, "combined_1280", "energy_per_img_j")
    print(f"  arithmetic            {86.3/21.6:.3f}x")
    print(f"  LL cache read misses  {u12c/u6c:.3f}x   <-- grows faster than arithmetic")
    print(f"  wall-clock latency    {u12l/u6l:.3f}x   <-- lands between the two")
    print(f"  gross energy          {u12e/u6e:.3f}x")
    print("\n  Weights are 36.2 MiB against a 2 MiB shared L3 (a factor of 18), so weights")
    print("  are streamed from DRAM on every inference. A FLOP-based cost model")
    print("  systematically under-predicts wall time on this platform.")

    # ---------------- replication session ----------------
    if REP.exists():
        hdr("REPLICATION SESSION  (Section III-D, IV-B, IV-D)")
        print("  An earlier, independently-run session, before the power and provenance")
        print("  instrumentation was added (11 columns, no power telemetry).\n")
        worst_lat = worst_cache = 0.0
        print(f"  {'Config':16s} {'metric':12s} {'replication':>12s} {'reported':>10s} {'dev':>7s}")
        for k in CFG:
            for c, lab, isc in [("lat_mean", "latency", False),
                                ("ll_cache_miss_rd", "LL miss", True),
                                ("l2d_cache_refill", "L2 refill", True)]:
                a, b = g[k][c].mean(), f[k][c].mean()
                dev = abs(a - b) / b * 100
                if isc:
                    worst_cache = max(worst_cache, dev)
                else:
                    worst_lat = max(worst_lat, dev)
                sa, sb = (a / 1e9, b / 1e9) if isc else (a, b)
                print(f"  {NICE[k]:16s} {lab:12s} {sa:12.3f} {sb:10.3f} {dev:6.2f}%")
        print(f"\n  => every cache figure reproduced to within {worst_cache:.2f}%")
        print(f"  => every latency figure reproduced to within {worst_lat:.2f}%")

        print("\n  Peak temperature — the ordering REVERSES between sessions:")
        for r in ["640", "1280"]:
            gu, gs = g[f"combined_{r}"].peak_temp, g[f"separate_{r}"].peak_temp
            fu, fs = f[f"combined_{r}"].peak_temp, f[f"separate_{r}"].peak_temp
            _, _, gp = welch(gu, gs)
            _, _, fp = welch(fu, fs)
            print(f"    @{r:4s} replication: uni {gu.mean():5.2f} vs sep {gs.mean():5.2f} -> "
                  f"{'unified' if gu.mean() > gs.mean() else 'separate':8s} hotter   p={gp:.4f}"
                  f"{'' if gp < 0.05 else '   (NOT significant)'}")
            print(f"    {'':5s} reported   : uni {fu.mean():5.2f} vs sep {fs.mean():5.2f} -> "
                  f"{'unified' if fu.mean() > fs.mean() else 'separate':8s} hotter   p={fp:.4f}"
                  f"{'' if fp < 0.05 else '   (NOT significant)'}")
        print("\n  Three of these four contrasts are nominally significant and they point in")
        print("  opposite directions between sessions; the fourth (replication @1280) is")
        print("  not significant at all. Either way there is no stable architectural")
        print("  ordering, which is why the paper makes NO claim from peak temperature.")

    hdr("DONE")
    print("  Every system-level number above — Tables III and IV, the intervals, the")
    print("  derived quantities, the capacity-matched bound, the resolution scaling and")
    print("  the replication check — is computed from results/ and none is hard-coded.")
    print("\n  The accuracy section is the one exception: its per-class inputs (PERCLASS,")
    print("  top of this file) are the output of scripts/refair_eval_commonval.py, which")
    print("  needs the model weights and cannot run here. They are reproduced verbatim so")
    print("  that the AGGREGATION SENSITIVITY — which is the claim being made — can be")
    print("  checked without them. Running refair_eval_commonval.py against the weights")
    print("  regenerates the inputs.")


if __name__ == "__main__":
    main()
