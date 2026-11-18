#!/usr/bin/env python3
"""
Stage 2 of the standalone 1%-data limits: fits, datacards, combine and plots, from the slim trees of
select_events.py. Reproduces CreateDatacardsDQCD / Fit / RunCombineDQCD / ParamPlotDQCD in data mode
(--fit-models fit_models_data, use_data), without law:

 per signal point (mass m) and category (singlev/multiv cat1-6), tight BDT region of the trigger case:
  * mass histogram muonSV_bestchi2_mass, 50 bins in [0.95 m, 1.05 m] (get_feature_mass_dxyzcut);
    fit range m +- 5 sigma, blinded m +- 2 sigma, sigma = 0.01 m                       (CreateDatacardsDQCD)
    m = GENERATED mass (label 0.33 -> 1/3 GeV etc., GENERATED_MASS / true_mass below)
  * background from DATA: envelope RooMultiPdf {pol1 (p0 0,-5,5), exp (c 0,-2,2), powerlaw a0*x^b0
    (a0 1,0,2; b0 0,-2,2)}, each fitted to the sidebands (binned, SumW2Error), parameters then frozen;
    if the sidebands hold < 10 (raw, unweighted) events: RooUniform instead             (Fit, base.get_fit)
  * background normalisation: floating <model>_norm starting at the data integral of the FULL window,
    range [0, 3x] ([0, 10] if empty)                                          (norm_bkg_to_data, save_proper_norm)
  * data_obs: the tight-region data in the full window
  * signal: Voigtian, mean m, sigma 0.0085 m, gamma 0.005 (all fixed); the "modelling" width systematic is
    built as in law: RooRealVar "modellingsigma" (constant) in sigma*(1+0.0015 m*modellingsigma) and the
    datacard line "modelling param 0 1" -- which combine ignores because no "modelling" variable exists, so
    the nuisance has no effect (the framework's effective behaviour, kept on purpose).
    rate = xs * lumi * sum(puWeight)_sel / sum(puWeight)_all, xs = 52.23 pb * 0.01 (ggH x BR(H->dark showers) = 1%)
  * "yieldscale rateParam * <signal> 0.01", frozen in combine -> limit on B(H->psi psi) = r * 1e-4
  * combine -M AsymptoticLimits --run blind -m 125 --freezeParameters yieldscale --cminDefaultMinimizerStrategy 0
    on the 12 categories combined, minus those with zero signal (CombineDatacards.avoid_empty_processes)

Scaling the 1% to the full 2024 dataset (default; --no-scale for the plain 1% result):
  every data event is weighted by n_total/n_read of its CRAB task directory (data_dirs.json written by submit.py,
  n_read = files actually read according to the Norm trees), and the signal is normalised to the full luminosity
  109.95 fb^-1 (reduced by the share of any directory with no file read). Without scaling the luminosity is the
  file-count fraction n_read/n_total of 109.95 fb^-1 and the data weights are 1.

  make_limits.py --case Mu10 --scenario A [--tag v2] [--no-scale] [--points p1,p2] [--jobs 8]

BDT threshold from data (--scan-bdt; AN-2023-119 section 9, user 2026-11-06): the expected limit is computed at
every threshold of --thresholds (the slim trees keep BDT > 0.6) with exactly the section-10 background estimation
above (signal region +-2 HWHM, envelope fitted to the data sidebands, function chosen at each point of the
likelihood scan through the discrete "pdf_index"), and the working point of each mass hypothesis is the threshold
with the smallest geometric mean of the median expected limit over its ctau points (the AN finds the optimum
ctau-independent). Outputs: bdt_scan_* (csv/json + limit-vs-threshold plots per mass, one line per ctau),
bdt_wp_* (chosen threshold per mass) and the usual limit products with the suffix _bestBDT.

Fixed background-efficiency working point from data sidebands (--wp-bkg-eff; AN Table 10: 1e-4 for scenario A,
1e-5 for B1, "auto" picks these): per mass hypothesis the BDT threshold is the (1 - eff) quantile of the BDT
score of the data events in the sidebands of the +-5 HWHM window (outside +-2 HWHM), all 12 categories, taken
from the no-BDT-cut selection (submit.py --tag v2_nobdt --no-signal --min-bdt -1, --nobdt-tag). Per-directory
1%->100% weights are applied to the quantile; the raw sideband count and the number of raw events above the
threshold are reported (with 1% of the data a 1e-5 point rests on O(1) event). Limits then run at these
thresholds: products with the suffix _WP1e-4 / _WP1e-5 (wp_tag), table bdt_wp_data_sc<S>_<case>_WP<eff>.csv.
Both working points are produced for every scenario (user 2026-11-06): --wp-bkg-eff 1e-4 and 1e-5, separate files.

Background from QCD MC instead of data (--bkg qcd, user 2026-11-06 "limits with data and QCD"): the 12 Mu-enriched
pT-binned QCD samples (config/run3_2024.py qcd_<bin>, cross sections below) selected with the same select_events.py
(submit.py --qcd --min-bdt -1, tag --qcd-tag), each event weighted by xs * lumi / sum(puWeight)_all of its bin.
  * data_obs and the background normalisation: the QCD MC of the TIGHT region in the full window (as data mode)
  * background shape: because the tight-region MC is sparse, the envelope functions are fitted to the LOOSE
    region (BDT > 0.6) QCD spectrum over the full window (no blinding needed for MC), as the framework's MC mode
    (CreateDatacardsDQCD: FitDQCD of "background" in the loose region); RooUniform if the loose region holds < 10
    raw MC events. Parameters frozen, function chosen by the discrete pdf_index as in data mode.
  * working points (--wp-bkg-eff): same definition as for data, on the xs-weighted QCD events in the sidebands
    (the AN's Table 10 efficiencies were defined on QCD MC)
  * luminosity: 109.95 fb^-1 (full 2024; 1% of it with --no-scale)
  Data vs QCD MC at the luminosity read (--bkg qcd --match-data-lumi; user 2026-11-12): QCD background built as the
  framework's MC mode (FitDQCD + CreateDatacardsDQCD with use_data off), no data event involved:
  * QCD MC and signal normalised to the luminosity of the data read (the --no-scale data luminosity)
  * per category: yield = LOOSE-region (BDT > 0.6) QCD in the window x the tight/loose ratio, the ratio being
    sum of weights (BDT > cut) / (BDT > 0.6) of the whole QCD sample with mass in 0-22 GeV (FitDQCD.get_additional_scaling;
    the framework measures it in category "base", here on the slim-tree events = inside the 12 categories after the
    material/dz veto). data_obs = that scaled loose spectrum, norm starts there, range [0, 3x]; shape as above.
  * BDT cut of each point from QCD MC ONLY (user 2026-11-17; before that it was copied from the data result):
    --wp-bkg-eff = the working point of the xs-weighted QCD sidebands, --scan-bdt = threshold scan of the QCD limits.
    The data curve keeps its own data-sideband cut, so the two curves are at different thresholds.
  * plots: data (stored result, green/yellow) vs QCD (blue), data1pct/<tag>/dataVSqcd/; stems limits_qcdMC_dataLumi_fwMC_*
  Data vs QCD MC at the full 2024 luminosity (--bkg qcd --match-data-full; user 2026-11-17): the same framework-MC
  mode, with QCD and signal normalised to the luminosity of the SCALED data result (109.95 fb^-1) thresholds from
  QCD only as above; the data curve is the stored scaled result (limits_data1pct_sc<S>_<case>_<WP>.json, dataUpscaled).
  Plots: data (stored scaled result) vs QCD -> data1pct/<tag>/dataVSqcdUpscaled/; QCD alone vs the 2018 HEPData limits
  as published -> data1pct/<tag>/qcdUpscaledVS2018/. Stems limits_qcdMC_fullLumi_fwMC_*.
  Products: limits_qcdMC_sc<S>_<case>_WP<eff>.*, bdt_wp_qcdMC_sc<S>_<case>_WP<eff>.csv, published under
  ~/public_html/parking/2024/limits/qcdMC/<tag>/<case>/scenario<S>/ (data: .../limits/data1pct/...).
"""
import argparse, glob, json, math, os, re, shutil, subprocess, sys
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TIGHT = {("A", "Mu10"): 0.9953, ("A", "DoubleMu"): 0.9958,          # config/run3_2024.py:43-62
         ("B1", "Mu10"): 0.9910, ("B1", "DoubleMu"): 0.9955}
DATA = {"Mu10": "data_2024_singlemu_1percent", "DoubleMu": "data_2024_doublemu_1percent"}
HLT_NAME = {"Mu10": "HLT_Mu10_Barrel_L1HP11_IP6", "DoubleMu": "HLT_DoubleMu4_3_LowMass"}   # select_events.py SKIM_YAML
SIGNAL_XS = 52.23 * 0.01
CATS = [f"singlev_cat{i}" for i in range(1, 7)] + [f"multiv_cat{i}" for i in range(1, 7)]
MIN_EVENTS_FOR_FITTING = 10
DEFAULT_THRESHOLDS = [0.6, 0.8, 0.9, 0.95, 0.97, 0.98, 0.99, 0.995, 0.997, 0.998, 0.999]
AN_WP_EFF = {"A": 1e-4, "B1": 1e-5}   # AN-2023-119 Table 10 background efficiencies
LOOSE_BDT = 0.6                         # loose region of the trigger case (select_events.py LOOSE_BDT)
LUMI_FULL_PB = 109950.                  # 2024 C-I, run3_2024.py lumi_pb
# Mu-enriched pT-binned QCD MC: cross sections [pb] copied from config/run3_2024.py (xs dict, xsdb)
QCD_XS = {"qcd_15to20": 3018000, "qcd_20to30": 2701000, "qcd_30to50": 1461000, "qcd_50to80": 407600,
          "qcd_80to120": 96070, "qcd_120to170": 23140, "qcd_170to300": 7754, "qcd_300to470": 699.6,
          "qcd_470to600": 67.67, "qcd_600to800": 21.27, "qcd_800to1000": 3.89, "qcd_1000toInf": 1.323}
BKG_LABEL = {"data": "data1pct", "qcd": "qcdMC"}
CRAB_DIR_RE = re.compile(r"^(.*)/\d{4}/nano_\d+\.root$")
LL = {"A": "A'", "B1": r"\pi_3"}   # the long-lived particle whose ctau is scanned
# 2018 reference limits (limits_2018/*.txt, see _tools/limits_2018_{digitize_AN,hepdata}.py): every limit plot is also
# written with them overlaid, file suffix _compare2018<source>Limits
REF2018_DIR = os.path.join(REPO, "limits_2018")
REF2018 = {"AN": "2018 AN", "HEPData": "2018 HEPData"}
REF2018_LUMI = "41.6 fb$^{-1}$ (13 TeV)"
REF2018_COLS = ("obs", "exp", "e68lo", "e68hi", "e95lo", "e95hi")
VARIANTS = [("", None)] + [(f"_compare2018{k}Limits", k) for k in REF2018]


