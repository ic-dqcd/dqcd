#!/usr/bin/env python3
"""Contribution of each L1 DoubleMu seed to the DoubleMuon parking paths, per 2024 era.

Why: the HLT_DoubleMu4_3_LowMass path is seeded by an OR of many L1 DoubleMu seeds, and
that OR changed through 2024. modules/muon_selection.py currently emulates ONE of them
(L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6, |eta| < 2.0) which measurement shows leaves ~10% of
fired events unaccounted for -- and, because several of the real seeds carry no "er"
restriction, it also understates the eta acceptance. This quantifies, era by era, which
seeds actually matter, so the emulation can be built on the ones that do.

    contribution(seed, era) = N(seed fired AND HLT fired) / N(HLT fired)

IMPORTANT -- this is a CONTRIBUTION, not a prescale. The nanoAOD carries no prescale
branch (checked: no branch matching "prescale"), so the actual L1 prescale values have to
come from the L1 menu / brilcalc / OMS. What is measured here is the effective firing
fraction, which already folds in whatever prescale was applied -- and for deciding which
seeds to emulate, that is the quantity that matters.

Seeds come in _pPAT / _pRECO prefire variants that carry identical decisions; only the
bare name is kept.

Output (getDoubleMuonPrescales.pdf):
    1. heatmap  seed x era of the contribution, for the seeds that ever matter
    2. one bar chart per era, top seeds, coloured by their |eta| restriction
plus a text table on stdout.

Run after sourcing setup.sh:
    python3 _tools/getDoubleMuonPrescales.py [--output path.pdf] [--n-files N] [--test]
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict, OrderedDict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import cmsstyle as cms
import goldenjson as gj

# Golden-JSON mask, set in main(). CERT is None when disabled or unavailable, in which
# case gj.mask() is never called and every data event is kept.
CERT = None
GCOUNT = gj.Counter()

XRD_SERVER = "root://gfe02.grid.hep.ph.ic.ac.uk/"
BASE = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024"

TREE_NAME = "Events"
PD_FOLDERS = [f"ParkingDoubleMuonLowMass{i}" for i in range(8)]

# the paths whose seeding we care about
HLT_PATHS = ["HLT_DoubleMu4_3_LowMass", "HLT_DoubleMu4_LowMass_Displaced"]

N_FILES_PER_ERA = 2      # per PD folder per era; the quantity converges fast

# Only the seeds that modules/muon_selection.py's doubleMuon__l1_conditions actually lists
# (enabled or commented) are shown. Every other L1_DoubleMu* seed in the menu can fire in
# coincidence with the path without seeding it -- e.g. L1_DoubleMu8_SQ shows ~11%, but that
# is just a hard dimuon event also passing a harder seed, not a contribution to the OR that
# fired the path. Including them makes the plot longer and the ranking misleading.
FRAMEWORK_SEEDS = [
    "L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",
    "L1_DoubleMu4p5_SQ_OS_dR_Max1p2",
    "L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",
    "L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",
    "L1_DoubleMu4_SQ_OS_dR_Max1p2",
    "L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",
    "L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",
    "L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",
    "L1_DoubleMu5_SQ_OS_dR_Max1p6",
    "L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",
    "L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",
    "L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",
]

# The set enabled in modules/muon_selection.py's doubleMuon__l1_conditions -- the five
# highest-contributing seeds averaged over all eras. Highlighted in bold on the heatmaps,
# and their per-event logical OR is shown as the top row: individual contributions cannot
# simply be added (the seeds overlap heavily), so the OR is the only honest measure of
# what this set actually covers.
TOP5 = [
    "L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",
    "L1_DoubleMu4p5_SQ_OS_dR_Max1p2",
    "L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",
    "L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",
    "L1_DoubleMu4_SQ_OS_dR_Max1p2",
]
# Cumulative ORs of the first N seeds, so the marginal gain of each addition is visible:
# if Top 2 already covers ~99%, seeds 3-5 are buying very little.
OR_SETS = [2, 3, 4, 5]


def or_label(n):
    return f"Logic OR of Top {n}"

_env_proxy = os.environ.get("X509_USER_PROXY", "")
if not (_env_proxy and os.path.exists(_env_proxy)):
    os.environ["X509_USER_PROXY"] = f"/tmp/x509up_u{os.getuid()}"
_XRDFS_ENV = os.environ


def log(msg, **kwargs):
    print(msg, flush=True, **kwargs)


def eta_restriction(seed):
    """|eta| implied by the seed name. CMS convention: 'erXpY' -> |eta| < X.Y; a seed
    with no 'er' token has no eta restriction beyond the L1 muon system's 2.4."""
    m = re.search(r"er(\d)p(\d)", seed)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    return 2.4


