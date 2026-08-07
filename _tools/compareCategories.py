#!/usr/bin/env python3
"""Per-category displacement distributions -- singlev, quadv, multiv (SIGNAL ONLY).

The three analysis groups, each binned on the displacement of its OWN vertex:

  * singlev / multiv : muonSV_dxy at min_chi2_index, exactly as config/legacy_2018.py
    bins them (a single lowest-chi2 neutral dimuon vertex -> singlev, cat_index == 0;
    two or more paired vertices -> multiv). Reproduced by _get_multivertices() /
    match_singlev_multiv(), a faithful port of get_multivertices() from
    modules/muonsv_selection.py.
  * quadv : fourmuonSV_dxy, the four-muon vertex's own displacement, for events with a
    valid "fourmuonSV + 2 consistent muonSV" configuration (ca.match_quadv). This is the
    variable the quadv category is defined on (config/run3_2024.py), so no comparison to
    the 2-muonSV midpoint is made here.

Only events passing the trigger + f_kin_or pre-selection (see compareCategoriesQuadv.py)
enter the plots. Formatting follows the CMS conventions -- see _tools/cmsstyle.py.

Each category gets its OWN set of three pages (the categories are NOT overlaid), nine
pages per PDF. Within a set the signal points are overlaid (colour = signal). Per category:

  * displacement, log x, log y
  * displacement, linear x (0 -- XMAX cm), log y
  * displacement split into two pointing-angle bins (< 0.2 and > 0.2), side by side,
    each with a per-(signal, dxy-bin) counts table below.

Order: singlev set, then quadv set, then multiv set.

THREE PDFs are written from a single read of each signal, differing in the dimuon
opening-angle requirement on the binning vertex:
  * compareCategories_DeltaRinclusive.pdf -- no dR cut
  * compareCategories_DeltaRCut.pdf        -- dR(mu,mu) < 1.2 (the framework's requirement)
  * compareCategories_DeltaRComparison.pdf -- both overlaid, inclusive solid / cut dashed;
    its tables give both counts per cell as "N(incl) | N(<1.2)".
Each page's info legend and title state the dR selection.

Run after sourcing setup.sh:
    python _tools/compareCategories.py [--output path.pdf] [--n-signal N] [--test]

--test reads only 1 file per signal point for a quick debug pass.
"""

import argparse
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

# reuse the quadv script's file discovery, reader (trigger + f_kin_or pre-selection),
# branch lists and quadv matcher, rather than duplicating them.
import compareCategoriesQuadv as ca
import cmsstyle as cms

XMAX        = 100.0        # cm, upper end of the displayed displacement range
DXY_EDGES   = (1.0, 10.0)  # dxy category boundaries [cm]: <1, 1-10, >10
PANGLE_EDGE = 0.2          # pointing-angle category boundary [rad]
NOCUT       = 1e9          # dr_max value that effectively disables the dR requirement

# describes the current PDF's dR selection; set by main() before writing each PDF, and
# appended to every page title so the two output files are unambiguous
DR_NOTE = ""

# muonSV_pAngle is needed for the singlev/multiv split; the quadv script does not read it
SV_EXTRA_BRANCHES = ["muonSV_pAngle"]

# Signal points, ordered as requested: both Scenario A points (increasing lifetime),
# then both Scenario B1 points (increasing lifetime). "tag" (used in the tables) writes
# the scenario as "scA"/"scB1".
def _sig(dirname, label, color, tag):
    return {"dir": dirname + "_TuneCP5_13p6TeV_powheg-pythia8",
            "label": label, "color": color, "tag": tag}

