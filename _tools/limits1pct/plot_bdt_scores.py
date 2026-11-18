#!/usr/bin/env python3
"""
BDT score distributions and mass spectra before/after the BDT selection: 2024 data (the ~1% read) vs QCD MC vs
signal, per trigger case and scenario (user 2026-11-13). Inputs = slim trees of select_events.py WITHOUT BDT cut:
  data    $CMT_STORE/Limits1pct/<nobdt-tag>/<case>/data_2024_*_1percent   (submit.py --tag v2_nobdt --no-signal --min-bdt -1)
  signal  $CMT_STORE/Limits1pct/<nobdt-tag>/<case>/scenario<S>_*           (submit.py --tag v2_nobdt --no-data --min-bdt -1)
  QCD MC  $CMT_STORE/Limits1pct/<qcd-tag>/<case>/qcd_*                     (submit.py --tag v2_qcd --qcd ... --min-bdt -1)
All 12 categories summed. Data weights 1 (not scaled), QCD normalised to the luminosity of the data read
(xs * lumi / sum(puWeight)), signal to xs = 52.23 pb x 1% at that luminosity.

Blinding: data inside the +-2 sigma core (sigma = 1% m) of ANY mass hypothesis of the scenario is never filled,
at any BDT stage. QCD and signal are filled everywhere.

Score pages (bdtScores/): unit area; left = score 0-1, right = tail on -log10(1 - score)
  * one page per mass hypothesis: data and QCD in the sidebands of the +-5 sigma window (outside +-2 sigma) = the
    population the working points are defined on; signal ctau points in the full window
  * one inclusive page: mass 0-22 GeV minus every core (data AND QCD) = the population of the QCD tight/loose ratio
Mass pages (massSpectra/): absolute yields at the luminosity read
  * full spectrum 0.2-22 GeV (dN/dm, cores as exact bins) at: no cut, BDT > 0.6, 0.9, 0.99, config tight WP
  * +-5 sigma window per mass hypothesis at: no cut, loose, data WP 1e-3, data WP 1e-4

  plot_bdt_scores.py --case DoubleMu --scenario A [--qcd-frac 0.1] [--replot]
Products: store <tag>/<case>/bdt_scores_sc<S>_<case>.json (histograms), published pdf/png + efficiency csv under
~/public_html/parking/2024/limits/data1pct/<tag>/{bdtScores,massSpectra}/[test_qcd<N>pct/]<case>/scenario<S>/
"""
import argparse, glob, json, math, os, sys
import numpy as np
from matplotlib.ticker import AutoMinorLocator, LogLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_limits as ML
from submit import signal_points

NOCUT, EVAL = -2., -0.5          # score is -1 where the BDT was not evaluated: "no cut" keeps those events
STAGES = [("no BDT cut", NOCUT), (r"BDT evaluated (score $\geq$ 0)", EVAL), ("BDT > 0.6", 0.6), ("BDT > 0.9", 0.9), ("BDT > 0.99", 0.99)]   # + config tight WP
LIN = (50, 0., 1.)
TAIL = (40, 0., 5.)            # t = -log10(1 - score)
MASS_LO, MASS_HI = 0.2, 22.
WPS = ("1e-3", "1e-4", "1e-5")
OVERLAY_WP = {"A": "1e-4", "B1": "1e-5"}        # AN-2023-119 Table 10 working points
SIG_COLORS = ["tab:red", "tab:orange", "tab:purple", "tab:brown", "tab:pink", "tab:olive"]


AXIS_FS, HEAD_FS = 21, 15        # score pages: one size for all axis titles; header
LEGEND_KW = dict(frameon=True, facecolor="white", framealpha=0.5, edgecolor="none")


def tail(x):
    return -math.log10(1. - x)


def window(m, n):
    mt = ML.true_mass(m)
    return mt * (1 - 0.01 * n), mt * (1 + 0.01 * n)


def mass_edges(masses):
    """Logarithmic grid 0.2-22 GeV with the blinded cores as exact bins (grid edges inside or within 1% of a core
    edge dropped)."""
    grid = np.logspace(math.log10(MASS_LO), math.log10(MASS_HI), 111)
    cores = [window(m, 2) for m in masses]
    keep = [e for e in grid if not any(lo * 0.99 < e < hi * 1.01 for lo, hi in cores)]
    return np.array(sorted(keep + [x for c in cores for x in c]))


def get(h):
    n = h.GetNbinsX()
    return [[h.GetBinContent(i) for i in range(1, n + 1)], [h.GetBinError(i) ** 2 for i in range(1, n + 1)]]


def add(tot, h, scale=1.):
    v, e = get(h)
    if tot is None:
        return [[x * scale for x in v], [x * scale * scale for x in e]]
    return [[a + x * scale for a, x in zip(tot[0], v)], [a + x * scale * scale for a, x in zip(tot[1], e)]]


def load_cuts(a, groups):
    """Data working points per mass group: {key: {"1e-3": cut, ..., "best": cut}} from the stored --no-scale data
    limits (v2 store)."""
    base = os.path.join(os.environ["CMT_STORE"], "Limits1pct", a.tag, a.case)
    out = {k: {} for k in groups}
    for wp in WPS:
        p = os.path.join(base, f"limits_data1pct_unscaled_sc{a.scenario}_{a.case}_WP{wp}_perMassWindowThreshold.json")
        if os.path.exists(p):
            d = json.load(open(p))["wp"]
            for k, (mpi, m) in groups.items():
                c = d.get(f"{m:g}", {}).get("cut")
                if c is not None and not math.isnan(c):
                    out[k][wp] = c
    p = os.path.join(base, f"limits_data1pct_unscaled_sc{a.scenario}_{a.case}_bestBDT_perMassWindowThreshold.json")
    if os.path.exists(p):
        for s in json.load(open(p))["points"].values():
            k = f"mpi_{s['mpi']}_mA_{s['mass']:g}"
            if k in out and s.get("cut") is not None:
                out[k]["best"] = s["cut"]
    return out


