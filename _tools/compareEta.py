#!/usr/bin/env python3
"""Trigger-matching efficiency vs |eta|, one page per trigger -- signal only.

Purpose: settle what the correct |eta| acceptance of each 2024 BParking path actually is,
so the ~108 "#TODO adjust thresholds better (?)" comments in modules/muon_selection.py can
be resolved with a measurement instead of an assumption. The module currently uses
|eta| < 0.8 everywhere (the BMTF/L1HP barrel edge, ~0.83), while _tools/compareDeltaR.py
used to use 1.2. This plots where the efficiency actually falls off.

Method, per trigger T:
    denominator  MuonBPark muons with looseId, pt > (T's threshold), and |sip3d| > 6 when
                 T's name contains IP6 -- i.e. every part of T's offline selection EXCEPT
                 the |eta| cut -- in events where the HLT path T fired
    numerator    those muons that are also matched to T, via the per-muon branch
                 MuonBPark_fired_HLT_<T>
    efficiency   numerator / denominator, binned in |eta|, with binomial errors

Using MuonBPark_fired_HLT_<T> makes this a real trigger-object matching efficiency rather
than a re-emulation of the trigger, which is the whole point: an emulation would bake in
the |eta| assumption we are trying to measure.

No data, no QCD -- just a couple of Scenario A points (the acceptance is a detector/menu
property, so signal is enough and it runs in minutes).

Note on the non-IP6 paths: modules/muon_selection.py applies |sip3d| > 6 to ALL of these,
including paths whose names carry no "IP6" (e.g. HLT_Mu0_Barrel_L1HP11). That looks like
an over-cut. --sip-all reproduces the module's behaviour so the two can be compared; the
default follows the path names.

Run after sourcing setup.sh:
    python3 _tools/compareEta.py [--output path.pdf] [--n-signal N] [--sip-all] [--test]
"""

import argparse
import os
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import cmsstyle as cms
import goldenjson as gj
# Golden-JSON mask, set in main(). CERT is None when disabled or unavailable, in which
# case every data event is kept. MC is never masked.
CERT = None
GCOUNT = gj.Counter()


XRD_SERVER = "root://gfe02.grid.hep.ph.ic.ac.uk/"
BASE = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024"

TREE_NAME = "Events"
N_SIGNAL_FILES = 20          # per point; plenty for an acceptance curve


def _sdir(dirname):
    return f"{BASE}/{dirname}_TuneCP5_13p6TeV_powheg-pythia8"


# A couple of Scenario A points, both ctau = 10 mm. The |eta| acceptance is a property of
# the menu, not of the signal model, so two points are enough -- they mainly serve as a
# consistency check on each other.
SIGNAL_POINTS = [
    {"tag": r"scA $m_\pi$=10, $m_A$=3.33",
     "dir": _sdir("GluGluHToDarkShowers-ScenarioA_Par-ctau-10-mA-3p33-mpi-10"),
     "color": "royalblue"},
    {"tag": r"scA $m_\pi$=4, $m_A$=0.40",
     "dir": _sdir("GluGluHToDarkShowers-ScenarioA_Par-ctau-10-mA-0p40-mpi-4"),
     "color": "darkorange"},
]