SIGNALS = [
    _sig("GluGluHToDarkShowers-ScenarioA_Par-ctau-0p1-mA-3p33-mpi-10",
         r"Scenario A: $m_\pi$=10 GeV, $m_A$=3.33 GeV, $c\tau$=0.1 mm",
         "forestgreen", r"scA c$\tau$=0.1"),
    _sig("GluGluHToDarkShowers-ScenarioA_Par-ctau-10-mA-3p33-mpi-10",
         r"Scenario A: $m_\pi$=10 GeV, $m_A$=3.33 GeV, $c\tau$=10 mm",
         "darkorange", r"scA c$\tau$=10"),
    _sig("GluGluHToDarkShowers-ScenarioB1_Par-ctau-0p1-mA-1p33-mpi-4",
         r"Scenario B1: $m_\pi$=4 GeV, $m_A$=1.33 GeV, $c\tau$=0.1 mm",
         "crimson", r"scB1 c$\tau$=0.1"),
    _sig("GluGluHToDarkShowers-ScenarioB1_Par-ctau-10-mA-1p33-mpi-4",
         r"Scenario B1: $m_\pi$=4 GeV, $m_A$=1.33 GeV, $c\tau$=10 mm",
         "darkviolet", r"scB1 c$\tau$=10"),
]
for _s in SIGNALS:
    _s["path"] = f"{ca.BASE}/{_s['dir']}"

# the three categories, in display order (each gets its own set of pages)
CATEGORIES = ["singlev", "quadv", "multiv"]

# legend/title text for the dR-selection variants (used in the comparison set)
DR_INCL_LABEL = r"$\Delta R$ inclusive"
DR_CUT_LABEL  = r"$\Delta R < 1.2$"


def log(msg, **kwargs):
    print(msg, flush=True, **kwargs)


# ----------------------------------------------------------------------------
# category matching
# ----------------------------------------------------------------------------
def _get_multivertices(mass, chi2, m1eta, m1phi, m2eta, m2phi, i1, i2, dr_max=1.2):
    """Python port of get_multivertices() from modules/muonsv_selection.py, run over the
    NEUTRAL muonSV subset exactly as the framework does. Returns (chi2s, indexes) of the
    selected vertices, positions being WITHIN the subset passed in.

    Pairs of quality muonSVs (chi2 < 10, eta != 0, dR < dr_max) whose masses agree to 3
    sigma (sigma = 1% of the mass) and which share no muon are kept; where two pairs share
    a vertex, the one whose OTHER vertex has the larger chi2 is dropped. If nothing pairs
    up, the single lowest-chi2 quality vertex is kept -- that is the singlev case.

    *dr_max* is the framework's 1.2 by default; pass NOCUT to disable the dR requirement
    (everything else -- chi2, eta, mass window, muon sharing -- is unchanged).

    NOTE: the C++ inner loop tests the dR of imuonSV again instead of imuonSV1 (a
    copy-paste slip). It is reproduced here on purpose: this script exists to describe what
    the framework actually selects, so it must match warts and all.
    """
    n = len(chi2)

    def quality(i):
        return (chi2[i] <= 10 and m1eta[i] != 0 and m2eta[i] != 0
                and ca._deltaR(m1eta[i], m1phi[i], m2eta[i], m2phi[i]) <= dr_max)

    pairs = []
    for a in range(max(n - 1, 0)):
        if not quality(a):
            continue
        for b in range(a + 1, n):
            # the framework re-tests `a`'s dR here, not `b`'s -- mirrored deliberately
            if (chi2[b] > 10 or m1eta[b] == 0 or m2eta[b] == 0
                    or ca._deltaR(m1eta[a], m1phi[a], m2eta[a], m2phi[a]) > dr_max):
                continue
            if mass[a] <= 0:
                continue
            if abs(mass[a] - mass[b]) / mass[a] >= 3 * 0.01:
                continue
            if len({i1[a], i2[a], i1[b], i2[b]}) == 4:
                pairs.append((a, b))

    # cleaning: two pairs sharing a vertex -> drop the one whose other vertex has larger chi2
    valid = [True] * len(pairs)
    for p in range(max(len(pairs) - 1, 0)):
        if not valid[p]:
            continue
        for q in range(p + 1, len(pairs)):
            if not valid[q]:
                continue
            if pairs[p][0] == pairs[q][0]:
                if chi2[pairs[p][1]] > chi2[pairs[q][1]]:
                    valid[p] = False
                    break
                valid[q] = False
            elif pairs[p][1] == pairs[q][1]:
                if chi2[pairs[p][0]] > chi2[pairs[q][0]]:
                    valid[p] = False
                    break
                valid[q] = False

    indexes, chi2s = [], []
    for p, ok in enumerate(valid):
        if not ok:
            continue
        for idx in pairs[p]:
            if idx not in indexes:
                indexes.append(idx)
                chi2s.append(chi2[idx])

    if not indexes:
        # nothing paired up: keep the single lowest-chi2 quality vertex (the singlev case)
        cand = [i for i in range(n) if quality(i)]
        if cand:
            best = min(cand, key=lambda i: chi2[i])
            indexes.append(best)
            chi2s.append(chi2[best])
    return chi2s, indexes


