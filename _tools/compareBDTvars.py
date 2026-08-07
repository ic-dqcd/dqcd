#!/usr/bin/env python3
"""Data vs QCD vs signal in every variable the 2024 DQCD BDT trains on.

The BDT (icenet modeltag scenario{A,B1}_all_no_DA_old_BDT_2024_ThirdSamples) is fed 652
features, which are 85 base variables flattened over 8 object slots each
(Jet_pt_0 ... Jet_pt_7, and so on). This script plots the LEADING slot only -- one page
per base variable, 85 pages -- because slots 1-7 of a given variable carry the same
physics with progressively worse statistics, and 652 pages is not a document anybody
reads. Which object "slot 0" is depends on the collection, and is NOT the file order:
icenet filters and re-orders every collection before flattening (see ORDERING below), so
this script reproduces that exactly. Get it wrong and "Jet_pt_0" silently becomes "the
first jet stored", which is not what the BDT saw.

Seven curves per page:
    Data                  ParkingSingleMuon + ParkingDoubleMuonLowMass, a random 1% of
                          the files (--data-frac, fixed seed), pooled.
    QCD                   the 12 MuEnriched pT-hat bins, 100 files each (--n-qcd), each
                          bin weighted by its cross section so the mixture is right.
    MinBias               InclusiveDileptonMinBias (DoubleMuOS43 filter), a random 5% of
                          the files (--minbias-frac, fixed seed). An ALTERNATIVE QCD
                          background to the pT-hat stack, not an addition to it -- the two
                          are separate curves and must never be summed.
    scA  ctau=10 / 0.1    mpi=10, mA=3.33, both lifetimes, read in full.
    scB1 ctau=10 / 0.1    mpi=4,  mA=1.33, both lifetimes, read in full.

Every curve is normalised to unit area: the point is the SHAPE the BDT sees, and the
three sources differ in absolute yield by many orders of magnitude. QCD is xs-weighted
BEFORE that normalisation, so its shape is the correct pT-hat mixture rather than a
flat average over bins.

SELECTION -- exactly the icenet combined-model preselection, taken from the training log
of cluster 4615190 (not from getSignalEff_noMET.C, whose kinematic legs differ: it uses
|eta| < 0.8 and an sip3d cut, icenet uses |eta| < 1.2 and no sip3d):

    (1) HLT_Mu10_Barrel_L1HP11_IP6 OR HLT_DoubleMu4_3_LowMass
    (2) Any muonSV with [(mu1pt>10 & |mu1eta|<1.2) or (mu2pt>10 & |mu2eta|<1.2)]
        OR  Any muonSV with [max(mu1pt,mu2pt)>4 & min(mu1pt,mu2pt)>3]

ORDERING -- from configs/dqcd/tune0_2024_new.yml, applied before taking slot 0:

    muonSV      keep charge == 0, then sort by chi2 ASCENDING   (best vertex first)
    fourmuonSV  keep charge == 0, then sort by chi2 ASCENDING
    SV          sort by dlen DESCENDING                         (most displaced first)
    Jet         sort by pt   DESCENDING                         (leading jet first)
    Muon        sort by pt   DESCENDING                         (leading muon first)

The four scalars (nMuon, nSV, nmuonSV, nfourmuonSV) are read straight from the file, so
nmuonSV counts vertices BEFORE the charge filter -- that is what the branch holds and
what the BDT was given.

Binning is set by a pre-scan over the first file of each sample: 60 bins between the
0.5 and 99.5 percentiles of the pooled values, or integer bins for the count-like and
index-like variables. Sentinel values (-1 jet/muon indices) fall inside the range and
are kept, since the BDT sees them too.

Run after sourcing setup.sh:
    python3 _tools/compareBDTvars.py [--output path.pdf] [--n-qcd N] [--data-frac F]
                                     [--minbias-frac F] [--no-minbias]
                                     [--test] [--only-vars REGEX]

--test reads 1 file per sample and writes a 5-page PDF: a fast wiring check.
--only-vars takes a regex on the base name, e.g. --only-vars 'muonSV_.*' for 15 pages.

Reading is histogram-streaming: each file is read, filled into the fixed bins and
discarded, so memory stays flat regardless of how much is read. A full run is dominated
by the data draw; 1% of the Parking datasets is several hundred files.
"""

import argparse
import os
import random
import re
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
# Golden-JSON mask, set in main(). CERT is None when disabled or unavailable, in which
# case every data event is kept. MC is never masked.
CERT = None
GCOUNT = gj.Counter()

# "Full" = the intended production configuration: the default QCD cap and the default
# data fraction. Set in main().
FULL_MODE = False


def gj_note():
    return ("  Data: golden JSON applied (certified lumisections)" if CERT is not None
            else "  Data: NO golden JSON applied")


XRD_SERVER = "root://gfe02.grid.hep.ph.ic.ac.uk/"
BASE = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024"
TREE_NAME = "Events"

N_QCD_FILES = 100      # per pT-hat bin (--n-qcd; <=0 reads all)
DATA_FRAC = 0.01       # 1% of the data files (--data-frac)
DATA_SEED = 20240729
QCD_SEED = 0
MINBIAS_FRAC = 0.05    # 5% of the MinBias files (--minbias-frac)
MINBIAS_SEED = 20260806
N_BINS = 60