# (HLT path, offline pt threshold, does the path require |sip3d| > 6)
#
# pt thresholds follow modules/muon_selection.py: the HLT MuN paths use N, and the
# HLT_Mu0_Barrel_L1HPn paths use the pt implied by their L1 seed (L1HP11 -> 10, L1HP10 -> 9,
# ... L1HP6 -> 5), with bare HLT_Mu0_Barrel unconstrained. The IP6 flag follows the path
# NAME -- "IP6" is the |sip3d| > 6 requirement.
TRIGGERS = [
    ("HLT_Mu10_Barrel_L1HP11_IP6",      10.0, True),
    ("HLT_Mu9_Barrel_L1HP10_IP6",        9.0, True),
    ("HLT_Mu8_Barrel_L1HP9_IP6",         8.0, True),
    ("HLT_Mu7_Barrel_L1HP8_IP6",         7.0, True),
    ("HLT_Mu6_Barrel_L1HP7_IP6",         6.0, True),
    ("HLT_Mu0_Barrel_L1HP6_IP6",         5.0, True),
    ("HLT_Mu0_Barrel_L1HP11",           10.0, False),
    ("HLT_Mu0_Barrel_L1HP10",            9.0, False),
    ("HLT_Mu0_Barrel_L1HP9",             8.0, False),
    ("HLT_Mu0_Barrel_L1HP8",             7.0, False),
    ("HLT_Mu0_Barrel_L1HP7",             6.0, False),
    ("HLT_Mu0_Barrel_L1HP6",             5.0, False),
    ("HLT_Mu0_Barrel",                   0.0, False),
    ("HLT_DoubleMu4_3_LowMass",          3.0, False),
    ("HLT_DoubleMu4_LowMass_Displaced",  4.0, False),
]

MUON_BRANCHES = ["MuonBPark_pt", "MuonBPark_eta", "MuonBPark_sip3d", "MuonBPark_looseId"]

ETA_BINS = np.linspace(0.0, 2.5, 51)       # 0.05-wide bins; the interesting edge is ~0.8
ETA_CENTRES = 0.5 * (ETA_BINS[1:] + ETA_BINS[:-1])

SIP3D_CUT = 6.0

# (position, linestyle). The dashed pair is the single-muon question this study settled:
# 0.8 (the BMTF/L1HP barrel edge used by modules/muon_selection.py) vs the 1.2 the _tools
# scripts used to carry. The dotted 2.4 is the L1 muon-system limit, and is the relevant
# boundary for the double-muon paths, whose seeds include several with no 'er' eta
# restriction -- so it is drawn only on those.
# One reference line per page, and only the one that applies to that trigger: 0.8 is the
# BMTF/L1HP barrel edge the single-muon paths live inside, 2.4 is the L1 muon-system limit
# relevant to the double-muon seeds. The old 1.2 line was the value the _tools scripts used
# to carry before this study measured the acceptance, and drawing it alongside suggested a
# threshold that is not used anywhere.
SINGLEMU_REF_LINE = (0.8, "--")
DOUBLEMU_REF_LINE = (2.4, ":")


def ref_lines_for(trigger):
    return [DOUBLEMU_REF_LINE] if "DoubleMu" in trigger else [SINGLEMU_REF_LINE]


def legend_loc_for(trigger):
    """Single-muon efficiency dies above |eta| ~ 0.9, so the bottom-left is where the
    curve is and the top-right is empty. The double-muon curves are flat all the way
    across, leaving the bottom-left free."""
    return "lower left" if "DoubleMu" in trigger else "upper right"

_env_proxy = os.environ.get("X509_USER_PROXY", "")
if not (_env_proxy and os.path.exists(_env_proxy)):
    os.environ["X509_USER_PROXY"] = f"/tmp/x509up_u{os.getuid()}"
_XRDFS_ENV = os.environ


def log(msg, **kwargs):
    print(msg, flush=True, **kwargs)


# ----------------------------------------------------------------------------
# file discovery (same approach as compareDeltaR.py)
# ----------------------------------------------------------------------------
def xrdfs_ls(path, server=None):
    srv = server or XRD_SERVER
    result = subprocess.run(["xrdfs", srv, "ls", "-l", path],
                            capture_output=True, text=True, env=_XRDFS_ENV)
    # A failed listing must not look like an empty directory -- see compareDeltaR.py
    if result.returncode != 0:
        raise RuntimeError(
            f"xrdfs ls failed for {srv}{path} (rc={result.returncode}). "
            f"Check X509_USER_PROXY and X509_CERT_DIR. stderr: {result.stderr.strip()}")
    entries = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        entries.append((parts[-1], parts[0].startswith("d")))
    return entries