def match_singlev_multiv(data, label, dr_max=1.2):
    """Reproduce the framework's singlev/multiv split and return, per event, the dxy and
    pAngle of the binning vertex -- muonSV_{dxy,pAngle}.at(min_chi2_index), exactly as
    config/legacy_2018.py's categories use them. *dr_max* gates the dimuon opening angle
    (1.2 = framework; NOCUT = no dR requirement).

    Returns {"singlev": (dxy, pAngle), "multiv": (dxy, pAngle)} as numpy arrays.
    cat_index == 0 -> singlev, != 0 -> multiv (the same rule as the config).
    """
    import awkward as ak
    chg = ak.to_list(data["muonSV_charge"])
    mass = ak.to_list(data["muonSV_mass"]);  chi2 = ak.to_list(data["muonSV_chi2"])
    m1e = ak.to_list(data["muonSV_mu1eta"]); m1p = ak.to_list(data["muonSV_mu1phi"])
    m2e = ak.to_list(data["muonSV_mu2eta"]); m2p = ak.to_list(data["muonSV_mu2phi"])
    i1 = ak.to_list(data["muonSV_mu1index"]); i2 = ak.to_list(data["muonSV_mu2index"])
    dxy = ak.to_list(data["muonSV_dxy"]);    pa = ak.to_list(data["muonSV_pAngle"])

    out = {"singlev": ([], []), "multiv": ([], [])}
    for e in range(len(chg)):
        # the framework runs get_multivertices over the NEUTRAL subset, then remaps the
        # resulting positions back onto the full muonSV collection
        keep = [k for k in range(len(chg[e])) if chg[e][k] == 0]
        if not keep:
            continue
        sub = lambda v: [v[e][k] for k in keep]
        chi2s, idxs = _get_multivertices(sub(mass), sub(chi2), sub(m1e), sub(m1p),
                                         sub(m2e), sub(m2p), sub(i1), sub(i2), dr_max=dr_max)
        if not idxs:
            continue
        cat_index = len(idxs) // 2                    # int(mass_multivertices.size() / 2)
        best = keep[idxs[int(np.argmin(chi2s))]]      # min_chi2_index, remapped to full
        # single_sel additionally demands both muon etas be non-zero at that vertex
        if m1e[e][best] == 0 or m2e[e][best] == 0:
            continue
        key = "singlev" if cat_index == 0 else "multiv"
        out[key][0].append(dxy[e][best])
        out[key][1].append(pa[e][best])

    res = {k: (np.array(v[0], dtype=float), np.array(v[1], dtype=float))
           for k, v in out.items()}
    tag = "dR<1.2" if dr_max < 100 else "no dR cut"
    log(f"  [{label}] [{tag}] singlev: {len(res['singlev'][0]):,} events, "
        f"multiv: {len(res['multiv'][0]):,} events")
    return res


