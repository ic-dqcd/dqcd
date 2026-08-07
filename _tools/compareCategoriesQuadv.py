#!/usr/bin/env python3
"""Cross-checks for the four-muon (quadv) selection -- SIGNAL POINTS ONLY.

Only events that pass the trigger + offline kinematic pre-selection (same as
getSignalEff_noMET.C f_kin_or: HLT_Mu10_Barrel_L1HP11_IP6 OR HLT_DoubleMu4_3_LowMass
AND, event-level over muonSVs, the Mu10 leg [(mu1pt>10 & |mu1eta|<1.2) ||
(mu2pt>10 & |mu2eta|<1.2)] OR the DoubleMu leg [max(mu1pt,mu2pt)>4 & min(mu1pt,mu2pt)>3])
and contain a valid "fourmuonSV + 2 consistent muonSV" configuration (the quadv group,
exactly as built by modules/muonsv_selection.py's select_fourmuon_plus_dimuon) enter
the plots. The Python matcher below is a faithful port of that C++ function.

Plot formatting follows the CMS conventions -- see the CMS_LABEL / SIM_HEADER block and
_cms_axes() below. In short: bold "CMS" + italic "Simulation Preliminary", ticks mirrored
inwards on all four sides, and the plot title reserved for the CMS label and the
energy/year (no luminosity, since every page is normalised simulation with no data).
Selections go in an in-plot legend, broader context in the page title.

If only part of the sample is read (--test, or --n-signal below the file count), every
plot says so via a "Partial sample plot (N of M files)" legend, and lumi_header() scales
the luminosity by the same fraction -- see SAMPLE_FILES.

Output PDF (compareCategoriesQuadv.pdf): ONE plot per page, all signal points overlaid.
Nine pages:

  1. Delta_xy(SV1,SV2) / max(dxyErr1, dxyErr2), dxyErr = dxy/dxySig
  2. Delta_3D(SV1,SV2) / max(dlenErr1, dlenErr2), dlenErr = dlen/dlenSig
     (Delta_xy = sqrt(dx^2+dy^2), Delta_3D = sqrt(dx^2+dy^2+dz^2))
  3. Delta_xy(SV1,SV2) overlaid with fourmuonSV_dxy   [log-x, log-y]
  4. ratio fourmuonSV_dxy / Delta_xy(SV1,SV2)          [log-x, log-y]
  5. pointing-angle definitions for the selected fourmuonSV [log-y]:
     * the stored fourmuonSV_pAngle
     * a scouting-style estimate: 3D angle between the four-muon momentum (sum of
       the four muons) and the SV displacement (SV - PV), acos(p.d/(|p||d|)), cf.
       https://github.com/cmstas/run3_scouting/blob/master/fillHistosScouting.py#L1434
  6. bin-by-bin ratio hist(fourmuonSV_pAngle) / hist(computed pAngle)
     (flat at 1 == the two definitions agree).
  7. quadv category populations vs dxy, split into two fourmuonSV_pAngle categories
     (< 0.2 and > 0.2), solid = fourmuonSV_dxy, dashed = the true displacement estimated
     from the 2 matched muonSVs (transverse distance from the PV to the midpoint of the
     two dimuon vertices), with the dxy category edges (1, 10 cm) marked and a counts
     table per panel.
  8. same, pAngle-inclusive.
  9. ratio of the two dxy definitions (fourmuonSV_dxy / 2-muonSV midpoint) vs dxy.

(A former page 10 compared both reco dxy definitions to a "gen truth" built as the
midpoint of the two dark-pion decay vertices. It has been removed: that truth shares its
midpoint construction with the 2-muonSV estimator, so the comparison was circular and the
"which estimator wins" fraction was decided by the definition, not by the physics.)

Run after sourcing setup.sh:
    python _tools/compareCategoriesQuadv.py [--output path.pdf] [--n-signal N] [--test]

--test reads only 1 file per signal point for a quick debug pass.
"""

import argparse
import math
import os
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.legend_handler import HandlerTuple

import cmsstyle as cms

XRD_SERVER = "root://gfe02.grid.hep.ph.ic.ac.uk/"
BASE       = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024"
SIG_BASE   = BASE

# --- CMS plotting conventions -------------------------------------------------
# Shared with the other _tools/compare*.py scripts; see _tools/cmsstyle.py for the rules.
CMS_LABEL   = cms.CMS_LABEL
SIM_HEADER  = cms.SIM_HEADER
BAND_ALPHA  = cms.BAND_ALPHA
lumi_header = cms.lumi_header
_cms_axes   = cms.cms_axes
_info_legend = cms.info_legend
_blank_entry = cms.blank_entry
_is_partial  = cms.is_partial

# Signal points: the two ctau=10 points shown in compareDeltaR, plus the same two
# mass points at ctau=0.1. Each entry: dir, plot label, colour, scenario.
# Plots are produced one scenario at a time ("A" and "B1" kept separate).
SIGNALS = [
    {
        "dir":   ("GluGluHToDarkShowers-ScenarioA_Par-ctau-0p1-mA-3p33-mpi-10"
                  "_TuneCP5_13p6TeV_powheg-pythia8"),
        "label": r"Scenario A: $m_\pi$=10 GeV, $m_A$=3.33 GeV, $c\tau$=0.1 mm",
        "color": "forestgreen", "tag": r"A c$\tau$=0.1",
    },
    {
        "dir":   ("GluGluHToDarkShowers-ScenarioB1_Par-ctau-0p1-mA-1p33-mpi-4"
                  "_TuneCP5_13p6TeV_powheg-pythia8"),
        "label": r"Scenario B1: $m_\pi$=4 GeV, $m_A$=1.33 GeV, $c\tau$=0.1 mm",
        "color": "crimson", "tag": r"B1 c$\tau$=0.1",
    },
    {
        "dir":   ("GluGluHToDarkShowers-ScenarioB1_Par-ctau-10-mA-1p33-mpi-4"
                  "_TuneCP5_13p6TeV_powheg-pythia8"),
        "label": r"Scenario B1: $m_\pi$=4 GeV, $m_A$=1.33 GeV, $c\tau$=10 mm",
        "color": "darkviolet", "tag": r"B1 c$\tau$=10",
    },
]
for _s in SIGNALS:
    _s["path"] = f"{SIG_BASE}/{_s['dir']}"

