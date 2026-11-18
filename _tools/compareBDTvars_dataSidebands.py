#!/usr/bin/env python3
"""BDT input variables after the full analysis preselection: data SIDEBANDS vs QCD vs MinBias vs signal.

Built on _tools/compareBDTvars.py (same page style, same binning logic, same "leading slot" convention) and on
_tools/limits1pct/ (same event selection, same 1% of the data, same sideband definition). One PDF per trigger
case (Mu10 = HLT_Mu10_Barrel_L1HP11_IP6, DoubleMu = HLT_DoubleMu4_3_LowMass), one variable per page.

Variables
---------
The deployed 2024 models (XGB_NOJETS_2024[_B1]_<case>.model, producer DQCD/Modules/python/
BDTULinference2024_4mu.py) take 532 inputs = 4 counters (nMuon, nSV, nmuonSV, nfourmuonSV) + 66 object variables
x 8 slots (Muon 16, muonSV 15, fourmuonSV 22, SV 13; NO jets). As compareBDTvars.py, the LEADING slot of each is
plotted -> 70 pages. The slot order is the producer's: Muon by pT (descending), muonSV and fourmuonSV with
charge == 0 by chi2 (ascending), SV by dlen (descending); counters are the raw nanoAOD ones. Events with no object
in a collection do not enter that collection's pages (the BDT gets the -999 padding there).

Selection (everything the framework applies before the BDT cut; identical to limits1pct/select_events.py, whose
module loader is imported): skim modules of config/modules_run3_efficienciesOnly_<trigger>.yaml (golden JSON for
data, MET filters, muon / muonSV / fourmuonSV / trigger / loose-muon selections, PU weight for MC, min-chi2
vertex), in one of the 12 categories (singlev/multiv cat1-6, multiv excluding quadv), material + dz veto on the
best-chi2 vertex. No BDT cut.

Curves (each normalised to unit area)
-------------------------------------
  Data sidebands  the SAME 1% of the data as limits1pct (data_dirs.json of $CMT_STORE/Limits1pct/v2/<case>: one
                  CRAB directory per (dataset, era), files nano_1..15), events weighted by n_total/n_read of their
                  directory. Sidebands as make_limits.py: muonSV_bestchi2_mass inside the fit window m +- 5 sigma
                  but outside the blinded core m +- 2 sigma, sigma = 0.01 m. One curve per mass hypothesis of the
                  two signal points (m = 1.33 and 0.33 GeV). Data in the cores is never written out.
  QCD             the 12 Mu-enriched pT-hat bins, all files (--qcd-frac 1; a seeded random subset below 1), every bin
                  weighted by xs / Sum(puWeight) of the events read (PreCounter-like) x puWeight. Full mass range.
  MinBias         InclusiveDileptonMinBias (DoubleMuOS43), all files (--minbias-frac), puWeight.
                  An ALTERNATIVE background model, never to be summed with the pT-binned QCD.
  Signal          scenario A  mpi=4, mA=1.33, ctau=10 and scenario B1 mpi=1, mA=0.33, ctau=10 (all files).

Usage (after `source setup.sh`):
  compareBDTvars_dataSidebands.py submit --case Mu10|DoubleMu [--test] [--local N]   # selection (condor or local)
  compareBDTvars_dataSidebands.py plot   --case Mu10|DoubleMu [--test] [--replot]    # PDFs, published
  (select is the per-job worker.)  --test: a handful of files per sample, tag "test", PDFs with the suffix _test.
  --replot: redraw from the cached histograms (label / style changes without re-reading the trees).
Outputs: $CMT_STORE/BDTvarsSidebands/<tag>/<case>/<dataset>/part_*.root (+ hists.pkl), PDFs in _tools/ and in
~/public_html/parking/2024/kinematic_checks/, each also as ..._withErrors, 70 pages, same binning in all of them:
  compareBDTvars_dataSidebands_<case>_bkgFullSample[_withErrors][_test].pdf
      QCD, MinBias and both signals as they pass the selection (no mass window); the two data sideband curves
  compareBDTvars_dataSidebands_<case>_bkgSidebands_mA<m>[_withErrors][_test].pdf   (m = 1p33, 0p33)
      data, QCD and MinBias all in the sidebands of that mass hypothesis; the signal of that mass, no mass window
"""
import argparse, glob, json, os, random, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path[:0] = [HERE, os.path.join(HERE, "limits1pct")]