def fill(a, path):
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.TH1.AddDirectory(False)
    ROOT.TH1.SetDefaultSumw2(True)
    bdt = "bdtA" if a.scenario == "A" else "bdtB1"
    store = os.path.join(os.environ["CMT_STORE"], "Limits1pct")
    nbase = os.path.join(store, a.nobdt_tag, a.case)
    points = signal_points(a.scenario)
    groups = {}
    for p in points:
        groups.setdefault(f"mpi_{ML.point_mpi(p)}_mA_{ML.point_mass(p):g}", (ML.point_mpi(p), ML.point_mass(p)))
    masses = sorted({m for _, m in groups.values()})
    cuts = load_cuts(a, groups)
    tight = ML.TIGHT[(a.scenario, a.case)]
    stages = STAGES + [(f"BDT > {tight:g} (tight WP)", tight)]
    edges = mass_edges(masses)
    core = " || ".join(f"(mass > {lo!r} && mass < {hi!r})" for lo, hi in (window(m, 2) for m in masses))
    print("blinded cores (data never filled):", core)

    data_files = sorted(glob.glob(os.path.join(nbase, ML.DATA[a.case], "part_*.root")))
    dw = ML.data_weights(nbase, data_files, False)
    lumi = dw["lumi_pb"]
    print(f"data: {len(data_files)} parts, {dw['n_read']} files read of {dw['n_total']} "
          f"({100. * dw['n_read'] / dw['n_total']:.3f} %), lumi {lumi:.1f} pb^-1")
    # Inclusive data working point (user 2026-11-13: first mass page "at the same working point" as the per-mass
    # pages): threshold above which the fraction OVERLAY_WP (1e-4 scenario A, 1e-5 B1) of the data remains, all
    # masses 0-22 GeV with the cores removed, all categories, events without score included in the denominator.
    wp = OVERLAY_WP[a.scenario]
    dinc = ROOT.RDataFrame("Events", ML.nonempty(ROOT, data_files)).Filter(f"!({core}) && mass > 0 && mass < {MASS_HI}")
    n_inc, top = dinc.Count(), dinc.Filter(f"{bdt} > 0.9").Take["float"](bdt)
    top = np.sort(np.array(list(top.GetValue()), dtype="float64"))[::-1]
    k_inc = int(float(wp) * n_inc.GetValue())
    incl_wp = None
    if 0 < k_inc < len(top):
        incl_wp = float(top[k_inc])            # exactly k_inc events lie above it (up to ties)
        stages = stages + [(f"BDT > {incl_wp:.4f} (data WP {wp}, all masses)", incl_wp)]
        print(f"inclusive data WP {wp}: BDT > {incl_wp:.6f} ({k_inc} of {n_inc.GetValue()} events above)")
    else:
        print(f"WARNING: no inclusive data WP {wp} ({k_inc} events needed, {len(top)} above 0.9)")
    qsets, rows = ML.qcd_sets(ROOT, os.path.join(store, a.qcd_tag, a.case), lumi, a.qcd_frac)
    samples = {"data": [(ML.nonempty(ROOT, data_files), 1., True)],
               "qcd": [(f, s, False) for f, s in qsets]}
    sig_norm = {}
    for p in points:
        files = sorted(glob.glob(os.path.join(nbase, p, "part_*.root")))
        if not files:
            print("WARNING: no no-BDT signal trees for", p); continue
        sumw = ML.sumw_all(ROOT, files)
        ne = ML.nonempty(ROOT, files)
        if ne and sumw > 0:
            samples[p] = [(ne, ML.SIGNAL_XS * lumi / sumw, False)]
            sig_norm[p] = {"sumw_all": sumw, "n_parts": len(files)}

    H, E = {}, {}      # H[name][sample] = [values, variances];  E[group][sample][cut label] = [sumw, n_raw]

    def model(name, bins):
        if isinstance(bins, tuple):
            return (name, "", *bins)
        return (name, "", len(bins) - 1, np.asarray(bins, dtype="float64"))

    for sname, sets in samples.items():
        is_sig = sname.startswith("scenario")
        own = f"mpi_{ML.point_mpi(sname)}_mA_{ML.point_mass(sname):g}" if is_sig else None
        booked = []      # (hist name, RResultPtr, scale)
        effs = []        # (group, label, sum ptr, count ptr, scale)
        for i, (files, scale, blind) in enumerate(sets):
            df = (ROOT.RDataFrame("Events", files).Define("w", "(double) (dirid >= 0 ? 1. : weight)")
                  .Define("t", f"-std::log10(std::max(1. - (double) {bdt}, 1e-7))")
                  .Define("s", f"(double) {bdt}"))
            if blind:
                df = df.Filter(f"!({core})", "blinded cores")
            full = df.Filter(f"mass > 0 && mass < {MASS_HI}")
            # inclusive score: data and QCD without the cores, signal everywhere
            inc = full if (blind or is_sig) else full.Filter(f"!({core})")
            for tag, col, bins in (("lin", "s", LIN), ("tail", "t", TAIL)):
                booked.append((f"score_incl_{tag}", inc.Histo1D(model(f"i{tag}{i}", bins), col, "w"), scale))
            for label, c in [("all", NOCUT), ("evaluated", EVAL), ("loose", ML.LOOSE_BDT), ("tight", tight)]:
                d = inc.Filter(f"s > {c!r}")
                effs.append(("incl", label, d.Sum("w"), d.Count(), scale))
            for j, (label, c) in enumerate(stages):
                booked.append((f"mass_full_{j}", full.Filter(f"s > {c!r}").Histo1D(model(f"mf{i}_{j}", edges), "mass", "w"), scale))
            for k, (mpi, m) in groups.items():
                if is_sig and k != own:
                    continue
                lo, hi = window(m, 5)
                clo, chi = window(m, 2)
                win = df.Filter(f"mass > {lo!r} && mass < {hi!r}")
                pop = win if is_sig else win.Filter(f"!(mass > {clo!r} && mass < {chi!r})")   # sidebands
                for tag, col, bins in (("lin", "s", LIN), ("tail", "t", TAIL)):
                    booked.append((f"score_{k}_{tag}", pop.Histo1D(model(f"s{k}{tag}{i}", bins), col, "w"), scale))
                ck = cuts[k]
                for label, c in [("all", NOCUT), ("evaluated", EVAL), ("loose", ML.LOOSE_BDT)] + [(x, ck[x]) for x in WPS + ("best",) if x in ck]:
                    d = pop.Filter(f"s > {c!r}")
                    effs.append((k, label, d.Sum("w"), d.Count(), scale))
                for label, c in [("nocut", NOCUT), ("loose", ML.LOOSE_BDT)] + [(x, ck[x]) for x in WPS if x in ck]:
                    booked.append((f"mass_{k}_{label}", win.Filter(f"s > {c!r}")
                                   .Histo1D(model(f"mw{k}{label}{i}", (50, lo, hi)), "mass", "w"), scale))
        for name, ptr, scale in booked:
            H.setdefault(name, {})
            H[name][sname] = add(H[name].get(sname), ptr.GetValue(), scale)
        for k, label, sw, n, scale in effs:
            e = E.setdefault(k, {}).setdefault(sname, {}).setdefault(label, [0., 0])
            e[0] += sw.GetValue() * scale; e[1] += int(n.GetValue())
        print("filled", sname, flush=True)

    out = {"case": a.case, "scenario": a.scenario, "lumi_pb": lumi, "data_fraction": dw["n_read"] / dw["n_total"],
           "qcd_frac": a.qcd_frac, "groups": groups, "cuts": cuts, "tight": tight, "stages": stages, "incl_wp": incl_wp,
           "mass_edges": list(edges), "cores": [window(m, 2) for m in masses], "points": list(sig_norm),
           "sig_norm": sig_norm, "qcd": rows, "H": H, "E": E}
    with open(path, "w") as f:
        json.dump(out, f)
    print("wrote", path)
    return out


