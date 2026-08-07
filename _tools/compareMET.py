#!/usr/bin/env python3
"""Compare PuppiMET from QCD MC vs Parking data, both from 2024__v2_withPuppyMET.

Two QCD backgrounds are drawn as separate curves: the pT-hat binned MuEnriched stack
(cross-section weighted) and InclusiveDileptonMinBias (--minbias-frac of its files,
default 5%, drawn at random with a fixed seed). They are ALTERNATIVE estimates of the same
background and must never be summed. Every curve is normalised to unit area, so no cross
section is needed for MinBias.

Run after sourcing setup.sh:
    python _tools/MET_studies/compareMET.py [--output path.pdf] [--bins N] [--xmax GeV]
                                            [--max-qcd-files N]
                                            [--minbias-frac F] [--no-minbias]
"""

import argparse
import os
import random
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import goldenjson as gj

# Golden-JSON mask, set in main(). CERT is None when disabled or unavailable, in which
# case every data event is kept. MC is never masked.
CERT = None
GCOUNT = gj.Counter()

XRD_SERVER  = "root://gfe02.grid.hep.ph.ic.ac.uk/"
BASE        = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024__v2_withPuppyMET"
QCD_BASE    = BASE
DATA_BASE   = BASE

# The MinBias QCD alternative: InclusiveDileptonMinBias with the DoubleMuOS43 generator
# filter, processed by Prijith (2026-07-30). A full path, not a directory under BASE: it
# lives in a different user's dCache area, and it is a DIFFERENT production from
# 2024__v2_withPuppyMET -- it carries PuppiMET_pt/phi and the Run-3 MET Flags, which is
# all this script needs, but it is not the v2 reprocessing of the same events.
MINBIAS_DIR   = ("/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/ppradeep/samples/Parking/Run3/"
                 "Nanotronv14/InclusiveDileptonMinBias_Fil-DoubleMuOS43_TuneCP5Plus_"
                 "13p6TeV_pythia8/2024WithMET/260730_143555")
MINBIAS_LABEL = "MinBias MC PuppiMET"
MINBIAS_COLOR = "darkorange"
MINBIAS_FRAC  = 0.05      # fraction of the MinBias files (--minbias-frac)
MINBIAS_SEED  = 20260806

SIG_BASE       = BASE
SIGNAL_SAMPLES = [
    (f"{SIG_BASE}/GluGluHToDarkShowers-ScenarioA_Par-ctau-10-mA-1p00-mpi-10_TuneCP5_13p6TeV_powheg-pythia8",
     r"Signal $c\tau$=10, $m_A$=1, $m_\pi$=10"),
    (f"{SIG_BASE}/GluGluHToDarkShowers-ScenarioA_Par-ctau-1p0-mA-1p00-mpi-10_TuneCP5_13p6TeV_powheg-pythia8",
     r"Signal $c\tau$=1, $m_A$=1, $m_\pi$=10"),
]
SIG_COLORS = ["forestgreen", "darkorchid"]

QCD_BRANCHES  = ["PuppiMET_pt", "PuppiMET_phi"]
DATA_BRANCHES = ["PuppiMET_pt", "PuppiMET_phi"]
TREE_NAME     = "Events"

# Cross-sections (pb) for QCD MuEnriched PT-hat bins at 13.6 TeV.
# Keys match the PT range extracted from the directory name.
QCD_XS = {
    "15to20":    2799000,
    "20to30":    2526000,
    "30to50":    1362000,
    "50to80":     376600,
    "80to120":     88930,
    "120to170":    21230,
    "170to300":     7055,
    "300to470":      619,
    "470to600":    59.24,
    "600to800":    18.21,
    "800to1000":   3.275,
    "1000":         1.078,
}

# setup.sh sets X509_USER_PROXY to a stale copy — override in-process so both
# uproot's XRootD reads and xrdfs subprocesses use the fresh system proxy.
os.environ["X509_USER_PROXY"] = f"/tmp/x509up_u{os.getuid()}"
_XRDFS_ENV  = os.environ


