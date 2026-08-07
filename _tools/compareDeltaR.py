#!/usr/bin/env python3
"""DeltaR of standard dimuon vertices (muonSV) -- QCD background vs signal.

Completely independent of compareAngles.py (no four-muon / quadv logic here).
For every charge-neutral muonSV (muonSV_charge == 0, as required throughout the
framework's MuonSV_isNeutral selection) the opening angle between its two muons,
    dR = deltaR(mu1, mu2) = sqrt(deta^2 + dphi^2),
is histogrammed. Events must pass the same trigger + offline kinematic pre-selection as
getSignalEff_noMET.C (f_kin_or): fire HLT_Mu10_Barrel_L1HP11_IP6 OR HLT_DoubleMu4_3_LowMass
AND, event-level (Any over muonSVs), satisfy the Mu10 leg
[(mu1pt>10 & |mu1eta|<0.8 & |sip3d1|>6) || (mu2pt>10 & ...)] OR the DoubleMu leg
[max(mu1pt,mu2pt)>4 & min(mu1pt,mu2pt)>3]. (No dR<1.2 or chi2 cut -- the full dR shape
is the point.)
QCD MC and each signal point are overlaid on a single page, x-axis 0..7, log y. QCD is
filled with a per-vertex weight equal to its pT-hat bin cross section (QCD_XS, in pb),
so high-pT bins (e.g. PT-1000, xs=1.323) contribute a tiny weight vs low-pT bins
(PT-15to20, xs~3e6); signals are raw counts (one process each).

Only a subset of the QCD files is read by default (--n-qcd per bin). That subset is drawn
at RANDOM with a fixed seed (QCD_SAMPLE_SEED, reproducible), and each bin's weight is
scaled by files_available/files_read, so the QCD curve is the ESTIMATED whole-sample
yield rather than just what was read. Signals are read in full at the default (--n-signal
100 > the ~33-50 files each has) and are NOT scaled. Any sample read only partly is listed
in an in-plot "Partial sample plot" legend (fully-read samples are omitted). Pass
--n-qcd 0 / --n-signal 0 to read everything.

MINBIAS -- a SECOND, independent background
-------------------------------------------
InclusiveDileptonMinBias (DoubleMuOS43 filter) is overlaid on every distribution page
alongside the pT-hat QCD stack, from a random 5% of its files (--minbias-frac, fixed
seed). It is an ALTERNATIVE estimate of the same background, never an addition: the two
curves are never summed.

NORMALISATION: the MinBias curve is scaled to 100% of its own sample and nothing else.
Only 5% of the files are read, so every vertex is weighted by files_available/files_read
and the curve is the estimated whole-sample yield -- a real number about a real sample.
It is NOT area-matched to QCD. The two therefore sit on the same log axis at different
absolute scales, because no cross section is available for MinBias (config/run3_2024.py
registers the dataset with qcd_15to20's xs and a "#TODO define"). Matching the areas
would invent a normalisation no measurement supports. Pass --minbias-xs PB once the cross
section is known and the curve becomes cross-section weighted too, i.e. directly
comparable to QCD.

s/sqrt(b): every significance page is produced TWICE -- once with b = the pT-hat QCD
stack, then immediately again with b = MinBias, on the next page. The two are separate
pages rather than two curves on one axis because their denominators carry different
arbitrary scales, so only the shapes and the positions of the maxima are comparable.

DATA (--data, off by default)
-----------------------------
With --data, real data (ParkingSingleMuon + ParkingDoubleMuonLowMass, POOLED -- an event
firing both lives in both PDs and is counted twice, acceptable for a shape) is overlaid on
every distribution page as hollow black squares, always the first entry in the legend. It
is read from a random --data-frac of the files (default 1%, fixed seed) and scaled by
files_available/files_read, exactly as MinBias is, so the curve estimates the whole data
sample. The golden JSON is applied to data and only to data; every other cut -- trigger
OR, kinematic legs, charge-neutral SV -- is identical to what the MC goes through.

Data is NOT drawn on the s/sqrt(b) pages: those show a signal-to-background ratio, and
data is neither. Without --data the output is byte-for-byte what it was before the flag
existed.

The output filename gains a "_withData" suffix whenever data is actually drawn
(compareDeltaR.pdf -> compareDeltaR_withData.pdf), so the two versions of a page never
overwrite each other.

Note: the secondary peak near dR = pi is genuine back-to-back muon pairs (small
dEta, |dPhi| ~ pi) -- not an artefact (verified: no mu1index==mu2index self-pairs,
no eta==0 sentinels). dPhi is wrapped to [-pi, pi], so dR can exceed pi only through
large dEta. The framework's analysis selection (dR < 1.2) would remove this peak.

=> a 7-page block per 1D variable, repeated for dR, |deta|, |dphi| and alpha, then the 2D
   maps -- compareDeltaR.pdf
   1. overview: QCD + MinBias + the two ctau=10 mm points (scA mA=3.33, scB1 mA=1.33)
   2. Scenario A: dR distribution, all A mass points at both lifetimes (each its own curve)
   3. Scenario A: s/sqrt(b) for a SLIDING dR cut, b = QCD pT-hat bins
   4. Scenario A: the same, b = MinBias
   5. Scenario B1: dR distribution
   6. Scenario B1: s/sqrt(b) for a SLIDING dR cut, b = QCD pT-hat bins
   7. Scenario B1: the same, b = MinBias
   (the s/sqrt(b) points are CUMULATIVE: the value at cut x uses every vertex with dR < x,
   so x is a candidate analysis cut. Absolute scale is arbitrary -- b is weighted, s is
   raw counts -- the shape and the location of the maximum are the point. The QCD and
   MinBias pages carry DIFFERENT arbitrary scales, so compare their shapes, not their
   heights.)
   Pages 4 and 7 are skipped when there is no MinBias (--no-minbias, or a merge of shards
   that predate it), which shifts the numbering but never silently blanks a page.

Run after sourcing setup.sh:
    python3 _tools/compareDeltaR.py [--output path.pdf] [--n-qcd N] [--n-signal N] [--test]
                                    [--minbias-frac F] [--minbias-xs PB] [--no-minbias]
                                    [--data] [--data-frac F]

--test reads only 1 QCD file, 1 MinBias file and 1 file per signal point for a quick
debug pass.

SHARDED RUNS (--qcd-bin / --signal-only / --dump / --merge)
-----------------------------------------------------------
Reading the whole sample in one process takes ~30 h, which no longer fits any IC
condor runtime tier, so the work splits per QCD PT-hat bin. Each shard dumps only
the HISTOGRAMS it contributes (see sample_hist), which is a loss-free summary for
these 5 pages and makes the merge instant and memory-free:

    # one job per PT-hat bin (12 of them), one for MinBias, one for all the signal points
    python3 _tools/compareDeltaR.py --qcd-bin QCD_Bin-PT-1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8 \
        --n-qcd 0 --dump shards/qcd_PT-1000.npz
    python3 _tools/compareDeltaR.py --minbias-only --dump shards/minbias.npz
    python3 _tools/compareDeltaR.py --data-only --dump shards/data.npz   # only with --data
    python3 _tools/compareDeltaR.py --signal-only --n-signal 0 --dump shards/signal.npz

    # then, once every shard exists (reads no ROOT files, takes seconds)
    python3 _tools/compareDeltaR.py --merge shards --output compareDeltaR_AllSamples.pdf

--merge refuses to run if any of the 12 QCD bins is missing: a silently absent shard
would leave the QCD normalisation quietly too low. A missing MinBias shard is only
WARNED about -- MinBias is never summed into the QCD estimate, so losing it costs a
curve, not a normalisation, and old shard directories stay mergeable. See
_tools/condor/compareDeltaR.dag for the condor wiring.
"""

import argparse
import glob
import math
import os
import random
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.backends.backend_pdf import PdfPages

import cmsstyle as cms
import goldenjson as gj
# Golden-JSON mask, set in main(). None = disabled/unavailable, in which case every
# data event is kept. MC is never masked.
CERT = None
GCOUNT = gj.Counter()

XRD_SERVER = "root://gfe02.grid.hep.ph.ic.ac.uk/"
BASE       = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024"

# No data on this page -- QCD and signal are both simulation -- so no luminosity is
# quoted; see _tools/cmsstyle.py. The QCD curve is cross-section weighted, not normalised
# to any luminosity.

def _sdir(dirname):
    return f"{BASE}/{dirname}_TuneCP5_13p6TeV_powheg-pythia8"


def _mp(scenario, mA, mpi, mA_str):
    """One mass point, with the two lifetime sample dirs (ctau = 10 mm and 0.1 mm)."""
    scen_dir = "ScenarioA" if scenario == "A" else "ScenarioB1"
    ctag = "scA" if scenario == "A" else "scB1"
    base = f"GluGluHToDarkShowers-{scen_dir}_Par-ctau-%s-mA-{mA_str}-mpi-{mpi}"
    return {"scenario": scenario, "mA": mA,
            "tag": rf"{ctag} $m_\pi$={mpi}, $m_A$={mA:g}",
            "d10": _sdir(base % "10"),
            "d01": _sdir(base % "0p1")}


# Mass points, ordered Scenario A (by increasing mA) then Scenario B1 (by increasing mA).
# Each is shown at BOTH lifetimes (ctau = 10 mm and 0.1 mm), every curve solid with its
# own colour and its own legend entry. Page 1 keeps the original two-signal overview; the
# per-scenario pages 2-3 (A) and 4-5 (B1) split them out.
MASS_POINTS = [
    _mp("A",  0.40, 4,  "0p40"),
    _mp("A",  1.00, 10, "1p00"),
    _mp("A",  3.33, 10, "3p33"),
    _mp("B1", 0.33, 1,  "0p33"),
    _mp("B1", 1.33, 4,  "1p33"),
    _mp("B1", 1.67, 5,  "1p67"),
]

# distinct colours for the per-(mass, lifetime) curves within one scenario plot
# Signal colours. Deliberately excludes every colour a NON-signal curve owns: blue is
# MinBias, crimson is QCD, black is Data. Both blue and crimson used to be in here, so a
# signal point could take the same colour as a background on the very page that compares
# them. Kept as one list so the ordering -- and therefore which point gets which colour --
# is identical on every page and between the overview and per-scenario plots.
PALETTE = ["darkorange", "forestgreen", "darkviolet", "saddlebrown", "deeppink", "olive"]

TREE_NAME = "Events"