# ------------------------------------------------------------------------------------------------------------ plots
def sig_label(d, p, plain=False):
    if plain:      # score pages: the scenario is in the legend title
        return f"Signal, $c\\tau$ = {ML.point_ctau(p):g} mm"
    return f"sc{d['scenario']}, $c\\tau$ = {ML.point_ctau(p):g} mm"


def bench_label(d, p):
    return f"sc{d['scenario']}, $m_{{\\pi}}$={ML.point_mpi(p)}, $m_{{A'}}$={ML.point_mass(p):g}, $c\\tau$={ML.point_ctau(p):g} mm"


def group_text(d, k, long=False):
    mpi, m = d["groups"][k]
    if long:
        return f"Scenario {d['scenario']}, mpi={mpi}, mA={m:g} GeV"
    return f"sc{d['scenario']}, mpi={mpi}, mA={m:g} GeV"


def header(ax, d, hep, fontsize=HEAD_FS):
    """CMS Preliminary + 'lumi (energy, year)', both at the same visual size."""
    hep.cms.text("Preliminary", ax=ax, loc=0, fontsize=fontsize)
    ax.text(1., 1.005, f"{d['lumi_pb'] / 1000.:.2f} fb$^{{-1}}$ (13.6 TeV, 2024)", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=fontsize * 1.3)


def minor_ticks(ax, logy=True, linx=True):
    """Intermediate ticks on both axes."""
    if logy:
        ax.yaxis.set_major_locator(LogLocator(base=10, numticks=30))
        ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=300))
        ax.yaxis.set_minor_formatter(NullFormatter())
    else:
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    if linx:
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))


def stairs_band(ax, edges, v, var, color, label, norm=1., band=True):
    v, err = np.array(v) / norm, np.sqrt(np.array(var)) / norm
    h = ax.stairs(v, edges, color=color, lw=2, label=label)
    if band:
        ax.fill_between(edges, np.append(v - err, 0), np.append(v + err, 0), step="post", color=color, alpha=0.25, lw=0)
    return h


def points(ax, edges, v, var, label, norm=1., mask=None):
    v, err = np.array(v) / norm, np.sqrt(np.array(var)) / norm
    c = 0.5 * (edges[1:] + edges[:-1])
    ok = v > 0 if mask is None else (v > 0) & mask
    return ax.errorbar(c[ok], v[ok], yerr=err[ok], fmt="o", color="black", ms=4, lw=1, label=label)


