#!/usr/bin/env python3
"""Compare secondary-vertex charge between QCD MC, Parking data and signal.

Two QCD backgrounds are drawn, as separate curves: the pT-hat binned MuEnriched stack and
InclusiveDileptonMinBias (--minbias-frac of its files, default 5%). They are ALTERNATIVE
descriptions of the same background, never to be summed.

Two vertex collections are compared:
  * two-muon  vertices  -> muonSV  collection (charge = q(mu1)+q(mu2))
  * four-muon vertices  -> <FOURMU> collection (see FOURMU_* constants below)

Each collection gets ONE page split into four quadrants:
  top-left    : all vertices, inclusive
  top-right   : best-chi2 vertex, inclusive
  bottom-left : all vertices, events passing the trigger OR
  bottom-right: best-chi2 vertex, events passing the trigger OR
(the trigger requirement is HLT_Mu10_Barrel_L1HP11_IP6 OR HLT_DoubleMu4_3_LowMass)

=> a 2-page PDF: compareSVcharge.pdf

Run after sourcing setup.sh:
    python _tools/compareSVcharge.py [--output path.pdf] [--list-branches]

Use --list-branches to open the first reachable file and dump every branch
whose name contains 'SV' or 'charge' (handy to confirm the four-muon branch).
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

import cmsstyle as cms
import goldenjson as gj
# Golden-JSON mask, set in main(). CERT is None when disabled or unavailable, in which
# case every data event is kept. MC is never masked.
CERT = None
GCOUNT = gj.Counter()


XRD_SERVER = "root://gfe02.grid.hep.ph.ic.ac.uk/"
# NOTE: base WITHOUT the "__v2_withPuppyMET" suffix used by compareMET.py.
BASE       = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024"
QCD_BASE   = BASE
DATA_BASE  = BASE
SIG_BASE   = BASE

# The MinBias QCD alternative: InclusiveDileptonMinBias with the DoubleMuOS43 generator
# filter, processed by Prijith (2026-07-30). It sits in a different user's dCache area, so
# this is a full path and NOT a directory under BASE -- gather_files() must list it
# separately rather than picking it up from the BASE listing.
MINBIAS_DIR   = ("/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/ppradeep/samples/Parking/Run3/"
                 "Nanotronv14/InclusiveDileptonMinBias_Fil-DoubleMuOS43_TuneCP5Plus_"
                 "13p6TeV_pythia8/2024WithMET/260730_143555")
MINBIAS_LABEL = "MinBias MC"
MINBIAS_COLOR = "darkorange"

# Signal points (Scenario A). Each entry: dir, plot label, colour.
def _compact(n):
    """Short entry count for legends: 4802800 -> '4.8M', 254320 -> '254k'."""
    if n >= 1e6:
        return f"{n / 1e6:.1f}M"
    if n >= 1e3:
        return f"{n / 1e3:.0f}k"
    return str(n)


SIGNALS = [
    {
        "dir":   ("GluGluHToDarkShowers-ScenarioA_Par-ctau-1p0-mA-1p33-mpi-4"
                  "_TuneCP5_13p6TeV_powheg-pythia8"),
        "label": r"scA: $m_\pi$=4, $m_A$=1.33, $c\tau$=1",
        "color": "forestgreen",
    },
    {
        "dir":   ("GluGluHToDarkShowers-ScenarioA_Par-ctau-0p1-mA-3p33-mpi-10"
                  "_TuneCP5_13p6TeV_powheg-pythia8"),
        "label": r"scA: $m_\pi$=10, $m_A$=3.33, $c\tau$=0.1",
        "color": "darkviolet",
    },
]
for _s in SIGNALS:
    _s["path"] = f"{SIG_BASE}/{_s['dir']}"

TREE_NAME = "Events"

# --- vertex-collection branch names -------------------------------------------
# Two-muon dimuon vertices (standard muonSV collection).
TWOMU_CHARGE = "muonSV_charge"
TWOMU_CHI    = "muonSV_chi2"     # min over vertices = "best chi2"; auto-corrected below
# Four-muon vertices (fourmuonSV_ collection).
FOURMU_CHARGE = "fourmuonSV_charge"
FOURMU_CHI    = "fourmuonSV_chi2"

# Event passes if EITHER of these triggers fired (bottom row of each page).
TRIGGERS       = ["HLT_Mu10_Barrel_L1HP11_IP6", "HLT_DoubleMu4_3_LowMass"]
TRIGGERS_LABEL = " OR ".join(TRIGGERS)

# how many files to read for each kind of sample
N_QCD_FILES    = 5    # per QCD PT-hat bin
N_SIGNAL_FILES = 10   # for the single signal point
N_DATA_FILES   = 5    # per Parking dataset
MINBIAS_FRAC   = 0.05 # fraction of the MinBias files (--minbias-frac)
MINBIAS_SEED   = 20260806

# Use the proxy already in the environment if it points to a real file (setup.sh
# normally sets X509_USER_PROXY to a freshly-created proxy); otherwise fall back
# to the conventional /tmp location.
_env_proxy = os.environ.get("X509_USER_PROXY", "")
if not (_env_proxy and os.path.exists(_env_proxy)):
    os.environ["X509_USER_PROXY"] = f"/tmp/x509up_u{os.getuid()}"
_XRDFS_ENV = os.environ


def log(msg, **kwargs):
    print(msg, flush=True, **kwargs)


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
        parts  = line.split()
        flags  = parts[0]
        name   = parts[-1]
        is_dir = flags.startswith("d")
        entries.append((name, is_dir))
    return entries


def list_root_files(directory, indent="  ", cap=None, server=None):
    """Recursively collect XRootD URLs for .root files under *directory*.
    Stops once *cap* files have been collected (None = no limit)."""
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
    log(f"{indent}   {len(files)} .root files collected under {directory.split('/')[-1]}"
        + (f" (cap {cap})" if cap else ""))
    return files


def resolve_branches(keys, charge_name, chi_name, label):
    """Pick the actual charge/chi2 branch names present in *keys*.

    Returns (charge_branch, chi_branch_or_None). Tries the configured name first,
    then a few common spellings so the script survives naming differences."""
    charge = charge_name if charge_name in keys else None
    if charge is None:
        for cand in (charge_name, charge_name.replace("_charge", "Charge")):
            if cand in keys:
                charge = cand
                break
    chi = None
    for cand in (chi_name, chi_name.replace("_chi2", "_chi"),
                 chi_name.replace("_chi2", "_chi2ndof"),
                 charge_name.replace("_charge", "_chi2") if charge_name else "",
                 charge_name.replace("_charge", "_chi") if charge_name else ""):
        if cand and cand in keys:
            chi = cand
            break
    log(f"  [{label}] charge branch = {charge!r}, chi2 branch = {chi!r}")
    return charge, chi


def read_sv(urls, charge_branch, chi_branch, label, is_data=False):
    """Read a jagged charge branch, its chi2, and the trigger flags from every URL.

    Returns a dict {charge, chi, trig} of arrays concatenated over files:
      * charge : awkward jagged array (per-vertex charge)
      * chi    : awkward jagged array (per-vertex chi2) or None
      * trig   : 1-D numpy bool array (per-event: passes TRIGGERS OR) or None
    All three are aligned event-by-event."""
    import uproot
    import awkward as ak
    charge_parts, chi_parts, trig_parts = [], [], []
    n = len(urls)
    for i, url in enumerate(urls, 1):
        fname = url.split("/")[-1]
        log(f"  [{i}/{n}] {fname}")
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                keys = set(tree.keys())
                cb, kb = resolve_branches(keys, charge_branch, chi_branch, label) \
                    if i == 1 else (charge_branch, chi_branch)
                if i == 1:
                    # remember the resolved names for the remaining files
                    charge_branch, chi_branch = cb, kb
                if charge_branch is None or charge_branch not in keys:
                    log(f"  [warn] {fname}: charge branch missing — skipping", file=sys.stderr)
                    continue
                gmask = None
                if is_data and CERT is not None:
                    gmask = GCOUNT.update(gj.mask(
                        tree["run"].array(library="np"),
                        tree["luminosityBlock"].array(library="np"), CERT))
                ch = tree[charge_branch].array(library="ak")
                charge_parts.append(ch[gmask] if gmask is not None else ch)
                if chi_branch and chi_branch in keys:
                    ck = tree[chi_branch].array(library="ak")
                    chi_parts.append(ck[gmask] if gmask is not None else ck)
                # event-level trigger OR mask
                present = [t for t in TRIGGERS if t in keys]
                if i == 1:
                    missing = [t for t in TRIGGERS if t not in keys]
                    if missing:
                        log(f"  [warn] {label}: trigger(s) absent, treated as not-fired: {missing}",
                            file=sys.stderr)
                    log(f"  [{label}] trigger OR over: {present}")
                nev   = len(charge_parts[-1])
                tmask = np.zeros(nev, dtype=bool)
                for t in present:
                    tv = tree[t].array(library="np").astype(bool)
                    tmask |= (tv[gmask] if gmask is not None else tv)
                trig_parts.append(tmask)
                nv = int(ak.sum(ak.num(charge_parts[-1])))
                log(f"         -> {nev:,} events ({int(tmask.sum()):,} pass trig), {nv:,} vertices")
        except Exception as exc:
            log(f"  [warn] skipping {fname}: {exc}", file=sys.stderr)
    if not charge_parts:
        return {"charge": None, "chi": None, "trig": None}
    charge = ak.concatenate(charge_parts)
    chi    = ak.concatenate(chi_parts) if chi_parts and len(chi_parts) == len(charge_parts) else None
    trig   = np.concatenate(trig_parts) if trig_parts and len(trig_parts) == len(charge_parts) else None
    return {"charge": charge, "chi": chi, "trig": trig}


def all_charges(sv, use_trig=False):
    """Flatten every vertex charge into a 1-D numpy array (optionally trigger-gated)."""
    import awkward as ak
    charge = sv["charge"]
    if charge is None:
        return np.array([], dtype=float)
    if use_trig:
        if sv["trig"] is None:
            return np.array([], dtype=float)
        charge = charge[sv["trig"]]
    if len(charge) == 0:
        return np.array([], dtype=float)
    return ak.to_numpy(ak.flatten(charge)).astype(float)


def best_chi2_charges(sv, use_trig=False):
    """One charge per event: the vertex with the smallest chi2 (optionally trigger-gated)."""
    import awkward as ak
    charge, chi = sv["charge"], sv["chi"]
    if charge is None or chi is None:
        return np.array([], dtype=float)
    if use_trig:
        if sv["trig"] is None:
            return np.array([], dtype=float)
        charge = charge[sv["trig"]]
        chi    = chi[sv["trig"]]
    has_v = ak.num(charge) > 0
    charge = charge[has_v]
    chi    = chi[has_v]
    if len(charge) == 0:
        return np.array([], dtype=float)
    idx  = ak.argmin(chi, axis=1, keepdims=True)
    best = ak.flatten(charge[idx])
    return ak.to_numpy(best).astype(float)


def int_bins(arrays):
    """Integer-centred bin edges spanning all values, plus (lo, hi) tick range."""
    nonempty = [a for a in arrays if len(a)]
    allv = np.concatenate(nonempty) if nonempty else np.array([0.0])
    lo = int(np.floor(allv.min())) - 1
    hi = int(np.ceil(allv.max())) + 1
    return np.arange(lo - 0.5, hi + 1.5, 1.0), lo, hi


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


def plot_charge(ax, datasets, bins):
    """datasets = list of (values, color, label, kind). Normalised step histograms.

    *kind* is "data", "bkg" or None and only drives the marker -- see marker_kw()."""
    centres = 0.5 * (bins[:-1] + bins[1:])
    for values, color, label, kind in datasets:
        if len(values) == 0:
            log(f"  [warn] '{label}': 0 entries — not plotted", file=sys.stderr)
            continue
        counts, edges = np.histogram(values, bins=bins)
        total = counts.sum()
        norm  = counts / total if total > 0 else counts * 0.0
        err   = np.sqrt(counts) / total if total > 0 else counts * 0.0
        # drawstyle, not ax.stairs(): a StepPatch cannot carry markers, and steps-mid
        # draws the identical line.
        ax.plot(centres, norm, drawstyle="steps-mid", color=color, linewidth=2,
                label=label, **marker_kw(kind, color))
        ax.errorbar(centres, norm, yerr=err, fmt="none", ecolor=color, alpha=0.5)


def make_page(coll_title, qcd_sv, data_sv, sig_svs, mb_sv=None):
    """One figure for a vertex collection: 2x2 quadrants.

      top-left  : all vertices, inclusive       top-right : best-chi2, inclusive
      bottom-l  : all vertices, pass triggers    bottom-r : best-chi2, pass triggers

    *sig_svs* is a list of (sv, label, color) for each signal point.
    *mb_sv* is the MinBias sample, drawn alongside the pT-hat QCD stack as a second,
    independent background estimate; None when --no-minbias was passed.
    """
    quadrants = [
        ("all vertices — inclusive",            lambda sv: all_charges(sv, use_trig=False)),
        (r"best-$\chi^2$ vertex — inclusive",   lambda sv: best_chi2_charges(sv, use_trig=False)),
        ("all vertices — pass triggers",        lambda sv: all_charges(sv, use_trig=True)),
        (r"best-$\chi^2$ vertex — pass triggers", lambda sv: best_chi2_charges(sv, use_trig=True)),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    for ax, (sub, fn) in zip(axes.flat, quadrants):
        qv, dv = fn(qcd_sv), fn(data_sv)
        mv = fn(mb_sv) if mb_sv is not None else np.array([], dtype=float)
        svs = [(fn(sv), label, color) for sv, label, color in sig_svs]
        bins, lo, hi = int_bins([qv, dv, mv] + [v for v, _, _ in svs])
        # the Data entry also states what fraction of the data sample is included -- a
        # reminder that these plots deliberately read only a small slice
        mb_entry = ([(mv, MINBIAS_COLOR, f"{MINBIAS_LABEL} ({_compact(len(mv))})", "bkg")]
                    if len(mv) else [])
        plot_charge(ax, [
            (qv,  "royalblue",   f"QCD MC, $p_T$ bins ({_compact(len(qv))})", "bkg"),
        ] + mb_entry + [
            (dv,  "tomato",      f"Data ({_compact(len(dv))}, {100 * cms.lumi_fraction():.2g}% of data)", "data"),
        ] + [
            (v, color, f"{label} ({_compact(len(v))})", None) for v, label, color in svs
        ], bins)
        ax.set_xlabel("Vertex charge", fontsize=11)
        ax.set_ylabel("Fraction of entries", fontsize=11)
        ax.set_xticks(np.arange(lo, hi + 1))
        # this page shows real data, so: "Preliminary" (not "Simulation") + a luminosity,
        # scaled to the fraction of the sample actually read
        cms.cms_axes(ax, header=cms.lumi_header(), fontsize=11, label=cms.CMS_LABEL_DATA)
        ax.legend(fontsize=9, **cms.LEGEND_KW)
        # the quadrant's selection goes in an in-plot legend, not the plot title
        cms.info_legend(ax, [sub], fontsize=9)
    fig.suptitle(f"{coll_title}\nbottom row requires:  {TRIGGERS_LABEL}\n"
                 "each distribution is normalised to unit area", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return fig


def gather_files(args):
    """Return dict of {kind: [urls]} for qcd (per bin), data (per dataset), signal."""
    log(f"Connecting to {XRD_SERVER}")
    log(f"Listing base {BASE}")
    top = xrdfs_ls(BASE)
    if not top:
        log(f"ERROR: cannot list {BASE} — check proxy / server", file=sys.stderr)
        sys.exit(1)
    log(f"  {len(top)} top-level entries found")

    # --test: just 1 file of each type (1 QCD bin, 1 Parking dataset, signal)
    if args.test:
        log("\n[TEST MODE] reading only 1 file of each type (qcd, data, signal)")

    # QCD: first N files of every PT-hat bin (test: 1 file from the first bin only)
    qcd_dirs = sorted(e for e in top if e[0].split("/")[-1].startswith("QCD_Bin-PT-"))
    log(f"\n[QCD] {len(qcd_dirs)} PT-bin directories; taking "
        f"{1 if args.test else args.n_qcd} file(s) {'total' if args.test else 'each'}")
    qcd_files = []
    n_read, n_avail = 0, 0
    for path, _ in qcd_dirs:
        log(f"  {path.split('/')[-1]}")
        before = len(qcd_files)
        _all = list_root_files(path)
        n_avail += len(_all)
        qcd_files.extend(_all[:1 if args.test else args.n_qcd])
        n_read = len(qcd_files)
        log(f"    subtotal: {len(qcd_files) - before} files")
        if args.test and qcd_files:
            break
    log(f"  => {len(qcd_files)} QCD files total")

    # MinBias: a seeded RANDOM fraction, not the first N. The sample is split over 0000/
    # 0001/0002 production subdirectories, so the head of the listing is one subdirectory
    # -- a subset of the JOBS, which is not the same thing as a subset of the sample.
    mb_files, n_mb_avail = [], 0
    if not args.no_minbias:
        log(f"\n[MinBias] {MINBIAS_DIR.split('/')[-3]}")
        all_mb = list_root_files(MINBIAS_DIR)
        if not all_mb:
            log(f"ERROR: no .root files under {MINBIAS_DIR} — check the path / proxy "
                f"(or pass --no-minbias)", file=sys.stderr)
            sys.exit(1)
        n_mb_avail = len(all_mb)
        n_mb = 1 if args.test else max(1, round(args.minbias_frac * n_mb_avail))
        mb_files = (random.Random(args.minbias_seed).sample(all_mb, n_mb)
                    if n_mb < n_mb_avail else all_mb)
        n_avail += n_mb_avail
        log(f"  => {len(mb_files)} of {n_mb_avail} MinBias files "
            f"({100 * len(mb_files) / n_mb_avail:.2f}%, seed {args.minbias_seed})")

    # Data: first N files of every Parking dataset (test: 1 file from first dataset)
    data_dirs = sorted(e for e in top if e[0].split("/")[-1].startswith("Parking"))
    log(f"\n[Data] {len(data_dirs)} Parking datasets; taking "
        f"{1 if args.test else args.n_data} file(s) {'total' if args.test else 'each'}")
    data_files = []
    n_data_avail = 0
    for path, _ in data_dirs:
        log(f"  {path.split('/')[-1]}")
        before = len(data_files)
        _all = list_root_files(path)
        n_avail += len(_all)
        n_data_avail += len(_all)
        data_files.extend(_all[:1 if args.test else args.n_data])
        log(f"    subtotal: {len(data_files) - before} files")
        if args.test and data_files:
            break
    log(f"  => {len(data_files)} Parking files total")

    # Signal: first N files of each point (test: 1 file each)
    n_sig = 1 if args.test else args.n_signal
    sig_files = []
    for sig in SIGNALS:
        log(f"\n[Signal] {sig['dir']}; taking {n_sig} files")
        _all = list_root_files(sig["path"])
        files_i = _all[:n_sig]
        n_avail += len(_all)
        log(f"  => {len(files_i)} signal files")
        sig_files.append(files_i)

    n_read = (len(qcd_files) + len(mb_files) + len(data_files)
              + sum(len(f) for f in sig_files))
    # "Partial sample" is shown only in --test. In a full run the MC is used in its
    # entirety for its purpose, and the amount of DATA is already conveyed by the quoted
    # luminosity and the "% of data" in the legend, so the label would just be noise.
    cms.set_sample_files(n_read if args.test else n_avail, n_avail)
    # ...and, separately, how much of the DATA: the luminosity refers to the Parking
    # datasets only, so it must not be scaled by a count blended with QCD/signal MC files
    cms.set_lumi_files(len(data_files), n_data_avail)
    if cms.is_partial():
        log(f"\n  PARTIAL SAMPLE: {n_read} of {n_avail} files "
            f"({100 * cms.sample_fraction():.2f}%) -- every plot is labelled as such")
    else:
        log(f"\n  [not flagged partial] read {n_read} of {n_avail} files")
    log(f"  data: {len(data_files)} of {n_data_avail} Parking files "
        f"({100 * cms.lumi_fraction():.2f}%) -> quoted luminosity {cms.lumi_header()}")

    return {"qcd": qcd_files, "minbias": mb_files, "data": data_files,
            "signal": sig_files}


def main():
    parser = argparse.ArgumentParser(description="Compare SV charge: QCD vs data vs signal")
    parser.add_argument("--output", default="compareSVcharge.pdf",
                        help="Output PDF (default: compareSVcharge.pdf)")
    parser.add_argument("--n-qcd", type=int, default=N_QCD_FILES,
                        help=f"Files per QCD bin (default: {N_QCD_FILES})")
    parser.add_argument("--n-data", type=int, default=N_DATA_FILES,
                        help=f"Files per Parking dataset (default: {N_DATA_FILES})")
    parser.add_argument("--n-signal", type=int, default=N_SIGNAL_FILES,
                        help=f"Signal files (default: {N_SIGNAL_FILES})")
    parser.add_argument("--minbias-frac", type=float, default=MINBIAS_FRAC,
                        help=f"Fraction of MinBias files, drawn at random with a fixed "
                             f"seed (default: {MINBIAS_FRAC} = 5%%)")
    parser.add_argument("--minbias-seed", type=int, default=MINBIAS_SEED,
                        help=f"Seed for the MinBias file draw (default: {MINBIAS_SEED})")
    parser.add_argument("--no-minbias", action="store_true",
                        help="Skip the MinBias sample entirely")
    parser.add_argument("--list-branches", action="store_true",
                        help="Open the first reachable file and dump SV/charge branches, then exit")
    parser.add_argument("--test", action="store_true",
                        help="Quick check: read only 1 file of each type (qcd, data, signal)")
    gj.add_args(parser)
    args = parser.parse_args()
    global CERT
    CERT = gj.from_args(args, log)

    files = gather_files(args)

    if args.list_branches:
        import uproot
        flat_sig = [u for fl in files["signal"] for u in fl]
        probe = flat_sig or files["qcd"] or files["data"]
        if not probe:
            log("ERROR: no files found to probe", file=sys.stderr)
            sys.exit(1)
        url = probe[0]
        log(f"\n[probe] opening {url}")
        with uproot.open(f"{url}:{TREE_NAME}") as tree:
            keys = sorted(tree.keys())
            log(f"  tree has {len(keys)} branches; matching 'SV' or 'charge':")
            for k in keys:
                if "SV" in k or "charge" in k.lower():
                    log(f"    {k}")
        return

    # --- read two-muon vertices (charge, chi2, trigger flags) ---
    log("\n=== Reading TWO-muon vertices (muonSV) ===")
    log("[QCD]");    q2 = read_sv(files["qcd"],    TWOMU_CHARGE, TWOMU_CHI, "2mu")
    m2 = None
    if files["minbias"]:
        log("[MinBias]")
        m2 = read_sv(files["minbias"], TWOMU_CHARGE, TWOMU_CHI, "2mu")
    log("[Data]");   d2 = read_sv(files["data"],   TWOMU_CHARGE, TWOMU_CHI, "2mu",
                              is_data=True)
    s2 = []
    for sig, sig_files in zip(SIGNALS, files["signal"]):
        log(f"[Signal] {sig['label']}")
        s2.append((read_sv(sig_files, TWOMU_CHARGE, TWOMU_CHI, "2mu"),
                   sig["label"], sig["color"]))

    # --- read four-muon vertices ---
    log("\n=== Reading FOUR-muon vertices (fourmuonSV) ===")
    log("[QCD]");    q4 = read_sv(files["qcd"],    FOURMU_CHARGE, FOURMU_CHI, "4mu")
    m4 = None
    if files["minbias"]:
        log("[MinBias]")
        m4 = read_sv(files["minbias"], FOURMU_CHARGE, FOURMU_CHI, "4mu")
    log("[Data]");   d4 = read_sv(files["data"],   FOURMU_CHARGE, FOURMU_CHI, "4mu",
                              is_data=True)
    s4 = []
    for sig, sig_files in zip(SIGNALS, files["signal"]):
        log(f"[Signal] {sig['label']}")
        s4.append((read_sv(sig_files, FOURMU_CHARGE, FOURMU_CHI, "4mu"),
                   sig["label"], sig["color"]))

    log("\n=== Building histograms / writing PDF ===")
    with PdfPages(args.output) as pdf:
        # Page 1: two-muon vertices (4 quadrants)
        log("  page 1: two-muon vertices (4 quadrants)")
        pdf.savefig(make_page("Two-muon vertex charge (muonSV)", q2, d2, s2, mb_sv=m2),
                    bbox_inches="tight")
        # Page 2: four-muon vertices (4 quadrants)
        log("  page 2: four-muon vertices (4 quadrants)")
        pdf.savefig(make_page("Four-muon vertex charge (fourmuonSV)", q4, d4, s4, mb_sv=m4),
                    bbox_inches="tight")
        plt.close("all")
    log(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
