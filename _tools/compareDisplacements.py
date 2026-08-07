#!/usr/bin/env python3
"""muonSV transverse displacement (Lxy) per trigger case.

Every charge-neutral muonSV (muonSV_charge == 0, as required throughout the framework's
MuonSV_isNeutral selection) of a passing event contributes its muonSV_dxy -- i.e. the
displacement of the standard dimuon vertices, not of fourmuonSV objects. No four-muon /
quadv logic here; the per-category (singlev / multiv / quadv) distributions live in
_tools/compareCategories.py.

Three curves, each = a trigger AND the offline kinematic leg compatible with it
(event-level, Any over muonSVs), mirroring the per-case configs
config/chi2_nobdt_scA_2024_{Mu10,DoubleMu,Mu10orDoubleMu}.yaml:

  * Mu10     : HLT_Mu10_Barrel_L1HP11_IP6
               AND Any[(mu1pt>10 & |mu1eta|<0.8 & |sip3d1|>6) || (mu2pt>10 & ...)]
  * DoubleMu : HLT_DoubleMu4_3_LowMass
               AND Any[max(mu1pt,mu2pt)>4 & min(mu1pt,mu2pt)>3
                       & |mu1eta|<2.4 & |mu2eta|<2.4 & (|sip3d1|>6 || |sip3d2|>6)]
  * Mu10 OR DoubleMu : the union of the two cases above

The legs are the two halves of getSignalEff_noMET.C's f_kin_or, here paired with their
own trigger rather than crossed, so each curve is self-consistent with its HLT path. The
two single-trigger cases are NOT exclusive: an event firing both contributes to both
curves, so their entries sum to MORE than the OR, which counts it once.

Raw entry counts (single process, no cross-section weighting), so the curves show the
relative trigger yields directly. No pAngle requirement is applied anywhere.

Plot formatting follows the CMS conventions -- see _tools/cmsstyle.py.

Output PDF (compareDisplacements.pdf): FOUR pages, all over 0 -- XMAX cm, log y:
one (log x, linear x) pair per signal point -- Scenario A mpi=4 mA=0.40 at ctau = 1 mm
and at ctau = 100 mm.

Run after sourcing setup.sh:
    python _tools/compareDisplacements.py [--output path.pdf] [--n-signal N]
                                          [--xmax CM] [--test]

--test reads only 1 file for a quick debug pass.
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
from matplotlib.lines import Line2D

import cmsstyle as cms

XRD_SERVER = "root://gfe02.grid.hep.ph.ic.ac.uk/"
BASE       = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024"

# Every page here is signal simulation with no data, so no luminosity is quoted;
# see _tools/cmsstyle.py for the conventions.

# The muonSV signal points: Scenario A, mpi = 4 GeV, mA = 0.40 GeV, at two lifetimes.
# Each one gets its own pair of pages (log x and linear x).
SIGNALS = [
    {
        "dir":      ("GluGluHToDarkShowers-ScenarioA_Par-ctau-1p0-mA-0p40-mpi-4"
                     "_TuneCP5_13p6TeV_powheg-pythia8"),
        "label":    r"Scenario A: $m_\pi$=4 GeV, $m_A$=0.40 GeV, $c\tau$=1 mm",
        "scenario": "Scenario A",
        "mpi":      4,      # GeV
        "mA":       0.40,   # GeV
        "ctau_mm":  1,      # mm
    },
    {
        "dir":      ("GluGluHToDarkShowers-ScenarioA_Par-ctau-100-mA-0p40-mpi-4"
                     "_TuneCP5_13p6TeV_powheg-pythia8"),
        "label":    r"Scenario A: $m_\pi$=4 GeV, $m_A$=0.40 GeV, $c\tau$=100 mm",
        "scenario": "Scenario A",
        "mpi":      4,      # GeV
        "mA":       0.40,   # GeV
        "ctau_mm":  100,    # mm
    },
]
for _s in SIGNALS:
    _s["path"] = f"{BASE}/{_s['dir']}"


def _signal_lines(sig):
    """The dataset description, one line per entry, in the style of
    _tools/getSignalEff_compare.C's top-left signal-info TLegend."""
    return [sig["scenario"],
            rf"$m_{{\bar{{\pi}}}}$ = {sig['mpi']:g} GeV",
            rf"$m_{{A'}}$ = {sig['mA']:.2f} GeV",
            rf"$c\tau$ = {sig['ctau_mm']:g} mm"]

