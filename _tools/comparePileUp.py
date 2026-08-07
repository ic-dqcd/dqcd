#!/usr/bin/env python3
"""Pileup-reweighting cross-checks for 2024 -- which PU weights to use, and do they apply.

Purpose: settle the open `puWeight` item for run3_2024.py. `modules/puWeight.py` still
points `puWeight_parking2024RDF` at the 2018 inputs (mcPileup2018.root /
data_parking18_with_var.root), so the 2024 chain currently reweights MC to the wrong year.
Three candidate replacements exist, and this script measures the differences between them
instead of arguing about them:

  central   /cvmfs/cms-griddata.cern.ch/cat/metadata/LUM/Run3-24...-Summer24-NanoAODv15/
            POG-maintained, versioned, era-split (B..I, CDEFGHI, BCDEFGHI). This is what
            the upstream Corrections/LUM/python/puCorrections.yaml now points at.
  repo      data/puWeights_2024.json.gz in cms-phys-ciemat/lum-corrections -- a stopgap
            from Aug 2025, made while the central 2024 payload did not yet exist. No
            longer referenced by that repo's own yaml.
  by hand   building the data profile from the certification histograms and the MC profile
            from QCD nTrueInt. Not implemented here: pages 1 and 5 show it is unnecessary.

NOTE the local Corrections/LUM checkout (Jul 2025) still has `fullYear2024` pointing at
the 2023_Summer23BPix file, with puCorrections.py printing "2024 PU weights not yet
available!". That warning is stale but the placeholder is live -- enabling the module
as-is silently applies 2023 weights. Page 3 quantifies what that costs.

The pages:

  1  MC nTrueInt profile, signal points vs QCD bins vs MinBias. If these agree, ONE MC
     profile serves every sample and no per-dataset handling is needed -- which matters
     because puWeightParkingRDF receives only isMC/year/isUL, with no dataset context.
     MinBias is a separate production from the pT-hat bins, so it is the sharpest test
     the page has of whether the premix library really is common to everything.
  2  The central 2024 weights (nominal/up/down) with the MC profile behind them, so the
     size of the correction is read against where the MC statistics actually are.
  3  Weight sources compared: repo vs central CDEFGHI vs central BCDEFGHI, with a ratio
     panel. This is where the repo file's truncation shows up.
  4  Per-era central weights (B..I) against the combined set -- the handle on the
     era-dependent trigger menu that a single merged histogram cannot give.
  5  Closure: MC nTrueInt before and after reweighting, and the implied data profile.
     <w> per sample is the test of whether the central weights assume THIS MC profile;
     it must come out at 1 if they do.
  6  The same closure, but in PV_npvsGood and WITH DATA. Page 5 cannot carry data: its x
     axis is Pileup_nTrueInt, a generator-level quantity absent from the parking nanoAOD.
     PV_npvsGood is the pileup observable data and MC share, so this is the page that
     says whether the correction actually improves data/MC agreement.
  7  The same data, split by era. The file draw is uniform over FILES, so eras enter the
     merged distribution weighted by file count, while the central weights are golden-JSON
     LUMINOSITY-weighted. Those are different averages over eras whose pileup genuinely
     differs, so page 6's residual can be an averaging effect rather than a bad weight --
     this page separates the two and locates any low-pileup population.
  8  One panel per era: data(era) vs MC reweighted with THAT era's own weights, with the
     combined correction drawn alongside. This is the only form of the test free of the
     averaging mismatch, and so the only one that can say whether the inclusive weights
     are genuinely wrong for parking.

CAVEAT on the data: files are drawn uniformly, so eras enter weighted by FILE COUNT, not
by luminosity, and ParkingSingleMuon + ParkingDoubleMuonLowMass are POOLED by default
(--data-streams). An event firing both triggers lives in both PDs and is counted twice.

What this does NOT settle: the central weights are golden-JSON inclusive, so they describe
all collisions, not the subset written to the parking datasets. If the parking trigger rate
varies with instantaneous luminosity within a fill, the parking PU spectrum is shifted and
these are the wrong weights -- the question that motivated deriving them by hand for 2018.
Page 6 is the cheap handle on it: a residual data/MC disagreement in npvsGood AFTER
reweighting is what an inclusive-vs-parking mismatch would look like. It is suggestive, not
conclusive -- npvsGood also folds in vertex reconstruction efficiency.

Run after sourcing setup.sh:
    python3 _tools/comparePileUp.py [--test] [--output path.pdf] [--no-publish]

Only shapes are plotted, so the heavy samples are capped rather than read whole: QCD at
--n-qcd-files (100) per bin even on a full run, MinBias at --minbias-frac (10%) of its
files, and data at --data-frac (0.1%) of the files, both drawn at random from a fixed seed.
The QCD and MinBias caps are the INTENDED configuration, not a shortfall -- both profiles
are converged long before them -- so neither is flagged as a partial sample. Signal is
not capped that way: a short signal read is a real shortfall and is still flagged.

The two backgrounds are never summed. "MC" on pages 2-8 means the QCD pT-hat profile;
MinBias is drawn alongside it as its own curve -- a dashed edge over the shaded QCD band
on pages 2-4, and a dashed line against QCD's solid one on pages 5-6. They come from
independent productions, so any disagreement between them is information, and a sum
(which is weighted by however many files each contributed) would hide it.
"""

import argparse
import json
import math
import os
import random
import re
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import cmsstyle as cms

XRD_SERVER = "root://gfe02.grid.hep.ph.ic.ac.uk/"
BASE = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024"
TREE_NAME = "Events"

WEBDIR = "/home/hep/jtafoyav/public_html/parking/2024/kinematic_checks"

# The central payload. "latest" is a symlink inside the campaign directory; pin a dated
# version instead if a result ever needs to be exactly reproducible.
CENTRAL_DIR = ("/cvmfs/cms-griddata.cern.ch/cat/metadata/LUM/"
               "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/latest")

# The lum-corrections stopgap. Fetched on demand; page 3 is skipped if it cannot be had.
REPO_JSON_URL = ("https://gitlab.cern.ch/cms-phys-ciemat/lum-corrections/-/raw/main/"
                 "data/puWeights_2024.json.gz")
REPO_JSON_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "data", "puWeights_2024_lumcorrections.json.gz")

# Bin per unit of nTrueInt, matching the correctionlib binning (integer edges, 0-99), so
# the profile and the weight curve are sampled on exactly the same grid.
PU_BINS = np.arange(0.0, 100.0, 1.0)
PU_CENTRES = 0.5 * (PU_BINS[1:] + PU_BINS[:-1])

# Reconstructed good primary vertices. This is the ONLY pileup observable data has --
# Pileup_nTrueInt is generator-level and absent from the parking nanoAOD -- so it is the
# variable in which the correction can actually be validated against data (page 6).
NPV_BINS = np.arange(0.0, 101.0, 1.0)
NPV_CENTRES = 0.5 * (NPV_BINS[1:] + NPV_BINS[:-1])

N_FILES_DEFAULT = 3          # per sample; the PU profile converges very fast
N_SIGNAL_POINTS = 4          # how many of SIGNAL_POINTS to use


def _sdir(dirname):
    return f"{BASE}/{dirname}_TuneCP5_13p6TeV_powheg-pythia8"


def _signal_point(scenario, mA, mpi, mA_str, ctau="10", ctau_str="10 mm"):
    """One signal point, named and located exactly as in compareDeltaR.py.

    Same helper shape as that script's _mp(), so the two tools label the same physics the
    same way and a point can be moved between them by copying one line."""
    scen_dir = "ScenarioA" if scenario == "A" else "ScenarioB1"
    ctag = "scA" if scenario == "A" else "scB1"
    return (rf"{ctag} $m_\pi$={mpi}, $m_A$={mA:g}, $c\tau$={ctau_str}",
            _sdir(f"GluGluHToDarkShowers-{scen_dir}_Par-ctau-{ctau}-mA-{mA_str}-mpi-{mpi}"))


# Two Scenario A and two Scenario B1 points, taken from compareDeltaR.py's MASS_POINTS and
# spanning the lowest and highest mA of each scenario. The pileup profile is a property of
# the premix library, not of the signal model, so these serve to demonstrate exactly that
# -- and using the same points as the dR study keeps the two comparable.
SIGNAL_POINTS = [
    _signal_point("A",  0.40, 4,  "0p40"),
    _signal_point("A",  3.33, 10, "3p33"),
    _signal_point("B1", 0.33, 1,  "0p33"),
    _signal_point("B1", 1.67, 5,  "1p67"),
]

# QCD bins spanning the pT range. The profile is a property of the premix library, not of
# the hard process, so a handful either side of the range is enough to show that.
QCD_BINS = ["15to20", "80to120", "170to300", "1000"]


def qcd_label(b):
    """"15to20" -> QCD, pT in (15,20) GeV.  The open-ended top bin is "1000" (=1000toInf),
    which has no upper edge to quote."""
    if "to" in b:
        lo, hi = b.split("to")
        return rf"QCD, $p_{{T}}\in({lo},{hi})$ GeV"
    return rf"QCD, $p_{{T}}>{b}$ GeV"