XRD = "gfe02.grid.hep.ph.ic.ac.uk"
PUBLISH = os.path.expanduser("~/public_html/parking/2024/kinematic_checks")
STEM = "compareBDTvars_dataSidebands"
TRIGGER = {"Mu10": "HLT_Mu10_Barrel_L1HP11_IP6", "DoubleMu": "HLT_DoubleMu4_3_LowMass"}
LIMITS_TAG = "v2"                      # the limits1pct production whose 1% data list is reused
SIGNALS = [  # (dataset, label, mass, colour)
    ("scenarioA_mpi_4_mA_1p33_ctau_10", r"scA, $m_\pi$=4, $m_A$=1.33, $c\tau$=10 mm", 1.33, "#1f77b4"),
    ("scenarioB1_mpi_1_mA_0p33_ctau_10", r"scB1, $m_\pi$=1, $m_A$=0.33, $c\tau$=10 mm", 0.33, "#2ca02c"),
]
SB_MASSES = [1.33, 0.33]
SIGNAL_NOTE = ", no mass window"     # on the _bkgSidebands pages: the signal is NOT cut to the sideband window
SB_COLORS = {1.33: "black", 0.33: "0.45"}
SIGMA_REL, N_FIT, N_BLIND = 0.01, 5, 2   # make_limits.py: window m +- 5 sigma, core m +- 2 sigma, sigma = 0.01 m
QCD_XS = {"qcd_15to20": 3018000, "qcd_20to30": 2701000, "qcd_30to50": 1461000, "qcd_50to80": 407600,
          "qcd_80to120": 96070, "qcd_120to170": 23140, "qcd_170to300": 7754, "qcd_300to470": 699.6,
          "qcd_470to600": 67.67, "qcd_600to800": 21.27, "qcd_800to1000": 3.89, "qcd_1000toInf": 1.323}
MINBIAS = "minbias"
MINBIAS_DIR = ("/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/ppradeep/samples/Parking/Run3/Nanotronv14/"
               "InclusiveDileptonMinBias_Fil-DoubleMuOS43_TuneCP5Plus_13p6TeV_pythia8/2024WithMET/260730_143555")
QCD_FRAC, MINBIAS_FRAC, SEED = 1.0, 1.0, 0     # user 2026-11-11: all of QCD and MinBias

# model inputs (BDTULinference2024_4mu.py INPUT_LAYOUT): collection -> (sort key, ascending, charge filter, vars)
COUNTERS = ["nMuon", "nSV", "nmuonSV", "nfourmuonSV"]
LAYOUT = {
    "Muon": ("Muon_pt", False, False,
             ["eta", "phi", "pt", "ptErr", "dxy", "dxyErr", "dz", "dzErr", "ip3d", "sip3d", "charge", "tightId",
              "softMva", "pfRelIso03_all", "miniPFRelIso_all", "jetIdx"]),
    "muonSV": ("muonSV_chi2", True, True,
               ["chi2", "pAngle", "dlen", "dlenSig", "dxy", "dxySig", "mu1pt", "mu1eta", "mu1phi", "mu2pt",
                "mu2eta", "mu2phi", "x", "y", "z"]),
    "fourmuonSV": ("fourmuonSV_chi2", True, True,
                   ["chi2", "pAngle", "dlen", "dlenSig", "dxy", "dxySig", "mu1pt", "mu1eta", "mu1phi", "mu2pt",
                    "mu2eta", "mu2phi", "mu3pt", "mu3eta", "mu3phi", "mu4pt", "mu4eta", "mu4phi", "x", "y", "z",
                    "mass"]),
    "SV": ("SV_dlen", False, False,
           ["pt", "eta", "phi", "x", "y", "z", "dxy", "dxySig", "dlen", "dlenSig", "pAngle", "chi2", "ndof"]),
}
ALL_VARS = COUNTERS + [f"{c}_{v}" for c, (_, _, _, vs) in LAYOUT.items() for v in vs]


def sideband_expr(m, var="mass"):
    s = SIGMA_REL * m
    return (f"({var} > {m - N_FIT * s} && {var} < {m + N_FIT * s} && "
            f"!({var} > {m - N_BLIND * s} && {var} < {m + N_BLIND * s}))")