# Font sizes for THIS page type, deliberately smaller than the cmsstyle house defaults
# (FS_LABEL/FS_AXES = 15, FS_LEGEND = 13). Those are tuned for the sibling scripts' pages,
# which carry two or three curves; this one carries six plus a multi-line partial-sample
# box, and at 15 pt the labels crowd the frame. cmsstyle.py itself is left alone -- it is
# shared with every other compare*.py.
FS_LABEL = 11     # axis titles
FS_AXES = 11      # -> CMS label 12, header 11, tick labels 10
FS_LEGEND = 9     # the curve legend
FS_PARTIAL = 8    # the "Partial sample plot" box (unchanged -- already small)

# ---------------------------------------------------------------------------
# samples
# ---------------------------------------------------------------------------
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

# The MinBias QCD alternative: InclusiveDileptonMinBias with the DoubleMuOS43 generator
# filter, processed by Prijith (2026-07-30). NOT under BASE -- it lives in a different
# user's dCache area -- so this is a full path, not a directory name appended to BASE.
# Same 2024 nanoAOD content as the pT-hat bins except Jet_puIdDisc, which this production
# does not carry; that one page therefore has no MinBias curve (the reader skips branches
# a sample does not have rather than faking a value).
MINBIAS_DIR = ("/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/ppradeep/samples/Parking/Run3/"
               "Nanotronv14/InclusiveDileptonMinBias_Fil-DoubleMuOS43_TuneCP5Plus_13p6TeV"
               "_pythia8/2024WithMET/260730_143555")
MINBIAS_LABEL = "MinBias (incl. dilepton)"


def _sig_dir(scen, ctau, mA_str, mpi):
    scen_dir = "ScenarioA" if scen == "A" else "ScenarioB1"
    return (f"{BASE}/GluGluHToDarkShowers-{scen_dir}_Par-ctau-{ctau}-mA-{mA_str}"
            f"-mpi-{mpi}_TuneCP5_13p6TeV_powheg-pythia8")


# Two (mass point, lifetime) combinations per scenario = 4 signal curves. The mass points
# are the two that compareDeltaR.py puts on its overview page, each at both lifetimes, so
# the pages show the LIFETIME dependence (the displaced-vertex variables are where signal
# and QCD separate, and ctau is what moves them).
SIGNALS = [
    ("scA $m_A$=3.33, $c\\tau$=10 mm",  _sig_dir("A", "10",  "3p33", 10), "#1f77b4"),
    ("scA $m_A$=3.33, $c\\tau$=0.1 mm", _sig_dir("A", "0p1", "3p33", 10), "#7fc0e8"),
    ("scB1 $m_A$=1.33, $c\\tau$=10 mm",  _sig_dir("B1", "10",  "1p33", 4), "#2ca02c"),
    ("scB1 $m_A$=1.33, $c\\tau$=0.1 mm", _sig_dir("B1", "0p1", "1p33", 4), "#90d18f"),
]
DATA_COLOR = "black"
QCD_COLOR = "#d62728"

# Marker convention, shared with compareDeltaR.py: data is a small SOLID black square, the
# two background estimates are WHITE-filled circles. Solid = measured, open = simulated,
# so the two kinds of curve are told apart by shape and fill rather than colour alone.
# White fill rather than unfilled, so a marker masks whatever curve passes under it.
DATA_MARKER, DATA_MARKER_SIZE = "s", 3.5
BKG_MARKER, BKG_MARKER_SIZE = "o", 4.0
MARKER_EDGE = 1.0

# The display label for the pT-hat QCD stack. Kept separate from the "QCD" dict key that
# indexes curves/sumw2, so the wording can change without invalidating a --replot dump.
QCD_LABEL = r"QCD ($\mu$-enriched, $p_T$-binned)"
# Orange, so the two backgrounds read as a pair against the red QCD without colliding with
# the blue/green signal families or the black data.
MINBIAS_COLOR = "#ff7f0e"

# ---------------------------------------------------------------------------
# the 85 BDT base variables, grouped by collection, in the model's own order
# ---------------------------------------------------------------------------
SCALARS = ["nMuon", "nSV", "nmuonSV", "nfourmuonSV"]

COLLECTIONS = {
    # name: (sort branch, ascending?, charge-filter?)
    "Jet":        ("Jet_pt",         False, False),
    "Muon":       ("Muon_pt",        False, False),
    "muonSV":     ("muonSV_chi2",    True,  True),
    "fourmuonSV": ("fourmuonSV_chi2", True, True),
    "SV":         ("SV_dlen",        False, False),
}