# QCD bins hold thousands of files each. Only shapes are plotted, so reading all of them
# buys nothing but hours -- this caps QCD even on a "full" (--n-files 0) run.
QCD_MAX_FILES = 100

# The MinBias QCD alternative: InclusiveDileptonMinBias with the DoubleMuOS43 generator
# filter, processed by Prijith (2026-07-30). A full path, not a directory under BASE --
# it lives in a different user's dCache area.
MINBIAS_DIR = ("/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/ppradeep/samples/Parking/Run3/"
               "Nanotronv14/InclusiveDileptonMinBias_Fil-DoubleMuOS43_TuneCP5Plus_13p6TeV"
               "_pythia8/2024WithMET/260730_143555")
MINBIAS_LABEL = "MinBias, incl. dilepton"
# Green: SIG_COLORS is a blue family and QCD_COLORS a red-to-orange one, so an orange here
# would read as a 5th QCD bin on page 1 -- which is exactly the comparison the page exists
# to make, and so exactly the thing the colour must not blur.
MINBIAS_COLOR = "#2ca02c"
# Capped by FRACTION rather than by a file count, because the point of the cap here is to
# read a representative slice of a ~2000-file sample rather than a fixed budget. 10% is
# ~200 files and several million events -- far more than a pileup SHAPE needs, which is
# why this cap (like the QCD one) counts as the intended configuration rather than a
# shortfall, and so suppresses the partial-sample banner. See SAMPLE_CAPS_ARE_COMPLETE.
MINBIAS_FRAC = 0.10
MINBIAS_SEED = 20260806

# Sample kinds whose cap IS the intended configuration, not a shortfall. Only shapes are
# plotted on every page of this document, and both of these converge long before their
# caps, so labelling them "partial" would be misleading rather than careful: it invites
# the reader to discount a curve that is in fact fully converged. Signal is NOT in here --
# it is read whole on a full run, so if it is short, that IS a shortfall worth flagging.
SAMPLE_CAPS_ARE_COMPLETE = {"qcd", "minbias"}

# Fraction of the data files to read for page 6, and the seed that makes the draw
# reproducible. 0.1% is already millions of events, far more than a shape needs.
DATA_FRAC = 0.001
DATA_SEED = 20240728

# Golden certification. Filtering is LUMISECTION-level, not run-level: the low-pileup
# events seen on pages 7-8 sit inside runs whose overall mean is normal, so a run-level
# test cannot remove them. From
# https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions24/
GOLDEN_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data", "Cert_Collisions2024_378981_386951_Golden.json")

ERAS = ["B", "C", "D", "E", "F", "G", "H", "I"]
ERA_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
              "#9467bd", "#8c564b", "#e377c2", "#17becf"]

SIG_COLORS = ["#1f77b4", "#4c9fd4", "#7fc0e8", "#b3ddf5"]
QCD_COLORS = ["#d62728", "#e8593a", "#f2865c", "#f8b18a"]

# One page geometry for every single-plot page (with or without a ratio/summary panel),
# so the PDF does not change shape as you page through it. The multi-panel grid on page 8
# is deliberately exempt -- it scales with the number of panels.
PAGE_SIZE = (10, 9)

SYST_STYLE = {"nominal": ("black", "-", 2.2),
              "up":      ("crimson", "--", 1.6),
              "down":    ("royalblue", "--", 1.6)}

_env_proxy = os.environ.get("X509_USER_PROXY", "")
if not (_env_proxy and os.path.exists(_env_proxy)):
    os.environ["X509_USER_PROXY"] = f"/tmp/x509up_u{os.getuid()}"
_XRDFS_ENV = os.environ


def log(msg, **kwargs):
    print(msg, flush=True, **kwargs)


# ----------------------------------------------------------------------------
# file discovery (same approach as compareDeltaR.py / compareEta.py)
# ----------------------------------------------------------------------------
def xrdfs_ls(path, server=None):
    srv = server or XRD_SERVER
    result = subprocess.run(["xrdfs", srv, "ls", "-l", path],
                            capture_output=True, text=True, env=_XRDFS_ENV)
    # A failed listing must not look like an empty directory -- that bug silently produced
    # empty shards in compareDeltaR.py once already.
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


def list_root_files(directory, server=None):
    srv = server or XRD_SERVER
    files = []
    for path, is_dir in xrdfs_ls(directory, server=srv):
        if is_dir:
            files.extend(list_root_files(path, server=srv))
        elif path.endswith(".root"):
            files.append(srv + path)
    return files


def discover_samples(n_signal_points, qcd_bins, with_minbias=True):
    """(tag, directory, colour, kind) for the signal points, QCD bins and MinBias to read.

    Signal points come from the fixed SIGNAL_POINTS list rather than being discovered, so
    they are the SAME points compareDeltaR.py studies and carry the same labels.
    """
    picks = []
    for i, (tag, d) in enumerate(SIGNAL_POINTS[:n_signal_points]):
        picks.append((tag, d, SIG_COLORS[i % len(SIG_COLORS)], "sig"))

    for i, b in enumerate(qcd_bins):
        d = f"{BASE}/QCD_Bin-PT-{b}_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8"
        picks.append((qcd_label(b), d, QCD_COLORS[i % len(QCD_COLORS)], "qcd"))

    if with_minbias:
        picks.append((MINBIAS_LABEL, MINBIAS_DIR, MINBIAS_COLOR, "minbias"))
    return picks


def collect_data_files(which="all"):
    """Every .root under the Parking* directories, for the data pages.

    *which* selects the primary dataset: "single" (ParkingSingleMuon), "double"
    (ParkingDoubleMuonLowMass) or "all". Note that "all" POOLS two different PDs with
    different triggers -- and an event firing both is present in both, so it is counted
    twice. Kept as the default because it is the largest sample, but a per-PD run is the
    honest comparison if the two turn out to differ.

    Cheap enough to enumerate in full: the leaf directories are flat (~1000 files each,
    ~0.4 s to list), and knowing the true total is what makes "1% of the data" an honest
    statement rather than a guess."""
    out = []
    for top, is_dir in xrdfs_ls(BASE):
        name = top.rsplit("/", 1)[-1]
        if not (is_dir and "Parking" in name):
            continue
        if which == "single" and "SingleMuon" not in name:
            continue
        if which == "double" and "DoubleMuonLowMass" not in name:
            continue
        found = list_root_files(top)
        log(f"    {name:32s} {len(found):>7,} files")
        out.extend(found)
    return out


# ----------------------------------------------------------------------------
# reading -> nTrueInt histogram per sample
# ----------------------------------------------------------------------------
def read_sample(directory, n_files, corr_set, frac=None, seed=0):
    """Per-sample histograms: nTrueInt, and PV_npvsGood both unweighted and PU-weighted.

    The weight has to be applied here, event by event, because it is a function of
    nTrueInt while the histogram is in npvsGood -- the two cannot be combined after the
    fact from the binned nTrueInt distribution alone.

    *frac* selects a seeded RANDOM fraction of the files instead of the first *n_files*.
    That matters for a sample split over several production subdirectories (MinBias is
    split over 0000/0001/0002): the head of the listing is one subdirectory, i.e. a subset
    of the JOBS, which is not a representative subset of the sample. Whichever of *frac*
    and *n_files* asks for fewer files wins, so a --test run still reads one file.
    """
    import uproot

    all_urls = list_root_files(directory)
    if not all_urls:
        raise RuntimeError(f"no .root files under {directory}")
    if frac is not None:
        n_pick = max(1, round(frac * len(all_urls)))
        if n_files is not None:
            n_pick = min(n_pick, n_files)
        urls = (random.Random(seed).sample(all_urls, n_pick)
                if n_pick < len(all_urls) else list(all_urls))
    else:
        urls = all_urls if n_files is None else all_urls[:n_files]

    nti = np.zeros(len(PU_BINS) - 1)
    npv = np.zeros(len(NPV_BINS) - 1)
    npv_w = {key: np.zeros(len(NPV_BINS) - 1) for key, _, _, _ in corr_set}
    used = 0
    for url in urls:
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                keys = set(tree.keys())
                if "Pileup_nTrueInt" not in keys:
                    log(f"    [warn] {url.split('/')[-1]}: no Pileup_nTrueInt -- skipping",
                        file=sys.stderr)
                    continue
                a = tree["Pileup_nTrueInt"].array(library="np")
                v = (tree["PV_npvsGood"].array(library="np")
                     if "PV_npvsGood" in keys else None)
            nti += np.histogram(a, bins=PU_BINS)[0]
            if v is not None:
                npv += np.histogram(v, bins=NPV_BINS)[0]
                for key, _, corr, _ in corr_set:
                    w = eval_weights(corr, a)
                    npv_w[key] += np.histogram(v, bins=NPV_BINS, weights=w)[0]
            used += 1
        except Exception as exc:
            log(f"    [warn] skipping {url.split('/')[-1]}: {exc}", file=sys.stderr)
    return dict(nti=nti, npv=npv, npv_w=npv_w, read=used, avail=len(all_urls))