def match_categories(data, label, dr_max=1.2):
    """Return {cat: (dxy, pAngle)} for singlev, quadv and multiv, as numpy arrays.

    singlev/multiv use muonSV_{dxy,pAngle} at min_chi2_index; quadv uses the selected
    fourmuonSV's own fourmuonSV_{dxy,pAngle}. *dr_max* gates the dimuon opening angle in
    all three (1.2 = framework; NOCUT = no dR requirement). For quadv it is applied by
    temporarily overriding ca.DR_MAX, which ca.match_quadv reads."""
    import awkward as ak
    sv = match_singlev_multiv(data, label, dr_max=dr_max)

    saved = ca.DR_MAX
    ca.DR_MAX = dr_max
    try:
        matches = ca.match_quadv(data, label)
    finally:
        ca.DR_MAX = saved
    fdxy = ak.to_list(data["fourmuonSV_dxy"])
    fpa  = ak.to_list(data["fourmuonSV_pAngle"])
    qdxy = np.array([fdxy[m["evt"]][m["fourmu"]] for m in matches], dtype=float)
    qpa  = np.array([fpa[m["evt"]][m["fourmu"]] for m in matches], dtype=float)

    return {"singlev": sv["singlev"], "quadv": (qdxy, qpa), "multiv": sv["multiv"]}


def read_both_variants(urls, label):
    """Read a signal ONCE and return (no_cut, with_cut) category dicts, so the two PDFs
    do not double the (network-bound) reading."""
    empty = {c: (np.array([]), np.array([])) for c in CATEGORIES}
    data = ca.read_branches(urls, ca.FOURMU_BRANCHES + ca.MUONSV_BRANCHES
                            + SV_EXTRA_BRANCHES, label)
    if data is None:
        log(f"  [warn] {label}: no readable files", file=sys.stderr)
        return empty, empty
    return match_categories(data, label, dr_max=NOCUT), \
           match_categories(data, label, dr_max=1.2)


# ----------------------------------------------------------------------------
# plotting -- each category (singlev / quadv / multiv) gets its OWN set of pages
# (the categories are NOT overlaid); a set is one category with the signal points
# overlaid. Three PDFs are written: DeltaR-inclusive, DeltaR<1.2, and a comparison
# overlaying the two (inclusive solid, cut dashed).
# ----------------------------------------------------------------------------
# what displacement each category is binned on, for the page titles
CAT_VAR = {"singlev": "muonSV_dxy at min_chi2_index",
           "quadv":   "fourmuonSV_dxy",
           "multiv":  "muonSV_dxy at min_chi2_index"}


def _draw_curves(ax, sig_cats, cat, bins, sel, ls):
    """Draw one displacement curve per signal (colour = signal, line style = *ls*)."""
    for sig, cats in sig_cats:
        dxy, pa = cats[cat]
        v = dxy if sel is None else dxy[sel(pa)]
        if len(v) == 0:
            continue
        counts, edges = np.histogram(v, bins=bins)
        ax.stairs(counts, edges, color=sig["color"], lw=2, ls=ls)