TREE_NAME = "Events"

N_SIGNAL_FILES = 60  # files per signal point (full mode; caps at all available, <=50)

# --- quadv matching cuts (mirror modules/muonsv_selection.py) -----------------
CHI2_MAX    = 10.0    # fourmuonSV and muonSV chi2 must be < CHI2_MAX
DR_MAX      = 1.2     # dimuon deltaR must be < DR_MAX
MASS_COH    = 0.03    # |mA - mB| / mA must be < MASS_COH

# branches to read per collection
FOURMU_BRANCHES = (
    ["fourmuonSV_chi2", "fourmuonSV_charge", "fourmuonSV_mass", "fourmuonSV_dxy",
     "fourmuonSV_x", "fourmuonSV_y", "fourmuonSV_z", "fourmuonSV_pAngle"]
    + [f"fourmuonSV_mu{i}index" for i in (1, 2, 3, 4)]
    + [f"fourmuonSV_mu{i}pt"    for i in (1, 2, 3, 4)]
    + [f"fourmuonSV_mu{i}eta"   for i in (1, 2, 3, 4)]
    + [f"fourmuonSV_mu{i}phi"   for i in (1, 2, 3, 4)]
)
MUONSV_BRANCHES = [
    "muonSV_chi2", "muonSV_charge", "muonSV_mass",
    "muonSV_mu1pt", "muonSV_mu1eta", "muonSV_mu1phi",
    "muonSV_mu2pt", "muonSV_mu2eta", "muonSV_mu2phi",
    "muonSV_mu1index", "muonSV_mu2index",
    "muonSV_x", "muonSV_y", "muonSV_z",
    "muonSV_dxy", "muonSV_dxySig", "muonSV_dlen", "muonSV_dlenSig",
    # IP6 leg: sip3d lives in MuonBPark, reached via muonSV_mu{1,2}index
    "MuonBPark_sip3d",
]
PV_BRANCHES = ["PV_x", "PV_y", "PV_z"]

# Event must fire EITHER trigger (single-muon OR double-muon). Missing branches are
# treated as not-fired.
TRIGGERS = ["HLT_Mu10_Barrel_L1HP11_IP6", "HLT_DoubleMu4_3_LowMass"]

MUON_MASS = 0.1057  # GeV

# proxy: prefer the one already in the environment (setup.sh sets X509_USER_PROXY)
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
# reading
# ----------------------------------------------------------------------------
def read_branches(urls, branches, label):
    """Read *branches* from every URL, concatenated event-by-event.

    Returns a dict {branch: awkward array}. Jagged collection branches stay
    jagged; flat per-event branches (PV_*) come back 1-D. Missing branches in a
    file cause that file to be skipped (with a warning)."""
    import uproot
    import awkward as ak
    parts = {b: [] for b in branches}
    n = len(urls)
    for i, url in enumerate(urls, 1):
        fname = url.split("/")[-1]
        log(f"  [{i}/{n}] {fname}")
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                keys = set(tree.keys())
                missing = [b for b in branches if b not in keys]
                if missing:
                    log(f"  [warn] {fname}: missing {missing} -- skipping", file=sys.stderr)
                    continue
                arrs = tree.arrays(branches, library="ak")
                nev = len(arrs)
                # event-level trigger OR mask; keep only events that fired
                present = [t for t in TRIGGERS if t in keys]
                if i == 1 and len(present) < len(TRIGGERS):
                    log(f"  [warn] {label}: trigger(s) absent, treated as not-fired: "
                        f"{[t for t in TRIGGERS if t not in keys]}", file=sys.stderr)
                tmask = np.zeros(nev, dtype=bool)
                for t in present:
                    tmask |= tree[t].array(library="np").astype(bool)
                # offline kinematic legs (f_kin_or from getSignalEff_noMET.C), event-level
                # Any over muonSVs: Mu10 leg OR DoubleMu leg
                # Mirrors modules/muon_selection.py: Mu10 leg pt>10, |eta|<0.8, |sip3d|>6
                # (was |eta|<1.2, no sip3d); DoubleMu leg pt>4/3, |eta|<2.0, |sip3d|>6.
                m1pt, m1eta = arrs["muonSV_mu1pt"], arrs["muonSV_mu1eta"]
                m2pt, m2eta = arrs["muonSV_mu2pt"], arrs["muonSV_mu2eta"]
                sip = arrs["MuonBPark_sip3d"]
                s1 = np.abs(sip[arrs["muonSV_mu1index"]])
                s2 = np.abs(sip[arrs["muonSV_mu2index"]])
                mu10 = ((m1pt > 10) & (np.abs(m1eta) < 0.8) & (s1 > 6)) | \
                       ((m2pt > 10) & (np.abs(m2eta) < 0.8) & (s2 > 6))
                mx, mn = np.maximum(m1pt, m2pt), np.minimum(m1pt, m2pt)
                dmu = ((mx > 4) & (mn > 3)
                       & (np.abs(m1eta) < 2.4) & (np.abs(m2eta) < 2.4)
                       & ((s1 > 6) | (s2 > 6)))
                kin = ak.to_numpy(ak.any(mu10 | dmu, axis=1))
                mask = tmask & kin       # trigger + kinematic pre-selection
                arrs = arrs[mask]
                for b in branches:
                    parts[b].append(arrs[b])
                log(f"         -> {nev:,} events ({int(tmask.sum()):,} trig, "
                    f"{int(mask.sum()):,} trig+kin)")
        except Exception as exc:
            log(f"  [warn] skipping {fname}: {exc}", file=sys.stderr)
    if not parts[branches[0]]:
        return None
    return {b: ak.concatenate(parts[b]) for b in branches}


# ----------------------------------------------------------------------------
# quadv matching (Python port of select_fourmuon_plus_dimuon)
# ----------------------------------------------------------------------------
def _deltaR(eta1, phi1, eta2, phi2):
    deta = eta1 - eta2
    dphi = math.atan2(math.sin(phi1 - phi2), math.cos(phi1 - phi2))
    return math.hypot(deta, dphi)


