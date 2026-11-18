#!/usr/bin/env python3
"""
Compare two versions of a DQCD BDT inference producer on the same signal and QCD events,
e.g. the old positional sv_legacy_t fill (which omitted SV_mass and shifted every SV input
from x onwards) against the by-name fill (fix of 2026-11-04).

Each version runs in its own subprocess (the C++ function names declared by the producer
are per-model and would collide in one ROOT session). Events are matched by
(run, luminosityBlock, event). The variant with the higher signal-vs-QCD AUC is the one the
model was trained with.

Printed per variant: fraction of scored events whose score changes, mean/max |delta|, ROC AUC,
a paired bootstrap of delta AUC, and signal/QCD efficiencies at --cuts. Plot: score overlays
(signal, QCD) and ROC, CMS style, copied to ~/public_html/parking/2024/SF_checks.

Producer sources: a file path, or "<gitref>:<path>" relative to the DQCD/Modules repo
(e.g. "ae489ed:python/BDTULinferenceFinal.py"). --patch-sv-fill builds the NEW variant from
OLD by rewriting the positional sv_legacy_t init into a by-name fill.

Example (2018 paper model, reproduces AUC 0.9548 -> 0.9616):
    python3 _tools/compareBDTSVFill.py --old ae489ed:python/BDTULinferenceFinal.py --patch-sv-fill \\
        --model XGB_NOJETS_45_scenarioA_final.model --label paper_scA
Example (current producer vs its HEAD version):
    python3 _tools/compareBDTSVFill.py --old HEAD:python/BDTULinferenceFinal.py \\
        --new python/BDTULinferenceFinal.py --model XGB_NOJETS_2018_scenarioA_ReproductionJuan.model
"""
import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys

import numpy as np

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
MODULES = os.path.join(REPO, "nanoaod_base_analysis/data/cmssw/CMSSW_13_0_13/src/DQCD/Modules")
PUBLIC = os.path.expanduser("~/public_html/parking/2024/SF_checks")

XRD = "root://gfe02.grid.hep.ph.ic.ac.uk//pnfs/hep.ph.ic.ac.uk/data/cms"
DEFAULT_SIGNAL = [f"{XRD}/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_10/"
                  f"nanotron_ext/240328_174120/0000/nano_{i}.root" for i in (68, 83, 105)]
_Q = (f"{XRD}/store/user/mcitron/darkshowersamples/bparkProductionAll_V1p3/tmp/QCD_Pt-%s_MuEnrichedPt5_"
      "TuneCP5_13TeV-pythia8_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2_"
      "MINIAODSIM_v1p1_generationSync/output_1.root")
DEFAULT_QCD = [_Q % b for b in ("20To30", "30To50")]


# ------------------------------------------------------------------------------------------
def patch_sv_fill(src):
    """Positional `svs[i] = sv_legacy_t({SV_pt[i], ..., SV_ndof[i]});` -> by-name fill."""
    pat = re.compile(r"(?P<ind>[ \t]*)svs\[i\] = sv_legacy_t\(\{\s*(?P<args>(?:SV_\w+\[i\],?\s*)+)\}\);")
    def repl(m):
        names = re.findall(r"SV_(\w+)\[i\]", m.group("args"))
        return m.group("ind") + " ".join(f"svs[i].{n} = SV_{n}[i];" for n in names)
    out, n = pat.subn(repl, src)
    if n != 1:
        sys.exit(f"--patch-sv-fill: expected 1 positional sv_legacy_t init, found {n}")
    return out


def materialise(spec, dest):
    """file path or gitref:path (in DQCD/Modules) -> local file `dest`."""
    if os.path.isfile(spec):
        shutil.copy(spec, dest)
    elif os.path.isfile(os.path.join(MODULES, spec)):
        shutil.copy(os.path.join(MODULES, spec), dest)
    elif ":" in spec:
        src = subprocess.run(["git", "-C", MODULES, "show", spec], capture_output=True, text=True)
        if src.returncode:
            sys.exit(f"git show {spec} failed: {src.stderr.strip()}")
        open(dest, "w").write(src.stdout)
    else:
        sys.exit(f"cannot find producer source {spec}")
    return dest