def store_dir(tag, case):
    return os.path.join(os.environ["CMT_STORE"], "BDTvarsSidebands", tag, case)


# ------------------------------------------------------------------------------------------------ select (worker)
def select(a):
    import array
    import select_events as se                      # limits1pct: the framework module loader + category strings
    sys.path[:0] = [REPO, os.environ.get("CMT_BASE", "")]
    import ROOT
    ROOT.gROOT.SetBatch(True)
    dir_ids = [int(x) for x in a.dir_ids.split(",")] if a.dir_ids else []
    if dir_ids and len(dir_ids) != len(a.files):
        sys.exit("--dir-ids must have one entry per input file")

    mods = se.load_skim_modules(a.case, se.fake_task(a.dataset, a.mc))
    chain = ROOT.TChain("Events")
    for f in a.files:
        chain.Add(f)
    df = ROOT.RDataFrame(chain)
    n_raw = df.Count()
    if a.mc:
        df, _ = mods.pop("puweight").run(df)
        sumw_raw = df.Sum("puWeight")
    else:
        mods.pop("puweight").run(df)
        sumw_raw = n_raw
    if dir_ids:
        expr = " : ".join(f'(rdfsampleinfo_.Contains("{f}") ? {i}' for f, i in zip(a.files, dir_ids))
        df = df.DefinePerSample("dirid", "(int) (" + expr + " : -1" + ")" * len(dir_ids) + ")")
    else:
        df = df.Define("dirid", "(int) -1")
    df = df.Define("selection", "event >= 0").Filter("selection", "base")
    for key, mod in mods.items():
        df, _ = mod.run(df)

    cat = " : ".join(f"({se.SINGLE} && {s}) ? {i + 1}" for i, s in enumerate(se.DXY_P))
    cat += " : " + " : ".join(f"({se.MULTI} && {s}) ? {i + 7}" for i, s in enumerate(se.DXY_P)) + " : 0"
    df = (df.Define("cat", cat)
            .Define("mass", "(float) muonSV_bestchi2_mass")
            .Define("weight", "(float) puWeight" if a.mc else "1.f")
            .Filter("cat > 0", "in a category")
            .Filter(se.DXYZ_CUT, "material + dz veto"))
    if not a.mc:    # data: sidebands only, the cores never leave the job
        df = df.Filter(" || ".join(sideband_expr(m) for m in SB_MASSES), "data sidebands")

    # leading slot of every collection, ordered as the BDT producer does
    ROOT.gInterpreter.Declare("""
        template <typename K, typename M> int bv_first(const K& key, const M& ok, bool asc) {
            int b = -1;
            for (size_t i = 0; i < key.size(); ++i) {
                if (!ok[i]) continue;
                if (b < 0 || (asc ? key[i] < key[b] : key[i] > key[b])) b = i;   // strict: stable_sort ties
            }
            return b;
        }""")
    have = set(str(c) for c in df.GetColumnNames())
    out = ["mass", "cat", "weight", "dirid"]
    for c in COUNTERS:
        if c in have:
            df = df.Define(f"bv_{c}", f"(float) {c}"); out.append(f"bv_{c}")
    for coll, (key, asc, charge, vs) in LAYOUT.items():
        if key not in have:
            print(f"[warn] no {key}: {coll} variables skipped"); continue
        ok = f"{coll}_charge == 0" if charge else f"{key} == {key}"
        df = df.Define(f"bv_i_{coll}", f"bv_first({key}, {ok}, {'true' if asc else 'false'})")
        for v in vs:
            if f"{coll}_{v}" not in have:
                print(f"[warn] no {coll}_{v}"); continue
            df = df.Define(f"bv_{coll}_{v}", f"bv_i_{coll} >= 0 ? (float) {coll}_{v}[bv_i_{coll}] : (float) NAN")
            out.append(f"bv_{coll}_{v}")

    report = df.Report()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    df.Snapshot("Events", tmp, out)
    f = ROOT.TFile.Open(tmp, "UPDATE")
    t = ROOT.TTree("Norm", "PreCounter-like normalisation")
    nr, sw, nf = array.array("d", [0]), array.array("d", [0]), array.array("i", [0])
    files = ROOT.std.string(";".join(a.files))
    t.Branch("n_raw", nr, "n_raw/D"); t.Branch("sumw_raw", sw, "sumw_raw/D")
    t.Branch("n_files", nf, "n_files/I"); t.Branch("files", files)
    nr[0] = n_raw.GetValue(); sw[0] = float(sumw_raw.GetValue()); nf[0] = len(a.files)
    t.Fill(); t.Write(); f.Close()
    os.replace(tmp, a.out)
    report.Print()
    print(f"n_raw {nr[0]:.0f} sumw_raw {sw[0]:.2f} n_files {nf[0]} -> {a.out}")