def ratio(ax, edges, dat, qcd, nd=1., nq=1., mask=None, band=True):
    """Data / QCD. band=True: data errors on the points, QCD statistical uncertainty as a band around 1;
    band=False (score pages, user 2026-11-13): no band, the QCD uncertainty is added in quadrature to the points."""
    dv, de = np.array(dat[0]) / nd, np.sqrt(np.array(dat[1])) / nd
    qv, qe = np.array(qcd[0]) / nq, np.sqrt(np.array(qcd[1])) / nq
    c = 0.5 * (edges[1:] + edges[:-1])
    ok = (dv > 0) & (qv > 0)
    if mask is not None:
        ok &= mask
    with np.errstate(divide="ignore", invalid="ignore"):
        r = dv / qv
        rel = np.where(qv > 0, qe / qv, 0.)
        err = de / qv if band else r * np.sqrt((de / np.where(dv > 0, dv, 1.)) ** 2 + rel ** 2)
        ax.errorbar(c[ok], r[ok], yerr=err[ok], fmt="o", color="black", ms=4, lw=1)
    if band:
        ax.fill_between(edges, np.append(1 - rel, 1), np.append(1 + rel, 1), step="post", color="royalblue", alpha=0.25, lw=0)
    ax.axhline(1., color="royalblue", lw=1)
    ax.set_ylim(0., 3.); ax.set_ylabel("Data / QCD", fontsize=18, loc="center")


def ylog(ax, arrays, pad_hi=30.):
    pos = [x for arr in arrays for x in np.ravel(arr) if x > 0]
    if not pos:
        return
    ax.set_yscale("log"); ax.set_ylim(max(min(pos) / 3., max(pos) * 1e-8), max(pos) * pad_hi)


def score_page(d, plt, hep, key, title, sigs, vlines, sel_text, ncol=3, cumulative=False, subtitle=""):
    """Two columns (score, tail), each with a data/QCD ratio panel. Unit area = ALL events of the population,
    including those without a score (-1), whose share is quoted in the legend title."""
    fig = plt.figure(figsize=(18, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], hspace=0.06, wspace=0.2, left=0.07, right=0.98, top=0.93, bottom=0.1)
    E = d["E"][key]
    tot = lambda s: E.get(s, {}).get("all", [0.])[0]
    nosc = lambda s: 100. * (1. - E[s]["evaluated"][0] / tot(s)) if tot(s) > 0 else float("nan")
    for col, (tag, bins) in enumerate((("lin", LIN), ("tail", TAIL))):
        h = d["H"].get(f"score_{key}_{tag}", {})
        if "data" not in h or "qcd" not in h:
            continue
        if cumulative:     # fraction of events at or above the lower edge of each bin (monotonic by construction)
            h = {k: [list(np.cumsum(v[0][::-1])[::-1]), list(np.cumsum(v[1][::-1])[::-1])] for k, v in h.items()}
        edges = np.linspace(bins[1], bins[2], bins[0] + 1)
        ax, rx = fig.add_subplot(gs[0, col]), fig.add_subplot(gs[1, col])
        nd, nq = tot("data"), tot("qcd")
        shown, handles = [], []
        hq = None
        if nq > 0:
            hq = stairs_band(ax, edges, *h["qcd"], "royalblue", "QCD MC", nq, band=False); shown.append(np.array(h["qcd"][0]) / nq)
        if nd > 0:
            handles.append(points(ax, edges, *h["data"], f"Data ({sel_text})", nd)); shown.append(np.array(h["data"][0]) / nd)
        if hq is not None:
            handles.append(hq)
        for i, (p, lab) in enumerate(sigs):
            ns = tot(p)
            if p in h and ns > 0:
                handles.append(ax.stairs(np.array(h[p][0]) / ns, edges, color=SIG_COLORS[i % len(SIG_COLORS)], lw=1.8, label=lab))
                shown.append(np.array(h[p][0]) / ns)
        nline = 0
        for lab, x, ls in vlines:
            xx = x if tag == "lin" else tail(x)
            if tag == "lin":
                continue                                    # cut lines only on the right-hand panel (user 2026-11-13)
            for axx in (ax, rx):
                axx.axvline(xx, color="0.35", ls=ls, lw=1.3)
            # label next to the line (x in data, y in axes coordinates), staggered so neighbours do not overlap
            ax.text(xx, 0.02, f" {lab} ({x:.4g}) ", transform=ax.get_xaxis_transform(), rotation=90,
                    ha="right", va="bottom", fontsize=12, color="0.2",
                    bbox=dict(facecolor="white", alpha=0.5, edgecolor="none", pad=0.5))
            nline += 1
        ax.set_yscale("log"); ax.set_ylim(1e-5, 1e3)        # fixed range (user 2026-11-13)
        ax.set_xlim(edges[0], edges[-1]); rx.set_xlim(edges[0], edges[-1])
        ax.set_ylabel("Fraction of events above the score" if cumulative else "Fraction of events / bin", fontsize=AXIS_FS); ax.tick_params(labelbottom=False)
        if nd > 0 and nq > 0:
            ratio(rx, edges, h["data"], h["qcd"], nd, nq, band=False)
        rx.set_ylabel("Data / QCD", fontsize=AXIS_FS, loc="center")
        rx.set_xlabel("BDT score", fontsize=AXIS_FS)
        # intermediate ticks on every axis
        ax.yaxis.set_major_locator(LogLocator(base=10, numticks=30))
        ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=300))
        ax.yaxis.set_minor_formatter(NullFormatter())
        rx.yaxis.set_minor_locator(AutoMinorLocator(2))
        if tag == "lin":
            for axx in (ax, rx):
                axx.xaxis.set_minor_locator(AutoMinorLocator(4))
        if tag == "tail":      # axis linear in -log10(1 - score), labelled with the score itself
            for axx in (ax, rx):
                axx.set_xticks([0, 1, 2, 3, 4, 5])
                axx.set_xticks([tail(1. - k * 10. ** -(n + 1)) for n in range(5) for k in range(2, 10)], minor=True)
            rx.set_xticklabels(["0", "0.9", "0.99", "0.999", "0.9999", ""])   # last label would overflow the page
        ax.legend(handles=handles, fontsize=12, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=ncol, title_fontsize=12, **LEGEND_KW,
                  title=f"{title}\n{ML.HLT_NAME[d['case']]}" + (f"\n{subtitle}" if subtitle else ""))
        hep.cms.text("Preliminary", ax=ax, loc=0, fontsize=HEAD_FS)     # header: both parts at the same size
        ax.text(1., 1.005, f"{d['lumi_pb'] / 1000.:.2f} fb$^{{-1}}$ (13.6 TeV, 2024)", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=HEAD_FS * 1.3)
    return fig