def load_2018(source, scenario, mpi, m):
    """2018 limits of one (scenario, m_pi, m_A') set from limits_2018/, None when that set was not published."""
    import numpy as np
    path = os.path.join(REF2018_DIR, f"limits_2018_{source}_sc{scenario}_mA{float(m):g}.txt".replace(".", "p", 1))
    if not os.path.exists(path):
        return None
    head = "".join(l for l in open(path) if l.startswith("#"))
    if float(re.search(r"m_pi3 = ([\d.]+)", head).group(1)) != float(mpi):
        return None
    d = np.loadtxt(path, ndmin=2)
    return {"ct": d[:, 0], **{c: d[:, i + 1] for i, c in enumerate(REF2018_COLS)}}


REF2018_LUMI_PB = 41600.


def scale_2018(ref, lumi_pb, power=1.):
    """2018 limits brought to the luminosity `lumi_pb`: every limit column times (41.6 fb^-1 / L)^power. power 1 =
    background-free search, limit ~ 1/L; power 0.5 = background-dominated, limit ~ 1/sqrt(L). Both are drawn in the
    2018downscaled plots (user 2026-11-12: 1/L in red, 1/sqrt(L) in violet). Returns (table, factor)."""
    if ref is None:
        return None, None
    f = (REF2018_LUMI_PB / lumi_pb) ** power
    return {k: (v if k == "ct" else v * f) for k, v in ref.items()}, f


def pub_dir(a):
    """Published directory. Data background: two sets under <tag>/ (user 2026-11-12): dataUpscaled = the 1% weighted
    to the full 2024 luminosity, 2018 as published; 2018downscaled = 2024 at the luminosity read (--no-scale), 2018
    scaled down to it."""
    if getattr(a, "match_data_lumi", False):
        # data vs QCD MC at the luminosity read (user 2026-11-12); a partial-QCD test goes to its own subdirectory
        test = [f"test_qcd{100. * a.qcd_frac:g}pct"] if a.qcd_frac < 1 else []
        sub = "dataVSqcdUpscaled" if getattr(a, "match_full", False) else "dataVSqcd"
        return os.path.join(a.publish, BKG_LABEL["data"], a.publish_tag, sub, *test, a.case, f"scenario{a.scenario}")
    mode = [] if a.bkg != "data" else ["dataUpscaled" if a.scale else "2018downscaled"]
    return os.path.join(a.publish, BKG_LABEL[a.bkg], a.publish_tag, *mode, a.case, f"scenario{a.scenario}")


def mode_tag(a):
    """File/work-area tag of the normalisation mode: '' (full luminosity), '_unscaled' (--no-scale), '_dataLumi'
    (QCD MC at the luminosity of the data read, framework-MC normalisation, --match-data-lumi; + '_qcd10pct' for a
    partial-QCD test)."""
    if getattr(a, "match_data_lumi", False):
        return ("_fullLumi_fwMC" if getattr(a, "match_full", False) else "_dataLumi_fwMC") + (f"_qcd{100. * a.qcd_frac:g}pct" if a.qcd_frac < 1 else "")
    return "" if a.scale else "_unscaled"


def wp_tag(eff):
    """1e-4 -> 'WP1e-4' (file suffix of a fixed background-efficiency working point)."""
    m, e = f"{eff:.0e}".split("e")
    return f"WP{m}e{int(e)}"


def point_mass(p):
    """Mass LABEL of the point (0.33, 0.67, ...): names, keys, plot labels, 2018 lookup. Physics: true_mass()."""
    return float(re.search(r"_mA_([0-9p]+)_", p).group(1).replace("p", "."))


# A' masses whose sample label is rounded: the 2024 fragments (production_2024/dqcd-production/python/
# withoutMuonFilter_.../*_cfi.py, "GeneralResonance void 1 0 0 <mass>") generate 1/3, 2/3, 5/6, 4/3, 5/3, 10/3 GeV.
# The generated mass is used for the window, the blinded core, the sidebands and the signal model (user 2026-11-12);
# the law framework uses 0.333 / 0.667 and leaves 1.33 (ProcessGroupNameWrapper.get_mass_point).
GENERATED_MASS = {0.33: 1. / 3, 0.67: 2. / 3, 0.83: 5. / 6, 1.33: 4. / 3, 1.67: 5. / 3, 3.33: 10. / 3}


def true_mass(m):
    return GENERATED_MASS.get(round(float(m), 2), float(m))


def point_ctau(p):
    return float(re.search(r"_ctau_([0-9p]+)$", p).group(1).replace("p", "."))


def point_mpi(p):
    return re.search(r"mpi_([0-9p]+)_", p).group(1).replace("p", ".")


def data_weights(base, data_files, scale):
    """Per-directory weights n_total/n_read from data_dirs.json + the files actually read (Norm trees)."""
    import ROOT
    info = json.load(open(os.path.join(base, "data_dirs.json")))
    dirs = info["dirs"]
    by_dir = {d["dir"]: d for d in dirs}
    n_read = {d["id"]: 0 for d in dirs}
    chain = ROOT.TChain("Norm")
    for f in data_files:
        chain.Add(f)
    for ev in chain:
        for f in str(ev.files).split(";"):
            m = CRAB_DIR_RE.match(f.split("gfe02.grid.hep.ph.ic.ac.uk/")[-1])
            if m and m.group(1) in by_dir:
                n_read[by_dir[m.group(1)]["id"]] += 1
    n_total = sum(d["n_total"] for d in dirs)
    covered = sum(d["n_total"] for d in dirs if n_read[d["id"]] > 0)
    rows, w = [], [1.] * len(dirs)
    for d in dirs:
        nr = n_read[d["id"]]
        if scale and nr > 0:
            w[d["id"]] = d["n_total"] / nr
        rows.append((d["id"], d["dataset"], d["era"], d["n_total"], d["n_1pct"], len(d["files"]), nr, w[d["id"]]))
    lumi_full = info["lumi_full_pb"]
    if scale:
        lumi = lumi_full * covered / n_total
    else:
        lumi = lumi_full * sum(n_read.values()) / n_total
    missing = [r for r in rows if r[6] < r[5]]
    return {"w": w, "lumi_pb": lumi, "lumi_full_pb": lumi_full, "n_total": n_total, "covered": covered,
            "n_read": sum(n_read.values()), "n_submitted": info["n_submitted"], "rows": rows, "missing": missing}


def declare_weights(ROOT, w):
    if not hasattr(ROOT, "L1P_DIRW"):
        ROOT.gInterpreter.Declare("std::vector<double> L1P_DIRW = {" + ", ".join(f"{x:.10g}" for x in w) + "};")


def histos(ROOT, sets, m, bdt, cut):
    """Weighted and raw mass histograms per category (index 1-12) above the BDT cut, summed over `sets` =
    [(files, scale)]: per-event weight = directory weight (data) or puWeight (MC), times the set's scale
    (1 for data and signal, xs * lumi / sumw for a QCD pT bin)."""
    m = true_mass(m)
    ROOT.TH1.AddDirectory(False)
    hw = [ROOT.TH1D(f"hw{c}", "", 50, 0.95 * m, 1.05 * m) for c in range(1, 13)]
    hr = [ROOT.TH1D(f"hr{c}", "", 50, 0.95 * m, 1.05 * m) for c in range(1, 13)]
    for h in hw + hr:
        h.Sumw2()
    for files, scale in sets:
        df = (ROOT.RDataFrame("Events", files).Filter(f"{bdt} > {cut}")
              .Define("w", "dirid >= 0 ? L1P_DIRW[dirid] : (double) weight"))
        tw = [df.Filter(f"cat == {c}").Histo1D((f"tw{c}", "", 50, 0.95 * m, 1.05 * m), "mass", "w") for c in range(1, 13)]
        tr = [df.Filter(f"cat == {c}").Histo1D((f"tr{c}", "", 50, 0.95 * m, 1.05 * m), "mass") for c in range(1, 13)]
        for h, t in zip(hw, tw):
            h.Add(t.GetValue(), scale)
        for h, t in zip(hr, tr):
            h.Add(t.GetValue())
    return hw, hr


def qcd_sets(ROOT, base, lumi_pb, frac=1.):
    """[(files, xs * lumi / sumw)] of the 12 QCD pT bins found under `base` (+ a report per bin). frac < 1: only
    every round(1/frac)-th output part of each bin (sumw from the same parts, so the normalisation stays right)."""
    sets, rows = [], []
    for ds, xs in QCD_XS.items():
        files = sorted(glob.glob(os.path.join(base, ds, "part_*.root")))
        if frac < 1:
            files = files[::max(1, int(round(1. / frac)))]
        if not files:
            rows.append((ds, 0, 0., 0., 0.)); continue
        sumw = sumw_all(ROOT, files)
        ne = nonempty(ROOT, files)
        nsel = ROOT.RDataFrame("Events", ne).Count().GetValue() if ne else 0
        scale = xs * lumi_pb / sumw if sumw > 0 else 0.
        if ne:
            sets.append((ne, scale))
        rows.append((ds, len(files), sumw, nsel, scale))
    return sets, rows


def qcd_tight_over_loose(ROOT, sets, bdt, cuts):
    """Inclusive tight/loose ratio of the QCD MC per BDT cut (FitDQCD.get_additional_scaling: integral of the tight
    over the loose region, mass 0-22 GeV): {repr(cut): {"ratio", "n_tight_raw", "n_loose_raw", "sumw_loose"}}."""
    booked = []
    for files, scale in sets:
        df = ROOT.RDataFrame("Events", files).Filter(f"{bdt} > {LOOSE_BDT} && mass > 0 && mass < 22")
        booked.append((scale, df.Sum("weight"), df.Count(),
                       [(df.Filter(f"{bdt} > {c!r}").Sum("weight"), df.Filter(f"{bdt} > {c!r}").Count()) for c in cuts]))
    loose = sum(sc * sw.GetValue() for sc, sw, _, _ in booked)
    n_loose = sum(n.GetValue() for _, _, n, _ in booked)
    out = {}
    for i, c in enumerate(cuts):
        tight = sum(sc * t[i][0].GetValue() for sc, _, _, t in booked)
        out[repr(c)] = {"ratio": tight / loose if loose > 0 else 0., "sumw_loose": loose,
                        "n_tight_raw": int(sum(t[i][1].GetValue() for _, _, _, t in booked)), "n_loose_raw": int(n_loose)}
    return out


# BDT threshold modes (user 2026-11-18): which background events define a working point. The suffix ends every
# output file name; per mass window = v2, the two inclusive modes = v3 / v4 (--publish-tag).
THRESHOLD = {"perMassWindow": "_perMassWindowThreshold",              # sidebands of the window of each mass hypothesis
             "inclusiveMassWindow": "_InclusiveMassWindowThreshold",  # sidebands of all windows of the scenario together
             "inclusiveFullRange": "_InclusiveFullRangeThreshold"}    # mass 0-22 GeV minus the +-2 HWHM cores
ALL_MASSES = [0.33, 0.4, 0.67, 1.0, 1.33]     # mass hypotheses whose cores are blinded in the full-range region
FILE_SUFFIX = ""                               # set in main() from --threshold


def F(name):
    """File name (no extension) with the threshold-mode suffix at its very end."""
    return name + FILE_SUFFIX


def data_stem(a):
    """Stem of the stored data result of the same working point: --no-scale, or the scaled one for --match-data-full."""
    return (f"limits_{BKG_LABEL['data']}{'' if getattr(a, 'match_full', False) else '_unscaled'}_sc{a.scenario}_{a.case}"
            + ("_bestBDT" if a.scan_bdt else "") + (f"_{wp_tag(a.wp_eff)}" if a.wp_eff else ""))