# QCD MuEnriched bins and their cross sections [pb]. Each QCD event is filled with a
# weight = the cross section of its pT-hat bin (proportional to the bin xs, exactly as
# getSignalEff_noMET.C does: per-event weight sigma_q, no /N, no luminosity). The high
# pT bins (e.g. PT-1000, xs=1.323) thus contribute a tiny weight vs the low-pT ones.
QCD_XS = {
    "QCD_Bin-PT-15to20_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":   3018000.0,
    "QCD_Bin-PT-20to30_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":   2701000.0,
    "QCD_Bin-PT-30to50_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":   1461000.0,
    "QCD_Bin-PT-50to80_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":    407600.0,
    "QCD_Bin-PT-80to120_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":    96070.0,
    "QCD_Bin-PT-120to170_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":   23140.0,
    "QCD_Bin-PT-170to300_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":    7754.0,
    "QCD_Bin-PT-300to470_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":     699.6,
    "QCD_Bin-PT-470to600_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":      67.67,
    "QCD_Bin-PT-600to800_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":      21.27,
    "QCD_Bin-PT-800to1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":      3.89,
    "QCD_Bin-PT-1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8":           1.323,
}

N_QCD_FILES    = 100  # per QCD PT-hat bin (--n-qcd; <=0 reads all)
N_SIGNAL_FILES = 100  # per signal point (--n-signal; <=0 reads all; caps at all available)
QCD_SAMPLE_SEED = 0   # seed for the random per-bin QCD file subset (reproducible)

# The MinBias QCD alternative: InclusiveDileptonMinBias with the DoubleMuOS43 generator
# filter, processed by Prijith (2026-07-30). A full path, not a directory under BASE --
# it lives in a different user's dCache area.
MINBIAS_DIR = ("/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/ppradeep/samples/Parking/Run3/"
               "Nanotronv14/InclusiveDileptonMinBias_Fil-DoubleMuOS43_TuneCP5Plus_13p6TeV"
               "_pythia8/2024WithMET/260730_143555")
MINBIAS_FRAC = 0.05         # fraction of the MinBias files (--minbias-frac)
MINBIAS_SEED = 20260806     # seed for the random MinBias file subset (reproducible)
# Blue. Black now belongs to Data alone (see DATA_COLOR) -- two solid black curves told
# apart only by their marker shape was too easy to misread where they cross. Blue is
# therefore reserved for MinBias and removed from the signal PALETTE, so no signal point
# can ever collide with it.
MINBIAS_COLOR = "royalblue"
# Cross section [pb], or None. None means "no xs known" -- see the module docstring: the
# curve is then drawn as a shape normalised to the QCD area. Set from --minbias-xs in
# main() and carried through the shard dump so a merge cannot silently change the meaning
# of the y axis.
MINBIAS_XS = None

# DATA -- ParkingSingleMuon + ParkingDoubleMuonLowMass, pooled, under BASE. Off unless
# --data is passed, so the default output is unchanged. A random seeded fraction, like
# MinBias: the sample is ~360k files and only its SHAPE is wanted here.
DATA_FRAC = 0.01            # 1% of the data files (--data-frac)
DATA_SEED = 20240729        # reproducible draw (--data-seed)
# Black with a hollow marker: this page is otherwise all filled/solid MC curves, so an
# unfilled marker reads as "measurement" at a glance and cannot be confused with them.
DATA_COLOR = "black"
# Backgrounds are WHITE-filled, not unfilled: an unfilled marker lets the curve behind it
# show through the middle, which on a page with several overlapping histograms reads as
# clutter. White fill keeps the hollow look while masking whatever passes underneath.
# Data is a solid black square, deliberately SMALLER than the background circles: it sits
# on top of statistical error bars, and a large marker swallows the short bars in the
# dense part of the spectrum, which is exactly where the bars are the point.
DATA_MARKER = "s"           # square, data (solid fill)
DATA_MARKER_SIZE = 3.5
BKG_MARKER = "o"            # circle, both background estimates
MARKER_SIZE = 4.5
MARKER_EDGE = 1.1

DR_BRANCHES = ["muonSV_mu1pt", "muonSV_mu1eta", "muonSV_mu1phi",
               "muonSV_mu2pt", "muonSV_mu2eta", "muonSV_mu2phi", "muonSV_charge",
               # needed for the IP6 leg of the trigger emulation: muonSV_mu{1,2}index
               # point into the MuonBPark collection, which is where sip3d lives
               # (there is no muonSV_*sip3d branch).
               "muonSV_mu1index", "muonSV_mu2index", "MuonBPark_sip3d"]

# Event must fire EITHER trigger (single-muon OR double-muon). Missing branches are
# treated as not-fired.
TRIGGERS = ["HLT_Mu10_Barrel_L1HP11_IP6", "HLT_DoubleMu4_3_LowMass"]

# proxy: prefer the one from the environment (setup.sh sets X509_USER_PROXY)
_env_proxy = os.environ.get("X509_USER_PROXY", "")
if not (_env_proxy and os.path.exists(_env_proxy)):
    os.environ["X509_USER_PROXY"] = f"/tmp/x509up_u{os.getuid()}"
_XRDFS_ENV = os.environ


def log(msg, **kwargs):
    print(msg, flush=True, **kwargs)


# ----------------------------------------------------------------------------
# file discovery (same approach as compareSVcharge.py)
# ----------------------------------------------------------------------------
def xrdfs_ls(path, server=None):
    srv = server or XRD_SERVER
    result = subprocess.run(
        ["xrdfs", srv, "ls", "-l", path],
        capture_output=True, text=True, env=_XRDFS_ENV,
    )
    # A failed listing MUST NOT look like an empty directory. Without this check a node
    # that cannot authenticate to the storage (e.g. no CA dir, so X509_CERT_DIR is
    # unset/wrong) returns rc != 0 with empty stdout, every sample silently reads zero
    # files, and the run still "succeeds" -- producing a shard full of zeros that the
    # partial-sample legend then labels COMPLETE, because 0 read >= 0 available.
    if result.returncode != 0:
        raise RuntimeError(
            f"xrdfs ls failed for {srv}{path} (rc={result.returncode}). "
            f"Check X509_USER_PROXY and X509_CERT_DIR. stderr: {result.stderr.strip()}")
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
# reading -> flat deltaR array
# ----------------------------------------------------------------------------
def read_deltaR(urls, label, is_data=False):
    """Return a flat numpy array of muonSV deltaR(mu1, mu2) over all *urls*.

    *is_data* applies the golden JSON (certified lumisections) before anything else. MC is
    never masked. Everything downstream -- trigger OR, the kinematic legs, the neutral-SV
    requirement -- is applied identically to data and MC, which is the point: the data
    curve has to come through the same selection as the samples it is drawn against."""
    import uproot
    import awkward as ak
    out = []
    n = len(urls)
    for i, url in enumerate(urls, 1):
        fname = url.split("/")[-1]
        log(f"  [{i}/{n}] {fname}")
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                keys = set(tree.keys())
                if any(b not in keys for b in DR_BRANCHES):
                    log(f"  [warn] {fname}: muonSV branches missing -- skipping", file=sys.stderr)
                    continue
                need = list(DR_BRANCHES)
                if is_data and CERT is not None:
                    need += [b for b in gj.BRANCHES if b not in need]
                a = tree.arrays(need, library="ak")
                gmask = None
                if is_data and CERT is not None:
                    gmask = GCOUNT.update(gj.mask(ak.to_numpy(a["run"]),
                                                  ak.to_numpy(a["luminosityBlock"]), CERT))
                    a = a[gmask]
                    if len(a) == 0:
                        continue
                # event-level trigger OR mask; keep only events that fired
                present = [t for t in TRIGGERS if t in keys]
                if i == 1 and len(present) < len(TRIGGERS):
                    log(f"  [warn] {label}: trigger(s) absent, treated as not-fired: "
                        f"{[t for t in TRIGGERS if t not in keys]}", file=sys.stderr)
                # tree[t] is read fresh from the file, so it is UNMASKED -- it has to be
                # cut down to the same events as `a` or the two disagree in length and the
                # mask silently selects the wrong rows.
                tmask = np.zeros(len(a), dtype=bool)
                for t in present:
                    tv = tree[t].array(library="np").astype(bool)
                    tmask |= (tv[gmask] if gmask is not None else tv)
                # Offline kinematic legs, event-level Any over muonSVs: Mu10 OR DoubleMu.
                # These now mirror modules/muon_selection.py
                # (DQCDMuonSelection2024RDFProducer_HLT_Mu10_Barrel_L1HP11_IP6) rather than
                # the looser cuts this script used to carry:
                #   Mu10 leg     pt > 10, |eta| < 0.8, |sip3d| > 6   (was |eta| < 1.2, no sip3d)
                #   DoubleMu leg pt > 4/3, |eta| < 2.4, |sip3d| > 6  (was no eta, no sip3d)
                # |eta| < 0.8 is the BMTF/L1HP barrel acceptance the trigger is seeded from,
                # and the "IP6" in the path name IS the |sip3d| > 6 requirement -- leaving it
                # out inflated the Mu10-leg acceptance. The L1 bit itself is not emulated here.
                m1pt, m1eta = a["muonSV_mu1pt"], a["muonSV_mu1eta"]
                m2pt, m2eta = a["muonSV_mu2pt"], a["muonSV_mu2eta"]
                sip = a["MuonBPark_sip3d"]
                s1 = np.abs(sip[a["muonSV_mu1index"]])
                s2 = np.abs(sip[a["muonSV_mu2index"]])
                mu10 = ((m1pt > 10) & (np.abs(m1eta) < 0.8) & (s1 > 6)) | \
                       ((m2pt > 10) & (np.abs(m2eta) < 0.8) & (s2 > 6))
                mx, mn = np.maximum(m1pt, m2pt), np.minimum(m1pt, m2pt)
                dmu = ((mx > 4) & (mn > 3)
                       & (np.abs(m1eta) < 2.4) & (np.abs(m2eta) < 2.4)
                       & ((s1 > 6) | (s2 > 6)))   # module requires Sum(...sip3d>6) > 0
                kin = ak.to_numpy(ak.any(mu10 | dmu, axis=1))
                mask = tmask & kin       # trigger + kinematic pre-selection
                a = a[mask]
                # only charge-neutral muonSVs, as in the framework (MuonSV_isNeutral)
                neutral = a["muonSV_charge"] == 0
                deta = a["muonSV_mu1eta"][neutral] - a["muonSV_mu2eta"][neutral]
                dphi = a["muonSV_mu1phi"][neutral] - a["muonSV_mu2phi"][neutral]
                dphi = np.arctan2(np.sin(dphi), np.cos(dphi))
                # Keep the COMPONENTS, not just dR: the deta/dphi pages and the 2D
                # heatmaps cannot be rebuilt from a dR histogram, and dR = hypot(deta,
                # dphi) is recovered exactly from them.
                # True 3D opening angle between the two muon momenta:
                #   cos(alpha) = (cos(dphi) + sinh(eta1) sinh(eta2)) / (cosh(eta1) cosh(eta2))
                # The pT factors cancel exactly, so this needs no extra branches. Unlike
                # dR it is a real angle -- bounded by pi, and the quantity that actually
                # says how collimated the pair is. dR is the eta-phi metric, which is
                # boost-friendly but is NOT an angle and can exceed pi.
                e1 = a["muonSV_mu1eta"][neutral]
                e2 = a["muonSV_mu2eta"][neutral]
                cosa = ((np.cos(dphi) + np.sinh(e1) * np.sinh(e2))
                        / (np.cosh(e1) * np.cosh(e2)))
                fdeta = np.abs(ak.to_numpy(ak.flatten(deta)).astype(float))
                fdphi = np.abs(ak.to_numpy(ak.flatten(dphi)).astype(float))
                # Flatten BEFORE clipping: np.clip is not a ufunc, so on a jagged awkward
                # array it destroys the layout and the later ak.to_numpy fails with
                # "cannot convert to RegularArray". Everything above is ufunc-only.
                fcos = ak.to_numpy(ak.flatten(cosa)).astype(float)
                falpha = np.arccos(np.clip(fcos, -1.0, 1.0))
                flat = np.stack([fdeta, fdphi, falpha])
                out.append(flat)
                log(f"         -> {flat.shape[1]:,} vertices "
                    f"({int(tmask.sum()):,} trig, {int(mask.sum()):,} trig+kin events)")
        except Exception as exc:
            log(f"  [warn] skipping {fname}: {exc}", file=sys.stderr)
    if not out:
        return np.zeros((3, 0), dtype=float)
    return np.concatenate(out, axis=1)


