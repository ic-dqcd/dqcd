#!/usr/bin/env python3
"""Visualise the content of a CMS golden certification JSON.

The JSON is a bare {run: [[lsA, lsB], ...]} mapping, which is impossible to read by eye:
475 runs and 287,603 certified lumisections for 2024. These four pages answer the
questions that actually come up when using it as an analysis lumi mask:

  1  How much of the year is certified, and where -- certified lumisections per run
     across the whole run range, coloured by era.
  2  How the certified total accumulates, so the relative weight of each era is visible
     rather than inferred from run counts.
  3  Per-era totals side by side, with the run count annotated.
  4  How FRAGMENTED the certification is -- how many disjoint lumisection intervals each
     run is chopped into, plus the worst offenders drawn interval by interval. This is
     the page that says whether a run-level mask could ever be a decent approximation:
     if runs were certified whole, one interval each, run-level filtering would be fine.

IMPORTANT: a lumisection count is a proxy for TIME (~23.3 s each), NOT for integrated
luminosity -- the instantaneous luminosity varies by more than a factor of two across a
fill. For real luminosity use brilcalc with a normtag. Nothing here should be quoted as
a luminosity.

Run after sourcing setup.sh:
    python3 _tools/plotGoldenJSON.py [--json PATH] [--output path.pdf] [--no-publish]
"""

import argparse
import json
import math
import os
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import cmsstyle as cms

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.join(HERE, "data", "Cert_Collisions2024_378981_386951_Golden.json")
# "Recorded with the detector on" -- the denominator for a certified FRACTION. The golden
# JSON alone only says what IS certified; it carries no notion of what was thrown away.
DCS = os.path.join(HERE, "data", "Collisions24_DCSOnly.json")
ERA_JSON = os.path.join(HERE, "data", "2024%s_Golden.json")
# Era I was taken in two campaigns that the sample area keeps apart as Run2024I and
# Run2024I_v2, and they cover DISJOINT run ranges (measured from the nanoAOD: I reaches
# 386642, I_v2 starts at 386704). The certification JSON knows only "2024I", so the split
# is applied here. The exact boundary is not pinned down: 9 certified runs (386661-386703)
# were not seen in either campaign in the sampled files, and this rule assigns them to I.
I_V2_FIRST_RUN = 386704

ERAS = ["B", "C", "D", "E", "F", "G", "H", "I", "I_v2"]
ERA_COLORS = ["#7f7f7f", "#1f77b4", "#ff7f0e", "#2ca02c",
              "#d62728", "#9467bd", "#8c564b", "#17becf", "#e377c2"]
WEBDIR = "/home/hep/jtafoyav/public_html/parking/2024/kinematic_checks"


def _era_label(e):
    return f"Run2024{e}"


def log(msg, **kw):
    print(msg, flush=True, **kw)


def load(path):
    """{run: [(lo, hi), ...]} with integer keys."""
    with open(path) as fh:
        d = json.load(fh)
    return {int(r): [(int(a), int(b)) for a, b in v] for r, v in d.items()}


def era_of_run(run, era_runs):
    for e, runs in era_runs.items():
        if run in runs:
            return e
    return None


def n_ls(ranges):
    return sum(b - a + 1 for a, b in ranges)


