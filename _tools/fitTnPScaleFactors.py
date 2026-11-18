#!/usr/bin/env python3
"""
Tag-and-probe J/psi fitter for the 2024 trigger / muon-ID scale factors.

Reads the pass/fail dimuon-mass histograms written by TriggerSFtnp2024 or IDSFtnp2024
(tasks/triggerscalefactor_2024.py), extracts the J/psi yield in every (displacement, pT) bin
for data and MC, and builds

    eff = N_pass / (N_pass + N_fail),     SF = eff_data / eff_MC

Outputs (in --out-dir, default _tools/output_SF):
    tnp_<task>_<case>_<var>_<method>.root   TH2 eff_data, eff_mc, sf (bin errors = stat. uncertainty)
    tnp_<task>_<case>_<var>_<method>.pdf    one page per bin (data + MC mass spectra with the yield
                                   extraction) and the three 2D maps; copied to public_html
    tnp_<task>_<case>_<var>_<method>.json   correctionlib, same layout as scripts/roottojson_idsf.py
                                   (inputs <var>, pt, ValType = sf/systup/systdown)

Bin edges are NOT duplicated here: they are parsed from the active *_bins lists of the task
class in tasks/triggerscalefactor_2024.py (the selection strings "X > a && X < b"), so the
task file stays the single source of truth.

Yield extraction (--method):
    count  (default) sideband subtraction: signal window 2.91-3.27 GeV (the AN J/psi window,
           applied on bin centres), linear background interpolated from the sidebands.
           Robust at low statistics.
    fit    RooFit simultaneous pass/fail fit: Gaussian J/psi (mean, sigma shared) on an
           exponential background per category. Falls back to "count" if the fit fails.

MC: the task histograms are unweighted. Different QCD pT bins are summed with --mc-weight
ds=w (e.g. xs/N_gen); without it all MC datasets get weight 1 and a warning is printed.

--legacy-binning: same measurement in the bins of the 2018 SF jsons the analysis consumes
(data/*.json). lxy/dxy: the fine pass/fail histograms are summed into the 2018 bins (every 2018
edge is a fine edge; checked). dxysig: the 2018 "alltriggers" bins are not unions of the fine
ones, so the task's dedicated family h_dxysiglegacy_* is read instead (needs a production with
--families dxysiglegacy). Outputs get the suffix _LegacyBinning and the PDFs go to
public_html/parking/2024/SF_check_LegacyBinning.

DoubleMuSFtnp2024 (tasks/triggerscalefactor_2024_doublemu.py, factorised dimuon T&P): fit each
stage with --case DoubleMu_L1 / DoubleMu_HLT as above (bins of TriggerSFtnp2024), then
--combine-stages builds eff = eff(L1) x eff(HLT|L1) for data and MC and SF = ratio from the two
per-stage ROOT outputs (same var/method/tag), written as tnp_DoubleMuSFtnp2024_DoubleMu_<var>_... .

Example:
    python3 _tools/fitTnPScaleFactors.py --task TriggerSFtnp2024 --case Mu10 \\
        --version prod_2024_trigsf --variable lxy \\
        --data-datasets data_2024_singlemu_HalfPerMil --mc-datasets qcd_15to20,qcd_20to30
"""
import argparse
import glob
import json
import math
import os
import re
import shutil
import sys

import numpy as np

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
TASK_FILE = os.path.join(REPO, "tasks", "triggerscalefactor_2024.py")
PUBLIC = os.path.expanduser("~/public_html/parking/2024/SF_checks")
PUBLIC_LEGACY = os.path.expanduser("~/public_html/parking/2024/SF_check_LegacyBinning")
LEGACY_SUFFIX = "LegacyBinning"

# histogram family -> (displacement bin list, pT bin list) used to fill it in the task
FAMILIES = {
    "dxy": ("dxy_bins", "pt_bins"),
    "lxy": ("lxy_bins", "pt_bins"),
    "dxysig": ("dxysig_bins3", "pt_bins3"),
    "dxysiglegacy": ("dxysig_bins_legacy", "pt_bins_legacy"),  # 2018 alltriggers bins (--legacy-binning)
}
VAR_LABEL = {"dxy": "Probe |d$_{xy}$| (cm)", "lxy": "muonSV l$_{xy}$ (cm)",
             "dxysig": "Probe |d$_{xy}$|/$\\sigma$"}
# 2018 SF json whose binning --legacy-binning reproduces for (task, variable); dxysig uses the
# dedicated task family instead (see FAMILIES)
LEGACY_JSON = {("TriggerSFtnp2024", "lxy"): "trigger_sf.json",
               ("TriggerSFtnp2024", "dxy"): "trigger_sf_mudxy.json",
               ("DoubleMuSFtnp2024", "lxy"): "trigger_sf.json",
               ("DoubleMuSFtnp2024", "dxy"): "trigger_sf_mudxy.json",
               ("IDSFtnp2024", "lxy"): "id_sf.json",
               ("IDSFtnp2024", "dxy"): "id_sf.json"}
SIG_WINDOW = (2.91, 3.27)  # GeV, AN-2023-119 J/psi window
# tasks that inherit their bin lists from another class (parse_bins reads that class)
BIN_CLASS = {"DoubleMuSFtnp2024": "TriggerSFtnp2024"}