# ------------------------------------------------------------------------------------------
def worker(a):
    """Run one producer variant, save scores (sorted by run/lumi/event) to a.out."""
    sys.argv = sys.argv[:1]
    import ROOT
    ROOT.EnableImplicitMT(4)
    spec = importlib.util.spec_from_file_location("bdtprod_variant", a.producer)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    model = a.model if os.path.isabs(a.model) else os.path.join(MODULES, "data", a.model)
    # the producer class name differs between lineages (DQCDULBDTNoJetProducer,
    # DQCDULBDTNoJetNoMETProducer, ...): take the one class defined in the file that has run()
    classes = [c for n, c in vars(mod).items() if isinstance(c, type) and c.__module__ == mod.__name__
               and hasattr(c, "run") and n.endswith("Producer")]
    if len(classes) != 1:
        sys.exit(f"expected one *Producer class in {a.producer}, found {[c.__name__ for c in classes]}")
    P = classes[0](isMC=True, year=a.year, scenario=a.scenario, model_path=model,
                   bdt_name="bdt", met_smear_tag=a.met_smear_tag)
    res = {}
    for lab, files in (("sig", a.signal_files), ("qcd", a.qcd_files)):
        df, cols = P.run(ROOT.RDataFrame("Events", files))
        d = df.AsNumpy([cols[0], "run", "luminosityBlock", "event"])
        key = np.stack([d["run"].astype(np.int64), d["luminosityBlock"].astype(np.int64),
                        d["event"].astype(np.int64)], 1)
        o = np.lexsort(key.T[::-1])
        res[lab], res[lab + "_key"] = d[cols[0]][o], key[o]
        print(f"  {lab}: {len(o)} events, scored {int((res[lab] != -1).sum())}")
    np.savez(a.out, **res)


# ------------------------------------------------------------------------------------------
def auc(s, b):
    from scipy.stats import rankdata
    r = rankdata(np.concatenate([s, b]))
    return (r[:len(s)].sum() - len(s) * (len(s) + 1) / 2) / (len(s) * len(b))


def roc(s, b):
    c = np.unique(np.concatenate([s, b]))[::-1]
    return np.array([np.mean(b >= x) for x in c]), np.array([np.mean(s >= x) for x in c])


def analyse(a, old, new):
    O, N = np.load(old), np.load(new)
    if not ((O["sig_key"] == N["sig_key"]).all() and (O["qcd_key"] == N["qcd_key"]).all()):
        sys.exit("event keys differ between the two variants")
    ms, mq = O["sig"] != -1, O["qcd"] != -1
    print(f"\n===== {a.label}")
    for lab, m in (("sig", ms), ("qcd", mq)):
        d = np.abs(O[lab][m] - N[lab][m])
        print(f"  {lab}: scored {m.sum()}, changed {np.mean(d > 1e-6):.1%}, "
              f"mean|d| {d.mean():.4f}, max|d| {d.max():.4f}")
    aucs = {}
    for tag, D in (("old", O), ("new", N)):
        s, q = D["sig"][ms], D["qcd"][mq]
        aucs[tag] = auc(s, q)
        effs = "  ".join(f">{c:g}: S {np.mean(s > c):.3f} B {np.mean(q > c):.4f}" for c in a.cuts)
        print(f"  {tag}: AUC {aucs[tag]:.4f} | {effs}")
    rng = np.random.default_rng(1)
    so, sn, qo, qn = O["sig"][ms], N["sig"][ms], O["qcd"][mq], N["qcd"][mq]
    dd = []
    for _ in range(a.bootstrap):
        i = rng.integers(0, len(so), len(so))
        j = rng.integers(0, len(qo), len(qo))
        dd.append(auc(sn[i], qn[j]) - auc(so[i], qo[j]))
    dd = np.array(dd)
    print(f"  dAUC(new-old) = {dd.mean():.4f} +- {dd.std():.4f} ({a.bootstrap} paired bootstrap "
          f"replicas, fraction <= 0: {np.mean(dd <= 0):.3f})")
    return O, N, ms, mq, aucs