def match_quadv(data, label):
    """For every event find the first valid fourmuonSV + 2 consistent muonSV.

    *data* merges the fourmuonSV/muonSV dicts for one signal. Returns a list of
    selected events as dicts with the resolved indices (one per matched event)::

        {"evt": e, "fourmu": i, "sv1": a, "sv2": b}

    Mirrors modules/muonsv_selection.py::select_fourmuon_plus_dimuon exactly.
    """
    import awkward as ak

    # only events with >=1 fourmuonSV AND >=2 muonSV can possibly match
    nfour = ak.num(data["fourmuonSV_chi2"])
    ntwo  = ak.num(data["muonSV_chi2"])
    cand  = np.where((ak.to_numpy(nfour) >= 1) & (ak.to_numpy(ntwo) >= 2))[0]
    log(f"  [{label}] {len(cand):,} candidate events (>=1 fourmuonSV & >=2 muonSV)"
        f" of {len(nfour):,}")

    # pull only the candidate events to python lists (fast enough; small subset)
    sub = {b: ak.to_list(data[b][cand]) for b in data
           if b.startswith(("fourmuonSV_", "muonSV_"))}

    selected = []
    for k, e in enumerate(cand):
        f_chi2 = sub["fourmuonSV_chi2"][k]
        f_chg  = sub["fourmuonSV_charge"][k]
        f_mu   = [sub[f"fourmuonSV_mu{j}index"][k] for j in (1, 2, 3, 4)]
        sv_chi2 = sub["muonSV_chi2"][k]
        sv_chg  = sub["muonSV_charge"][k]
        sv_mass = sub["muonSV_mass"][k]
        sv_m1e, sv_m1p = sub["muonSV_mu1eta"][k], sub["muonSV_mu1phi"][k]
        sv_m2e, sv_m2p = sub["muonSV_mu2eta"][k], sub["muonSV_mu2phi"][k]
        sv_i1, sv_i2 = sub["muonSV_mu1index"][k], sub["muonSV_mu2index"][k]
        nsv = len(sv_chi2)

        hit = None
        for i in range(len(f_chi2)):
            if f_chi2[i] >= CHI2_MAX or f_chg[i] != 0:
                continue
            four = {f_mu[0][i], f_mu[1][i], f_mu[2][i], f_mu[3][i]}

            def good_sv(a):
                return (sv_chg[a] == 0 and sv_chi2[a] < CHI2_MAX
                        and _deltaR(sv_m1e[a], sv_m1p[a], sv_m2e[a], sv_m2p[a]) < DR_MAX
                        and sv_i1[a] in four and sv_i2[a] in four)

            for a in range(nsv):
                if not good_sv(a):
                    continue
                for b in range(a + 1, nsv):
                    if not good_sv(b):
                        continue
                    combined = {sv_i1[a], sv_i2[a], sv_i1[b], sv_i2[b]}
                    if len(combined) != 4:
                        continue
                    mA, mB = sv_mass[a], sv_mass[b]
                    if mA <= 0 or mB <= 0:
                        continue
                    if abs(mA - mB) / mA < MASS_COH:
                        hit = (i, a, b)
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            selected.append({"evt": int(e), "fourmu": hit[0], "sv1": hit[1], "sv2": hit[2]})

    log(f"  [{label}] {len(selected):,} events with a quadv match")
    return selected


