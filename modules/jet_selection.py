from Base.Modules.baseModules import JetLepMetSyst
from analysis_tools.utils import import_root
ROOT = import_root()

LOOSE = 1
TIGHT = 2
TIGHTLEPTONVETO = 4


class DQCDJetSelectionRDFProducer(JetLepMetSyst):
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2018)
        self.df_filter = kwargs.pop("filter", True)
        self.jet_id = kwargs.pop("jet_id", "loose")
        assert self.jet_id in ["loose", "tight", "tightleptonveto"]

        super(DQCDJetSelectionRDFProducer, self).__init__(*args, **kwargs)

        ROOT.gInterpreter.Declare("""
            using Vint = const ROOT::RVec<int>&;
            ROOT::RVec<int> globaljet_indexes(int nJet, Vint global_jetIdx) {
                ROOT::RVec<int> indexes(nJet, -1);
                for (size_t i = 0; i < global_jetIdx.size(); i++) {
                    if (global_jetIdx[i] >= 0)
                        indexes[global_jetIdx[i]] = i;
                }
                return indexes;
            }
            ROOT::RVec<int> get_global_int_element(Vint global_vec, Vint jet_global_indexes) {
                ROOT::RVec<int> values(jet_global_indexes.size(), -1);
                for (size_t i = 0; i < jet_global_indexes.size(); i++) {
                    if (jet_global_indexes[i] >= 0)
                        values[i] = global_vec[jet_global_indexes[i]];
                }
                return values;
            }
        """)

    def run(self, df):
        sel = [f"Jet_pt{self.jet_syst} > 15.", "abs(Jet_eta) < 2.4", "Jet_nConstituents >= 2",
            f"(Jet_pt{self.jet_syst} > 50 || Jet_puId >= 1)"]
        if self.year in [2017, 2018] and self.jet_id == "loose":
            self.jet_id = "tight"
        sel.append("Jet_jetId >= %s" % eval(self.jet_id.upper()))

        df = df.Define("Jet_globalIndexes", "globaljet_indexes(nJet, global_jetIdx)")
        df = df.Define("Jet_numberCpf", "get_global_int_element(global_numberCpf, Jet_globalIndexes)")
        df = df.Define("Jet_numberMuon", "get_global_int_element(global_numberMuon, Jet_globalIndexes)")
        df = df.Define("Jet_numberElectron", "get_global_int_element(global_numberElectron, Jet_globalIndexes)")

        df = df.Define("Jet_selected", " && ".join(sel))

        # filter by selected number of jets
        if self.df_filter:
            df = df.Filter(f"Jet_pt{self.jet_syst}[Jet_selected > 0].size() > 0")

        return df, ["Jet_numberCpf", "Jet_numberMuon", "Jet_numberElectron", "Jet_selected"]


def DQCDJetSelectionRDF(*args, **kwargs):
    return lambda: DQCDJetSelectionRDFProducer(*args, **kwargs)
