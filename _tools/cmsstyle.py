#!/usr/bin/env python3
"""Shared CMS plotting conventions for the _tools/compare*.py cross-check scripts.

Single source of truth, so the convention is fixed in one place rather than drifting
across scripts. Import it and use `_cms_axes` / `info_legend` / `LEGEND_KW`:

    import cmsstyle as cms
    cms.set_sample_files(n_read, n_available)   # once, before plotting
    ...
    cms.cms_axes(ax)                            # CMS label + energy/year + 4-sided ticks
    ax.legend(..., **cms.LEGEND_KW)             # no border, semi-transparent white bg
    cms.info_legend(ax, ["Pointing angle < 0.2"])

The conventions:

  * "CMS" bold, the extra text ("Simulation", "Preliminary", ...) italic, top-left.
    If data is not explicitly added, it is all simulation.
  * Top-right: energy and year. Luminosity ONLY when data (or MC normalised to data) is
    shown -- and then scaled to the fraction of the sample actually read, see lumi_header().
  * The plot title carries nothing else. Selections go in an in-plot legend, broader
    context in the page title (fig.suptitle).
  * Ticks on all four sides, pointing inwards.
  * One legend per plot, no border, semi-transparent white background so labels stay
    readable over the curves without hiding them.
  * Uncertainty bands drawn faint (BAND_ALPHA).
  * A partial read is always stated on the plot, in bold.
  * Keep axis titles terse ("Fraction of events"); the verbose version goes in the page
    title.
"""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.legend import Legend

# CMS-style axis-title placement: x flush right, y flush top
plt.rcParams["xaxis.labellocation"] = "right"
plt.rcParams["yaxis.labellocation"] = "top"

# "CMS" bold + italic extra text. Use CMS_LABEL when the page is simulation only (if data
# is not explicitly added, it is all simulation); CMS_LABEL_DATA the moment real data is
# drawn -- calling a page with data "Simulation" would be simply wrong.
CMS_LABEL = r"$\bf{CMS}$ $\it{Simulation\ Preliminary}$"
CMS_LABEL_DATA = r"$\bf{CMS}$ $\it{Preliminary}$"

# Simulation-only header: energy and year, NO luminosity -- quoting one next to a
# normalised MC shape would be meaningless, nothing is scaled to it.
SIM_HEADER = r"(13.6 TeV, 2024)"

# Full-sample luminosity (cf. getSignalEff_noMET.C: LUMI = 109.95e3 pb^-1, 2024, 13.6 TeV)
LUMI_FB = 109.95

# Legends: no border (distracting), but keep the semi-transparent white background so a
# label stays readable where it overlaps a curve while the curve still shows through.
LEGEND_KW = dict(frameon=True, framealpha=0.6, edgecolor="none", facecolor="white")

# Uncertainty bands are context, not the message: a strong shade competes with the curve.
BAND_ALPHA = 0.12

# Preferred font sizes for the compare*.py cross-check plots. Bumped up so the plots read
# clearly in slides -- use these on new plots of this kind rather than ad-hoc numbers.
FS_LABEL  = 15   # axis titles
FS_LEGEND = 13   # in-plot legends
FS_TITLE  = 15   # page title (fig.suptitle)
FS_AXES   = 15   # pass to cms_axes(): CMS label = +1, header = this, tick labels = this-1

# (files read, files available) over everything drawn; set by set_sample_files().
SAMPLE_FILES = (0, 0)

# (data files read, data files available). Luminosity belongs to the DATA, so on a page
# mixing MC and data it must NOT scale with the blended file count -- reading 60 QCD files
# says nothing about how much data is shown. Set via set_lumi_files(); when unset,
# lumi_header() falls back to the overall sample fraction (right for a data-only page).
LUMI_FILES = None


def set_sample_files(n_read, n_available):
    """Record how much of the sample was read. Call before any plotting: it drives the
    "Partial sample plot" label (and the luminosity, unless set_lumi_files() overrides)."""
    global SAMPLE_FILES
    SAMPLE_FILES = (n_read, n_available)


def set_lumi_files(n_read, n_available):
    """Record how much of the DATA was read, for scaling the quoted luminosity. Use this
    on any page that mixes data with MC."""
    global LUMI_FILES
    LUMI_FILES = (n_read, n_available)


def sample_fraction():
    read, avail = SAMPLE_FILES
    return (read / avail) if avail else 1.0


def lumi_fraction():
    read, avail = LUMI_FILES if LUMI_FILES else SAMPLE_FILES
    return (read / avail) if avail else 1.0


def is_partial():
    return sample_fraction() < 0.999