def gather_qcd_bins(args):
    """N files of every QCD PT-hat bin, kept per bin with its cross section.

    Returns (bins, n_read, n_available), where bins is a list of
    (bin_name, xs, [files], n_bin_available, n_bin_read). When a bin is only partly read
    the files are drawn at RANDOM (seeded, reproducible) rather than the first N, and
    n_bin_available/n_bin_read let the caller scale that bin up to an estimated total.
    --n-qcd <= 0 reads every file; test mode reads 1 file of the first bin."""
    log(f"\n[QCD] listing {BASE}")
    top = xrdfs_ls(BASE)
    qcd_dirs = sorted(e for e in top if e[0].split("/")[-1].startswith("QCD_Bin-PT-"))
    # shard mode: restrict to the single PT-hat bin this job owns
    if getattr(args, "qcd_bin", None):
        qcd_dirs = [e for e in qcd_dirs if e[0].split("/")[-1] == args.qcd_bin]
        if not qcd_dirs:
            raise SystemExit(f"[error] --qcd-bin {args.qcd_bin!r} not found under {BASE}")
    # cap: 1 in test, all if --n-qcd <= 0, else n_qcd. None = no cap.
    cap = 1 if args.test else (args.n_qcd if args.n_qcd > 0 else None)
    log(f"  {len(qcd_dirs)} PT-bin directories; taking "
        f"{cap if cap else 'ALL'} file(s) {'total' if args.test else 'each'}")
    rng = random.Random(QCD_SAMPLE_SEED)   # reproducible random subset per bin
    bins = []
    n_read, n_avail = 0, 0
    for path, _ in qcd_dirs:
        name = path.split("/")[-1]
        xs = QCD_XS.get(name)
        if xs is None:
            log(f"  [warn] no cross section for {name} -- skipping", file=sys.stderr)
            continue
        all_files = list_root_files(path)
        if not all_files:
            raise SystemExit(f"[error] no .root files found for QCD bin {name} under {path}")
        if cap is None or cap >= len(all_files):
            bfiles = list(all_files)                       # whole bin
        else:
            bfiles = rng.sample(all_files, cap)            # random subset, seeded
        n_avail += len(all_files)
        n_read += len(bfiles)
        bins.append((name, xs, bfiles, len(all_files), len(bfiles)))
        if args.test and bfiles:
            break
    log(f"  => {sum(len(b[2]) for b in bins)} QCD files over {len(bins)} bins")
    return bins, n_read, n_avail


DR_BINS = np.linspace(0, 7.0, 70)             # x-axis 0..7 for the distributions
# Fine bin edges for the CUMULATIVE s/sqrt(b) sums; the cut value is each upper edge,
# so the point at cut x uses every vertex with dR < x. Defined here (rather than just
# above plot_significance, where it used to live) because sample_hist needs both
# binnings.
SB_CUT_EDGES = np.arange(0.0, 7.0001, 0.05)
SB_CUTS = SB_CUT_EDGES[1:]

# The three 1D variables. |deta| reaches 4.8 for two |eta| < 2.4 muons; |dphi| is wrapped
# to [0, pi] and so is bounded by pi -- which is exactly why dR > pi requires eta
# separation, the motivation for the dR = pi reference line.
DETA_BINS = np.linspace(0.0, 5.0, 51)
DPHI_BINS = np.linspace(0.0, math.pi, 51)
SB_DETA_EDGES = np.arange(0.0, 5.0001, 0.05)
SB_DPHI_EDGES = np.arange(0.0, math.pi + 1e-9, 0.05)
ALPHA_BINS = np.linspace(0.0, math.pi, 51)
SB_ALPHA_EDGES = np.arange(0.0, math.pi + 1e-9, 0.05)

# 2D (|deta|, |dphi|) grid. Coarser than the 1D binnings on purpose: it carries 50 x 32
# cells per sample, and the s/sqrt(b) map is its double cumulative sum, so every cell is
# the significance of the RECTANGULAR cut |deta| < x AND |dphi| < y.
H2_ETA_EDGES = np.arange(0.0, 5.0001, 0.1)
H2_PHI_EDGES = np.arange(0.0, math.pi + 1e-9, 0.1)

# name -> (axis label, display bins, s/sqrt(b) cut edges, reference lines, x max)
# name -> (axis label, display bins, s/sqrt(b) cut edges, x max)
# The 4th field used to hold dR reference lines (dR = 1.2 and dR = pi, drawn dashed with
# their own legend entries). They are gone: the pages are read as distributions, and a
# grey line labelled "cut" invites the eye to treat one particular threshold as decided
# when the whole point of the s/sqrt(b) pages is to derive it. Removed rather than made
# optional -- nothing else consumed them.
VAR_SPECS = {
    "dr":   (r"Muon SV $\Delta R(\mu,\mu)$",        DR_BINS,   SB_CUT_EDGES, 7.0),
    "deta": (r"Muon SV $|\Delta\eta(\mu,\mu)|$",   DETA_BINS, SB_DETA_EDGES, 5.0),
    "dphi": (r"Muon SV $|\Delta\phi(\mu,\mu)|$",   DPHI_BINS, SB_DPHI_EDGES, math.pi),
    # the true 3D opening angle -- an actual angle, so pi is a hard ceiling
    "alpha": (r"Muon SV 3D opening angle $\alpha(\mu,\mu)$", ALPHA_BINS, SB_ALPHA_EDGES,
              math.pi),
}


# ----------------------------------------------------------------------------
# per-sample histograms -- the unit of work that gets sharded
# ----------------------------------------------------------------------------
# Both binnings above are fixed, and every one of the 5 pages is built purely from
# histograms on them, so a pair of histograms is a LOSS-FREE summary of a sample for
# these plots. Sharding therefore dumps ~210 floats per sample instead of the ~1e8
# raw dR values, and merging is an elementwise sum:
#     sum_bins hist(dr_bin, weights=xs_bin)  ==  hist(concat(dr_bin), weights=concat(xs_bin))
# because the QCD weight is constant within a PT-hat bin. That identity is what makes
# per-bin sharding give bit-for-bit the same curves as the old single-process run,
# and it keeps the merge step at ~0 memory instead of the ~5 GB the concatenated
# arrays needed.

VARS_1D = ("dr", "deta", "dphi", "alpha")
HIST_KEYS = [f"{v}_{k}" for v in VARS_1D for k in ("dist", "cum")] + ["h2"]


def sample_hist(deltas, weight=None):
    """Everything the plots need from one sample's (|deta|, |dphi|) array.

    *deltas* is shape (2, N). dR is recomputed here rather than stored upstream, so the
    dR pages stay bit-for-bit what they were while deta/dphi/2D come for free.

    weight: per-vertex constant (the QCD bin's xs * files_avail/files_read scale) or
    None for raw counts (signal). Kept as a scalar rather than an array because it is
    constant by construction -- see the identity above."""
    deta, dphi, alpha = deltas[0], deltas[1], deltas[2]
    dr = np.hypot(deta, dphi)
    n = len(dr)
    w = None if weight is None else np.full(n, weight, dtype=float)
    out = {"n": int(n), "wsum": float(n if weight is None else weight * n)}
    for name, vals in (("dr", dr), ("deta", deta), ("dphi", dphi), ("alpha", alpha)):
        _, bins, sb, _ = VAR_SPECS[name]
        out[f"{name}_dist"] = np.histogram(vals, bins=bins, weights=w)[0].astype(float)
        out[f"{name}_cum"] = np.histogram(vals, bins=sb, weights=w)[0].astype(float)
    out["h2"] = np.histogram2d(deta, dphi, bins=[H2_ETA_EDGES, H2_PHI_EDGES],
                               weights=w)[0].astype(float)
    return out


def _zeros_for(key):
    if key == "h2":
        return np.zeros((len(H2_ETA_EDGES) - 1, len(H2_PHI_EDGES) - 1))
    name, kind = key.rsplit("_", 1)
    _, bins, sb, _ = VAR_SPECS[name]
    return np.zeros(len((bins if kind == "dist" else sb)) - 1)


def empty_hist():
    h = {k: _zeros_for(k) for k in HIST_KEYS}
    h.update(n=0, wsum=0.0)
    return h


def add_hist(a, b):
    h = {k: a[k] + b[k] for k in HIST_KEYS}
    h.update(n=a["n"] + b["n"], wsum=a["wsum"] + b["wsum"])
    return h