def sumw_all(ROOT, files):
    return ROOT.RDataFrame("Norm", files).Sum("sumw_raw").GetValue()


def nonempty(ROOT, files):
    """Files whose Events tree holds entries: Snapshot writes no branches when nothing was selected, and such a
    file at the head of a TChain hides every column. Norm trees are always there (use the full list for sumw)."""
    out = []
    for f in files:
        t = ROOT.TFile.Open(f)
        tr = t.Get("Events") if t and not t.IsZombie() else None
        if tr and tr.GetEntries() > 0:
            out.append(f)
        if t:
            t.Close()
    return out


def build_category(ROOT, wdir, cat, m, hdata, hraw, hsig, sig_rate, hshape=None, hshape_raw=None):
    """Workspace + datacard for one category, exactly in the framework's data mode. With hshape/hshape_raw
    (QCD MC mode) the envelope is fitted to that loose-region spectrum over the full window instead of the
    sidebands of hdata, and the "enough events" decision uses its raw count."""
    m = true_mass(m)
    sigma = 0.01 * m
    lo, hi = m - 5 * sigma, m + 5 * sigma
    blo, bhi = m - 2 * sigma, m + 2 * sigma
    x = ROOT.RooRealVar("x", "x", lo, hi)
    x.setRange("loSB", lo, blo); x.setRange("hiSB", bhi, hi); x.setRange("full", lo, hi)
    data = ROOT.RooDataHist("data_obs", "data_obs", ROOT.RooArgList(x), hdata)

    # sideband count, as Fit's blinded "integral" (bins with centres outside the blind window); the
    # "enough events to fit a shape" decision uses the RAW event count, the yields the weighted one
    n_full = hdata.Integral()
    n_raw = hraw.Integral()
    n_sb = sum(hdata.GetBinContent(i) for i in range(1, hdata.GetNbinsX() + 1)
               if not (blo <= hdata.GetBinCenter(i) <= bhi))
    n_sb_raw = sum(hraw.GetBinContent(i) for i in range(1, hraw.GetNbinsX() + 1)
                   if not (blo <= hraw.GetBinCenter(i) <= bhi))

    w = ROOT.RooWorkspace("w", "w")
    keep = []
    info = {"n_full": n_full, "n_full_raw": n_raw, "n_sideband": n_sb, "n_sideband_raw": n_sb_raw,
            "sig_rate": sig_rate,
            "hist": {"edges": [hdata.GetBinLowEdge(i) for i in range(1, hdata.GetNbinsX() + 2)],
                     "w": [hdata.GetBinContent(i) for i in range(1, hdata.GetNbinsX() + 1)],
                     "raw": [hraw.GetBinContent(i) for i in range(1, hraw.GetNbinsX() + 1)]}}
    if hshape is not None:
        shape_data = ROOT.RooDataHist("shape_obs", "shape_obs", ROOT.RooArgList(x), hshape)
        n_shape_raw = hshape_raw.Integral()
        fit_range = "full"
        info.update(n_shape=hshape.Integral(), n_shape_raw=n_shape_raw, shape_region=f"loose (BDT > {LOOSE_BDT})")
    else:
        shape_data, n_shape_raw, fit_range = data, n_sb_raw, "loSB,hiSB"
    bkg_name = f"model_bkg_{cat}"
    if n_shape_raw < MIN_EVENTS_FOR_FITTING:
        bkg = ROOT.RooUniform(bkg_name, bkg_name, ROOT.RooArgSet(x))
        getattr(w, "import")(bkg)
        info["bkg_model"] = "constant"
        envelope = None
    else:
        p0 = ROOT.RooRealVar(f"p0_{cat}", "p0", 0, -5, 5)
        c = ROOT.RooRealVar(f"c_{cat}", "c", 0, -2, 2)
        a0 = ROOT.RooRealVar(f"a0_{cat}", "a0", 1, 0, 2)
        b0 = ROOT.RooRealVar(f"b0_{cat}", "b0", 0, -2, 2)
        funs = [ROOT.RooPolynomial(f"model_polynomial_{cat}", "", x, ROOT.RooArgList(p0)),
                ROOT.RooExponential(f"model_exponential_{cat}", "", x, c),
                ROOT.RooGenericPdf(f"model_powerlaw_{cat}", "@1 * TMath::Power(@0, @2)",
                                   ROOT.RooArgList(x, a0, b0))]
        keep += [p0, c, a0, b0] + funs
        info["bkg_params"] = {}
        for f in funs:
            f.fitTo(shape_data, ROOT.RooFit.Range(fit_range), ROOT.RooFit.SumW2Error(True),
                    ROOT.RooFit.PrintLevel(-1))
        for v in (p0, c, a0, b0):
            info["bkg_params"][v.GetName()] = v.getVal()
            v.setConstant(True)
        envelope = f"pdf_index_{cat}"
        idx = ROOT.RooCategory(envelope, "")
        models = ROOT.RooArgList(*funs)
        multi = ROOT.RooMultiPdf(bkg_name, "", idx, models)
        keep += [idx, models, multi]
        getattr(w, "import")(idx)
        getattr(w, "import")(multi)
        info["bkg_model"] = "envelope"
    norm = ROOT.RooRealVar(bkg_name + "_norm", "Background yield", n_full, 0,
                           3 * n_full if n_full > 0 else 10.)
    getattr(w, "import")(norm)

    # signal: fixed Voigtian; "modelling" width systematic built as law does it (see module docstring)
    mean = ROOT.RooRealVar(f"mean_{cat}", "mean", m)
    gamma = ROOT.RooRealVar(f"gamma_{cat}", "gamma", 0.005)
    sig0 = ROOT.RooRealVar(f"sigma_{cat}", "sigma", 0.0085 * m)
    modelling = ROOT.RooRealVar("modellingsigma", "modellingsigma", 0, -5, 5)
    modelling.setConstant(True)
    sigma_syst = ROOT.RooFormulaVar(f"sigma_syst_{cat}", f"@0*(1+{0.0015 * m}*@1)",
                                    ROOT.RooArgList(sig0, modelling))
    sig = ROOT.RooVoigtian(f"model_sig_{cat}", "", x, mean, gamma, sigma_syst)
    keep += [mean, gamma, sig0, modelling, sigma_syst, sig]
    getattr(w, "import")(sig, ROOT.RooFit.RecycleConflictNodes())
    getattr(w, "import")(data)
    ws_path = os.path.join(wdir, f"ws_{cat}.root")
    w.writeToFile(ws_path)

    card = os.path.join(wdir, f"card_{cat}.txt")
    with open(card, "w") as f:
        f.write(f"""imax 1
jmax 1
kmax *
---------------
shapes sig      {cat} {ws_path} w:model_sig_{cat}
shapes bkg      {cat} {ws_path} w:{bkg_name}
shapes data_obs {cat} {ws_path} w:data_obs
---------------
bin          {cat}
observation  -1
---------------
bin          {cat} {cat}
process      sig bkg
process      0 1
rate         {sig_rate} 1
---------------
modelling param 0.0 1.0
""")
        if envelope:
            f.write(f"{envelope} discrete\n")
        f.write("yieldscale rateParam * sig 0.01\n")
    return card, info


def run_point(args):
    point, a, sig_files, bkg, dw = args
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)
    ROOT.gSystem.Load("libHiggsAnalysisCombinedLimit")
    declare_weights(ROOT, dw)
    m = point_mass(point)
    bdt = "bdtA" if a.scenario == "A" else "bdtB1"
    if getattr(a, "point_cuts", None):     # data vs QCD: the cut of the data result, also for the best-BDT set
        wdir = os.path.join(a.workdir, point, wp_subdir(a)); os.makedirs(wdir, exist_ok=True)
        summ = limit_for_cut(ROOT, point, a, sig_files, bkg, m, bdt, a.point_cuts[point], wdir)
        if a.wp_cuts is not None:
            summ["wp"] = a.wp_cuts[f"{m:g}"]
        return point, summ
    if not a.scan_bdt:
        cut = TIGHT[(a.scenario, a.case)]
        wdir = os.path.join(a.workdir, point)
        if a.wp_cuts is not None:   # data-sideband working point of this mass (--wp-bkg-eff)
            cut = a.wp_cuts[f"{m:g}"]["cut"]
            wdir = os.path.join(a.workdir, point, f"wp_{a.wp_eff:g}")
        os.makedirs(wdir, exist_ok=True)
        summ = limit_for_cut(ROOT, point, a, sig_files, bkg, m, bdt, cut, wdir)
        if a.wp_cuts is not None:
            summ["wp"] = a.wp_cuts[f"{m:g}"]
        return point, summ
    scan = {}
    for cut in a.thresholds:
        wdir = os.path.join(a.workdir, point, f"bdt_{cut:g}"); os.makedirs(wdir, exist_ok=True)
        scan[f"{cut:g}"] = limit_for_cut(ROOT, point, a, sig_files, bkg, m, bdt, cut, wdir)
    return point, {"mass": m, "ctau": point_ctau(point), "mpi": point_mpi(point), "scan": scan}


def limit_for_cut(ROOT, point, a, sig_files, bkg, m, bdt, cut, wdir):
    """Datacards, combine and summary of one signal point at one BDT threshold. `bkg` = [(files, scale)]."""
    sig_all, sig_ne = sig_files          # all parts (Norm trees) / parts with selected events
    fw = getattr(a, "qcd_ratio", None)
    if not fw:
        hd, hd_raw = histos(ROOT, bkg, m, bdt, cut)
    hs, _ = histos(ROOT, [(sig_ne, 1.)] if sig_ne else [], m, bdt, cut)
    if a.bkg == "qcd":   # shape from the loose region (see module docstring)
        hl, hl_raw = histos(ROOT, bkg, m, bdt, LOOSE_BDT)
        if fw:           # framework MC mode: yield = loose spectrum x inclusive tight/loose ratio
            tl = fw[repr(cut)]
            hd = [h.Clone(f"hd{i}") for i, h in enumerate(hl)]
            for h in hd:
                h.Scale(tl["ratio"])
            hd_raw = hl_raw
    else:
        hl, hl_raw = [None] * 12, [None] * 12
    norm = SIGNAL_XS * a.lumi_pb / sumw_all(ROOT, sig_all)
    cards, summary = [], {"mass": m, "mass_true": true_mass(m), "ctau": point_ctau(point), "mpi": point_mpi(point), "lumi_pb": a.lumi_pb,
                          "cut": cut, "scaled": a.scale, "bkg": a.bkg, "cats": {}}
    if fw:
        summary.update(qcd_norm="loose x inclusive tight/loose", tl=tl)
    for i, cat in enumerate(CATS):
        card, info = build_category(ROOT, wdir, cat, m, hd[i], hd_raw[i], hs[i], hs[i].Integral() * norm,
                                    hl[i], hl_raw[i])
        summary["cats"][cat] = info
        # CombineDatacards.avoid_empty_processes: drop categories with no signal; a background from
        # data is kept even when empty
        if info["sig_rate"] == 0:
            info["dropped"] = "no signal"
            continue
        cards.append(f"{cat}={card}")

    comb = os.path.join(wdir, "card_combined.txt")
    if not cards:    # every category dropped: no limit (infinite); happens for very tight working points
        summary["error"] = "no signal event passes the BDT cut in any category"
        return summary
    sh = lambda cmd: subprocess.run(cmd, shell=True, cwd=wdir, capture_output=True, text=True)
    r = sh(f"combineCards.py {' '.join(cards)} > {comb}")
    r = sh(f"text2workspace.py {comb} -m 125 -o {wdir}/ws_combined.root")
    if r.returncode:
        summary["error"] = "text2workspace: " + r.stderr[-2000:]
        return summary
    # as RunCombineDQCD (+ --cminDefaultMinimizerStrategy 0 as the framework); weak points need r >> 20,
    # beyond combine's default r range, so retry with a wider --rMax when no limit comes out
    lim = {}
    for rmax in (None, 1e4, 1e5, 1e6):
        r = sh(f"combine -M AsymptoticLimits --run blind -m 125 --freezeParameters yieldscale "
               f"--cminDefaultMinimizerStrategy 0 " + (f"--rMax {rmax:g} " if rmax else "")
               + f"-n _{point} {wdir}/ws_combined.root")
        with open(os.path.join(wdir, "combine.log"), "w") as f:
            f.write(r.stdout + r.stderr)
        for line in r.stdout.splitlines():
            mm = re.match(r"Expected\s+([0-9.]+)%: r < ([0-9.eE+-]+)", line.strip())
            if mm:
                lim[mm.group(1)] = float(mm.group(2))
        if len(lim) == 5:
            summary["rmax"] = rmax
            break
    summary["r_limits"] = lim
    summary["br_limits"] = {k: v * 1e-4 for k, v in lim.items()}   # yieldscale 0.01 x xs BR 1%
    if not lim:
        summary["error"] = "combine: " + (r.stdout + r.stderr)[-2000:]
    return summary