VARS = {
    "Jet": ["Jet_pt", "Jet_eta", "Jet_phi", "Jet_chEmEF", "Jet_chHEF", "Jet_neEmEF",
            "Jet_neHEF", "Jet_muEF", "Jet_muonSubtrFactor", "Jet_nMuons",
            "Jet_nElectrons", "Jet_nConstituents", "Jet_puIdDisc", "Jet_muonIdx1",
            "Jet_muonIdx2"],
    "Muon": ["Muon_eta", "Muon_phi", "Muon_pt", "Muon_ptErr", "Muon_dxy", "Muon_dxyErr",
             "Muon_dz", "Muon_dzErr", "Muon_ip3d", "Muon_sip3d", "Muon_charge",
             "Muon_tightId", "Muon_softMva", "Muon_pfRelIso03_all",
             "Muon_miniPFRelIso_all", "Muon_jetIdx"],
    "muonSV": ["muonSV_chi2", "muonSV_pAngle", "muonSV_dlen", "muonSV_dlenSig",
               "muonSV_dxy", "muonSV_dxySig", "muonSV_mu1pt", "muonSV_mu1eta",
               "muonSV_mu1phi", "muonSV_mu2pt", "muonSV_mu2eta", "muonSV_mu2phi",
               "muonSV_x", "muonSV_y", "muonSV_z"],
    "fourmuonSV": ["fourmuonSV_chi2", "fourmuonSV_pAngle", "fourmuonSV_dlen",
                   "fourmuonSV_dlenSig", "fourmuonSV_dxy", "fourmuonSV_dxySig",
                   "fourmuonSV_mu1pt", "fourmuonSV_mu1eta", "fourmuonSV_mu1phi",
                   "fourmuonSV_mu2pt", "fourmuonSV_mu2eta", "fourmuonSV_mu2phi",
                   "fourmuonSV_mu3pt", "fourmuonSV_mu3eta", "fourmuonSV_mu3phi",
                   "fourmuonSV_mu4pt", "fourmuonSV_mu4eta", "fourmuonSV_mu4phi",
                   "fourmuonSV_x", "fourmuonSV_y", "fourmuonSV_z", "fourmuonSV_mass"],
    "SV": ["SV_pt", "SV_eta", "SV_phi", "SV_x", "SV_y", "SV_z", "SV_dxy", "SV_dxySig",
           "SV_dlen", "SV_dlenSig", "SV_pAngle", "SV_chi2", "SV_ndof"],
}

# Variables that are counts / indices / flags -- integer bins, not 60 float bins.
INTEGER_VARS = {"nMuon", "nSV", "nmuonSV", "nfourmuonSV", "Jet_nMuons", "Jet_nElectrons",
                "Jet_nConstituents", "Jet_muonIdx1", "Jet_muonIdx2", "Muon_charge",
                "Muon_tightId", "Muon_jetIdx", "SV_ndof"}

TRIGGERS = ["HLT_Mu10_Barrel_L1HP11_IP6", "HLT_DoubleMu4_3_LowMass"]

# Shown on every page in full mode, in place of the partial-sample banner. Built from the
# same constants the cuts use, so it cannot drift from what was actually applied.
def selection_lines():
    return [
        "Selection (icenet combined-model preselection):",
        "  " + " OR ".join(t.replace("_", r"\_") for t in TRIGGERS),
        r"  Any muonSV: ($p_T^{\mu1}$>10 & $|\eta^{\mu1}|$<1.2) or "
        r"($p_T^{\mu2}$>10 & $|\eta^{\mu2}|$<1.2)",
        r"  OR Any muonSV: max($p_T$)>4 & min($p_T$)>3",
        "  muonSV / fourmuonSV: charge = 0, sorted by $\chi^2$; slot 0 only",
    ]
PRESEL_BRANCHES = ["muonSV_mu1pt", "muonSV_mu1eta", "muonSV_mu2pt", "muonSV_mu2eta"]

_env_proxy = os.environ.get("X509_USER_PROXY", "")
if not (_env_proxy and os.path.exists(_env_proxy)):
    os.environ["X509_USER_PROXY"] = f"/tmp/x509up_u{os.getuid()}"
_XRDFS_ENV = os.environ


def log(msg, **kw):
    print(msg, flush=True, **kw)


def all_base_vars():
    out = list(SCALARS)
    for c in ["Jet", "Muon", "muonSV", "fourmuonSV", "SV"]:
        out.extend(VARS[c])
    return out


def branches_needed():
    """Every branch the reader touches: the 85 variables, the sort keys, the charge
    branches for the two SV filters, the preselection legs and the triggers."""
    need = set(SCALARS)
    for c, vs in VARS.items():
        need.update(vs)
        sort_b, _, charge = COLLECTIONS[c]
        need.add(sort_b)
        if charge:
            need.add(f"{c}_charge")
    need.update(PRESEL_BRANCHES)
    need.update(TRIGGERS)
    return sorted(need)


# ---------------------------------------------------------------------------
# file discovery
# ---------------------------------------------------------------------------
def xrdfs_ls(path, server=None):
    srv = server or XRD_SERVER
    r = subprocess.run(["xrdfs", srv, "ls", "-l", path],
                       capture_output=True, text=True, env=_XRDFS_ENV)
    # A failed listing must never look like an empty directory -- otherwise a node that
    # cannot authenticate silently reads zero files and the run still "succeeds".
    if r.returncode != 0:
        raise RuntimeError(f"xrdfs ls failed for {srv}{path} (rc={r.returncode}). "
                           f"Check X509_USER_PROXY. stderr: {r.stderr.strip()}")
    out = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        out.append((parts[-1], parts[0].startswith("d")))
    return out


def list_root_files(directory, server=None):
    srv = server or XRD_SERVER
    files = []
    for path, is_dir in xrdfs_ls(directory, server=srv):
        if is_dir:
            files.extend(list_root_files(path, server=srv))
        elif path.endswith(".root"):
            files.append(srv + path)
    return files