# Data read at (or above) the configured --data-frac IS the intended production setting,
# not a shortfall, so it is not flagged as a partial sample -- the same reasoning
# comparePileUp applies to its QCD and MinBias caps. Set in main(); a --test run never
# qualifies, since one file is a wiring check and calling that complete would be a lie.
#
# NOTE this is deliberately separate from the "est. total" wording. Whether the read was
# the INTENDED one and whether the quoted yield is EXTRAPOLATED are different facts: 1% of
# the files is the configuration we want, and its total is still an extrapolation. So the
# banner goes away while the number keeps saying "est.".
DATA_AS_COMPLETE = False


def _partial_legend_entries(partials):
    """*partials* with the samples that are complete-by-configuration removed."""
    if not DATA_AS_COMPLETE:
        return partials
    return [q for q in (partials or []) if q[0] != "Data"]


def _total_word(partials, name):
    """"total" if that sample was read whole, "est. total" if it was not.

    The number quoted in a legend is only an ESTIMATE when a partial read has been scaled
    up by files_available/files_read. Read the sample whole and the scale factor is 1, so
    the number is exact and calling it an estimate understates what is known. Whether a
    read was partial is already stated by the "Partial sample plot" legend, so the word
    here only has to agree with it -- hence both are driven off the same *partials* list.

    Unknown sample (or no file counts) falls back to the cautious "est. total"."""
    for n, read, avail in partials or []:
        if n == name:
            return "total" if avail and read >= avail else "est. total"
    return "est. total"


def _draw_qcd(ax, qcd_h, label=True, var="dr", partials=None):
    """QCD stairs (xs-weighted, scaled to the whole-sample total).
    Returns the tallest bin content (for the y-axis headroom), 0 if nothing drawn."""
    if qcd_h["n"] == 0:
        log("  [warn] QCD: 0 entries -- not plotted", file=sys.stderr)
        return 0.0
    counts = qcd_h[f"{var}_dist"]
    word = _total_word(partials, "QCD")
    lab = f"QCD MC (xs-weighted, {word} {qcd_h['wsum']:,.3g})" if label else None
    if counts.max() <= 0:
        return 0.0
    edges = VAR_SPECS[var][1]
    centres = 0.5 * (edges[:-1] + edges[1:])
    ax.plot(centres, counts, drawstyle="steps-mid", color="crimson", linewidth=2,
            marker=BKG_MARKER, markersize=MARKER_SIZE, markerfacecolor="white",
            markeredgecolor="crimson", markeredgewidth=MARKER_EDGE, label=lab)
    return float(counts[counts > 0].max())


def _draw_minbias(ax, mb_h, qcd_h, var="dr", partials=None):
    """MinBias stairs, drawn next to (never added to) the pT-hat QCD curve.

    The histogram is drawn EXACTLY as filled -- never rescaled to the QCD curve. Only a
    fraction of the files is read (--minbias-frac), so read_minbias_hist() already weights
    every vertex by files_available/files_read: the curve is the estimated yield of 100%
    of the MinBias sample, which is a real number about a real sample. With --minbias-xs
    that yield is also cross-section weighted and so directly comparable to QCD; without
    one the two curves sit on the same axis at different absolute scales, which is honest
    -- an area match would invent a normalisation that no measurement supports.

    Returns the tallest drawn bin (for the y headroom), 0 if nothing was drawn."""
    if mb_h is None or mb_h["n"] == 0:
        return 0.0
    counts = mb_h[f"{var}_dist"]
    if counts.sum() <= 0:
        return 0.0
    # "100% of sample" is gone: how much was read is the Partial-sample legend's job, and
    # repeating it here contradicted itself by also saying "est.". The word now tracks the
    # actual read -- exact when whole, estimated when scaled up from a fraction.
    word = _total_word(partials, "MinBias")
    lab = ("MinBias MC (xs-weighted, {} {:,.3g})".format(word, mb_h["wsum"])
           if MINBIAS_XS is not None
           else "MinBias MC ({} {:,.3g})".format(word, mb_h["wsum"]))
    edges = VAR_SPECS[var][1]
    centres = 0.5 * (edges[:-1] + edges[1:])
    ax.plot(centres, counts, drawstyle="steps-mid", color=MINBIAS_COLOR, linewidth=2,
            marker=BKG_MARKER, markersize=MARKER_SIZE, markerfacecolor="white",
            markeredgecolor=MINBIAS_COLOR, markeredgewidth=MARKER_EDGE, label=lab)
    return float(counts[counts > 0].max())


def _draw_data(ax, data_h, var="dr", partials=None):
    """Data as a step histogram with solid black squares and statistical error bars.

    The bars are sqrt(sum w^2) per bin. Only sum(w) is stored, but the data weight is
    CONSTANT by construction (every vertex carries the same files_available/files_read
    scale), so sum(w^2) = w * sum(w) and w itself is recoverable as wsum/n. That identity
    is why no extra array had to be carried through the shards to get an uncertainty --
    but it holds only while the weight is constant, so it would need revisiting if data
    ever gained a per-event weight.

    The bars are the honest reason not to over-read these curves: at --data-frac 0.01 the
    scale-up factor is ~100, so a bin holding a handful of raw entries has an uncertainty
    of order its own value however smooth the line through it looks.

    The full count array is passed, not just the non-empty bins. A log axis masks
    non-positive points, so empty bins leave a gap -- which is what should happen -- while
    filtering them first would have joined non-adjacent bins into one misleading step.

    The handle is stashed on the axes so _legend_data_first() can hoist it to the top of
    the legend. Returns the tallest drawn point (for the y headroom), 0 if nothing drawn."""
    if data_h is None or data_h["n"] == 0:
        return 0.0
    counts = data_h[f"{var}_dist"]
    if counts.sum() <= 0:
        return 0.0
    edges = VAR_SPECS[var][1]
    centres = 0.5 * (edges[:-1] + edges[1:])
    # w = wsum/n is the constant per-vertex weight; see the docstring.
    w = data_h["wsum"] / data_h["n"] if data_h["n"] else 1.0
    err = np.sqrt(np.maximum(w * counts, 0.0))
    # A downward bar must not reach zero or below: the y axis is log, and matplotlib
    # silently drops the whole bar rather than clipping it.
    lo_err = np.where(counts - err > 0, err, counts * (1.0 - 1e-3))
    ax.errorbar(centres, counts, yerr=[lo_err, err], fmt="none", ecolor=DATA_COLOR,
                elinewidth=1.0, capsize=0, zorder=9)
    h, = ax.plot(centres, counts, drawstyle="steps-mid",
                 color=DATA_COLOR, linewidth=1.6,
                 marker=DATA_MARKER, markersize=DATA_MARKER_SIZE,
                 markerfacecolor=DATA_COLOR, markeredgecolor=DATA_COLOR,
                 markeredgewidth=MARKER_EDGE, zorder=10,
                 label=(f"Data, scaled to {cms.LUMI_FB:.3g} fb$^{{-1}}$ "
                        f"({_total_word(partials, 'Data')} {data_h['wsum']:,.3g})"))
    ax._data_handles = [h]
    return float((counts + err)[counts > 0].max())


# Fraction of the (log) axis height the tallest curve is allowed to fill. Lowering it
# lifts the top of the axis, so the curves occupy less of the canvas and the legend has
# more clear space above them.
HEADROOM = 0.75


def _apply_headroom(ax, ymax_data, frac=HEADROOM):
    """Set the log-y upper limit so the tallest plotted value sits at `frac` (=80%) of the
    axes height, leaving the top (1-frac) as headroom. Keeps matplotlib's autoscaled
    bottom; only the top is moved."""
    if not (ymax_data > 0):
        return
    ax.autoscale(enable=True, axis="y")
    lo = max(ax.get_ylim()[0], 1e-300)
    log_span = (math.log10(ymax_data) - math.log10(lo)) / frac
    ax.set_ylim(lo, lo * 10 ** log_span)


def _legend_data_first(ax, **kw):
    """Legend with the Data entry forced to the TOP of the box.

    Explicit rather than relying on draw order: matplotlib collects ax.lines before
    ax.patches, and Data is drawn with markers (a Line2D) while every MC curve is an
    ax.stairs StepPatch -- so Data would usually come out first by accident. "Usually" is
    not good enough for a legend whose reading order is part of the message, and the
    accident reverses the moment a curve changes artist type."""
    handles, labels = ax.get_legend_handles_labels()
    data_ids = {id(h) for h in getattr(ax, "_data_handles", [])}
    first = [i for i, h in enumerate(handles) if id(h) in data_ids]
    rest = [i for i, h in enumerate(handles) if id(h) not in data_ids]
    order = first + rest
    return ax.legend([handles[i] for i in order], [labels[i] for i in order], **kw)


def _finish_dr(ax, var="dr", with_data=False):
    """Axis furniture. *with_data* switches the header to the data convention.

    A page carrying real data must NOT be labelled "Simulation" (cmsstyle.py says so
    outright), and it must quote a luminosity. The header quotes the luminosity ACTUALLY
    READ -- LUMI_FB scaled by files_read/files_available, via cms.set_lumi_files() -- so
    it describes the data that went into the plot and nothing more. That the curve is then
    scaled up to the full 2024 luminosity is stated where the scaling lives, in the Data
    legend entry, rather than by inflating the header.

    Pages without data keep "Simulation Preliminary" and no luminosity, so a run with
    --data does not relabel the s/sqrt(b) pages, which have no data on them."""
    label, _, _, xmax = VAR_SPECS[var]
    ax.set_yscale("log")
    ax.set_xlim(0, xmax)
    ax.set_xlabel(label, fontsize=12)
    ax.set_ylabel("Number of events", fontsize=12)
    if with_data:
        cms.cms_axes(ax, header=cms.lumi_header(), label=cms.CMS_LABEL_DATA)
    else:
        cms.cms_axes(ax)


def _scenario_curves(mass_data, scenario):
    """[(label, colour, dr)] for every (mass, lifetime) of one scenario, ordered by mA
    then lifetime, each with its own colour and explicit legend label."""
    curves, ci = [], 0
    for mp, dr10, dr01 in mass_data:
        if mp["scenario"] != scenario:
            continue
        for ct_label, dr in ((r"$c\tau$=0.1 mm", dr01), (r"$c\tau$=10 mm", dr10)):
            curves.append((f"{mp['tag']}, {ct_label}", PALETTE[ci % len(PALETTE)], dr))
            ci += 1
    return curves