def list_root_files(directory, indent="  ", server=None):
    srv = server or XRD_SERVER
    files = []
    for path, is_dir in xrdfs_ls(directory, server=srv):
        if is_dir:
            files.extend(list_root_files(path, indent + "  ", server=srv))
        elif path.endswith(".root"):
            files.append(srv + path)
    log(f"{indent}   {len(files)} .root files under {directory.split('/')[-1]}")
    return files


# ----------------------------------------------------------------------------
# reading -> per-trigger (numerator, denominator) |eta| histograms
# ----------------------------------------------------------------------------
def accumulate(urls, label, sip_all=False):
    """{trigger: {"num": counts, "den": counts}} over all *urls*, binned in |eta|."""
    import uproot
    import awkward as ak

    acc = {t: {"num": np.zeros(len(ETA_BINS) - 1), "den": np.zeros(len(ETA_BINS) - 1)}
           for t, _, _ in TRIGGERS}
    n = len(urls)
    for i, url in enumerate(urls, 1):
        fname = url.split("/")[-1]
        log(f"  [{i}/{n}] {fname}")
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                keys = set(tree.keys())
                missing = [b for b in MUON_BRANCHES if b not in keys]
                if missing:
                    log(f"  [warn] {fname}: missing {missing} -- skipping", file=sys.stderr)
                    continue
                need = list(MUON_BRANCHES)
                for t, _, _ in TRIGGERS:
                    matched = f"MuonBPark_fired_{t}"
                    if t in keys:
                        need.append(t)
                    if matched in keys:
                        need.append(matched)
                a = tree.arrays(need, library="ak")

                pt = a["MuonBPark_pt"]
                aeta = np.abs(a["MuonBPark_eta"])
                sip = np.abs(a["MuonBPark_sip3d"])
                loose = a["MuonBPark_looseId"] == 1

                for t, pt_cut, needs_ip6 in TRIGGERS:
                    matched = f"MuonBPark_fired_{t}"
                    if t not in keys or matched not in keys:
                        if i == 1:
                            log(f"  [warn] {label}: {t} or its per-muon flag absent "
                                f"-- page will be empty", file=sys.stderr)
                        continue
                    fired_evt = a[t] == 1
                    # denominator: everything for this trigger EXCEPT the |eta| cut
                    den = loose & (pt > pt_cut)
                    if needs_ip6 or sip_all:
                        den = den & (sip > SIP3D_CUT)
                    den = den & fired_evt          # broadcasts the event-level flag
                    num = den & (a[matched] == 1)

                    for key, m in (("den", den), ("num", num)):
                        vals = ak.to_numpy(ak.flatten(aeta[m]))
                        if vals.size:
                            acc[t][key] += np.histogram(vals, bins=ETA_BINS)[0]
        except Exception as exc:
            log(f"  [warn] skipping {fname}: {exc}", file=sys.stderr)
    return acc


def efficiency(num, den):
    """Efficiency and binomial (Wald) error, NaN where the denominator is empty."""
    with np.errstate(divide="ignore", invalid="ignore"):
        eff = np.where(den > 0, num / den, np.nan)
        err = np.where(den > 0, np.sqrt(np.clip(eff * (1 - eff), 0, None) / np.maximum(den, 1)), np.nan)
    return eff, err


# ----------------------------------------------------------------------------
# DATA: one panel per parking stream, one curve per epoch
# ----------------------------------------------------------------------------
# Same layout as _tools/parkingMET_per_epoch.py -- the acceptance can move with the menu
# during the year, and a per-stream x per-epoch grid is what makes that visible.

SINGLE_STREAMS = [f"ParkingSingleMuon{i}" for i in range(12)]
DOUBLE_STREAMS = [f"ParkingDoubleMuonLowMass{i}" for i in range(8)]

# one representative path per parking stream; (trigger, pt cut, needs IP6, streams, tag)
DATA_PAGES = [
    ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0, True,  SINGLE_STREAMS, "SingleMuon"),
    ("HLT_DoubleMu4_3_LowMass",     3.0, False, DOUBLE_STREAMS, "DoubleMuonLowMass"),
]