def _finish_panel(ax, bins, logx, frac):
    """Category edges, log scales, axis titles, CMS decorations, headroom."""
    for edge in DXY_EDGES:
        ax.axvline(edge, color="grey", ls=":", lw=1.2, alpha=0.9)
    if logx:
        ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(bins[0], bins[-1])
    ax.set_xlabel("Displacement dxy [cm]", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Number of entries", fontsize=cms.FS_LABEL)
    cms.cms_axes(ax, fontsize=cms.FS_AXES)
    cms.extend_log_top(ax, frac)


def _dxy_bins(logx):
    return (np.logspace(-4, np.log10(XMAX), 60) if logx else np.linspace(0, XMAX, 60))


# ---- legends ---------------------------------------------------------------
def _sig_handles(sig_cats):
    return ([Line2D([], [], color=s["color"], lw=2) for s, _ in sig_cats],
            [s["label"] for s, _ in sig_cats])


def _cat_legend(ax, sig_cats, fontsize=None):
    """One frameless legend: the signal points. Smaller than the other legends -- the
    signal labels are long, so a big font here crowds the plot."""
    fontsize = cms.FS_LEGEND - 3 if fontsize is None else fontsize
    handles, labels = _sig_handles(sig_cats)
    ax.legend(handles=handles, labels=labels, fontsize=fontsize, loc="upper right",
              **cms.LEGEND_KW)


def _cmp_legend(ax, sig_cats, fontsize=None):
    """Signal points, a blank spacer row, then the solid/dashed dR-selection key."""
    fontsize = cms.FS_LEGEND - 3 if fontsize is None else fontsize
    handles, labels = _sig_handles(sig_cats)
    bh, bl = cms.blank_entry()
    handles.append(bh)
    labels.append(bl)
    handles += [Line2D([], [], color="black", lw=2, ls="-"),
                Line2D([], [], color="black", lw=2, ls="--")]
    labels  += [f"{DR_INCL_LABEL} (solid)", f"{DR_CUT_LABEL} (dashed)"]
    ax.legend(handles=handles, labels=labels, fontsize=fontsize, loc="upper right",
              **cms.LEGEND_KW)


def _cat_info(ax, lines, fontsize=None):
    """info legend with the leading "Category: ..." line in bold."""
    fontsize = cms.FS_LEGEND if fontsize is None else fontsize
    leg = cms.info_legend(ax, lines, fontsize=fontsize)
    if leg is not None:
        leg.get_texts()[0].set_fontweight("bold")   # the "Category:" line
    return leg


# ---- tables ----------------------------------------------------------------
def _dxy_cat_counts(dxy):
    """Entries per dxy category [<1, 1-10, >10] plus total."""
    dxy = np.asarray(dxy)
    return [int(np.sum(dxy < DXY_EDGES[0])),
            int(np.sum((dxy >= DXY_EDGES[0]) & (dxy < DXY_EDGES[1]))),
            int(np.sum(dxy >= DXY_EDGES[1])),
            int(len(dxy))]


_COL_LABELS = [r"dxy$<$1", "1--10", r"dxy$>$10", "Total"]


def _cat_table(ax, sig_cats, cat, sel):
    """Counts per signal x dxy bin for ONE category, events passing *sel*."""
    ax.axis("off")
    rows, cells, row_colors = [], [], []
    for sig, cats in sig_cats:
        dxy, pa = cats[cat]
        rows.append(sig["tag"])
        cells.append([f"{x:,}" for x in _dxy_cat_counts(dxy[sel(pa)])])
        row_colors.append(sig["color"])
    tbl = ax.table(cellText=cells, rowLabels=rows, colLabels=_COL_LABELS,
                   cellLoc="center", rowLoc="center", bbox=[0.35, 0.0, 0.6, 1.0])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    for r, col in enumerate(row_colors):
        tbl[(r + 1, -1)].get_text().set_color(col)


def _cmp_table(ax, nocut_cats, cut_cats, cat, sel):
    """Counts per signal x dxy bin with BOTH selections in each cell, as
    'N(DeltaR incl.) | N(DeltaR<1.2)'. A small note above explains the format."""
    ax.axis("off")
    ax.text(0.5, 1.02, r"cell: N($\Delta R$ inclusive)  |  N($\Delta R < 1.2$)",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8, style="italic")
    rows, cells, row_colors = [], [], []
    for (sig, nc), (_, cc) in zip(nocut_cats, cut_cats):
        ndxy, npa = nc[cat]
        cdxy, cpa = cc[cat]
        ni = _dxy_cat_counts(ndxy[sel(npa)])
        ci = _dxy_cat_counts(cdxy[sel(cpa)])
        rows.append(sig["tag"])
        cells.append([f"{ni[k]:,} | {ci[k]:,}" for k in range(4)])
        row_colors.append(sig["color"])
    tbl = ax.table(cellText=cells, rowLabels=rows, colLabels=_COL_LABELS,
                   cellLoc="center", rowLoc="center", bbox=[0.28, 0.0, 0.70, 0.88])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7)
    for r, col in enumerate(row_colors):
        tbl[(r + 1, -1)].get_text().set_color(col)