# ------------------------------------------------------------------------------------------
# bin edges from the task file
# ------------------------------------------------------------------------------------------
def parse_bins(task, list_name):
    """[(lo, hi), ...] from the active list `list_name` of class `task` (''' blocks dropped)."""
    src = open(TASK_FILE).read()
    task = BIN_CLASS.get(task, task)
    i = src.find(f"class {task}(")
    if i < 0:
        sys.exit(f"class {task} not found in {TASK_FILE}")
    j = src.find("\nclass ", i + 10)
    body = re.sub(r"'''.*?'''", "", src[i:j if j > 0 else None], flags=re.S)
    m = re.search(rf"\n\s*{list_name}\s*=\s*\[(.*?)\]", body, re.S)
    if not m:
        sys.exit(f"{list_name} not found (active) in class {task}")
    bins = []
    for cut in re.findall(r'"([^"]+)"', m.group(1)):
        lo = re.search(r">\s*([-\d.eE+]+)", cut)
        hi = re.search(r"<\s*([-\d.eE+]+)", cut)
        if not (lo and hi):
            sys.exit(f"cannot parse bin '{cut}' in {task}.{list_name}")
        bins.append((float(lo.group(1)), float(hi.group(1))))
    return bins


def edges_of(bins, what):
    """Contiguous edges; warn about gaps/overlaps (the TH2 then uses the lower edges)."""
    for (a, b), (c, d) in zip(bins, bins[1:]):
        if not math.isclose(b, c, rel_tol=1e-9, abs_tol=1e-12):
            print(f"WARNING: {what} bins not contiguous: [{a},{b}] then [{c},{d}]")
    return [lo for lo, _ in bins] + [bins[-1][1]]


def legacy_edges(task, variable, fine_vedges, fine_pedges):
    """2018 json edges of (task, variable) expressed on the fine binning: the leading 0 becomes the
    first fine edge and the trailing inf the last one. Every legacy edge must be a fine edge."""
    sys.path.insert(0, TOOLS)
    from compareSF2018vs2024 import load_2018
    s = load_2018(os.path.join(REPO, "data", LEGACY_JSON[(task, variable)]))
    out = []
    for what, e2018, fine in (("displacement", s["x_edges"], fine_vedges), ("pt", s["pt_edges"], fine_pedges)):
        e = [float(x) for x in e2018]
        e[0], e[-1] = float(fine[0]), float(fine[-1])
        # the 2018 overflow [last, inf) may coincide with the end of the fine range (ID: 10 cm)
        if math.isclose(e[-1], e[-2], rel_tol=1e-9, abs_tol=1e-12):
            e.pop()
        if math.isclose(e[0], e[1], rel_tol=1e-9, abs_tol=1e-12):
            e.pop(0)
        for x in e:
            if not any(math.isclose(x, float(f), rel_tol=1e-9, abs_tol=1e-12) for f in fine):
                sys.exit(f"--legacy-binning: 2018 {what} edge {x:g} ({LEGACY_JSON[(task, variable)]}) is not "
                         f"an edge of the fine {task} {variable} bins {[float(f) for f in fine]}")
        out.append(e)
    return out[0], out[1]


def merge_bins(cont, var2, fine, coarse, axis):
    """Sum the fine bins along `axis` (0 displacement, 1 pT) that fall inside each coarse bin.
    Contents and variances are both additive (independent Poisson counts per fine bin)."""
    groups = []
    for lo, hi in zip(coarse, coarse[1:]):
        groups.append([i for i in range(len(fine) - 1)
                       if fine[i] >= lo - 1e-9 * max(abs(lo), 1) and fine[i + 1] <= hi + 1e-9 * max(abs(hi), 1)])
    used = sorted(sum(groups, []))
    if used != list(range(len(fine) - 1)) or any(not g for g in groups):
        sys.exit(f"merge_bins: fine bins {fine} do not tile the coarse bins {coarse} (used {used})")
    c = np.stack([cont.take(g, axis=axis).sum(axis=axis) for g in groups], axis=axis)
    v = np.stack([var2.take(g, axis=axis).sum(axis=axis) for g in groups], axis=axis)
    assert np.isclose(c.sum(), cont.sum()) and np.isclose(v.sum(), var2.sum())
    return c, v


# ------------------------------------------------------------------------------------------
# inputs
# ------------------------------------------------------------------------------------------
def store():
    s = os.environ.get("CMT_STORE")
    if not s:
        sys.exit("CMT_STORE is not set: source setup.sh first")
    return s


def histo_files(task, ds, case, version):
    pat = os.path.join(store(), task, "run3_2024", ds, "cat_base", case, version, "histos_*.root")
    files = sorted(glob.glob(pat))
    if not files:
        sys.exit(f"no inputs: {pat}")
    return files