def sideband_working_points(ROOT, sets, masses, bdt, eff, w, fixed=None, mode="perMassWindow", region_masses=None):
    """Per mass: BDT threshold with background efficiency `eff` in the sidebands of the +-5 HWHM window
    (outside +-2 HWHM), all categories, from no-BDT-cut trees `sets` = [(files, scale)] (data: directory
    weights 1%->100%; QCD MC: puWeight x xs scale). Weighted quantile; raw counts kept.
    With `fixed` = {mass key: cut} the cut is given (best-BDT threshold) and only the sideband counts are filled.
    mode (THRESHOLD): perMassWindow = one cut per mass from its own sidebands; inclusiveMassWindow = ONE cut from the
    sidebands of all windows of `region_masses` together; inclusiveFullRange = ONE cut from mass 0-22 GeV minus the
    +-2 HWHM cores of ALL_MASSES. In the inclusive modes every mass key gets the same entry."""
    import numpy as np
    declare_weights(ROOT, w)
    dfs = [(ROOT.RDataFrame("Events", files).Define("w", "dirid >= 0 ? L1P_DIRW[dirid] : (double) weight"), scale)
           for files, scale in sets]
    out = {}
    win = lambda m, k: f"(mass > {true_mass(m) * (1 - 0.01 * k)} && mass < {true_mass(m) * (1 + 0.01 * k)})"
    if mode == "inclusiveMassWindow":
        rm = sorted(set(region_masses or masses))
        regions = [("all", " || ".join(f"({win(m, 5)} && !{win(m, 2)})" for m in rm),
                    "sidebands of all mass windows (" + ", ".join(f"{m:g}" for m in rm) + " GeV)")]
    elif mode == "inclusiveFullRange":
        regions = [("all", "mass > 0 && mass < 22 && " + " && ".join(f"!{win(m, 2)}" for m in ALL_MASSES),
                    "mass 0-22 GeV minus the cores")]
    else:
        regions = [(m, f"{win(m, 5)} && !{win(m, 2)}", "") for m in sorted(set(masses))]
    for m, sb, region in regions:
        b, ww = [], []
        for df, scale in dfs:
            cols = df.Filter(sb).AsNumpy([bdt, "w"])
            b.append(cols[bdt].astype(float)); ww.append(cols["w"].astype(float) * scale)
        b, ww = np.concatenate(b), np.concatenate(ww)
        n_raw = len(b)
        info = {"target_eff": eff, "n_sideband_raw": int(n_raw), "n_sideband_weighted": float(ww.sum()),
                "threshold_mode": mode, "region": region}
        if n_raw == 0:
            info.update(cut=float("nan"), n_above_raw=0, eff_raw=float("nan"), note="no sideband events")
        elif fixed is not None:
            cut = float(fixed[f"{m:g}"])
            n_above = int((b > cut).sum())
            info.update(cut=cut, n_above_raw=n_above, eff_raw=n_above / n_raw, note="fixed cut",
                        target_eff=float(ww[b > cut].sum() / ww.sum()))
        else:
            order = np.argsort(b)[::-1]                      # descending BDT
            cum = np.cumsum(ww[order]) / ww.sum()           # weighted fraction above (and including) each value
            k = int(np.searchsorted(cum, eff, side="right"))  # first index where the fraction exceeds eff
            # threshold just below the k-th highest value: fraction above it <= eff (k = 0 -> above the maximum)
            cut = float(b[order[k - 1]]) if k > 0 else float(np.nextafter(b.max(), 1.0))
            n_above = int((b > cut).sum())
            info.update(cut=cut, n_above_raw=n_above, eff_raw=n_above / n_raw,
                        note="" if n_raw * eff >= 10 else f"low statistics: {n_raw:.0f} x {eff:g} < 10 events")
        for key in ([m] if mode == "perMassWindow" else sorted(set(masses))):
            out[f"{key:g}"] = dict(info)
        print(f"  WP {'m=%g' % m if mode == 'perMassWindow' else region}: {n_raw} raw events, BDT > {info['cut']:.5f} "
              f"({info['n_above_raw']} above, raw eff {info['eff_raw']:.2g}) {info['note']}")
    return out


def choose_thresholds(results, thresholds):
    """Per (mpi, mass): the threshold with the smallest geometric mean of the median expected limit over the
    ctau points (all points must have a limit at that threshold). -> {(mpi, mass): (cut_key, scores)}"""
    by_mass = {}
    for p, s in results.items():
        by_mass.setdefault((s["mpi"], s["mass"]), []).append(s)
    chosen = {}
    for key, rows in by_mass.items():
        score = {}
        for cut in thresholds:
            k = f"{cut:g}"
            meds = [(r["scan"].get(k) or {}).get("br_limits", {}).get("50.0") for r in rows]
            if all(x is not None and x > 0 for x in meds):
                score[k] = math.exp(sum(math.log(x) for x in meds) / len(meds))
        chosen[key] = (min(score, key=score.get) if score else None, score)
    return chosen