EPOCH_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
                "#9467bd", "#8c564b", "#e377c2", "#17becf"]


def epoch_label(dirname):
    return dirname.replace("nanotron-v15_2024__from_", "").replace("-MINIv6NANOv15", "")


def collect_data(streams, trigger, pt_cut, needs_ip6, max_files, sip_all=False):
    """{stream: {epoch: (num, den)}} of |eta| histograms for one trigger, over data."""
    import uproot
    import awkward as ak

    matched = f"MuonBPark_fired_{trigger}"
    out = {}
    for si, stream in enumerate(streams, 1):
        log(f"\n  [{si}/{len(streams)}] {stream}")
        per_epoch = {}
        try:
            entries = xrdfs_ls(f"{BASE}/{stream}")
        except RuntimeError as exc:
            log(f"    [warn] {exc}", file=sys.stderr)
            out[stream] = per_epoch
            continue
        for path, is_dir in entries:
            if not is_dir:
                continue
            epoch = epoch_label(path.split("/")[-1])
            urls = []
            _collect_files(path, urls, max_files)
            if not urls:
                continue
            num = np.zeros(len(ETA_BINS) - 1)
            den = np.zeros(len(ETA_BINS) - 1)
            for url in urls:
                try:
                    with uproot.open(f"{url}:{TREE_NAME}") as tree:
                        keys = set(tree.keys())
                        if trigger not in keys or matched not in keys:
                            continue
                        if any(b not in keys for b in MUON_BRANCHES):
                            continue
                        a = tree.arrays(MUON_BRANCHES + [trigger, matched]
                                        + (gj.BRANCHES if CERT is not None else []),
                                        library="ak")
                        if CERT is not None:
                            keep = GCOUNT.update(gj.mask(
                                ak.to_numpy(a["run"]),
                                ak.to_numpy(a["luminosityBlock"]), CERT))
                            a = a[keep]
                            if len(a) == 0:
                                continue
                        d = (a["MuonBPark_looseId"] == 1) & (a["MuonBPark_pt"] > pt_cut)
                        if needs_ip6 or sip_all:
                            d = d & (np.abs(a["MuonBPark_sip3d"]) > SIP3D_CUT)
                        d = d & (a[trigger] == 1)
                        n = d & (a[matched] == 1)
                        aeta = np.abs(a["MuonBPark_eta"])
                        for key, m in (("den", d), ("num", n)):
                            v = ak.to_numpy(ak.flatten(aeta[m]))
                            if v.size:
                                h = np.histogram(v, bins=ETA_BINS)[0]
                                if key == "den":
                                    den += h
                                else:
                                    num += h
                except Exception as exc:
                    log(f"    [warn] {url.split('/')[-1]}: {exc}", file=sys.stderr)
            if den.sum() > 0:
                per_epoch[epoch] = (num, den)
                log(f"    {epoch:22s} {int(den.sum()):>9,} muons")
        out[stream] = per_epoch
    return out


def _collect_files(path, out, cap):
    if len(out) >= cap:
        return
    for p, is_dir in xrdfs_ls(path):
        if len(out) >= cap:
            return
        if is_dir:
            _collect_files(p, out, cap)
        elif p.endswith(".root"):
            out.append(XRD_SERVER + p)