SIG_NORM = r"signal normalised to $\mathcal{B}(H\to\psi\psi)$ = 1%"
MASS_X = r"$m_{\mu\mu}$ of the best-$\chi^2$ muonSV [GeV]"


def mass_full_page(d, plt, hep, j, benches):
    """Same formatting as the score pages (user 2026-11-13): no QCD band, legend data -> QCD -> signals on a
    half-transparent white box below the top ticks, common axis-title size, intermediate ticks."""
    label, cut = d["stages"][j]
    h = d["H"][f"mass_full_{j}"]
    edges = np.array(d["mass_edges"]); width = np.diff(edges)
    mask = np.array([not any(lo - 1e-9 <= edges[i] and edges[i + 1] <= hi + 1e-9 for lo, hi in d["cores"]) for i in range(len(width))])
    fig = plt.figure(figsize=(13, 10))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.06, left=0.11, right=0.97, top=0.93, bottom=0.1)
    ax, rx = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    dens = lambda v: [np.array(v[0]) / width, np.array(v[1]) / width ** 2]
    q, dat = dens(h["qcd"]), dens(h["data"])
    hq = stairs_band(ax, edges, *q, "royalblue", "QCD MC", band=False)
    handles = [points(ax, edges, *dat, "Data", mask=mask)]
    shown = [q[0], dat[0][mask]]
    for n, (lo, hi) in enumerate(d["cores"]):
        for axx in (ax, rx):
            hb = axx.axvspan(lo, hi, facecolor="none", edgecolor="0.75", hatch="//", lw=0, zorder=0, label="Blinded in data")
            if n == 0 and axx is ax:
                handles.append(hb)
    handles.append(hq)                      # legend order: data, blinded, QCD, signals (user 2026-11-13)
    for i, p in enumerate(benches):
        if p in h:
            s = dens(h[p])
            handles.append(ax.stairs(s[0], edges, color=SIG_COLORS[i % len(SIG_COLORS)], lw=1.5, label=bench_label(d, p)))
    ax.set_yscale("log"); ax.set_ylim(5e-4, 9e10)          # fixed range (user 2026-11-13)
    for axx in (ax, rx):
        axx.set_xscale("log"); axx.set_xlim(MASS_LO, MASS_HI)
    ax.set_ylabel("Events / GeV", fontsize=AXIS_FS); ax.tick_params(labelbottom=False)
    ratio(rx, edges, [h["data"][0], h["data"][1]], [h["qcd"][0], h["qcd"][1]], mask=mask, band=False)
    rx.set_ylabel("Data / QCD", fontsize=AXIS_FS, loc="center")
    rx.set_xlabel(MASS_X, fontsize=AXIS_FS)
    minor_ticks(ax, linx=False); minor_ticks(rx, logy=False, linx=False)
    ax.legend(handles=handles, fontsize=12, loc="upper right", bbox_to_anchor=(0.99, 0.965), ncol=1, title_fontsize=13, **LEGEND_KW,
              title=f"{label}\n{ML.HLT_NAME[d['case']]}")
    header(ax, d, hep)
    return fig


def mass_stages_page(d, plt, hep):
    edges = np.array(d["mass_edges"]); width = np.diff(edges)
    mask = np.array([not any(lo - 1e-9 <= edges[i] and edges[i + 1] <= hi + 1e-9 for lo, hi in d["cores"]) for i in range(len(width))])
    fig, axes = plt.subplots(1, 2, figsize=(20, 9))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.93, bottom=0.1, wspace=0.18)
    cols = ["black", "0.55", "tab:blue", "tab:green", "tab:orange", "tab:red", "tab:purple"]
    for ax, sample, name in zip(axes, ("data", "qcd"), ("Data (cores blinded)", "QCD MC")):
        shown = []
        for j, (label, cut) in enumerate(d["stages"]):
            v = np.array(d["H"][f"mass_full_{j}"][sample][0]) / width
            if sample == "data":
                v = np.where(mask, v, np.nan)
            ax.stairs(v, edges, color=cols[j % len(cols)], lw=1.6, label=label)
            shown.append(v[np.isfinite(v)])
        ylog(ax, shown, pad_hi=1e3)
        ax.set_xscale("log"); ax.set_xlim(MASS_LO, MASS_HI)
        ax.set_xlabel(MASS_X, fontsize=AXIS_FS); ax.set_ylabel("Events / GeV", fontsize=AXIS_FS)
        minor_ticks(ax, linx=False)
        ax.legend(fontsize=13, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=2, title_fontsize=13, **LEGEND_KW,
                  title=f"Scenario {d['scenario']}, {name}\n{ML.HLT_NAME[d['case']]}")
        header(ax, d, hep)
    return fig