def xrdfs_ls(path):
    r = subprocess.run(["xrdfs", XRD_SERVER, "ls", "-l", path],
                       capture_output=True, text=True, env=_XRDFS_ENV)
    if r.returncode != 0:
        raise RuntimeError(f"xrdfs ls failed for {path} (rc={r.returncode}): {r.stderr.strip()}")
    out = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if line:
            parts = line.split()
            out.append((parts[-1], parts[0].startswith("d")))
    return out


def files_under(path, cap):
    """Up to *cap* .root files under *path*, depth-first."""
    found = []
    for p, is_dir in xrdfs_ls(path):
        if len(found) >= cap:
            break
        if is_dir:
            found.extend(files_under(p, cap - len(found)))
        elif p.endswith(".root"):
            found.append(XRD_SERVER + p)
    return found


def discover(n_files):
    """{era_label: [file urls]} across all DoubleMuon PD folders.

    The era label keeps the reprocessing version (e.g. Run2024F-v3), because the L1 menu
    can differ between versions of the same era -- which is exactly the drift we're after.
    """
    eras = defaultdict(list)
    for pd in PD_FOLDERS:
        try:
            entries = xrdfs_ls(f"{BASE}/{pd}")
        except RuntimeError as exc:
            log(f"  [warn] {pd}: {exc}", file=sys.stderr)
            continue
        for path, is_dir in entries:
            if not is_dir:
                continue
            name = path.split("/")[-1]
            m = re.search(r"from_(Run2024[A-Z])-.*?(v\d+)$", name)
            label = f"{m.group(1)}-{m.group(2)}" if m else name
            got = files_under(path, n_files)
            if got:
                eras[label].extend(got)
                log(f"  {pd:28s} {label:14s} +{len(got)} file(s)")
    return OrderedDict(sorted(eras.items()))


def scan(files, label):
    """(n_hlt_by_path, {seed: counts_by_path}) over *files*."""
    import uproot
    n_hlt = np.zeros(len(HLT_PATHS))
    counts = defaultdict(lambda: np.zeros(len(HLT_PATHS)))
    runs = set()
    for i, url in enumerate(files, 1):
        try:
            with uproot.open(f"{url}:{TREE_NAME}") as tree:
                keys = set(tree.keys())
                seeds = sorted(k for k in keys
                               if k.startswith("L1_DoubleMu")
                               and not k.endswith(("_pPAT", "_pRECO")))
                paths = [p for p in HLT_PATHS if p in keys]
                if not paths or not seeds:
                    continue
                a = tree.arrays(paths + seeds + gj.BRANCHES, library="np")
                if CERT is not None:
                    keep = GCOUNT.update(gj.mask(a["run"], a["luminosityBlock"], CERT))
                    a = {k: v[keep] for k, v in a.items()}
                if len(a["run"]) == 0:
                    continue
                runs.update(np.unique(a["run"]).tolist())
                masks = []
                for j, p in enumerate(HLT_PATHS):
                    m = a[p].astype(bool) if p in paths else np.zeros(len(a["run"]), bool)
                    masks.append(m)
                    n_hlt[j] += m.sum()
                for s in seeds:
                    sv = a[s].astype(bool)
                    for j, m in enumerate(masks):
                        counts[s][j] += (sv & m).sum()
                # cumulative per-event ORs of the enabled set -- computed here, not summed
                # later, because the seeds overlap heavily
                or_mask = np.zeros(len(a["run"]), bool)
                for n, s in enumerate(TOP5, start=1):
                    if s in keys:
                        or_mask |= a[s].astype(bool)
                    if n in OR_SETS:
                        for j, m in enumerate(masks):
                            counts[or_label(n)][j] += (or_mask & m).sum()
        except Exception as exc:
            log(f"    [warn] {url.split('/')[-1]}: {exc}", file=sys.stderr)
    log(f"  [{label}] {len(files)} files, runs {min(runs) if runs else '-'}"
        f"-{max(runs) if runs else '-'}, "
        + ", ".join(f"{p.split('_',1)[1]}={int(n):,}" for p, n in zip(HLT_PATHS, n_hlt)))
    return n_hlt, counts


