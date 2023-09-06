from analysis_tools.utils import import_root
ROOT = import_root()

LOOSE = 1
TIGHT = 2
TIGHTLEPTONVETO = 4


class DQCDJetSelectionRDFProducer():
    def __init__(self, *args, **kwargs): 
        self.year = kwargs.pop("year", 2018)
        self.jet_id = kwargs.pop("jet_id", "loose")
        assert self.jet_id in ["loose", "tight", "tightleptonveto"]

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
        sel = ["Jet_pt > 15.", "abs(Jet_eta) < 2.4", "Jet_nConstituents >= 2"]
        if self.year in [2017, 2018] and self.jet_id == "loose":
            self.jet_id = "tight"
        sel.append("Jet_jetId >= %s" % eval(self.jet_id.upper()))
        
        df = df.Define("Jet_globalIndexes", "globaljet_indexes(nJet, global_jetIdx)")       
        df = df.Define("Jet_numberCpf", "get_global_int_element(global_numberCpf, Jet_globalIndexes)")
        df = df.Define("Jet_numberMuon", "get_global_int_element(global_numberMuon, Jet_globalIndexes)")
        df = df.Define("Jet_numberElectron", "get_global_int_element(global_numberElectron, Jet_globalIndexes)")

        df = df.Define("Jet_selected", " && ".join(sel))

        # filter by selected number of jets
        df = df.Filter("Jet_pt[Jet_selected > 0].size() > 0")

        return df, ["Jet_numberCpf", "Jet_numberMuon", "Jet_numberElectron"]


def DQCDJetSelectionRDF(*args, **kwargs):
    return lambda: DQCDJetSelectionRDFProducer(*args, **kwargs)