def plot_data_grid(data, streams, trigger, pt_cut, needs_ip6, sip_all):
    """One panel per stream, one curve per epoch -- layout as parkingMET_per_epoch.py."""
    import math
    n = len(streams)
    ncols = min(4, n)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(6.0 * ncols, 4.8 * nrows), squeeze=False)
    ax_flat = [axes[r][c] for r in range(nrows) for c in range(ncols)]
    for ax in ax_flat[n:]:
        ax.set_visible(False)

    sel = [f"pT > {pt_cut:g} GeV", "looseId"] + (["|sip3d| > 6"] if (needs_ip6 or sip_all) else [])
    panel_legend_title = ", ".join(sel) + r"  (no $|\eta|$ cut)"

    for i, stream in enumerate(streams):
        ax = ax_flat[i]
        epochs = data.get(stream, {})
        ax.set_title(stream.replace("Parking", ""), fontsize=13, fontweight="bold")
        if not epochs:
            ax.text(0.5, 0.5, "no data", transform=ax.transAxes,
                    ha="center", va="center", color="grey", fontsize=12)
            continue
        for j, epoch in enumerate(sorted(epochs)):
            num, den = epochs[epoch]
            eff, err = efficiency(num, den)
            color = EPOCH_COLORS[j % len(EPOCH_COLORS)]
            ax.stairs(np.nan_to_num(eff, nan=0.0), ETA_BINS, color=color, linewidth=1.5,
                      label=f"{epoch} ({int(den.sum()):,})")
            ax.fill_between(ETA_CENTRES, eff - err, eff + err,
                            step="mid", alpha=0.2, color=color)
        for x, ls in ref_lines_for(trigger):
            ax.axvline(x, color="grey", ls=ls, lw=0.8, alpha=0.6)
        ax.set_xlim(0, 2.5)
        ax.set_ylim(0, 1.15)
        ax.set_xlabel(r"$|\eta|$", fontsize=12)
        ax.set_ylabel("efficiency", fontsize=12)
        ax.tick_params(labelsize=10)
        # selection text lives in the legend header, not in a title -- see plot_trigger
        ax.legend(fontsize=8, loc=legend_loc_for(trigger), ncol=1,
                  title=panel_legend_title, title_fontsize=8)

    # Single-line page title only -- the selection detail is in each panel's legend header.
    # Headroom is computed in inches and converted to a figure fraction so it scales with
    # the number of rows; a fixed rect top overlapped the first row's panel titles.
    head_in = 0.65                      # inches for a 1-line, 16pt suptitle
    head = head_in / (4.8 * nrows)      # 4.8 in per panel row, see figsize above
    fig.tight_layout()
    fig.subplots_adjust(top=1.0 - head)
    fig.suptitle(f"DATA -- {trigger}   (one panel per stream, one curve per epoch)",
                 fontsize=16, y=1.0 - 0.2 * head, va="top")
    return fig


# ----------------------------------------------------------------------------
# plotting: one page per trigger
# ----------------------------------------------------------------------------
def plot_trigger(trigger, pt_cut, needs_ip6, per_point, sip_all):
    fig, ax = plt.subplots(figsize=(10, 8))
    any_entries = False
    for tag, color, acc in per_point:
        num, den = acc[trigger]["num"], acc[trigger]["den"]
        if den.sum() == 0:
            continue
        any_entries = True
        eff, err = efficiency(num, den)
        # These ARE histograms -- num and den are binned counts -- so draw them as
        # steps over the bin edges rather than as scattered points, with the binomial
        # error as a bar at each bin centre.
        ax.stairs(np.nan_to_num(eff, nan=0.0), ETA_BINS, color=color, linewidth=2,
                  label=f"{tag}  ({int(den.sum()):,} muons)")
        ax.errorbar(ETA_CENTRES, eff, yerr=err, fmt="none",
                    ecolor=color, elinewidth=1, alpha=0.75)

    for x, ls in ref_lines_for(trigger):
        ax.axvline(x, color="grey", ls=ls, lw=1, alpha=0.7)
        # inside the axes, not above them: at 1.02 these labels collided with the title
        ax.text(x, 0.93, f" {x:g}", color="grey", fontsize=11,
                ha="left", va="top", transform=ax.get_xaxis_transform())

    ax.set_xlim(0, 2.5)
    ax.set_ylim(0, 1.15)
    ax.set_xlabel(r"$|\eta|$ of the muon", fontsize=14)
    ax.set_ylabel("Trigger-matching efficiency", fontsize=14)
    cms.cms_axes(ax)

    sel = [f"$p_T >$ {pt_cut:g} GeV", "looseId"]
    if needs_ip6 or sip_all:
        sel.append(r"$|\mathrm{sip3d}| > 6$")
    # NO ax.set_title here: cms.cms_axes() owns the space above the axes for the CMS
    # label, and a multi-line title collides with it. The trigger and its selection go
    # in the legend header instead, where they sit with the curves they describe.
    legend_title = f"{trigger}\n" + ", ".join(sel) + r"  (no $|\eta|$ cut)"

    if any_entries:
        ax.legend(fontsize=11, loc=legend_loc_for(trigger), title=legend_title,
                  title_fontsize=11, **cms.LEGEND_KW)
    else:
        ax.text(0.5, 0.5, "no entries", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="crimson")
    fig.tight_layout()
    return fig


