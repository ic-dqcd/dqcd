#!/usr/bin/env python3
"""
Stage 1 of the standalone 1%-data limits: event selection, run per group of nanoAOD files.

Reproduces what the framework (PreprocessRDF -> Categorization -> PrePlot) does to each event, WITHOUT law:
  * the skim modules of config/modules_run3_efficienciesOnly_<path>.yaml, instantiated from the yaml exactly as
    RDFModuleTask.get_feature_modules does (parameters "self.*" eval'd against a stand-in task object), in file
    order: golden-JSON lumi mask (data), MET filters, muon/muonSV/fourmuonSV/trigger/loose selections, PU weight (MC).
    bdtsf is skipped (BDT_SF = 1.0 and is not a weight); chi2 (DummyMinChi2RDF) is run once.
  * the feature modules: the 2024 BDTs of BOTH scenarios for the trigger case (BDTULinference2024_<case> ->
    bdt_scenarioA_onlymu, BDTULinference2024_B1_<case> -> bdt_scenarioB1_onlymu), so the data is read once.
  * the 12 analysis categories (legacy_2018.add_categories + run3_2024 quadv exclusion of multiv) and the
    muonSV_bestchi2_mass feature selection (material dxy veto + dz veto, get_feature_mass_dxyzcut).
  * MC: the PreCounter normalisation denominator Sum(puWeight * filter_efficiency) over ALL raw events
    (filter_efficiency = 1 for every 2024 signal point), and weight = puWeight (weights.base).

Output: a slim tree "Events" (mass, cat 1-12 [1-6 singlev, 7-12 multiv], bdtA, bdtB1, weight, dirid, run, lumi, event)
with events that pass the loosest region (BDT > 0.6 for either scenario; --min-bdt -1 keeps the whole
preselected spectrum, used for the data-sideband BDT working points), plus a TTree "Norm" holding n_raw and
sumw_raw (the denominator), n_files and the ';'-joined list of input files actually read.
  weight: puWeight for MC, 1 for data (the per-directory 1%->100% scaling is applied by make_limits.py)
  dirid : index of the CRAB task directory of the event's file in data_dirs.json (--dir-ids), -1 for MC

Usage: select_events.py --case Mu10|DoubleMu --dataset NAME [--mc] [--dir-ids i1,i2,..] --out OUT.root FILE [FILE ...]
"""
import argparse, os, sys, types
from collections import OrderedDict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKIM_YAML = {"Mu10": "modules_run3_efficienciesOnly_HLT_Mu10_Barrel_L1HP11_IP6",
             "DoubleMu": "modules_run3_efficienciesOnly_HLT_DoubleMu4_3_LowMass"}
BDT_MODULES = {"A": ("DQCD.Modules.BDTULinference2024_{case}", "bdt_scenarioA_onlymu"),
               "B1": ("DQCD.Modules.BDTULinference2024_B1_{case}", "bdt_scenarioB1_onlymu")}
LOOSE_BDT = 0.6   # loose_bdt_scenario{A,B1}_<case>: everything tighter is a subset

# config/legacy_2018.py add_categories (+ run3_2024.py: multiv_* && !(isFourMuonPlusDimuonSV == 1))
D, P = "muonSV_dxy.at(min_chi2_index)", "muonSV_pAngle.at(min_chi2_index)"
SINGLE = "cat_index == 0 && muonSV_mu1eta.at(min_chi2_index) != 0 && muonSV_mu2eta.at(min_chi2_index) != 0"
MULTI = "cat_index > 0 && !(isFourMuonPlusDimuonSV == 1)"
DXY_P = [f"{D} < 1 && {P} < 0.2", f"{D} < 1 && {P} > 0.2",
         f"{D} > 1 && {D} < 10 && {P} < 0.2", f"{D} > 1 && {D} < 10 && {P} > 0.2",
         f"{D} > 10 && {P} < 0.2", f"{D} > 10 && {P} > 0.2"]
# get_feature_mass_dxyzcut: legacy_2018.py dxy_cut (material) && dz_cut
DXYZ_CUT = ("!((muonSV_bestchi2_dxy >= 6.4 && muonSV_bestchi2_dxy <= 7.3) || "
            "(muonSV_bestchi2_dxy >= 10.5 && muonSV_bestchi2_dxy <= 11.5) || "
            "(muonSV_bestchi2_dxy >= 15.6 && muonSV_bestchi2_dxy <= 16.6)) && "
            "(abs(muonSV_bestchi2_z) < 27 || abs(muonSV_bestchi2_z) > 52)")


def fake_task(dataset_name, is_mc):
    """Stand-in for the law task, so the yaml 'self.config...' / 'self.dataset...' strings eval the same way."""
    process = types.SimpleNamespace(isMC=is_mc, isData=not is_mc, isSignal=is_mc,
                                    name=dataset_name if is_mc else "data")
    dataset = types.SimpleNamespace(process=process, name=dataset_name, has_tag=lambda tag: False)
    config = types.SimpleNamespace(year=2024, get_aux=lambda key, default=None: default)
    return types.SimpleNamespace(config=config, dataset=dataset)