def collect_data_files():
    """Every .root under the Parking* directories (both PDs pooled)."""
    out = []
    for top, is_dir in xrdfs_ls(BASE):
        name = top.rsplit("/", 1)[-1]
        if is_dir and "Parking" in name:
            found = list_root_files(top)
            log(f"    {name:36s} {len(found):>7,} files")
            out.extend(found)
    return out


# ---------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------
def slot0_values(tree, keys, is_data=False):
    """Read one file and return {base_var: 1-D np.array of the leading-slot value}.

    Events failing the preselection are dropped first. Then each collection is filtered
    and re-ordered as icenet does, and slot 0 is taken. Events whose collection is empty
    after filtering contribute nothing to that collection's variables (the BDT pads them,
    but a padding sentinel is not a measurement and would pile up a fake spike)."""
    import awkward as ak

    need = [b for b in branches_needed() if b in keys]
    if is_data and CERT is not None:
        need = need + [b for b in gj.BRANCHES if b not in need]
    a = tree.arrays(need, library="ak")

    # (0) certified lumisections -- DATA only; MC has no meaningful run/lumisection
    if is_data and CERT is not None:
        keep = GCOUNT.update(gj.mask(ak.to_numpy(a["run"]),
                                     ak.to_numpy(a["luminosityBlock"]), CERT))
        a = a[keep]
        if len(a) == 0:
            return {}

    # (1) trigger OR -- a missing trigger branch counts as not fired
    trig = None
    for t in TRIGGERS:
        if t in keys:
            trig = a[t] if trig is None else (trig | a[t])
    if trig is None:
        return {}
    a = a[trig]
    if len(a) == 0:
        return {}

    # (2) kinematic legs, event level (Any over muonSV)
    if all(b in keys for b in PRESEL_BRANCHES):
        mu10 = ak.sum(((a["muonSV_mu1pt"] > 10.0) & (abs(a["muonSV_mu1eta"]) < 1.2)) |
                      ((a["muonSV_mu2pt"] > 10.0) & (abs(a["muonSV_mu2eta"]) < 1.2)), -1) > 0
        dmu = ak.sum((np.maximum(a["muonSV_mu1pt"], a["muonSV_mu2pt"]) > 4.0) &
                     (np.minimum(a["muonSV_mu1pt"], a["muonSV_mu2pt"]) > 3.0), -1) > 0
        a = a[mu10 | dmu]
    if len(a) == 0:
        return {}

    def _clean(x):
        """awkward -> plain float64, with the option-type slots dropped.

        ak.firsts() returns an OPTION type, so ak.to_numpy() hands back a MaskedArray.
        np.percentile and np.histogram both ignore the mask and silently consume the
        underlying fill values, which are arbitrary -- so the mask has to be applied
        here, not left for numpy to discard. Non-finite entries go the same way."""
        y = ak.to_numpy(x)
        y = y.compressed() if np.ma.isMaskedArray(y) else np.asarray(y)
        y = y.astype(np.float64)
        return y[np.isfinite(y)]

    out = {}
    for s in SCALARS:
        if s in keys:
            out[s] = _clean(a[s])

    for coll, vlist in VARS.items():
        sort_b, ascending, charge = COLLECTIONS[coll]
        if sort_b not in keys:
            continue
        idx_ok = ak.ones_like(a[sort_b], dtype=bool)
        if charge and f"{coll}_charge" in keys:
            idx_ok = a[f"{coll}_charge"] == 0
        key = a[sort_b][idx_ok]
        order = ak.argsort(key, axis=-1, ascending=ascending)
        keep = ak.num(key, axis=-1) > 0
        if not ak.any(keep):
            continue
        for v in vlist:
            if v not in keys:
                continue
            col = a[v][idx_ok][order][keep]
            out[v] = _clean(ak.firsts(col))
    return out


def read_files(urls, label, ranges=None, hists=None, sumw2=None, weight=1.0,
               scan_only=False, scan_store=None, is_data=False):
    """Stream *urls*. If scan_only, stash values for range-finding; else fill *hists*.

    *sumw2* accumulates sum(w^2) per bin alongside sum(w), which is what the error bars
    need. For an unweighted sample (weight=1) it equals the raw count, so the error is the
    plain sqrt(N); for QCD, where the 12 pT-hat bins enter with weights spanning six
    orders of magnitude, sum(w) alone cannot give an uncertainty -- a bin fed by a handful
    of high-weight low-pT events has a large error that the summed curve hides completely.
    It has to be accumulated here; it is not recoverable from the finished histogram."""
    import uproot
    n = len(urls)
    n_ev = 0
    for i, url in enumerate(urls, 1):
        if i == 1 or i % 25 == 0 or i == n:
            log(f"    [{i}/{n}] {label}")
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                vals = slot0_values(tree, set(tree.keys()), is_data=is_data)
        except Exception as e:
            log(f"    [warn] {label}: {url.rsplit('/', 1)[-1]}: {e}", file=sys.stderr)
            continue
        if not vals:
            continue
        n_ev += max((len(v) for v in vals.values()), default=0)
        if scan_only:
            for k, v in vals.items():
                if len(v):
                    scan_store.setdefault(k, []).append(v[:20000])
        else:
            for k, v in vals.items():
                if k not in ranges or not len(v):
                    continue
                edges = ranges[k]
                # Clip into the axis rather than discarding: the range is a 0.5-99.5
                # percentile, and the fraction living outside it differs a lot between
                # samples (the high-pT QCD bins especially). Dropping those entries would
                # renormalise each curve over a different subset and quietly distort the
                # very comparison the page exists to make. Overflow therefore piles into
                # the edge bins, as it would in any HEP plot.
                h, _ = np.histogram(np.clip(v, edges[0], edges[-1]), bins=edges)
                hists[k] = hists.get(k, np.zeros(len(edges) - 1)) + h * weight
                if sumw2 is not None:
                    sumw2[k] = sumw2.get(k, np.zeros(len(edges) - 1)) + h * weight ** 2
    return n_ev