def load(ROOT, files, weights, nvar, npt, var):
    """Sum pass/fail spectra over files -> (content, var(content)) arrays [nvar, npt, 2, nbins]
    plus the mass binning. var(content) = sum w^2 n (Poisson per file)."""
    cont = var2 = None
    edges = None
    for f, w in zip(files, weights):
        tf = ROOT.TFile.Open(f)
        for iv in range(nvar):
            for ip in range(npt):
                for k, tag in enumerate(("Pass", "Fail")):
                    h = tf.Get(f"h_{var}_{iv}_pT_{ip}_{tag}")
                    if not h:
                        sys.exit(f"missing h_{var}_{iv}_pT_{ip}_{tag} in {f}")
                    n = np.array([h.GetBinContent(b) for b in range(1, h.GetNbinsX() + 1)])
                    if cont is None:
                        nb = h.GetNbinsX()
                        cont = np.zeros((nvar, npt, 2, nb))
                        var2 = np.zeros_like(cont)
                        edges = np.array([h.GetXaxis().GetBinLowEdge(b) for b in range(1, nb + 2)])
                    n = np.clip(n, 0, None)  # Fail = total - pass can round to tiny negatives
                    cont[iv, ip, k] += w * n
                    var2[iv, ip, k] += w * w * n
        tf.Close()
    return cont, var2, edges


# ------------------------------------------------------------------------------------------
# yield extraction
# ------------------------------------------------------------------------------------------
def count_yield(n, v, centres):
    """Sideband subtraction with a straight-line background fitted to the sidebands.
    Returns (signal, var(signal), (p0, p1) of the line in events per mass bin, or None)."""
    sig = (centres >= SIG_WINDOW[0]) & (centres <= SIG_WINDOW[1])
    sb = ~sig
    x, y, vy = centres[sb], n[sb], v[sb]
    p = None
    if y.sum() <= 0:
        bkg, vbkg = 0.0, 0.0
    else:
        # weighted least squares, weights from Poisson variance (>=1 to keep empty bins)
        wls = 1.0 / np.clip(vy, 1.0, None)
        A = np.vstack([np.ones_like(x), x]).T
        cov = np.linalg.pinv(A.T @ (A * wls[:, None]))
        p = cov @ (A.T @ (wls * y))
        As = np.vstack([np.ones(sig.sum()), centres[sig]]).T
        b = As @ p
        bkg = float(np.clip(b, 0, None).sum())
        g = As.sum(axis=0)
        vbkg = float(g @ cov @ g)
    s = float(n[sig].sum()) - bkg
    return s, float(v[sig].sum()) + vbkg, (None if p is None else (float(p[0]), float(p[1])))


def fit_yields(ROOT, np_, vp, nf, vf, edges):
    """Simultaneous RooFit pass/fail fit. Returns (Sp, Sf, var_p, var_f, cov_pf, curves) or None.
    An empty category (no entries) is left out of the fit and gets yield 0 +- 0."""
    lo, hi = float(edges[0]), float(edges[-1])
    tags = [t for t, n in (("pass", np_), ("fail", nf)) if n.sum() > 0]
    if not tags:
        return None
    x = ROOT.RooRealVar("m", "m", lo, hi)
    hists = {}
    for tag, n, v in (("pass", np_, vp), ("fail", nf, vf)):
        if tag not in tags:
            continue
        h = ROOT.TH1D(f"h_{tag}_{id(n)}", "", len(edges) - 1, np.asarray(edges, dtype="d"))
        for b, (c, e2) in enumerate(zip(n, v), start=1):
            h.SetBinContent(b, c)
            h.SetBinError(b, math.sqrt(max(e2, 0)))
        hists[tag] = h
    cat = ROOT.RooCategory("cat", "cat")
    m = ROOT.std.map("std::string, TH1*")()
    for tag in tags:
        cat.defineType(tag)
        m[tag] = hists[tag]
    data = ROOT.RooDataHist("d", "d", ROOT.RooArgList(x), cat, m)

    mean = ROOT.RooRealVar("mean", "mean", 3.097, 3.05, 3.15)
    sigma = ROOT.RooRealVar("sigma", "sigma", 0.03, 0.01, 0.08)
    keep = [x, cat, data, mean, sigma, hists, m]
    sim = ROOT.RooSimultaneous("sim", "sim", cat)
    comps = {}
    for tag, n in (("pass", np_), ("fail", nf)):
        if tag not in tags:
            continue
        tot = max(float(n.sum()), 1.0)
        g = ROOT.RooGaussian(f"g_{tag}", "", x, mean, sigma)
        c = ROOT.RooRealVar(f"c_{tag}", "", -1.0, -20.0, 5.0)
        e = ROOT.RooExponential(f"e_{tag}", "", x, c)
        ns = ROOT.RooRealVar(f"ns_{tag}", "", 0.5 * tot, -0.2 * tot, 2.0 * tot)
        nb = ROOT.RooRealVar(f"nb_{tag}", "", 0.5 * tot, 0.0, 2.0 * tot)
        pdf = ROOT.RooAddPdf(f"pdf_{tag}", "", ROOT.RooArgList(g, e), ROOT.RooArgList(ns, nb))
        sim.addPdf(pdf, tag)
        comps[tag] = (pdf, g, e, ns, nb)
        keep += [g, c, e, ns, nb, pdf]
    r = sim.fitTo(data, ROOT.RooFit.Save(True), ROOT.RooFit.PrintLevel(-1),
                  ROOT.RooFit.Extended(True), ROOT.RooFit.SumW2Error(True))
    if not r or r.status() != 0 or r.covQual() < 2:
        return None
    def yv(tag):
        return (comps[tag][3].getVal(), comps[tag][3].getError() ** 2) if tag in comps else (0.0, 0.0)
    (sp, vsp), (sf, vsf) = yv("pass"), yv("fail")
    cov = 0.0
    if len(comps) == 2:
        nsp, nsf = comps["pass"][3], comps["fail"][3]
        cov = r.correlation(nsp, nsf) * nsp.getError() * nsf.getError()
    # curves for plotting: total and background, in events per mass bin
    grid = np.linspace(lo, hi, 200)
    width = (hi - lo) / (len(edges) - 1)
    curves = {}
    for tag in ("pass", "fail"):
        if tag not in comps:
            curves[tag] = (grid, np.zeros_like(grid), np.zeros_like(grid))
            continue
        pdf, g, e, ns, nb = comps[tag]
        nset = ROOT.RooArgSet(x)
        tot, bkg = [], []
        for xv in grid:
            x.setVal(xv)
            tot.append(pdf.getVal(nset) * (ns.getVal() + nb.getVal()) * width)
            bkg.append(e.getVal(nset) * nb.getVal() * width)
        curves[tag] = (grid, np.array(tot), np.array(bkg))
    return sp, sf, vsp, vsf, cov, curves