def data_key(url):
    """(stream, era) parsed from a data file path.

    Layout under BASE is  <stream>/<epoch>/<timestamp>/<subdir>/nano_N.root, and the
    epoch directory carries the run era, e.g.
    nanotron-v15_2024__from_Run2024C-MINIv6NANOv15-v1 -> Run2024C-v1.
    """
    parts = url.split(f"{BASE}/")[-1].split("/")
    stream = parts[0] if parts else "?"
    epoch = parts[1] if len(parts) > 1 else "?"
    era = epoch.replace("nanotron-v15_2024__from_", "").replace("-MINIv6NANOv15", "")
    # Strip the trailing processing version: the "-vN" suffix is a REPROCESSING pass that
    # varies per stream, not a run range. 13 streams carry Run2024I-v3, 3 carry -v2, 2
    # carry -v4 -- same data, different processing. Splitting on it would split on stream.
    # What remains is the data period: Run2024C..H, Run2024I and the Run2024I_v2 re-reco.
    era = re.sub(r"-v\d+$", "", era)
    return stream, era


def era_letter(label):
    """Run2024F-v3 -> F,  Run2024I_v2-v2 -> I.

    The central payloads are one file per RUN ERA (B..I), while the sample area splits
    each era into processing versions. Page 8 matches data to weights, so it has to group
    at the era the weights are actually defined at."""
    m = re.match(r"Run2024([A-Z])", label)
    return m.group(1) if m else "?"


def load_golden(path):
    """{run: [(lo, hi), ...]} of certified lumisection ranges, or None if unavailable."""
    if not path or not os.path.exists(path):
        return None
    with open(path) as fh:
        cert = json.load(fh)
    out = {int(r): [(int(a), int(b)) for a, b in v] for r, v in cert.items()}
    n_ls = sum(b - a + 1 for v in out.values() for a, b in v)
    log(f"  golden JSON: {len(out)} runs, {n_ls:,} lumisections  ({os.path.basename(path)})")
    return out


def golden_mask(runs, lumis, cert):
    """Per-event bool: is this (run, lumisection) certified?"""
    keep = np.zeros(len(runs), dtype=bool)
    for run in np.unique(runs):
        ranges = cert.get(int(run))
        if not ranges:
            continue                      # run absent from the JSON -> not certified
        sel = runs == run
        l = lumis[sel]
        m = np.zeros(len(l), dtype=bool)
        for lo, hi in ranges:
            m |= (l >= lo) & (l <= hi)
        keep[sel] = m
    return keep


def read_data_npv(urls, cert=None):
    """PV_npvsGood over data files, kept split by era as well as summed.

    Data carries no Pileup_nTrueInt, which is why page 6 lives in npvsGood. The per-era
    split exists because the draw is uniform over FILES, so eras enter weighted by file
    count rather than by luminosity -- if one era has a genuinely different pileup
    profile, that shows up here rather than being silently averaged into the total.
    """
    import uproot

    npv = np.zeros(len(NPV_BINS) - 1)
    rej = np.zeros(len(NPV_BINS) - 1)
    per_era, per_era_n = {}, {}
    n_evt = n_rej = 0
    for i, url in enumerate(urls, 1):
        if i % 100 == 0 or i == len(urls):
            log(f"    [{i}/{len(urls)}] {n_evt:,} events so far")
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                if "PV_npvsGood" not in tree.keys():
                    continue
                v = tree["PV_npvsGood"].array(library="np")
                if cert is not None:
                    r = tree["run"].array(library="np")
                    b = tree["luminosityBlock"].array(library="np")
                    keep = golden_mask(r, b, cert)
                    n_rej += int((~keep).sum())
                    rej += np.histogram(v[~keep], bins=NPV_BINS)[0]
                    v = v[keep]
            h = np.histogram(v, bins=NPV_BINS)[0]
            npv += h
            _, era = data_key(url)
            if era not in per_era:
                per_era[era] = np.zeros(len(NPV_BINS) - 1)
                per_era_n[era] = 0
            per_era[era] += h
            per_era_n[era] += len(v)
            n_evt += len(v)
        except Exception as exc:
            log(f"    [warn] skipping {url.split('/')[-1]}: {exc}", file=sys.stderr)
    return dict(total=npv, per_era=per_era, per_era_n=per_era_n, n_evt=n_evt,
                rejected=rej, n_rejected=n_rej)


def stats(counts, centres=PU_CENTRES):
    """(mean, rms) of a binned distribution."""
    tot = counts.sum()
    if tot <= 0:
        return float("nan"), float("nan")
    mean = (counts * centres).sum() / tot
    var = (counts * (centres - mean) ** 2).sum() / tot
    return mean, math.sqrt(max(var, 0.0))


def normalise(counts):
    tot = counts.sum()
    return counts / tot if tot > 0 else counts


def max_cdf_dev(a, b):
    """Largest |CDF difference| between two normalised profiles -- a shape-difference
    number that does not depend on the binning the way a bin-by-bin ratio does."""
    return float(np.abs(np.cumsum(normalise(a)) - np.cumsum(normalise(b))).max())


# ----------------------------------------------------------------------------
# corrections
# ----------------------------------------------------------------------------
def load_correction(path):
    """(evaluator, correction name). Each of these files holds exactly one set."""
    import correctionlib
    cs = correctionlib.CorrectionSet.from_file(path)
    name = list(cs.keys())[0]
    return cs[name], name


def eval_weights(corr, x, syst="nominal"):
    return np.asarray(corr.evaluate(np.asarray(x, dtype=float), syst), dtype=float)


def ensure_repo_json(path, url):
    """The lum-corrections stopgap, fetched on demand. Returns the path, or None if it
    cannot be obtained -- page 3 is then skipped rather than failing the whole run."""
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    log(f"  fetching {url}")
    try:
        import urllib.request
        urllib.request.urlretrieve(url, path)
        return path
    except Exception as exc:
        log(f"  [warn] could not fetch the lum-corrections file ({exc}); "
            f"skipping the weight-source page", file=sys.stderr)
        return None


# ----------------------------------------------------------------------------
# plot helpers
# ----------------------------------------------------------------------------
def _ticks(ax):
    """4-sided inward ticks on a sub-panel. cms.cms_axes() also writes the CMS label, so
    it belongs on the main panel only."""
    ax.tick_params(which="both", direction="in", top=True, right=True,
                   labelsize=cms.FS_AXES - 1)
    ax.minorticks_on()


def _transparent_legends(fig):
    """Drop the legend backgrounds entirely on this page.

    cmsstyle keeps a semi-transparent white fill so labels stay readable over a curve.
    These pages are sparse enough that the fill only hides the curves it sits on, so they
    are drawn fully transparent instead -- local to this script, not a change to the
    shared convention."""
    from matplotlib.legend import Legend
    for ax in fig.axes:
        for child in ax.get_children():
            if isinstance(child, Legend):
                child.get_frame().set_alpha(0.0)


def _left_align_legend(leg):
    """Left-align the entries under a wider legend title.

    Entries are centred under the title by default, which leaves them floating well to
    its right. Nudging the whole legend left instead would push the (much wider) title
    off the canvas. matplotlib 3.4 -- what setup.sh provides -- has no public
    set_alignment(), so reach into the VPacker, guarded in case that changes."""
    try:
        leg._legend_box.align = "left"
    except AttributeError:
        pass


def _text_legend(ax, lines, loc="upper left", fontsize=9):
    """Text-only legend WITHOUT the automatic partial-read line cms.info_legend() adds.

    For pages that already state their own per-source file counts, where the generic
    "Partial sample plot" line would be a redundant third statement of the same thing."""
    from matplotlib.legend import Legend
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], ls="", marker="") for _ in lines]
    leg = Legend(ax, handles, list(lines), loc=loc, fontsize=fontsize,
                 handlelength=0, handletextpad=0, labelspacing=0.3, **cms.LEGEND_KW)
    ax.add_artist(leg)
    ax._has_info_legend = True
    return leg


def _stack_below(fig, ax, upper, lower, gap=0.035, x=0.02):
    """Put the *lower* legend directly under *upper*, both flush left, with a small gap.

    Needs a draw first: the height of the upper legend depends on how many entries and
    how long a title it ended up with, which is only known once it has been laid out.
    """
    fig.canvas.draw()
    y0 = upper.get_window_extent().transformed(ax.transAxes.inverted()).y0
    lower.set_bbox_to_anchor((x, y0 - gap), transform=ax.transAxes)


def _partial_note(ax, loc="lower right"):
    """State a partial read WITHOUT colliding with the curve legend.

    cms.stamp_partial() defaults to the upper left, which is where every legend on these
    pages already is. Calling info_legend() here also stamps the axes so a later
    stamp_partial() will not add a second copy."""
    return cms.info_legend(ax, [], loc=loc, fontsize=cms.FS_LEGEND - 3)


def _ratio_ylabel(rax, text):
    """Ratio-panel y title, centred. cmsstyle sets yaxis.labellocation='top' globally,
    which is the CMS convention on the main panel but strands this label at the top of a
    panel a third the height -- centred is the readable choice here."""
    rax.set_ylabel(text, fontsize=cms.FS_LABEL - 3, loc="center")