TREE_NAME = "Events"

N_SIGNAL_FILES = 40    # caps at all available
XMAX           = 100.0 # cm, upper end of the displayed Lxy range on both pages
N_RETRIES      = 3     # xrootd reads occasionally hit a transient "Internal timeout"



TRIG_MU10     = "HLT_Mu10_Barrel_L1HP11_IP6"
TRIG_DOUBLEMU = "HLT_DoubleMu4_3_LowMass"
TRIGGERS = [TRIG_MU10, TRIG_DOUBLEMU]

# the trigger cases, in plot order. "key" indexes the per-case arrays. The OR is drawn
# first and thicker so the other two sit on top of it: it is their union, so wherever one
# of them coincides with the OR it hides it, which is exactly the useful thing to see.
CASES = [
    {"key": "or",       "label": "OR (Single- + Double-muon)",
     "color": "black",     "lw": 2.4},
    {"key": "mu10",     "label": TRIG_MU10,     "color": "crimson",   "lw": 2.0},
    {"key": "doublemu", "label": TRIG_DOUBLEMU, "color": "royalblue", "lw": 2.0},
]

DXY_BRANCHES = ["muonSV_dxy", "muonSV_charge",
                "muonSV_mu1pt", "muonSV_mu1eta",
                "muonSV_mu2pt", "muonSV_mu2eta",
                # IP6 leg: muonSV_mu{1,2}index point into MuonBPark, which is where
                # sip3d lives (there is no muonSV_*sip3d branch)
                "muonSV_mu1index", "muonSV_mu2index", "MuonBPark_sip3d"]

# proxy: prefer the one from the environment (setup.sh sets X509_USER_PROXY)
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


# ----------------------------------------------------------------------------
# reading -> per-case flat muonSV_dxy arrays
# ----------------------------------------------------------------------------
def _read_one(url, label, first):
    """Read one file. Returns (dxy_by_case, nevt_by_case) for it, or None if the file has
    no muonSV branches. Raises on an I/O failure so the caller can retry."""
    import uproot
    import awkward as ak
    fname = url.split("/")[-1]
    with uproot.open(f"{url}:{TREE_NAME}") as tree:
        keys = set(tree.keys())
        if any(b not in keys for b in DXY_BRANCHES):
            log(f"  [warn] {fname}: muonSV branches missing -- skipping", file=sys.stderr)
            return None
        a = tree.arrays(DXY_BRANCHES, library="ak")
        if first:
            absent = [t for t in TRIGGERS if t not in keys]
            if absent:
                log(f"  [warn] {label}: trigger(s) absent, treated as not-fired: "
                    f"{absent}", file=sys.stderr)

        # event-level trigger decisions; a missing branch is treated as not-fired
        def trig(name):
            if name not in keys:
                return np.zeros(len(a), dtype=bool)
            return tree[name].array(library="np").astype(bool)
        t_mu10, t_dmu = trig(TRIG_MU10), trig(TRIG_DOUBLEMU)

        # Offline kinematic legs, event-level Any. Mirrors modules/muon_selection.py:
        #   Mu10 leg     pt > 10, |eta| < 0.8, |sip3d| > 6   (was |eta| < 1.2, no sip3d)
        #   DoubleMu leg pt > 4/3, |eta| < 2.4, |sip3d| > 6  (was no eta, no sip3d)
        # |eta| < 0.8 is the BMTF/L1HP barrel acceptance; "IP6" IS |sip3d| > 6.
        m1pt, m1eta = a["muonSV_mu1pt"], a["muonSV_mu1eta"]
        m2pt, m2eta = a["muonSV_mu2pt"], a["muonSV_mu2eta"]
        sip = a["MuonBPark_sip3d"]
        s1 = np.abs(sip[a["muonSV_mu1index"]])
        s2 = np.abs(sip[a["muonSV_mu2index"]])
        leg_mu10 = ((m1pt > 10) & (np.abs(m1eta) < 0.8) & (s1 > 6)) | \
                   ((m2pt > 10) & (np.abs(m2eta) < 0.8) & (s2 > 6))
        mx, mn = np.maximum(m1pt, m2pt), np.minimum(m1pt, m2pt)
        leg_dmu = ((mx > 4) & (mn > 3)
                   & (np.abs(m1eta) < 2.4) & (np.abs(m2eta) < 2.4)
                   & ((s1 > 6) | (s2 > 6)))
        k_mu10 = ak.to_numpy(ak.any(leg_mu10, axis=1))
        k_dmu  = ak.to_numpy(ak.any(leg_dmu, axis=1))

        # each case pairs a trigger with its OWN compatible offline leg; the OR is their
        # union, so an event firing both is counted once there but in both single cases
        case_mu10 = t_mu10 & k_mu10
        case_dmu  = t_dmu & k_dmu
        masks = {
            "or":       case_mu10 | case_dmu,
            "mu10":     case_mu10,
            "doublemu": case_dmu,
        }
        neutral = a["muonSV_charge"] == 0
        dxy, nevt = {}, {}
        for key, mask in masks.items():
            sel = a["muonSV_dxy"][mask][neutral[mask]]
            dxy[key]  = ak.to_numpy(ak.flatten(sel)).astype(float)
            nevt[key] = int(mask.sum())
        log(f"         -> events: OR {nevt['or']:,}, Mu10 {nevt['mu10']:,}, "
            f"DoubleMu {nevt['doublemu']:,}")
        return dxy, nevt