# ---- pages -----------------------------------------------------------------
def _title(cat, dr_label, extra=""):
    return (f"{cat}: displacement of the binning vertex ({CAT_VAR[cat]}){extra}\n"
            f"{dr_label};   dotted: dxy category edges (1, 10 cm)")


_SPLITS = [(r"Pointing angle $<$ %.1f" % PANGLE_EDGE, lambda pa: pa < PANGLE_EDGE),
           (r"Pointing angle $>$ %.1f" % PANGLE_EDGE, lambda pa: pa >= PANGLE_EDGE)]


# --- single-variant pages (one dR selection) --------------------------------
def _page_dxy(sig_cats, cat, logx, dr_label):
    fig, ax = plt.subplots(figsize=(10, 8))
    bins = _dxy_bins(logx)
    _draw_curves(ax, sig_cats, cat, bins, None, "-")
    _finish_panel(ax, bins, logx, 0.80)
    _cat_legend(ax, sig_cats)
    _cat_info(ax, [f"Category: {cat}", dr_label])
    fig.suptitle(_title(cat, dr_label), fontsize=cms.FS_TITLE)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return fig


def _page_pangle_split(sig_cats, cat, dr_label):
    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1.3], hspace=0.32, wspace=0.18)
    bins = _dxy_bins(True)
    for col, (ptitle, sel) in enumerate(_SPLITS):
        ax = fig.add_subplot(gs[0, col])
        _draw_curves(ax, sig_cats, cat, bins, sel, "-")
        _finish_panel(ax, bins, True, 0.75)   # 5% less tall, to clear the legend
        _cat_legend(ax, sig_cats, fontsize=9)
        _cat_info(ax, [f"Category: {cat}", dr_label, ptitle], fontsize=11)
        _cat_table(fig.add_subplot(gs[1, col]), sig_cats, cat, sel)
    fig.suptitle(_title(cat, dr_label, ", split by pointing angle"), fontsize=cms.FS_TITLE)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return fig


# --- comparison pages (both dR selections overlaid) -------------------------
_CMP_LABEL = f"{DR_INCL_LABEL} (solid) vs {DR_CUT_LABEL} (dashed)"


def _page_cmp_dxy(nocut_cats, cut_cats, cat, logx):
    fig, ax = plt.subplots(figsize=(10, 8))
    bins = _dxy_bins(logx)
    _draw_curves(ax, nocut_cats, cat, bins, None, "-")
    _draw_curves(ax, cut_cats,   cat, bins, None, "--")
    _finish_panel(ax, bins, logx, 0.80)
    _cmp_legend(ax, nocut_cats)
    _cat_info(ax, [f"Category: {cat}"])
    fig.suptitle(_title(cat, _CMP_LABEL), fontsize=cms.FS_TITLE)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return fig


def _page_cmp_pangle_split(nocut_cats, cut_cats, cat):
    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1.45], hspace=0.40, wspace=0.18)
    bins = _dxy_bins(True)
    for col, (ptitle, sel) in enumerate(_SPLITS):
        ax = fig.add_subplot(gs[0, col])
        _draw_curves(ax, nocut_cats, cat, bins, sel, "-")
        _draw_curves(ax, cut_cats,   cat, bins, sel, "--")
        _finish_panel(ax, bins, True, 0.75)
        _cmp_legend(ax, nocut_cats, fontsize=8)
        _cat_info(ax, [f"Category: {cat}", ptitle], fontsize=11)
        _cmp_table(fig.add_subplot(gs[1, col]), nocut_cats, cut_cats, cat, sel)
    fig.suptitle(_title(cat, _CMP_LABEL, ", split by pointing angle"), fontsize=cms.FS_TITLE)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return fig