# Marker convention, shared with compareDeltaR / compareBDTvars / compareSVcharge /
# compareMET: data is a small SOLID black square, the background estimates (pT-hat QCD and
# MinBias) are WHITE-filled circles. Solid = measured, open = simulated. Applied on the
# closure page, which is the only one here carrying data and both backgrounds together;
# the weight and per-era pages are curve-vs-curve comparisons where markers would only add
# texture.
DATA_MARKER, DATA_MARKER_SIZE = "s", 3.5
BKG_MARKER, BKG_MARKER_SIZE = "o", 4.0
MARKER_EDGE = 1.0


def marker_kw(kind, colour):
    """Marker styling for a curve of *kind* in {"data", "bkg", None}."""
    if kind == "data":
        return dict(marker=DATA_MARKER, markersize=DATA_MARKER_SIZE,
                    markerfacecolor=colour, markeredgecolor=colour,
                    markeredgewidth=MARKER_EDGE)
    if kind == "bkg":
        return dict(marker=BKG_MARKER, markersize=BKG_MARKER_SIZE,
                    markerfacecolor="white", markeredgecolor=colour,
                    markeredgewidth=MARKER_EDGE)
    return {}


def _ratio_figure():
    """Main panel + ratio panel sharing an x axis."""
    fig, (ax, rax) = plt.subplots(
        2, 1, figsize=PAGE_SIZE, sharex=True,
        gridspec_kw=dict(height_ratios=[3, 1], hspace=0.05))
    return fig, ax, rax


def _finish_ratio(fig, title):
    """Lay out a ratio figure. tight_layout() fights the fixed hspace of the shared-x
    gridspec (it warns and then gets the spacing wrong), so place the panels explicitly."""
    fig.suptitle(title, fontsize=cms.FS_TITLE)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.92, bottom=0.08, hspace=0.05)


def _xlim(ax):
    """Trim to where the MC actually lives -- the correction files run to 99, but nothing
    in these samples is above ~75 and the empty tail wastes most of the axis."""
    ax.set_xlim(0, 80)


HEADROOM = 0.8      # curves fill at most this fraction of the axis height


def _weight_ylim(ax, curves):
    """Scale to the weight curves, not to the MC-profile shading. The shading is drawn
    from a floor of 1e-4 purely so it fills; letting it set the limits would squash every
    curve into the top third of the axis. Limits go tight to the data first, then
    extend_log_top() opens the headroom -- it works from the current ylim."""
    lo = min(float(c[c > 0].min()) for c in curves if np.any(c > 0))
    hi = max(float(c.max()) for c in curves)
    ax.set_ylim(max(0.5 * lo, 1e-3), hi)
    cms.extend_log_top(ax, HEADROOM)


def _profile_shading(ax, qcd_profile, top, mb_profile=None):
    """The MC profile behind a weight curve: a weight of 20 is irrelevant where there are
    no events, and this is the only honest way to show that on the same axes.

    The shading is the QCD pT-hat profile ALONE, not a sum over every sample read. A sum
    is dominated by whichever sample happened to contribute most files, which is a
    property of the read rather than of the physics, and it hides the very disagreement
    page 1 exists to look for.

    *mb_profile* is drawn on top as a dashed EDGE using the same scale factor -- both are
    unit-normalised first, then multiplied by the same number -- so the dashed line
    against the filled band is a direct shape comparison of the two independent
    productions, not two curves normalised to different things."""
    h = normalise(qcd_profile)
    scale = top / max(h.max(), 1e-12)
    ax.fill_between(PU_CENTRES, 1e-4, np.maximum(h * scale, 1e-4), step="mid",
                    color="grey", alpha=0.16, lw=0, label="QCD profile (arb. norm.)")
    if mb_profile is not None and mb_profile.sum() > 0:
        hm = normalise(mb_profile) * scale
        ax.stairs(np.maximum(hm, 1e-4), PU_BINS, color="grey", lw=1.4, ls="--",
                  zorder=1.5, label="MinBias profile (same norm.)")


# ----------------------------------------------------------------------------
# page 1: MC nTrueInt profiles, signal vs QCD
# ----------------------------------------------------------------------------
def plot_profiles(profiles):
    fig, ax, rax = _ratio_figure()
    ref_tag, ref_counts = profiles[0]["tag"], profiles[0]["nti"]
    ref = normalise(ref_counts)

    worst, hmax = 0.0, 0.0
    for i, s in enumerate(profiles):
        tag, counts, color = s["tag"], s["nti"], s["color"]
        h = normalise(counts)
        hmax = max(hmax, float(h.max()))
        mean, rms = stats(counts)
        # Mark the curve the ratio panel divides by, so the flat line at 1 is attributable.
        suffix = "   (ref)" if i == 0 else ""
        ax.stairs(h, PU_BINS, color=color, linewidth=1.8,
                  label=rf"{tag}   $\langle n \rangle$={mean:.2f}, RMS={rms:.2f}{suffix}")
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(ref > 0, h / ref, np.nan)
        rax.stairs(r, PU_BINS, color=color, linewidth=1.4)
        worst = max(worst, max_cdf_dev(counts, ref_counts))

    rax.axhline(1.0, color="grey", lw=0.8, ls="--")
    ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
    # Name the numerator, not just the denominator: a bare "/ reference" does not say what
    # is being divided. Which sample IS the reference is spelled out in the legend title,
    # since the full sample name would be longer than this panel is tall.
    _ratio_ylabel(rax, "sample / reference")
    rax.set_xlabel(r"$n_{\mathrm{TrueInt}}$", fontsize=cms.FS_LABEL)
    rax.set_ylim(0.7, 1.3)
    ax.set_ylim(0, hmax)
    cms.extend_linear_top(ax, HEADROOM)
    _xlim(ax)
    _ticks(rax)
    cms.cms_axes(ax, fontsize=cms.FS_AXES)

    # Everything describing the comparison goes in the legend header, so the one legend
    # carries it: a second text box at upper right lands on top of the curve legend.
    title = (f"Generated pileup profile, per sample\n"
             f"reference: {ref_tag}   |   max CDF deviation: {worst:.3f}")
    ax.legend(fontsize=cms.FS_LEGEND - 2, loc="upper left", title=title,
              title_fontsize=cms.FS_LEGEND - 1, **cms.LEGEND_KW)
    # Per-sample file counts, since the samples are read independently. Placed lower right,
    # where the distribution has already fallen to zero.
    # In full mode cms.is_partial() is False by construction (see main), so the
    # per-sample block disappears with every other partial-read banner.
    if cms.is_partial():
        cms.partial_samples_legend(
            ax, [(s["tag"], s["read"], s["legend_avail"]) for s in profiles],
            loc="lower right", fontsize=cms.FS_LEGEND - 4)
    _finish_ratio(fig, "MC pileup profile -- does one profile serve signal and QCD?")
    return fig


# ----------------------------------------------------------------------------
# page 2: the central weights, against the MC statistics
# ----------------------------------------------------------------------------
def plot_central_weights(corr, name, qcd_profile, mb_profile=None):
    fig, ax = plt.subplots(figsize=PAGE_SIZE)

    curves = [eval_weights(corr, PU_CENTRES, s) for s in ("nominal", "up", "down")]
    _profile_shading(ax, qcd_profile, 0.9 * max(c.max() for c in curves), mb_profile)

    for syst, w in zip(("nominal", "up", "down"), curves):
        color, ls, lw = SYST_STYLE[syst]
        ax.plot(PU_CENTRES, w, color=color, ls=ls, lw=lw, label=syst)

    ax.axhline(1.0, color="grey", lw=0.8, ls=":")
    ax.set_yscale("log")
    _weight_ylim(ax, curves)
    ax.set_xlabel(r"$n_{\mathrm{TrueInt}}$", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Pileup weight", fontsize=cms.FS_LABEL)
    _xlim(ax)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, label=cms.CMS_LABEL_DATA)
    ax.legend(fontsize=cms.FS_LEGEND, loc="upper left", title=name,
              title_fontsize=cms.FS_LEGEND, **cms.LEGEND_KW)
    _partial_note(ax)
    fig.suptitle("Central 2024 pileup weights, with the MC statistics behind them",
                 fontsize=cms.FS_TITLE)
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------
# page 3: weight sources compared
# ----------------------------------------------------------------------------
def plot_sources(sources, qcd_profile, mb_profile=None):
    """*sources* = [(label, corr, colour)], the first being the reference for the ratio."""
    fig, ax, rax = _ratio_figure()
    ref_label, ref_corr, _ = sources[0]
    ref = eval_weights(ref_corr, PU_CENTRES)
    curves = [(lbl, eval_weights(c, PU_CENTRES), col) for lbl, c, col in sources]
    _profile_shading(ax, qcd_profile, 0.9 * max(w.max() for _, w, _ in curves), mb_profile)

    # These sets agree closely, so a curve drawn underneath another is simply invisible.
    # Reference thick and solid at the BACK, alternatives thin and dashed in front: the
    # dashes then read against the reference wherever the two coincide.
    for i, (label, w, color) in enumerate(curves):
        # A source that has run out of coverage returns exactly 1. Flag that only where
        # the reference is still correcting -- above ~75 every set goes flat because the
        # correction simply ends, which is not a defect.
        note = ""
        flat = np.where((w == 1.0) & (ref != 1.0) & (PU_CENTRES > 40))[0]
        if flat.size:
            x = PU_CENTRES[flat[0]]
            note = f"   [flat 1 above {x:.0f}]"
            ax.axvline(x, color=color, ls=":", lw=1.2, alpha=0.8)
        style = (dict(lw=2.8, ls="-", zorder=2) if i == 0
                 else dict(lw=1.6, ls="--", zorder=4 + i))
        if i == 0:
            note += "   (ref)"
        ax.plot(PU_CENTRES, w, color=color, label=label + note, **style)
        with np.errstate(divide="ignore", invalid="ignore"):
            rax.plot(PU_CENTRES, np.where(ref > 0, w / ref, np.nan), color=color, **style)

    rax.axhline(1.0, color="grey", lw=0.8, ls="--")
    ax.set_yscale("log")
    _weight_ylim(ax, [w for _, w, _ in curves])
    ax.set_ylabel("Pileup weight", fontsize=cms.FS_LABEL)
    _ratio_ylabel(rax, "source / reference")
    rax.set_xlabel(r"$n_{\mathrm{TrueInt}}$", fontsize=cms.FS_LABEL)
    rax.set_ylim(0.0, 2.0)
    _xlim(ax)
    _ticks(rax)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, label=cms.CMS_LABEL_DATA)
    ax.legend(fontsize=cms.FS_LEGEND - 2, loc="upper left",
              title="Nominal weight, by source",
              title_fontsize=cms.FS_LEGEND - 1, **cms.LEGEND_KW)
    _partial_note(ax)
    _finish_ratio(fig, "Weight sources compared -- central vs the lum-corrections stopgap")
    return fig