# ----------------------------------------------------------------------------
def page_per_run(cert, era_runs):
    fig, ax = plt.subplots(figsize=(11, 7))
    for i, e in enumerate(ERAS):
        runs = sorted(r for r in cert if r in era_runs.get(e, set()))
        if not runs:
            continue
        ax.bar(runs, [n_ls(cert[r]) for r in runs], width=6,
               color=ERA_COLORS[i], label=f"{_era_label(e)} ({len(runs)} runs)")
    unknown = sorted(r for r in cert if era_of_run(r, era_runs) is None)
    if unknown:
        ax.bar(unknown, [n_ls(cert[r]) for r in unknown], width=6,
               color="black", label=f"no era file ({len(unknown)})")
    ax.set_xlabel("Run number", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Certified lumisections", fontsize=cms.FS_LABEL)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, label=cms.CMS_LABEL_DATA)
    ax.legend(fontsize=cms.FS_LEGEND - 2, loc="upper left", ncol=2,
              title="Golden certification, per run", title_fontsize=cms.FS_LEGEND - 1,
              **cms.LEGEND_KW)
    fig.suptitle("Where the certified data is -- lumisections per run", fontsize=cms.FS_TITLE)
    fig.tight_layout()
    return fig


def page_cumulative(cert, era_runs):
    fig, ax = plt.subplots(figsize=(11, 7))
    runs = sorted(cert)
    cum = np.cumsum([n_ls(cert[r]) for r in runs])
    ax.step(runs, cum, where="post", color="black", lw=2, label="all certified")
    for i, e in enumerate(ERAS):
        er = sorted(r for r in runs if r in era_runs.get(e, set()))
        if not er:
            continue
        ax.axvspan(er[0], er[-1], color=ERA_COLORS[i], alpha=0.18, lw=0)
        # Rotated: the late eras (H, I, I_v2) are narrow in run number, so horizontal
        # labels ran into each other.
        ax.text(0.5 * (er[0] + er[-1]), cum[-1] * 0.02, _era_label(e), ha="center",
                va="bottom", rotation=90, fontsize=cms.FS_LEGEND - 2,
                color=ERA_COLORS[i], fontweight="bold")
    ax.set_xlabel("Run number", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Cumulative certified lumisections", fontsize=cms.FS_LABEL)
    ax.set_ylim(0, cum[-1] * 1.12)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, label=cms.CMS_LABEL_DATA)
    ax.legend(fontsize=cms.FS_LEGEND, loc="upper left",
              title=f"{len(runs)} runs, {cum[-1]:,} lumisections total",
              title_fontsize=cms.FS_LEGEND - 1, **cms.LEGEND_KW)
    fig.suptitle("How the certified total accumulates through the year",
                 fontsize=cms.FS_TITLE)
    fig.tight_layout()
    return fig


def page_era_totals(cert, era_runs, era_cert):
    fig, ax = plt.subplots(figsize=(11, 7))
    tot = [n_ls(sum((cert[r] for r in sorted(cert) if r in era_runs.get(e, set())), []))
           for e in ERAS]
    bars = ax.bar(range(len(ERAS)), tot, color=ERA_COLORS, width=0.65)
    for i, (b, e) in enumerate(zip(bars, ERAS)):
        n = len([r for r in cert if r in era_runs.get(e, set())])
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                f"{tot[i]:,}\n{n} runs", ha="center", va="bottom",
                fontsize=cms.FS_LEGEND - 2)
    ax.set_xticks(range(len(ERAS)))
    ax.set_xticklabels([_era_label(e) for e in ERAS], rotation=90,
                       fontsize=cms.FS_LEGEND - 2)
    ax.set_ylabel("Certified lumisections", fontsize=cms.FS_LABEL)
    ax.set_ylim(0, max(tot) * 1.25)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, label=cms.CMS_LABEL_DATA)
    # the per-era files and the full-year file need not agree exactly
    total_era = sum(n_ls(v) for d in era_cert.values() for v in [sum(d.values(), [])])
    total_full = n_ls(sum(cert.values(), []))
    cms.info_legend(ax, [
        f"full-year JSON: {total_full:,} LS",
        f"sum of per-era JSONs: {total_era:,} LS",
        f"difference: {total_era - total_full:+,} LS "
        f"({100.0 * (total_era - total_full) / total_full:+.2f}%)",
    ], loc="upper right", fontsize=cms.FS_LEGEND - 2)
    fig.suptitle("Certified lumisections per era", fontsize=cms.FS_TITLE)
    fig.tight_layout()
    return fig


def _ls_set(ranges):
    """The lumisections of one run as a set, so golden and DCS can be intersected
    honestly -- the two files do not use the same interval boundaries."""
    out = set()
    for a, b in ranges:
        out.update(range(a, b + 1))
    return out