# ----------------------------------------------------------------------------
# observables from matched events
# ----------------------------------------------------------------------------
def compute_observables(data, matches, label):
    """Turn the matched events into the 1-D arrays the plots need."""
    import awkward as ak
    fx = ak.to_list(data["fourmuonSV_x"]);   fy = ak.to_list(data["fourmuonSV_y"])
    fz = ak.to_list(data["fourmuonSV_z"]);   fpa = ak.to_list(data["fourmuonSV_pAngle"])
    fdxy = ak.to_list(data["fourmuonSV_dxy"])
    fpt = {j: ak.to_list(data[f"fourmuonSV_mu{j}pt"])  for j in (1, 2, 3, 4)}
    fet = {j: ak.to_list(data[f"fourmuonSV_mu{j}eta"]) for j in (1, 2, 3, 4)}
    fph = {j: ak.to_list(data[f"fourmuonSV_mu{j}phi"]) for j in (1, 2, 3, 4)}
    sx = ak.to_list(data["muonSV_x"]); sy = ak.to_list(data["muonSV_y"]); sz = ak.to_list(data["muonSV_z"])
    sdxy = ak.to_list(data["muonSV_dxy"]); sdxysig = ak.to_list(data["muonSV_dxySig"])
    sdlen = ak.to_list(data["muonSV_dlen"]); sdlensig = ak.to_list(data["muonSV_dlenSig"])
    pvx = ak.to_numpy(data["PV_x"]); pvy = ak.to_numpy(data["PV_y"]); pvz = ak.to_numpy(data["PV_z"])

    dxy12, d3d12, dxy_pull, d3d_pull, fourmu_dxy, dxy_ratio = [], [], [], [], [], []
    pang_stored, pang_est = [], []
    est2sv_dxy = []  # displacement estimated from the 2 matched muonSVs (see below)
    for m in matches:
        e, i, a, b = m["evt"], m["fourmu"], m["sv1"], m["sv2"]

        # page 1: distances between the two matched muonSVs vs their uncertainties,
        # plus fourmuonSV_dxy and the fourmuonSV_dxy / Delta_xy ratio
        dxy = math.hypot(sx[e][a] - sx[e][b], sy[e][a] - sy[e][b])      # transverse
        d3d = math.sqrt((sx[e][a] - sx[e][b]) ** 2 +
                        (sy[e][a] - sy[e][b]) ** 2 +
                        (sz[e][a] - sz[e][b]) ** 2)                      # 3D
        # per-SV uncertainties: dxyErr = dxy/dxySig, dlenErr = dlen/dlenSig
        dxyerr_a = sdxy[e][a] / sdxysig[e][a] if sdxysig[e][a] > 0 else float("nan")
        dxyerr_b = sdxy[e][b] / sdxysig[e][b] if sdxysig[e][b] > 0 else float("nan")
        dlenerr_a = sdlen[e][a] / sdlensig[e][a] if sdlensig[e][a] > 0 else float("nan")
        dlenerr_b = sdlen[e][b] / sdlensig[e][b] if sdlensig[e][b] > 0 else float("nan")
        dxyerr_max = max(dxyerr_a, dxyerr_b)
        dlenerr_max = max(dlenerr_a, dlenerr_b)
        fdxy_i = fdxy[e][i]

        dxy12.append(dxy)
        d3d12.append(d3d)
        dxy_pull.append(dxy / dxyerr_max if dxyerr_max > 0 else float("nan"))
        d3d_pull.append(d3d / dlenerr_max if dlenerr_max > 0 else float("nan"))
        fourmu_dxy.append(fdxy_i)
        dxy_ratio.append(fdxy_i / dxy if dxy > 0 else float("nan"))

        # true displacement estimated from the 2 matched muonSVs: the two dimuon vertices
        # SV1=(sx[a],sy[a]), SV2=(sx[b],sy[b]) are the two dark-pion decay points; their
        # equal-weight midpoint is the best single-point proxy for where the four-muon
        # system decays. Its transverse distance from the PV is the displacement estimate,
        # directly analogous to nanotron's fourmuonSV_dxy = |SV_4mu - PV|_xy. This combines
        # BOTH muonSVs (unlike the framework binning var, which uses only one vertex's dxy).
        mx = 0.5 * (sx[e][a] + sx[e][b])
        my = 0.5 * (sy[e][a] + sy[e][b])
        est2sv_dxy.append(math.hypot(mx - pvx[e], my - pvy[e]))

        # page 2: stored pAngle of the selected fourmuonSV
        stored = fpa[e][i]
        pang_stored.append(stored)

        # scouting-style estimate: 3D angle between four-muon momentum and (SV - PV)
        px = py = pz = 0.0
        for j in (1, 2, 3, 4):
            pt, eta, phi = fpt[j][e][i], fet[j][e][i], fph[j][e][i]
            px += pt * math.cos(phi)
            py += pt * math.sin(phi)
            pz += pt * math.sinh(eta)
        dx, dy, dz = fx[e][i] - pvx[e], fy[e][i] - pvy[e], fz[e][i] - pvz[e]
        pmag = math.sqrt(px * px + py * py + pz * pz)
        dmag = math.sqrt(dx * dx + dy * dy + dz * dz)
        if pmag > 0 and dmag > 0:
            cosa = (px * dx + py * dy + pz * dz) / (pmag * dmag)
            cosa = max(-1.0, min(1.0, cosa))
            est = math.acos(cosa)
        else:
            est = float("nan")
        pang_est.append(est)

    clean = lambda v: np.array([x for x in v if x == x], dtype=float)  # drop NaNs
    # aligned (jointly-cleaned) arrays for the category-population plots: per matched
    # event keep fourmuonSV_dxy, the 2-muonSV midpoint displacement and fourmuonSV_pAngle
    fd = np.array(fourmu_dxy, dtype=float)
    qd = np.array(est2sv_dxy, dtype=float)
    fp = np.array(pang_stored, dtype=float)
    cm = np.isfinite(fd) & np.isfinite(qd) & np.isfinite(fp)
    log(f"  [{label}] {int(cm.sum()):,} of {len(matches):,} matched events enter the "
        f"category pages")
    return {
        "dxy12":       clean(dxy12),
        "d3d12":       clean(d3d12),
        "dxy_pull":    clean(dxy_pull),
        "d3d_pull":    clean(d3d_pull),
        "fourmu_dxy":  clean(fourmu_dxy),
        "dxy_ratio":   clean(dxy_ratio),
        "pang_stored": clean(pang_stored),
        "pang_est":    clean(pang_est),
        # aligned per-event category inputs
        "cat_fourmu_dxy": fd[cm],
        "cat_est_dxy":    qd[cm],
        "cat_fpa":        fp[cm],
    }


# ----------------------------------------------------------------------------
# plotting
# ----------------------------------------------------------------------------
def _norm_hist(ax, values, bins, color, label=None, ls="-", err="band"):
    """Normalised step histogram. *err* controls the uncertainty drawing:
      "band" -> shaded sqrt(N)/N band following the steps (used for solid lines)
      "bars" -> standard error bars at bin centres (used for dashed lines)
      None   -> line only."""
    if len(values) == 0:
        if label:
            log(f"  [warn] '{label}': 0 entries -- not plotted", file=sys.stderr)
        return
    counts, edges = np.histogram(values, bins=bins)
    total = counts.sum()
    norm = counts / total if total > 0 else counts * 0.0
    e = np.sqrt(counts) / total if total > 0 else counts * 0.0
    ax.stairs(norm, edges, color=color, linewidth=2, linestyle=ls, label=label)
    if err == "band":
        lo = np.clip(norm - e, 1e-12, None)   # keep positive for log-y axes
        hi = norm + e
        ax.fill_between(edges, np.r_[lo, lo[-1]], np.r_[hi, hi[-1]],
                        step="post", color=color, alpha=BAND_ALPHA, linewidth=0)
    elif err == "bars":
        centres = 0.5 * (edges[:-1] + edges[1:])
        ax.errorbar(centres, norm, yerr=e, fmt="none", ecolor=color, alpha=0.8,
                    elinewidth=1, capsize=2)