# ----------------------------------------------------------------------------
# page 4: per-era spread
# ----------------------------------------------------------------------------
def plot_eras(era_corrs, combined, combined_name, qcd_profile, mb_profile=None):
    fig, ax, rax = _ratio_figure()
    ref = eval_weights(combined, PU_CENTRES)
    curves = [eval_weights(c, PU_CENTRES) for _, c in era_corrs] + [ref]
    _profile_shading(ax, qcd_profile, 0.9 * max(c.max() for c in curves), mb_profile)

    for i, (era, corr) in enumerate(era_corrs):
        w = eval_weights(corr, PU_CENTRES)
        color = ERA_COLORS[i % len(ERA_COLORS)]
        ax.plot(PU_CENTRES, w, color=color, lw=1.4, label=f"era {era}")
        with np.errstate(divide="ignore", invalid="ignore"):
            rax.plot(PU_CENTRES, np.where(ref > 0, w / ref, np.nan), color=color, lw=1.2)

    ax.plot(PU_CENTRES, ref, color="black", lw=2.4, zorder=6, label="combined   (ref)")
    rax.axhline(1.0, color="black", lw=0.9, ls="--")

    ax.set_yscale("log")
    _weight_ylim(ax, curves)
    ax.set_ylabel("Pileup weight", fontsize=cms.FS_LABEL)
    _ratio_ylabel(rax, "era / combined")
    rax.set_xlabel(r"$n_{\mathrm{TrueInt}}$", fontsize=cms.FS_LABEL)
    rax.set_ylim(0.0, 2.0)
    _xlim(ax)
    _ticks(rax)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, label=cms.CMS_LABEL_DATA)
    leg = ax.legend(fontsize=cms.FS_LEGEND - 2, loc="upper left", ncol=2,
                    title=f"Central 2024 weights, per era (combined: {combined_name})",
                    title_fontsize=cms.FS_LEGEND - 1, **cms.LEGEND_KW)
    _left_align_legend(leg)
    _partial_note(ax)
    _finish_ratio(
        fig, "Per-era pileup weights -- the handle a single merged histogram cannot give")
    return fig


# ----------------------------------------------------------------------------
# page 5: closure
# ----------------------------------------------------------------------------
def plot_closure(profiles, corr_set):
    """MC before/after reweighting, one curve per correction, plus <w> per sample.

    <w> is the real test of whether a set of weights was derived against THIS MC profile:
    the files are normalised so that reweighting the profile they assume leaves the event
    count unchanged. <w> away from 1 means the sample was produced with a different
    pileup profile and those weights do not apply to it. Showing both corrections side by
    side turns that from a pass/fail into a comparison.
    """
    fig, ax = plt.subplots(figsize=PAGE_SIZE)

    # QCD solid, MinBias dashed, same colour for the same correction: the page's question
    # is what a correction DOES, and drawing the two backgrounds in one colour per
    # correction puts the pair of curves that answer it side by side. Signal is left out
    # -- these curves are the background spectrum being corrected, and folding a signal
    # sample into them would only blur it. Every sample, signal included, still gets its
    # own <w> line in the block below, which is where per-sample behaviour belongs.
    families = [("QCD $p_T$ bins", "qcd", "-", 2.2)]
    if any(s["kind"] == "minbias" for s in profiles):
        families.append(("MinBias", "minbias", "--", 1.8))

    tops, weights = [], {}
    for key, _label, corr, _color in corr_set:
        weights[key] = eval_weights(corr, PU_CENTRES)

    for fam_label, kind, ls, lw in families:
        total = np.zeros(len(PU_BINS) - 1)
        for s in profiles:
            if s["kind"] == kind:
                total += s["nti"]
        if total.sum() == 0:
            continue
        before = normalise(total)
        m_before, r_before = stats(total)
        tops.append(float(before.max()))
        ax.stairs(before, PU_BINS, color="royalblue", lw=lw, ls=ls,
                  label=rf"{fam_label}, unweighted   $\langle n \rangle$={m_before:.2f}, "
                        rf"RMS={r_before:.2f}")
        for key, label, _corr, color in corr_set:
            w = weights[key]
            after = normalise(total * w)
            m, r = stats(total * w)
            tops.append(float(after.max()))
            ax.stairs(after, PU_BINS, color=color, lw=lw, ls=ls,
                      label=rf"{fam_label}, P.U. reweighted [{label}]   "
                            rf"$\langle n \rangle$={m:.2f}, RMS={r:.2f}")

    keys = [k for k, _, _, _ in corr_set]
    lines = [r"$\langle w \rangle$ per sample:   " + "  |  ".join(l for _, l, _, _ in corr_set)]
    for s in profiles:
        tot = s["nti"].sum()
        vals = [(s["nti"] * weights[k]).sum() / tot if tot > 0 else float("nan")
                for k in keys]
        lines.append(f"{s['tag']}:   " + "  |  ".join(f"{v:.4f}" for v in vals))
    lines.append(r"$\langle w \rangle = 1$ <=> the weights assume this MC profile")

    ax.set_xlabel(r"$n_{\mathrm{TrueInt}}$", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
    ax.set_ylim(0, max(tops))
    cms.extend_linear_top(ax, HEADROOM)
    _xlim(ax)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, label=cms.CMS_LABEL_DATA)
    leg = ax.legend(fontsize=cms.FS_LEGEND - 1, loc="upper left",
                    title=r"nominal weights, evaluated at $n_{\mathrm{TrueInt}}$",
                    title_fontsize=cms.FS_LEGEND - 1, **cms.LEGEND_KW)
    # Both legends flush left, the per-sample <w> block stacked under the curve legend.
    info = cms.info_legend(ax, lines, loc="upper left", fontsize=cms.FS_LEGEND - 3)
    fig.suptitle("Closure -- the reweighted MC is the pileup spectrum of the data",
                 fontsize=cms.FS_TITLE)
    fig.tight_layout()
    if info is not None:
        _stack_below(fig, ax, leg, info)
    return fig