def efficiency(sp, sf, vp, vf, cov=0.0):
    tot = sp + sf
    if tot <= 0 or sp < 0:
        return float("nan"), float("nan")
    eff = sp / tot
    var = (sf * sf * vp + sp * sp * vf - 2 * sp * sf * cov) / tot ** 4
    return eff, math.sqrt(max(var, 0.0))


def extract(ROOT, cont, var2, edges, method):
    """-> eff[nvar,npt], err[nvar,npt], details[(iv,ip)] for plotting."""
    nvar, npt = cont.shape[:2]
    centres = 0.5 * (edges[1:] + edges[:-1])
    eff = np.full((nvar, npt), np.nan)
    err = np.full((nvar, npt), np.nan)
    det = {}
    for iv in range(nvar):
        for ip in range(npt):
            n_p, n_f = cont[iv, ip]
            v_p, v_f = var2[iv, ip]
            used, curves = "count", None
            if method == "fit" and n_p.sum() + n_f.sum() >= 20:
                res = fit_yields(ROOT, n_p, v_p, n_f, v_f, edges)
                if res:
                    sp, sf, vp, vf, cov, curves = res
                    used = "fit"
            fit_failed = method == "fit" and used == "count"
            if used == "count":
                sp, vp, lp = count_yield(n_p, v_p, centres)
                sf, vf, lf = count_yield(n_f, v_f, centres)
                cov = 0.0
                curves = {"pass": lp, "fail": lf}  # sideband line parameters
            e, de = efficiency(sp, sf, vp, vf, cov)
            eff[iv, ip], err[iv, ip] = e, de
            det[(iv, ip)] = dict(n=(n_p, n_f), sp=sp, sf=sf, used=used, curves=curves,
                                 fit_failed=fit_failed)
    return eff, err, det


# ------------------------------------------------------------------------------------------
# outputs
# ------------------------------------------------------------------------------------------
def write_root(ROOT, path, vedges, pedges, maps, lumi_fb=None):
    f = ROOT.TFile(path, "RECREATE")
    if lumi_fb is not None:   # effective luminosity of the data drawn, read back by --combine-stages
        ROOT.TParameter("double")("lumi_fb", float(lumi_fb)).Write()
    for name, (val, err) in maps.items():
        h = ROOT.TH2D(name, f"{name};var;pt", len(vedges) - 1, np.asarray(vedges, "d"),
                      len(pedges) - 1, np.asarray(pedges, "d"))
        for iv in range(len(vedges) - 1):
            for ip in range(len(pedges) - 1):
                if np.isfinite(val[iv, ip]):
                    h.SetBinContent(iv + 1, ip + 1, val[iv, ip])
                    h.SetBinError(iv + 1, ip + 1, err[iv, ip])
        h.Write()
    f.Close()


def write_json(path, name, var, vedges, pedges, sf, dsf, overflow_unc):
    """Same layout as scripts/roottojson_idsf.py: first edges -> 0, pT last edge -> inf,
    plus one displacement overflow bin [last, inf) with 1 +- overflow_unc (AN: lxy > 10 cm).
    Bins without a valid SF get 1 +- 1."""
    ve = [0.0] + list(vedges[1:]) + [float("inf")]
    pe = [0.0] + list(pedges[1:-1]) + [float("inf")]
    content = []
    for iv in range(len(ve) - 1):
        row = []
        for ip in range(len(pe) - 1):
            if iv >= sf.shape[0]:
                c, e = 1.0, overflow_unc
            elif np.isfinite(sf[iv, ip]) and np.isfinite(dsf[iv, ip]):
                c, e = float(sf[iv, ip]), float(dsf[iv, ip])
            else:
                c, e = 1.0, 1.0
            row.append({"nodetype": "category", "input": "ValType", "content": [
                {"key": "sf", "value": c}, {"key": "systup", "value": c + e},
                {"key": "systdown", "value": c - e}]})
        content.append({"nodetype": "binning", "input": "pt", "edges": pe,
                        "content": row, "flow": "error"})
    d = {"schema_version": 2, "corrections": [{
        "name": name, "description": f"{name} (tag-and-probe, stat. uncertainty only)",
        "version": 1,
        "inputs": [{"name": var, "type": "real", "description": f"probe/muonSV {var}"},
                   {"name": "pt", "type": "real", "description": "Probe pt"},
                   {"name": "ValType", "type": "string",
                    "description": "sf (nominal), systup/systdown (= sf +- stat. unc.)"}],
        "output": {"name": "weight", "type": "real", "description": "scale factor or variation"},
        "data": {"nodetype": "binning", "input": var, "edges": ve, "content": content,
                 "flow": "error"}}]}
    with open(path, "w") as f:
        json.dump(d, f, indent=2)