# --- dR distribution: QCD + a set of signal curves --------------------------
def plot_dr_dist(qcd_h, curves, partials, legend_title=None, var="dr", mb_h=None,
                 data_h=None):
    fig, ax = plt.subplots(figsize=(10, 8))
    ymax = _draw_qcd(ax, qcd_h, var=var, partials=partials)
    ymax = max(ymax, _draw_minbias(ax, mb_h, qcd_h, var=var, partials=partials))
    ymax = max(ymax, _draw_data(ax, data_h, var=var, partials=partials))
    bins = VAR_SPECS[var][1]
    for label, color, h in curves:
        if h["n"] == 0:
            log(f"  [warn] '{label}': 0 entries -- not plotted", file=sys.stderr)
            continue
        counts = h[f"{var}_dist"]
        ax.stairs(counts, bins, color=color, linewidth=2, label=f"{label} ({h['n']:,})")
        if len(counts):
            ymax = max(ymax, float(counts.max()))
    # Keyed on what was DRAWN, not on the --data flag: a page with an empty data
    # histogram is a simulation page and must stay labelled as one.
    _finish_dr(ax, var, with_data=(data_h is not None and data_h["n"] > 0))
    _apply_headroom(ax, ymax)
    # Fixed corner, not loc="best": "best" is data-dependent, so two pages showing the
    # same kind of plot could place their legends differently.
    _legend_data_first(ax, fontsize=10, loc="upper right", title=legend_title,
                      **cms.LEGEND_KW)
    cms.partial_samples_legend(ax, _partial_legend_entries(partials), fontsize=9)
    fig.tight_layout()
    return fig


# --- s/sqrt(b) for a SLIDING dR cut (cumulative: dR < cut) -------------------
# Each point at cut x uses ALL vertices with dR < x, not a single 0.1-wide bin: a fine
# histogram is cumulatively summed. So x is a candidate analysis cut and the curve shows
# how s/sqrt(b) evolves as the cut is loosened from 0 to 7.
def plot_significance(bkg_h, curves, partials, legend_title=None, var="dr",
                      bkg_label="QCD"):
    """s/sqrt(b) for a SLIDING dR cut: the point at cut x includes every vertex with
    dR < x (cumulative) -- s = signal counts below the cut, b = the background yield
    below the cut. The absolute scale is arbitrary (the background is weighted, the signal
    is raw counts); the shape -- and where s/sqrt(b) is maximised -- is the point.

    *bkg_label* names what is in the denominator, and the PDF carries one page per
    background. It is stated in the legend header (not the axis title, which would only
    repeat it) because the two backgrounds have DIFFERENT arbitrary scales -- QCD is
    cross-section weighted (pb), MinBias is a vertex count scaled to 100% of its sample --
    so the two pages' heights must never be read against each other. Only the shapes and
    the positions of the maxima are comparable."""
    fig, ax = plt.subplots(figsize=(10, 8))
    xlabel, _, sb_edges, xmax = VAR_SPECS[var]
    cuts = sb_edges[1:]
    b_cum = np.cumsum(bkg_h[f"{var}_cum"])        # background yield below the cut
    ymax = 0.0
    for label, color, h in curves:
        if h["n"] == 0:
            continue
        s_cum = np.cumsum(h[f"{var}_cum"])        # signal counts below the cut
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(b_cum > 0, s_cum / np.sqrt(b_cum), np.nan)
        ax.plot(cuts, ratio, color=color, lw=2, label=label)
        finite = ratio[np.isfinite(ratio)]
        if finite.size:
            ymax = max(ymax, float(finite.max()))
    ax.set_yscale("log")
    ax.set_xlim(0, xmax)
    # Same wording as the distribution pages, with "cut" appended: the axis is the same
    # quantity, just used as a threshold rather than plotted directly.
    ax.set_xlabel(xlabel + " cut", fontsize=12)
    sym = {"dr": r"\Delta R", "deta": r"|\Delta\eta|", "dphi": r"|\Delta\phi|",
           "alpha": r"\alpha"}[var]
    ax.set_ylabel(rf"$s/\sqrt{{b}}$  (cumulative, for ${sym} <$ cut)", fontsize=12)
    cms.cms_axes(ax)
    _apply_headroom(ax, ymax)
    # The legend header defines BOTH symbols in the y-axis formula -- s on one line, b on
    # the next -- so it is the single place that says what this page is a significance
    # OF. That is why the axis title does not repeat the background: the two s/sqrt(b)
    # pages for a scenario sit on consecutive pages and are told apart here.
    title = (f"$s$ = {legend_title}\n$b$ = {bkg_label}" if legend_title
             else f"$b$ = {bkg_label}")
    _legend_data_first(ax, fontsize=10, loc="lower right", title=title,
                      **cms.LEGEND_KW)
    cms.partial_samples_legend(ax, _partial_legend_entries(partials), fontsize=9)
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------
# reading -> histograms (shared by the monolithic and the sharded paths)
# ----------------------------------------------------------------------------
def read_qcd_hist(args):
    """(summed QCD hist, files_read, files_available). Honours --qcd-bin, so in shard
    mode this is one PT-hat bin and the caller dumps it for the merge step."""
    qcd_bins, qcd_read, qcd_avail = gather_qcd_bins(args)
    total = empty_hist()
    for name, xs, bfiles, n_bin_avail, n_bin_read in qcd_bins:
        log(f"\n[QCD bin] {name}  (xs = {xs:g} pb, {n_bin_read} of {n_bin_avail} files)")
        dr = read_deltaR(bfiles, name)
        if len(dr):
            # per-vertex weight = bin xs, scaled by files_available / files_read so the
            # partly-read bin estimates the yield of the WHOLE bin
            scale = xs * (n_bin_avail / n_bin_read if n_bin_read else 1.0)
            total = add_hist(total, sample_hist(dr, scale))
    return total, qcd_read, qcd_avail


def parse_chunk(spec):
    """"3/8" -> (3, 8), validated. None -> (0, 1), i.e. the whole selection."""
    if not spec:
        return 0, 1
    try:
        i, n = (int(x) for x in spec.split("/", 1))
    except ValueError:
        raise SystemExit(f"[error] --minbias-chunk must look like I/N, got {spec!r}")
    if not (n >= 1 and 0 <= i < n):
        raise SystemExit(f"[error] --minbias-chunk {spec!r}: need N >= 1 and 0 <= I < N")
    return i, n


def read_minbias_hist(args):
    """(MinBias hist, files_read, files_available) from a seeded random fraction.

    A random draw, not the head of the listing: the sample is split over 0000/0001/0002
    production subdirectories, so the first N files are one subdirectory -- a subset of
    the JOBS rather than of the sample.

    The per-vertex weight mirrors what read_qcd_hist() does for a pT-hat bin: xs scaled by
    files_available/files_selected, so a partial read estimates the whole sample. With no
    xs the weight is just that file scale, leaving the histogram in units of "estimated
    whole-sample vertex count", which is what the plots draw.

    --minbias-chunk I/N splits the SELECTED files N ways so the read can run as N parallel
    jobs whose shards are summed. Two properties make that sum exact rather than
    approximate:
      * the split is STRIDED (files[i::N]), not block, so every chunk spans the whole
        listing -- no chunk is one production subdirectory, which a block split would
        make it;
      * the file scale is computed from the SELECTION, not from the chunk, so every chunk
        carries the same weight and summing N of them reproduces the single-process
        result bit for bit. Scaling per chunk instead would multiply the total by N.
    """
    log(f"\n[MinBias] listing {MINBIAS_DIR}")
    all_files = list_root_files(MINBIAS_DIR)
    if not all_files:
        raise SystemExit(f"[error] no .root files found for MinBias under {MINBIAS_DIR}. "
                         f"Pass --no-minbias to run without it.")
    n = 1 if args.test else max(1, round(args.minbias_frac * len(all_files)))
    sel = (random.Random(args.minbias_seed).sample(all_files, n)
           if n < len(all_files) else list(all_files))
    # Sort before striding: random.sample() preserves no useful order, and a chunk must be
    # reproducible from (seed, frac, I/N) alone for the shards to be re-creatable.
    sel = sorted(sel)
    ci, cn = parse_chunk(getattr(args, "minbias_chunk", None))
    files = sel[ci::cn]
    if not files:
        raise SystemExit(f"[error] --minbias-chunk {ci}/{cn} selects no files "
                         f"(only {len(sel)} in the selection)")
    log(f"  {len(sel)} of {len(all_files)} files selected "
        f"({100 * len(sel) / len(all_files):.2f}%, seed {args.minbias_seed})"
        + (f"; chunk {ci}/{cn} -> {len(files)} files" if cn > 1 else "")
        + (f", xs = {MINBIAS_XS:g} pb" if MINBIAS_XS is not None else ", no xs (shape only)"))
    deltas = read_deltaR(files, f"MinBias[{ci}/{cn}]" if cn > 1 else "MinBias")
    scale = (MINBIAS_XS if MINBIAS_XS is not None else 1.0) * (len(all_files) / len(sel))
    total = sample_hist(deltas, scale) if len(deltas[0]) else empty_hist()
    return total, len(files), len(all_files)


def collect_data_files():
    """Every .root under the Parking* directories at BASE, both PDs pooled.

    NOTE the pooling: an event firing both a single-muon and a double-muon path lives in
    both primary datasets and is therefore counted twice here. That is acceptable for a
    SHAPE comparison -- which is all this page makes of data -- but it would not be for a
    yield."""
    out = []
    for top, is_dir in xrdfs_ls(BASE):
        name = top.rsplit("/", 1)[-1]
        if is_dir and "Parking" in name:
            found = list_root_files(top)
            log(f"    {name:34s} {len(found):>7,} files")
            out.extend(found)
    return out


def read_data_hist(args):
    """(Data hist, files_read, files_available) from a seeded random fraction.

    Weighted by files_available/files_read exactly as MinBias is, so the curve is the
    estimated yield of the WHOLE data sample rather than of the 1% actually read. It still
    shares no absolute scale with the xs-weighted QCD curve -- nothing here is normalised
    to a luminosity -- so data is drawn to be compared in SHAPE, and its legend says so.

    Supports --data-chunk I/N on the same strided basis as MinBias, because 1% of ~360k
    files is a few thousand files and that is a long serial read."""
    log(f"\n[Data] listing {BASE}")
    all_files = collect_data_files()
    if not all_files:
        raise SystemExit(f"[error] no Parking* .root files found under {BASE}. "
                         f"Drop --data to run without them.")
    n = 1 if args.test else max(1, round(args.data_frac * len(all_files)))
    sel = sorted(random.Random(args.data_seed).sample(all_files, n)
                 if n < len(all_files) else all_files)
    ci, cn = parse_chunk(getattr(args, "data_chunk", None))
    files = sel[ci::cn]
    if not files:
        raise SystemExit(f"[error] --data-chunk {ci}/{cn} selects no files "
                         f"(only {len(sel)} in the selection)")
    log(f"  {len(sel):,} of {len(all_files):,} files selected "
        f"({100 * len(sel) / len(all_files):.3f}%, seed {args.data_seed})"
        + (f"; chunk {ci}/{cn} -> {len(files):,} files" if cn > 1 else ""))
    deltas = read_deltaR(files, f"Data[{ci}/{cn}]" if cn > 1 else "Data", is_data=True)
    scale = len(all_files) / len(sel)
    total = sample_hist(deltas, scale) if len(deltas[0]) else empty_hist()
    return total, len(files), len(all_files)