def curve(ax, edges, v, color, lw, after, ms=5):
    """Histogram line: solid before the BDT cut; dashed with open squares at the filled bins after it."""
    v = np.asarray(v, dtype=float)
    ax.stairs(v, edges, color=color, lw=lw, ls="--" if after else "-")
    if after:
        c = np.sqrt(edges[1:] * edges[:-1]) if ax.get_xscale() == "log" else 0.5 * (edges[1:] + edges[:-1])
        ok = np.isfinite(v) & (v > 0)
        ax.plot(c[ok], v[ok], ls="none", marker="s", mfc="none", mec=color, ms=ms)


def style_handles(after_label):
    from matplotlib.lines import Line2D
    return [Line2D([], [], color="0.3", lw=1.5, ls="-", label="solid: no BDT cut"),
            Line2D([], [], color="0.3", lw=1.5, ls="--", marker="s", mfc="none", ms=6, label=f"dashed, open squares: {after_label}")]


def mass_before_after_page(d, plt, hep, sigs):
    """First page (user 2026-11-13): full spectrum with data, QCD MC and a couple of signal points overlaid,
    before the BDT cut (solid) and after the inclusive data working point (dashed, open squares); the config
    tight working point if the histograms hold no inclusive one."""
    from matplotlib.lines import Line2D
    edges = np.array(d["mass_edges"]); width = np.diff(edges)
    mask = np.array([not any(lo - 1e-9 <= edges[i] and edges[i + 1] <= hi + 1e-9 for lo, hi in d["cores"]) for i in range(len(width))])
    last = len(d["stages"]) - 1 if d.get("incl_wp") else [j for j, (_, c) in enumerate(d["stages"]) if c == d["tight"]][0]
    fig, ax = plt.subplots(figsize=(13, 10))
    fig.subplots_adjust(left=0.11, right=0.97, top=0.93, bottom=0.1)
    ax.set_xscale("log")
    for j, after in ((0, False), (last, True)):
        h = d["H"][f"mass_full_{j}"]
        curve(ax, edges, np.array(h["qcd"][0]) / width, "royalblue", 2, after, ms=4)
        curve(ax, edges, np.where(mask, np.array(h["data"][0]) / width, np.nan), "black", 2, after, ms=4)
        for i, p in enumerate(sigs):
            if p in h:
                curve(ax, edges, np.array(h[p][0]) / width, SIG_COLORS[i % len(SIG_COLORS)], 1.5, after, ms=4)
    handles = [Line2D([], [], color="black", lw=2, label="Data (cores blinded)"), Line2D([], [], color="royalblue", lw=2, label="QCD MC")]
    handles += [Line2D([], [], color=SIG_COLORS[i % len(SIG_COLORS)], lw=1.5, label=bench_label(d, p)) for i, p in enumerate(sigs)]
    handles += style_handles(d["stages"][last][0])
    ax.set_yscale("log"); ax.set_ylim(5e-4, 9e10); ax.set_xlim(MASS_LO, MASS_HI)
    ax.set_xlabel(MASS_X, fontsize=AXIS_FS); ax.set_ylabel("Events / GeV", fontsize=AXIS_FS)
    minor_ticks(ax, linx=False)
    ax.legend(handles=handles, fontsize=13, loc="upper right", bbox_to_anchor=(0.99, 0.965), ncol=1, title_fontsize=13, **LEGEND_KW,
              title=ML.HLT_NAME[d["case"]])
    header(ax, d, hep)
    return fig


