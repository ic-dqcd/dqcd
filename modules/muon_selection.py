from analysis_tools.utils import import_root
ROOT = import_root()


# UL 2018 class
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
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

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


#1 -> SingleMuon: HLT_Mu10_Barrel_L1HP11_IP6
class DQCDMuonSelection2024RDFProducer_HLT_Mu10_Barrel_L1HP11_IP6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                ### >>> NO SEED ACTIVE -- this class does not use the double-muon trigger <<<
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),   # [84.5%] stable all year
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),   # [61.0%] stable all year
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),   # [60.5%] stable all year
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),   # [34.7%] off in F-v2, H-v1
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),   # [32.4%] off in F-v2, H-v1
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),  # [24.0%]
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),  # [15.4%] on from era E
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",    0.0, 1.4),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "SingleMuonTrigger_flag") # Triggering only on HLT_Mu10_Barrel_L1HP11_IP6
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            #"HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_HLT_Mu10_Barrel_L1HP11_IP6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_HLT_Mu10_Barrel_L1HP11_IP6(*args, **kwargs)


#2 -> SingleMuon: HLT_Mu9_Barrel_L1HP10_IP6
class DQCDMuonSelection2024RDFProducer_HLT_Mu9_Barrel_L1HP10_IP6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            ("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                ### >>> NO SEED ACTIVE -- this class does not use the double-muon trigger <<<
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),   # [84.5%] stable all year
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),   # [61.0%] stable all year
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),   # [60.5%] stable all year
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),   # [34.7%] off in F-v2, H-v1
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),   # [32.4%] off in F-v2, H-v1
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),  # [24.0%]
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),  # [15.4%] on from era E
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",    0.0, 1.4),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "SingleMuonTrigger_flag") # Triggering only on HLT_Mu9_Barrel_L1HP10_IP6
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            #"HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_HLT_Mu9_Barrel_L1HP10_IP6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_HLT_Mu9_Barrel_L1HP10_IP6(*args, **kwargs)


#3 -> SingleMuon: HLT_Mu8_Barrel_L1HP9_IP6
class DQCDMuonSelection2024RDFProducer_HLT_Mu8_Barrel_L1HP9_IP6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            ("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                ### >>> NO SEED ACTIVE -- this class does not use the double-muon trigger <<<
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),   # [84.5%] stable all year
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),   # [61.0%] stable all year
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),   # [60.5%] stable all year
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),   # [34.7%] off in F-v2, H-v1
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),   # [32.4%] off in F-v2, H-v1
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),  # [24.0%]
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),  # [15.4%] on from era E
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",    0.0, 1.4),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "SingleMuonTrigger_flag") # Triggering only on HLT_Mu8_Barrel_L1HP9_IP6
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            #"HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_HLT_Mu8_Barrel_L1HP9_IP6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_HLT_Mu8_Barrel_L1HP9_IP6(*args, **kwargs)


#4 -> SingleMuon: HLT_Mu7_Barrel_L1HP8_IP6
class DQCDMuonSelection2024RDFProducer_HLT_Mu7_Barrel_L1HP8_IP6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            ("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                ### >>> NO SEED ACTIVE -- this class does not use the double-muon trigger <<<
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),   # [84.5%] stable all year
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),   # [61.0%] stable all year
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),   # [60.5%] stable all year
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),   # [34.7%] off in F-v2, H-v1
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),   # [32.4%] off in F-v2, H-v1
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),  # [24.0%]
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),  # [15.4%] on from era E
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",    0.0, 1.4),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "SingleMuonTrigger_flag") # Triggering only on HLT_Mu7_Barrel_L1HP8_IP6
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            #"HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_HLT_Mu7_Barrel_L1HP8_IP6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_HLT_Mu7_Barrel_L1HP8_IP6(*args, **kwargs)