def scan_plots(results, chosen, a, dirs, stem):
    """Median expected limit vs BDT threshold per mass hypothesis, one line per ctau (AN Fig. 45-47)."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    import mplhep as hep
    hep.style.use("CMS")
    by_mass = {}
    for p, s in results.items():
        by_mass.setdefault((s["mpi"], s["mass"]), []).append(s)
    lumi_fb = a.lumi_pb / 1000.
    for (mpi, m), rows in sorted(by_mass.items(), key=lambda kv: (float(kv[0][0]), kv[0][1])):
        fig, ax = plt.subplots(figsize=(10, 8))
        for s in sorted(rows, key=lambda r: r["ctau"]):
            xs, ys = [], []
            for k, r in s["scan"].items():
                med = r.get("br_limits", {}).get("50.0")
                if med:
                    xs.append(float(k)); ys.append(med)
            ax.plot(xs, ys, "o-", label=rf"$c\tau$ = {s['ctau']:g} mm")
        best = chosen.get((mpi, m), (None, {}))[0]
        if best:
            ax.axvline(float(best), color="k", ls="--", label=f"chosen BDT > {best}")
        ax.set_yscale("log")
        ax.set_xlabel("BDT threshold"); ax.set_ylabel(r"Median expected limit on $\mathit{B}(H\to\psi\overline{\psi})$")
        ax.text(0.05, 0.95, f"Scenario {a.scenario}, {a.case}\n{dataset_text(a)}\n" + rf"$m_{{\pi}}$={mpi} GeV, $m_{{A'}}$={m} GeV",
                transform=ax.transAxes, fontsize=16, va="top")
        cms_label(ax, a)
        ax.legend(loc="lower left", fontsize=12)
        save(fig, dirs["wp"], f"{stem}_mpi_{mpi}_mA_{m}")
        plt.close(fig)


def out_dirs(pub, sub):
    """Layout (user 2026-11-06): overview plots at the top level, the individual mass-point PDFs and the tables of a
    working point in <pub>/<sub>/ (WP1e-4, bestBDT, ...), every PNG in a png/ subdirectory of where its PDF is."""
    d = {"top": pub, "top_png": os.path.join(pub, "png"), "wp": os.path.join(pub, sub),
         "wp_png": os.path.join(pub, sub, "png")}
    for v in d.values():
        os.makedirs(v, exist_ok=True)
    return d


def save(fig, directory, stem):
    fig.savefig(os.path.join(directory, F(stem) + ".pdf"))
    fig.savefig(os.path.join(directory, "png", F(stem) + ".png"))


def bkg_fit_pages(results, a, path):
    """One page per (signal point, category): the background spectrum entering the datacard (tight region,
    weighted), the +-2 HWHM core shaded, and the fitted envelope functions (each normalised to the sideband yield)
    or the flat model; text with the window / core / sideband counts (weighted and raw). Data: the core points are
    NEVER drawn, whatever the fraction of the dataset (user 2026-11-06); QCD MC is drawn completely."""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import mplhep as hep
    hep.style.use("CMS")
    show_core = a.bkg != "data"
    order = sorted(results.items(), key=lambda kv: (float(kv[1]["mpi"]), kv[1]["mass"], kv[1]["ctau"]))
    with PdfPages(path) as pdf:
        for point, s in order:
            m = true_mass(s["mass"])
            sigma = 0.01 * m
            lo, hi, blo, bhi = m - 5 * sigma, m + 5 * sigma, m - 2 * sigma, m + 2 * sigma
            wp = s.get("wp")
            cut_txt = f"BDT > {s['cut']:.4f}" + (f"  (WP {wp_tag(a.wp_eff)[2:]}: {wp['n_above_raw']} sideband events above)" if wp else "")
            for cat in CATS:
                c = s["cats"][cat]
                h = c.get("hist")
                if not h:
                    continue
                edges = np.array(h["edges"]); w = np.array(h["w"]); raw = np.array(h["raw"])
                centres = 0.5 * (edges[1:] + edges[:-1]); bw = edges[1] - edges[0]
                err = np.sqrt(np.maximum(raw, 1)) * (w / np.maximum(raw, 1))
                sb = ~((centres > blo) & (centres < bhi))
                fig, ax = plt.subplots(figsize=(11, 8.5))
                ax.axvspan(blo, bhi, color="0.80", zorder=0, label="core $\pm2$ HWHM")
                ax.errorbar(centres[sb], w[sb], yerr=err[sb], fmt="ko", ms=5,
                            label=("sidebands\n" + dataset_text(a, short=True).replace(", ", ",\n"))
                                  if a.bkg == "data" else "sidebands, QCD MC")
                if show_core:
                    ax.errorbar(centres[~sb], w[~sb], yerr=err[~sb], fmt="o", ms=5, color="white", ecolor="white",
                                label="core, QCD MC")
                else:
                    ax.plot([], [], " ", label="core: blinded")
                n_core_w, n_core_raw = w[~sb].sum(), raw[~sb].sum()
                x = np.linspace(lo, hi, 400)
                xlo, xhi = x[x < blo], x[x > bhi]
                if c.get("bkg_model") == "envelope":
                    prm = c["bkg_params"]
                    funs = {"pol1": lambda t: 1 + prm[f"p0_{cat}"] * t,
                            "exp": lambda t: np.exp(prm[f"c_{cat}"] * t),
                            "powerlaw": lambda t: np.power(t, prm[f"b0_{cat}"])}
                    for (name, f), col in zip(funs.items(), ("C0", "C1", "C2")):
                        norm = c["n_sideband"] * bw / (np.trapz(f(xlo), xlo) + np.trapz(f(xhi), xhi))
                        ax.plot(x, f(x) * norm, color=col, lw=2, label=name)
                else:
                    nsb_bins = sb.sum()
                    if nsb_bins:
                        ax.plot(x, np.full_like(x, c["n_sideband"] / nsb_bins), color="C3", lw=2,
                                label="flat (< 10 raw sideband events)")
                shown = w if show_core else w[sb]
                ax.set_xlim(lo, hi)
                ax.set_ylim(0, max(1.0, 2.0 * (shown.max() if len(shown) else 0)))
                ax.set_xlabel(r"$m_{\mu\mu}$ [GeV]"); ax.set_ylabel(f"Events / {bw * 1000:.1f} MeV")
                shape = f"\nshape from {c['shape_region']}: {c['n_shape_raw']:.0f} raw" if "shape_region" in c else ""
                ax.text(0.03, 0.96, f"{cat}: {c.get('bkg_model', '')}\n"
                        f"window:    {c['n_full']:9.1f}  ({c['n_full_raw']:.0f} raw)\n"
                        f"core:      {n_core_w:9.1f}  ({n_core_raw:.0f} raw)\n"
                        f"sidebands: {c['n_sideband']:9.1f}  ({c['n_sideband_raw']:.0f} raw)" + shape
                        + ("\n[no signal in this category: dropped]" if c.get("dropped") else ""),
                        transform=ax.transAxes, fontsize=13, va="top", family="monospace",
                        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85))
                ax.legend(loc="upper right", fontsize=11, frameon=False)
                cms_label(ax, a)
                fig.text(0.5, 0.030, f"{point}   |   scenario {a.scenario}, {a.case}   |   {dataset_text(a)}",
                         ha="center", fontsize=12)
                fig.text(0.5, 0.005, f"{cut_txt}   |   fit window m $\pm$ 5 HWHM, 50 bins", ha="center", fontsize=12)
                fig.tight_layout(rect=(0, 0.055, 1, 1))
                pdf.savefig(fig)
                plt.close(fig)


def dataset_text(a, short=False):
    """'0.79% of 2024 data, normalised to 109.95 fb^-1' / 'QCD MC ...' (short: without the sample details)."""
    if a.bkg == "qcd":
        return (f"QCD MC, {a.lumi_pb / 1000.:.2f} fb$^{{-1}}$" if short
                else f"QCD MC (Mu-enriched, $p_T$-binned), {a.lumi_pb / 1000.:.2f} fb$^{{-1}}$")
    frac = f"{100. * a.data_fraction:.2f}% of 2024 data"
    if a.scale:
        return f"{frac}, normalised to {a.lumi_pb / 1000.:.2f} fb$^{{-1}}$"
    return f"{frac}, not scaled ({a.lumi_pb / 1000.:.2f} fb$^{{-1}}$)"


def wp_counts(wp, who=""):
    """'12 of 63520 sideband events' with the region of the threshold mode ('…, all mass windows' / '… events, 0-22 GeV')."""
    mode = wp.get("threshold_mode", "perMassWindow")
    what = {"perMassWindow": "sideband events", "inclusiveMassWindow": "sideband events, all mass windows",
            "inclusiveFullRange": "events, mass 0-22 GeV"}[mode]
    return f"{wp['n_above_raw']} of {wp['n_sideband_raw']} {who}{what}"


def wp_text(a, rows):
    """'WP 1e-4: BDT > 0.9953 (12 of 63520 sideband events above)' of a fixed-efficiency working point (QCD-only
    threshold: '... QCD MC sideband events above', raw MC events; also for its best-BDT threshold), else ''."""
    wp = rows[0].get("wp") if rows else None
    if not wp or not (a.wp_eff or "QCD" in wp.get("source", "")):
        return ""
    name = f"WP {wp_tag(a.wp_eff)[2:]}" if a.wp_eff else "Best BDT threshold"
    who = "QCD MC " if "QCD" in wp.get("source", "") else ""
    return f"\n{name}: BDT > {wp['cut']:.4f} ({wp_counts(wp, who)} above)"


def cms_label(ax, a, header=True, **kw):
    """CMS label + 'lumi (energy)' header; header=False (2024 vs 2018 plots): label only, the luminosity and energy
    of each year are in the legend titles."""
    import mplhep as hep
    if getattr(a, "match_data_lumi", False):   # data vs QCD MC, both at the luminosity read
        hep.cms.label("Preliminary", data=True, rlabel=f"{a.lumi_pb / 1000.:.2f} fb$^{{-1}}$ (13.6 TeV, 2024)", ax=ax, loc=0, **kw)
    elif not header:
        hep.cms.text("Preliminary" if a.bkg == "data" else "Simulation Preliminary", ax=ax, loc=0, **kw)
    elif a.bkg == "qcd":
        hep.cms.label("Preliminary", data=False, rlabel="(13.6 TeV, 2024)", ax=ax, loc=0, **kw)
    else:
        hep.cms.label("Preliminary", data=True, rlabel=f"{a.lumi_pb / 1000.:.2f} fb$^{{-1}}$ (13.6 TeV, 2024)", ax=ax, loc=0, **kw)


def titled_legend(ax, title, handles, fontsize, **kw):
    leg = ax.legend(handles=handles, title=title, fontsize=fontsize, **kw)
    leg.get_title().set_fontsize(fontsize); leg.get_title().set_fontweight("bold")
    leg._legend_box.align = "center"
    leg.get_title().set_multialignment("center")
    ax.add_artist(leg)
    return leg


def draw_limit(ax, rows, a, mpi, m, fontsize=18, ref=None, source=None, ref2=None):
    """Expected limit vs ctau of one mass set. With `source` (AN | HEPData) the 2018 limits `ref` are overlaid in red
    (observed: solid + open squares, median: dashed, 68%: hatched, 95%: dotted edges); the y axis is then extended
    upwards to hold the two titled legends and the text box above the curves."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    x = [s["ctau"] for s in rows]
    g = lambda q: [s["br_limits"][q] for s in rows]
    ax.fill_between(x, g("2.5"), g("97.5"), color="#F5BB54", label="95% expected", zorder=1)
    ax.fill_between(x, g("16.0"), g("84.0"), color="#607641", label="68% expected", zorder=2)
    ax.plot(x, g("50.0"), "k--", label="Median expected", zorder=4)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(rf"$c\tau$ [mm] of ${LL[a.scenario]}$")
    ax.set_ylabel(r"Upper limit on $\mathit{B}(H\to\psi\overline{\psi})$")
    ax.set_xlim(min(x), max(x))
    head = (f"Scenario {a.scenario}, {a.case}\n{dataset_text(a)}\n"
            + rf"$m_{{\pi}}$={mpi} GeV, $m_{{A'}}$={m} GeV")
    if source is None:
        ax.set_ylim(1e-5, 1.)
        if a.scale:
            ax.text(0.05, 0.80, head + wp_text(a, rows), transform=ax.transAxes, fontsize=fontsize * 0.85, va="top")
            ax.legend(loc="upper right", fontsize=fontsize * 16. / 18.)
        else:     # limits at the luminosity read sit in the upper decades: text and legend below them
            ax.text(0.05, 0.05, head + wp_text(a, rows), transform=ax.transAxes, fontsize=fontsize * 0.85, va="bottom")
            ax.legend(loc="lower right", bbox_to_anchor=(0.99, 0.24), fontsize=fontsize * 16. / 18.)
        return
    qcd = source == "QCD"       # data vs QCD MC (same luminosity): blue, no observed curve
    c = "royalblue" if qcd else "crimson"
    c2 = "darkviolet"           # second 2018 table (1/sqrt(L) scaling), hatched the other way
    for r, col, hatch in ((ref, c, "///"), (ref2, c2, "\\\\\\")):
        if r is None:
            continue
        ax.fill_between(r["ct"], r["e68lo"], r["e68hi"], facecolor="none", edgecolor=col, hatch=hatch, lw=0, zorder=3)
        ax.plot(r["ct"], r["e95lo"], ":", color=col, lw=1.4, zorder=3)
        ax.plot(r["ct"], r["e95hi"], ":", color=col, lw=1.4, zorder=3)
        ax.plot(r["ct"], r["exp"], "--", color=col, lw=2, zorder=6)
        if "obs" in r:
            ax.plot(r["ct"], r["obs"], "-", color=col, marker="s", mfc="white", ms=7, lw=2, zorder=7)
    ax.set_ylim(1e-5, 1.)
    from matplotlib.ticker import LogLocator, NullFormatter
    ax.yaxis.set_major_locator(LogLocator(base=10, numticks=20))            # a labelled tick at every decade
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=range(2, 10), numticks=100))   # + the 2..9 ticks in between
    ax.yaxis.set_minor_formatter(NullFormatter())
    fs = fontsize * 0.7
    inv = ax.transAxes.inverted()
    box = lambda artist: artist.get_window_extent().transformed(inv)
    # top row (above every curve): bold "Scenario, masses" + full trigger name on the left, dataset / WP on the right
    bold = ax.text(0.03, 0.965, f"Scenario {a.scenario}, " + rf"$\mathbf{{m_{{\pi}}}}$={mpi} GeV, $\mathbf{{m_{{A'}}}}$={m} GeV"
                   + f"\n{HLT_NAME[a.case]}", transform=ax.transAxes, fontsize=fs, va="top", fontweight="bold")
    if qcd:
        # each background defines its own threshold (user 2026-11-17: the QCD one must not know about data)
        cnt = lambda wp, who: f" ({wp_counts(wp, who)})" if wp else ""
        itext = (("Best BDT threshold" if a.scan_bdt else f"WP {wp_tag(a.wp_eff)[2:]}" if a.wp_eff else "Tight WP")
                 + f"\nData: BDT > {rows[0]['cut']:.4f}" + cnt(rows[0].get("wp"), ""))
        if ref is not None:
            itext += f"\nQCD MC: BDT > {ref['cut']:.4f}" + cnt(ref.get("wp"), "MC ")
    else:
        itext = dataset_text(a) + wp_text(a, rows).replace(" (", "\n(")
    info = ax.text(0.97, 0.965, itext, transform=ax.transAxes,
                   fontsize=fs, va="top", ha="right", multialignment="right")
    h24 = [Line2D([], [], color="k", ls="--", label="Median expected"),
           Patch(color="#607641", label="68% expected"), Patch(color="#F5BB54", label="95% expected")]
    hand = lambda col, hatch: [Line2D([], [], color=col, marker="s", mfc="white", ms=7, label="Observed"),
                               Line2D([], [], color=col, ls="--", label="Median expected"),
                               Patch(facecolor="none", edgecolor=col, hatch=hatch, label="68% expected"),
                               Line2D([], [], color=col, ls=":", label="95% expected")]
    h18 = hand(c, "///")
    if qcd:
        h18 = h18[1:]
    t24 = f"2024\n{a.lumi_pb / 1000.:.2f} fb$^{{-1}}$ (13.6 TeV)"
    if qcd:
        t18 = ""
    elif a.scale:
        t18 = REF2018[source] + "\n" + (REF2018_LUMI if ref is not None else "(not available)")
    else:     # 2018 scaled down to the 2024 luminosity read (plots(): scale_2018)
        t18 = (REF2018[source] + f" $\\times$ {REF2018_LUMI_PB / a.lumi_pb:.1f}  (limit $\\propto 1/L$)\n"
               + (f"41.6 $\\to$ {a.lumi_pb / 1000.:.2f} fb$^{{-1}}$ (13 TeV)" if ref is not None else "(not available)"))
    if qcd:
        t24 = f"Background from data\n{100. * a.data_fraction:.2f}% of 2024 data, " + (
            f"normalised to {a.lumi_pb / 1000.:.2f} fb$^{{-1}}$" if a.scale else "not scaled")
        t18 = "Background from QCD MC\n" + (f"loose $\\times$ tight/loose, {a.lumi_pb / 1000.:.2f} fb$^{{-1}}$"
                                             if ref is not None else "(not available)")
    kw = dict(loc="upper left", labelspacing=0.3, handlelength=1.8, borderaxespad=0., frameon=True, framealpha=0.7,
              edgecolor="none", facecolor="white")
    legs = [(t24, h24), (t18, h18 if ref is not None else [])]
    if ref2 is not None:
        legs.append((REF2018[source] + f" $\\times$ {(REF2018_LUMI_PB / a.lumi_pb) ** 0.5:.1f}  (limit $\\propto 1/\\sqrt{{L}}$)\n"
                     + f"41.6 $\\to$ {a.lumi_pb / 1000.:.2f} fb$^{{-1}}$ (13 TeV)", hand(c2, "\\\\\\")))
    def place(x, y, widths):      # the legends side by side from (x, y), each `widths[i]` wide
        out = []
        for (t, h), w in zip(legs, widths):
            out.append(titled_legend(ax, t, h, fs, bbox_to_anchor=(x, y), **kw)); x += w
        return out
    # second row: the legends side by side, at the horizontal position where the curves underneath are lowest
    tmp = place(0.02, 0.5, [0.3] * len(legs))
    ax.figure.canvas.draw()
    ytop = min(box(bold).y0, box(info).y0) - 0.015
    widths = [box(l).width + 0.01 for l in tmp]
    widths[-1] -= 0.01
    hleg = max(box(l).height for l in tmp)
    for l in tmp:
        l.remove()
    w24, w18 = widths[0], sum(widths[1:])
    (x_lo, x_hi), (y_lo, y_hi) = np.log10(ax.get_xlim()), np.log10(ax.get_ylim())
    refc = lambda col: [(r["ct"], r[k]) for r in (ref, ref2) if r is not None for k in (col, "obs") if k in r]
    curves = [(x, g("97.5"))] + refc("e95hi")
    def height(f_lo, f_hi):      # highest curve (axes fraction) under the span [f_lo, f_hi] of the x axis
        q = x_lo + np.linspace(f_lo, f_hi, 60) * (x_hi - x_lo)
        return max(np.interp(q, np.log10(cx), np.log10(cy)).max() for cx, cy in curves)
    cand = np.arange(0.03, max(0.03, 0.97 - (w24 + w18)) + 1e-6, 0.01)
    best = min(cand, key=lambda f: (round(height(f, f + w24 + w18), 2), abs(f + 0.5 * (w24 + w18) - 0.5)))
    frac = lambda logy: (logy - y_lo) / (y_hi - y_lo)
    lows = [(x, g("2.5"))] + refc("e95lo")
    q = np.linspace(x_lo, x_hi, 200)
    floor = frac(min(np.interp(q, np.log10(cx), np.log10(cy)).min() for cx, cy in lows))     # lowest curve
    htext = max(box(bold).height, box(info).height)
    top_over = frac(height(best, best + w24 + w18)) - (ytop - hleg)      # > 0: the curves reach into the legends
    bot_over = 0.035 + htext + 0.02 + hleg - floor                        # > 0: same for the bottom placement
    if top_over > 0 and bot_over < top_over:
        # the curves reach into the top rows (limits at the luminosity read) and there is more room below them
        # (user 2026-11-17: legends must not sit on the curves): texts on the bottom row, the legends above them
        for t in (bold, info):
            t.set_y(0.035); t.set_va("bottom")
        place(0.5 - 0.5 * (w24 + w18), 0.035 + htext + 0.02 + hleg, widths)
    else:
        place(best, ytop, widths)