# ------------------------------------------------------------------------------------------------ submit
def xrd(f):
    return f if f.startswith("root://") else f"root://{XRD}/" + f


def sample_lists(a):
    """{dataset: (is_mc, [(file, dirid or None)], n_available)} + the data-directory info."""
    import submit as lsub                            # limits1pct/submit.py: cached lists, signal files
    tmp_dir = os.environ["CMT_TMP_DIR"]
    rng = lambda: random.Random(SEED)
    info = json.load(open(os.path.join(os.environ["CMT_STORE"], "Limits1pct", LIMITS_TAG, a.case, "data_dirs.json")))
    data = [(xrd(f), d["id"]) for d in info["dirs"] for f in d["files"]]
    if a.test:
        data = rng().sample(data, 20)
    out = {lsub.DATA[a.case]: (False, data, info["n_total"])}
    for ds in QCD_XS:
        files = sorted(xrd(f) for f in lsub.cached_list(tmp_dir, ds))
        n = 2 if a.test else max(1, round(a.qcd_frac * len(files)))
        out[ds] = (True, [(f, None) for f in sorted(rng().sample(files, n))], len(files))
    mb = sorted(xrd(f) for f in lsub.xrdfs_ls(MINBIAS_DIR))
    if not mb:
        sys.exit(f"no MinBias files listed under {MINBIAS_DIR} (proxy?)")
    n = 5 if a.test else max(1, round(a.minbias_frac * len(mb)))
    out[MINBIAS] = (True, [(f, None) for f in sorted(rng().sample(mb, n))], len(mb))
    for ds, *_ in SIGNALS:
        files = lsub.signal_files(ds, tmp_dir)
        out[ds] = (True, [(f, None) for f in (files[:2] if a.test else files)], len(files))
    return out, info


def submit(a):
    tag = a.tag or ("test" if a.test else "v2")
    store = store_dir(tag, a.case)
    os.makedirs(store, exist_ok=True)
    samples, info = sample_lists(a)
    with open(os.path.join(store, "samples.json"), "w") as f:
        json.dump({"data_dirs": info, "samples": {ds: {"mc": mc, "n_available": na, "files": [x[0] for x in fl]}
                                                  for ds, (mc, fl, na) in samples.items()}}, f, indent=1)
    per_job = {False: a.files_per_job, True: a.mc_files_per_job}
    todo = []
    for ds, (mc, fl, na) in samples.items():
        n = per_job[mc]
        print(f"  {ds:36s} {len(fl):>5} of {na:>6} files")
        for i in range(0, len(fl), n):
            o = os.path.join(store, ds, f"part_{i // n}.root")
            if not os.path.exists(o):
                chunk = fl[i:i + n]
                todo.append((ds, mc, o, [c[0] for c in chunk], [c[1] for c in chunk] if not mc else None))
    print(f"{len(todo)} jobs to run -> {store}")
    if not todo or a.dry_run:
        return
    jobdir = os.path.join(store, "condor"); os.makedirs(jobdir, exist_ok=True)
    jobs_file = os.path.join(jobdir, f"jobs_{os.getpid()}.txt")
    with open(jobs_file, "w") as f:
        for ds, mc, o, files, ids in todo:
            f.write(f"{ds} {'--mc' if mc else '-'} {o} {','.join(files)} "
                    f"{','.join(str(i) for i in ids) if ids else '-'}\n")
    wrapper = os.path.join(jobdir, "run.sh")
    with open(wrapper, "w") as f:
        f.write(f"""#!/bin/bash
# $1 jobs file, $2 0-based job index. Line: dataset, --mc or -, output, comma-separated files, dir ids or -
read -r DS MC OUT FILES IDS < <(sed -n "$(( $2 + 1 ))p" "$1")
cd {REPO}
source setup.sh > /dev/null 2>&1
export OMP_NUM_THREADS=1
[ "$MC" = "--mc" ] || MC=""
[ "$IDS" = "-" ] && IDS="" || IDS="--dir-ids $IDS"
timeout 10000 python3 {os.path.abspath(__file__)} select --case {a.case} --dataset $DS $MC $IDS --out $OUT ${{FILES//,/ }}
""")
    os.chmod(wrapper, 0o755)
    if a.local:
        from concurrent.futures import ThreadPoolExecutor
        def run(i):
            with open(os.path.join(jobdir, f"local_{i}.log"), "w") as log:
                return subprocess.run([wrapper, jobs_file, str(i)], stdout=log, stderr=subprocess.STDOUT).returncode
        with ThreadPoolExecutor(a.local) as ex:
            rcs = list(ex.map(run, range(len(todo))))
        print(f"local run: {sum(r == 0 for r in rcs)}/{len(rcs)} jobs OK (logs in {jobdir})")
        return
    sub = os.path.join(jobdir, f"submit_{os.getpid()}.sub")
    with open(sub, "w") as f:
        f.write(f"""universe = vanilla
executable = {wrapper}
arguments = {jobs_file} $(Process)
getenv = true
output = /dev/null
error = {jobdir}/err_$(Cluster)_$(Process).txt
log = /dev/null
request_cpus = 1
request_memory = 2000
+MaxRuntime = 10799
x509userproxy = {os.environ.get('X509_USER_PROXY', '')}
queue {len(todo)}
""")
    print(subprocess.run(["condor_submit", sub], capture_output=True, text=True).stdout.strip())