#5 -> SingleMuon: HLT_Mu6_Barrel_L1HP7_IP6
class DQCDMuonSelection2024RDFProducer_HLT_Mu6_Barrel_L1HP7_IP6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            ("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                ### >>> NO SEED ACTIVE -- this class does not use the double-muon trigger <<<
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),   # [84.5%] stable all year
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),   # [61.0%] stable all year
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),   # [60.5%] stable all year
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),   # [34.7%] off in F-v2, H-v1
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),   # [32.4%] off in F-v2, H-v1
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),  # [24.0%]
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),  # [15.4%] on from era E
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",    0.0, 1.4),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "SingleMuonTrigger_flag") # Triggering only on HLT_Mu6_Barrel_L1HP7_IP6
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            #"HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_HLT_Mu6_Barrel_L1HP7_IP6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_HLT_Mu6_Barrel_L1HP7_IP6(*args, **kwargs)


#8 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (inclusive, no L1 seed requirement)
class DQCDMuonSelection2024RDFProducer_HLT_DoubleMu4_3_LowMass():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                ### >>> NO SEED ACTIVE -- inclusive double-muon HLT, no L1 seed requirement <<<
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),   # [84.5%] stable all year
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),   # [61.0%] stable all year
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),   # [60.5%] stable all year
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),   # [34.7%] off in F-v2, H-v1
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),   # [32.4%] off in F-v2, H-v1
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),  # [24.0%]
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),  # [15.4%] on from era E
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",    0.0, 1.4),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            # INCLUSIVE DoubleMu: only the raw HLT bit is required. The
            # doubleMuon__l1_conditions list above and doubleMuon__inner_or built from it are
            # therefore UNUSED in this class -- reading the list is NOT evidence that the seeds
            # are applied. They are kept for the per-seed contributions they record and so that
            # re-enabling the seeded version is a one-line swap below.
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass)"       # Inclusive: only dominant double-mu HLT path, NO L1 seed requirement
                #f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_HLT_DoubleMu4_3_LowMass(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_HLT_DoubleMu4_3_LowMass(*args, **kwargs)


#16 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                ("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2(*args, **kwargs)


#17 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                ("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),   # [84.5%] stable all year
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),   # [61.0%] stable all year
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),   # [60.5%] stable all year
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),   # [34.7%] off in F-v2, H-v1
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),   # [32.4%] off in F-v2, H-v1
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),  # [24.0%]
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),  # [15.4%] on from era E
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",    0.0, 1.4),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6(*args, **kwargs)


#18 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu5_SQ_OS_dR_Max1p6)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu5_SQ_OS_dR_Max1p6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                ("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu5_SQ_OS_dR_Max1p6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu5_SQ_OS_dR_Max1p6(*args, **kwargs)


#19 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                ("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6(*args, **kwargs)


#20 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                ("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2(*args, **kwargs)


#21 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                ("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6(*args, **kwargs)


#22 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                ("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6(*args, **kwargs)


#23 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                ("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5(*args, **kwargs)


#24 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                ("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4(*args, **kwargs)


#25 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                ("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4(*args, **kwargs)


#27 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu4p5_SQ_OS_dR_Max1p2)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu4p5_SQ_OS_dR_Max1p2():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                ("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu4p5_SQ_OS_dR_Max1p2(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu4p5_SQ_OS_dR_Max1p2(*args, **kwargs)