def plots(results, a, dirs, stem):
    """Per-mass-set limit plots + overview, each in three versions: plain, and with the 2018 AN / HEPData limits
    overlaid (suffixes of VARIANTS). Mass sets without a 2018 result get no individual comparison plot (they
    still have their page, 2024 only, in the comparison overview). Overview: plain = all mass sets in a grid on one
    page; comparison versions = multipage PDF, one mass set per page."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    import mplhep as hep
    hep.style.use("CMS")
    by_mass = {}
    for p, s in results.items():
        if s.get("br_limits"):
            by_mass.setdefault((s["mpi"], s["mass"]), []).append(s)
    sets = sorted(by_mass.items(), key=lambda kv: (float(kv[0][0]), kv[0][1]))
    for (mpi, m), rows in sets:
        rows.sort(key=lambda s: s["ctau"])
    from matplotlib.backends.backend_pdf import PdfPages
    if getattr(a, "match_data_lumi", False):
        return plots_data_vs_qcd(by_mass, a, dirs, stem, plt, PdfPages)
    for suffix, source in VARIANTS:
        refs = {k: load_2018(source, a.scenario, *k) if source else None for k, _ in sets}
        refs2 = {k: None for k in refs}
        if not a.scale:     # 2018 at the 2024 luminosity read, both scalings
            refs2 = {k: scale_2018(r, a.lumi_pb, 0.5)[0] for k, r in refs.items()}
            refs = {k: scale_2018(r, a.lumi_pb)[0] for k, r in refs.items()}
        # comparison versions: the overview is a multipage PDF, one mass set per page (user 2026-11-11), no overview PNG
        book = PdfPages(os.path.join(dirs["top"], F(f"{stem}_overview{suffix}") + ".pdf")) if source and sets else None
        for (mpi, m), rows in sets:
            # comparison versions: 12x9 canvas, room for the legends above the curves with the 1e-5..1 range
            fig, ax = plt.subplots(figsize=(12, 9) if source else (10, 8))
            if source:
                fig.subplots_adjust(left=0.12, right=0.97, bottom=0.12, top=0.93)
            draw_limit(ax, rows, a, mpi, m, ref=refs[(mpi, m)], source=source, ref2=refs2[(mpi, m)])
            cms_label(ax, a, header=source is None)
            if source and refs[(mpi, m)] is None:
                print(f"  no 2018 {source} limits for scenario {a.scenario} mpi {mpi} mA {m}: no individual comparison plot")
            else:
                save(fig, dirs["wp"], f"{stem}_mpi_{mpi}_mA_{m}{suffix}")
            if book:
                book.savefig(fig)
            plt.close(fig)
        if book:
            book.close()
            stale = os.path.join(dirs["top_png"], F(f"{stem}_overview{suffix}") + ".png")   # grid overview of an earlier version
            if os.path.exists(stale):
                os.remove(stale)
        elif sets:
            # plain version: all mass sets on one page
            ncol = 3 if len(sets) > 4 else 2
            nrow = math.ceil(len(sets) / ncol)
            fig, axes = plt.subplots(nrow, ncol, figsize=(8 * ncol, 6.5 * nrow))
            axes = list(axes.flat) if hasattr(axes, "flat") else [axes]
            for ax, ((mpi, m), rows) in zip(axes, sets):
                draw_limit(ax, rows, a, mpi, m, fontsize=14)
                cms_label(ax, a, fontsize=16)
            for ax in axes[len(sets):]:
                ax.axis("off")
            fig.tight_layout()
            save(fig, dirs["top"], f"{stem}_overview")
            plt.close(fig)


def plots_data_vs_qcd(qcd_by_mass, a, dirs, stem, plt, PdfPages):
    """2024 only (user 2026-11-12): expected limits with the background from the data read (green/yellow bands, from
    the stored --no-scale data result of the same working point) against the background from QCD MC normalised to the
    same luminosity (blue: dashed median, hatched 68%, dotted 95%). One plot per mass set + multipage overview."""
    dpath = os.path.join(a.base, F(data_stem(a)) + ".json")
    if not os.path.exists(dpath):
        sys.exit(f"no data limits {dpath}: run the same working point with --bkg data first")
    d = json.load(open(dpath))
    if abs(d["lumi_pb"] / a.lumi_pb - 1) > 1e-6:
        sys.exit(f"luminosity mismatch: data {d['lumi_pb']} vs QCD {a.lumi_pb} pb^-1")
    data_by_mass = {}
    for p, s in d["points"].items():
        if s.get("br_limits"):
            data_by_mass.setdefault((s["mpi"], s["mass"]), []).append(s)
    sets = sorted(data_by_mass.items(), key=lambda kv: (float(kv[0][0]), kv[0][1]))
    book = PdfPages(os.path.join(dirs["top"], F(f"{stem}_overview_dataVSqcd") + ".pdf")) if sets else None
    q = {"exp": "50.0", "e68lo": "16.0", "e68hi": "84.0", "e95lo": "2.5", "e95hi": "97.5"}
    for (mpi, m), rows in sets:
        rows.sort(key=lambda s: s["ctau"])
        qrows = sorted(qcd_by_mass.get((mpi, m), []), key=lambda s: s["ctau"])
        ref = None
        if qrows:
            ref = {"ct": np.array([s["ctau"] for s in qrows]), "cut": qrows[0]["cut"], "wp": qrows[0].get("wp"),
                   **{k: np.array([s["br_limits"][v] for s in qrows]) for k, v in q.items()}}
        fig, ax = plt.subplots(figsize=(12, 9))
        fig.subplots_adjust(left=0.12, right=0.97, bottom=0.12, top=0.93)
        draw_limit(ax, rows, a, mpi, m, ref=ref, source="QCD")
        cms_label(ax, a)
        save(fig, dirs["wp"], f"{stem}_mpi_{mpi}_mA_{m}_dataVSqcd")
        book.savefig(fig)
        plt.close(fig)
    if book:
        book.close()
    if getattr(a, "match_full", False):
        plots_qcd_vs_2018(qcd_by_mass, a, stem, plt, PdfPages)


def plots_qcd_vs_2018(qcd_by_mass, a, stem, plt, PdfPages, source="HEPData"):
    """--match-data-full (user 2026-11-17): the QCD-MC-background limit at the full 2024 luminosity against the 2018
    limits as published (HEPData, not scaled). Drawn as the 2018-comparison version of the standard plots, in
    <tag>/qcdUpscaledVS2018/<case>/scenario<S>/; one plot per mass set with a 2018 result + multipage overview."""
    import copy
    q = copy.copy(a)
    q.match_data_lumi = q.match_full = False      # draw_limit / cms_label: plain QCD-MC labels, 2018 as published
    q.bkg, q.scale = "qcd", True
    pub = os.path.join(a.publish, BKG_LABEL["data"], a.publish_tag, "qcdUpscaledVS2018", a.case, f"scenario{a.scenario}")
    dirs = out_dirs(pub, wp_subdir(a))
    suffix = f"_compare2018{source}Limits"
    sets = sorted(qcd_by_mass.items(), key=lambda kv: (float(kv[0][0]), kv[0][1]))
    book = PdfPages(os.path.join(dirs["top"], F(f"{stem}_overview{suffix}") + ".pdf")) if sets else None
    for (mpi, m), rows in sets:
        rows = sorted(rows, key=lambda s: s["ctau"])
        ref = load_2018(source, a.scenario, mpi, m)
        fig, ax = plt.subplots(figsize=(12, 9))
        fig.subplots_adjust(left=0.12, right=0.97, bottom=0.12, top=0.93)
        draw_limit(ax, rows, q, mpi, m, ref=ref, source=source)
        cms_label(ax, q, header=False)
        if ref is None:
            print(f"  no 2018 {source} limits for scenario {a.scenario} mpi {mpi} mA {m}: no individual comparison plot")
        else:
            save(fig, dirs["wp"], f"{stem}_mpi_{mpi}_mA_{m}{suffix}")
        book.savefig(fig)
        plt.close(fig)
    if book:
        book.close()
    print("QCD (full luminosity) vs 2018", source, "->", pub)


def stem_name(a):
    return (f"limits_{BKG_LABEL[a.bkg]}{mode_tag(a)}_sc{a.scenario}_{a.case}"
            + ("_bestBDT" if a.scan_bdt else "") + (f"_{wp_tag(a.wp_eff)}" if a.wp_eff else ""))


def wp_subdir(a):
    return wp_tag(a.wp_eff) if a.wp_eff else ("bestBDT" if a.scan_bdt else "tightConfig")


def replot(a, base):
    """Redraw the limit plots (all VARIANTS) from the stored <stem>.json, without touching trees or combine."""
    stem = stem_name(a)
    d = json.load(open(os.path.join(base, F(stem) + ".json")))
    a.lumi_pb = d["lumi_pb"]
    if a.bkg == "data":
        a.data_fraction = d["data"]["n_read"] / d["data"]["n_total"]
    elif a.match_data_lumi:
        a.data_fraction = d["data"]["data_fraction"]
    pub = pub_dir(a)
    plots(d["points"], a, out_dirs(pub, wp_subdir(a)), stem)
    print("replotted", stem, "->", pub)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=list(DATA))
    ap.add_argument("--scenario", required=True, choices=["A", "B1"])
    ap.add_argument("--tag", default="v2")
    ap.add_argument("--bkg", default="data", choices=["data", "qcd"],
                    help="background: 1%% data (sideband envelope) or the Mu-enriched QCD MC (loose-region shape)")
    ap.add_argument("--qcd-tag", default="v2_qcd", help="tag of the QCD MC selection (submit.py --qcd --min-bdt -1)")
    ap.add_argument("--no-scale", action="store_true", help="plain 1%% result (data weights 1, 1%% luminosity)")
    ap.add_argument("--match-data-lumi", action="store_true",
                    help="--bkg qcd only: QCD MC and signal normalised to the luminosity of the data read (the "
                         "--no-scale data luminosity); plots = data (stored --no-scale result) vs QCD, in "
                         "data1pct/<tag>/dataVSqcd/")
    ap.add_argument("--threshold", default="perMassWindow", choices=list(THRESHOLD),
                    help="events defining a --wp-bkg-eff working point: the sidebands of each mass window (default), the "
                         "sidebands of all windows of the scenario together, or mass 0-22 GeV minus the cores (one cut "
                         "per scenario in the last two). The mode suffix ends every output file name.")
    ap.add_argument("--publish-tag", default=None, help="version directory of the published plots (default: --tag)")
    ap.add_argument("--match-data-full", action="store_true",
                    help="--bkg qcd: as --match-data-lumi but at the full 2024 luminosity of the SCALED data result "
                         "(cuts from that stored result); plots = data (scaled) vs QCD in data1pct/<tag>/dataVSqcdUpscaled/ "
                         "and QCD vs 2018 HEPData in data1pct/<tag>/qcdUpscaledVS2018/")
    ap.add_argument("--qcd-frac", type=float, default=1., help="--bkg qcd: use only this fraction of the QCD parts (test)")
    ap.add_argument("--points", default="", help="comma list; default all of config/scenario<S>.yaml")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--publish", default=os.path.expanduser("~/public_html/parking/2024/limits"),
                    help="root of the published results (+ data1pct|qcdMC/<tag>/<case>/scenario<S>)")
    ap.add_argument("--wp-bkg-eff", default=None,
                    help="BDT threshold per mass = this background efficiency in the data sidebands (no-BDT trees "
                         "of --nobdt-tag); 'auto' = AN Table 10 (A 1e-4, B1 1e-5)")
    ap.add_argument("--nobdt-tag", default="v2_nobdt", help="tag of the no-BDT-cut data selection")
    ap.add_argument("--scan-bdt", action="store_true",
                    help="expected limits at every --thresholds value; working point per mass = best median limit")
    ap.add_argument("--bkg-plots", action="store_true",
                    help="also write bkgfits_<stem>.pdf: one page per signal point with the 12 background spectra, "
                         "core/sideband counts and the fitted functions")
    ap.add_argument("--thresholds", default=",".join(f"{t:g}" for t in DEFAULT_THRESHOLDS),
                    help="comma list of BDT thresholds for --scan-bdt (the config tight WP is always added)")
    ap.add_argument("--replot", action="store_true",
                    help="only redraw the limit plots (plain + 2018 AN / HEPData overlays) from the stored json")
    a = ap.parse_args()
    a.scale = not a.no_scale
    global FILE_SUFFIX
    FILE_SUFFIX = THRESHOLD[a.threshold]
    a.publish_tag = a.publish_tag or a.tag
    if a.threshold != "perMassWindow" and not a.wp_bkg_eff:
        sys.exit("--threshold inclusive* needs --wp-bkg-eff (best BDT / config cut exist only per mass window)")
    a.match_full = a.match_data_full
    if a.match_full:
        if a.no_scale or a.qcd_frac < 1:
            sys.exit("--match-data-full is the full-luminosity mode: no --no-scale, no --qcd-frac")
        a.match_data_lumi = True      # same code path (framework-MC normalisation, cuts of the data result)
    if a.match_data_lumi:
        if a.bkg != "qcd":
            sys.exit("--match-data-lumi / --match-data-full need --bkg qcd")
        a.scale = a.match_full
    a.thresholds = sorted(set([float(t) for t in a.thresholds.split(",")] + [TIGHT[(a.scenario, a.case)]])) if a.scan_bdt else []
    a.wp_cuts, a.wp_eff = None, None
    if a.wp_bkg_eff:
        if a.scan_bdt:
            sys.exit("--wp-bkg-eff and --scan-bdt are exclusive")
        a.wp_eff = AN_WP_EFF[a.scenario] if a.wp_bkg_eff == "auto" else float(a.wp_bkg_eff)
    base = os.path.join(os.environ["CMT_STORE"], "Limits1pct", a.tag, a.case)
    a.base = base
    if a.replot:
        return replot(a, base)
    a.workdir = os.path.join(base, "combine" + ("" if a.bkg == "data" else "_" + a.bkg) + mode_tag(a),
                             *([] if a.threshold == "perMassWindow" else [a.threshold]),
                             f"scenario{a.scenario}")
    os.makedirs(a.workdir, exist_ok=True)
    import ROOT
    ROOT.gROOT.SetBatch(True)

    sys.path.insert(0, HERE)
    from submit import signal_points
    points = a.points.split(",") if a.points else signal_points(a.scenario)
    bkg_info = {}
    if a.bkg == "data":
        data_files = sorted(glob.glob(os.path.join(base, DATA[a.case], "part_*.root")))
        dw = data_weights(base, data_files, a.scale)
        a.lumi_pb = dw["lumi_pb"]
        print(f"data: {len(data_files)} output parts, {dw['n_read']}/{dw['n_submitted']} submitted files read "
              f"({dw['n_total']} files in the full dataset, {100. * dw['n_read'] / dw['n_total']:.3f} %); "
              f"{'scaled to' if a.scale else 'unscaled,'} lumi = {a.lumi_pb:.1f} pb^-1")
        if dw["missing"]:
            print(f"WARNING: {len(dw['missing'])} directories have fewer files read than submitted "
                  "(failed/corrupt jobs?); their weights use the files actually read:")
            for r in dw["missing"]:
                print(f"   {r[1]}/{r[2]}: submitted {r[5]}, read {r[6]} of {r[3]} total")
        with open(os.path.join(base, f"data_weights_{a.case}.csv"), "w") as f:
            f.write("id,dataset,era,n_total,n_1pct,n_submitted,n_read,weight\n")
            for r in dw["rows"]:
                f.write(",".join(str(x) for x in r[:7]) + f",{r[7]:.4f}\n")
        a.data_fraction = dw["n_read"] / dw["n_total"]
        bkg = [(nonempty(ROOT, data_files), 1.)]
        dirw = dw["w"]
        bkg_info = {k: v for k, v in dw.items() if k != "w"}
    else:
        a.lumi_pb = LUMI_FULL_PB if a.scale else 0.01 * LUMI_FULL_PB
        if a.match_data_lumi:     # luminosity of the data result: the one read (--no-scale) or the scaled one
            dw = data_weights(base, sorted(glob.glob(os.path.join(base, DATA[a.case], "part_*.root"))), a.match_full)
            a.lumi_pb, a.data_fraction = dw["lumi_pb"], dw["n_read"] / dw["n_total"]
        qbase = os.path.join(os.environ["CMT_STORE"], "Limits1pct", a.qcd_tag, a.case)
        bkg, rows = qcd_sets(ROOT, qbase, a.lumi_pb, a.qcd_frac)
        missing = [r[0] for r in rows if r[1] == 0]
        if missing:
            sys.exit(f"no QCD trees for {missing} under {qbase} (submit.py --qcd --tag {a.qcd_tag} --min-bdt -1)")
        print(f"QCD MC background from {qbase}, lumi = {a.lumi_pb:.1f} pb^-1:")
        print("  dataset        parts    sum(puWeight)_all   selected   xs*lumi/sumw")
        for r in rows:
            print(f"  {r[0]:14s} {r[1]:5d} {r[2]:19.1f} {r[3]:10d} {r[4]:14.4g}")
        dirw = [1.]
        bkg_info = {"qcd": [dict(zip(("dataset", "n_parts", "sumw_raw", "n_selected", "scale"), r)) for r in rows],
                    "qcd_frac": a.qcd_frac, "data_fraction": getattr(a, "data_fraction", None)}
    stem = stem_name(a)

    if a.match_data_lumi:
        # thresholds from QCD MC only (user 2026-11-17: "it shouldn't know anything about data"): the working point
        # of each mass from the xs-weighted QCD sidebands, or (--scan-bdt) a threshold scan on the QCD limits
        bdtv = "bdtA" if a.scenario == "A" else "bdtB1"
        if a.wp_eff:
            print(f"QCD-MC sideband working points (eff {a.wp_eff:g}, xs-weighted):")
            a.wp_cuts = {k: dict(v, source="QCD MC sidebands") for k, v in sideband_working_points(
                ROOT, bkg, [point_mass(p) for p in points], bdtv, a.wp_eff, dirw, mode=a.threshold,
                region_masses=[point_mass(p) for p in signal_points(a.scenario)]).items()}
            wcsv = os.path.join(base, F(f"bdt_wp_{BKG_LABEL[a.bkg]}{mode_tag(a)}_sc{a.scenario}_{a.case}"
                                        f"_{wp_tag(a.wp_eff)}") + ".csv")
            with open(wcsv, "w") as f:
                f.write("mass,target_eff,bdt_cut,n_sideband_raw,n_above_raw,eff_raw,note\n")
                for k, v in sorted(a.wp_cuts.items(), key=lambda kv: float(kv[0])):
                    f.write(f"{k},{v['target_eff']:g},{v['cut']:.6f},{v['n_sideband_raw']},{v['n_above_raw']},"
                            f"{v['eff_raw']:.3g},{v['note']}\n")
            a.point_cuts = {p: a.wp_cuts[f"{point_mass(p):g}"]["cut"] for p in points
                            if a.wp_cuts[f"{point_mass(p):g}"]["cut"] == a.wp_cuts[f"{point_mass(p):g}"]["cut"]}
            points = [p for p in points if p in a.point_cuts]
            cuts = sorted(set(a.point_cuts.values()))
        elif a.scan_bdt:
            cuts = list(a.thresholds)
        else:
            a.point_cuts = {p: TIGHT[(a.scenario, a.case)] for p in points}
            cuts = [TIGHT[(a.scenario, a.case)]]
        a.qcd_ratio = qcd_tight_over_loose(ROOT, bkg, bdtv, cuts)
        bkg_info["tight_over_loose"] = a.qcd_ratio
        print(f"QCD tight/loose ratio (loose = BDT > {LOOSE_BDT}, mass 0-22 GeV, all categories):")
        for c in cuts:
            r = a.qcd_ratio[repr(c)]
            print(f"  BDT > {c:.5f}: ratio {r['ratio']:.4g}  ({r['n_tight_raw']} / {r['n_loose_raw']} raw MC events)")
        print("  background files:", sorted(set(os.path.dirname(f) for fs, _ in bkg for f in fs)))

    if a.wp_eff and not a.match_data_lumi:
        if a.bkg == "data":
            nobdt = sorted(glob.glob(os.path.join(os.environ["CMT_STORE"], "Limits1pct", a.nobdt_tag, a.case,
                                                  DATA[a.case], "part_*.root")))
            if not nobdt:
                sys.exit(f"no no-BDT-cut data trees for tag {a.nobdt_tag} (submit.py --tag {a.nobdt_tag} --no-signal --min-bdt -1)")
            wp_sets = [(nonempty(ROOT, nobdt), 1.)]
            print(f"data-sideband working points (eff {a.wp_eff:g}, {len(nobdt)} no-BDT parts, "
                  f"{'weighted' if a.scale else 'unweighted'}):")
        else:
            wp_sets = bkg     # the QCD trees carry the whole preselected spectrum (--min-bdt -1)
            print(f"QCD-MC sideband working points (eff {a.wp_eff:g}, xs-weighted):")
        a.wp_cuts = sideband_working_points(ROOT, wp_sets, [point_mass(p) for p in points],
                                            "bdtA" if a.scenario == "A" else "bdtB1", a.wp_eff, dirw, mode=a.threshold,
                                            region_masses=[point_mass(p) for p in signal_points(a.scenario)])
        wcsv = os.path.join(base, F(f"bdt_wp_{BKG_LABEL[a.bkg]}{mode_tag(a)}_sc{a.scenario}_{a.case}"
                                    f"_{wp_tag(a.wp_eff)}") + ".csv")
        with open(wcsv, "w") as f:
            f.write("mass,target_eff,bdt_cut,n_sideband_raw,n_above_raw,eff_raw,note\n")
            for k, v in sorted(a.wp_cuts.items(), key=lambda kv: float(kv[0])):
                f.write(f"{k},{v['target_eff']:g},{v['cut']:.6f},{v['n_sideband_raw']},{v['n_above_raw']},"
                        f"{v['eff_raw']:.3g},{v['note']}\n")

    tasks = []
    for p in points:
        sf = sorted(glob.glob(os.path.join(base, p, "part_*.root")))
        if not sf:
            print(f"  {p}: no signal output, skipped"); continue
        tasks.append((p, a, (sf, nonempty(ROOT, sf)), bkg, dirw))
    with Pool(a.jobs) as pool:
        results = dict(pool.map(run_point, tasks))

    pub = pub_dir(a)
    dirs = out_dirs(pub, wp_subdir(a))
    if a.scan_bdt:
        # scan products, then continue with the per-point results at the chosen threshold of each mass
        chosen = choose_thresholds(results, a.thresholds)
        sstem = f"bdt_scan{'' if a.bkg == 'data' else '_' + BKG_LABEL[a.bkg]}{mode_tag(a)}_sc{a.scenario}_{a.case}"
        scsv = os.path.join(base, F(sstem) + ".csv")
        with open(scsv, "w") as f:
            f.write("point,mpi,mass,ctau,bdt_cut,n_bkg_window_raw,n_sideband_raw,exp16,exp50,exp84,chosen\n")
            for p, s in sorted(results.items(), key=lambda kv: (float(kv[1]["mpi"]), kv[1]["mass"], kv[1]["ctau"])):
                best = chosen[(s["mpi"], s["mass"])][0]
                for k, r in s["scan"].items():
                    b = r.get("br_limits", {})
                    nraw = sum(c["n_full_raw"] for c in r["cats"].values())
                    nsb = sum(c["n_sideband_raw"] for c in r["cats"].values())
                    f.write(f"{p},{s['mpi']},{s['mass']},{s['ctau']},{k},{nraw:.0f},{nsb:.0f},"
                            + ",".join(f"{b.get(q, float('nan')):.4g}" for q in ("16.0", "50.0", "84.0"))
                            + f",{int(k == best)}\n")
        json.dump({"thresholds": a.thresholds, "chosen": {f"{k[0]}_{k[1]}": v for k, v in chosen.items()},
                   "points": results}, open(scsv.replace(".csv", ".json"), "w"), indent=1)
        wcsv = os.path.join(base, F(f"bdt_wp{'' if a.bkg == 'data' else '_' + BKG_LABEL[a.bkg]}{mode_tag(a)}_sc{a.scenario}_{a.case}") + ".csv")
        with open(wcsv, "w") as f:
            f.write("mpi,mass,bdt_cut,geomean_exp50," + ",".join(f"exp50_{t:g}" for t in a.thresholds) + "\n")
            for (mpi, m), (best, score) in sorted(chosen.items(), key=lambda kv: (float(kv[0][0]), kv[0][1])):
                f.write(f"{mpi},{m},{best},{score.get(best, float('nan')):.4g},"
                        + ",".join(f"{score.get(f'{t:g}', float('nan')):.4g}" for t in a.thresholds) + "\n")
                print(f"mpi {mpi} mA {m}: BDT > {best}  (geomean median limit {score.get(best, float('nan')):.3g})")
        scan_plots(results, chosen, a, dirs, sstem)
        for fcopy in (scsv, scsv.replace(".csv", ".json"), wcsv):
            shutil.copy(fcopy, dirs["wp"])
        results = {p: dict(s["scan"][chosen[(s["mpi"], s["mass"])][0]], mass=s["mass"], ctau=s["ctau"], mpi=s["mpi"])
                   for p, s in results.items() if chosen[(s["mpi"], s["mass"])][0]}
        if a.match_data_lumi and results:   # QCD sideband counts at the chosen threshold of each mass (plot labels)
            fixed = {f"{s['mass']:g}": s["cut"] for s in results.values()}
            a.wp_cuts = {k: dict(v, source="QCD MC sidebands (best-BDT threshold of the QCD scan)")
                         for k, v in sideband_working_points(ROOT, bkg, [float(k) for k in fixed],
                                                             "bdtA" if a.scenario == "A" else "bdtB1", None, dirw, fixed).items()}
            for s in results.values():
                s["wp"] = a.wp_cuts[f"{s['mass']:g}"]

    out = os.path.join(base, F(stem) + ".json")
    json.dump({"lumi_pb": a.lumi_pb, "scaled": a.scale, "bkg": a.bkg, "data": bkg_info,
               "wp": a.wp_cuts, "points": results}, open(out, "w"), indent=1)
    csv = out.replace(".json", ".csv")
    with open(csv, "w") as f:
        f.write("point,mpi,mass,ctau,lumi_pb,n_bkg_window_raw,n_bkg_window_weighted,exp2p5,exp16,exp50,exp84,exp97p5\n")
        for p, s in sorted(results.items(), key=lambda kv: (float(kv[1]["mpi"]), kv[1]["mass"], kv[1]["ctau"])):
            b = s.get("br_limits", {})
            nraw = sum(c["n_full_raw"] for c in s["cats"].values())
            nw = sum(c["n_full"] for c in s["cats"].values())
            f.write(f"{p},{s['mpi']},{s['mass']},{s['ctau']},{a.lumi_pb:.1f},{nraw:.0f},{nw:.1f},"
                    + ",".join(f"{b.get(q, float('nan')):.4g}" for q in ("2.5", "16.0", "50.0", "84.0", "97.5")) + "\n")
    if a.wp_eff:
        shutil.copy(wcsv, dirs["wp"])
    plots(results, a, dirs, stem)
    if a.bkg_plots:
        bkg_fit_pages(results, a, os.path.join(dirs["wp"], F(f"bkgfits_{stem}") + ".pdf"))
    shutil.copy(csv, dirs["wp"]); shutil.copy(out, dirs["wp"])
    if a.bkg == "data":
        shutil.copy(os.path.join(base, f"data_weights_{a.case}.csv"), pub)
    for p, s in sorted(results.items(), key=lambda kv: (float(kv[1]["mpi"]), kv[1]["mass"], kv[1]["ctau"])):
        b = s.get("br_limits", {})
        print(f"{p:42s} median {b.get('50.0', float('nan')):.3g}  [{b.get('16.0', float('nan')):.3g}, "
              f"{b.get('84.0', float('nan')):.3g}]" + ("  ERROR" if "error" in s else ""))
    print("->", csv, "and", pub)


if __name__ == "__main__":
    main()
