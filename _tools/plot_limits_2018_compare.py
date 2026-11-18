#!/usr/bin/env python3
"""
Overlay the 2018 limits digitised from the AN (limits_2018/limits_2018_AN_*.txt) with the published HEPData ones
(limits_2018_HEPData_*.txt): one page per scenario x m_A' (8 pages), limit vs ctau with a ratio panel AN / HEPData
(HEPData interpolated in log-log at the AN lifetimes). Same y range on every page (--ylim).

Usage: plot_limits_2018_compare.py [--dir limits_2018] [--ylim 1e-5,1]
                                   [--out ~/public_html/parking/2024/limits/limits_2018_AN_vs_HEPData.pdf]
"""
import argparse, os, re, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cmsstyle as cms

HEADER = r"41.6 fb$^{-1}$ (13 TeV, 2018)"
MASSES = ("0p33", "0p4", "0p67", "1p33")
COLS = ("obs", "exp", "e68lo", "e68hi", "e95lo", "e95hi")


def load(path):
    d = np.loadtxt(path)
    head = "".join(l for l in open(path) if l.startswith("#"))
    mpi = re.search(r"m_pi3 = ([\d.]+)", head).group(1)
    return {"ct": d[:, 0], **{c: d[:, i + 1] for i, c in enumerate(COLS)}, "mpi": mpi}


def interp(xq, x, y):
    o = np.argsort(x)
    return 10 ** np.interp(np.log10(xq), np.log10(x[o]), np.log10(y[o]))


def titled_legend(ax, title, handles, x):
    """Legend whose title carries the source name (centred), anchored with its top-left corner at axes x."""
    fs = cms.FS_LEGEND - 3
    leg = ax.legend(handles=handles, title=title, loc="upper left", bbox_to_anchor=(x, 0.995), fontsize=fs, labelspacing=0.3,
                    **cms.LEGEND_KW)
    leg.get_title().set_fontsize(fs + 1); leg.get_title().set_fontweight("bold")
    leg._legend_box.align = "center"   # title centred over the entries (old matplotlib: no `alignment` kwarg)
    ax.add_artist(leg)
    return leg


def page(pdf, sc, m, an, hd, ylim):
    fig, (ax, rx) = plt.subplots(2, 1, figsize=(8, 8.5), sharex=True,
                                 gridspec_kw=dict(height_ratios=[3, 1.1], hspace=0.06))
    # HEPData: the published style (filled bands)
    ax.fill_between(hd["ct"], hd["e95lo"], hd["e95hi"], color="#f5bb54", lw=0, zorder=1)
    ax.fill_between(hd["ct"], hd["e68lo"], hd["e68hi"], color="#607641", lw=0, zorder=2)
    ax.plot(hd["ct"], hd["exp"], "k--", lw=1.5, zorder=4)
    ax.plot(hd["ct"], hd["obs"], "k-", marker="o", ms=5, lw=1.5, zorder=5)
    # AN: red, bands as outlines only so both are readable
    ax.fill_between(an["ct"], an["e68lo"], an["e68hi"], facecolor="none", edgecolor="crimson", hatch="///", lw=0, zorder=3)
    ax.plot(an["ct"], an["e95lo"], ":", color="crimson", lw=1.2, zorder=3)
    ax.plot(an["ct"], an["e95hi"], ":", color="crimson", lw=1.2, zorder=3)
    ax.plot(an["ct"], an["exp"], "--", color="crimson", lw=1.8, zorder=6)
    ax.plot(an["ct"], an["obs"], "-", color="crimson", marker="s", mfc="white", ms=6, lw=1.8, zorder=7)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_ylabel(r"95% CL upper limit on $\mathcal{B}(\mathrm{H}\to\psi\psi)$", fontsize=cms.FS_LABEL)
    ax.set_ylim(*ylim)
    cms.cms_axes(ax, header=HEADER, fontsize=cms.FS_AXES, label=cms.CMS_LABEL_DATA)
    titled_legend(ax, "HEPData", [Line2D([], [], color="k", marker="o", ms=5, label="Observed"),
                                  Line2D([], [], color="k", ls="--", label="Median expected"),
                                  Patch(color="#607641", label="68% expected"),
                                  Patch(color="#f5bb54", label="95% expected")], 0.14)
    titled_legend(ax, "AN", [Line2D([], [], color="crimson", marker="s", mfc="white", ms=6, label="Observed"),
                             Line2D([], [], color="crimson", ls="--", label="Median expected"),
                             Patch(facecolor="none", edgecolor="crimson", hatch="///", label="68% expected"),
                             Line2D([], [], color="crimson", ls=":", label="95% expected")], 0.43)
    ax.text(0.03, 0.03, f"Scenario {sc}\n$m_{{\\tilde{{\\pi}}_3}}$ = {hd['mpi']} GeV\n$m_{{A'}}$ = {m.replace('p', '.')} GeV",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=cms.FS_LEGEND)
    # ratio AN / HEPData at the AN lifetimes (HEPData interpolated in log-log)
    for key, style, lab in (("obs", dict(ls="-", marker="s", mfc="white"), "Observed"),
                            ("exp", dict(ls="--", marker="o"), "Median expected")):
        rx.plot(an["ct"], an[key] / interp(an["ct"], hd["ct"], hd[key]), color="crimson", lw=1.5, ms=5, label=lab, **style)
    rx.axhline(1, color="gray", lw=0.8)
    rx.set_yscale("log"); rx.set_ylim(0.05, 3)
    rx.set_yticks([0.1, 0.3, 1, 3]); rx.set_yticklabels(["0.1", "0.3", "1", "3"])
    rx.set_ylabel("AN / HEPData", fontsize=cms.FS_LABEL - 1)
    rx.set_xlabel(r"$c\tau$ [mm]", fontsize=cms.FS_LABEL)
    rx.tick_params(which="both", direction="in", top=True, right=True)
    rx.legend(loc="lower right", fontsize=cms.FS_LEGEND - 3, ncol=2, **cms.LEGEND_KW)
    pdf.savefig(fig); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "limits_2018"))
    ap.add_argument("--out", default=os.path.expanduser("~/public_html/parking/2024/limits/limits_2018_AN_vs_HEPData.pdf"))
    ap.add_argument("--ylim", default="1e-5,1", help="common y range of the limit panel on all pages: lo,hi")
    a = ap.parse_args()
    ylim = tuple(float(v) for v in a.ylim.split(","))
    with PdfPages(a.out) as pdf:
        for sc in ("A", "B1"):
            for m in MASSES:
                page(pdf, sc, m, load(f"{a.dir}/limits_2018_AN_sc{sc}_mA{m}.txt"),
                     load(f"{a.dir}/limits_2018_HEPData_sc{sc}_mA{m}.txt"), ylim)
    print("written", a.out)


if __name__ == "__main__":
    main()