def plot_heatmap(eras, seeds, table, path_idx, pdf):
    """seed x era contribution heatmap for one HLT path.

    The OR of the enabled (Top 5) set is the first row, and those five seeds are shown in
    bold, so it is immediately visible which seeds the analysis uses and what they cover
    together. The OR is a per-event quantity from scan(): the individual rows overlap
    heavily and must NOT be added up."""
    or_rows = [or_label(n) for n in OR_SETS]
    rows = or_rows + list(seeds)
    mat = np.array([[table[e].get(s, np.zeros(len(HLT_PATHS)))[path_idx] for e in eras]
                    for s in rows])

    fig, ax = plt.subplots(figsize=(2.5 + 0.95 * len(eras), 2.0 + 0.40 * len(rows)))
    im = ax.imshow(mat, aspect="auto", cmap="viridis", vmin=0, vmax=1)
    ax.set_xticks(range(len(eras)))
    ax.set_xticklabels(eras, rotation=45, ha="right", fontsize=10)

    # Only the SEED NAME is bolded for the enabled seeds -- the "[|eta|<x]" suffix stays
    # regular weight, which a whole-label set_fontweight() cannot do. mathtext gives the
    # per-part control; underscores must be escaped or they become subscripts.
    labels = []
    for s in rows:
        if s in or_rows:
            labels.append(s)
        else:
            name = s.replace("L1_DoubleMu", "DM")
            suffix = f"  [|$\\eta$|<{eta_restriction(s):g}]"
            if s in TOP5:
                labels.append(r"$\mathbf{" + name.replace("_", r"\_") + r"}$" + suffix)
            else:
                labels.append(name + suffix)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels, fontsize=9)
    for tick, s in zip(ax.get_yticklabels(), rows):
        if s in or_rows:
            tick.set_fontweight("bold")

    # rule separating the OR summary rows from the per-seed rows
    ax.axhline(len(or_rows) - 0.5, color="white", lw=2.5)

    for i in range(len(rows)):
        emph = rows[i] in or_rows or rows[i] in TOP5
        for j in range(len(eras)):
            if mat[i, j] > 0.005:
                ax.text(j, i, f"{mat[i, j]*100:.0f}", ha="center", va="center",
                        fontsize=9 if emph else 8,
                        fontweight="bold" if emph else "normal",
                        color="white" if mat[i, j] < 0.6 else "black")

    ax.set_title(f"{HLT_PATHS[path_idx]}\ncontribution of each L1 seed [%], by era"
                 "\n(bold = enabled in modules/muon_selection.py)", fontsize=12)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("fraction of HLT-fired events in which the seed also fired", fontsize=10)
    fig.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def plot_era_bars(era, seeds, table, path_idx, pdf, top=12):
    vals = sorted(((table[era].get(s, np.zeros(2))[path_idx], s) for s in seeds), reverse=True)[:top]
    if not vals or vals[0][0] == 0:
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    ys = np.arange(len(vals))
    # colour by eta restriction: unrestricted seeds are the ones that widen the acceptance
    colors = ["crimson" if eta_restriction(s) >= 2.4 else "royalblue" for _, s in vals]
    ax.barh(ys, [v * 100 for v, _ in vals], color=colors)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{s.replace('L1_DoubleMu','DM')} [|$\\eta$|<{eta_restriction(s):g}]"
                        for _, s in vals], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("contribution to HLT-fired events [%]", fontsize=11)
    ax.set_xlim(0, 100)
    # The path name plus era is long and was overrunning the axes as a title; it reads
    # better as the legend header, where it sits next to the colour key it qualifies.
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="crimson", label=r"no $\eta$ restriction (|$\eta$|<2.4)"),
                       Patch(color="royalblue", label=r"$\eta$-restricted seed")],
              title=f"{HLT_PATHS[path_idx]}\nera {era}",
              title_fontsize=10, fontsize=9, loc="lower right")
    cms.cms_axes(ax)
    fig.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="L1 DoubleMu seed contributions per era")
    parser.add_argument("--output", default="getDoubleMuonPrescales.pdf")
    parser.add_argument("--n-files", type=int, default=N_FILES_PER_ERA,
                        help=f"files per PD folder per era (default {N_FILES_PER_ERA})")
    parser.add_argument("--test", action="store_true", help="1 file per PD folder per era")
    gj.add_args(parser)
    args = parser.parse_args()
    global CERT
    CERT = gj.from_args(args, log)

    n_files = 1 if args.test else args.n_files

    log(f"\n=== discovering eras ({n_files} file(s) per PD folder per era) ===")
    eras = discover(n_files)
    if not eras:
        raise SystemExit("[error] no data files found")
    log(f"\n{len(eras)} era(s): {', '.join(eras)}")

    table = {}          # era -> {seed: contribution array over HLT_PATHS}
    totals = {}
    log("\n=== scanning ===")
    for era, files in eras.items():
        n_hlt, counts = scan(files, era)
        totals[era] = n_hlt
        table[era] = {s: c / np.maximum(n_hlt, 1) for s, c in counts.items()}

    # seeds worth showing: reach MIN_CONTRIB in any era, for either path
    # The OR rows are summaries, not seeds -- they are added separately at the top of the
    # heatmap and must not compete for a place in the per-seed ranking.
    # Restricted to the framework's own seed list, ranked by mean contribution across
    # eras (the same ranking that picked TOP5). Coincidental seeds are excluded.
    seeds = sorted([s for s in FRAMEWORK_SEEDS if any(s in table[e] for e in table)],
                   key=lambda s: -np.mean([table[e].get(s, np.zeros(len(HLT_PATHS)))[0]
                                           for e in table]))
    log(f"\n{len(seeds)} framework seed(s) shown "
        f"({len(TOP5)} enabled in modules/muon_selection.py)")

    for j, path in enumerate(HLT_PATHS):
        log(f"\n=== {path} ===")
        hdr = "  " + "seed".ljust(46) + "|eta|  " + "  ".join(f"{e:>12s}" for e in eras)
        log(hdr)
        for n in OR_SETS:
            r = "  ".join(
                f"{table[e].get(or_label(n), np.zeros(len(HLT_PATHS)))[j]*100:11.1f}%"
                for e in eras)
            log(f"  {('>> ' + or_label(n)).ljust(46)}{'':5s}  {r}")
        log("  " + "-" * (len(hdr) - 2))
        for s in seeds:
            row = "  ".join(f"{table[e].get(s, np.zeros(len(HLT_PATHS)))[j]*100:11.1f}%"
                            for e in eras)
            mark = "*" if s in TOP5 else " "   # * = enabled in muon_selection.py
            log(f" {mark}{s.ljust(46)}{eta_restriction(s):5.1f}  {row}")
        log("  " + "-" * (len(hdr) - 2))
        log("  " + "N(HLT fired)".ljust(52) + "  ".join(f"{int(totals[e][j]):11,} " for e in eras))

    log("\n=== Writing PDF ===")
    with PdfPages(args.output) as pdf:
        for j in range(len(HLT_PATHS)):
            plot_heatmap(list(eras), seeds, table, j, pdf)
        for j in range(len(HLT_PATHS)):
            for era in eras:
                plot_era_bars(era, seeds, table, j, pdf)
    log(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