# ----------------------------------------------------------------------------
# page 6: the same closure, validated against data
# ----------------------------------------------------------------------------
def plot_npv_closure(profiles, data_npv, data_events, data_read, data_total, corr_set,
                     full_mode=False):
    """Reconstructed-vertex multiplicity: data vs MC, before and after PU reweighting.

    Page 5 cannot be drawn with data on it -- its x axis is Pileup_nTrueInt, a
    generator-level quantity that does not exist in the parking nanoAOD. PV_npvsGood is
    the pileup observable data and MC have in common, so this is where the correction can
    be judged: if the weights are right, the red curve should sit closer to the data than
    the blue one. Shapes are unit-normalised, so this tests the SHAPE only, not the rate.
    """
    fig, ax = plt.subplots(figsize=PAGE_SIZE)

    # Same convention as page 5: QCD solid, MinBias dashed, one colour per correction.
    # Data is black and solid -- it is what both backgrounds are being judged against, so
    # it must not share a line style with either of them.
    families = [("QCD $p_T$ bins", "qcd", "-", 2.0)]
    if any(s["kind"] == "minbias" for s in profiles):
        families.append(("MinBias", "minbias", "--", 1.8))

    entries = [(data_npv, "black", "Data", "-", 2.4, "data")]
    for fam_label, kind, ls, lw in families:
        sel = [s for s in profiles if s["kind"] == kind]
        if not sel:
            continue
        mc = np.zeros(len(NPV_BINS) - 1)
        for s in sel:
            mc += s["npv"]
        if mc.sum() == 0:
            continue
        entries.append((mc, "royalblue", f"{fam_label}, unweighted", ls, lw, "bkg"))
        for key, label, _, color in corr_set:
            mc_w = np.zeros(len(NPV_BINS) - 1)
            for s in sel:
                mc_w += s["npv_w"][key]
            entries.append((mc_w, color, f"{fam_label}, P.U. reweighted [{label}]",
                            ls, lw, "bkg"))

    curves, data_mean = [], stats(data_npv, NPV_CENTRES)[0]
    npv_centres = NPV_CENTRES
    for counts, color, lbl, ls, lw, kind in entries:
        h = normalise(counts)
        m, r = stats(counts, NPV_CENTRES)
        curves.append(h)
        # The bias against data is the number this page exists to compare, so quote it
        # rather than leaving the reader to subtract two means in their head.
        bias = "" if lbl == "Data" else rf",  $\Delta$={m - data_mean:+.2f}"
        # drawstyle, not ax.stairs(): a StepPatch cannot carry markers.
        ax.plot(npv_centres, h, drawstyle="steps-mid", color=color, lw=lw, ls=ls,
                label=rf"{lbl}   $\langle N \rangle$={m:.2f}, RMS={r:.2f}{bias}",
                **marker_kw(kind, color))

    ax.set_xlabel(r"$N_{\mathrm{PV}}$ (good primary vertices)", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
    ax.set_xlim(0, 80)
    ax.set_ylim(0, max(float(c.max()) for c in curves))
    cms.extend_linear_top(ax, HEADROOM)
    cms.set_lumi_files(data_read, data_total)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, header=cms.lumi_header(),
                 label=cms.CMS_LABEL_DATA)

    leg = ax.legend(fontsize=cms.FS_LEGEND - 1, loc="upper left",
                    title="unit-normalised shapes",
                    title_fontsize=cms.FS_LEGEND - 1, **cms.LEGEND_KW)
    lines = [
        f"Data: {data_read:,} of {data_total:,} files "
        f"({100 * data_read / max(data_total, 1):.2f}%)",
        f"        {data_events:,} events, randomly drawn",
        "MC: QCD $p_T$ bins (solid), MinBias (dashed) -- kept separate, never summed",
    ]
    # On a full run the caps (all signal, 100 files/QCD bin, 0.1% of data) are the
    # intended configuration rather than a shortfall, and the lines above already state
    # them -- so the generic "Partial sample plot" line is dropped as redundant.
    info = (_text_legend(ax, lines, loc="upper left", fontsize=cms.FS_LEGEND - 2)
            if full_mode else
            cms.info_legend(ax, lines, loc="upper left", fontsize=cms.FS_LEGEND - 2))
    fig.suptitle("Data validation -- does the pileup correction improve the agreement?",
                 fontsize=cms.FS_TITLE)
    fig.tight_layout()
    if info is not None:
        _stack_below(fig, ax, leg, info, gap=0.012)
    return fig


# ----------------------------------------------------------------------------
# page 7: the data, broken down by era
# ----------------------------------------------------------------------------
def plot_data_eras(data, profiles, corr_set, min_events=20000):
    """Data PV_npvsGood per era, plus <N> per era against the merged data and the MC.

    Why this page exists: the data files are drawn uniformly, so eras enter the merged
    distribution weighted by FILE COUNT, while the central weights are golden-JSON
    LUMINOSITY-weighted over eras C-I. Those are different averages over eras whose
    pileup genuinely differs, so a residual data/MC offset on page 6 can come from the
    averaging alone, with nothing wrong with the weights. Splitting by era separates the
    two -- and locates any low-pileup population instead of leaving it as a bump.
    """
    eras = sorted(e for e in data["per_era"] if data["per_era_n"][e] >= min_events)
    if not eras:
        return None

    fig, (ax, bx) = plt.subplots(
        2, 1, figsize=PAGE_SIZE, gridspec_kw=dict(height_ratios=[2.3, 1]))
    colours = plt.cm.tab20(np.linspace(0, 1, max(len(eras), 2)))

    means = []
    for i, era in enumerate(eras):
        h = normalise(data["per_era"][era])
        m, _ = stats(data["per_era"][era], NPV_CENTRES)
        means.append(m)
        ax.stairs(h, NPV_BINS, color=colours[i], lw=1.3,
                  label=f"{era}  ({data['per_era_n'][era] / 1e6:.1f}M)  " r"$\langle N \rangle$="
                        f"{m:.1f}")

    d_mean, _ = stats(data["total"], NPV_CENTRES)
    ax.stairs(normalise(data["total"]), NPV_BINS, color="black", lw=2.6,
              label=rf"All data merged   $\langle N \rangle$={d_mean:.2f}")

    # "MC" here is the QCD pT-hat profile, matching pages 2-6: a sum over every sample
    # read would be weighted by file count rather than by physics, and the era offsets
    # this page measures are small enough for that to matter.
    qcd_profiles = [s for s in profiles if s["kind"] == "qcd"]
    mc_means = {}
    for key, label, _, color in corr_set:
        mc_w = np.zeros(len(NPV_BINS) - 1)
        for s in qcd_profiles:
            mc_w += s["npv_w"][key]
        m, _ = stats(mc_w, NPV_CENTRES)
        mc_means[label] = m
        ax.stairs(normalise(mc_w), NPV_BINS, color=color, lw=2.0, ls="--",
                  label=rf"QCD reweighted [{label}]   $\langle N \rangle$={m:.2f}")

    ax.set_xlim(0, 80)
    ax.set_xlabel(r"$N_{\mathrm{PV}}$ (good primary vertices)", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
    ax.set_ylim(0, max(float(normalise(data["per_era"][e]).max()) for e in eras))
    cms.extend_linear_top(ax, HEADROOM)
    cms.cms_axes(ax, fontsize=cms.FS_AXES, header=cms.lumi_header(),
                 label=cms.CMS_LABEL_DATA)
    ax.legend(fontsize=cms.FS_LEGEND - 4, loc="upper left", ncol=2,
              title=f"Data by era (>= {min_events / 1000:.0f}k events), unit-normalised",
              title_fontsize=cms.FS_LEGEND - 3, **cms.LEGEND_KW)

    # Summary panel: the era spread at a glance, which 18 overlapping curves do not give.
    bx.plot(range(len(eras)), means, "o", color="black", ms=7, label=r"data, per era")
    bx.axhline(d_mean, color="grey", lw=1.4, ls="-", label="all data merged")
    for (key, label, _, color) in corr_set:
        bx.axhline(mc_means[label], color=color, lw=1.4, ls="--",
                   label=f"MC reweighted [{label}]")
    bx.set_xticks(range(len(eras)))
    bx.set_xticklabels(eras, rotation=45, ha="right", fontsize=cms.FS_LEGEND - 4)
    bx.set_ylabel(r"$\langle N_{\mathrm{PV}} \rangle$", fontsize=cms.FS_LABEL - 2)
    _ticks(bx)
    bx.legend(fontsize=cms.FS_LEGEND - 4, loc="best", ncol=2, **cms.LEGEND_KW)

    fig.suptitle("Data pileup by era -- is the merged data/MC offset an averaging effect?",
                 fontsize=cms.FS_TITLE)
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------
# page 8: each era's data against MC weighted with THAT era's correction
# ----------------------------------------------------------------------------
def plot_era_matched(data, profiles, era_corrs, combined_key, combined_label,
                     min_events=500000, split_versions=("I",), min_events_split=100000):
    """One panel per era: data(era) vs MC reweighted with that era's own weights.

    This is the comparison pages 6 and 7 cannot make. There, merged file-weighted data is
    held against a single luminosity-weighted correction, so the era spread (5.5 vertices)
    swamps the difference between corrections (0.3). Matching each era to its own weights
    removes the averaging mismatch entirely, and is the only form of this test that can
    say whether the inclusive weights are actually wrong for parking.

    The combined correction is drawn alongside so the question "does per-era beat
    inclusive?" is answered panel by panel rather than asserted.
    """
    avail = {e for e, _ in era_corrs}
    # Group the data by run era: the sample area splits eras into processing versions,
    # the weights do not.
    by_letter, n_by_letter = {}, {}
    for label, hist in data["per_era"].items():
        L = era_letter(label)
        if L not in avail:
            continue
        by_letter[L] = by_letter.get(L, np.zeros(len(NPV_BINS) - 1)) + hist
        n_by_letter[L] = n_by_letter.get(L, 0) + data["per_era_n"][label]

    # Eras in *split_versions* get one panel per processing version instead of one pooled
    # panel, all still compared against that ERA's weights -- there is only one correction
    # per run era, so the versions share it by construction. Era I needs this: its
    # versions run 36.9-38.5 except Run2024I_v2-v3 at 21.8, and pooling them buries a
    # genuinely anomalous subset inside an otherwise well-behaved era.
    panels = []          # (title, era letter, hist, n_events)
    for L in sorted(by_letter):
        if L in split_versions:
            for label in sorted(l for l in data["per_era"] if era_letter(l) == L):
                if data["per_era_n"][label] >= min_events_split:
                    panels.append((label, L, data["per_era"][label],
                                   data["per_era_n"][label]))
        elif n_by_letter[L] >= min_events:
            panels.append((f"Era {L}", L, by_letter[L], n_by_letter[L]))
    if not panels:
        return None

    ncols = min(3, len(panels))
    nrows = math.ceil(len(panels) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.8 * ncols, 4.6 * nrows),
                             squeeze=False)
    flat = [axes[r][c] for r in range(nrows) for c in range(ncols)]
    for ax in flat[len(panels):]:
        ax.set_visible(False)

    summary = []
    for i, (title, L, d_hist, n_evt) in enumerate(panels):
        ax = flat[i]
        d_h = normalise(d_hist)
        d_m, d_r = stats(d_hist, NPV_CENTRES)

        mc_era = np.zeros(len(NPV_BINS) - 1)
        mc_comb = np.zeros(len(NPV_BINS) - 1)
        for s in (s for s in profiles if s["kind"] == "qcd"):
            mc_era += s["npv_w"][f"era_{L}"]
            mc_comb += s["npv_w"][combined_key]
        e_m, _ = stats(mc_era, NPV_CENTRES)
        c_m, _ = stats(mc_comb, NPV_CENTRES)
        summary.append((title, d_m, e_m, c_m))

        ax.stairs(d_h, NPV_BINS, color="black", lw=2.4,
                  label=rf"Data   $\langle N \rangle$={d_m:.2f}")
        ax.stairs(normalise(mc_era), NPV_BINS, color="crimson", lw=2.0,
                  label=rf"MC [era {L} wts]   $\langle N \rangle$={e_m:.2f}, "
                        rf"$\Delta$={e_m - d_m:+.2f}")
        ax.stairs(normalise(mc_comb), NPV_BINS, color="grey", lw=1.6, ls="--",
                  label=rf"MC [{combined_label}]   $\langle N \rangle$={c_m:.2f}, "
                        rf"$\Delta$={c_m - d_m:+.2f}")

        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlim(0, 70)
        ax.set_xlabel(r"$N_{\mathrm{PV}}$", fontsize=12)
        ax.set_ylabel("Fraction of events", fontsize=12)
        ax.tick_params(which="both", direction="in", top=True, right=True, labelsize=10)
        ax.minorticks_on()
        leg = ax.legend(fontsize=8.5, loc="upper left",
                        title=f"{n_evt / 1e6:.2f}M data events",
                        title_fontsize=8.5, **cms.LEGEND_KW)
        _left_align_legend(leg)

    log("\n  page 8, era-matched agreement (Delta = MC - data):")
    log(f"    {'panel':22s}   data   era-wts  (Delta)   combined  (Delta)")
    for title, d_m, e_m, c_m in summary:
        log(f"    {title:22s} {d_m:6.2f}  {e_m:7.2f} ({e_m - d_m:+5.2f})  "
            f"{c_m:7.2f} ({c_m - d_m:+5.2f})")

    head = 0.55 / (4.6 * nrows)
    fig.tight_layout()
    fig.subplots_adjust(top=1.0 - head)
    fig.suptitle("Era-matched validation -- data vs MC weighted with that era's own "
                 "correction", fontsize=cms.FS_TITLE, y=1.0 - 0.15 * head, va="top")
    return fig