def read_signal_hists(args):
    """([(mass_point, hist_ctau10, hist_ctau0.1)], partials) over every MASS_POINTS entry."""
    n_sig = 1 if args.test else (args.n_signal if args.n_signal > 0 else None)
    partials = []

    def _read(path, label):
        all_urls = list_root_files(path)
        # An empty sample is an error, never a legitimate result: with 0 files the
        # partial-sample legend reports "COMPLETE" (0 read >= 0 available) and the
        # curve silently vanishes from the plot.
        if not all_urls:
            raise SystemExit(f"[error] no .root files found for {label} under {path}")
        urls = all_urls if n_sig is None else all_urls[:n_sig]
        partials.append((label, len(urls), len(all_urls)))
        return sample_hist(read_deltaR(urls, label))

    mass_data = []
    for mp in MASS_POINTS:
        log(f"\n=== {mp['tag']}  ctau=10 ===")
        h10 = _read(mp["d10"], f"{mp['tag']} ctau=10")
        log(f"\n=== {mp['tag']}  ctau=0.1 ===")
        h01 = _read(mp["d01"], f"{mp['tag']} ctau=0.1")
        mass_data.append((mp, h10, h01))
    return mass_data, partials


# ----------------------------------------------------------------------------
# shard dump / merge
# ----------------------------------------------------------------------------
SHARD_FORMAT = 3   # 1 = dR only; 2 adds deta/dphi/2D; 3 adds the 3D angle


def dump_qcd_shard(path, bin_name, qcd_h, n_read, n_avail):
    np.savez(path, kind="qcd", qcd_bin=bin_name, fmt=SHARD_FORMAT,
             n=qcd_h["n"], wsum=qcd_h["wsum"], read=n_read, avail=n_avail,
             **{k: qcd_h[k] for k in HIST_KEYS})
    log(f"\nSaved QCD shard: {path}  ({bin_name}, {qcd_h['n']:,} vertices)")


def dump_minbias_shard(path, mb_h, n_read, n_avail, chunk="0/1"):
    # xs is stored so the merge knows whether the histogram is an absolute yield or a bare
    # count -- without it a shard made with --minbias-xs and one made without would be
    # indistinguishable, and the merged page would put an arbitrary scale on the y axis.
    # chunk is stored so the merge can sum parallel chunks while still refusing to add the
    # same one twice -- the MinBias analogue of the QCD duplicate-bin guard.
    np.savez(path, kind="minbias", fmt=SHARD_FORMAT, chunk=chunk,
             n=mb_h["n"], wsum=mb_h["wsum"], read=n_read, avail=n_avail,
             xs=(np.nan if MINBIAS_XS is None else float(MINBIAS_XS)),
             **{k: mb_h[k] for k in HIST_KEYS})
    log(f"\nSaved MinBias shard: {path}  (chunk {chunk}, {mb_h['n']:,} vertices)")


def dump_data_shard(path, data_h, n_read, n_avail, chunk="0/1"):
    # Same chunk bookkeeping as the MinBias shard: chunks are disjoint slices of one
    # selection, so the merge may SUM them but must refuse the same slice twice.
    np.savez(path, kind="data", fmt=SHARD_FORMAT, chunk=chunk,
             n=data_h["n"], wsum=data_h["wsum"], read=n_read, avail=n_avail,
             **{k: data_h[k] for k in HIST_KEYS})
    log(f"\nSaved Data shard: {path}  (chunk {chunk}, {data_h['n']:,} vertices)")


def dump_signal_shard(path, mass_data, partials):
    out = {"kind": "signal", "fmt": SHARD_FORMAT}
    names, reads, avails = zip(*partials) if partials else ((), (), ())
    out["sig_names"] = np.array(names)
    out["sig_read"] = np.array(reads, dtype=int)
    out["sig_avail"] = np.array(avails, dtype=int)
    for i, (_mp, h10, h01) in enumerate(mass_data):
        for tag, h in (("d10", h10), ("d01", h01)):
            for k in HIST_KEYS:
                out[f"s{i}_{tag}_{k}"] = h[k]
            out[f"s{i}_{tag}_n"] = h["n"]
    np.savez(path, **out)
    log(f"\nSaved signal shard: {path}  ({len(mass_data)} mass points)")


def _check_fmt(z, path):
    """Refuse a shard written before deta/dphi/2D were recorded.

    Those pages cannot be rebuilt from a dR histogram, so a stale shard would either
    crash on a missing key or -- worse -- silently contribute nothing to the new pages
    while still counting towards the QCD normalisation."""
    fmt = int(z["fmt"]) if "fmt" in z.files else 1
    if fmt < SHARD_FORMAT:
        raise SystemExit(
            f"[error] {os.path.basename(path)} is shard format v{fmt}, this build needs "
            f"v{SHARD_FORMAT}.\n        Format v1 stored only dR histograms; the deta, "
            f"dphi and 2D pages need the components.\n        Re-run the shard jobs "
            f"(the ROOT files must be read again) into a NEW directory.")


def load_shards(directory):
    """Merge every .npz under *directory* into (qcd_hist, minbias_hist, mass_data, partials).

    Hard-fails on a missing QCD bin: a silently absent shard would leave the QCD
    normalisation quietly too low, which is far worse than not producing a plot. A missing
    MinBias shard is only warned about -- MinBias is never summed into QCD, so its absence
    costs one curve rather than corrupting a normalisation, and shard directories written
    before MinBias existed stay mergeable."""
    global MINBIAS_XS
    files = sorted(glob.glob(os.path.join(directory, "*.npz")))
    if not files:
        raise SystemExit(f"[error] no .npz shards found under {directory}")

    qcd = empty_hist()
    qcd_read = qcd_avail = 0
    seen_bins = set()
    mass_data = None
    sig_partials = []
    minbias = None
    mb_read = mb_avail = 0
    seen_mb_chunks = set()
    data_h = None
    da_read = da_avail = 0
    seen_da_chunks = set()

    for f in files:
        z = np.load(f, allow_pickle=False)
        kind = str(z["kind"])
        if kind == "qcd":
            name = str(z["qcd_bin"])
            if name in seen_bins:
                raise SystemExit(f"[error] duplicate QCD shard for {name} ({f})")
            seen_bins.add(name)
            _check_fmt(z, f)
            qcd = add_hist(qcd, {**{k: z[k] for k in HIST_KEYS},
                                 "n": int(z["n"]), "wsum": float(z["wsum"])})
            qcd_read += int(z["read"])
            qcd_avail += int(z["avail"])
        elif kind == "minbias":
            _check_fmt(z, f)
            chunk = str(z["chunk"]) if "chunk" in z.files else "0/1"
            if chunk in seen_mb_chunks:
                raise SystemExit(f"[error] duplicate MinBias chunk {chunk} ({f})")
            seen_mb_chunks.add(chunk)
            part = {**{k: z[k] for k in HIST_KEYS},
                    "n": int(z["n"]), "wsum": float(z["wsum"])}
            minbias = part if minbias is None else add_hist(minbias, part)
            # Chunks are disjoint slices of ONE selection, so files read add up while the
            # sample size does not -- every chunk reports the same total.
            mb_read += int(z["read"])
            mb_avail = max(mb_avail, int(z["avail"]))
            # The shard, not the command line, decides what the MinBias histogram means:
            # it was filled with (or without) an xs at read time and that cannot be undone
            # here. Overriding it from --minbias-xs on the merge would relabel an
            # unweighted histogram as an absolute yield.
            xs = float(z["xs"]) if "xs" in z.files else float("nan")
            MINBIAS_XS = None if math.isnan(xs) else xs
        elif kind == "data":
            _check_fmt(z, f)
            chunk = str(z["chunk"]) if "chunk" in z.files else "0/1"
            if chunk in seen_da_chunks:
                raise SystemExit(f"[error] duplicate Data chunk {chunk} ({f})")
            seen_da_chunks.add(chunk)
            part = {**{k: z[k] for k in HIST_KEYS},
                    "n": int(z["n"]), "wsum": float(z["wsum"])}
            data_h = part if data_h is None else add_hist(data_h, part)
            da_read += int(z["read"])
            da_avail = max(da_avail, int(z["avail"]))
        elif kind == "signal":
            if mass_data is not None:
                raise SystemExit(f"[error] more than one signal shard ({f})")
            _check_fmt(z, f)
            mass_data = []
            for i, mp in enumerate(MASS_POINTS):
                hs = []
                for tag in ("d10", "d01"):
                    n = int(z[f"s{i}_{tag}_n"])
                    hs.append({**{k: z[f"s{i}_{tag}_{k}"] for k in HIST_KEYS},
                               "n": n, "wsum": float(n)})
                mass_data.append((mp, hs[0], hs[1]))
            sig_partials = [(str(n), int(r), int(a)) for n, r, a
                            in zip(z["sig_names"], z["sig_read"], z["sig_avail"])]
        else:
            raise SystemExit(f"[error] unknown shard kind {kind!r} in {f}")
        log(f"  loaded {kind:6s} shard {os.path.basename(f)}")

    missing = set(QCD_XS) - seen_bins
    if missing:
        raise SystemExit("[error] missing QCD shard(s), refusing to merge:\n  "
                         + "\n  ".join(sorted(missing)))
    if mass_data is None:
        raise SystemExit("[error] no signal shard found, refusing to merge")
    if minbias is None:
        log("  [warn] no MinBias shard found -- merging without the MinBias curve",
            file=sys.stderr)
    else:
        # A parallel MinBias read is only complete if every chunk of its N is present.
        # A missing one silently lowers the MinBias yield, so say so loudly -- but do not
        # abort: unlike a missing QCD bin this costs statistics on one curve, not the
        # normalisation of the whole page.
        cns = {int(c.split("/")[1]) for c in seen_mb_chunks}
        if len(cns) > 1:
            raise SystemExit(f"[error] MinBias shards disagree on the chunk count: "
                             f"{sorted(seen_mb_chunks)}. They are slices of different "
                             f"splits and must not be summed.")
        cn = cns.pop()
        missing_mb = {f"{i}/{cn}" for i in range(cn)} - seen_mb_chunks
        if missing_mb:
            log(f"  [warn] MinBias is missing chunk(s) {sorted(missing_mb)} of {cn} -- "
                f"its curve is short by that fraction", file=sys.stderr)

    if data_h is not None:
        cns = {int(c.split("/")[1]) for c in seen_da_chunks}
        if len(cns) > 1:
            raise SystemExit(f"[error] Data shards disagree on the chunk count: "
                             f"{sorted(seen_da_chunks)}. They are slices of different "
                             f"splits and must not be summed.")
        cn = cns.pop()
        missing_da = {f"{i}/{cn}" for i in range(cn)} - seen_da_chunks
        if missing_da:
            log(f"  [warn] Data is missing chunk(s) {sorted(missing_da)} of {cn} -- "
                f"its curve is short by that fraction", file=sys.stderr)

    log(f"\nMerged {len(seen_bins)} QCD bins ({qcd['n']:,} vertices) + "
        f"{len(mass_data)} signal mass points"
        + (f" + MinBias ({minbias['n']:,} vertices)" if minbias else "")
        + (f" + Data ({data_h['n']:,} vertices)" if data_h else ""))
    partials = [("QCD", qcd_read, qcd_avail)]
    if minbias is not None:
        partials.append(("MinBias", mb_read, mb_avail))
    if data_h is not None:
        partials.append(("Data", da_read, da_avail))
    return qcd, minbias, data_h, mass_data, partials + sig_partials