def log(msg, **kwargs):
    print(msg, flush=True, **kwargs)


# Marker convention, shared with compareDeltaR.py / compareBDTvars.py: data is a small
# SOLID black square, the two background estimates (pT-hat QCD and MinBias) are
# WHITE-filled circles. Solid = measured, open = simulated, so the two kinds of curve are
# told apart by shape and fill rather than by colour alone. White fill rather than
# unfilled, so a marker masks whatever curve passes underneath it.
DATA_MARKER, DATA_MARKER_SIZE = "s", 3.5
BKG_MARKER, BKG_MARKER_SIZE = "o", 4.0
MARKER_EDGE = 1.0


def marker_kw(kind, colour):
    """Marker styling for a curve of *kind* in {"data", "bkg", None}. {} for anything else
    (signal), which stays unmarked so a page of many signal points does not become
    texture."""
    if kind == "data":
        return dict(marker=DATA_MARKER, markersize=DATA_MARKER_SIZE,
                    markerfacecolor=colour, markeredgecolor=colour,
                    markeredgewidth=MARKER_EDGE)
    if kind == "bkg":
        return dict(marker=BKG_MARKER, markersize=BKG_MARKER_SIZE,
                    markerfacecolor="white", markeredgecolor=colour,
                    markeredgewidth=MARKER_EDGE)
    return {}


def get_qcd_xs(dirname):
    """Return cross-section (pb) for a QCD PT-bin directory, or None if unrecognised."""
    import re
    m = re.search(r"QCD_Bin-PT-([^_]+)", dirname)
    if not m:
        return None
    return QCD_XS.get(m.group(1))


# Run-3 MET filters (year > 2018).
# Required: must be present in the tree; missing branch raises a warning and fails all events.
_MET_FLAGS_REQUIRED = [
    "Flag_goodVertices",
    "Flag_globalSuperTightHalo2016Filter",
    "Flag_EcalDeadCellTriggerPrimitiveFilter",
    "Flag_BadPFMuonFilter",
    "Flag_BadPFMuonDzFilter",
    "Flag_hfNoisyHitsFilter",
]
# Optional: applied when present, treated as passing when absent (mirrors MetFilterProducer).
_MET_FLAG_OPTIONAL  = "Flag_ecalBadCalibFilter"
_MET_FLAG_DATA_ONLY = "Flag_eeBadScFilter"


def met_filter_mask(tree, is_mc, apply=True):
    """Boolean mask of events passing Run-3 MET filters."""
    if not apply:
        return np.ones(tree.num_entries, dtype=bool)
    keys  = set(tree.keys())
    mask  = np.ones(tree.num_entries, dtype=bool)
    for flag in _MET_FLAGS_REQUIRED:
        if flag not in keys:
            log(f"  [warn] required MET flag '{flag}' missing from tree — failing all events",
                file=sys.stderr)
            return np.zeros(tree.num_entries, dtype=bool)
        mask &= tree[flag].array(library="np").astype(bool)
    if _MET_FLAG_OPTIONAL in keys:
        mask &= tree[_MET_FLAG_OPTIONAL].array(library="np").astype(bool)
    if not is_mc and _MET_FLAG_DATA_ONLY in keys:
        mask &= tree[_MET_FLAG_DATA_ONLY].array(library="np").astype(bool)
    return mask


def xrdfs_ls(path, server=None):
    """Return list of (full_path, is_dir) for entries in *path* via xrdfs."""
    srv = server or XRD_SERVER
    result = subprocess.run(
        ["xrdfs", srv, "ls", "-l", path],
        capture_output=True, text=True, env=_XRDFS_ENV,
    )
    entries = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # xrdfs -l output: flags  size  date  time  full_path
        parts  = line.split()
        flags  = parts[0]
        name   = parts[-1]
        is_dir = flags.startswith("d")
        entries.append((name, is_dir))
    return entries


