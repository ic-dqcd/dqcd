from analysis_tools.utils import import_root
ROOT = import_root()

class DQCDMuonSelectionRDFProducer():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2018)

        ROOT.gInterpreter.Declare("""
            #include "DataFormats/Math/interface/deltaR.h"
            using Vint = const ROOT::RVec<int>&;
            using Vfloat = const ROOT::RVec<float>&;
            ROOT::RVec<int> match_col1_col2(Vfloat pt1, Vfloat eta1, Vfloat phi1,
                    Vfloat pt2, Vfloat eta2, Vfloat phi2, float max_dpt, float max_dr) {
                ROOT::RVec<int> matching(eta1.size(), -1);
                for (auto i = 0; i < eta1.size(); i++) {
                    float min_dR = 999;
                    int min_dR_index = -1;
                    for (auto j = 0; j < eta2.size(); j++) {
                        auto dR = reco::deltaR(eta1[i], phi1[i], eta2[j], phi2[j]);
                        if (dR < max_dr && dR < min_dR && fabs((pt2[j] / pt1[i]) - 1) < max_dpt) {
                            min_dR = dR;
                            min_dR_index = j;
                        }
                    }
                    matching[i] = min_dR_index;
                }
                return matching;
            }
            std::vector<ROOT::RVec<int>> get_leading_elems(Vfloat vec) {
                ROOT::RVec<int> leading(vec.size(), 0);
                ROOT::RVec<int> subleading(vec.size(), 0);
                int lead_index = -1;
                int sublead_index = -1;
                float lead_value = -999.;
                float sublead_value = -999.;
                for (size_t i = 0; i < vec.size(); i++) {
                    if (vec[i] > lead_value) {
                        sublead_value = lead_value;
                        lead_value = vec[i];
                        sublead_index = lead_index;
                        sublead_index = i;
                    } else if (vec[i] > sublead_value) {
                        sublead_value = vec[i];
                        sublead_index = i;
                    }
                }
                if (lead_index != -1) {
                    leading[lead_index] = 1;
                }
                if (sublead_index != -1) {
                    subleading[sublead_index] = 1;
                }
                return {leading, subleading};
            }
        """)

    def run(self, df):
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 9.) && (abs(MuonBPark_eta) < 1.5 && abs(MuonBPark_sip3d) > 6.)""")

        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        #df = df.Filter("All(MuonBPark_isLooseMuon == 1)", "ALL muons in the event are loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isMuonWithEtaAndPtReq == 1].size() > 0", ">= 1 muon with pt and eta req")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringMuon == 1].size() > 0", ">= 1 triggering muon")

        # trigger flag
        if self.year == 2018:
            df = df.Define("DisplacedMuonTrigger_flag", " || ".join([
                "HLT_Mu9_IP6_part0",
                "HLT_Mu9_IP6_part1",
                "HLT_Mu9_IP6_part2",
                "HLT_Mu9_IP6_part3",
                "HLT_Mu9_IP6_part4",
                "HLT_Mu7_IP4_part0",
                "HLT_Mu7_IP4_part1",
                "HLT_Mu7_IP4_part2",
                "HLT_Mu7_IP4_part3",
                "HLT_Mu7_IP4_part4",
                "HLT_Mu8_IP3_part0",
                "HLT_Mu8_IP3_part1",
                "HLT_Mu8_IP3_part2",
                "HLT_Mu8_IP3_part3",
                "HLT_Mu8_IP3_part4",
                "HLT_Mu8_IP5_part0",
                "HLT_Mu8_IP5_part1",
                "HLT_Mu8_IP5_part2",
                "HLT_Mu8_IP5_part3",
                "HLT_Mu8_IP5_part4",
                "HLT_Mu8_IP6_part0",
                "HLT_Mu8_IP6_part1",
                "HLT_Mu8_IP6_part2",
                "HLT_Mu8_IP6_part3",
                "HLT_Mu8_IP6_part4",
                "HLT_Mu9_IP4_part0",
                "HLT_Mu9_IP4_part1",
                "HLT_Mu9_IP4_part2",
                "HLT_Mu9_IP4_part3",
                "HLT_Mu9_IP4_part4",
                "HLT_Mu9_IP5_part0",
                "HLT_Mu9_IP5_part1",
                "HLT_Mu9_IP5_part2",
                "HLT_Mu9_IP5_part3",
                "HLT_Mu9_IP5_part4",
                "HLT_Mu12_IP6_part0",
                "HLT_Mu12_IP6_part1",
                "HLT_Mu12_IP6_part2",
                "HLT_Mu12_IP6_part3",
                "HLT_Mu12_IP6_part4"
            ]))
        
        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", """match_col1_col2(
        #     MuonBPark_pt, MuonBPark_eta, MuonBPark_phi,
        #     cpf_pt, cpf_eta, cpf_phi,
        #     0.1, 0.02)""")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)").Define(
            "MuonBPark_isLeading", "leading[0]").Define("MuonBPark_isSubleading", "leading[1]")

        # match to trigger muons
        # trigger matched
        df = df.Define("MuonBPark_trigger_matched", """(MuonBPark_isTriggeringMuon > 0) &&
            (MuonBPark_isTriggering > 0) && 
            (MuonBPark_fired_HLT_Mu9_IP6 > 0 || MuonBPark_fired_HLT_Mu7_IP4 > 0 || MuonBPark_fired_HLT_Mu8_IP3 > 0 || MuonBPark_fired_HLT_Mu8_IP5 > 0 || MuonBPark_fired_HLT_Mu8_IP6 > 0 || MuonBPark_fired_HLT_Mu9_IP4 > 0 || MuonBPark_fired_HLT_Mu9_IP5 > 0 || MuonBPark_fired_HLT_Mu12_IP6 > 0)""")
        df = df.Filter("MuonBPark_pt[MuonBPark_trigger_matched > 0].size() > 0", ">= 1 trigger-matched muon")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 1.5""")

        return df, ["MuonBPark_isLooseMuon", "MuonBPark_isTriggeringMuon",
            "MuonBPark_isMuonWithEtaAndPtReq",
            #"MuonBPark_isMuonWithEtaAndPtReq", "MuonBPark_cpf_match",
            "MuonBPark_isLeading", "MuonBPark_isSubleading",
            "MuonBPark_trigger_matched", "MuonBPark_isMuonWithTighterEtaAndPtReq"]


def DQCDMuonSelectionRDF(*args, **kwargs):
    return lambda: DQCDMuonSelectionRDFProducer(*args, **kwargs)