def read_dxy(urls, label):
    """Return (dxy_by_case, nevt_by_case, failed): for each trigger case a flat numpy array
    of muonSV_dxy over all charge-neutral muonSVs of the events passing that case, and the
    number of events passing it. Each file is retried up to N_RETRIES times (xrootd throws
    transient timeouts); *failed* lists the files that never made it, so a short read is
    reported rather than silently undercounting the sample."""
    parts = {c["key"]: [] for c in CASES}
    nevt  = {c["key"]: 0 for c in CASES}
    failed = []
    n = len(urls)
    for i, url in enumerate(urls, 1):
        fname = url.split("/")[-1]
        log(f"  [{i}/{n}] {fname}")
        for attempt in range(1, N_RETRIES + 1):
            try:
                got = _read_one(url, label, first=(i == 1))
                if got is not None:
                    fdxy, fnevt = got
                    for c in CASES:
                        parts[c["key"]].append(fdxy[c["key"]])
                        nevt[c["key"]] += fnevt[c["key"]]
                break
            except Exception as exc:
                if attempt < N_RETRIES:
                    log(f"  [warn] {fname}: attempt {attempt}/{N_RETRIES} failed ({exc}) "
                        f"-- retrying", file=sys.stderr)
                else:
                    log(f"  [ERROR] {fname}: giving up after {N_RETRIES} attempts: {exc}",
                        file=sys.stderr)
                    failed.append(fname)
    dxy = {k: (np.concatenate(v) if v else np.array([], dtype=float))
           for k, v in parts.items()}
    return dxy, nevt, failed


def _extend_log_top(ax, frac=0.75):
    """Raise the (log) y upper limit so the tallest bar fills only *frac* of the axis
    height, leaving headroom for the legend."""
    lo, hi = ax.get_ylim()
    if lo <= 0 or hi <= 0:
        return
    log_lo, log_hi = np.log10(lo), np.log10(hi)
    ax.set_ylim(lo, 10 ** (log_lo + (log_hi - log_lo) / frac))