def _curve_legend(ax, sig_obs, count_key, style_specs, loc="upper right", fontsize=None):
    """ONE frameless legend for the whole plot: a coloured line per signal point, a blank
    spacer row, then the line-style key. Everything describing the curves belongs in the
    same box -- two legends in different corners are harder to read than one.

    *style_specs* = list of (kind, label) with kind in {"band", "bars"}, so the style key
    visually shows the uncertainty style: a shaded band behind a solid line ("band"), or a
    dashed line with error-bar caps ("bars")."""
    fontsize = cms.FS_LEGEND if fontsize is None else fontsize
    handles = [Line2D([], [], color=s["color"], lw=2) for s, _ in sig_obs]
    labels  = [f"{s['label']} ({len(o[count_key]):,})" for s, o in sig_obs]

    blank_h, blank_l = _blank_entry()
    handles.append(blank_h)
    labels.append(blank_l)

    hmap = {}
    for kind, label in style_specs:
        if kind == "band":
            h = (Patch(facecolor="black", alpha=BAND_ALPHA, edgecolor="none"),
                 Line2D([], [], color="black", lw=2, ls="-"))
            hmap[h] = HandlerTuple(ndivide=1)  # overlay patch + line
        else:  # bars: dashed line with error-bar caps (NaN data -> nothing on axes)
            h = ax.errorbar([np.nan], [np.nan], yerr=[np.nan], color="black",
                            lw=2, ls="--", capsize=3, marker="")
        handles.append(h)
        labels.append(label)

    ax.legend(handles=handles, labels=labels, loc=loc, fontsize=fontsize,
              **cms.LEGEND_KW, handler_map=hmap)


def _extend_log_top(ax, frac=0.75):
    """Raise the (log) y upper limit so the tallest bar fills only *frac* of the axis
    height, leaving headroom for the legend."""
    lo, hi = ax.get_ylim()
    if lo <= 0 or hi <= 0:
        return
    log_lo, log_hi = math.log10(lo), math.log10(hi)
    ax.set_ylim(lo, 10 ** (log_lo + (log_hi - log_lo) / frac))


def _auto_bins(arrays, nbins=60, lo=0.0):
    """Linear bin edges from lo to the 99th percentile over all non-empty arrays."""
    nonempty = [a for a in arrays if len(a)]
    allv = np.concatenate(nonempty) if nonempty else np.array([1.0])
    hi = np.percentile(allv, 99) if len(allv) > 1 else 1.0
    return np.linspace(lo, max(hi, lo + 1e-3), nbins)


def _auto_log_bins(arrays, nbins=60, hi=None):
    """Log-spaced bin edges from the 1st to 99th percentile of positive values.
    *hi* (cm) overrides the upper edge (e.g. 100 to show the full displacement range)."""
    nonempty = [a[a > 0] for a in arrays if len(a)]
    allv = np.concatenate([a for a in nonempty if len(a)]) if nonempty else np.array([1.0])
    if len(allv) < 2:
        return np.logspace(-3, np.log10(hi) if hi else 0, nbins)
    lo = max(np.percentile(allv, 1), allv.min())
    hi = hi if hi is not None else np.percentile(allv, 99)
    if hi <= lo:
        hi = lo * 10
    return np.logspace(np.log10(lo), np.log10(hi), nbins)


def _suptitle(fig, note=None):
    """Page title. Clarifying information lives HERE (or in an in-plot legend), never in
    the plot title, which carries only the CMS label and the energy/year. *note* carries
    the verbose version of anything kept terse on the axes.

    Also stamps the "Partial sample plot" warning onto every axes of the page that has not
    already got an info legend of its own, so a partial read can never go unstated."""
    cms.stamp_partial(fig)
    txt = ("quadv: fourmuonSV + 2 consistent muonSV\n"
           "trigger (Mu10 OR DoubleMu) + offline kinematic pre-selection")
    if note:
        txt += "\n" + note
    fig.suptitle(txt, fontsize=cms.FS_TITLE)
    fig.tight_layout(rect=[0, 0, 1, 0.93 if note else 0.95])


# the y axis just says "Fraction of events"; this spells out what that means
NORM_NOTE = "each distribution is normalised to unit area; bands/bars are statistical only"


