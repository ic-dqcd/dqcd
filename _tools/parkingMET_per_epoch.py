#!/usr/bin/env python3
"""Per-stream, per-epoch PuppiMET distributions for Parking data.

Produces 4 PDFs:
  parking_SingleMuon_PuppiMET_pt.pdf
  parking_SingleMuon_PuppiMET_phi.pdf
  parking_DoubleMuon_PuppiMET_pt.pdf
  parking_DoubleMuon_PuppiMET_phi.pdf

Each PDF has one panel per Parking stream, with one line per Run2024 epoch.

Run after sourcing setup.sh:
    python3 _tools/parkingMET_per_epoch.py [--max-files-per-epoch N] [--bins N] [--xmax GeV]
"""

import argparse
import math
import os
import random
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

XRD_SERVER = "root://gfe02.grid.hep.ph.ic.ac.uk/"
PNFS_BASE  = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024__v2_withPuppyMET"
TREE_NAME  = "Events"
BRANCHES   = ["PuppiMET_pt", "PuppiMET_phi"]

os.environ["X509_USER_PROXY"] = f"/tmp/x509up_u{os.getuid()}"
_ENV = os.environ

EPOCH_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#17becf",
]


def log(msg):
    print(msg, flush=True)


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


def met_filter_mask(tree):
    """Boolean mask for data events passing Run-3 MET filters (includes eeBadScFilter)."""
    keys = set(tree.keys())
    mask = np.ones(tree.num_entries, dtype=bool)
    for flag in _MET_FLAGS_REQUIRED:
        if flag not in keys:
            log(f"  [warn] required MET flag '{flag}' missing from tree — failing all events")
            return np.zeros(tree.num_entries, dtype=bool)
        mask &= tree[flag].array(library="np").astype(bool)
    if _MET_FLAG_OPTIONAL in keys:
        mask &= tree[_MET_FLAG_OPTIONAL].array(library="np").astype(bool)
    if _MET_FLAG_DATA_ONLY in keys:
        mask &= tree[_MET_FLAG_DATA_ONLY].array(library="np").astype(bool)
    return mask


def xrdfs_ls(path):
    result = subprocess.run(
        ["xrdfs", XRD_SERVER, "ls", "-l", path],
        capture_output=True, text=True, env=_ENV,
    )
    entries = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts  = line.split()
        is_dir = parts[0].startswith("d")
        entries.append((parts[-1], is_dir))
    return entries


def list_root_files(directory, cap=None):
    files = []
    for path, is_dir in xrdfs_ls(directory):
        if cap and len(files) >= cap:
            break
        if is_dir:
            files.extend(list_root_files(path, cap=(cap - len(files)) if cap else None))
        elif path.endswith(".root"):
            files.append(XRD_SERVER + path)
    return files


def read_branches(urls):
    """Read all BRANCHES from urls in one pass. Returns {branch: np.array}."""
    import uproot
    accum = {b: [] for b in BRANCHES}
    for url in urls:
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                mask = met_filter_mask(tree)
                for b in BRANCHES:
                    accum[b].append(tree[b].array(library="np")[mask])
        except Exception as exc:
            log(f"    [warn] {url.split('/')[-1]}: {exc}")
    return {b: (np.concatenate(arrs) if arrs else np.array([], dtype=np.float32))
            for b, arrs in accum.items()}


def epoch_label(dirname):
    return dirname.replace("nanotron-v15_2024__from_", "")


def collect_data(streams, max_files, data_frac, seed):
    """Read all branches for every stream×epoch in a single pass.

    Returns:
        {stream_name: {epoch_label: {branch: np.array}}}
    """
    rng    = random.Random(seed)
    result = {}

    for i, stream_path in enumerate(streams):
        name = stream_path.split("/")[-1]
        log(f"\n  [{i+1}/{len(streams)}] {name}")
        result[name] = {}

        for path, is_dir in xrdfs_ls(stream_path):
            if not is_dir:
                continue
            label = epoch_label(path.split("/")[-1])
            if "MINIv6NANOv15" not in label:
                continue

            log(f"    epoch: {label}")
            all_files = list_root_files(path)           # always full list
            n_select  = max(1, round(len(all_files) * data_frac))
            # Small dataset: fractional sampling would give ~1 file, so take all
            if len(all_files) <= 5:
                files = all_files
            else:
                files = rng.sample(all_files, n_select) # random blind draw
                if max_files:
                    files = files[:max_files]           # cap only after draw
            log(f"      {len(files)}/{len(all_files)} files ({data_frac*100:.4g}%, seed={seed})")

            if not files:
                continue

            log(f"      reading {BRANCHES} ...")
            result[name][label] = read_branches(files)
            n_evts = len(result[name][label]["PuppiMET_pt"])
            log(f"      => {n_evts:,} events")

    return result