def list_root_files(directory, indent="  ", cap=None, server=None):
    """Recursively collect XRootD URLs for every .root file under *directory*.
    Stops early once *cap* files have been collected (None = no limit)."""
    srv = server or XRD_SERVER
    entries = xrdfs_ls(directory, server=srv)
    files = []
    for path, is_dir in entries:
        if cap and len(files) >= cap:
            break
        if is_dir:
            log(f"{indent}-> {path.split('/')[-1]}/")
            remaining = (cap - len(files)) if cap else None
            files.extend(list_root_files(path, indent + "  ", cap=remaining, server=srv))
        elif path.endswith(".root"):
            files.append(srv + path)
    log(f"{indent}   {len(files)} .root files found under {directory.split('/')[-1]}")
    return files


def read_branches(urls, branches, label, is_mc=False, apply_met=True):
    """Read *branches* from every URL; return a dict {branch: flat numpy array}."""
    import uproot
    accum = {b: [] for b in branches}
    n = len(urls)
    for i, url in enumerate(urls, 1):
        fname = url.split("/")[-1]
        log(f"  [{i}/{n}] {fname}")
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                mask = met_filter_mask(tree, is_mc, apply=apply_met)
                # certified lumisections -- DATA only
                if not is_mc and CERT is not None:
                    r = tree["run"].array(library="np")
                    l = tree["luminosityBlock"].array(library="np")
                    mask &= GCOUNT.update(gj.mask(r, l, CERT))
                nevt = int(mask.sum())
                for b in branches:
                    accum[b].append(tree[b].array(library="np")[mask])
            suffix = " (after MET filters)" if apply_met else " (no MET filters)"
            log(f"         -> {nevt:,} events{suffix}")
        except Exception as exc:
            log(f"  [warn] skipping {fname}: {exc}", file=sys.stderr)
    return {b: (np.concatenate(arrs) if arrs else np.array([], dtype=np.float32))
            for b, arrs in accum.items()}