# --- 2D (|deta|, |dphi|) maps -----------------------------------------------
def _h2_panels(qcd_h, curves, mb_h=None):
    """[(title, hist2d)] -- every signal curve first, then the background panels.

    Signal is what the page is about; the background is the reference you compare them
    against, so it reads better as the final panel than as the one that pushes the signal
    points out of the top-left corner. Each panel has its own log colour scale, so the
    MinBias panel is readable next to the QCD one whatever its normalisation."""
    panels = [(lab, h["h2"]) for lab, _c, h in curves if h["n"] > 0]
    panels.append(("QCD MC (xs-weighted)", qcd_h["h2"]))
    if mb_h is not None and mb_h["n"] > 0:
        panels.append(("MinBias MC" + (" (xs-weighted)" if MINBIAS_XS is not None
                                       else " (arb. norm.)"), mb_h["h2"]))
    return panels


def _h2_grid(n):
    ncols = min(3, n)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.6 * ncols, 4.4 * nrows),
                             squeeze=False)
    flat = [axes[r][c] for r in range(nrows) for c in range(ncols)]
    for ax in flat[n:]:
        ax.set_visible(False)
    return fig, flat, nrows


def _h2_axes(ax, title):
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel(r"$|\Delta\eta(\mu,\mu)|$", fontsize=11)
    ax.set_ylabel(r"$|\Delta\phi(\mu,\mu)|$", fontsize=11)
    ax.tick_params(which="both", direction="in", top=True, right=True, labelsize=9)
    # No dR contours here. dR = hypot(deta, dphi) would be a quarter circle, but that
    # treats the two axes as commensurable -- |deta| is a pseudorapidity difference and
    # |dphi| an angle in radians -- so the circle asserts a metric this plane does not
    # have. The dR pages are where a dR cut belongs.
    ax.set_xlim(H2_ETA_EDGES[0], H2_ETA_EDGES[-1])
    ax.set_ylim(H2_PHI_EDGES[0], H2_PHI_EDGES[-1])


def plot_h2_counts(qcd_h, curves, partials, legend_title=None, mb_h=None):
    """Event density in (|deta|, |dphi|), one panel per sample, log colour scale.

    The dashed and dotted white arcs are the dR = 1.2 and dR = pi cuts: dR is the radius
    in this plane, so a dR cut is a quarter circle and the plane shows directly what a
    rectangular (deta, dphi) cut would keep instead."""
    panels = _h2_panels(qcd_h, curves, mb_h)
    fig, flat, nrows = _h2_grid(len(panels))
    for ax, (title, h2) in zip(flat, panels):
        pos = h2[h2 > 0]
        if pos.size == 0:
            ax.set_visible(False)
            continue
        m = ax.pcolormesh(H2_ETA_EDGES, H2_PHI_EDGES, h2.T,
                          norm=matplotlib.colors.LogNorm(vmin=pos.min(), vmax=pos.max()),
                          cmap="viridis", shading="auto")
        fig.colorbar(m, ax=ax, label="events")
        _h2_axes(ax, title)
    fig.tight_layout()
    fig.subplots_adjust(top=1.0 - 0.75 / (4.4 * nrows))
    fig.suptitle("Event density in $(|\Delta\eta|, |\Delta\phi|)$"
                 + (f" -- {legend_title}" if legend_title else ""),
                 fontsize=15, y=0.998, va="top")
    return fig