def page_certified_fraction(cert, dcs, era_runs):
    """Certified fraction per era: |golden AND DCS| / |DCS|.

    DCS-only is what was recorded with the detector in a usable state, so this is the
    fraction of RECORDED data that survives the golden mask.

    Two things this has to get right, and a naive golden/DCS ratio gets both wrong:

      * the numerator must be the INTERSECTION. Three golden runs (386615-386617) are
        absent from the DCS file altogether, so counting all golden lumisections against a
        denominator that lacks them pushed Run2024I above 100%. 235 golden lumisections
        (0.08% of the year) sit outside DCS this way -- a real inconsistency between two
        files of different vintage, reported below rather than hidden.
      * the denominator must include runs that were recorded and certified NOWHERE, or the
        fraction only measures certified runs against themselves. Eras are therefore taken
        as run RANGES, and every DCS run in the range counts.
    """
    fig, ax = plt.subplots(figsize=(11, 7))
    spans = {e: (min(r), max(r)) for e, r in era_runs.items() if r}

    labels, frac, gtot, dtot, outside = [], [], [], [], []
    for e in ERAS:
        if e not in spans:
            continue
        lo, hi = spans[e]
        g_in = d_tot = g_out = 0
        for r, v in dcs.items():
            if lo <= r <= hi:
                D = _ls_set(v)
                d_tot += len(D)
                if r in cert:
                    g_in += len(_ls_set(cert[r]) & D)
        for r, v in cert.items():
            if lo <= r <= hi and r not in dcs:
                g_out += len(_ls_set(v))
        if d_tot == 0:
            continue
        labels.append(_era_label(e))
        frac.append(100.0 * g_in / d_tot)
        gtot.append(g_in)
        dtot.append(d_tot)
        outside.append(g_out)

    bars = ax.bar(range(len(labels)), frac, color=ERA_COLORS[:len(labels)], width=0.65)
    for b, f, g, d in zip(bars, frac, gtot, dtot):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.2,
                f"{f:.1f}%\n{g:,}/{d:,}", ha="center", va="bottom",
                fontsize=cms.FS_LEGEND - 3)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=cms.FS_LEGEND - 2)
    ax.set_ylabel("Certified fraction of recorded lumisections [%]", fontsize=cms.FS_LABEL)
    # Room for BOTH the two-line bar annotations (which reach ~107 on this scale) and
    # the summary block above them; at ylim 118 they landed on top of each other.
    ax.set_ylim(0, 150)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, label=cms.CMS_LABEL_DATA)
    lines = [f"all eras: {100.0 * sum(gtot) / sum(dtot):.1f}%"
             f"  ({sum(gtot):,} / {sum(dtot):,})",
             "numerator: golden AND DCS   denominator: DCS-only",
             "lumisections, NOT integrated luminosity"]
    n_out = sum(outside)
    if n_out:
        lines.append(f"{n_out:,} golden LS lie OUTSIDE DCS (excluded)")
    cms.info_legend(ax, lines, loc="upper left", fontsize=cms.FS_LEGEND - 3)
    fig.suptitle("What fraction of each era survives the golden JSON?",
                 fontsize=cms.FS_TITLE)
    fig.tight_layout()
    return fig