def partial_label():
    read, avail = SAMPLE_FILES
    return f"Partial sample plot ({read} of {avail} files)"


def lumi_header():
    """Header for a page showing data (or MC normalised to data). The luminosity is scaled
    by the fraction of the DATA read (see set_lumi_files), so the number matches what is
    actually drawn -- never quote the full lumi next to a fraction of the events."""
    return rf"{LUMI_FB * lumi_fraction():.3g} fb$^{{-1}}$ (13.6 TeV, 2024)"


def cms_axes(ax, header=SIM_HEADER, fontsize=12, label=CMS_LABEL):
    """CMS label (left), energy/year header (right), ticks mirrored inwards on all four
    sides. On a page that shows data pass BOTH header=lumi_header() and
    label=CMS_LABEL_DATA."""
    ax.tick_params(which="both", direction="in", top=True, right=True, labelsize=fontsize - 1)
    ax.minorticks_on()
    ax.set_title(label, loc="left", fontsize=fontsize + 1)
    ax.set_title(header, loc="right", fontsize=fontsize)


def blank_entry():
    """An invisible handle + empty label: a spacer row inside a legend. Use this to group
    entries in ONE legend instead of opening a second one."""
    return Line2D([], [], ls="", marker=""), " "


def info_legend(ax, lines=(), loc="upper left", fontsize=9):
    """Text-only in-plot legend for the panel's selection plus, when only part of the
    sample was read, the bold "Partial sample plot" warning.

    Built via Legend(...) + add_artist rather than ax.legend(), so it never displaces a
    curve legend the page has already put on the axes."""
    lines = list(lines)
    partial_idx = None
    if is_partial():
        partial_idx = len(lines)
        lines.append(partial_label())
    if not lines:
        return None
    handles = [Line2D([], [], ls="", marker="") for _ in lines]
    leg = Legend(ax, handles, lines, loc=loc, fontsize=fontsize,
                 handlelength=0, handletextpad=0, labelspacing=0.3, **LEGEND_KW)
    if partial_idx is not None:      # make the warning stand out
        leg.get_texts()[partial_idx].set_fontweight("bold")
    ax.add_artist(leg)
    ax._has_info_legend = True       # stamp_partial() must not add a second one
    return leg


def partial_samples_legend(ax, samples, loc="upper left", fontsize=9):
    """In-plot legend headed by a bold "Partial sample plot", then one line per sample
    that was only PARTIALLY read -- fully-read samples are omitted. Nothing is drawn if
    every sample is complete.

    *samples* = iterable of (name, files_read, files_available). Use this instead of the
    generic info_legend() when the samples have independent file counts (e.g. QCD bins vs
    signal points) and you want a per-sample breakdown."""
    parts = [(n, r, a) for n, r, a in samples if a and r < a]
    if not parts:
        return None
    lines = ["Partial sample plot"]
    lines += [f"{n}: {r:,} of {a:,} files ({100 * r / a:.1f}%)" for n, r, a in parts]
    handles = [Line2D([], [], ls="", marker="") for _ in lines]
    leg = Legend(ax, handles, lines, loc=loc, fontsize=fontsize,
                 handlelength=0, handletextpad=0, labelspacing=0.3, **LEGEND_KW)
    leg.get_texts()[0].set_fontweight("bold")   # the "Partial sample plot" title
    ax.add_artist(leg)
    ax._has_info_legend = True
    return leg


def stamp_partial(fig):
    """Put the partial-sample warning on every axes of *fig* that has data and no info
    legend of its own, so a partial read can never go unstated on a page."""
    if not is_partial():
        return
    for ax in fig.axes:
        if getattr(ax, "_has_info_legend", False) or not ax.get_visible():
            continue
        if ax.has_data():
            info_legend(ax)


def extend_log_top(ax, frac=0.75):
    """Raise the (log) y upper limit so the tallest bar fills only *frac* of the axis
    height, leaving headroom for the legend."""
    import math
    lo, hi = ax.get_ylim()
    if lo <= 0 or hi <= 0:
        return
    log_lo, log_hi = math.log10(lo), math.log10(hi)
    ax.set_ylim(lo, 10 ** (log_lo + (log_hi - log_lo) / frac))


def extend_linear_top(ax, frac=0.75):
    """Linear counterpart of extend_log_top(): raise the y upper limit so the tallest
    entry fills only *frac* of the axis height.

    Set the limits tight to the data first -- this works from the CURRENT ylim, so it
    compounds with matplotlib's own autoscale margin if that is left in place."""
    lo, hi = ax.get_ylim()
    if hi <= lo:
        return
    ax.set_ylim(lo, lo + (hi - lo) / frac)
