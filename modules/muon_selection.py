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


class DQCDMuonSelection2024RDFProducer():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)

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

    # TODO must modify pT thresholds to match 2024 triggers
    def run(self, df):
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon",
            "(MuonBPark_looseId == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq",
            "(MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)")
        df = df.Define("MuonBPark_isTriggeringSingleMuon",
            "(MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 9.) && (abs(MuonBPark_eta) < 1.5 && abs(MuonBPark_sip3d) > 6.)")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 1.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 1.5 && abs(MuonBPark_sip3d) > 6.))
                """)

        # filtering
        #TODO these may not be useful. Remnants of the original class, to be deleted once confirmed their uselessness
        #df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        ##df = df.Filter("All(MuonBPark_isLooseMuon == 1)", "ALL muons in the event are loose muon")
        #df = df.Filter("MuonBPark_pt[MuonBPark_isMuonWithEtaAndPtReq == 1].size() > 0", ">= 1 muon with pt and eta req")
        #df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon == 1].size() > 0", ">= 1 triggering muon")

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # single-muon displaced triggers
            df = df.Define("SingleMuonTrigger_flag", " || ".join([
                "HLT_Mu10_Barrel_L1HP11_IP6",
                "HLT_Mu9_Barrel_L1HP10_IP6",
                "HLT_Mu8_Barrel_L1HP9_IP6",
                "HLT_Mu7_Barrel_L1HP8_IP6",
                "HLT_Mu6_Barrel_L1HP7_IP6",
                "HLT_Mu0_Barrel_L1HP6_IP6",
                "HLT_Mu0_Barrel_L1HP11",
                "HLT_Mu0_Barrel",
                "HLT_Mu0_Barrel_L1HP10",
                "HLT_Mu0_Barrel_L1HP9",
                "HLT_Mu0_Barrel_L1HP8",
                "HLT_Mu0_Barrel_L1HP7",
                "HLT_Mu0_Barrel_L1HP6"
            ]))

            # double-muon displaced triggers
            df = df.Define("DoubleMuonTrigger_flag", " || ".join([
                "HLT_DoubleMu4_3_LowMass",
                "HLT_DoubleMu4_LowMass_Displaced"
            ]))

            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")

        # single-muon: require >= 1 muon with pT > 10 and |eta| < 1.5
        #TODO adjust thresholds better (?)
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 10. && abs(MuonBPark_eta) < 1.5) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV)
        #TODO adjust thresholds better (?)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # overall selection-based pass
        df = df.Filter("MuonBPark_passSingleMuonSel || MuonBPark_passDoubleMuonSel",
                       "Pass muon pT/eta cuts matching trigger")

        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass displaced muon trigger")

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

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 10. && abs(MuonBPark_eta) < 1.5")

        # Double-muon-style lower and asymmetric cuts (per-muon flag)
        df = df.Define("MuonBPark_passDoubleMuonLike", """MuonBPark_isLooseMuon == 1 &&
            (
              (MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) ||
              (MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4)
            )
        """)


        # match to trigger muons
        # for 2024, we want:
        #    - single-muon triggers to require at least 1 trigger-matched muon
        #    - double-muon triggers to require at least 2 trigger0matched muons
        # trigger matched
        # per-muon matching
        df = df.Define("MuonBPark_SingleMuon_trigger_matched", """
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            (
                MuonBPark_fired_HLT_Mu10_Barrel_L1HP11_IP6_V > 0 ||
                MuonBPark_fired_HLT_Mu9_Barrel_L1HP10_IP6_v > 0 ||
                MuonBPark_fired_HLT_Mu8_Barrel_L1HP9_IP6_v > 0 ||
                MuonBPark_fired_HLT_Mu7_Barrel_L1HP8_IP6_v > 0 ||
                MuonBPark_fired_HLT_Mu6_Barrel_L1HP7_IP6_V > 0 ||
                MuonBPark_fired_HLT_MuO_Barrel_L1HP6_IP6_v > 0 ||
                MuonBPark_fired_HLT_MuO_Barrel_L1HP11_v > 0 ||
                MuonBPark_fired_HLT_MuO_BarreLv > 0 ||
                MuonBPark_fired_HLT_MuO_Barrel_L1HP10_v > 0 ||
                MuonBPark_fired_HLT_Muo_Barrel_L1HP9_v > 0 ||
                MuonBPark_fired_HLT_MuO_Barrel_L1HP8_v > 0 ||
                MuonBPark_fired_HLT_MuO_Barrel_L1HP7_v > 0 ||
                MuonBPark_fired_HLT_MuO_Barrel_L1HP6_v > 0
            )
        """)
#TODO SingleMuon triggers seem to have typos...
# The lines above are typo-consistent
# To change eventually for the folloring (corrected) list
#                MuonBPark_fired_HLT_Mu10_Barrel_L1HP11_IP6_V > 0 ||
#                MuonBPark_fired_HLT_Mu9_Barrel_L1HP10_IP6_V > 0 ||
#                MuonBPark_fired_HLT_Mu8_Barrel_L1HP9_IP6_V > 0 ||
#                MuonBPark_fired_HLT_Mu7_Barrel_L1HP8_IP6_V > 0 ||
#                MuonBPark_fired_HLT_Mu6_Barrel_L1HP7_IP6_V > 0 ||
#                MuonBPark_fired_HLT_Mu0_Barrel_L1HP6_IP6_V > 0 ||
#                MuonBPark_fired_HLT_Mu0_Barrel_L1HP11_V > 0 ||
#                MuonBPark_fired_HLT_Mu0_Barrel_V > 0 ||
#                MuonBPark_fired_HLT_Mu0_Barrel_L1HP10_V > 0 ||
#                MuonBPark_fired_HLT_Mu0_Barrel_L1HP9_V > 0 ||
#                MuonBPark_fired_HLT_Mu0_Barrel_L1HP8_V > 0 ||
#                MuonBPark_fired_HLT_Mu0_Barrel_L1HP7_V > 0 ||
#                MuonBPark_fired_HLT_Mu0_Barrel_L1HP6_V > 0

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", """
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            (
                MuonBPark_fired_HLT_DoubleMu4_3_LowMass > 0 ||
                MuonBPark_fired_HLT_DoubleMu4_LowMass_Displaced > 0
            )
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # TODO may need to remove since below I definve a filter taking into cosideration priority ordering. To be checked
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matching requirement")

        #df = df.Filter("MuonBPark_pt[MuonBPark_trigger_matched > 0].size() > 0", ">= 1 trigger-matched muon") #TODO not needed anymore (?) -> now split into MuonBPark_SingleMuon_trigger_matched and MuonBPark_DoubleMuon_trigger_matched

        # mutually-exclusive categories
        #     priority 1: single-muon category (harder trigger, higher pt threhsholds). N.B. many less single-muon than double-muons
        #     priority 2: double-muon category (only gets events not taken by the single-muon category)
        # TODO may need to check priority order or if we want them mutually exclussive even
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuonExclusive",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuonExclusive",
            "(!passSingleMuonExclusive) && MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        # filter taking into cosideration priority ordering
        df = df.Filter("passSingleMuonExclusive || passDoubleMuonExclusive",
            "Pass trigger-matching with priority")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 1.5""")

        return df, [
            # per-muon flags
            "MuonBPark_isLooseMuon",
            "MuonBPark_isTriggeringSingleMuon",
            "MuonBPark_isTriggeringDoubleMuon",
            "MuonBPark_isMuonWithEtaAndPtReq",
            #"MuonBPark_isMuonWithEtaAndPtReq", "MuonBPark_cpf_match",
            "MuonBPark_isLeading",
            "MuonBPark_isSubleading",
            "MuonBPark_SingleMuon_trigger_matched",
            "MuonBPark_DoubleMuon_trigger_matched",
            "MuonBPark_isMuonWithTighterEtaAndPtReq",
            "MuonBPark_passSingleMuonLike",
            "MuonBPark_passDoubleMuonLike",

            # trigger flags
            "SingleMuonTrigger_flag",
            "DoubleMuonTrigger_flag",
            "DisplacedMuonTrigger_flag",

            # event-level selections
            "MuonBPark_passSingleMuonSel",
            "MuonBPark_passDoubleMuonSel",
            "MuonBPark_passSingleMuonMatch",
            "MuonBPark_passDoubleMuonMatch",

            # mutually-exclusive priority-based categories
            "passSingleMuonExclusive",
            "passDoubleMuonExclusive"
        ]


def DQCDMuonSelectionRDF(*args, **kwargs):
    return lambda: DQCDMuonSelectionRDFProducer(*args, **kwargs)

def DQCDMuonSelection2024RDF(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer(*args, **kwargs)