#28 -> DoubleMuon: HLT_DoubleMu4_3_LowMass (L1_DoubleMu4_SQ_OS_dR_Max1p2)
class DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu4_SQ_OS_dR_Max1p2():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            #("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2", 0.0, 1.4),
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),
                ("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "DoubleMuonTrigger_flag") # Triggering only on HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_DoubleMuon_L1_DoubleMu4_SQ_OS_dR_Max1p2(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_DoubleMuon_L1_DoubleMu4_SQ_OS_dR_Max1p2(*args, **kwargs)



#=== combined single+double (Mu10 || DoubleMu) producer ===
#     -> SingleMuon || DoubleMuon: HLT_Mu10_Barrel_L1HP11_IP6 || HLT_DoubleMu4_3_LowMass (inclusive, no L1 seed requirement)
class DQCDMuonSelection2024RDFProducer_Mu10orDoubleMu():
    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop("year", 2024)
        self.isMC = kwargs.pop("isMC", False)
        self.veto_single_muon = kwargs.pop("veto_single_muon", False)

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
        # per-muon definitions
        df = df.Define("MuonBPark_isLooseMuon", """(MuonBPark_looseId == 1) &&
            (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5)""")
        df = df.Define("MuonBPark_isMuonWithEtaAndPtReq", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 2.4)""")
        df = df.Define("MuonBPark_isTriggeringSingleMuon", """(MuonBPark_isLooseMuon == 1) &&
            (MuonBPark_pt > 5.) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)""")
        df = df.Define("MuonBPark_isTriggeringDoubleMuon",
            """((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 4.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.)) ||
               ((MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > 3.) && (abs(MuonBPark_eta) < 2.5 && abs(MuonBPark_sip3d) > 6.))
                """)


        # filtering
        df = df.Filter("MuonBPark_pt[MuonBPark_isLooseMuon == 1].size() > 0", ">= 1 loose muon")
        df = df.Filter("MuonBPark_pt[MuonBPark_isTriggeringSingleMuon].size() > 0 || MuonBPark_pt[MuonBPark_isTriggeringDoubleMuon].size() > 1", ">= 1(2) muon(s) with pt and eta trig. req(s)")

        # Single-muon HLT paths used by THIS class. Single source of truth: it builds SingleMuonTrigger_flag below AND the trigger matching further down, so the two can never drift apart.
        # Comment a line out to drop that path.
        # The HLT_Mu0_Barrel* paths were removed (2026-08-05): every one of them is heavily prescaled and contributes negligibly.
        singleMuon__hlt_conditions = [
            ### (HLT_name, offline pt_cut)
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Overlap veto. ParkingSingleMuon and ParkingDoubleMuonLowMass are two separate data samples, but an event firing both a single- and a double-muon parking trigger is written into BOTH, so running over the two double-counts it. When veto_single_muon is set (data only) this class drops the events the SingleMuon run would already have selected, making the two samples disjoint by construction.
        # This list is deliberately SEPARATE from singleMuon__hlt_conditions above: that one answers "what does this class trigger on" (correctly empty for a double-muon class), while this one must MIRROR the singleMuon__hlt_conditions of whatever config you run on ParkingSingleMuon.
        pdVeto__hlt_conditions = [
            ### (HLT_name, offline pt_cut) -- keep in step with the SingleMuon config
            ("HLT_Mu10_Barrel_L1HP11_IP6", 10.0),
            #("HLT_Mu9_Barrel_L1HP10_IP6",   9.0),
            #("HLT_Mu8_Barrel_L1HP9_IP6",    8.0),
            #("HLT_Mu7_Barrel_L1HP8_IP6",    7.0),
            #("HLT_Mu6_Barrel_L1HP7_IP6",    6.0),
        ]

        # Ownership list: which HLT paths put an event into the ParkingSingleMuon data sample. Used by the "ownership" veto mode. Only the dominant path HLT_Mu10_Barrel_L1HP11_IP6 is used: the non-dominant single-muon paths are not of interest here, and the heavily prescaled HLT_Mu0_Barrel* ones contribute 4 of 16939 events (0.02%) on the 1% data sample.
        pdVeto__ownership_paths = [
            "HLT_Mu10_Barrel_L1HP11_IP6",
            #"HLT_Mu9_Barrel_L1HP10_IP6",
            #"HLT_Mu8_Barrel_L1HP9_IP6",
            #"HLT_Mu7_Barrel_L1HP8_IP6",
            #"HLT_Mu6_Barrel_L1HP7_IP6",
        ]

        # trigger flags
        # separating into single- and double-muon triggers
        if self.year == 2024:

            # Single-muon triggers
            # "false" fallback: with every path commented out the join is empty, and an empty Define expression is a C++ error ("cannot form a reference to 'void'").
            singleMuon__or = " || ".join(
                f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && "
                f"(abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
                for p, pt in singleMuon__hlt_conditions) or "false"

            df = df.Define("SingleMuonTrigger_flag", singleMuon__or)



            # Double-muon displaced triggers

            #    For 2024, HLT_DoubleMu4_3_LowMass and HLT_DoubleMu4_LowMass_Displaced have the same seeds
            #    Define an array with the L1 seeds of each of the DoubleMuon triggers, along with the pt and era requirements
            doubleMuon__l1_conditions = [
                ### (L1_name, pt_cut, eta_cut)
                ### >>> NO SEED ACTIVE -- inclusive double-muon HLT, no L1 seed requirement <<<
                #("L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",      3.0, 2.0),   # [84.5%] stable all year
                #("L1_DoubleMu4p5_SQ_OS_dR_Max1p2",         3.5, 2.4),   # [61.0%] stable all year
                #("L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",      0.0, 1.4),   # [60.5%] stable all year
                #("L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",      2.0, 2.0),   # [34.7%] off in F-v2, H-v1
                #("L1_DoubleMu4_SQ_OS_dR_Max1p2",           3.0, 2.4),   # [32.4%] off in F-v2, H-v1
                #("L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",      0.0, 1.5),  # [24.0%]
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",    0.0, 2.0),  # [15.4%] on from era E
                #("L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",    0.0, 1.4),
                #("L1_DoubleMu5_SQ_OS_dR_Max1p6",           4.0, 2.4),
                #("L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",    0.0, 1.5),
                #("L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",    0.0, 2.0),
                #("L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",    0.0, 1.4),
            ]

            # build per-L1 clause that requires at least one MuonBPark muon to satisfy the cuts (i.e. Sum() > 0 )
            doubleMuon__per_l1_exprs = []
            for (l1, pt_cut, eta_cut) in doubleMuon__l1_conditions:
                # include MuonBPark_isLooseMuon == 1 as requested
                cond = (
                    f"(({l1}) && (Sum((MuonBPark_isLooseMuon == 1) && "
                    f"(MuonBPark_pt > {pt_cut:.1f}) && (abs(MuonBPark_eta) < {eta_cut:.1f}) && "
                    f"(abs(MuonBPark_sip3d) > 6.)) > 0))"
                )
                doubleMuon__per_l1_exprs.append(cond)

            # inner OR of all L1 clauses
            # "false" fallback: with every seed commented out the join is empty, and "HLT_... && ()" is a C++ syntax error. "false" means "no L1 seed accepted".
            doubleMuon__inner_or = " || ".join(doubleMuon__per_l1_exprs) or "false"

            # now build full DoubleMuon HLT expression: HLT_DoubleMu4_3_LowMass && (doubleMuon__inner_or)  OR HLT_DoubleMu4_LowMass_Displaced && (doubleMuon__inner_or)
            #     N.B. HLT_DoubleMu4_LowMass_Displaced is a subset of HLT_DoubleMu4_3_LowMass
            #
            # INCLUSIVE DoubleMu: the L1 seed requirement is deliberately NOT applied here --
            # only the raw HLT bit is required, matching
            # DQCDMuonSelection2024RDFProducer_HLT_DoubleMu4_3_LowMass. The
            # doubleMuon__l1_conditions list above and doubleMuon__inner_or built from it are
            # therefore UNUSED in this class; they are kept because the per-seed contributions
            # they record are the reference for the per-seed studies, and to make re-enabling
            # the seeded version a one-line swap below.
            expr = (
                "("
                f"(HLT_DoubleMu4_3_LowMass)"       # Inclusive: only dominant double-mu HLT path, NO L1 seed requirement
                #f"(HLT_DoubleMu4_3_LowMass && ({doubleMuon__inner_or}))"       # Only dominant double-mu HLT path, only relevant L1 seeds
                #f"(HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced ) && ({doubleMuon__inner_or})"       # Both double-mu HLT paths (N.B. Displaced is a subset off HLT_DoubleMu4_3_LowMass), only relevant L1 seeds
                ")"
            )

            # debug print to inspect final expression
            #print("DoubleMuonTrigger_flag expression:\n", expr)

            # define double muon trigger flag
            df = df.Define("DoubleMuonTrigger_flag", expr)


            # combine in a general "pass trigger" filter
            df = df.Define("DisplacedMuonTrigger_flag",
               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag") # Triggering on HLT_Mu10_Barrel_L1HP11_IP6 || HLT_DoubleMu4_3_LowMass
#               "SingleMuonTrigger_flag || DoubleMuonTrigger_flag")


        df = df.Filter("DisplacedMuonTrigger_flag > 0", "Pass trigger(s)")

        # Rebuild the SingleMuon run's FULL selection (trigger flag AND offline kinematics AND trigger matching) so the veto is the exact complement of what that run keeps. A trigger-level veto would instead drop events that fire both triggers but fail the single-muon selection, losing them from both samples.
        pdVeto__or = " || ".join(
            f"(({p}) && ( Sum( (MuonBPark_isLooseMuon == 1) && (MuonBPark_pt > {pt:.1f}) && (abs(MuonBPark_eta) < 0.8 && abs(MuonBPark_sip3d) > 6.)) > 0 ))"
            for p, pt in pdVeto__hlt_conditions) or "false"
        pdVeto__matched_or = " || ".join(
            f"MuonBPark_fired_{p} > 0" for p, _ in pdVeto__hlt_conditions) or "false"

        df = df.Define("pdVeto_SingleMuonTrigger_flag", pdVeto__or)
        df = df.Define("MuonBPark_pdVeto_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({pdVeto__matched_or})
        """)
        df = df.Define("pdVeto_passSingleMuon",
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1) && "
            "(pdVeto_SingleMuonTrigger_flag && Sum(MuonBPark_pdVeto_SingleMuon_trigger_matched) >= 1)")
        # Mu8/Mu7/Mu6 only entered the menu in the later eras (they are absent from the Run2024C/D nanoAOD), so build the OR from the paths actually present in this file. A path that does not exist in an era cannot have fired in it, so dropping it is exact, not an approximation.
        pdVeto__available = set(str(c) for c in df.GetColumnNames())
        pdVeto__ownership_or = " || ".join(
            q for q in pdVeto__ownership_paths if q in pdVeto__available) or "false"
        df = df.Define("pdVeto_firedSingleMuon", pdVeto__ownership_or)

        # Both flags are always computed so the overlap can be measured without applying a cut, and neither is ever applied to MC: MC is not split into these two samples, so vetoing there would simply delete signal events that fire both triggers.
        # Which flag to cut on depends on how the two data samples are processed. "selection": each data sample is run with its OWN category config, so the veto must be the complement of the other run's selection -> pdVeto_passSingleMuon. "ownership": BOTH data samples are run with the SAME (combined) config, so which sample an event belongs to is decided by the raw HLT bits -> pdVeto_firedSingleMuon; a selection-based veto would leak events that fired a single-muon path but fail our offline single-muon selection.
        veto_mode = self.veto_single_muon
        if veto_mode is True:
            veto_mode = "selection"
        elif not veto_mode:
            veto_mode = ""
        if veto_mode not in ("", "selection", "ownership"):
            raise ValueError('veto_single_muon must be False, "selection" or "ownership", got %r' % (self.veto_single_muon,))
        if veto_mode and not self.isMC:
            df = df.Filter("!pdVeto_passSingleMuon" if veto_mode == "selection" else "!pdVeto_firedSingleMuon",
                "Overlap veto (%s): already counted in the SingleMuon data" % veto_mode)

        # single-muon: require >= 1 muon with pT > 5 and |eta| < 0.8. pT>5 accommodates every remaining single-muon path (Mu6-Mu10 Barrel IP6).
        df = df.Define("MuonBPark_passSingleMuonSel",
            "(SingleMuonTrigger_flag && Sum(MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8) >= 1)")

        # double-muon: require >= 2 muons with asymmetric thresholds (leading > 4, subleading > 3) (i.e. at least one muon > 4GeV, and at least 2 muons > 3GeV), both in the |eta| < 2.4 region (most inclusive one given the L1 seeds)
        df = df.Define("MuonBPark_passDoubleMuonSel",
            """DoubleMuonTrigger_flag && (
               (Sum(MuonBPark_pt > 4. && abs(MuonBPark_eta) < 2.4) >= 1 &&
                Sum(MuonBPark_pt > 3. && abs(MuonBPark_eta) < 2.4) >= 2)
               )""")

        # cpf candidates
        #df = df.Define("cpf_pt", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py)")
        df = df.Define("cpf_p", "sqrt(cpf_px * cpf_px + cpf_py * cpf_py + cpf_pz * cpf_pz)")
        df = df.Define("cpf_eta", "atanh(cpf_pz/cpf_p)")
        df = df.Define("cpf_phi", "atan2(cpf_py, cpf_px)")
        df = df.Define("cpf_mu_dR", "atan2(cpf_py, cpf_px)")
        # df = df.Define("MuonBPark_cpf_match", "match_col1_col2(MuonBPark_pt, MuonBPark_eta, MuonBPark_phi, cpf_pt, cpf_eta, cpf_phi, 0.1, 0.02)")

        df = df.Define("leading", "get_leading_elems(MuonBPark_pt)") \
            .Define("MuonBPark_isLeading", "leading[0]") \
            .Define("MuonBPark_isSubleading", "leading[1]")

        # Single-muon-style tighter cuts (per-muon flag)
        df = df.Define("MuonBPark_passSingleMuonLike",
            "MuonBPark_isLooseMuon && MuonBPark_pt > 5. && abs(MuonBPark_eta) < 0.8")

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
        #    - double-muon triggers to require at least 2 trigger-matched muons
        # same paths as SingleMuonTrigger_flag -- one source of truth, cannot drift
        singleMuon__matched_paths = [q for q, _ in singleMuon__hlt_conditions]
        doubleMuon__matched_paths = [
            "HLT_DoubleMu4_3_LowMass",
            #"HLT_DoubleMu4_LowMass_Displaced",
        ]
        singleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in singleMuon__matched_paths) or "false"
        doubleMuon__matched_or = " || ".join(
            f"MuonBPark_fired_{q} > 0" for q in doubleMuon__matched_paths) or "false"

        df = df.Define("MuonBPark_SingleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringSingleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({singleMuon__matched_or})
        """)

        df = df.Define("MuonBPark_DoubleMuon_trigger_matched", f"""
            (MuonBPark_isTriggeringDoubleMuon > 0) &&
            (MuonBPark_isTriggering > 0) &&
            ({doubleMuon__matched_or})
        """)


        # event-level requirements
        df = df.Define("MuonBPark_passSingleMuonMatch",
            "SingleMuonTrigger_flag && Sum(MuonBPark_SingleMuon_trigger_matched) >= 1")

        df = df.Define("MuonBPark_passDoubleMuonMatch",
            "DoubleMuonTrigger_flag && Sum(MuonBPark_DoubleMuon_trigger_matched) >= 2")

        # Redundant as an event filter: the priority filter below strictly implies this one, so it
        # rejects no extra events. Kept only because it contributes its own line to the RDataFrame
        # cutflow report.
        df = df.Filter("MuonBPark_passSingleMuonMatch || MuonBPark_passDoubleMuonMatch",
            "Pass trigger-matched req.")

        # Category flags. NOT mutually exclusive: an event satisfying both requirements carries both, and its muonSVs are selected under whichever category they qualify for (see DQCDTriggerSelection2024RDFProducer). The single-muon category used to veto the double-muon one, which pushed overlap events down the single-muon branch and cost them the double-muon muonSV treatment.
        # TODO an alternative is to remove this, and generate 2 separate datasets for single- and double-muon candidates
        df = df.Define("passSingleMuon",
            "MuonBPark_passSingleMuonSel && MuonBPark_passSingleMuonMatch")

        df = df.Define("passDoubleMuon",
            "MuonBPark_passDoubleMuonSel && MuonBPark_passDoubleMuonMatch")

        df = df.Filter("passSingleMuon || passDoubleMuon",
            "Pass single- or double-muon category")

        # tighter eta and pt reqs
        df = df.Define("MuonBPark_isMuonWithTighterEtaAndPtReq", """MuonBPark_isLooseMuon == 1 &&
            MuonBPark_pt > 10. && abs(MuonBPark_eta) < 0.8""")

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

            # category flags (not mutually exclusive)
            "passSingleMuon",
            "passDoubleMuon",

            # Primary-dataset-overlap veto
            "MuonBPark_pdVeto_SingleMuon_trigger_matched",
            "pdVeto_SingleMuonTrigger_flag",
            "pdVeto_passSingleMuon",
            "pdVeto_firedSingleMuon"
        ]

def DQCDMuonSelection2024RDF_Mu10orDoubleMu(*args, **kwargs):
    return lambda: DQCDMuonSelection2024RDFProducer_Mu10orDoubleMu(*args, **kwargs)