def plot(path, args, vbins, pbins, det_d, det_m, maps, lumi_fb, n_read, n_exp, lumi_text=None):
    """lumi_text: replaces the '<lumi> fb-1' part of the data header (used by --combine-stages)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    sys.path.insert(0, TOOLS)
    import cmsstyle as cms
    cms.LUMI_FB = lumi_fb
    cms.set_lumi_files(n_read, n_exp)
    header = cms.lumi_header() if lumi_text is None else lumi_text + " (13.6 TeV, 2024)"
    vlab = VAR_LABEL[args.variable]
    with PdfPages(path) as pdf:
        # 2D maps
        for name, title in (("eff_data", "Data efficiency"), ("eff_mc", "MC efficiency"),
                            ("sf", "Scale factor")):
            if name not in maps:
                continue  # data-only mode
            val, err = maps[name]
            fig, ax = plt.subplots(figsize=(10, 7))
            fig.suptitle(f"{args.task} ({args.case}): {title} vs {args.variable} and probe p$_T$; "
                         f"yield method {args.method}{args._bintag}", fontsize=cms.FS_TITLE - 2)
            # plot on bin-index axes (edges span decades), label with edges; pcolormesh keeps
            # the PDF vector (a masked imshow image does not rasterise reliably)
            im = ax.pcolormesh(np.arange(val.shape[0] + 1) - 0.5, np.arange(val.shape[1] + 1) - 0.5,
                               np.ma.masked_invalid(val.T), cmap="viridis", vmin=0,
                               vmax=1.0 if name != "sf" else 1.5, shading="flat")
            for iv in range(val.shape[0]):
                for ip in range(val.shape[1]):
                    if np.isfinite(val[iv, ip]):
                        ax.text(iv, ip, f"{val[iv, ip]:.2f}\n±{err[iv, ip]:.2f}", ha="center",
                                va="center", fontsize=7, color="w")
            ax.set_xticks(np.arange(len(vbins)))
            ax.set_xticklabels([f"{a:g}-{b:g}" for a, b in vbins], rotation=60, fontsize=8)
            ax.set_yticks(np.arange(len(pbins)))
            ax.set_yticklabels([f"{a:g}-{b:g}" for a, b in pbins])
            ax.set_xlabel(vlab, fontsize=cms.FS_LABEL)
            ax.set_ylabel("Probe p$_T$ (GeV)", fontsize=cms.FS_LABEL)
            fig.colorbar(im, ax=ax, label=title)
            if name == "eff_mc":
                cms.cms_axes(ax, fontsize=cms.FS_AXES)
            else:
                cms.cms_axes(ax, header=header, fontsize=cms.FS_AXES,
                             label=cms.CMS_LABEL_DATA)
            ax.minorticks_off()
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)
        # per-bin mass spectra
        for (iv, ip), dd in (det_d or {}).items():
            dm = det_m.get((iv, ip)) if det_m else None
            if sum(n.sum() for n in dd["n"]) + (sum(n.sum() for n in dm["n"]) if dm else 0) <= 0:
                continue  # empty in data and MC: no page
            rows = ((dd, True), (dm, False)) if det_m else ((dd, True),)
            fig, axs = plt.subplots(len(rows), 2, figsize=(13, 9 if det_m else 5), squeeze=False)
            fig.suptitle(f"{args.task} ({args.case}): {args.variable} {vbins[iv][0]:g}-{vbins[iv][1]:g}, "
                         f"probe p$_T$ {pbins[ip][0]:g}-{pbins[ip][1]:g} GeV; shaded = J/psi window "
                         f"{SIG_WINDOW[0]}-{SIG_WINDOW[1]} GeV{args._bintag}", fontsize=cms.FS_TITLE - 3)
            for row, (d, is_data) in enumerate(rows):
                for col, tag in enumerate(("Pass", "Fail")):
                    ax = axs[row, col]
                    if d is None:
                        ax.set_axis_off()
                        continue
                    n = d["n"][col]
                    e = args._mass_edges
                    c = 0.5 * (e[1:] + e[:-1])
                    ax.errorbar(c, n, yerr=np.sqrt(np.clip(n, 0, None)), fmt="o", color="k", ms=4,
                                label=f"{'Data' if is_data else 'MC'} {tag.lower()}")
                    cur = d["curves"][tag.lower()] if d["curves"] else None
                    if d["used"] == "fit" and cur:
                        g, tot, bkg = cur
                        ax.plot(g, tot, color="tab:red", label="Fit: Gaus + exp")
                        ax.plot(g, bkg, color="tab:blue", ls="--", label="Fit: background")
                    elif cur:
                        # sideband straight line: solid where fitted, dashed where extrapolated
                        p0, p1 = cur
                        lab = "Sideband line fit" + (" (RooFit failed)" if d.get("fit_failed") else "")
                        for lo_, hi_, ls_, lb_ in ((e[0], SIG_WINDOW[0], "-", lab),
                                                   (SIG_WINDOW[0], SIG_WINDOW[1], "--", None),
                                                   (SIG_WINDOW[1], e[-1], "-", None)):
                            gx = np.linspace(lo_, hi_, 20)
                            ax.plot(gx, np.clip(p0 + p1 * gx, 0, None), color="tab:blue", ls=ls_,
                                    label=lb_)
                    ax.axvspan(*SIG_WINDOW, color="gray", alpha=cms.BAND_ALPHA)
                    s = d["sp"] if tag == "Pass" else d["sf"]
                    ax.plot([], [], " ", label=f"J/psi yield {s:.1f} ({d['used']})")
                    ax.set_xlabel("Dimuon mass (GeV)", fontsize=cms.FS_LABEL)
                    ax.set_ylabel("Events", fontsize=cms.FS_LABEL)
                    ax.set_ylim(bottom=0)
                    cms.extend_linear_top(ax)
                    ax.legend(loc="upper right", frameon=False, fontsize=cms.FS_LEGEND - 2)
                    if is_data:
                        cms.cms_axes(ax, header=header, fontsize=cms.FS_AXES - 2,
                                     label=cms.CMS_LABEL_DATA)
                    else:
                        cms.cms_axes(ax, fontsize=cms.FS_AXES - 2)
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def read_lumi(ROOT, path):
    """Effective data luminosity stored by write_root (None for outputs of older versions)."""
    f = ROOT.TFile.Open(path)
    par = f.Get("lumi_fb")
    return float(par.GetVal()) if par else None


def read_maps(ROOT, path):
    """eff_data / eff_mc / sf TH2 of a fitter output -> {name: (val, err)} (empty bins -> nan), edges."""
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        sys.exit(f"cannot open {path}")
    maps, xe, ye = {}, None, None
    for name in ("eff_data", "eff_mc", "sf"):
        h = f.Get(name)
        if not h:
            continue
        nx, ny = h.GetNbinsX(), h.GetNbinsY()
        val = np.array([[h.GetBinContent(i, j) for j in range(1, ny + 1)] for i in range(1, nx + 1)])
        err = np.array([[h.GetBinError(i, j) for j in range(1, ny + 1)] for i in range(1, nx + 1)])
        empty = (val == 0) & (err == 0)
        val[empty], err[empty] = np.nan, np.nan
        maps[name] = (val, err)
        xe = [h.GetXaxis().GetBinLowEdge(i) for i in range(1, nx + 2)]
        ye = [h.GetYaxis().GetBinLowEdge(i) for i in range(1, ny + 2)]
    f.Close()
    return maps, xe, ye


def combine_stages(args, ROOT, pub):
    """eff = eff(L1) x eff(HLT|L1) per bin for data and MC (relative errors in quadrature), SF = ratio."""
    suffix = (f"_{args.tag}" if args.tag else "") + (f"_{LEGACY_SUFFIX}" if args.legacy_binning else "")
    base = f"tnp_{args.task}_DoubleMu_{{}}_{args.variable}_{args.method}{suffix}"
    ins = {st: os.path.join(args.out_dir, base.format(st) + ".root") for st in ("L1", "HLT")}
    for st, path in ins.items():
        if not os.path.exists(path):
            sys.exit(f"--combine-stages: missing stage {st} output {path} (fit it first with --case DoubleMu_{st})")
    m1, xe1, ye1 = read_maps(ROOT, ins["L1"])
    m2, xe2, ye2 = read_maps(ROOT, ins["HLT"])
    if not (np.allclose(xe1, xe2) and np.allclose(ye1, ye2)):
        sys.exit(f"--combine-stages: different binnings: {xe1} x {ye1} vs {xe2} x {ye2}")
    maps = {}
    with np.errstate(divide="ignore", invalid="ignore"):
        for name in ("eff_data", "eff_mc"):
            (a, da), (b, db) = m1[name], m2[name]
            v = a * b
            maps[name] = (v, np.abs(v) * np.sqrt((da / a) ** 2 + (db / b) ** 2))
        (ed, ded), (em, dem) = maps["eff_data"], maps["eff_mc"]
        sf = ed / em
        maps["sf"] = (sf, np.abs(sf) * np.sqrt((ded / ed) ** 2 + (dem / em) ** 2))
    bad = ~np.isfinite(sf)
    print(f"combined {os.path.basename(ins['L1'])} x {os.path.basename(ins['HLT'])}: bins {sf.size}, "
          f"valid SF {int((~bad).sum())}, set to 1+-1 in the json: {int(bad.sum())}")
    vedges, pedges = [float(x) for x in xe1], [float(y) for y in ye1]
    vbins, pbins = list(zip(vedges, vedges[1:])), list(zip(pedges, pedges[1:]))
    os.makedirs(args.out_dir, exist_ok=True)
    args.case = "DoubleMu"
    args._bintag = " [2018 legacy binning]" if args.legacy_binning else ""
    args._bintag += "\neff = eff(L1) x eff(HLT|L1)"
    lumis = [float(x) for x in args.stage_lumi_fb.split(",")] if args.stage_lumi_fb else \
        [read_lumi(ROOT, ins[st]) for st in ("L1", "HLT")]
    lumi_text = (f"{lumis[0]:.3g} (L1) + {lumis[1]:.3g} (HLT) fb$^{{-1}}$" if None not in lumis
                 else "L1 x HLT stages")
    stem = os.path.join(args.out_dir, f"tnp_{args.task}_DoubleMu_{args.variable}_{args.method}{suffix}")
    write_root(ROOT, stem + ".root", vedges, pedges, maps)
    name = args.json_name or (f"trigger_DoubleMu_{args.variable}_pt_TnP_2024"
                              + (f"_{LEGACY_SUFFIX}" if args.legacy_binning else ""))
    write_json(stem + ".json", name, args.variable, vedges, pedges, maps["sf"][0], maps["sf"][1], args.overflow_unc)
    plot(stem + ".pdf", args, vbins, pbins, None, None, maps, 0., 1, 1, lumi_text=lumi_text)
    print("written:", stem + ".{root,json,pdf}")
    if not args.no_publish:
        os.makedirs(pub, exist_ok=True)
        shutil.copy(stem + ".pdf", pub)
        print("copied to", pub)


def print_eff_summary(eff, err, det):
    sp = sum(d["sp"] for d in det.values())
    sf = sum(d["sf"] for d in det.values())
    nfit = sum(d["used"] == "fit" for d in det.values())
    print(f"J/psi yields summed over bins: pass {sp:.1f}, fail {sf:.1f}; "
          f"bins with a valid eff: {int(np.isfinite(eff).sum())}/{eff.size}, fitted: {nfit}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--task", required=True, choices=["TriggerSFtnp2024", "IDSFtnp2024", "DoubleMuSFtnp2024"])
    p.add_argument("--case", default="Mu10")
    p.add_argument("--version", default=None, help="task output version (required unless --combine-stages)")
    p.add_argument("--variable", default="lxy", choices=list(FAMILIES))
    p.add_argument("--data-datasets", default=None, help="comma separated (required unless --combine-stages)")
    p.add_argument("--mc-datasets", default=None,
                   help="comma separated; omit for a data-only run (eff_data only, no SF, no json)")
    p.add_argument("--mc-weight", action="append", default=[], help="ds=w, repeatable")
    p.add_argument("--method", default="count", choices=["count", "fit"])
    p.add_argument("--lumi-fb", type=float, default=109.95 * 5e-4,
                   help="luminosity of the full data datasets (default: HalfPerMil of 109.95/fb)")
    p.add_argument("--expected-data-files", type=int, default=0,
                   help="number of histos_*.root of a complete data production (scales the lumi)")
    p.add_argument("--overflow-unc", type=float, default=0.05,
                   help="uncertainty of the SF=1 overflow displacement bin in the json")
    p.add_argument("--tag", default="", help="suffix of the output names, e.g. the MC used (BuToJpsiK, QCD)")
    p.add_argument("--stage-lumi-fb", default="",
                   help="--combine-stages: 'L1,HLT' effective data luminosities for the header (default: the "
                        "values stored in the two stage outputs)")
    p.add_argument("--combine-stages", action="store_true",
                   help="DoubleMuSFtnp2024: combine the fitted DoubleMu_L1 and DoubleMu_HLT outputs of this "
                        "variable/method/tag into eff = eff(L1) x eff(HLT|L1) and SF (no histograms read)")
    p.add_argument("--legacy-binning", action="store_true",
                   help="measure in the bins of the 2018 SF jsons (data/*.json); outputs get the suffix "
                        f"_{LEGACY_SUFFIX} and the PDF goes to {PUBLIC_LEGACY}")
    p.add_argument("--json-name", default=None, help="correction name (default built from task/var)")
    p.add_argument("--out-dir", default=os.path.join(TOOLS, "output_SF"))
    p.add_argument("--no-publish", action="store_true", help="do not copy the PDF to public_html")
    args = p.parse_args()

    pub = PUBLIC_LEGACY if args.legacy_binning else PUBLIC
    sys.argv = sys.argv[:1]  # keep ROOT from parsing our options
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

    if args.combine_stages:
        if args.task != "DoubleMuSFtnp2024":
            sys.exit("--combine-stages is for --task DoubleMuSFtnp2024")
        combine_stages(args, ROOT, pub)
        return
    if not args.data_datasets or not args.version:
        sys.exit("--data-datasets and --version are required")

    # histogram family read from the task output; dxysig in the legacy binning has its own family
    family = "dxysiglegacy" if args.legacy_binning and args.variable == "dxysig" else args.variable
    vname, pname = FAMILIES[family]
    vbins, pbins = parse_bins(args.task, vname), parse_bins(args.task, pname)
    vedges, pedges = edges_of(vbins, vname), edges_of(pbins, pname)
    print(f"{args.task}.{vname}: {len(vbins)} bins, {pname}: {len(pbins)} bins")
    n_v, n_p = len(vbins), len(pbins)  # bins of the histograms on disk
    merge = args.legacy_binning and family == args.variable
    args._bintag = " [2018 legacy binning]" if args.legacy_binning else ""
    if merge:  # fine histograms summed into the 2018 bins after loading
        fine_v, fine_p = vedges, pedges
        vedges, pedges = legacy_edges(args.task, args.variable, fine_v, fine_p)
        vbins, pbins = list(zip(vedges, vedges[1:])), list(zip(pedges, pedges[1:]))
        print(f"legacy binning ({LEGACY_JSON[(args.task, args.variable)]}): {args.variable} edges "
              f"{[float(f'{e:g}') for e in vedges]}, pt edges {[float(f'{e:g}') for e in pedges]}")

    def load_bins(files, weights):
        c, v, me = load(ROOT, files, weights, n_v, n_p, family)
        if merge:
            c, v = merge_bins(c, v, fine_v, vedges, 0)
            c, v = merge_bins(c, v, fine_p, pedges, 1)
        return c, v, me

    wmap = dict(kv.split("=") for kv in args.mc_weight)
    data_files, mc_files, mc_w = [], [], []
    for ds in args.data_datasets.split(","):
        data_files += histo_files(args.task, ds, args.case, args.version)
    mc_ds = args.mc_datasets.split(",") if args.mc_datasets else []
    if len(mc_ds) > 1 and not wmap:
        print("WARNING: several MC datasets summed with weight 1 (pass --mc-weight ds=xs/N_gen)")
    for ds in mc_ds:
        fs = histo_files(args.task, ds, args.case, args.version)
        mc_files += fs
        mc_w += [float(wmap.get(ds, 1.0))] * len(fs)
    print(f"data: {len(data_files)} files, MC: {len(mc_files)} files")

    cd, vd, medges = load_bins(data_files, [1.0] * len(data_files))
    args._mass_edges = medges
    eff_d, err_d, det_d = extract(ROOT, cd, vd, medges, args.method)
    eff_lumi = args.lumi_fb * len(data_files) / (args.expected_data_files or len(data_files))
    if not mc_files:  # data-only: efficiencies and mass pages, no SF / json
        print_eff_summary(eff_d, err_d, det_d)
        os.makedirs(args.out_dir, exist_ok=True)
        stem = os.path.join(args.out_dir, f"tnp_{args.task}_{args.case}_{args.variable}_{args.method}_dataonly")
        stem += f"_{args.tag}" if args.tag else ""
        stem += f"_{LEGACY_SUFFIX}" if args.legacy_binning else ""
        maps = {"eff_data": (eff_d, err_d)}
        write_root(ROOT, stem + ".root", vedges, pedges, maps, lumi_fb=eff_lumi)
        plot(stem + ".pdf", args, vbins, pbins, det_d, None, maps, args.lumi_fb,
             len(data_files), args.expected_data_files or len(data_files))
        print("written:", stem + ".{root,pdf}")
        if not args.no_publish:
            os.makedirs(pub, exist_ok=True)
            shutil.copy(stem + ".pdf", pub)
            print("copied to", pub)
        return

    cm, vm, _ = load_bins(mc_files, mc_w)
    eff_m, err_m, det_m = extract(ROOT, cm, vm, medges, args.method)
    with np.errstate(divide="ignore", invalid="ignore"):
        sf = eff_d / eff_m
        dsf = np.abs(sf) * np.sqrt((err_d / eff_d) ** 2 + (err_m / eff_m) ** 2)
    bad = ~np.isfinite(sf)
    print(f"bins: {sf.size}, with a valid SF: {int((~bad).sum())}, set to 1+-1 in the json: {int(bad.sum())}")

    os.makedirs(args.out_dir, exist_ok=True)
    stem = os.path.join(args.out_dir, f"tnp_{args.task}_{args.case}_{args.variable}_{args.method}")
    stem += f"_{args.tag}" if args.tag else ""
    stem += f"_{LEGACY_SUFFIX}" if args.legacy_binning else ""
    maps = {"eff_data": (eff_d, err_d), "eff_mc": (eff_m, err_m), "sf": (sf, dsf)}
    write_root(ROOT, stem + ".root", vedges, pedges, maps, lumi_fb=eff_lumi)
    name = args.json_name or (f"{'NUM_LooseID' if 'IDSF' in args.task else 'trigger'}_{args.case}_{args.variable}_pt_TnP_2024"
                              + (f"_{LEGACY_SUFFIX}" if args.legacy_binning else ""))
    write_json(stem + ".json", name, args.variable, vedges, pedges, sf, dsf, args.overflow_unc)
    plot(stem + ".pdf", args, vbins, pbins, det_d, det_m, maps, args.lumi_fb,
         len(data_files), args.expected_data_files or len(data_files))
    print("written:", stem + ".{root,json,pdf}")
    if not args.no_publish:
        os.makedirs(pub, exist_ok=True)
        shutil.copy(stem + ".pdf", pub)
        print("copied to", pub)


if __name__ == "__main__":
    main()
