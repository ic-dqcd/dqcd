#!/usr/bin/env python3
"""BuToJpsiK 2018 vs 2024: the branches the trigger/ID scale-factor task has to be ported.

tasks/triggerscalefactor.py was written against the 2018 nanotron production and reads a
collection, TrigObjBPark, that the 2024 production does not write. This makes one page per
affected variable so the port is decided on what the distributions actually look like
rather than on branch names alone.

The samples:
  2018  /BuToJpsiK_BMuonFilter_SoftQCDnonD_TuneCP5_13TeV-pythia8-evtgen/
        jleonhol-BuToKJPsiMC-.../USER            (13 TeV)
  2024  BuToJpsiK_Fil-BMuon_Par-SoftQCDnonD_TuneCP5_13p6TeV_pythia8-evtgen,
        nanotron-v15_2024-RunIII2024Summer24     (13.6 TeV)

Two things the pages are built to answer:

  1. TrigObjBPark vs TrigObj. 2018 writes BOTH, with identical field sets -- TrigObjBPark is
     the B-parking-filtered copy. 2024 writes only TrigObj. So each TrigObjBPark page also
     draws 2018's TrigObj, and the question "can 2024 TrigObj stand in for 2018
     TrigObjBPark?" is answered by whether those two 2018 curves agree.
  2. TriggerMuon vs TriggerObject. 2018's TriggerMuon and 2024's TriggerObject overlap in
     pt/eta/phi/charge/pdgId/vx/vy/vz; the rest of TriggerMuon (dxy, dz, ip3d, sip3d, mass,
     ptErr) has no 2024 counterpart and is drawn 2018-only, clearly marked.

NOTE: TrigObjBPark_l1dR is referenced 32 times by the 2018 task but exists in NEITHER
file. That code path cannot have run on this dataset, so there is nothing to reproduce --
it is flagged on its own page rather than silently skipped.

Shapes are unit-normalised: the two samples differ in size and in centre-of-mass energy
(13 vs 13.6 TeV), so only the shapes are comparable, never the rates.

Run after sourcing setup.sh:
    python3 _tools/compareJPsi2018v2024.py [--n-2018 N] [--n-2024 N] [--output path.pdf]
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

XRD = "root://gfe02.grid.hep.ph.ic.ac.uk/"
DIR_2018 = ("/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/jleonhol/nanotron/butokjpsimc/"
            "BuToJpsiK_BMuonFilter_SoftQCDnonD_TuneCP5_13TeV-pythia8-evtgen/"
            "BuToKJPsiMC/231113_091452/0000")
DIR_2024 = ("/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024/"
            "BuToJpsiK_Fil-BMuon_Par-SoftQCDnonD_TuneCP5_13p6TeV_pythia8-evtgen/"
            "nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2/"
            "260803_145456/0000")

WEBDIR = "/home/hep/jtafoyav/public_html/parking/2024/kinematic_checks"

C18, C24, CALT = "royalblue", "crimson", "seagreen"

# (page title, 2018 branch, 2024 branch or None, 2018 alternative or None, binning)
# binning: (nbins, lo, hi) or "int" for integer-valued quantities
VARS = [
    # --- the collection the SF task actually reads -------------------------
    ("Trigger-object multiplicity", "nTrigObjBPark", "nTrigObj", "nTrigObj", "int"),
    ("Trigger object $p_T$",   "TrigObjBPark_pt",   "TrigObj_pt",   "TrigObj_pt",   (60, 0, 60)),
    ("Trigger object $\\eta$", "TrigObjBPark_eta",  "TrigObj_eta",  "TrigObj_eta",  (60, -3, 3)),
    ("Trigger object $\\phi$", "TrigObjBPark_phi",  "TrigObj_phi",  "TrigObj_phi",  (60, -3.2, 3.2)),
    ("Trigger object L1 $p_T$",       "TrigObjBPark_l1pt",   "TrigObj_l1pt",   "TrigObj_l1pt",   (60, 0, 60)),
    ("Trigger object L1 $p_T$ (2nd)", "TrigObjBPark_l1pt_2", "TrigObj_l1pt_2", "TrigObj_l1pt_2", (60, 0, 60)),
    ("Trigger object L2 $p_T$",       "TrigObjBPark_l2pt",   "TrigObj_l2pt",   "TrigObj_l2pt",   (60, 0, 60)),
    ("Trigger object L1 iso",     "TrigObjBPark_l1iso",    "TrigObj_l1iso",    "TrigObj_l1iso",    "int"),
    ("Trigger object L1 charge",  "TrigObjBPark_l1charge", "TrigObj_l1charge", "TrigObj_l1charge", "int"),
    ("Trigger object id",         "TrigObjBPark_id",       "TrigObj_id",       "TrigObj_id",       "int"),
    ("Trigger object filterBits", "TrigObjBPark_filterBits", "TrigObj_filterBits", "TrigObj_filterBits", "int"),
    # --- the 2018 code wants this and NOTHING has it -----------------------
    ("L1 dR  (referenced by the 2018 task, absent from both samples)",
     "TrigObjBPark_l1dR", "TrigObj_l1dR", None, (50, 0, 0.5)),
    # --- TriggerMuon (2018) vs TriggerObject (2024) ------------------------
    ("Trigger muon multiplicity", "nTriggerMuon", "nTriggerObject", None, "int"),
    ("Trigger muon $p_T$",   "TriggerMuon_pt",     "TriggerObject_pt",     None, (60, 0, 60)),
    ("Trigger muon $\\eta$", "TriggerMuon_eta",    "TriggerObject_eta",    None, (60, -3, 3)),
    ("Trigger muon $\\phi$", "TriggerMuon_phi",    "TriggerObject_phi",    None, (60, -3.2, 3.2)),
    ("Trigger muon charge",  "TriggerMuon_charge", "TriggerObject_charge", None, "int"),
    ("Trigger muon pdgId",   "TriggerMuon_pdgId",  "TriggerObject_pdgId",  None, "int"),
    ("Trigger muon vx", "TriggerMuon_vx", "TriggerObject_vx", None, (60, -0.5, 0.5)),
    ("Trigger muon vy", "TriggerMuon_vy", "TriggerObject_vy", None, (60, -0.5, 0.5)),
    ("Trigger muon vz", "TriggerMuon_vz", "TriggerObject_vz", None, (60, -20, 20)),
    # 2018-only fields of TriggerMuon
    ("Trigger muon $d_{xy}$",  "TriggerMuon_dxy",   None, None, (60, -0.5, 0.5)),
    ("Trigger muon $d_z$",     "TriggerMuon_dz",    None, None, (60, -20, 20)),
    ("Trigger muon $ip3d$",    "TriggerMuon_ip3d",  None, None, (60, 0, 1.0)),
    ("Trigger muon $sip3d$",   "TriggerMuon_sip3d", None, None, (60, 0, 30)),
    ("Trigger muon mass",      "TriggerMuon_mass",  None, None, (60, 0, 0.3)),
    # --- per-muon HLT matching: the path itself changed --------------------
    ("Per-muon HLT match (2018 Mu9_IP6  vs  2024 Mu10_Barrel_L1HP11_IP6)",
     "MuonBPark_fired_HLT_Mu9_IP6", "MuonBPark_fired_HLT_Mu10_Barrel_L1HP11_IP6", None, "int"),
    # --- the tag/probe inputs that DO port unchanged (sanity) --------------
    ("muonSV mass  (J/$\\psi$ window)", "muonSV_mass", "muonSV_mass", None, (60, 2.6, 3.6)),
    ("muonSV $\\chi^2$",  "muonSV_chi2",   "muonSV_chi2",   None, (60, 0, 20)),
    ("muonSV $d_{xy}$ significance", "muonSV_dxySig", "muonSV_dxySig", None, (60, 0, 50)),
    ("Muon $p_T$",        "Muon_pt",       "Muon_pt",       None, (60, 0, 40)),
    ("Muon $d_{xy}$ (BS)", "Muon_dxybs",   "Muon_dxybs",    None, (60, -0.5, 0.5)),
    ("Muon $sip3d$",      "Muon_sip3d",    "Muon_sip3d",    None, (60, 0, 30)),
]


def log(msg, **kw):
    print(msg, flush=True, **kw)


def xrdfs_ls(path):
    r = subprocess.run(["xrdfs", "gfe02.grid.hep.ph.ic.ac.uk", "ls", path],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"xrdfs ls failed for {path}: {r.stderr.strip()[:200]}")
    return [f for f in r.stdout.split() if f.endswith(".root")]


def read(files, branches):
    """{branch: flat np.array} over *files*; a branch absent from the tree is skipped."""
    import uproot
    import awkward as ak

    out = {b: [] for b in branches}
    present = None
    for i, f in enumerate(files, 1):
        try:
            with uproot.open(XRD + f) as fh:
                tree = fh["Events"]
                keys = set(tree.keys())
                if present is None:
                    present = [b for b in branches if b in keys]
                    missing = [b for b in branches if b not in keys]
                    if missing:
                        log(f"    absent from this sample: {missing}")
                a = tree.arrays(present, library="ak")
        except Exception as exc:
            log(f"    [warn] {f.rsplit('/', 1)[-1]}: {exc}", file=sys.stderr)
            continue
        for b in present:
            v = a[b]
            # jagged -> flatten; scalar per event -> keep as is
            try:
                v = ak.flatten(v)
            except Exception:
                pass
            out[b].append(ak.to_numpy(v).astype(float))
        log(f"    [{i}/{len(files)}] {f.rsplit('/', 1)[-1]}")
    return {b: (np.concatenate(v) if v else np.array([])) for b, v in out.items()}


def page(title, series, binning):
    """One page: overlaid unit-normalised shapes. *series* = [(label, values, colour)].

    Series order is preserved in the legend, and an entry whose branch does not exist in
    that sample still gets a legend line -- marked "(Branch not available)" instead of the
    entry count -- so a missing branch reads as a fact about the sample rather than as a
    curve someone forgot to draw."""
    fig, ax = plt.subplots(figsize=(10, 7))
    drawn = [(l, v, c) for l, v, c in series if v is not None and len(v)]

    edges = None
    if drawn:
        if binning == "int":
            allv = np.concatenate([v for _, v, _ in drawn])
            lo, hi = int(np.floor(allv.min())), int(np.ceil(allv.max()))
            hi = min(hi, lo + 60)                     # filterBits can be huge
            edges = np.arange(lo - 0.5, hi + 1.5, 1.0)
        else:
            n, lo, hi = binning
            edges = np.linspace(lo, hi, n + 1)

    # Handles are collected explicitly: matplotlib's automatic legend groups ax.lines
    # before ax.patches, so the empty Line2D proxy used for a missing branch would jump
    # ABOVE the ax.stairs histograms no matter what order they were created in.
    handles, labels = [], []
    for label, v, colour in series:                   # keep the caller's order
        if v is not None and len(v) and edges is not None:
            h, _ = np.histogram(v, bins=edges)
            tot = h.sum()
            if tot:
                art = ax.stairs(h / tot, edges, color=colour, lw=2)
                handles.append(art)
                labels.append(f"{label}   ({len(v):,} entries, mean {v.mean():.3g})")
                continue
        art, = ax.plot([], [], color=colour, lw=2)
        handles.append(art)
        labels.append(f"{label}   (Branch not available)")

    if not drawn:
        ax.text(0.5, 0.5, "branch present in neither sample", ha="center", va="center",
                transform=ax.transAxes, fontsize=15, color="crimson")
    ax.set_ylabel("Fraction of entries", fontsize=cms.FS_LABEL)
    ax.set_xlabel(title, fontsize=cms.FS_LABEL)
    cms.cms_axes(ax, fontsize=cms.FS_AXES)
    ax.legend(handles, labels, fontsize=cms.FS_LEGEND - 1, loc="upper right",
              title="unit-normalised shapes; 13 TeV (2018) vs 13.6 TeV (2024)",
              title_fontsize=cms.FS_LEGEND - 2, **cms.LEGEND_KW)
    fig.suptitle(title, fontsize=cms.FS_TITLE)
    fig.tight_layout()
    return fig


def main():
    p = argparse.ArgumentParser(description="BuToJpsiK 2018 vs 2024 branch comparison")
    p.add_argument("--output", default="compareJPsi2018v2024.pdf")
    p.add_argument("--n-2018", type=int, default=1, help="files from the 2018 sample")
    p.add_argument("--n-2024", type=int, default=3, help="files from the 2024 sample")
    p.add_argument("--no-publish", action="store_true")
    args = p.parse_args()

    f18 = sorted(xrdfs_ls(DIR_2018))[:args.n_2018]
    f24 = sorted(xrdfs_ls(DIR_2024))[:args.n_2024]
    log(f"2018: {len(f18)} file(s)\n2024: {len(f24)} file(s)")

    b18 = sorted({v[1] for v in VARS if v[1]} | {v[3] for v in VARS if v[3]})
    b24 = sorted({v[2] for v in VARS if v[2]})
    log("\n=== reading 2018 ===")
    d18 = read(f18, b18)
    log("\n=== reading 2024 ===")
    d24 = read(f24, b24)

    log("\n=== writing PDF ===")
    with PdfPages(args.output) as pdf:
        for title, v18, v24, alt18, binning in VARS:
            # 2018 entries first (the BPark collection, then the standard one), 2024 last
            series = [(f"2018  {v18}", d18.get(v18), C18)]
            if alt18 and alt18 != v18:
                series.append((f"2018  {alt18}  (standard collection)", d18.get(alt18), CALT))
            series.append((f"2024  {v24}" if v24 else "2024  (no equivalent)",
                           d24.get(v24) if v24 else None, C24))
            pdf.savefig(page(title, series, binning), bbox_inches="tight")
            plt.close("all")
    log(f"Saved: {args.output} ({len(VARS)} pages)")

    if not args.no_publish:
        try:
            os.makedirs(WEBDIR, exist_ok=True)
            subprocess.run(["cp", args.output, WEBDIR], check=True)
            log(f"Published: {os.path.join(WEBDIR, os.path.basename(args.output))}")
        except Exception as exc:
            log(f"[warn] publish failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