# ------------------------------------------------------------------------------------------------ plot
def load(ROOT, files, cols):
    """{col: np.array} over the non-empty parts (Snapshot writes no branches when nothing is selected)."""
    import numpy as np
    good = []
    for f in files:
        t = ROOT.TFile.Open(f)
        tr = t.Get("Events") if t and not t.IsZombie() else None
        if tr and tr.GetEntries() > 0:
            good.append(f)
        if t:
            t.Close()
    if not good:
        return {}
    df = ROOT.RDataFrame("Events", good)
    have = set(str(c) for c in df.GetColumnNames())
    arr = df.AsNumpy([c for c in cols if c in have])
    return {k: np.asarray(v) for k, v in arr.items()}


def norm_info(ROOT, files):
    """(sum of sumw_raw, files read) from the Norm trees."""
    sumw, read = 0., []
    ch = ROOT.TChain("Norm")
    for f in files:
        ch.Add(f)
    for ev in ch:
        sumw += ev.sumw_raw
        read += str(ev.files).split(";")
    return sumw, read


def fmt_n(n):
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.1f}k" if n >= 1e4 else f"{n:,.0f}"


def plot(a):
    import pickle
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import cmsstyle as cms
    import compareBDTvars as base                    # binning logic + page style constants

    tag = a.tag or ("test" if a.test else "v2")
    store = store_dir(tag, a.case)
    cache = os.path.join(store, "hists.pkl")
    if a.replot:
        with open(cache, "rb") as f:
            C = pickle.load(f)
    else:
        C = fill_histograms(a, store, base)
        with open(cache, "wb") as f:
            pickle.dump(C, f)
        print(f"histograms cached in {cache} (redraw with --replot)")
    H, ranges, scales, partial = C["H"], C["ranges"], C["scales"], C["partial"]
    n_data_read, n_data_total = C["n_data_read"], C["n_data_total"]
    cms.set_lumi_files(n_data_read, n_data_total)
    cms.set_sample_files(1, 1)      # the per-sample partial lines are written explicitly below
    want = [v for v in ALL_VARS if v in ranges]
    if a.only_vars:
        want = [v for v in want if re.search(a.only_vars, v)]
    pct = f"{100. * n_data_read / n_data_total:.2f}% of 2024 data"
    head = [f"{TRIGGER[a.case]} selection, no BDT cut",
            "  preselection, 12 categories, material + dz veto"]
    window = rf"{N_BLIND}%<$|m_{{\mu\mu}}/m_A-1|$<{N_FIT}%"

    def write(path, errors, curves, info, partial):
        """curves = [(histogram key, label, colour, kind)]"""
        with PdfPages(path) as pdf:
            for var in want:
                edges = ranges[var]
                centres = 0.5 * (edges[:-1] + edges[1:])
                fig, ax = plt.subplots(figsize=(7.4, 5.6))
                drawn, ypos = False, []
                for key, label, colour, kind in curves:
                    if var not in H.get(key, {}):
                        continue
                    h, h2, n = H[key][var]
                    tot = h.sum()
                    if tot <= 0:
                        continue
                    y = h / tot
                    drawn = True
                    ypos += [y[y > 0].min(), y.max()]
                    mk, z, lw = {}, 2, 1.4
                    if kind == "data":
                        mk = dict(marker=base.DATA_MARKER, markersize=base.DATA_MARKER_SIZE, markerfacecolor=colour,
                                  markeredgecolor=colour, markeredgewidth=base.MARKER_EDGE)
                        z, lw = 5, 1.8
                    elif kind == "bkg":
                        mk = dict(marker=base.BKG_MARKER, markersize=base.BKG_MARKER_SIZE, markerfacecolor="white",
                                  markeredgecolor=colour, markeredgewidth=base.MARKER_EDGE)
                    ax.plot(centres, y, drawstyle="steps-mid", color=colour, lw=lw, zorder=z,
                            label=f"{label} ({fmt_n(n)})", **mk)
                    if errors:
                        err = np.sqrt(h2) / tot
                        lo = np.where(y - err > 0, y - err, 1e-12)
                        ax.fill_between(centres, lo, y + err, step="mid", color=colour, alpha=cms.BAND_ALPHA,
                                        lw=0, zorder=z - 1)
                ax.set_xscale(scales.get(var, "linear"))
                ax.set_xlabel(var + " (leading slot)" if var not in COUNTERS else var, fontsize=base.FS_LABEL)
                ax.set_ylabel("Fraction of events / bin", fontsize=base.FS_LABEL)
                ax.set_yscale("log")
                ax.set_xlim(edges[0], edges[-1])
                cms.cms_axes(ax, header=cms.lumi_header(), fontsize=base.FS_AXES, label=cms.CMS_LABEL_DATA)
                if drawn:
                    # explicit limits: empty bins (y = 0) must not drag a log axis down
                    ax.set_ylim(max(min(ypos) * 0.5, max(ypos) * 1e-5), max(ypos) * 1.5)
                    cms.extend_log_top(ax, frac=0.55)
                    ax.legend(loc="upper right", fontsize=base.FS_LEGEND - 1, **cms.LEGEND_KW)
                    part = [f"  {n}: {r:,} of {t:,} files ({100 * r / t:.2g}%)" for n, r, t in partial if t and r < t]
                    lines = info + (["Partial sample plot"] + part if part else [])
                    leg = cms.info_legend(ax, lines, loc="upper left", fontsize=base.FS_PARTIAL - 1)
                    if part:
                        leg.get_texts()[len(info)].set_fontweight("bold")
                fig.tight_layout()
                pdf.savefig(fig)
                plt.close(fig)
        os.makedirs(PUBLISH, exist_ok=True)
        dest = os.path.join(PUBLISH, os.path.basename(path))
        shutil.copyfile(path, dest); os.chmod(dest, 0o644)
        print(f"wrote {path} ({len(want)} pages) -> {dest}")

    sfx = "_test" if a.test else ""
    out = a.output or os.path.join(HERE, f"{STEM}_{a.case}")
    bkgs = [("qcd", base.QCD_LABEL, base.QCD_COLOR), (MINBIAS, base.MINBIAS_LABEL, base.MINBIAS_COLOR)]

    # (1) _bkgFullSample: QCD, MinBias and signal as they pass the selection (no mass window); data in the sidebands
    curves = [(f"data|sb{m}", f"Data sidebands, $m_A$={m:g}", SB_COLORS[m], "data") for m in SB_MASSES]
    curves += [(f"{k}|full", label, colour, "bkg") for k, label, colour in bkgs]
    curves += [(f"{ds}|full", label, colour, "sig") for ds, label, _, colour in SIGNALS]
    info = head + [f"  Data: sidebands only, {window}, {pct}",
                   "  MC: no mass window.  Leading slot of each collection"]
    write(f"{out}_bkgFullSample{sfx}.pdf", False, curves, info, partial)
    write(f"{out}_bkgFullSample_withErrors{sfx}.pdf", True, curves, info, partial)

    # (2) _bkgSidebands_mA<m>: QCD and MinBias in the SAME sideband window as the data, one PDF per mass hypothesis
    # (the signal of that mass has no mass window: it lives in the blinded core). Same binning as (1).
    for m in SB_MASSES:
        curves = [(f"data|sb{m}", f"Data sidebands, $m_A$={m:g}", "black", "data")]
        curves += [(f"{k}|sb{m}", label + ", sidebands", colour, "bkg") for k, label, colour in bkgs]
        curves += [(f"{ds}|full", label + SIGNAL_NOTE, colour, "sig") for ds, label, ms, colour in SIGNALS if ms == m]
        info = head + [rf"  Data, QCD, MinBias: $m_A$={m:g} sidebands,",
                       f"  {window};  signal: no mass window",
                       f"  {pct}.  Leading slot of each collection"]
        part_m = [t for t in partial if not t[0].startswith("sc") or f"$m_A$={m:g}" in t[0]]
        stem = f"{out}_bkgSidebands_mA{m:g}".replace(".", "p")
        write(f"{stem}{sfx}.pdf", False, curves, info, part_m)
        write(f"{stem}_withErrors{sfx}.pdf", True, curves, info, part_m)


