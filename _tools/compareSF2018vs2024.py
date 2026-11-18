#!/usr/bin/env python3
"""Overlay the 2024 tag-and-probe muon scale factors (from _tools/fitTnPScaleFactors.py) on the
2018 ones in data/*.json, one panel per 2024 probe-pT bin, SF vs displacement.

Comparisons (2018 json -> 2024 output), matched by the variable each SF is binned in:
    ID       data/id_sf.json                  |muonSV_dxy| (= SV lxy)  <-> IDSFtnp2024      lxy
    trigger  data/trigger_sf.json  (default)  |muonSV_dxy| (= SV lxy)  <-> TriggerSFtnp2024 lxy
    trigger  data/trigger_sf_mudxy.json       probe-muon |dxy|         <-> TriggerSFtnp2024 dxy
    trigger  data/trigger_sf_alltriggers.json probe pT x dxy/sigma     <-> TriggerSFtnp2024 dxysig
             (2018 = all B-parking triggers, the AN final choice; 2024 = Mu10 only)

2018 bands: the 2018 pT bin containing the centre of the 2024 pT bin; sf with [systdown, systup].
2024 points: count (filled) and fit (open) yields; x error bar = bin width; points outside
the y range are drawn as triangles at the edge.

--case DoubleMu draws only the ID page (2018 had no dimuon-trigger SF to compare with).

Example:
    python3 _tools/compareSF2018vs2024.py --tag BuToJpsiK
    python3 _tools/compareSF2018vs2024.py --tag BuToJpsiK --case DoubleMu
    python3 _tools/compareSF2018vs2024.py --tag BuToJpsiK --suffix LegacyBinning   # 2024 in the 2018 bins
"""
import argparse
import json
import math
import os
import shutil
import sys

import numpy as np

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(TOOLS)
PUBLIC = os.path.expanduser("~/public_html/parking/2024/SF_checks")

COMPARISONS = [
    dict(name="ID", json="id_sf.json", task="IDSFtnp2024", var="lxy", cases=("Mu10", "DoubleMu"),
         title="Muon loose ID SF: 2018 (|muonSV d$_{xy}$|) vs 2024 {case} stream (muonSV L$_{xy}$)",
         xlabel="muonSV L$_{xy}$ (cm)", log=True),
    dict(name="trigger", json="trigger_sf.json", task="TriggerSFtnp2024", var="lxy", cases=("Mu10",),
         title="Trigger SF: 2018 default (|muonSV d$_{xy}$|) vs 2024 Mu10 (muonSV L$_{xy}$)",
         xlabel="muonSV L$_{xy}$ (cm)", log=True),
    dict(name="trigger_mudxy", json="trigger_sf_mudxy.json", task="TriggerSFtnp2024", var="dxy", cases=("Mu10",),
         title="Trigger SF: 2018 muon |d$_{xy}$| vs 2024 Mu10 probe |d$_{xy}$|",
         xlabel="Probe |d$_{xy}$| (cm)", log=True),
    dict(name="trigger_alltriggers", json="trigger_sf_alltriggers.json", task="TriggerSFtnp2024",
         var="dxysig", cases=("Mu10",), title="Trigger SF: 2018 all B-parking triggers vs 2024 Mu10, in |d$_{xy}$|/$\\sigma$",
         xlabel="Probe |d$_{xy}$|/$\\sigma$", log=True),
]


def load_2018(path):
    """-> dict(x_edges, pt_edges, sf, up, down) with arrays [nx, npt] (x = displacement)."""
    c = json.load(open(path))["corrections"][0]
    outer = c["data"]
    inner_input = outer["content"][0]["input"]
    ne_o, ne_i = len(outer["edges"]) - 1, len(outer["content"][0]["edges"]) - 1
    vals = {k: np.full((ne_o, ne_i), np.nan) for k in ("sf", "systup", "systdown")}
    for io, node in enumerate(outer["content"]):
        for ii, cat in enumerate(node["content"]):
            for item in cat["content"]:
                vals[item["key"]][io, ii] = item["value"]
    if outer["input"] == "pt":  # alltriggers: pt outer, dxysig inner -> transpose
        x_edges, pt_edges = node["edges"], outer["edges"]
        vals = {k: v.T for k, v in vals.items()}
    else:
        x_edges, pt_edges = outer["edges"], outer["content"][0]["edges"]
        assert inner_input == "pt", inner_input
    return dict(name=c["name"], x_edges=np.array(x_edges, float), pt_edges=np.array(pt_edges, float),
                sf=vals["sf"], up=vals["systup"], down=vals["systdown"])