def load_skim_modules(case, task):
    import yaml
    with open(os.path.join(REPO, "config", SKIM_YAML[case] + ".yaml")) as f:
        conf = yaml.safe_load(f)                       # dicts keep the file order (py >= 3.7)
    mods = OrderedDict()
    for key, m in conf.items():
        if key == "bdtsf":
            continue                                    # BDT_SF = 1.0, not a weight (and clashes later)
        params = {}
        for p, v in (m.get("parameters") or {}).items():
            if isinstance(v, str) and "self" in v:
                v = eval(v, {}, {"self": task})        # as base.py:622
            params[p] = v
        mod = __import__(m["path"], fromlist=[m["name"]])
        mods[key] = getattr(mod, m["name"])(**params)()
    return mods


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=list(SKIM_YAML))
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--mc", action="store_true")
    ap.add_argument("--dir-ids", default="", help="data: CRAB-directory id of each input file (comma list)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-events", type=int, default=0, help="testing only")
    ap.add_argument("--min-bdt", type=float, default=LOOSE_BDT,
                    help="keep events with bdtA or bdtB1 above this (default: the loose region 0.6); "
                         "negative = no BDT cut (full preselected spectrum, for data-sideband BDT efficiencies)")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    dir_ids = [int(x) for x in a.dir_ids.split(",")] if a.dir_ids else []
    if dir_ids and len(dir_ids) != len(a.files):
        sys.exit("--dir-ids must have one entry per input file")

    sys.path[:0] = [REPO, os.environ.get("CMT_BASE", "")]
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.EnableImplicitMT(int(os.environ.get("NTHREADS", "1"))) if int(os.environ.get("NTHREADS", "1")) > 1 else None

    task = fake_task(a.dataset, a.mc)
    mods = load_skim_modules(a.case, task)
    for scen, (path, name) in BDT_MODULES.items():
        mod = __import__(path.format(case=a.case), fromlist=["DQCDULBDTNoJet"])
        mods["bdt_" + scen] = mod.DQCDULBDTNoJet(isMC=a.mc, year=2024, bdt_name=name)()

    chain = ROOT.TChain("Events")
    for f in a.files:
        chain.Add(f)
    df = ROOT.RDataFrame(chain)
    if a.max_events:
        df = df.Range(a.max_events)

    # PreCounter denominator (weights_2024.yaml: puWeight * filter_efficiency, no selection)
    n_raw = df.Count()
    if a.mc:
        df, _ = mods.pop("puweight").run(df)           # same producer/file as the skim's puweight
        sumw_raw = df.Sum("puWeight")
    else:
        mods.pop("puweight").run(df)                    # no-op for data, keeps the order honest
        sumw_raw = n_raw

    # CRAB task directory of each event's input file (data only): evaluated once per file by RDataFrame
    if dir_ids:
        expr = " : ".join(f'(rdfsampleinfo_.Contains("{f}") ? {i}' for f, i in zip(a.files, dir_ids))
        df = df.DefinePerSample("dirid", "(int) (" + expr + " : -1" + ")" * len(dir_ids) + ")")
    else:
        df = df.Define("dirid", "(int) -1")

    df = df.Define("selection", "event >= 0").Filter("selection", "base")   # base category
    for key, mod in mods.items():
        df, _ = mod.run(df)

    cat = " : ".join(f"({SINGLE} && {s}) ? {i + 1}" for i, s in enumerate(DXY_P))
    cat += " : " + " : ".join(f"({MULTI} && {s}) ? {i + 7}" for i, s in enumerate(DXY_P)) + " : 0"
    df = (df.Define("cat", cat)
            .Define("mass", "muonSV_bestchi2_mass")
            .Define("bdtA", "(float) bdt_scenarioA_onlymu")
            .Define("bdtB1", "(float) bdt_scenarioB1_onlymu")
            .Define("weight", "(float) puWeight" if a.mc else "1.f")
            .Define("lumi", "luminosityBlock")
            .Filter("cat > 0", "in a category")
            .Filter(DXYZ_CUT, "material + dz veto"))
    if a.min_bdt >= 0:
        df = df.Filter(f"bdtA > {a.min_bdt} || bdtB1 > {a.min_bdt}", "loose BDT")
    report = df.Report()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    tmp = a.out + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)                                  # leftover of a crashed job
    df.Snapshot("Events", tmp, ["mass", "cat", "bdtA", "bdtB1", "weight", "dirid", "run", "lumi", "event"])

    f = ROOT.TFile.Open(tmp, "UPDATE")
    t = ROOT.TTree("Norm", "PreCounter-like normalisation")
    import array
    nr, sw, nf = array.array("d", [0]), array.array("d", [0]), array.array("i", [0])
    files = ROOT.std.string(";".join(a.files))
    t.Branch("n_raw", nr, "n_raw/D"); t.Branch("sumw_raw", sw, "sumw_raw/D")
    t.Branch("n_files", nf, "n_files/I"); t.Branch("files", files)
    nr[0] = n_raw.GetValue(); sw[0] = float(sumw_raw.GetValue()); nf[0] = len(a.files)
    t.Fill(); t.Write(); f.Close()
    os.replace(tmp, a.out)
    report.Print()
    print(f"n_raw {nr[0]:.0f} sumw_raw {sw[0]:.2f} n_files {nf[0]} -> {a.out}")


if __name__ == "__main__":
    main()