# ----------------------------------------------------------------------------
def publish(pdf_path, webdir):
    try:
        os.makedirs(webdir, exist_ok=True)
        dest = os.path.join(webdir, os.path.basename(pdf_path))
        subprocess.run(["cp", pdf_path, dest], check=True)
        log(f"Published: {dest}")
    except Exception as exc:
        log(f"[warn] could not publish to {webdir}: {exc}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description="2024 pileup-reweighting cross-checks")
    p.add_argument("--output", default="comparePileUp.pdf",
                   help="Output PDF (default: comparePileUp.pdf)")
    p.add_argument("--n-files", type=int, default=N_FILES_DEFAULT,
                   help=f"Files per sample, <=0 for ALL (default: {N_FILES_DEFAULT})")
    p.add_argument("--n-signal-points", type=int, default=N_SIGNAL_POINTS,
                   help=f"How many of the fixed signal points to use (default: {N_SIGNAL_POINTS})")
    p.add_argument("--n-qcd-files", type=int, default=QCD_MAX_FILES,
                   help=f"Cap on files per QCD bin, applied even on a full run "
                        f"(default: {QCD_MAX_FILES}); only shapes are plotted")
    p.add_argument("--minbias-frac", type=float, default=MINBIAS_FRAC,
                   help=f"Fraction of the MinBias files, drawn at random with a fixed "
                        f"seed (default: {MINBIAS_FRAC} = 5%%)")
    p.add_argument("--minbias-seed", type=int, default=MINBIAS_SEED,
                   help=f"Seed for the MinBias file draw (default: {MINBIAS_SEED})")
    p.add_argument("--no-minbias", action="store_true",
                   help="Skip the MinBias sample entirely")
    p.add_argument("--data-frac", type=float, default=DATA_FRAC,
                   help=f"Fraction of data files for page 6, 0 disables it "
                        f"(default: {DATA_FRAC} = 0.1%%)")
    p.add_argument("--max-data-files", type=int, default=0,
                   help="Hard cap on data files, 0 for none (safety valve for --data-frac)")
    p.add_argument("--data-streams", choices=["all", "single", "double"], default="all",
                   help="Which parking PD to read: ParkingSingleMuon, "
                        "ParkingDoubleMuonLowMass, or both pooled (default: all)")
    p.add_argument("--golden-json", default=GOLDEN_JSON,
                   help="Certified lumisection JSON applied to DATA (default: the 2024 "
                        "golden cert in _tools/data)")
    p.add_argument("--no-golden", action="store_true",
                   help="Do NOT apply the golden JSON -- use every data event")
    p.add_argument("--data-seed", type=int, default=DATA_SEED,
                   help=f"Seed for the random data-file draw (default: {DATA_SEED})")
    p.add_argument("--central-dir", default=CENTRAL_DIR,
                   help="Directory holding the central puWeights_*.json.gz")
    p.add_argument("--era-set", default="CDEFGHI",
                   help="Central era set used for pages 2 and 5 (default: CDEFGHI)")
    p.add_argument("--repo-json", default=REPO_JSON_CACHE,
                   help="lum-corrections data/puWeights_2024.json.gz (fetched if absent)")
    p.add_argument("--no-publish", action="store_true",
                   help=f"Do not copy the PDF to {WEBDIR}")
    p.add_argument("--test", action="store_true", help="Quick check: 1 file per sample")
    args = p.parse_args()

    # A test run must never land on the full run's filename. Auto-suffixing means the two
    # can both be published side by side, so --no-publish is not needed to protect the
    # good output -- only to skip publishing entirely.
    if args.test and args.output == p.get_default("output"):
        args.output = args.output.replace(".pdf", "_test.pdf")

    if args.test:
        log(f"[TEST MODE] 1 file per sample -> {args.output}")
    n_files = 1 if args.test else (args.n_files if args.n_files > 0 else None)

    # --- corrections -------------------------------------------------------
    main_path = os.path.join(args.central_dir, f"puWeights_{args.era_set}.json.gz")
    if not os.path.exists(main_path):
        raise SystemExit(f"[error] no central payload at {main_path}")
    main_corr, main_name = load_correction(main_path)
    log(f"Central set: {main_name}\n  {main_path}")

    era_corrs = []
    for era in ERAS:
        path = os.path.join(args.central_dir, f"puWeights_{era}.json.gz")
        if os.path.exists(path):
            era_corrs.append((era, load_correction(path)[0]))
    log(f"  per-era sets found: {', '.join(e for e, _ in era_corrs) or 'none'}")

    sources = [(main_name, main_corr, "black")]
    alt = os.path.join(args.central_dir, "puWeights_BCDEFGHI.json.gz")
    if os.path.exists(alt) and args.era_set != "BCDEFGHI":
        c, n = load_correction(alt)
        sources.append((n, c, "seagreen"))

    # Corrections whose EFFECT is compared on pages 5 and 6: page 3 shows the weight
    # curves differ, these two pages show what that difference does to the MC. Colours
    # match page 3 so the same source reads the same across the document.
    corr_set = [("central", "central", main_corr, "crimson")]
    repo_path = ensure_repo_json(args.repo_json, REPO_JSON_URL)
    if repo_path:
        c, n = load_correction(repo_path)
        sources.append((f"{n}  (lumi. corr. repo)", c, "darkorange"))
        corr_set.append(("repo", "lumi. corr. repo", c, "darkorange"))
    log(f"  corrections applied to MC: {', '.join(l for _, l, _, _ in corr_set)}")

    # Pages 5-7 compare central vs stopgap; page 8 needs every per-era correction applied
    # to the MC as well, so the reader gets the union.
    weight_corrs = list(corr_set) + [(f"era_{e}", f"era {e}", c, "crimson")
                                     for e, c in era_corrs]

    # --- MC profiles -------------------------------------------------------
    samples = discover_samples(args.n_signal_points, QCD_BINS,
                               with_minbias=not args.no_minbias)
    profiles, read_tot, avail_tot = [], 0, 0
    for tag, directory, color, kind in samples:
        # QCD bins hold thousands of files and only their SHAPE is used, so they are
        # capped independently -- including on a "full" run, where n_files is None.
        cap, frac = n_files, None
        if kind == "qcd":
            cap = args.n_qcd_files if cap is None else min(cap, args.n_qcd_files)
        elif kind == "minbias":
            frac = args.minbias_frac
        log(f"\n=== {tag} ===")
        try:
            s = read_sample(directory, cap, weight_corrs, frac=frac,
                            seed=args.minbias_seed)
        except Exception as exc:
            log(f"  [warn] skipping: {exc}", file=sys.stderr)
            continue
        if s["nti"].sum() == 0:
            log("  [warn] no entries -- skipping", file=sys.stderr)
            continue
        mean, rms = stats(s["nti"])
        log(f"  {s['read']} of {s['avail']} files, {int(s['nti'].sum()):,} events, "
            f"<n>={mean:.2f}, RMS={rms:.2f}")
        # legend_avail is what the partial-sample legend divides by; avail stays the true
        # file count for the log line. For a kind read at its intended cap they are equal,
        # so `read < avail` is false and the sample drops out of the legend entirely --
        # without pretending, in the log, that more was read.
        #
        # "Intended cap" is checked, not assumed: a --test run reads ONE file per sample,
        # and calling that complete would be a lie of exactly the kind this legend exists
        # to prevent. Only a run at (or above) the configured cap earns the label.
        complete = kind in SAMPLE_CAPS_ARE_COMPLETE and not args.test and (
            args.n_qcd_files >= QCD_MAX_FILES if kind == "qcd"
            else args.minbias_frac >= MINBIAS_FRAC)
        s.update(tag=tag, color=color, kind=kind, complete=complete,
                 legend_avail=(s["read"] if complete else s["avail"]))
        profiles.append(s)
        read_tot += s["read"]
        avail_tot += s["legend_avail"]
    if not profiles:
        raise SystemExit("[error] no sample could be read")
    # "Full" = all signal files and the intended QCD cap. The caps are then the chosen
    # configuration rather than a shortfall, so declaring the sample complete switches
    # off every "Partial sample plot" banner at once -- cms.is_partial() drives them all.
    full_mode = ((n_files is None) and args.n_qcd_files >= QCD_MAX_FILES
                 and (args.no_minbias or args.minbias_frac >= MINBIAS_FRAC))
    cms.set_sample_files(read_tot, read_tot if full_mode else avail_tot)
    if full_mode:
        log(f"\n[FULL MODE] all signal files, {args.n_qcd_files}/QCD bin, "
            f"{100 * args.minbias_frac:g}% of MinBias "
            f"-- partial-sample banners suppressed")

    # The two background profiles are kept SEPARATE from here on. Pages 2-6 used to work
    # from a single sum over every sample read, which is dominated by whichever sample
    # contributed the most files -- an artefact of the read, not of the physics -- and
    # which silently averages away any disagreement between two independent productions.
    # QCD (summed over its pT-hat bins) and MinBias are now carried side by side, so every
    # page shows whether they agree instead of assuming it.
    qcd_total = np.zeros(len(PU_BINS) - 1)
    mb_total = np.zeros(len(PU_BINS) - 1)
    for s in profiles:
        if s["kind"] == "qcd":
            qcd_total += s["nti"]
        elif s["kind"] == "minbias":
            mb_total += s["nti"]
    if qcd_total.sum() == 0:
        raise SystemExit("[error] no QCD profile was read -- pages 2-6 have no background")
    if mb_total.sum() == 0:
        mb_total = None      # --no-minbias: every MinBias curve is simply not drawn

    # --- data for page 6 ---------------------------------------------------
    data = None
    if args.data_frac > 0:
        log("\n=== DATA (page 6) ===")
        cert = None if args.no_golden else load_golden(args.golden_json)
        if cert is None and not args.no_golden:
            log(f"  [warn] no golden JSON at {args.golden_json} -- using ALL data events",
                file=sys.stderr)
        try:
            all_data = collect_data_files(args.data_streams)
            n_pick = max(1, round(args.data_frac * len(all_data)))
            if args.max_data_files > 0:
                n_pick = min(n_pick, args.max_data_files)
            if args.test:
                n_pick = min(n_pick, 2)
            picked = random.Random(args.data_seed).sample(all_data, n_pick)
            log(f"  {len(all_data):,} data files total; reading a random "
                f"{100 * n_pick / len(all_data):.3f}% = {n_pick} of them "
                f"(seed {args.data_seed})")

            # The draw is uniform over FILES, so eras and streams enter in proportion to
            # their file counts -- not to luminosity, and not evenly. Log what actually
            # came out, so "is the sample representative?" is answerable from the log
            # rather than assumed.
            by_stream, by_era = {}, {}
            for u in picked:
                st, er = data_key(u)
                by_stream[st] = by_stream.get(st, 0) + 1
                by_era[er] = by_era.get(er, 0) + 1
            for name, table in (("stream", by_stream), ("era", by_era)):
                log(f"  draw composition by {name}:")
                for k in sorted(table):
                    log(f"    {k:34s} {table[k]:>6,}  ({100 * table[k] / n_pick:5.2f}%)")
            n_single = sum(v for k, v in by_stream.items() if "SingleMuon" in k)
            n_double = sum(v for k, v in by_stream.items() if "DoubleMuonLowMass" in k)
            log(f"  eras represented: {len(by_era)} of the 18 in the sample area")
            log(f"  PD split: SingleMuon {n_single:,} ({100 * n_single / n_pick:.1f}%), "
                f"DoubleMuonLowMass {n_double:,} ({100 * n_double / n_pick:.1f}%)"
                f"   [--data-streams {args.data_streams}]")

            d = read_data_npv(picked, cert)
            if d["total"].sum() > 0:
                m, r = stats(d["total"], NPV_CENTRES)
                log(f"  {d['n_evt']:,} data events, <N_PV>={m:.2f}, RMS={r:.2f}")
                if d["n_rejected"]:
                    rm, rr = stats(d["rejected"], NPV_CENTRES)
                    frac = 100.0 * d["n_rejected"] / (d["n_evt"] + d["n_rejected"])
                    log(f"  golden JSON rejected {d['n_rejected']:,} events ({frac:.2f}%), "
                        f"<N_PV>={rm:.2f}, RMS={rr:.2f}")
                for era in sorted(d["per_era"]):
                    em, er_ = stats(d["per_era"][era], NPV_CENTRES)
                    log(f"    {era:24s} {d['per_era_n'][era]:>12,} evt   "
                        f"<N_PV>={em:5.2f}  RMS={er_:5.2f}")
                d.update(read=n_pick, total_files=len(all_data))
                data = d
        except Exception as exc:
            log(f"  [warn] data page skipped: {exc}", file=sys.stderr)

    # --- pages -------------------------------------------------------------
    log("\n=== Writing PDF ===")

    def save(fig):
        """Every page goes through here, so the transparency is applied once."""
        _transparent_legends(fig)
        # No bbox_inches="tight" -- it crops to content, which is what made pages of the
        # same figsize come out at different sizes. Layout is handled per page instead.
        pdf.savefig(fig)

    with PdfPages(args.output) as pdf:
        # plot_profiles() writes its own per-sample partial-read legend, so no
        # stamp_partial() here -- that would add a second one on the ratio panel.
        save(plot_profiles(profiles))

        save(plot_central_weights(main_corr, main_name, qcd_total, mb_total))

        if len(sources) > 1:
            save(plot_sources(sources, qcd_total, mb_total))
        else:
            log("  [warn] only one weight source available -- skipping page 3",
                file=sys.stderr)

        if era_corrs:
            save(plot_eras(era_corrs, main_corr, main_name, qcd_total, mb_total))

        save(plot_closure(profiles, corr_set))

        if data is not None:
            save(plot_npv_closure(profiles, data["total"], data["n_evt"], data["read"],
                                  data["total_files"], corr_set,
                                  full_mode=(n_files is None)))
            era_fig = plot_data_eras(data, profiles, corr_set)
            if era_fig is not None:
                save(era_fig)
            else:
                log("  [warn] no era passed the statistics cut -- skipping page 7",
                    file=sys.stderr)
            if era_corrs:
                m_fig = plot_era_matched(data, profiles, era_corrs, "central", "combined")
                if m_fig is not None:
                    save(m_fig)
                else:
                    log("  [warn] no era passed the statistics cut -- skipping page 8",
                        file=sys.stderr)
        else:
            log("  [warn] no data read -- skipping page 6", file=sys.stderr)
        plt.close("all")

    log(f"\nSaved: {args.output}")
    if not args.no_publish:
        publish(args.output, WEBDIR)


if __name__ == "__main__":
    main()