def page_dxy_pull(sig_obs):
    """Delta_xy(SV1,SV2) / max(dxyErr1, dxyErr2)  (transverse pull)."""
    fig, ax = plt.subplots(figsize=(10, 8))
    bins = _auto_bins([o["dxy_pull"] for _, o in sig_obs])
    for sig, o in sig_obs:
        _norm_hist(ax, o["dxy_pull"], bins, sig["color"],
                   f"{sig['label']} ({len(o['dxy_pull']):,})")
    ax.set_xlabel("2D distance significance", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
    _cms_axes(ax, fontsize=cms.FS_AXES)
    ax.legend(fontsize=cms.FS_LEGEND, **cms.LEGEND_KW,
              title=r"$\Delta_{xy}(\mathrm{SV}_1,\mathrm{SV}_2)/\max(\mathrm{dxyErr}_1,\mathrm{dxyErr}_2)$,"
                    r" dxyErr=dxy/dxySig")
    _suptitle(fig, NORM_NOTE)
    return fig


def page_d3d_pull(sig_obs):
    """Delta_3D(SV1,SV2) / max(dlenErr1, dlenErr2)  (3D pull)."""
    fig, ax = plt.subplots(figsize=(10, 8))
    bins = _auto_bins([o["d3d_pull"] for _, o in sig_obs])
    for sig, o in sig_obs:
        _norm_hist(ax, o["d3d_pull"], bins, sig["color"],
                   f"{sig['label']} ({len(o['d3d_pull']):,})")
    ax.set_xlabel("3D distance significance", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
    _cms_axes(ax, fontsize=cms.FS_AXES)
    ax.legend(fontsize=cms.FS_LEGEND, **cms.LEGEND_KW,
              title=r"$\Delta_{3D}(\mathrm{SV}_1,\mathrm{SV}_2)/\max(\mathrm{dlenErr}_1,\mathrm{dlenErr}_2)$,"
                    r" dlenErr=dlen/dlenSig")
    _suptitle(fig, NORM_NOTE)
    return fig


def page_dxy_vs_fourmu(sig_obs):
    """Delta_xy(SV1,SV2) (solid) overlaid with fourmuonSV_dxy (dashed); log-x, log-y."""
    fig, ax = plt.subplots(figsize=(10, 8))
    bins = _auto_log_bins([o["dxy12"] for _, o in sig_obs] + [o["fourmu_dxy"] for _, o in sig_obs],
                          hi=100)   # show the full displacement range up to 100 cm
    for sig, o in sig_obs:
        c = sig["color"]
        _norm_hist(ax, o["dxy12"], bins, c, ls="-", err="band")        # solid: Delta_xy
        _norm_hist(ax, o["fourmu_dxy"], bins, c, ls="--", err="bars")  # dashed: fourmuonSV_dxy
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("2D distance [cm]", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
    _cms_axes(ax, fontsize=cms.FS_AXES)
    _extend_log_top(ax, 0.70)   # extra headroom so the legend clears the curves
    _curve_legend(ax, sig_obs, "dxy12",
                 [("band", r"(solid) $\Delta_{xy}(\mathrm{SV}_1,\mathrm{SV}_2)$"),
                  ("bars", "(dashed) fourmuonSV_dxy")])
    _suptitle(fig, NORM_NOTE)
    return fig


def page_dxy_ratio(sig_obs):
    """Ratio fourmuonSV_dxy / Delta_xy(SV1,SV2); log-x, log-y."""
    fig, ax = plt.subplots(figsize=(10, 8))
    bins = _auto_log_bins([o["dxy_ratio"] for _, o in sig_obs])
    for sig, o in sig_obs:
        _norm_hist(ax, o["dxy_ratio"], bins, sig["color"],
                   f"{sig['label']} ({len(o['dxy_ratio']):,})")
    ax.axvline(1.0, color="grey", ls="--", lw=1, alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"fourmuonSV_dxy / $\Delta_{xy}(\mathrm{SV}_1,\mathrm{SV}_2)$", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
    _cms_axes(ax, fontsize=cms.FS_AXES)
    _extend_log_top(ax, 0.80)
    ax.legend(loc="upper right", fontsize=cms.FS_LEGEND, **cms.LEGEND_KW)
    _suptitle(fig, NORM_NOTE)
    return fig


def page_pangle(sig_obs):
    """Stored fourmuonSV_pAngle (solid) vs scouting-style estimate (dashed); log-y."""
    fig, ax = plt.subplots(figsize=(10, 8))
    bins = np.linspace(0, math.pi, 60)
    for sig, o in sig_obs:
        c = sig["color"]
        _norm_hist(ax, o["pang_stored"], bins, c, ls="-", err="band")  # solid: stored pAngle
        _norm_hist(ax, o["pang_est"], bins, c, ls="--", err="bars")    # dashed: computed pAngle
    ax.set_yscale("log")
    ax.set_ylim(bottom=1e-4)   # fixed lower limit (keeps the autoscaled top)
    ax.set_xlabel("Pointing angle [rad]", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
    _cms_axes(ax, fontsize=cms.FS_AXES)
    _curve_legend(ax, sig_obs, "pang_stored",
                 [("band", "(solid) fourmuonSV_pAngle"),
                  ("bars", r"(dashed) $\arccos(\vec{p}_{4\mu}\cdot\vec{d}/|\vec{p}||\vec{d}|)$, "
                           r"$\vec{d}=$SV$-$PV")])
    _suptitle(fig, NORM_NOTE)
    return fig


def page_pangle_ratio(sig_obs):
    """Bin-by-bin ratio hist(fourmuonSV_pAngle) / hist(computed pAngle), per signal."""
    fig, ax = plt.subplots(figsize=(10, 8))
    bins = np.linspace(0, math.pi, 60)             # same binning as the overlay
    centres = 0.5 * (bins[:-1] + bins[1:])
    for sig, o in sig_obs:
        ns, _ = np.histogram(o["pang_stored"], bins=bins)
        ne, _ = np.histogram(o["pang_est"],    bins=bins)
        good = ne > 0
        ratio = np.full(ns.shape, np.nan)
        ratio[good] = ns[good] / ne[good]
        # Poisson error propagation on the bin ratio
        err = np.full(ns.shape, np.nan)
        nz = good & (ns > 0)
        err[nz] = ratio[nz] * np.sqrt(1.0 / ns[nz] + 1.0 / ne[nz])
        ax.errorbar(centres[good], ratio[good], yerr=err[good], fmt="o", ms=4,
                    color=sig["color"], ecolor=sig["color"], capsize=2,
                    label=f"{sig['label']} ({int(ns.sum()):,})")
    ax.axhline(1.0, color="grey", ls="--", lw=1, alpha=0.7)
    ax.set_xlabel("Pointing angle [rad]", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Stored / computed  (per bin)", fontsize=cms.FS_LABEL)
    _cms_axes(ax, fontsize=cms.FS_AXES)
    ax.legend(fontsize=cms.FS_LEGEND, **cms.LEGEND_KW,
              title="hist(fourmuonSV_pAngle) / hist(computed pAngle)")
    _suptitle(fig)
    return fig


# --- quadv category populations -----------------------------------------------
# dxy category edges [cm] (quadv_cat boundaries): <1, 1-10, >10
DXY_EDGES = (1.0, 10.0)
PANGLE_EDGE = 0.2   # quadv pAngle category boundary [rad]


def _dxy_cat_counts(dxy):
    """Entries per dxy category [<1, 1-10, >10] plus total."""
    dxy = np.asarray(dxy)
    return [int(np.sum(dxy < DXY_EDGES[0])),
            int(np.sum((dxy >= DXY_EDGES[0]) & (dxy < DXY_EDGES[1]))),
            int(np.sum(dxy >= DXY_EDGES[1])),
            int(len(dxy))]


def _cat_panel(ax, subset, fs_label=11, fs_axes=10, frac=0.80):
    """dxy distribution: solid = fourmuonSV_dxy, dashed = 2-muonSV midpoint displacement,
    per signal. *subset* = list of (sig, fourmu_dxy, est_dxy). Vertical lines mark edges.
    The split page (two panels) keeps the small default fonts; the inclusive page (one
    plot) passes the larger preferred sizes. Lower *frac* = more headroom above the curves."""
    bins = np.logspace(-4, 2, 60)   # 1e-4 .. 100 cm
    for sig, fd, qd in subset:
        c = sig["color"]
        if len(fd):
            counts, edges = np.histogram(fd, bins=bins)
            ax.stairs(counts, edges, color=c, ls="-", lw=2)
        if len(qd):
            counts, edges = np.histogram(qd, bins=bins)
            ax.stairs(counts, edges, color=c, ls="--", lw=2)
    for edge in DXY_EDGES:
        ax.axvline(edge, color="grey", ls="--", lw=1.2, alpha=0.8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-4, 100)
    ax.set_xlabel("Displacement dxy [cm]", fontsize=fs_label)
    ax.set_ylabel("Number of entries", fontsize=fs_label)
    _cms_axes(ax, fontsize=fs_axes)
    _extend_log_top(ax, frac)


# the two dxy definitions (solid = fourmuonSV's own dxy; dashed = the 2-muonSV estimate:
# transverse distance from the PV to the midpoint of the two matched dimuon vertices)
DEF_SOLID  = r"fourmuonSV_dxy, from fit of the 4-$\mu$"
DEF_DASHED = "2-muonSV midpoint displacement from PV"


def _cat_legend(ax, sig_obs, fontsize=8):
    """ONE frameless legend: the signal points, a blank spacer row, then the two dxy
    definitions (solid/dashed)."""
    handles = [Line2D([], [], color=s["color"], lw=2) for s, _ in sig_obs]
    labels  = [s["label"] for s, _ in sig_obs]

    blank_h, blank_l = _blank_entry()
    handles.append(blank_h)
    labels.append(blank_l)

    handles += [Line2D([], [], color="black", lw=2, ls="-"),
                Line2D([], [], color="black", lw=2, ls="--")]
    labels  += [f"{DEF_SOLID} (solid)", f"{DEF_DASHED} (dashed)"]

    return ax.legend(handles=handles, labels=labels, fontsize=fontsize, loc="upper right",
                     **cms.LEGEND_KW)


def _cat_table(ax, subset, bbox=(0.44, 0.0, 0.54, 0.95), fontsize=7):
    """Little table of entries per (signal, dxy definition) x dxy category.
    Constrained with an explicit bbox so cells stay small and never overflow. *bbox*
    ([x0, y0, w, h] in axes fraction) lets a caller place it below the plot (default) or,
    with a taller/narrower bbox, in a column to its right."""
    ax.axis("off")
    col_labels = [r"dxy$<$1", "1--10", r"dxy$>$10", "Total"]
    rows, cells, row_colors = [], [], []
    for sig, fd, qd in subset:
        rows.append(f"{sig['tag']} fourmuonSV")
        cells.append([f"{v:,}" for v in _dxy_cat_counts(fd)])
        row_colors.append(sig["color"])
        rows.append(f"{sig['tag']} 2muSV mid")
        cells.append([f"{v:,}" for v in _dxy_cat_counts(qd)])
        row_colors.append(sig["color"])
    tbl = ax.table(cellText=cells, rowLabels=rows, colLabels=col_labels,
                   cellLoc="center", rowLoc="center", bbox=list(bbox))
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(fontsize)
    for r, col in enumerate(row_colors):        # colour the row-label text by signal
        tbl[(r + 1, -1)].get_text().set_color(col)


def page_cat_pangle_split(sig_obs):
    """Page: two dxy panels side by side, one per fourmuonSV_pAngle category, each with a
    counts table below. solid = fourmuonSV_dxy, dashed = quadv_muonSV_dxy."""
    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1.4], hspace=0.32, wspace=0.18)
    splits = [(r"Pointing angle $<$ %.1f" % PANGLE_EDGE, lambda fp: fp < PANGLE_EDGE),
              (r"Pointing angle $>$ %.1f" % PANGLE_EDGE, lambda fp: fp >= PANGLE_EDGE)]
    for col, (title, sel) in enumerate(splits):
        subset = []
        for sig, o in sig_obs:
            m = sel(o["cat_fpa"])
            subset.append((sig, o["cat_fourmu_dxy"][m], o["cat_est_dxy"][m]))
        ax = fig.add_subplot(gs[0, col])
        _cat_panel(ax, subset, frac=0.70)   # extra headroom so the legend clears the curves
        _cat_legend(ax, sig_obs)
        # the selection goes in an in-plot legend, not the plot title
        _info_legend(ax, [title])
        _cat_table(fig.add_subplot(gs[1, col]), subset)
    fig.suptitle("quadv category populations vs dxy, split by fourmuonSV_pAngle\n"
                 f"solid: {DEF_SOLID}    dashed: {DEF_DASHED}    "
                 "grey lines: dxy category edges (1, 10 cm)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    return fig


def page_cat_pangle_inclusive(sig_obs):
    """Page: single dxy panel, pAngle-inclusive, with a counts table to its right."""
    fig = plt.figure(figsize=(14, 7))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.3, 1.0], wspace=0.10)
    subset = [(sig, o["cat_fourmu_dxy"], o["cat_est_dxy"]) for sig, o in sig_obs]
    ax = fig.add_subplot(gs[0, 0])
    # one plot per page -> the larger preferred fonts
    _cat_panel(ax, subset, fs_label=cms.FS_LABEL, fs_axes=cms.FS_AXES)
    _cat_legend(ax, sig_obs, fontsize=cms.FS_LEGEND)
    _info_legend(ax)
    # table in the right column, shifted right so its row labels clear the plot and it
    # fills the space under the (wide) page title
    _cat_table(fig.add_subplot(gs[0, 1]), subset, bbox=(0.42, 0.30, 0.56, 0.40), fontsize=8)
    # y=1.03 lifts the title clear of the plot; tight-bbox then keeps that gap (a plain
    # rect margin would be cropped away by bbox_inches="tight")
    fig.suptitle("quadv category populations vs dxy (pAngle-inclusive)\n"
                 f"solid: {DEF_SOLID}    dashed: {DEF_DASHED}    "
                 "grey lines: dxy category edges (1, 10 cm)", fontsize=cms.FS_TITLE, y=1.03)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    return fig


def _dxy_ratio_panel(ax, subset, title):
    """Bin-by-bin ratio hist(fourmuonSV_dxy) / hist(2-muonSV midpoint dxy) per signal, vs dxy."""
    bins = np.logspace(-4, 2, 40)                     # 1e-4 .. 100 cm
    centres = np.sqrt(bins[:-1] * bins[1:])           # geometric bin centres (log)
    for sig, fd, qd in subset:
        nf, _ = np.histogram(fd, bins=bins)
        nq, _ = np.histogram(qd, bins=bins)
        good = nq > 0
        ratio = np.full(nf.shape, np.nan)
        ratio[good] = nf[good] / nq[good]
        err = np.full(nf.shape, np.nan)
        nz = good & (nf > 0)
        err[nz] = ratio[nz] * np.sqrt(1.0 / nf[nz] + 1.0 / nq[nz])
        ax.errorbar(centres[good], ratio[good], yerr=err[good], fmt="o", ms=3,
                    color=sig["color"], ecolor=sig["color"], capsize=2, label=sig["label"])
    for edge in DXY_EDGES:
        ax.axvline(edge, color="grey", ls="--", lw=1.2, alpha=0.8)
    ax.axhline(1.0, color="grey", ls=":", lw=1, alpha=0.7)
    ax.set_xscale("log")
    ax.set_xlim(1e-4, 100)
    ax.set_xlabel("Displacement dxy [cm]", fontsize=11)
    ax.set_ylabel("fourmuonSV_dxy / (2-muonSV midpoint dxy)", fontsize=10)
    _cms_axes(ax, fontsize=10)
    ax.legend(fontsize=7, loc="upper right", **cms.LEGEND_KW)
    # the panel's selection goes in an in-plot legend, not the plot title
    _info_legend(ax, [title], fontsize=7)


def page_cat_dxy_ratio(sig_obs):
    """Page: bin-by-bin ratio of the two dxy definitions per signal, in the two
    fourmuonSV_pAngle categories and pAngle-inclusive (3 panels)."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    panels = [(r"Pointing angle $<$ %.1f" % PANGLE_EDGE, lambda fp: fp < PANGLE_EDGE),
              (r"Pointing angle $>$ %.1f" % PANGLE_EDGE, lambda fp: fp >= PANGLE_EDGE),
              ("Pointing angle: inclusive", None)]
    for ax, (title, sel) in zip(axes, panels):
        subset = []
        for sig, o in sig_obs:
            if sel is None:
                fd, qd = o["cat_fourmu_dxy"], o["cat_est_dxy"]
            else:
                m = sel(o["cat_fpa"])
                fd, qd = o["cat_fourmu_dxy"][m], o["cat_est_dxy"][m]
            subset.append((sig, fd, qd))
        _dxy_ratio_panel(ax, subset, title)
    fig.suptitle("Ratio of dxy distributions: fourmuonSV_dxy / (2-muonSV midpoint dxy)\n"
                 "grey dashed: dxy category edges (1, 10 cm);  dotted: ratio = 1", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    return fig


# one entry per plot type: (function, short log name)
PLOT_FUNCS = [
    (page_dxy_pull,      "dxy distance/uncertainty pull"),
    (page_d3d_pull,      "3D distance/uncertainty pull"),
    (page_dxy_vs_fourmu, "Delta_xy vs fourmuonSV_dxy"),
    (page_dxy_ratio,     "fourmuonSV_dxy / Delta_xy ratio"),
    (page_pangle,        "pointing-angle overlay"),
    (page_pangle_ratio,  "pointing-angle histogram ratio"),
    (page_cat_pangle_split,     "quadv category populations (pAngle split)"),
    (page_cat_pangle_inclusive, "quadv category populations (pAngle inclusive)"),
    (page_cat_dxy_ratio,        "quadv dxy-definition ratio (pAngle split + inclusive)"),
]


# ----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Compare quadv distances / pointing angles (signal only)")
    parser.add_argument("--output", default="compareCategoriesQuadv.pdf",
                        help="Output PDF (default: compareCategoriesQuadv.pdf)")
    parser.add_argument("--n-signal", type=int, default=N_SIGNAL_FILES,
                        help=f"Signal files per point (default: {N_SIGNAL_FILES})")
    parser.add_argument("--test", action="store_true",
                        help="Quick check: read only 1 file per signal point")
    args = parser.parse_args()

    n_sig = 1 if args.test else args.n_signal
    if args.test:
        log("[TEST MODE] reading only 1 file per signal point")

    branches = list(FOURMU_BRANCHES) + list(MUONSV_BRANCHES) + list(PV_BRANCHES)

    sig_obs = []
    n_read, n_avail = 0, 0
    for sig in SIGNALS:
        log(f"\n=== {sig['dir']} (taking {n_sig} files) ===")
        # list everything, then take the first n_sig: knowing how many files exist is what
        # tells the plots whether they are showing the whole sample or only part of it
        all_urls = list_root_files(sig["path"], cap=None)
        urls = all_urls[:n_sig]
        n_avail += len(all_urls)
        n_read += len(urls)
        if not urls:
            log(f"  [warn] no files found for {sig['dir']}", file=sys.stderr)
            continue
        data = read_branches(urls, branches, sig["label"])
        if data is None:
            log(f"  [warn] no readable data for {sig['dir']}", file=sys.stderr)
            continue
        matches = match_quadv(data, sig["label"])
        obs = compute_observables(data, matches, sig["label"])
        sig_obs.append((sig, obs))

    if not sig_obs:
        log("ERROR: no signal data to plot", file=sys.stderr)
        sys.exit(1)

    # tell the plots how much of the sample they are showing (must precede any plotting)
    cms.set_sample_files(n_read, n_avail)
    if cms.is_partial():
        log(f"\n  PARTIAL SAMPLE: {n_read} of {n_avail} files "
            f"({100 * cms.sample_fraction():.1f}%) -- every plot is labelled as such")
    else:
        log(f"\n  full sample: all {n_avail} files read")

    # one page per plot type, all signals overlaid
    log("\n=== Writing PDF ===")
    page = 0
    with PdfPages(args.output) as pdf:
        for fn, name in PLOT_FUNCS:
            page += 1
            log(f"  page {page}: {name}")
            pdf.savefig(fn(sig_obs), bbox_inches="tight")
            plt.close("all")
    log(f"\nSaved: {args.output} ({page} pages)")


if __name__ == "__main__":
    main()