def page_fragmentation(cert, n_show=14):
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(11, 9),
                                 gridspec_kw=dict(height_ratios=[1, 1.5]))
    nint = np.array([len(v) for v in cert.values()])
    ax.hist(nint, bins=np.arange(0.5, nint.max() + 1.5), color="steelblue")
    ax.set_yscale("log")
    ax.set_xlabel("Disjoint certified lumisection intervals in a run",
                  fontsize=cms.FS_LABEL - 2)
    ax.set_ylabel("Runs", fontsize=cms.FS_LABEL - 2)
    ax.tick_params(which="both", direction="in", top=True, right=True)
    ax.minorticks_on()
    whole = int((nint == 1).sum())
    cms.info_legend(ax, [
        f"{whole} of {len(nint)} runs ({100.0 * whole / len(nint):.0f}%) "
        f"certified as ONE interval",
        f"worst run is split into {nint.max()} intervals",
        "-> a run-level mask cannot reproduce this",
    ], loc="upper right", fontsize=cms.FS_LEGEND - 2)

    worst = sorted(cert, key=lambda r: -len(cert[r]))[:n_show]
    for y, run in enumerate(worst):
        for a, b in cert[run]:
            bx.barh(y, b - a + 1, left=a, height=0.65, color="seagreen")
        hi = max(b for _, b in cert[run])
        bx.barh(y, hi, left=0, height=0.65, color="lightgrey", zorder=0)
    bx.set_yticks(range(len(worst)))
    bx.set_yticklabels([f"{r}  ({len(cert[r])})" for r in worst],
                       fontsize=cms.FS_LEGEND - 3)
    bx.invert_yaxis()
    bx.set_xlabel("Lumisection", fontsize=cms.FS_LABEL - 2)
    bx.tick_params(which="both", direction="in", top=True, right=True)
    bx.set_title("Most fragmented runs: green = certified, grey = not",
                 fontsize=cms.FS_LEGEND)
    fig.suptitle("How fragmented is the certification?", fontsize=cms.FS_TITLE)
    fig.tight_layout()
    return fig


def main():
    p = argparse.ArgumentParser(description="visualise a golden certification JSON")
    p.add_argument("--json", default=GOLDEN)
    p.add_argument("--dcs", default=DCS,
                   help="DCS-only JSON used as the denominator of the certified fraction")
    p.add_argument("--output", default="goldenJSON.pdf")
    p.add_argument("--no-publish", action="store_true")
    args = p.parse_args()

    cert = load(args.json)
    log(f"{os.path.basename(args.json)}: {len(cert)} runs, "
        f"{n_ls(sum(cert.values(), [])):,} lumisections")

    era_cert, era_runs = {}, {}
    for e in ERAS:
        if e == "I_v2":
            continue                       # produced by splitting I, just below
        path = ERA_JSON % e
        if os.path.exists(path):
            era_cert[e] = load(path)
            era_runs[e] = set(era_cert[e])
    if "I" in era_cert:
        full_i = era_cert["I"]
        era_cert["I"] = {r: v for r, v in full_i.items() if r < I_V2_FIRST_RUN}
        era_cert["I_v2"] = {r: v for r, v in full_i.items() if r >= I_V2_FIRST_RUN}
        era_runs["I"] = set(era_cert["I"])
        era_runs["I_v2"] = set(era_cert["I_v2"])
        log(f"  era I split at run {I_V2_FIRST_RUN}: "
            f"I -> {len(era_runs['I'])} runs, I_v2 -> {len(era_runs['I_v2'])} runs")
    log(f"per-era files found: {', '.join(sorted(era_cert)) or 'none'}")

    dcs = load(args.dcs) if os.path.exists(args.dcs) else None
    if dcs is None:
        log(f"  [warn] no DCS-only JSON at {args.dcs} -- skipping the fraction page",
            file=sys.stderr)
    else:
        log(f"  DCS-only: {len(dcs)} runs, {n_ls(sum(dcs.values(), [])):,} lumisections")

    pages = [page_per_run(cert, era_runs),
             page_cumulative(cert, era_runs),
             page_era_totals(cert, era_runs, era_cert)]
    if dcs is not None:
        pages.append(page_certified_fraction(cert, dcs, era_runs))
    pages.append(page_fragmentation(cert))

    with PdfPages(args.output) as pdf:
        for fig in pages:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close("all")
    log(f"Saved: {args.output} ({len(pages)} pages)")

    if not args.no_publish:
        try:
            os.makedirs(WEBDIR, exist_ok=True)
            subprocess.run(["cp", args.output, WEBDIR], check=True)
            log(f"Published: {os.path.join(WEBDIR, os.path.basename(args.output))}")
        except Exception as exc:
            log(f"[warn] publish failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