def mass_overlay_page(d, plt, hep, k):
    """Mass window of one hypothesis: no BDT cut (solid, filled markers) vs after the BDT cut at the data working
    point of the scenario (dashed, open markers) -- user 2026-11-13. None if the histograms are not there."""
    from matplotlib.lines import Line2D
    wp = OVERLAY_WP[d["scenario"]]
    h0, h1 = d["H"].get(f"mass_{k}_nocut", {}), d["H"].get(f"mass_{k}_{wp}", {})
    if "qcd" not in h0 or "qcd" not in h1:
        return None
    mpi, m = d["groups"][k]
    lo, hi = window(m, 5); clo, chi = window(m, 2)
    edges = np.linspace(lo, hi, 51); c = 0.5 * (edges[1:] + edges[:-1])
    mask = ~((c > clo) & (c < chi))
    cut = d["cuts"][k][wp]
    sigs = sorted([p for p in d["points"] if f"mpi_{ML.point_mpi(p)}_mA_{ML.point_mass(p):g}" == k], key=ML.point_ctau)
    fig, ax = plt.subplots(figsize=(13, 10))
    fig.subplots_adjust(left=0.11, right=0.97, top=0.93, bottom=0.1)
    shown, handles = [], []
    for hh, ls, after in ((h0, "-", False), (h1, "--", True)):
        v, err = np.array(hh["data"][0]), np.sqrt(np.array(hh["data"][1]))
        ok = (v > 0) & mask
        ax.errorbar(c[ok], v[ok], yerr=err[ok], fmt="s" if after else "o", color="black", mfc="none" if after else "black", ms=6 if after else 5, lw=1)
        curve(ax, edges, hh["qcd"][0], "royalblue", 2, after)
        shown += [v[mask], hh["qcd"][0]]
        for i, p in enumerate(sigs):
            if p in hh:
                curve(ax, edges, hh[p][0], SIG_COLORS[i % len(SIG_COLORS)], 1.5, after)
                shown.append(hh[p][0])
    hb = ax.axvspan(clo, chi, facecolor="none", edgecolor="0.75", hatch="//", lw=0, zorder=0, label="Blinded in data")
    handles = [Line2D([], [], color="black", marker="o", ls="none", ms=5, label="Data (sidebands)"), hb,
               Line2D([], [], color="royalblue", lw=2, label="QCD MC")]
    handles += [Line2D([], [], color=SIG_COLORS[i % len(SIG_COLORS)], lw=1.5, label=bench_label(d, p)) for i, p in enumerate(sigs)]
    handles += style_handles(f"BDT > {cut:.4f} (WP {wp})")
    ylog(ax, shown, pad_hi=1e6)
    ax.set_xlim(lo, hi); ax.set_xlabel(r"$m_{\mu\mu}$ [GeV]", fontsize=AXIS_FS)
    ax.set_ylabel(f"Events / {1000 * (hi - lo) / 50:.2g} MeV", fontsize=AXIS_FS)
    minor_ticks(ax)
    ax.legend(handles=handles, fontsize=12, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=2, title_fontsize=13, **LEGEND_KW,
              title=ML.HLT_NAME[d['case']])
    header(ax, d, hep)
    return fig


def mass_window_page(d, plt, hep, k):
    mpi, m = d["groups"][k]
    lo, hi = window(m, 5); clo, chi = window(m, 2)
    edges = np.linspace(lo, hi, 51); c = 0.5 * (edges[1:] + edges[:-1])
    mask = ~((c > clo) & (c < chi))
    ck = d["cuts"][k]
    panels = [("nocut", "no BDT cut"), ("loose", f"BDT > {ML.LOOSE_BDT:g} (loose)")] + \
             [(x, f"BDT > {ck[x]:.4f} (data WP {x})") for x in WPS[:2] if x in ck]
    sigs = sorted([p for p in d["points"] if f"mpi_{ML.point_mpi(p)}_mA_{ML.point_mass(p):g}" == k], key=ML.point_ctau)
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.95, bottom=0.07, wspace=0.18, hspace=0.2)
    for ax, (tag, label) in zip(axes.flat, panels):
        h = d["H"].get(f"mass_{k}_{tag}", {})
        if "qcd" not in h:
            ax.set_axis_off(); continue
        hq = stairs_band(ax, edges, *h["qcd"], "royalblue", "QCD MC", band=False)
        handles = [points(ax, edges, *h["data"], "Data (sidebands)", mask=mask),
                   ax.axvspan(clo, chi, facecolor="none", edgecolor="0.75", hatch="//", lw=0, zorder=0, label="Blinded in data"), hq]
        shown = [h["qcd"][0], np.array(h["data"][0])[mask]]
        for i, p in enumerate(sigs):
            if p in h:
                handles.append(ax.stairs(h[p][0], edges, color=SIG_COLORS[i % len(SIG_COLORS)], lw=1.5, label=bench_label(d, p)))
                shown.append(h[p][0])
        ylog(ax, shown, pad_hi=3e5)
        ax.set_xlim(lo, hi); ax.set_xlabel(r"$m_{\mu\mu}$ [GeV]", fontsize=AXIS_FS)
        ax.set_ylabel(f"Events / {1000 * (hi - lo) / 50:.2g} MeV", fontsize=AXIS_FS)
        minor_ticks(ax)
        ax.legend(handles=handles, fontsize=12, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=2, title_fontsize=13, **LEGEND_KW,
                  title=f"{label}\n{ML.HLT_NAME[d['case']]}")
        header(ax, d, hep)
    for ax in axes.flat[len(panels):]:
        ax.set_axis_off()
    return fig