def plot_h2_significance(qcd_h, curves, partials, legend_title=None):
    """s/sqrt(b) for a RECTANGULAR cut: each cell (x, y) uses every vertex with
    |deta| < x AND |dphi| < y, i.e. the double cumulative sum of the 2D histogram.

    This is the 2D analogue of the sliding 1D cut, and it is the page that says whether a
    rectangular cut in the two components beats the circular dR cut that uses them
    together."""
    b2 = np.cumsum(np.cumsum(qcd_h["h2"], axis=0), axis=1)
    entries = [(lab, h["h2"], h["n"]) for lab, _c, h in curves if h["n"] > 0]
    if not entries:
        return None

    def sig(h2):
        """s/sqrt(b) for the rectangular cut at every cell."""
        s2 = np.cumsum(np.cumsum(h2, axis=0), axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(b2 > 0, s2 / np.sqrt(b2), np.nan)

    def best(z):
        return np.unravel_index(
            np.nanargmax(np.where(np.isfinite(z), z, -np.inf)), z.shape)

    # Combined signal: every point rescaled to the SAME total before summing, so a point
    # that simply has more MC files cannot dominate the optimum. The result is the
    # average signal shape, and its s/sqrt(b) maximum is the one cut that serves the
    # whole grid rather than any single mass point.
    comb = np.zeros_like(qcd_h["h2"])
    for _lab, h2, n in entries:
        comb += h2 / float(n)
    z_comb = sig(comb)
    bi, bj = best(z_comb)
    ov_eta, ov_phi = H2_ETA_EDGES[bi + 1], H2_PHI_EDGES[bj + 1]

    panels = [(lab, h2) for lab, h2, _n in entries]
    panels.append(("ALL signal points combined\n(each normalised to the same total)", comb))
    fig, flat, nrows = _h2_grid(len(panels))
    for ax, (title, h2) in zip(flat, panels):
        z = sig(h2)
        finite = z[np.isfinite(z) & (z > 0)]
        if finite.size == 0:
            ax.set_visible(False)
            continue
        m = ax.pcolormesh(H2_ETA_EDGES, H2_PHI_EDGES, z.T,
                          norm=matplotlib.colors.LogNorm(vmin=finite.min(),
                                                         vmax=finite.max()),
                          cmap="magma", shading="auto")
        fig.colorbar(m, ax=ax, label=r"$s/\sqrt{b}$")
        i, j = best(z)
        ax.plot(H2_ETA_EDGES[i + 1], H2_PHI_EDGES[j + 1], "*", color="white",
                ms=12, mec="black", mew=0.6, label="best for this point")
        ax.plot(ov_eta, ov_phi, "X", color="deepskyblue", ms=9, mec="black", mew=0.6,
                label="best combined")
        _h2_axes(ax, f"{title}\nbest here: "
                     rf"$|\Delta\eta|<${H2_ETA_EDGES[i+1]:.1f}, "
                     rf"$|\Delta\phi|<${H2_PHI_EDGES[j+1]:.1f}")
        # One legend per panel: the two markers can coincide, and a reader looking at any
        # single panel should not have to find the first one to learn which is which.
        ax.legend(fontsize=8, loc="lower right", framealpha=0.65)
    fig.tight_layout()
    # two-line panel titles here (sample + best cut), so more headroom than
    # the counts page needs
    fig.subplots_adjust(top=1.0 - 1.25 / (4.4 * nrows))
    fig.suptitle(r"$s/\sqrt{b}$ for a rectangular $(|\Delta\eta|, |\Delta\phi|)$ cut"
                 + (f" -- {legend_title}" if legend_title else "")
                 + rf"   |   best combined: $|\Delta\eta|<${ov_eta:.1f}, "
                   rf"$|\Delta\phi|<${ov_phi:.1f}",
                 fontsize=13, y=0.998, va="top")
    return fig


def main():
    parser = argparse.ArgumentParser(description="muonSV deltaR: QCD vs signal")
    parser.add_argument("--output", default="compareDeltaR.pdf",
                        help="Output PDF (default: compareDeltaR.pdf)")
    parser.add_argument("--n-qcd", type=int, default=N_QCD_FILES,
                        help=f"Files per QCD bin, <=0 for ALL (default: {N_QCD_FILES}); "
                             "a partial QCD read is a random seeded subset and is scaled "
                             "up to an estimated total")
    parser.add_argument("--n-signal", type=int, default=N_SIGNAL_FILES,
                        help=f"Signal files per point, <=0 for ALL (default: "
                             f"{N_SIGNAL_FILES}; caps at all available)")
    parser.add_argument("--minbias-frac", type=float, default=MINBIAS_FRAC,
                        help=f"Fraction of the MinBias files, drawn at random with a "
                             f"fixed seed (default: {MINBIAS_FRAC} = 5%%)")
    parser.add_argument("--minbias-seed", type=int, default=MINBIAS_SEED,
                        help=f"Seed for the MinBias file draw (default: {MINBIAS_SEED})")
    parser.add_argument("--minbias-xs", type=float, default=None, metavar="PB",
                        help="Cross section [pb] for the MinBias sample. Without it the "
                             "MinBias curve is a SHAPE, area-matched to QCD; with it the "
                             "curve is an absolute xs-weighted yield like QCD. No xs is "
                             "known yet (config/run3_2024.py still has '#TODO define').")
    parser.add_argument("--no-minbias", action="store_true",
                        help="Skip the MinBias sample entirely")
    parser.add_argument("--test", action="store_true",
                        help="Quick check: 1 QCD file, 1 MinBias file and 1 file per "
                             "signal point")
    parser.add_argument("--qcd-bin", default=None, metavar="DIRNAME",
                        help="Shard mode: read ONLY this QCD PT-hat bin directory "
                             "(e.g. QCD_Bin-PT-15to20_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8) "
                             "and no signal. Use with --dump.")
    parser.add_argument("--signal-only", action="store_true",
                        help="Shard mode: read the signal mass points and no QCD. "
                             "Use with --dump.")
    parser.add_argument("--minbias-only", action="store_true",
                        help="Shard mode: read ONLY the MinBias sample. Use with --dump.")
    parser.add_argument("--minbias-chunk", default=None, metavar="I/N",
                        help="Split the selected MinBias files N ways and read slice I "
                             "(strided, so each slice spans the whole sample). Lets a "
                             "100%% read run as N parallel --minbias-only jobs whose "
                             "shards the merge sums exactly. Use with --dump.")
    parser.add_argument("--data", action="store_true",
                        help="Also draw real data (ParkingSingleMuon + "
                             "ParkingDoubleMuonLowMass, pooled) on every distribution "
                             "page. OFF by default, so the default output is unchanged. "
                             "Data never appears on the s/sqrt(b) pages.")
    parser.add_argument("--data-frac", type=float, default=DATA_FRAC,
                        help=f"Fraction of the data files, drawn at random with a fixed "
                             f"seed (default: {DATA_FRAC} = 1%%). Lower it for testing.")
    parser.add_argument("--data-seed", type=int, default=DATA_SEED,
                        help=f"Seed for the data file draw (default: {DATA_SEED})")
    parser.add_argument("--data-only", action="store_true",
                        help="Shard mode: read ONLY the data. Use with --dump.")
    parser.add_argument("--data-chunk", default=None, metavar="I/N",
                        help="Split the selected data files N ways and read slice I, as "
                             "--minbias-chunk does. Use with --dump.")
    parser.add_argument("--dump", default=None, metavar="PATH.npz",
                        help="Write this shard's histograms to PATH.npz instead of a PDF")
    parser.add_argument("--merge", default=None, metavar="DIR",
                        help="Merge every .npz shard under DIR into the final PDF "
                             "(reads no ROOT files)")
    gj.add_args(parser)
    args = parser.parse_args()

    modes = [m for m in ("--qcd-bin" if args.qcd_bin else None,
                         "--signal-only" if args.signal_only else None,
                         "--minbias-only" if args.minbias_only else None,
                         "--data-only" if args.data_only else None) if m]
    if len(modes) > 1:
        parser.error(f"{', '.join(modes)} are mutually exclusive")
    if args.dump and args.merge:
        parser.error("--dump and --merge are mutually exclusive")
    if args.dump and not modes:
        parser.error("--dump needs one of --qcd-bin, --minbias-only, --data-only "
                     "or --signal-only")
    if args.minbias_only and args.no_minbias:
        parser.error("--minbias-only and --no-minbias are contradictory")
    if args.minbias_chunk and not args.minbias_only:
        # Silently reading one chunk in a non-shard run would produce a MinBias curve
        # short by a factor of N with nothing on the page saying so.
        parser.error("--minbias-chunk only applies to a --minbias-only shard run")
    if args.data_chunk and not args.data_only:
        parser.error("--data-chunk only applies to a --data-only shard run")
    # --data-only IS a request for data; requiring --data as well would be noise.
    if args.data_only:
        args.data = True

    global MINBIAS_XS, CERT, DATA_AS_COMPLETE
    DATA_AS_COMPLETE = bool(args.data and not args.test
                            and args.data_frac >= DATA_FRAC)
    MINBIAS_XS = args.minbias_xs
    # Only relevant when data is read; harmless (and silent) otherwise.
    CERT = gj.from_args(args, log) if args.data else None

    if args.test:
        log("[TEST MODE] 1 QCD file + 1 MinBias file + 1 file per signal point")

    if args.merge:
        log(f"\n=== Merging shards from {args.merge} ===")
        qcd_h, mb_h, data_h, mass_data, partials = load_shards(args.merge)
        if not args.data and data_h is not None:
            # A data shard in the directory does not by itself mean the page wants data
            # drawn -- --data is still the switch, so the default output stays unchanged
            # even in a shard dir that happens to contain one.
            log("  (data shard present but --data not passed: not drawing it)")
            data_h = None
            partials = [q for q in partials if q[0] != "Data"]
        if args.no_minbias and mb_h is not None:
            # --no-minbias means "no MinBias curve" whichever path produced it; on a merge
            # the shard is already on disk, so the only thing left to do is drop it here.
            log("  --no-minbias: dropping the MinBias shard from this merge")
            mb_h = None
            partials = [p for p in partials if p[0] != "MinBias"]
    else:
        partials = []
        # Each shard mode reads exactly one sample kind; the others stay empty so the
        # dump carries only what this job owns.
        if args.signal_only or args.minbias_only or args.data_only:
            qcd_h, qcd_read, qcd_avail = empty_hist(), 0, 0
        else:
            log("\n=== QCD ===")
            qcd_h, qcd_read, qcd_avail = read_qcd_hist(args)

        mb_h, mb_read, mb_avail = None, 0, 0
        if not (args.no_minbias or args.qcd_bin or args.signal_only or args.data_only):
            log("\n=== MinBias ===")
            mb_h, mb_read, mb_avail = read_minbias_hist(args)

        data_h, da_read, da_avail = None, 0, 0
        if args.data and not (args.qcd_bin or args.signal_only or args.minbias_only):
            log("\n=== Data ===")
            data_h, da_read, da_avail = read_data_hist(args)

        if args.qcd_bin or args.minbias_only or args.data_only:
            mass_data, sig_partials = [], []
        else:
            mass_data, sig_partials = read_signal_hists(args)

        if args.dump:
            if args.qcd_bin:
                dump_qcd_shard(args.dump, args.qcd_bin, qcd_h, qcd_read, qcd_avail)
            elif args.minbias_only:
                ci, cn = parse_chunk(args.minbias_chunk)
                dump_minbias_shard(args.dump, mb_h, mb_read, mb_avail, f"{ci}/{cn}")
            elif args.data_only:
                ci, cn = parse_chunk(args.data_chunk)
                dump_data_shard(args.dump, data_h, da_read, da_avail, f"{ci}/{cn}")
            else:
                dump_signal_shard(args.dump, mass_data, sig_partials)
            return

        partials = [("QCD", qcd_read, qcd_avail)]
        if mb_h is not None:
            partials.append(("MinBias", mb_read, mb_avail))
        if data_h is not None:
            partials.append(("Data", da_read, da_avail))
        partials += sig_partials

    for name, r, a in partials:
        state = "COMPLETE" if r >= a else f"partial ({100 * r / a:.1f}%)"
        log(f"  [{state}] {name}: {r} of {a} files")

    # A page with data on it is a different deliverable from the same page without, so it
    # gets its own filename and cannot silently overwrite the MC-only version. Keyed on
    # data_h rather than on args.data: if --data was asked for but no data survived (an
    # empty read, or a merge directory with no data shard), nothing is drawn and the name
    # must not claim otherwise. The guard makes a re-run with an explicit --output that
    # already carries the suffix idempotent rather than doubling it.
    if data_h is not None:
        # Drives cms.lumi_header(): the header must quote the luminosity of the files
        # actually read, not the one the curve is extrapolated to.
        for _n, _r, _a in partials:
            if _n == "Data":
                cms.set_lumi_files(_r, _a)
                break
        stem, ext = os.path.splitext(args.output)
        # "in", not "endswith": a name like ..._withData_test already says it carries
        # data, and endswith() only caught the suffix in final position, so that file got
        # a second "_withData" appended and was written somewhere nobody was looking.
        if "_withData" not in stem:
            args.output = f"{stem}_withData{ext or '.pdf'}"
            log(f"  data included -> writing to {args.output}")

    # page 1 keeps the original overview: two ctau = 10 mm points (scA mA=3.33, scB1 mA=1.33)
    def _dr10(scenario, mA):
        for mp, h10, _ in mass_data:
            if mp["scenario"] == scenario and abs(mp["mA"] - mA) < 1e-6:
                return f"{mp['tag']}, $c\\tau$=10 mm", h10
        return None, empty_hist()
    l_a, dr_a = _dr10("A", 3.33)
    l_b, dr_b = _dr10("B1", 1.33)
    # From PALETTE, not hardcoded: page 1 and the per-scenario pages then agree on colour
    # for the same physics, and neither can drift into a background's colour.
    page1_curves = [(l_a, PALETTE[0], dr_a), (l_b, PALETTE[1], dr_b)]

    a_curves  = _scenario_curves(mass_data, "A")
    b1_curves = _scenario_curves(mass_data, "B1")

    log("\n=== Writing PDF ===")
    n_pages = 0
    with PdfPages(args.output) as pdf:
        def save(fig):
            nonlocal n_pages
            if fig is None:
                return
            pdf.savefig(fig, bbox_inches="tight")
            n_pages += 1

        # Same five pages per variable: overview, then distribution + s/sqrt(b) for each
        # scenario. dR first so the existing page numbering is unchanged.
        # Every s/sqrt(b) page is IMMEDIATELY followed by the same page computed against
        # MinBias instead of the pT-hat stack, so the two backgrounds can be compared by
        # paging once rather than by hunting through the document. The two are separate
        # pages, never two curves on one axis: their denominators have different arbitrary
        # scales (see plot_significance), so overlaying them would invite exactly the
        # height comparison that is meaningless.
        def _sb(bkg_curves, title, var):
            save(plot_significance(qcd_h, bkg_curves, partials, title, var=var,
                                   bkg_label="QCD $p_T$ bins"))
            if mb_h is not None and mb_h["n"] > 0:
                save(plot_significance(mb_h, bkg_curves, partials, title, var=var,
                                       bkg_label="MinBias"))

        for var in VARS_1D:
            save(plot_dr_dist(qcd_h, page1_curves, partials, var=var, mb_h=mb_h,
                              data_h=data_h))
            save(plot_dr_dist(qcd_h, a_curves, partials, "Scenario A", var=var, mb_h=mb_h,
                              data_h=data_h))
            _sb(a_curves, "Scenario A", var)
            save(plot_dr_dist(qcd_h, b1_curves, partials, "Scenario B1", var=var, mb_h=mb_h,
                              data_h=data_h))
            _sb(b1_curves, "Scenario B1", var)

        # 2D maps: the components together, where a dR cut is a quarter circle
        for scen, curves in (("Scenario A", a_curves), ("Scenario B1", b1_curves)):
            save(plot_h2_counts(qcd_h, curves, partials, scen, mb_h=mb_h))
            save(plot_h2_significance(qcd_h, curves, partials, scen))
        plt.close("all")
    log(f"\nSaved: {args.output} ({n_pages} pages)")


if __name__ == "__main__":
    main()