# ---------------------------------------------------------------------------
# binning
# ---------------------------------------------------------------------------
def build_ranges(scan):
    """60 bins per variable, integer bins for the count/index variables.

    *scan* is {sample_label: {var: [chunks]}}. The range is the MEDIAN across samples of
    each sample's own (0.5, 99.5) percentiles -- NOT the percentile of everything pooled.
    Pooling is what a first version did and it is wrong here: the scan reads one file per
    sample, so the tiny-cross-section QCD bins (PT-1000 and friends) enter with the same
    weight as the low-pT ones that actually dominate the physical QCD mixture. Their long
    tails then set the upper edge -- Jet_pt ran to 1.6 TeV -- and squashed data, signal
    and the whole low-pT QCD bulk into the first couple of bins. Taking the median over
    samples makes one extreme sample unable to blow out the axis."""
    ranges, scales = {}, {}
    for v in all_base_vars():
        los, his, meds, iqrs, q3s, n_tot, neg = [], [], [], [], [], 0, False
        for store in scan.values():
            chunks = store.get(v, [])
            if not chunks:
                continue
            xs = np.concatenate(chunks)
            xs = xs[np.isfinite(xs)]
            if len(xs) < 10:
                continue
            n_tot += len(xs)
            neg = neg or bool(np.any(xs < 0))
            q1, med, q3 = np.percentile(xs, [25, 50, 75])
            los.append(np.percentile(xs, 0.5))
            his.append(np.percentile(xs, 99.5))
            meds.append(med)
            iqrs.append(q3 - q1)
            q3s.append(q3)
        if not los or n_tot < 10:
            continue
        lo_m, hi_m = float(np.median(los)), float(np.median(his))
        q3_m = float(np.median(q3s))

        # LOG or LINEAR? Some of these variables (the chi2s, the significances, sip3d)
        # have a bulk below ~100 and a REAL tail reaching 1e5-1e6 -- checked against the
        # data, the tail is not an artefact and 99% of Data genuinely occupies the whole
        # span. No linear axis can show both, and capping the range would throw the tail
        # into an overflow bin. Those get log bins instead, which is the usual treatment
        # for a chi2 anyway. Everything bounded (eta, phi, the energy fractions, the
        # counts) stays linear.
        if (not neg) and q3_m > 0 and hi_m / q3_m > 50 and v not in INTEGER_VARS:
            hi_l = hi_m                       # keep the tail: no IQR cap on a log axis
            lo_l = lo_m if lo_m > 0 else hi_l * 1e-6
            lo_l = max(lo_l, hi_l * 1e-6)     # floor, so chi2 == 0 has somewhere to clip
            if hi_l > lo_l > 0:
                ranges[v] = np.logspace(np.log10(lo_l), np.log10(hi_l), N_BINS + 1)
                scales[v] = "log"
                continue

        # Heavy tails: a percentile alone is not enough. muonSV_chi2 has a p99.5 of
        # ~850,000 while its bulk sits below ~100, so a percentile-only axis put >97% of
        # every curve in the first bin and the page said nothing. Cap the edges with an
        # IQR envelope, which tracks the bulk and ignores the tail; the min/max with the
        # percentile keeps well-behaved bounded variables (eta, phi, the fractions)
        # exactly as they were.
        med_m, iqr_m = float(np.median(meds)), float(np.median(iqrs))
        if iqr_m > 0:
            hi_m = min(hi_m, med_m + 8.0 * iqr_m)
            lo_m = max(lo_m, med_m - 8.0 * iqr_m)
        if not neg:
            lo_m = max(lo_m, 0.0)   # no negative axis for a quantity that is never < 0
        # a single representative array, only for the integer-vs-float decision below
        x = np.array([lo_m, hi_m])
        if v in INTEGER_VARS:
            lo, hi = np.floor(lo_m), np.ceil(hi_m)
            hi = max(hi, lo + 1)
            if hi - lo > 60:
                ranges[v] = np.linspace(lo, hi, N_BINS + 1)
            else:
                ranges[v] = np.arange(lo - 0.5, hi + 1.5, 1.0)
        else:
            lo, hi = lo_m, hi_m
            if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
                continue
            pad = 0.02 * (hi - lo)
            lo_p = lo - pad
            if not neg:
                lo_p = max(lo_p, 0.0)   # the pad must not push the axis below zero either
            ranges[v] = np.linspace(lo_p, hi + pad, N_BINS + 1)
        scales.setdefault(v, "linear")
    return ranges, scales