def plot(a, d):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import mplhep as hep
    hep.style.use("CMS")
    test = [f"test_qcd{100. * d['qcd_frac']:g}pct"] if d["qcd_frac"] < 1 else []
    root = os.path.join(a.publish, "data1pct", a.tag)
    stem = f"sc{a.scenario}_{a.case}"
    order = sorted(d["groups"], key=lambda k: (float(d["groups"][k][0]), d["groups"][k][1]))
    pts = sorted(d["points"], key=lambda p: (float(ML.point_mpi(p)), ML.point_mass(p), ML.point_ctau(p)))
    by_group = {k: [p for p in pts if f"mpi_{ML.point_mpi(p)}_mA_{ML.point_mass(p):g}" == k] for k in order}
    benches = []       # lightest and heaviest mass group, shortest and longest ctau
    by_m = sorted(order, key=lambda k: d["groups"][k][1])
    for k in dict.fromkeys([by_m[0], by_m[-1]]):
        if by_group[k]:
            benches += list(dict.fromkeys([by_group[k][0], by_group[k][-1]]))

    def emit(sub, name, pages):
        pub = os.path.join(root, sub, *test, a.case, f"scenario{a.scenario}")
        os.makedirs(os.path.join(pub, "png"), exist_ok=True)
        with PdfPages(os.path.join(pub, f"{name}_{stem}.pdf")) as pdf:
            for tag, fig in pages:
                pdf.savefig(fig); fig.savefig(os.path.join(pub, "png", f"{name}_{stem}_{tag}.png"), dpi=110); plt.close(fig)
        print("published", os.path.join(pub, f"{name}_{stem}.pdf"))
        return pub

    ls = {"1e-3": "--", "1e-4": "-.", "1e-5": ":", "best": (0, (5, 1, 1, 1, 1, 1))}
    pages = [("inclusive", score_page(d, plt, hep, "incl", f"Scenario {d['scenario']}, all masses 0-22 GeV, signal cores removed",
                                       [(p, bench_label(d, p)) for p in benches],
                                       [("loose", ML.LOOSE_BDT, "-"), ("tight", d["tight"], "--")], "cores blinded", ncol=2))]
    for k in order:
        ck = d["cuts"][k]
        vl = [("loose", ML.LOOSE_BDT, "-")] + [(f"WP {x}" if x != "best" else "best BDT", ck[x], ls[x]) for x in WPS + ("best",) if x in ck]
        pages.append((k.replace(".", "p"), score_page(d, plt, hep, k, group_text(d, k, True),
                                                      [(p, sig_label(d, p, True)) for p in by_group[k]], vl, "sidebands",
                                                      subtitle="data, QCD: sidebands; signal: window")))
    # cumulative versions of the same pages (user 2026-11-13), appended to the same pdf
    pages.append(("cumulative_inclusive", score_page(d, plt, hep, "incl", f"Scenario {d['scenario']}, all masses 0-22 GeV, signal cores removed",
                                                     [(p, bench_label(d, p)) for p in benches],
                                                     [("loose", ML.LOOSE_BDT, "-"), ("tight", d["tight"], "--")], "cores blinded",
                                                     ncol=2, cumulative=True)))
    for k in order:
        ck = d["cuts"][k]
        vl = [("loose", ML.LOOSE_BDT, "-")] + [(f"WP {x}" if x != "best" else "best BDT", ck[x], ls[x]) for x in WPS + ("best",) if x in ck]
        pages.append(("cumulative_" + k.replace(".", "p"),
                      score_page(d, plt, hep, k, group_text(d, k, True),
                                 [(p, sig_label(d, p, True)) for p in by_group[k]], vl, "sidebands", cumulative=True,
                                 subtitle="data, QCD: sidebands; signal: window")))
    pub = emit("bdtScores", "bdt_scores", pages)
    with open(os.path.join(pub, f"bdt_efficiencies_{stem}.csv"), "w") as f:
        f.write("population,sample,selection,cut,sumw,n_raw,fraction_of_all\n")   # all = incl. events without score (-1)
        for k in ["incl"] + order:
            for s, e in d["E"].get(k, {}).items():
                for label, (sw, n) in e.items():
                    cut = {"all": "none", "evaluated": 0., "loose": ML.LOOSE_BDT, "tight": d["tight"]}.get(label, d["cuts"].get(k, {}).get(label))
                    tot = e["all"][0]
                    f.write(f"{k},{s},{label},{cut},{sw:.6g},{n},{sw / tot if tot > 0 else float('nan'):.4g}\n")

    # no BDT cut vs after the working-point cut, one page per mass hypothesis, first in the pdf (user 2026-11-13)
    mid = [by_group[k][len(by_group[k]) // 2] for k in dict.fromkeys([by_m[0], by_m[-1]]) if by_group[k]]
    pages = [("before_after", mass_before_after_page(d, plt, hep, mid))]
    pages += [("overlay_" + k.replace(".", "p"), f) for k in order for f in [mass_overlay_page(d, plt, hep, k)] if f is not None]
    pages += [("stages", mass_stages_page(d, plt, hep))]
    pages += [(f"full_stage{j}", mass_full_page(d, plt, hep, j, benches)) for j in range(len(d["stages"]))]
    pages += [("window_" + k.replace(".", "p"), mass_window_page(d, plt, hep, k)) for k in order]
    emit("massSpectra", "mass_spectra", pages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=list(ML.DATA))
    ap.add_argument("--scenario", required=True, choices=["A", "B1"])
    ap.add_argument("--tag", default="v2", help="limits production: stored data working points, publish directory")
    ap.add_argument("--nobdt-tag", default="v2_nobdt", help="no-BDT-cut selection of data and signal")
    ap.add_argument("--qcd-tag", default="v2_qcd")
    ap.add_argument("--qcd-frac", type=float, default=1., help="use only this fraction of the QCD parts (test)")
    ap.add_argument("--publish", default=os.path.expanduser("~/public_html/parking/2024/limits"))
    ap.add_argument("--replot", action="store_true", help="redraw from the stored histograms")
    a = ap.parse_args()
    suffix = f"_qcd{100. * a.qcd_frac:g}pct" if a.qcd_frac < 1 else ""
    path = os.path.join(os.environ["CMT_STORE"], "Limits1pct", a.tag, a.case, f"bdt_scores_sc{a.scenario}_{a.case}{suffix}.json")
    d = json.load(open(path)) if a.replot else fill(a, path)
    plot(a, d)


if __name__ == "__main__":
    main()