def make_plot(data, streams, branch, bins, title, xlabel, yscale, pt_cut=None):
    """Render one figure from pre-collected data dict. Returns the figure."""
    n      = len(streams)
    ncols  = min(4, n)
    nrows  = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(5 * ncols, 4 * nrows),
                             squeeze=False)

    ax_flat = [axes[r][c] for r in range(nrows) for c in range(ncols)]
    for ax in ax_flat[n:]:
        ax.set_visible(False)

    for i, stream_path in enumerate(streams):
        ax    = ax_flat[i]
        name  = stream_path.split("/")[-1]
        epochs = data.get(name, {})

        if not epochs:
            ax.set_title(name.replace("Parking", ""), fontsize=9)
            ax.text(0.5, 0.5, "no data", transform=ax.transAxes,
                    ha="center", va="center", color="grey")
            continue

        for j, epoch in enumerate(sorted(epochs)):
            values = epochs[epoch][branch]
            if pt_cut is not None:
                mask   = epochs[epoch]["PuppiMET_pt"] > pt_cut
                values = values[mask]
            if len(values) == 0:
                continue
            color   = EPOCH_COLORS[j % len(EPOCH_COLORS)]
            counts, edges = np.histogram(values, bins=bins)
            widths  = np.diff(edges)
            total   = counts.sum()
            norm    = counts / (total * widths)
            err     = np.sqrt(counts) / (total * widths)
            centres = 0.5 * (edges[:-1] + edges[1:])
            short   = epoch.replace("-MINIv6NANOv15", "").replace("_v2", "")

            ax.stairs(norm, edges, color=color, linewidth=1.5,
                      label=f"{short} ({len(values):,})")
            ax.fill_between(centres, norm - err, norm + err,
                            step="mid", alpha=0.2, color=color)

        ax.set_title(name.replace("Parking", ""), fontsize=9)
        ax.set_xlabel(xlabel, fontsize=8)
        ax.set_ylabel("Norm. events / bin", fontsize=8)
        ax.set_yscale(yscale)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=6, loc="upper right")

    fig.suptitle(title, fontsize=13, y=1.01)
    fig.tight_layout()
    return fig


def main():
    parser = argparse.ArgumentParser(
        description="Per-stream per-epoch PuppiMET plots for Parking data")
    parser.add_argument("--max-files-per-epoch", type=int, default=None,
                        help="Hard cap on files read per epoch after the blind draw — for quick tests only")
    parser.add_argument("--data-frac", type=float, default=0.01,
                        help="Fraction of files to draw per epoch (default: 0.01 = 1%%)")
    parser.add_argument("--seed",   type=int,   default=42)
    parser.add_argument("--bins",   type=int,   default=50)
    parser.add_argument("--xmax",   type=float, default=300,
                        help="Upper PuppiMET_pt limit in GeV (default: 300)")
    parser.add_argument("--outdir", default=".",
                        help="Output directory for PDFs (default: .)")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    log(f"Listing {PNFS_BASE} ...")
    top = xrdfs_ls(PNFS_BASE)
    if not top:
        log("ERROR: cannot list base path — check proxy", file=sys.stderr)
        sys.exit(1)

    singles = sorted(p for p, d in top if d and "ParkingSingleMuon"        in p.split("/")[-1])
    doubles = sorted(p for p, d in top if d and "ParkingDoubleMuonLowMass" in p.split("/")[-1])
    log(f"  {len(singles)} SingleMuon streams, {len(doubles)} DoubleMuon streams")

    bins_pt  = np.linspace(0, args.xmax, args.bins + 1)
    bins_phi = np.linspace(-np.pi, np.pi, args.bins + 1)
    cap      = args.max_files_per_epoch
    blind    = f"{args.data_frac*100:.4g}% data, seed={args.seed}"

    for streams, tag in [(singles, "SingleMuon"), (doubles, "DoubleMuon")]:
        log(f"\n{'='*60}")
        log(f"[{tag}] Collecting data (single pass over all streams × epochs) ...")
        data = collect_data(streams, cap, args.data_frac, args.seed)

        log(f"\n[{tag}] Rendering plots ...")

        pt_cuts = [
            (None, r"MET $p_T$ inclusive"),
            (30,   r"MET $p_T > 30$ GeV"),
            (50,   r"MET $p_T > 50$ GeV"),
        ]

        pt_path = os.path.join(args.outdir, f"parking_{tag}_PuppiMET_pt.pdf")
        with PdfPages(pt_path) as pdf:
            for pt_cut, cut_label in pt_cuts:
                fig = make_plot(
                    data, streams, "PuppiMET_pt", bins_pt,
                    title=f"{tag} — PuppiMET $p_T$ per epoch  [{blind}]  ({cut_label})",
                    xlabel="PuppiMET $p_T$ [GeV]", yscale="log",
                    pt_cut=pt_cut,
                )
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
        log(f"Saved: {pt_path}")

        phi_path = os.path.join(args.outdir, f"parking_{tag}_PuppiMET_phi.pdf")
        with PdfPages(phi_path) as pdf:
            for pt_cut, cut_label in pt_cuts:
                fig = make_plot(
                    data, streams, "PuppiMET_phi", bins_phi,
                    title=f"{tag} — PuppiMET $\\phi$ per epoch  [{blind}]  ({cut_label})",
                    xlabel=r"PuppiMET $\phi$ [rad]", yscale="linear",
                    pt_cut=pt_cut,
                )
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
        log(f"Saved: {phi_path}")


if __name__ == "__main__":
    main()