# ----------------------------------------------------------------------------
def _write_single(out, sig_cats, dr_label):
    log(f"\n=== Writing {out}  ({dr_label}) ===")
    page = 0
    with PdfPages(out) as pdf:
        for cat in CATEGORIES:
            for fig in (_page_dxy(sig_cats, cat, True, dr_label),
                        _page_dxy(sig_cats, cat, False, dr_label),
                        _page_pangle_split(sig_cats, cat, dr_label)):
                page += 1
                pdf.savefig(fig, bbox_inches="tight")
                plt.close("all")
    log(f"Saved: {out} ({page} pages)")


def _write_comparison(out, nocut_cats, cut_cats):
    log(f"\n=== Writing {out}  (DeltaR inclusive vs < 1.2) ===")
    page = 0
    with PdfPages(out) as pdf:
        for cat in CATEGORIES:
            for fig in (_page_cmp_dxy(nocut_cats, cut_cats, cat, True),
                        _page_cmp_dxy(nocut_cats, cut_cats, cat, False),
                        _page_cmp_pangle_split(nocut_cats, cut_cats, cat)):
                page += 1
                pdf.savefig(fig, bbox_inches="tight")
                plt.close("all")
    log(f"Saved: {out} ({page} pages)")


def main():
    parser = argparse.ArgumentParser(
        description="Per-category (singlev/quadv/multiv) displacement, signal only")
    parser.add_argument("--output", default="compareCategories.pdf",
                        help="Base name; three PDFs are written: <base>_DeltaRinclusive.pdf,"
                             " <base>_DeltaRCut.pdf, <base>_DeltaRComparison.pdf")
    parser.add_argument("--n-signal", type=int, default=ca.N_SIGNAL_FILES,
                        help=f"Signal files per point (default: {ca.N_SIGNAL_FILES})")
    parser.add_argument("--test", action="store_true",
                        help="Quick check: read only 1 file per signal point")
    args = parser.parse_args()

    if args.test:
        log("[TEST MODE] reading only 1 file per signal point")
    n_sig = 1 if args.test else args.n_signal

    # read each signal once; keep both dR variants
    nocut_cats, cut_cats = [], []
    n_read, n_avail = 0, 0
    for sig in SIGNALS:
        log(f"\n=== {sig['dir']} (taking {n_sig} files) ===")
        all_urls = ca.list_root_files(sig["path"])
        urls = all_urls[:n_sig]
        n_avail += len(all_urls)
        n_read += len(urls)
        if not urls:
            log(f"  [warn] no files for {sig['dir']}", file=sys.stderr)
            continue
        nocut, cut = read_both_variants(urls, sig["label"])
        nocut_cats.append((sig, nocut))
        cut_cats.append((sig, cut))

    if not nocut_cats:
        log("ERROR: no signal data to plot", file=sys.stderr)
        sys.exit(1)

    cms.set_sample_files(n_read, n_avail)
    if cms.is_partial():
        log(f"\n  PARTIAL SAMPLE: {n_read} of {n_avail} files "
            f"({100 * cms.sample_fraction():.1f}%) -- every plot is labelled as such")
    else:
        log(f"\n  full sample: all {n_avail} files read")

    base = args.output[:-4] if args.output.endswith(".pdf") else args.output
    _write_single(base + "_DeltaRinclusive.pdf", nocut_cats, DR_INCL_LABEL)
    _write_single(base + "_DeltaRCut.pdf",        cut_cats,   DR_CUT_LABEL)
    _write_comparison(base + "_DeltaRComparison.pdf", nocut_cats, cut_cats)


if __name__ == "__main__":
    main()
