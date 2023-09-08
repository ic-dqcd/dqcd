from analysis_tools.utils import import_root
ROOT = import_root()

pathk = "/vols/cms/khl216/nano_out/nanotron_v3_bdt_0p9994_fixed_with_gen_match/bparkProductionAll_V1p0/HiddenValley_vector_m_2_ctau_10_xiO_1_xiL_1_privateMC_11X_NANOAODSIM_v1p0_generationSync/"
import os
filesk = os.listdir(pathk)
filesk.sort()

fj = "/vols/cms/jleonhol/cmt/PreprocessRDF/legacy_2018/m_2_ctau_10_xiO_1_xiL_1/cat_base/prod_0609_b/data_{}.root"


for ifk, fk in enumerate(filesk):
    print(fk)
    tfj = ROOT.TFile.Open(fj.format(ifk))
    tfk = ROOT.TFile.Open(pathk + fk)

    i = 0
    jetsj = []
    for ev in tfj.Events:
        jetsj.append((i, [elem for elem in ev.Jet_pt]))
        i += 1

    i = 0
    jetsk = []
    for ev in tfk.Friends:
        jetsk.append((i, [elem for elem in ev.Jet_pt]))
        i += 1

    for ev in jetsj:
        # print(ev)
        if ev not in jetsk:
            print(ev)
            break