def fill_histograms(a, store, base):
    """Stream the slim trees (a few parts at a time: the full MinBias is tens of millions of events) into
    histograms H[key][var] = [sum w, sum w^2, raw entries], keys "<sample>|full" and "<sample>|sb<m>"."""
    import numpy as np
    import ROOT
    ROOT.gROOT.SetBatch(True)
    import submit as lsub
    meta = json.load(open(os.path.join(store, "samples.json")))
    cols = ["mass", "weight", "dirid"] + [f"bv_{v}" for v in ALL_VARS]
    parts = lambda ds: sorted(glob.glob(os.path.join(store, ds, "part_*.root")))
    CHUNK = 8

    def sb(x, m):
        s = SIGMA_REL * m
        return (x > m - N_FIT * s) & (x < m + N_FIT * s) & ~((x > m - N_BLIND * s) & (x < m + N_BLIND * s))

    # ---- data: per-directory weights n_total/n_read (files actually read), as make_limits.data_weights
    dirs = meta["data_dirs"]["dirs"]
    ds_data = lsub.DATA[a.case]
    _, read = norm_info(ROOT, parts(ds_data))
    n_read = {d["id"]: 0 for d in dirs}
    by_dir = {d["dir"]: d["id"] for d in dirs}
    for f in read:
        m = lsub.CRAB_DIR_RE.match(f.split(XRD + "/")[-1])
        if m and m.group(1) in by_dir:
            n_read[by_dir[m.group(1)]] += 1
    wdir = np.array([d["n_total"] / n_read[d["id"]] if n_read[d["id"]] else 0. for d in dirs])
    n_data_read, n_data_total = sum(n_read.values()), meta["data_dirs"]["n_total"]
    partial = [("Data", n_data_read, n_data_total)]
    print(f"data: {n_data_read} of {len(meta['samples'][ds_data]['files'])} selected files read "
          f"({100. * n_data_read / n_data_total:.2f}% of {n_data_total})")

    # sources: (dataset, histogram sample key, per-event weight function, regions)
    sb_regions = {f"sb{m}": (lambda x, m=m: sb(x, m)) for m in SB_MASSES}
    full = {"full": lambda x: np.ones(len(x), dtype=bool)}
    src = [(ds_data, "data", lambda d: wdir[d["dirid"].astype(int)], sb_regions)]
    qread = qavail = 0
    for ds, xs in QCD_XS.items():
        sumw, read = norm_info(ROOT, parts(ds))
        qread += len(read); qavail += meta["samples"][ds]["n_available"]
        print(f"  {ds:16s} {len(read):>5} files, weight/event {xs / sumw if sumw else 0:.3g}")
        if sumw:
            src.append((ds, "qcd", lambda d, k=xs / sumw: d["weight"] * k, {**full, **sb_regions}))
    partial.append((f"QCD ({len(QCD_XS)} pT bins)", qread, qavail))
    _, read = norm_info(ROOT, parts(MINBIAS))
    partial.append(("MinBias", len(read), meta["samples"][MINBIAS]["n_available"]))
    src.append((MINBIAS, MINBIAS, lambda d: d["weight"], {**full, **sb_regions}))
    for ds, label, m, colour in SIGNALS:
        _, read = norm_info(ROOT, parts(ds))
        partial.append((label.split(",")[0] + f", $m_A$={m:g}", len(read), meta["samples"][ds]["n_available"]))
        src.append((ds, ds, lambda d: d["weight"], full))

    # ---- pass 1, binning: compareBDTvars.build_ranges (median over samples of each sample's own percentiles),
    # from the first parts of every dataset (data: each sideband is its own sample)
    scan = {}
    for ds, key, wf, regions in src:
        d = load(ROOT, parts(ds)[:5 * CHUNK], cols)
        if not d:
            continue
        for rname, rf in (regions.items() if key == "data" else [("full", full["full"])]):
            sel = rf(d["mass"])
            scan[f"{ds}|{rname}"] = {}
            for var in ALL_VARS:
                x = d.get(f"bv_{var}")
                if x is not None:
                    x = x[sel]
                    x = x[np.isfinite(x)]
                    if len(x):
                        scan[f"{ds}|{rname}"][var] = [x[:20000]]
    ranges, scales = base.build_ranges(scan)
    missing = [v for v in ALL_VARS if v not in ranges]
    if missing:
        print(f"[warn] no binning (no entries) for: {missing}")

    # ---- pass 2, fill (values outside the axis go to the edge bins)
    H = {}
    for ds, key, wf, regions in src:
        pl = parts(ds)
        nsel = 0
        for i in range(0, len(pl), CHUNK):
            d = load(ROOT, pl[i:i + CHUNK], cols)
            if not d:
                continue
            w = wf(d).astype(np.float64)
            sels = {r: rf(d["mass"]) for r, rf in regions.items()}
            nsel += len(w)
            for var, edges in ranges.items():
                x = d.get(f"bv_{var}")
                if x is None:
                    continue
                ok = np.isfinite(x)
                nb = len(edges) - 1
                idx = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, nb - 1)
                for r, sel in sels.items():
                    k = ok & sel
                    h = H.setdefault(f"{key}|{r}", {}).setdefault(var, [np.zeros(nb), np.zeros(nb), 0])
                    h[0] += np.bincount(idx[k], weights=w[k], minlength=nb)
                    h[1] += np.bincount(idx[k], weights=w[k] ** 2, minlength=nb)
                    h[2] += int(k.sum())
        print(f"  {ds:36s} {len(pl):>5} parts, {nsel:>9} selected events")
    return {"H": H, "ranges": ranges, "scales": scales, "partial": partial,
            "n_data_read": n_data_read, "n_data_total": n_data_total}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("select")
    s.add_argument("--case", required=True, choices=list(TRIGGER)); s.add_argument("--dataset", required=True)
    s.add_argument("--mc", action="store_true"); s.add_argument("--dir-ids", default="")
    s.add_argument("--out", required=True); s.add_argument("files", nargs="+")
    s = sp.add_parser("submit")
    s.add_argument("--case", required=True, choices=list(TRIGGER)); s.add_argument("--tag", default=None)
    s.add_argument("--test", action="store_true"); s.add_argument("--dry-run", action="store_true")
    s.add_argument("--local", type=int, default=0, help="run the jobs here with this many parallel workers")
    s.add_argument("--qcd-frac", type=float, default=QCD_FRAC); s.add_argument("--minbias-frac", type=float, default=MINBIAS_FRAC)
    s.add_argument("--files-per-job", type=int, default=5); s.add_argument("--mc-files-per-job", type=int, default=20)
    s = sp.add_parser("plot")
    s.add_argument("--case", required=True, choices=list(TRIGGER)); s.add_argument("--tag", default=None)
    s.add_argument("--test", action="store_true"); s.add_argument("--only-vars", default=None)
    s.add_argument("--replot", action="store_true", help="redraw from the cached histograms (hists.pkl in the store)")
    s.add_argument("--output", default=None, help="output stem (default _tools/compareBDTvars_dataSidebands_<case>)")
    a = ap.parse_args()
    {"select": select, "submit": submit, "plot": plot}[a.cmd](a)


if __name__ == "__main__":
    main()