def main():
    parser = argparse.ArgumentParser(description="trigger-matching efficiency vs |eta|")
    parser.add_argument("--output", default="compareEta.pdf",
                        help="Output PDF (default: compareEta.pdf)")
    parser.add_argument("--n-signal", type=int, default=N_SIGNAL_FILES,
                        help=f"Files per signal point, <=0 for ALL (default: {N_SIGNAL_FILES})")
    parser.add_argument("--sip-all", action="store_true",
                        help="Apply |sip3d| > 6 to every path, including the non-IP6 ones, "
                             "reproducing modules/muon_selection.py")
    parser.add_argument("--test", action="store_true",
                        help="Quick check: 1 file per signal point")
    parser.add_argument("--data-files", type=int, default=2,
                        help="files per stream x epoch for the two DATA grid pages "
                             "(default 2 -- enough to see the shape); 0 disables them")
    gj.add_args(parser)
    args = parser.parse_args()
    global CERT
    CERT = gj.from_args(args, log)

    if args.test:
        log("[TEST MODE] 1 file per signal point")
    if args.sip_all:
        log("[--sip-all] |sip3d| > 6 applied to every path (module behaviour)")

    n_sig = 1 if args.test else (args.n_signal if args.n_signal > 0 else None)

    per_point = []
    for mp in SIGNAL_POINTS:
        log(f"\n=== {mp['tag']} ===")
        all_urls = list_root_files(mp["dir"])
        if not all_urls:
            raise SystemExit(f"[error] no .root files under {mp['dir']}")
        urls = all_urls if n_sig is None else all_urls[:n_sig]
        log(f"  reading {len(urls)} of {len(all_urls)} files")
        per_point.append((mp["tag"], mp["color"], accumulate(urls, mp["tag"], args.sip_all)))

    # DATA: two extra grid pages, one per parking stream family. These do not replace the
    # MC pages -- the MC pages measure the acceptance cleanly, these show whether it moved
    # with the menu during the year.
    data_pages = []
    if args.data_files > 0:
        n_data = 1 if args.test else args.data_files
        for trigger, pt_cut, needs_ip6, streams, tag in DATA_PAGES:
            log(f"\n=== DATA {tag}: {trigger} ({n_data} file(s) per stream x epoch) ===")
            d = collect_data(streams, trigger, pt_cut, needs_ip6, n_data, args.sip_all)
            data_pages.append((d, streams, trigger, pt_cut, needs_ip6))

    log("\n=== Writing PDF ===")
    with PdfPages(args.output) as pdf:
        for trigger, pt_cut, needs_ip6 in TRIGGERS:
            pdf.savefig(plot_trigger(trigger, pt_cut, needs_ip6, per_point, args.sip_all),
                        bbox_inches="tight")
        for d, streams, trigger, pt_cut, needs_ip6 in data_pages:
            pdf.savefig(plot_data_grid(d, streams, trigger, pt_cut, needs_ip6, args.sip_all),
                        bbox_inches="tight")
        plt.close("all")
    log(f"\nSaved: {args.output} ({len(TRIGGERS)} MC pages + {len(data_pages)} DATA grid pages)")


if __name__ == "__main__":
    main()