def load_2024(ROOT, path):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        sys.exit(f"cannot open {path}")
    h = f.Get("sf")
    xe = np.array([h.GetXaxis().GetBinLowEdge(i) for i in range(1, h.GetNbinsX() + 2)])
    pe = np.array([h.GetYaxis().GetBinLowEdge(i) for i in range(1, h.GetNbinsY() + 2)])
    sf = np.full((len(xe) - 1, len(pe) - 1), np.nan)
    err = np.full_like(sf, np.nan)
    for i in range(len(xe) - 1):
        for j in range(len(pe) - 1):
            v, e = h.GetBinContent(i + 1, j + 1), h.GetBinError(i + 1, j + 1)
            if (v != 0 or e != 0) and math.isfinite(v) and math.isfinite(e):
                sf[i, j], err[i, j] = v, e
    f.Close()
    return dict(x_edges=xe, pt_edges=pe, sf=sf, err=err)


def draw_page(pdf, plt, cms, comp, s18, s24c, s24f, ylim):
    xe, pe = s24c["x_edges"], s24c["pt_edges"]
    rows = [j for j in range(len(pe) - 1) if np.isfinite(s24c["sf"][:, j]).any()]
    ncol = 3 if len(rows) > 4 else 2
    nrow = math.ceil(len(rows) / ncol)
    fig, axs = plt.subplots(nrow, ncol, figsize=(6.2 * ncol, 4.9 * nrow), squeeze=False)
    fig.suptitle(comp["title"].replace("{case}", comp.get("case", "")), fontsize=cms.FS_TITLE)
    xlo, xhi = xe[0], xe[-1]
    for k, ax in enumerate(axs.flat):
        if k >= len(rows):
            ax.set_axis_off()
            continue
        j = rows[k]
        ptc = 0.5 * (pe[j] + pe[j + 1])
        # 2018 band
        j18 = np.searchsorted(s18["pt_edges"], ptc, side="right") - 1
        p18lo, p18hi = s18["pt_edges"][j18], s18["pt_edges"][j18 + 1]
        first = True
        for i in range(len(s18["x_edges"]) - 1):
            a, b = max(s18["x_edges"][i], xlo), min(s18["x_edges"][i + 1], xhi)
            if b <= a or not np.isfinite(s18["sf"][i, j18]):
                continue
            ax.fill_between([a, b], s18["down"][i, j18], s18["up"][i, j18], color="tab:blue",
                            alpha=0.25, lw=0, step=None)
            ax.plot([a, b], [s18["sf"][i, j18]] * 2, color="tab:blue", lw=2,
                    label=(f"2018 (p$_T$ {p18lo:g}-{p18hi:g} GeV)".replace("inf", "$\\infty$")
                           if first else None))
            first = False
        # 2024 points
        for s, mk, fc, lab, shift in ((s24c, "o", "k", "2024, count", 1.0),
                                      (s24f, "s", "none", "2024, fit", 1.12)):
            if s is None:
                continue
            ok = np.isfinite(s["sf"][:, j])
            if not ok.any():
                continue
            lo_e, hi_e = xe[:-1][ok], xe[1:][ok]
            xc = np.sqrt(lo_e * hi_e) * shift if comp["log"] else 0.5 * (lo_e + hi_e)
            y, e = s["sf"][ok, j], s["err"][ok, j]
            inside = (y >= ylim[0]) & (y <= ylim[1])
            ax.errorbar(xc[inside], y[inside], yerr=e[inside],
                        xerr=[xc[inside] - lo_e[inside], hi_e[inside] - xc[inside]] if shift == 1.0 else None,
                        fmt=mk, color="k", mfc=fc, ms=5, lw=1, capsize=0, label=lab)
            if (~inside).any():
                yy = np.where(y[~inside] > ylim[1], ylim[1] - 0.04, ylim[0] + 0.04)
                ax.scatter(xc[~inside], yy, marker="^", c="tab:red", s=30, zorder=5,
                           label="2024 outside range" if shift == 1.0 else None)
        ax.axhline(1.0, color="gray", ls="--", lw=1)
        if comp["log"]:
            ax.set_xscale("log")
        ax.set_xlim(xlo, xhi)
        ax.set_ylim(*ylim)
        ax.set_xlabel(comp["xlabel"], fontsize=cms.FS_LABEL)
        ax.set_ylabel("Scale factor", fontsize=cms.FS_LABEL)
        ax.legend(loc="lower right", fontsize=cms.FS_LEGEND - 3, **cms.LEGEND_KW,
                  title=f"2024 probe p$_T$ {pe[j]:g}-{pe[j + 1]:g} GeV", title_fontsize=cms.FS_LEGEND - 3)
        cms.cms_axes(ax, header="2018 (13 TeV) vs 2024 (13.6 TeV)", fontsize=cms.FS_AXES - 3,
                     label=cms.CMS_LABEL_DATA)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tag", default="BuToJpsiK", help="tag of the 2024 fitter outputs (MC used)")
    p.add_argument("--case", default="Mu10")
    p.add_argument("--in-dir", default=os.path.join(TOOLS, "output_SF"))
    p.add_argument("--ymin", type=float, default=0.0)
    p.add_argument("--ymax", type=float, default=2.0)
    p.add_argument("--out", default=None, help="output pdf (default in --in-dir)")
    p.add_argument("--no-publish", action="store_true")
    p.add_argument("--suffix", default="", help="extra suffix of the fitter outputs, e.g. LegacyBinning "
                   "(fitTnPScaleFactors.py --legacy-binning); the PDF then goes to public_html/.../SF_check_<suffix>")
    args = p.parse_args()
    sfx = f"_{args.suffix}" if args.suffix else ""
    public = os.path.join(os.path.dirname(PUBLIC), f"SF_check_{args.suffix}") if args.suffix else PUBLIC

    sys.argv = sys.argv[:1]
    import ROOT
    ROOT.gROOT.SetBatch(True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    sys.path.insert(0, TOOLS)
    import cmsstyle as cms

    out = args.out or os.path.join(args.in_dir, f"compare_SF_2018_vs_2024_{args.case}_{args.tag}{sfx}.pdf")
    with PdfPages(out) as pdf:
        for comp in COMPARISONS:
            if args.case not in comp["cases"]:
                continue  # no 2018 counterpart (2018 had no dimuon trigger SF)
            comp = dict(comp, case=args.case)
            s18 = load_2018(os.path.join(BASE, "data", comp["json"]))
            stem = os.path.join(args.in_dir, f"tnp_{comp['task']}_{args.case}_{comp['var']}_{{}}_{args.tag}{sfx}.root")
            if not os.path.exists(stem.format("count")):
                print(f"{comp['name']}: SKIPPED, missing {stem.format('count')}")
                continue
            s24c = load_2024(ROOT, stem.format("count"))
            s24f = load_2024(ROOT, stem.format("fit")) if os.path.exists(stem.format("fit")) else None
            draw_page(pdf, plt, cms, comp, s18, s24c, s24f, (args.ymin, args.ymax))
            print(f"{comp['name']}: 2018 {s18['name']} vs {os.path.basename(stem.format('count'))}")
    print("written:", out)
    if not args.no_publish:
        os.makedirs(public, exist_ok=True)
        shutil.copy(out, public)
        print("copied to", public)


if __name__ == "__main__":
    main()
