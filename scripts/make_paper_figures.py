#!/usr/bin/env python3
"""Figures 1-4 for Paper 6 (unified vs separate detection architectures)."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np
from scipy import stats
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.labelsize": 8.5,
    "axes.titlesize": 9,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
})

UNI = "#1f5c8b"      # unified
SEP = "#c1553b"      # separate
GAIN = "#2a7f62"
LOSS = "#b03a2e"
GREY = "#5a5a5a"
LGREY = "#d9d9d9"


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf")
    fig.savefig(f"{OUT}/{name}.png")
    plt.close(fig)
    print("wrote", name)


# ----------------------------------------------------------------------
# FIG 1 - measurement chain
# ----------------------------------------------------------------------
def fig1():
    fig, ax = plt.subplots(figsize=(7.1, 2.75))
    ax.set_xlim(0, 100); ax.set_ylim(-5, 45); ax.axis("off")

    def box(x, y, w, h, title, sub, fc="white", ec=GREY, lw=0.9):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                    boxstyle="round,pad=0.6,rounding_size=1.2",
                    fc=fc, ec=ec, lw=lw, zorder=2))
        ax.text(x + w/2, y + h*0.63, title, ha="center", va="center",
                fontsize=8.2, fontweight="bold", zorder=3)
        ax.text(x + w/2, y + h*0.26, sub, ha="center", va="center",
                fontsize=6.8, color=GREY, zorder=3, linespacing=1.35)

    def arrow(x1, x2, y):
        ax.add_patch(FancyArrowPatch((x1, y), (x2, y),
                    arrowstyle="-|>", mutation_scale=9,
                    lw=1.0, color=GREY, zorder=1))

    y, h = 15, 12
    box(2,  y, 20, h, "Battery pack", "4 cells in series\n13.6 – 16.7 V")
    box(29, y, 21, h, "UPS HAT", "coulomb-counting gauge\n$P=V\\cdot I$ @ 2 Hz")
    box(57, y, 17, h, "5 V buck", "conversion loss\nincluded")
    box(81, y, 17, h, "Raspberry Pi 5", "+ Active Cooler\n4 ORT threads")

    for a, b in ((22.9, 28.1), (50.9, 56.1), (74.9, 80.1)):
        arrow(a, b, y + h/2)

    # this work's measurement node
    ax.plot([39.5], [y], marker="o", ms=6, mfc=UNI, mec="white", mew=1.1, zorder=5)
    ax.annotate("measurement node (this work)\nSoC + cooler + HAT quiescent + buck loss",
                xy=(39.5, y), xytext=(39.5, 4.2),
                ha="center", va="center", fontsize=7.2, color=UNI,
                fontweight="bold", linespacing=1.4,
                arrowprops=dict(arrowstyle="-", lw=0.9, color=UNI))

    # vendor node
    ax.plot([89.5], [y + h], marker="o", ms=5.2, mfc="white",
            mec=SEP, mew=1.3, zorder=5)
    ax.annotate("published bare-board node\nSoC only",
                xy=(89.5, y + h), xytext=(86, 33.2),
                ha="center", va="center", fontsize=7.2, color=SEP,
                linespacing=1.4,
                arrowprops=dict(arrowstyle="-", lw=0.9, color=SEP))

    ax.text(2, 41, "Battery-rail measurement is 1.3–1.8$\\times$ the published board-level envelope",
            fontsize=8.2, fontweight="bold", va="center")
    ax.text(2, -3.0,
            "Discharge control: active power varies 0.35% between a full pack (16.57 V) and a 25% pack (13.57 V).  "
            "Battery operation verified per sample by two witnesses.",
            fontsize=6.5, color=GREY, va="center")
    save(fig, "Fig1_measurement_chain")


# ----------------------------------------------------------------------
# FIG 2 - AP gain vs target area
# ----------------------------------------------------------------------
def fig2():
    cls = ["Stem_borer","Psyllid_damage","Psyllid","Algal","weevil_damage",
           "Scale_insect","Phomopsis","weevil","Leaf_rot","leafhopper_damage",
           "Root_disease","Pink_disease"]
    area = np.array([336,494,1140,1529,2190,6538,12203,13209,36885,48864,70358,291112], float)
    ap640  = np.array([.151,.366,.317,.416,.823,.242,.810,.578,.784,.513,.393,.407])
    ap1280 = np.array([.132,.479,.476,.464,.929,.296,.818,.495,.776,.435,.346,.235])
    gain = ap1280 - ap640
    under = np.array([c in ("weevil","Pink_disease") for c in cls])

    inst = np.array([33,418,539,275,78,57,160,4,83,39,59,20], float)

    rho, p = stats.spearmanr(area, gain)
    print(f"  Spearman all 12   : rho={rho:.3f} p={p:.4f}")
    m = ~np.isin(cls, ["weevil"])
    rho2, p2 = stats.spearmanr(area[m], gain[m])
    print(f"  excl. weevil      : rho={rho2:.3f} p={p2:.4f}")
    m3 = ~np.isin(cls, ["weevil", "Pink_disease"])
    rho3, p3 = stats.spearmanr(area[m3], gain[m3])
    print(f"  excl. both (n=10) : rho={rho3:.3f} p={p3:.4f}   <- not significant")
    ig, il = inst[gain > 0].sum(), inst[gain < 0].sum()
    print(f"  instances on gaining classes: {ig:.0f} / {inst.sum():.0f}"
          f"  ({ig/inst.sum()*100:.0f}%)")

    fig, ax = plt.subplots(figsize=(7.1, 3.95))
    ax.axhline(0, color="black", lw=0.8, zorder=1)

    for i, c in enumerate(cls):
        col = GAIN if gain[i] > 0 else LOSS
        ax.scatter(area[i], gain[i], s=68, c="white", edgecolors=col,
                   linewidths=1.5, zorder=3,
                   marker="o" if not under[i] else "s")
        ax.scatter(area[i], gain[i], s=68, c=col, alpha=.22,
                   edgecolors="none", zorder=2,
                   marker="o" if not under[i] else "s")

    off = {"Stem_borer":(-.28,.019),"Psyllid_damage":(0,.020),"Psyllid":(0,.020),
           "Algal":(0,.019),"weevil_damage":(0,.019),"Scale_insect":(0,.019),
           "Phomopsis":(0,.019),"weevil":(0,-.028),"Leaf_rot":(0,.019),
           "leafhopper_damage":(0,-.030),"Root_disease":(0,.019),
           "Pink_disease":(0,.020)}
    for i, c in enumerate(cls):
        if c == "Stem_borer":
            continue          # named inside its callout instead
        dx, dy = off[c]
        lab = c + (" †" if under[i] else "")
        ax.annotate(lab, (area[i], gain[i]), xytext=(area[i]*(1+dx), gain[i]+dy),
                    ha="center", fontsize=6.6,
                    color=GREY if not under[i] else "#999999")

    ax.set_xscale("log")
    ax.set_xlabel("Mean bounding-box area (px$^2$, log scale)")
    ax.set_ylabel("$\\Delta$AP@0.5   (1280 $-$ 640)")
    ax.set_xlim(200, 6.5e5)
    ax.set_ylim(-.215, .255)

    ax.text(.985, .97, f"Spearman $\\rho$ = {rho:.2f}  ($p$ = {p:.3f})   all 12\n"
                       f"$\\rho$ = {rho2:.2f}  ($p$ = {p2:.3f})   excl. weevil\n"
                       f"$\\rho$ = {rho3:.2f}  ($p$ = {p3:.3f})   excl. both $\\dagger$  (n.s.)",
            transform=ax.transAxes, va="top", ha="right", fontsize=7.2,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=LGREY, lw=.7))

    ax.text(.985, .715, "6 gain   mean area 4,016 px$^2$   1,527 instances\n"
                       "6 lose   mean area 76,794 px$^2$      238 instances\n"
                       "excl. $\\dagger$: area ratio 19$\\times$ $\\rightarrow$ 9.7$\\times$",
            transform=ax.transAxes, va="top", ha="right", fontsize=7.2,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=LGREY, lw=.7))

    ax.annotate("Stem_borer — departs from trend:\nrecall-limited,\nnot resolution-limited",
                xy=(336, -.019), xytext=(430, -.135),
                fontsize=6.8, color=GREY, ha="center", linespacing=1.4,
                arrowprops=dict(arrowstyle="->", lw=.8, color=GREY,
                                connectionstyle="arc3,rad=-0.3"))

    ax.set_title("The classes that gain from higher resolution are the smaller ones \u2014 "
                 "and carry 87% of the instances",
                 loc="left", fontweight="bold", pad=8)
    fig.text(.125, -.02, "† Under-sampled in validation (weevil, 4 instances; Pink_disease, 20); "
             "not interpreted individually.", fontsize=6.5, color=GREY)
    save(fig, "Fig2_ap_gain_vs_area")


# ----------------------------------------------------------------------
# FIG 3 - scaling: FLOPs vs cache vs wall time
# ----------------------------------------------------------------------
def fig3():
    fig, ax = plt.subplots(figsize=(4.6, 3.3))
    labels = ["GFLOPs", "LLC read\nmisses", "Wall-clock\nlatency"]
    vals = [86.3/21.6, 22.39/4.54, 1561.5/357.7]
    print(f"  scaling ratios: {[round(v,3) for v in vals]}")
    cols = [GREY, "#8c6bb1", UNI]

    bars = ax.bar(labels, vals, width=.55, color=cols, edgecolor="none", zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+.09, f"{v:.2f}$\\times$",
                ha="center", fontsize=9, fontweight="bold",
                color=b.get_facecolor())

    ax.axhline(4.0, color="black", lw=.9, ls=(0,(4,2.5)), zorder=2)
    ax.text(2.52, 4.0, "exact arithmetic\nscaling (4.00$\\times$)",
            va="center", ha="left", fontsize=6.8, color="black", linespacing=1.35)

    ax.set_ylim(0, 5.55)
    ax.set_ylabel("Ratio, 1280 / 640  (unified detector)")
    ax.set_yticks([0,1,2,3,4,5])
    ax.grid(axis="y", lw=.5, color=LGREY, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title("Memory traffic, not arithmetic,\nsets the latency", loc="left",
                 fontweight="bold", pad=8)
    fig.text(.02, -.05,
             "Single model, single backbone, single thread count — no capacity confound.\n"
             "Weights 36.2 MiB against a 2 MiB shared L3: never resident, streamed from DRAM every inference.",
             fontsize=6.5, color=GREY, linespacing=1.5)
    save(fig, "Fig3_scaling_decomposition")


# ----------------------------------------------------------------------
# FIG 4 - latency and energy
# ----------------------------------------------------------------------
def fig4():
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.0))
    groups = ["640", "1280"]
    x = np.arange(2); w = .34

    lat_u, lat_u_sd = [357.7, 1561.5], [1.9, 8.2]
    lat_s, lat_s_sd = [510.8, 2213.9], [1.3, 4.7]
    en_u,  en_u_sd  = [4.37, 18.61], [.05, .20]
    en_s,  en_s_sd  = [6.14, 26.20], [.03, .06]

    ek = dict(elinewidth=.9, capsize=2.5, capthick=.9, ecolor="#333333")

    for ax, (u, usd, s, ssd, ylab, unit, title) in zip(axes, [
        (lat_u, lat_u_sd, lat_s, lat_s_sd, "Latency per image (ms)", "ms", "Latency"),
        (en_u,  en_u_sd,  en_s,  en_s_sd,  "Gross energy per image (J)", "J", "Energy"),
    ]):
        ax.bar(x-w/2, u, w, yerr=usd, color=UNI, label="Unified (1 model)",
               error_kw=ek, zorder=3)
        ax.bar(x+w/2, s, w, yerr=ssd, color=SEP, label="Separate (2 models)",
               error_kw=ek, zorder=3)

        for xi, (a, b) in enumerate(zip(u, s)):
            top = max(a, b)
            ax.text(xi, top*1.115, f"$-${(1-a/b)*100:.1f}%", ha="center",
                    fontsize=8.2, fontweight="bold", color=UNI)
            ax.plot([xi-w/2, xi-w/2, xi+w/2, xi+w/2],
                    [a*1.03, top*1.085, top*1.085, b*1.03],
                    lw=.8, color=GREY, zorder=2)

        ax.set_xticks(x); ax.set_xticklabels([f"{g}$\\times${g}" for g in groups])
        ax.set_ylabel(ylab)
        ax.set_ylim(0, max(s)*1.30)
        ax.grid(axis="y", lw=.5, color=LGREY, zorder=0)
        ax.set_axisbelow(True)
        ax.set_title(title, loc="left", fontweight="bold", pad=6)

    axes[0].legend(frameon=False, loc="upper left", bbox_to_anchor=(0, .93))
    axes[1].text(.03, .95, "Endurance @640:\n≈59,300 frames / 72 Wh\nvs ≈42,200  (+40%)",
                 transform=axes[1].transAxes, ha="left", va="top", fontsize=7,
                 color=GREY, linespacing=1.45)

    fig.text(.02, -.045,
             "Mean $\\pm$ SD over eight trials per configuration, consecutive within one battery session, "
             "on battery, performance governor. Latency SD $<$ 0.6% of mean throughout.\n"
             "Mean latency difference 153.1 ms (95% CI 151.3$-$154.9) at 640 and 652.4 ms (645.0$-$659.7) at 1280; "
             "energy 1.77 J (1.72$-$1.81) and 7.59 J (7.42$-$7.75). Zero throttling events in 32 trials.",
             fontsize=6.5, color=GREY, linespacing=1.5)
    fig.tight_layout()
    save(fig, "Fig4_latency_energy")


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4()