def _page(dxy, nevt, bins, logx, sig):
    """One page: the trigger-case muonSV Lxy curves of *sig*, raw counts. The legend
    carries each case's event count (NOT its muonSV count -- an event contributes several
    vertices), so Mu10 + DoubleMu > OR wherever events fire both triggers."""
    fig, ax = plt.subplots(figsize=(10, 8))
    for case in CASES:
        v = dxy[case["key"]]
        if len(v) == 0:
            log(f"  [warn] '{case['label']}': 0 entries -- not plotted", file=sys.stderr)
            continue
        counts, edges = np.histogram(v, bins=bins)
        ax.stairs(counts, edges, color=case["color"], lw=case["lw"])
    if logx:
        ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(bins[0], bins[-1])
    ax.set_xlabel(r"$L_{xy}$ [cm]", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Number of entries", fontsize=cms.FS_LABEL)
    ax.tick_params(labelsize=12)
    cms.cms_axes(ax, fontsize=cms.FS_AXES)
    _extend_log_top(ax, 0.80)
    # dataset description + any partial-sample warning (top-left), cf. getSignalEff_compare.C
    cms.info_legend(ax, _signal_lines(sig), fontsize=cms.FS_LEGEND)
    # trigger cases (top-right), each with its event count
    handles = [Line2D([], [], color=c["color"], lw=c["lw"],
                      label=f"{c['label']} ({nevt[c['key']]:,})")
               for c in CASES]
    ax.legend(handles=handles, fontsize=cms.FS_LEGEND, loc="upper right", **cms.LEGEND_KW)
    fig.suptitle("muonSV $L_{xy}$ per trigger case\n"
                 "all charge-neutral muonSVs of passing events", fontsize=cms.FS_TITLE)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return fig


def page_loglog(dxy, nevt, xmax, sig):
    bins = np.logspace(-4, np.log10(xmax), 60)
    return _page(dxy, nevt, bins, logx=True, sig=sig)


def page_linlog(dxy, nevt, xmax, sig):
    bins = np.linspace(0, xmax, 60)
    return _page(dxy, nevt, bins, logx=False, sig=sig)


def main():
    parser = argparse.ArgumentParser(
        description="muonSV Lxy per trigger case for one signal point")
    parser.add_argument("--output", default="compareDisplacements.pdf",
                        help="Output PDF (default: compareDisplacements.pdf)")
    parser.add_argument("--n-signal", type=int, default=N_SIGNAL_FILES,
                        help=f"Files to read, 0 or less = the whole sample "
                             f"(default: {N_SIGNAL_FILES})")
    parser.add_argument("--xmax", type=float, default=XMAX,
                        help=f"Upper end of the Lxy range [cm] (default: {XMAX:g})")
    parser.add_argument("--test", action="store_true",
                        help="Quick check: read only 1 file")
    args = parser.parse_args()

    if args.test:
        log("[TEST MODE] 1 file")

    # cap=None reads the whole sample
    cap = 1 if args.test else (args.n_signal if args.n_signal > 0 else None)

    # muonSV pages: one (log x, linear x) pair per signal point
    muonsv = []
    n_read, n_avail = 0, 0
    for sig in SIGNALS:
        log(f"\n=== {sig['dir']} (taking {cap if cap else 'ALL'} files) ===")
        all_urls = list_root_files(sig["path"])
        urls = all_urls[:cap] if cap else all_urls
        n_avail += len(all_urls)
        n_read += len(urls)
        dxy, nevt, failed = read_dxy(urls, sig["label"])
        for c in CASES:
            log(f"  [{c['label']}] {nevt[c['key']]:,} events, "
                f"{len(dxy[c['key']]):,} neutral muonSVs")
        if failed:
            log(f"  [ERROR] {len(failed)} of {len(urls)} files could NOT be read, the plots "
                f"are missing their events: {failed}", file=sys.stderr)
        else:
            log(f"  all {len(urls)} files read successfully")
        muonsv.append((sig, dxy, nevt))

    # tell the plots how much of the sample they show (must precede any plotting)
    cms.set_sample_files(n_read, n_avail)
    if cms.is_partial():
        log(f"\n  PARTIAL SAMPLE: {n_read} of {n_avail} files "
            f"({100 * cms.sample_fraction():.1f}%) -- every plot is labelled as such")
    else:
        log(f"\n  full sample: all {n_avail} files read")

    log("\n=== Writing PDF ===")
    with PdfPages(args.output) as pdf:
        for sig, dxy, nevt in muonsv:
            pdf.savefig(page_loglog(dxy, nevt, args.xmax, sig), bbox_inches="tight")
            pdf.savefig(page_linlog(dxy, nevt, args.xmax, sig), bbox_inches="tight")
        plt.close("all")
    log(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