# ---------------------------------------------------------------------------
# plotting
# ---------------------------------------------------------------------------
def draw_page(pdf, var, edges, curves, partial, scale="linear", errors=False):
    """One page: unit-area shapes of *curves* = [(label, hist, sumw2, colour, is_data)].

    With *errors*, each curve carries a +/-1 sigma band, sqrt(sum w^2)/sum(w) on the
    normalised value. The denominator's own uncertainty is ignored, as usual for a shape
    plot -- it is a global scale, not a per-bin wobble."""
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    centres = 0.5 * (edges[:-1] + edges[1:])
    any_data = False

    for label, h, s2, colour, is_data, is_bkg in curves:
        tot = h.sum()
        if tot <= 0:
            continue
        y = h / tot
        any_data = True
        lw = 1.8 if is_data else 1.4
        z = 5 if is_data else 2
        mk = {}
        if is_data:
            mk = dict(marker=DATA_MARKER, markersize=DATA_MARKER_SIZE,
                      markerfacecolor=colour, markeredgecolor=colour,
                      markeredgewidth=MARKER_EDGE)
        elif is_bkg:
            mk = dict(marker=BKG_MARKER, markersize=BKG_MARKER_SIZE,
                      markerfacecolor="white", markeredgecolor=colour,
                      markeredgewidth=MARKER_EDGE)
        # drawstyle, not ax.step(): ax.step cannot carry markers, and steps-mid draws the
        # identical line. Signals stay unmarked -- there are four of them and marking every
        # curve would turn the page into texture.
        ax.plot(centres, y, drawstyle="steps-mid", color=colour, lw=lw, label=label,
                zorder=z, **mk)
        if errors and s2 is not None:
            err = np.sqrt(np.maximum(s2, 0.0)) / tot
            # the y axis is log, so the lower edge has to stay strictly positive
            lo = np.where(y - err > 0, y - err, y * 1e-3)
            ax.fill_between(centres, lo, y + err, step="mid", color=colour,
                            alpha=cms.BAND_ALPHA, lw=0, zorder=z - 1)

    ax.set_xscale(scale)
    ax.set_xlabel(var, fontsize=FS_LABEL)
    ax.set_ylabel("Fraction of entries / bin", fontsize=FS_LABEL)
    ax.set_yscale("log")
    ax.set_xlim(edges[0], edges[-1])
    cms.cms_axes(ax, header=cms.lumi_header(), fontsize=FS_AXES,
                 label=cms.CMS_LABEL_DATA)
    if any_data:
        cms.extend_log_top(ax, frac=0.62)
        ax.legend(loc="upper right", fontsize=FS_LEGEND, **cms.LEGEND_KW)
        # In full mode the file caps ARE the intended configuration, not a shortfall, so
        # the partial-sample banner is noise -- the selection is the useful thing to state.
        if FULL_MODE:
            cms.info_legend(ax, selection_lines() + [gj_note()],
                            loc="upper left", fontsize=FS_PARTIAL)
        else:
            cms.partial_samples_legend(ax, partial, loc="upper left", fontsize=FS_PARTIAL)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def write_pdf(path, want, ranges, scales, curves, sumw2, partial, errors=False):
    """One page per variable, in the model's own variable order."""
    # (dict key, display label, colour, is_data, is_background)
    order = [("Data", "Data", DATA_COLOR, True, False),
             ("QCD", QCD_LABEL, QCD_COLOR, False, True),
             (MINBIAS_LABEL, MINBIAS_LABEL, MINBIAS_COLOR, False, True)] + \
            [(l, l, c, False, False) for l, _, c in SIGNALS]
    log(f"\n=== writing {path} ({len(want)} pages, errors={errors}) ===")
    with PdfPages(path) as pdf:
        for v in want:
            nb = len(ranges[v]) - 1
            page = [(label,
                     curves.get(key, {}).get(v, np.zeros(nb)),
                     sumw2.get(key, {}).get(v),
                     colour, is_data, is_bkg)
                    for key, label, colour, is_data, is_bkg in order]
            draw_page(pdf, v, ranges[v], page, partial,
                      scale=scales.get(v, "linear"), errors=errors)
    log(f"wrote {path}")


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--output", default="compareBDTvars.pdf")
    p.add_argument("--n-qcd", type=int, default=N_QCD_FILES,
                   help=f"files per QCD pT-hat bin (default {N_QCD_FILES}; <=0 = all)")
    p.add_argument("--n-signal", type=int, default=0,
                   help="files per signal point (default 0 = all)")
    p.add_argument("--data-frac", type=float, default=DATA_FRAC,
                   help=f"fraction of data files (default {DATA_FRAC} = 1%%)")
    p.add_argument("--data-seed", type=int, default=DATA_SEED)
    p.add_argument("--qcd-seed", type=int, default=QCD_SEED)
    p.add_argument("--minbias-frac", type=float, default=MINBIAS_FRAC,
                   help=f"fraction of MinBias files (default {MINBIAS_FRAC} = 5%%)")
    p.add_argument("--minbias-seed", type=int, default=MINBIAS_SEED)
    p.add_argument("--no-minbias", action="store_true",
                   help="skip the MinBias sample entirely")
    p.add_argument("--only-vars", default=None, help="regex on the base variable name")
    p.add_argument("--test", action="store_true",
                   help="1 file per sample, 5 pages -- a wiring check")
    p.add_argument("--dump", default=None, metavar="PATH.npz",
                   help="also save the filled histograms, so the PDF can be redrawn "
                        "later without re-reading anything")
    p.add_argument("--replot", default=None, metavar="PATH.npz",
                   help="skip all reading and redraw the PDF from a --dump file. The "
                        "read is hours; a font or range tweak should not cost that twice.")
    p.add_argument("--errors", action="store_true",
                   help="draw a +/-1 sigma band on every curve (sqrt(sum w^2)/sum w). "
                        "Needs sum(w^2), so a dump made before this option existed "
                        "cannot be replotted with it.")
    p.add_argument("--full-legend", action="store_true",
                   help="Show the selection summary instead of the partial-sample banner "
                        "even on a reduced run (for previewing it)")
    gj.add_args(p)
    args = p.parse_args()
    global CERT, FULL_MODE
    CERT = gj.from_args(args, log)
    # --test overrides the file counts internally without touching args.n_qcd /
    # args.data_frac, so those alone would call a test run "full". Exclude it explicitly.
    FULL_MODE = args.full_legend or (
        not args.test and args.n_qcd >= N_QCD_FILES and args.data_frac >= DATA_FRAC
        and (args.no_minbias or args.minbias_frac >= MINBIAS_FRAC))
    if FULL_MODE:
        why = ("forced by --full-legend" if args.full_legend
               else f"{args.n_qcd} files/QCD bin, {100 * args.data_frac:g}% of data, "
                    f"{100 * args.minbias_frac:g}% of MinBias")
        log(f"[FULL MODE] {why} -- partial-sample banner replaced by the selection summary")

    if args.replot:
        z = np.load(args.replot, allow_pickle=True)
        curves = z["curves"].item()
        ranges = z["ranges"].item()
        scales = z["scales"].item() if "scales" in z else {}
        sumw2 = z["sumw2"].item() if "sumw2" in z else {}
        partial = [tuple(t) for t in z["partial"].tolist()]
        cms.set_lumi_files(int(z["lumi_read"]), int(z["lumi_avail"]))
        if args.errors and not sumw2:
            sys.exit(f"{args.replot} has no sum(w^2) -- it predates --errors. Re-run the "
                     f"fill to get error bands.")
        want = [v for v in all_base_vars() if v in ranges]
        if args.only_vars:
            rx = re.compile(args.only_vars)
            want = [v for v in want if rx.search(v)]
        log(f"replotting {len(want)} page(s) from {args.replot}")
        write_pdf(args.output, want, ranges, scales, curves, sumw2, partial,
                  errors=args.errors)
        return

    want = all_base_vars()
    if args.only_vars:
        rx = re.compile(args.only_vars)
        want = [v for v in want if rx.search(v)]
        if not want:
            sys.exit(f"--only-vars {args.only_vars!r} matched none of the 85 variables")
    if args.test:
        want = want[:5]
    log(f"plotting {len(want)} variable(s), leading slot only")

    # ---- file lists -------------------------------------------------------
    log("\n=== file discovery ===")
    samples = []   # (label, urls, colour, is_data, weight, n_avail)

    log("  DATA")
    all_data = collect_data_files()
    n_pick = max(1, round(args.data_frac * len(all_data)))
    if args.test:
        n_pick = 1
    picked = random.Random(args.data_seed).sample(all_data, n_pick)
    log(f"    {len(all_data):,} data files total; reading a random "
        f"{100 * n_pick / len(all_data):.3f}% = {n_pick:,} (seed {args.data_seed})")
    cms.set_lumi_files(n_pick, len(all_data))
    samples.append(("Data", picked, DATA_COLOR, True, 1.0, len(all_data)))

    log("  QCD")
    qcd_parts = []
    for d, xs in QCD_XS.items():
        files = list_root_files(f"{BASE}/{d}")
        n = len(files) if args.n_qcd <= 0 else min(args.n_qcd, len(files))
        if args.test:
            n = 1
        sub = random.Random(args.qcd_seed).sample(files, n) if n < len(files) else files
        # scale each bin by files_available/files_read so the xs-weighted mixture is the
        # estimated whole-sample shape, not just the shape of what was read
        w = xs * (len(files) / max(1, n))
        qcd_parts.append((d, sub, w, len(files)))
        log(f"    {d.split('_Fil')[0]:28s} {n:>5,} of {len(files):>6,} files")

    log("  MINBIAS")
    # A seeded RANDOM draw, not the first N: the sample is split over 0000/0001/0002
    # production subdirectories, so taking the head of the listing would read one
    # subdirectory only -- a subset of the jobs, not a subset of the sample.
    mb_files, mb_avail = [], 0
    if not args.no_minbias:
        all_mb = list_root_files(MINBIAS_DIR)
        if not all_mb:
            sys.exit(f"[error] no .root files under {MINBIAS_DIR} -- check the path/proxy. "
                     f"Pass --no-minbias to run without it.")
        mb_avail = len(all_mb)
        n_mb = 1 if args.test else max(1, round(args.minbias_frac * mb_avail))
        mb_files = (random.Random(args.minbias_seed).sample(all_mb, n_mb)
                    if n_mb < mb_avail else all_mb)
        log(f"    {MINBIAS_LABEL:34s} {len(mb_files):>5,} of {mb_avail:>6,} files "
            f"({100 * len(mb_files) / mb_avail:.2f}%, seed {args.minbias_seed})")

    log("  SIGNAL")
    sig_parts = []
    for label, d, colour in SIGNALS:
        files = list_root_files(d)
        n = len(files) if args.n_signal <= 0 else min(args.n_signal, len(files))
        if args.test:
            n = 1
        sub = files[:n]
        sig_parts.append((label, sub, colour, len(files)))
        log(f"    {label:34s} {n:>5,} of {len(files):>6,} files")

    # ---- pass 1: ranges ---------------------------------------------------
    log("\n=== pass 1: binning scan (first file of each sample) ===")
    # kept PER SAMPLE: build_ranges takes the median of the samples' own percentiles, so
    # one extreme sample cannot set the axis for everybody (see build_ranges)
    scan = {}
    scan["Data"] = {}
    read_files(picked[:1], "Data", scan_only=True, scan_store=scan["Data"],
               is_data=True)
    for d, sub, w, _ in qcd_parts:
        name = d.split("_Fil")[0]
        scan[name] = {}
        read_files(sub[:1], name, scan_only=True, scan_store=scan[name])
    if mb_files:
        # MinBias joins the scan on the same footing as every other sample: build_ranges
        # takes the MEDIAN of the per-sample percentiles, so leaving it out would let an
        # axis be set without ever having seen the sample it now has to display, and any
        # MinBias tail beyond that axis would silently pile into the edge bin.
        scan[MINBIAS_LABEL] = {}
        read_files(mb_files[:1], MINBIAS_LABEL, scan_only=True,
                   scan_store=scan[MINBIAS_LABEL])
    for label, sub, colour, _ in sig_parts:
        scan[label] = {}
        read_files(sub[:1], label, scan_only=True, scan_store=scan[label])
    ranges, scales = build_ranges(scan)
    n_log = sum(1 for s in scales.values() if s == "log")
    log(f"  {n_log} variable(s) get a log x-axis (heavy tail), "
        f"{len(ranges) - n_log} linear")
    missing = [v for v in want if v not in ranges]
    if missing:
        log(f"  [warn] no binning for {len(missing)} variable(s) (no entries in the "
            f"scan): {missing}", file=sys.stderr)
    want = [v for v in want if v in ranges]
    log(f"  binned {len(want)} variable(s)")

    # ---- pass 2: fill -----------------------------------------------------
    log("\n=== pass 2: filling ===")
    curves = {}          # label -> {var: sum of weights per bin}
    sumw2 = {}           # label -> {var: sum of weights^2 per bin}  (for the error bands)
    partial = []         # (name, read, available) for the in-plot legend

    h, s2 = {}, {}
    n_ev = read_files(picked, "Data", ranges=ranges, hists=h, sumw2=s2,
                      is_data=True)
    curves["Data"], sumw2["Data"] = h, s2
    partial.append(("Data", n_pick, len(all_data)))
    log(f"  Data: {n_ev:,} selected events")

    hq, s2q = {}, {}
    qcd_read = qcd_avail = 0
    for d, sub, w, avail in qcd_parts:
        read_files(sub, d.split("_Fil")[0], ranges=ranges, hists=hq, sumw2=s2q, weight=w)
        qcd_read += len(sub)
        qcd_avail += avail
    curves["QCD"], sumw2["QCD"] = hq, s2q
    # one summary line for all 12 pT-hat bins: listing them individually made a 17-line
    # legend that covered the plot, and every bin is read at the same per-bin cap anyway
    partial.append((f"QCD ({len(qcd_parts)} pT bins)", qcd_read, qcd_avail))

    if mb_files:
        hmb, s2mb = {}, {}
        n_ev = read_files(mb_files, MINBIAS_LABEL, ranges=ranges, hists=hmb, sumw2=s2mb)
        curves[MINBIAS_LABEL], sumw2[MINBIAS_LABEL] = hmb, s2mb
        partial.append((MINBIAS_LABEL, len(mb_files), mb_avail))
        log(f"  {MINBIAS_LABEL}: {n_ev:,} selected events")

    for label, sub, colour, avail in sig_parts:
        hs, s2s = {}, {}
        n_ev = read_files(sub, label, ranges=ranges, hists=hs, sumw2=s2s)
        curves[label], sumw2[label] = hs, s2s
        partial.append((label, len(sub), avail))
        log(f"  {label}: {n_ev:,} selected events")

    # ---- write ------------------------------------------------------------
    if args.dump:
        read, avail = cms.LUMI_FILES if cms.LUMI_FILES else (n_pick, len(all_data))
        np.savez_compressed(args.dump, curves=np.array(curves, dtype=object),
                            sumw2=np.array(sumw2, dtype=object),
                            ranges=np.array(ranges, dtype=object),
                            scales=np.array(scales, dtype=object),
                            partial=np.array(partial, dtype=object),
                            lumi_read=read, lumi_avail=avail)
        log(f"dumped histograms to {args.dump} (redraw with --replot)")

    # Both deliverables from the one read: the plain shapes, and the same shapes with
    # +/-1 sigma bands. --errors picks which one a single call makes; here we want both,
    # and the with-errors name is derived from --output so they sit side by side.
    write_pdf(args.output, want, ranges, scales, curves, sumw2, partial, errors=False)
    err_out = re.sub(r"\.pdf$", "", args.output) + "_withErrors.pdf"
    write_pdf(err_out, want, ranges, scales, curves, sumw2, partial, errors=True)


if __name__ == "__main__":
    main()
