import os
import law
import luigi

from cmt.base_tasks.base import DatasetTaskWithCategory, HTCondorWorkflow, SGEWorkflow, InputData
from cmt.base_tasks.preprocessing import PreprocessRDF

from analysis_tools.utils import create_file_dir, import_root

ROOT = import_root()

class PNetDataProducer(DatasetTaskWithCategory, law.LocalWorkflow, HTCondorWorkflow, SGEWorkflow):
    base_category_name = luigi.Parameter(default="base", description="the name of the "
        "base category with the initial selection, default: base")
    
    keys = ["px", "py", "pz", "e", "deta", "dphi", "logpt", "loge", "logptrel", "logerel",
        "dr", "q", "isElectron", "isMuon", "isChargedHadron",
        "isNeutralHadron", "isPhoton", "tanhdxy", "tanhdz", "dxyerror",
        "dzerror"]

    def create_branch_map(self):
        return len(self.dataset.get_files(
            os.path.expandvars("$CMT_TMP_DIR/%s/" % self.config_name), add_prefix=False,
            check_empty=True))

    def workflow_requires(self):
        return {"data": PreprocessRDF.vreq(self, category_name=self.base_category_name)}

    def requires(self):
        return PreprocessRDF.vreq(self, category_name=self.base_category_name,
            branch=self.branch)

    def output(self):
        return self.local_target(f"data_{self.branch}.root")

    def get_pnet_input_data(self, filename):
        import pandas
        import numpy as np
        import awkward as ak
        import uproot as up
        df = ROOT.RDataFrame("Events", filename)
        npy = df.AsNumpy()
        df = pandas.DataFrame(npy)
        
        d = {col: [] for col in self.keys if str(col) != "Jet_withMatchedMuon"}
        d["signal"] = []
        d["background"] = []

        for iev, ev in df.iterrows():
            for ijet, (matched, dark) in enumerate(
                    zip(ev["Jet_withMatchedMuon"], ev["Jet_fromDarkShower"])):
                if matched == 1:
                    jet = []
                    for ip, cpf_jetidx in enumerate(ev["cpf_jetIdx_sel"]):
                        if cpf_jetidx == ijet:
                            jet.append([
                                ev["cpf_px_sel"][ip], ev["cpf_py_sel"][ip],
                                ev["cpf_pz_sel"][ip], ev["cpf_e_sel"][ip],
                                ev["cpf_deta_sel"][ip], ev["cpf_dphi_sel"][ip],
                                ev["cpf_logpt_sel"][ip], ev["cpf_loge_sel"][ip],
                                ev["cpf_logptrel_sel"][ip], ev["cpf_logerel_sel"][ip],
                                ev["cpf_deltaR_sel"][ip], ev["cpf_charge_sel"][ip],
                                int(ev["cpf_isElectron_sel"][ip]), int(ev["cpf_isMuon_sel"][ip]),
                                int(ev["cpf_isChargedHadron_sel"][ip]), 0, 0,
                                ev["cpf_tanhdxy_sel"][ip], ev["cpf_tanhdz_sel"][ip],
                                ev["cpf_dxyError_sel"][ip], ev["cpf_dzError_sel"][ip],
                            ])

                    for ip, npf_jetidx in enumerate(ev["npf_jetIdx_sel"]):
                        if cpf_jetidx == ijet:
                            jet.append([
                                ev["npf_px_sel"][ip], ev["npf_py_sel"][ip],
                                ev["npf_pz_sel"][ip], ev["npf_e_sel"][ip],
                                ev["npf_deta_sel"][ip], ev["npf_dphi_sel"][ip],
                                ev["npf_logpt_sel"][ip], ev["npf_loge_sel"][ip],
                                ev["npf_logptrel_sel"][ip], ev["npf_logerel_sel"][ip],
                                ev["npf_deltaR_sel"][ip], 0,
                                0, 0, 0,
                                int(ev["npf_isNeutralHadron_sel"][ip]),
                                int(ev["npf_isGamma_sel"][ip]),
                                -999, -999,
                                -999, -999,
                            ])
                    if len(jet) == 0:
                        continue

                    d["signal"].append(dark)
                    d["background"].append(1 - dark)
                    # d.append({"signal": dark})
                    jet.sort(key=lambda x: x[3], reverse=True)
                    for ikey, key in enumerate(self.keys):
                        d[key].append(np.array(
                            # [elem[ikey] for elem in jet] + [0. for i in range(200 - len(jet))],
                            [elem[ikey] for elem in jet],
                            dtype=np.float64))
        return d

    def run(self):
        d = self.get_pnet_input_data(self.input().path)
        f = up.recreate(create_file_dir(self.output().path))
        f["Events"] = {"signal": d["signal"], "background": d["background"],
            "Part": ak.zip({key: d[key] for key in self.keys})}