def plot(a, O, N, ms, mq, aucs, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sys.path.insert(0, TOOLS)
    import cmsstyle as cms
    hdr = f"(13 TeV, {a.year})" if a.year <= 2018 else f"(13.6 TeV, {a.year})"
    fig, axs = plt.subplots(1, 3, figsize=(19, 5.8))
    fig.suptitle(f"{a.label}: {a.old_name} (dashed) vs {a.new_name} (solid); model {os.path.basename(a.model)}; "
                 "scored events, unit area", fontsize=cms.FS_TITLE - 3)
    bins = np.linspace(0, 1, 51)
    for ax, lab, m, col, nm in ((axs[0], "sig", ms, "tab:red", "Signal"), (axs[1], "qcd", mq, "tab:blue", "QCD")):
        for D, ls, t in ((O, "--", "old"), (N, "-", "new")):
            ax.hist(D[lab][m], bins, histtype="step", ls=ls, color=col, lw=1.8, density=True, label=f"{nm}, {t}")
        ax.set_yscale("log")
        ax.set_xlabel("BDT score", fontsize=cms.FS_LABEL)
        ax.set_ylabel("Fraction of events", fontsize=cms.FS_LABEL)
        ax.legend(loc="upper center", frameon=False, fontsize=cms.FS_LEGEND)
        cms.extend_log_top(ax)
        cms.cms_axes(ax, header=hdr, fontsize=cms.FS_AXES)
    ax = axs[2]
    for D, ls, t in ((O, "--", "old"), (N, "-", "new")):
        x, y = roc(D["sig"][ms], D["qcd"][mq])
        ax.plot(x, y, ls=ls, color="k", lw=1.8, label=f"{t}, AUC={aucs[t]:.4f}")
    ax.set_xscale("log")
    ax.set_xlim(1e-4, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("QCD efficiency", fontsize=cms.FS_LABEL)
    ax.set_ylabel("Signal efficiency", fontsize=cms.FS_LABEL)
    ax.legend(loc="upper left", frameon=False, fontsize=cms.FS_LEGEND)
    cms.cms_axes(ax, header=hdr, fontsize=cms.FS_AXES)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--old", help="producer source: file, DQCD/Modules-relative path or gitref:path")
    p.add_argument("--new", help="producer source (omit with --patch-sv-fill)")
    p.add_argument("--patch-sv-fill", action="store_true", help="NEW = OLD with the by-name SV fill")
    p.add_argument("--model", required=True, help="model file (absolute, or name in DQCD/Modules/data)")
    p.add_argument("--year", type=int, default=2018)
    p.add_argument("--scenario", default="A")
    p.add_argument("--met-smear-tag", default="", help='"" reads MET_pt from raw nano')
    p.add_argument("--signal-files", nargs="+", default=DEFAULT_SIGNAL)
    p.add_argument("--qcd-files", nargs="+", default=DEFAULT_QCD)
    p.add_argument("--cuts", type=float, nargs="+", default=[0.7, 0.98, 0.99])
    p.add_argument("--bootstrap", type=int, default=300)
    p.add_argument("--label", default="bdt_svfill")
    p.add_argument("--out-dir", default=os.path.join(os.environ.get("CMT_STORE", "/tmp"), "_tools_output", "bdt_svfill_check"))
    p.add_argument("--no-publish", action="store_true")
    # internal: one variant per subprocess
    p.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--producer", help=argparse.SUPPRESS)
    p.add_argument("--out", help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.worker:
        return worker(a)

    if not a.old or not (a.new or a.patch_sv_fill):
        p.error("need --old and either --new or --patch-sv-fill")
    if not os.environ.get("CMSSW_BASE"):
        sys.exit("CMSSW_BASE is not set: source setup.sh first")
    os.makedirs(a.out_dir, exist_ok=True)
    old_py = materialise(a.old, os.path.join(a.out_dir, f"{a.label}_old_producer.py"))
    new_py = os.path.join(a.out_dir, f"{a.label}_new_producer.py")
    if a.patch_sv_fill:
        open(new_py, "w").write(patch_sv_fill(open(old_py).read()))
    else:
        materialise(a.new, new_py)
    a.old_name, a.new_name = a.old, (a.new or f"{a.old} + by-name SV fill")

    outs = {}
    for tag, prod in (("old", old_py), ("new", new_py)):
        out = os.path.join(a.out_dir, f"{a.label}_{tag}.npz")
        cmd = [sys.executable, os.path.abspath(__file__), "--worker", "--producer", prod, "--out", out,
               "--model", a.model, "--year", str(a.year), "--scenario", a.scenario,
               "--met-smear-tag", a.met_smear_tag, "--signal-files", *a.signal_files,
               "--qcd-files", *a.qcd_files]
        print(f"running {tag} variant ({prod})")
        outs[tag] = subprocess.Popen(cmd), out
    for tag, (proc, _) in outs.items():
        if proc.wait():
            sys.exit(f"{tag} variant failed")

    O, N, ms, mq, aucs = analyse(a, outs["old"][1], outs["new"][1])
    pdf = os.path.join(a.out_dir, f"bdt_svfill_{a.label}.pdf")
    plot(a, O, N, ms, mq, aucs, pdf)
    print("written:", pdf)
    if not a.no_publish:
        os.makedirs(PUBLIC, exist_ok=True)
        shutil.copy(pdf, PUBLIC)
        print("copied to", PUBLIC)


if __name__ == "__main__":
    main()