def main():
    parser = argparse.ArgumentParser(
        description="Plot PuppiMET: QCD MC vs Parking data, both from v2_withPuppyMET")
    parser.add_argument("--output", default="compareMET.pdf",
                        help="Output file (default: compareMET.pdf)")
    parser.add_argument("--bins", type=int, default=60,
                        help="Number of histogram bins (default: 60)")
    parser.add_argument("--xmax", type=float, default=300,
                        help="Upper MET axis limit in GeV (default: 300)")
    parser.add_argument("--max-qcd-files", type=int, default=10,
                        help="Cap QCD files per PT bin (default: 10)")
    parser.add_argument("--minbias-frac", type=float, default=MINBIAS_FRAC,
                        help=f"Fraction of MinBias files, drawn at random with a fixed "
                             f"seed (default: {MINBIAS_FRAC} = 5%%)")
    parser.add_argument("--minbias-seed", type=int, default=MINBIAS_SEED,
                        help=f"Seed for the MinBias file draw (default: {MINBIAS_SEED})")
    parser.add_argument("--no-minbias", action="store_true",
                        help="Skip the MinBias sample entirely")
    parser.add_argument("--test", action="store_true",
                        help="Quick check: read 1 file per sample (QCD, data, each signal)")
    parser.add_argument("--no-met-filter", action="store_true",
                        help="Skip MET filters — plot inclusive distributions")
    gj.add_args(parser)
    args = parser.parse_args()
    global CERT
    CERT = gj.from_args(args, log)

    # --- QCD files (all PT bins, from v1 base) ---
    log(f"Connecting to {XRD_SERVER} ...")
    log(f"Listing QCD base {QCD_BASE} ...")
    qcd_top = xrdfs_ls(QCD_BASE)
    if not qcd_top:
        log(f"ERROR: cannot list {QCD_BASE} — check proxy / server", file=sys.stderr)
        sys.exit(1)
    log(f"  {len(qcd_top)} top-level entries found")

    qcd_dirs = sorted(e for e in qcd_top if e[0].split("/")[-1].startswith("QCD_Bin-PT-"))
    log(f"\n[QCD] Scanning {len(qcd_dirs)} PT-bin directories (xs-weighted)...")
    file_cap = 1 if args.test else args.max_qcd_files

    # --- Parking data files (v2 withPuppyMET, all files) ---
    log(f"\nListing data base {DATA_BASE} ...")
    data_top = xrdfs_ls(DATA_BASE)
    if not data_top:
        log(f"ERROR: cannot list {DATA_BASE} — check proxy / server", file=sys.stderr)
        sys.exit(1)
    log(f"  {len(data_top)} top-level entries found")

    data_dirs = sorted(e for e in data_top if e[0].split("/")[-1].startswith("Parking"))
    log(f"\n[Data] Scanning {len(data_dirs)} Parking directories...")
    data_files = []
    for path, _ in data_dirs:
        log(f"  {path.split('/')[-1]}")
        before = len(data_files)
        data_files.extend(list_root_files(path, cap=1 if args.test else None))
        log(f"    subtotal: {len(data_files) - before} files")
        if args.test and data_files:
            break
    log(f"  => {len(data_files)} Parking files total ({len(data_dirs)} streams)")

    # --- read QCD bin by bin with cross-section weighting ---
    apply_met = not args.no_met_filter
    qcd_parts = {b: [] for b in QCD_BRANCHES}
    qcd_w_parts = []
    total_qcd_files = 0
    for path, _ in qcd_dirs:
        bin_name = path.split("/")[-1]
        xs = get_qcd_xs(bin_name)
        if xs is None:
            log(f"  [warn] no cross-section for {bin_name} — skipping", file=sys.stderr)
            continue
        log(f"  {bin_name}  (xs={xs} pb)")
        bin_files = list_root_files(path, cap=file_cap)
        total_qcd_files += len(bin_files)
        if not bin_files:
            continue
        bin_data = read_branches(bin_files, QCD_BRANCHES, bin_name, is_mc=True, apply_met=apply_met)
        n_bin = len(bin_data[QCD_BRANCHES[0]])
        if n_bin == 0:
            continue
        w = xs / n_bin
        log(f"    {n_bin:,} events, weight = {w:.4e}")
        for b in QCD_BRANCHES:
            qcd_parts[b].append(bin_data[b])
        qcd_w_parts.append(np.full(n_bin, w))
        if args.test and qcd_w_parts:
            break
    qcd = {b: np.concatenate(qcd_parts[b]) if qcd_parts[b] else np.array([], dtype=np.float32)
           for b in QCD_BRANCHES}
    qcd["weight"] = np.concatenate(qcd_w_parts) if qcd_w_parts else np.array([])
    log(f"  => {len(qcd['PuppiMET_pt']):,} QCD events total from {total_qcd_files} files")

    # --- MinBias: a seeded RANDOM fraction of the files ---
    # Not the first N: the sample is split over 0000/0001/0002 production subdirectories,
    # so the head of the listing is one subdirectory -- a subset of the JOBS rather than a
    # subset of the sample.
    minbias = None
    if not args.no_minbias:
        log(f"\n[MinBias] Listing {MINBIAS_DIR.split('/')[-3]} ...")
        all_mb = list_root_files(MINBIAS_DIR)
        if not all_mb:
            log(f"ERROR: no .root files under {MINBIAS_DIR} — check the path / proxy "
                f"(or pass --no-minbias)", file=sys.stderr)
            sys.exit(1)
        n_mb = 1 if args.test else max(1, round(args.minbias_frac * len(all_mb)))
        mb_files = (random.Random(args.minbias_seed).sample(all_mb, n_mb)
                    if n_mb < len(all_mb) else all_mb)
        log(f"  => {len(mb_files)} of {len(all_mb)} MinBias files "
            f"({100 * len(mb_files) / len(all_mb):.2f}%, seed {args.minbias_seed})")
        mb_data = read_branches(mb_files, QCD_BRANCHES, "MinBias", is_mc=True,
                                apply_met=apply_met)
        log(f"  => {len(mb_data['PuppiMET_pt']):,} MinBias events")
        minbias = (mb_data, len(mb_files), len(all_mb))

    log(f"\n[Data] Reading {DATA_BRANCHES} from {len(data_files)} files...")
    data = read_branches(data_files, DATA_BRANCHES, "Data", is_mc=False, apply_met=apply_met)
    log(f"  => {len(data['PuppiMET_pt']):,} data events total")

    # --- Signal files ---
    signals = []
    for sig_path, sig_label in SIGNAL_SAMPLES:
        short = sig_path.split("/")[-1]
        log(f"\n[Signal] Listing {short} ...")
        sig_files = list_root_files(sig_path, cap=1 if args.test else None)
        log(f"  => {len(sig_files)} signal files")
        log(f"[Signal] Reading PuppiMET branches ...")
        sig_data = read_branches(sig_files, ["PuppiMET_pt", "PuppiMET_phi"], "Signal", is_mc=True, apply_met=apply_met)
        log(f"  => {len(sig_data['PuppiMET_pt']):,} signal events")
        signals.append((sig_data, sig_label, len(sig_files)))

    n_qcd  = len(qcd["PuppiMET_pt"])
    n_data = len(data["PuppiMET_pt"])

    qcd_detail = f"{file_cap} files/bin" if file_cap else "all files"

    bins_pt  = np.linspace(0, args.xmax, args.bins + 1)
    bins_phi = np.linspace(-np.pi, np.pi, args.bins + 1)

    def plot_with_errors(ax, values, bins, color, label, weights=None, kind=None):
        counts, edges = np.histogram(values, bins=bins, weights=weights)
        # Error: sqrt(sum(w^2)) per bin; for unweighted this reduces to sqrt(N)
        w2 = weights ** 2 if weights is not None else None
        counts_w2, _ = np.histogram(values, bins=bins, weights=w2)
        widths  = np.diff(edges)
        total   = counts.sum()
        norm    = counts / (total * widths) if total > 0 else counts * 0.0
        err     = np.sqrt(counts_w2) / (total * widths) if total > 0 else counts * 0.0
        centres = 0.5 * (edges[:-1] + edges[1:])
        ax.plot(centres, norm, drawstyle="steps-mid", color=color, linewidth=2,
                label=label, **marker_kw(kind, color))
        ax.fill_between(centres, norm - err, norm + err,
                        step="mid", alpha=0.25, color=color)

    def make_page(pt_cut):
        # All cuts are on PuppiMET_pt; use `is not None` so pt_cut=0 would also work
        mask_q = qcd["PuppiMET_pt"]  > pt_cut if pt_cut is not None else slice(None)
        mask_d = data["PuppiMET_pt"] > pt_cut if pt_cut is not None else slice(None)
        q_pt  = qcd["PuppiMET_pt"][mask_q];   q_phi  = qcd["PuppiMET_phi"][mask_q]
        q_w   = qcd["weight"][mask_q]
        d_pt  = data["PuppiMET_pt"][mask_d];  d_phi  = data["PuppiMET_phi"][mask_d]

        cut_str    = rf"PuppiMET $p_T > {pt_cut}$ GeV" if pt_cut is not None else "inclusive"
        qcd_label  = (f"QCD MC PuppiMET, $p_T$ bins  ({len(q_pt):,} events, "
                      f"{qcd_detail}, xs-weighted)")
        data_label = f"Data PuppiMET  ({len(d_pt):,} events, {len(data_files)} files)"

        fig, (ax_pt, ax_phi) = plt.subplots(1, 2, figsize=(14, 6))

        plot_with_errors(ax_pt, q_pt, bins_pt, "royalblue", qcd_label, weights=q_w, kind="bkg")
        plot_with_errors(ax_phi, q_phi, bins_phi, "royalblue", qcd_label, weights=q_w, kind="bkg")

        # MinBias: unweighted (one process, no pT-hat stack to reweight) and unit-area
        # normalised like every other curve, so it needs no cross section to sit on the
        # same axes as the xs-weighted QCD stack. It is an alternative to that stack,
        # not an addition to it.
        if minbias is not None:
            mb_data, mb_read, mb_avail = minbias
            mask_m = (mb_data["PuppiMET_pt"] > pt_cut if pt_cut is not None
                      else slice(None))
            m_pt, m_phi = mb_data["PuppiMET_pt"][mask_m], mb_data["PuppiMET_phi"][mask_m]
            if len(m_pt):
                mb_label = (f"{MINBIAS_LABEL}  ({len(m_pt):,} events, "
                            f"{mb_read} of {mb_avail} files)")
                plot_with_errors(ax_pt, m_pt, bins_pt, MINBIAS_COLOR, mb_label, kind="bkg")
                plot_with_errors(ax_phi, m_phi, bins_phi, MINBIAS_COLOR, mb_label, kind="bkg")
            else:
                log("  [warn] MinBias: 0 events after cut — skipping", file=sys.stderr)

        plot_with_errors(ax_pt, d_pt, bins_pt, "tomato",    data_label, kind="data")
        plot_with_errors(ax_phi, d_phi, bins_phi, "tomato",    data_label, kind="data")

        for (sig_data, sig_label_base, sig_nfiles), color in zip(signals, SIG_COLORS):
            # cut on PuppiMET_pt, consistent with QCD and data masks above
            mask_s = sig_data["PuppiMET_pt"] > pt_cut if pt_cut is not None else slice(None)
            s_pt   = sig_data["PuppiMET_pt"][mask_s]
            s_phi  = sig_data["PuppiMET_phi"][mask_s]
            if len(s_pt) == 0:
                log(f"  [warn] {sig_label_base}: 0 events after cut — skipping", file=sys.stderr)
                continue
            s_label = f"{sig_label_base}  ({len(s_pt):,} events, {sig_nfiles} files)"
            plot_with_errors(ax_pt,  s_pt,  bins_pt,  color, s_label)
            plot_with_errors(ax_phi, s_phi, bins_phi, color, s_label)

        ax_pt.set_xlabel(r"PuppiMET $p_T$ [GeV]", fontsize=13)
        ax_pt.set_ylabel("Normalised events / bin", fontsize=13)
        ax_pt.set_title(rf"PuppiMET $p_T$: QCD MC vs Data (v2)  [{cut_str}]", fontsize=13)
        ax_pt.set_yscale("log")
        ax_pt.set_xlim(0, args.xmax)
        ax_pt.legend(fontsize=10)

        ax_phi.set_xlabel(r"PuppiMET $\phi$ [rad]", fontsize=13)
        ax_phi.set_ylabel("Normalised events / bin", fontsize=13)
        ax_phi.set_title(rf"PuppiMET $\phi$: QCD MC vs Data (v2)  [{cut_str}]", fontsize=13)
        ax_phi.set_xlim(-np.pi, np.pi)
        ax_phi.legend(fontsize=10)

        fig.suptitle(f"PuppiMET comparison: QCD MC vs Parking data (v2 withPuppyMET)  —  {cut_str}",
                     fontsize=14)
        fig.tight_layout()
        return fig

    # --- save 3-page PDF ---
    with PdfPages(args.output) as pdf:
        for pt_cut in [None, 30, 50]:
            fig = make_page(pt_cut)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
