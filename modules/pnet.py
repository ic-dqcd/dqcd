from Base.Modules.baseModules import JetLepMetSyst
from analysis_tools.utils import import_root

ROOT = import_root()

class PNetVarRDFProducer():
    def __init__(self, *args, **kwargs):
        self.isMC = kwargs.pop("isMC", True)
        ROOT.gInterpreter.Declare("""
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            using Vbool = const ROOT::RVec<bool>&;

            ROOT::RVec<double> isMuonFromDarkShower(int nMuon, Vint Muon_genPartIdx,
                Vfloat GenPart_pdgId, Vfloat GenPart_genPartIdxMother)
            {
                ROOT::RVec<double> muon_from_dark_shower(nMuon, 0);
                for (size_t iMuon=0; iMuon < nMuon; iMuon++) {
                    // leaving unmatched muon as false, probably won't consider them later
                    if (Muon_genPartIdx[iMuon] < 0) 
                        continue;
                    int genidx = Muon_genPartIdx[iMuon];
                    while (genidx != -1) {
                        if ((GenPart_pdgId[genidx] > 4000000 && GenPart_pdgId[genidx] < 5000000) ||
                                (GenPart_pdgId[genidx] == 999999) ||
                                (GenPart_pdgId[genidx] == 9900015)) {
                            muon_from_dark_shower[iMuon] = 1;
                            break;
                        } else {
                            genidx = GenPart_genPartIdxMother[genidx];
                        }
                    }
                }
                return muon_from_dark_shower;
            }

            std::vector<ROOT::RVec<double>> isJetWithMatchedMuon(int nMuon, Vint Muon_jetIdx, int nJet,
                Vint Muon_genPartIdx, Vfloat Muon_fromDarkShower)
            {
                 ROOT::RVec<double> jet_with_matched_muon(nJet, 0);
                 ROOT::RVec<double> jet_with_dark_shower_muon(nJet, 0);
                 for (size_t iMuon=0; iMuon < nMuon; iMuon++) {
                    if (Muon_jetIdx[iMuon] >= 0 && Muon_genPartIdx[iMuon] >= 0) {
                        jet_with_matched_muon[Muon_jetIdx[iMuon]] = 1;
                        if (Muon_fromDarkShower[iMuon])
                            jet_with_dark_shower_muon[Muon_jetIdx[iMuon]] = 1;
                    }
                 }
                 return {jet_with_matched_muon, jet_with_dark_shower_muon};
            }

            ROOT::RVec<double> isPfMatchedToMatchedJet(int npf, Vint pf_jetIdx, Vfloat Jet_withMatchedMuon)
            {
                 ROOT::RVec<double> pfMatchedToMatchedJet(npf, 0);
                 for (size_t ipf=0; ipf < npf; ipf++) {
                    if (pf_jetIdx[ipf] >= 0) {
                        if (Jet_withMatchedMuon[pf_jetIdx[ipf]])
                            pfMatchedToMatchedJet[ipf] = 1;
                    }
                 }
                 return pfMatchedToMatchedJet;
            }
        """)

    def run(self, df):
        if not self.isMC:
            return df, []
        else:
            df = df.Define("Muon_fromDarkShower", """isMuonFromDarkShower(nMuon, Muon_genPartIdx,
                GenPart_pdgId, GenPart_genPartIdxMother)""")

            df = df.Define("jet_darkvars", """isJetWithMatchedMuon(nMuon, Muon_jetIdx,
                nJet, Muon_genPartIdx, Muon_fromDarkShower)""")

            df = df.Define("Jet_withMatchedMuon", "jet_darkvars[0]")
            df = df.Define("Jet_fromDarkShower", "jet_darkvars[1]")
            # df = df.Define("Jet_fromDarkShower_sel", "Jet_fromDarkShower[Jet_withMatchedMuon == 1]")

            df = df.Define("cpf_matchedToMatchedJet", """isPfMatchedToMatchedJet(ncpf, cpf_jetIdx,
                Jet_withMatchedMuon)""")
            df = df.Define("npf_matchedToMatchedJet", """isPfMatchedToMatchedJet(nnpf, npf_jetIdx,
                Jet_withMatchedMuon)""")

            df = df.Define("cpf_logpt", "log(cpf_pt)")
            df = df.Define("cpf_loge", "log(cpf_e)")
            df = df.Define("cpf_logptrel", "log(cpf_ptrel)")
            df = df.Define("cpf_logerel", "log(cpf_erel)")

            df = df.Define("cpf_isElectron", "abs(cpf_pdgId) == 11")
            df = df.Define("cpf_isMuon", "abs(cpf_pdgId) == 13")
            df = df.Define("cpf_isChargedHadron", "abs(cpf_pdgId) == 211")
            df = df.Define("cpf_charge", """ROOT::RVec<int> charge(ncpf, 1);
                for (size_t i = 0; i < ncpf; i++) if (cpf_pdgId[i] < 0) charge[i] = -1;
                return charge;""")

            df = df.Define("cpf_tanhdxy", "tanh(cpf_dxy)")
            df = df.Define("cpf_tanhdz", "tanh(cpf_dz)")

            df = df.Define("npf_logpt", "log(npf_pt)")
            df = df.Define("npf_loge", "log(npf_e)")
            df = df.Define("npf_logptrel", "log(npf_ptrel)")
            df = df.Define("npf_logerel", "log(npf_erel)")

            df = df.Define("npf_isNeutralHadron", "abs(npf_pdgId) == 130")

            branches = ["Jet_withMatchedMuon", "Jet_fromDarkShower", "cpf_matchedToMatchedJet",
                "npf_matchedToMatchedJet"]
            for var in ["cpf_deta", "cpf_dphi", "cpf_logpt", "cpf_logpt_sel", "cpf_loge",
                    "cpf_logptrel", "cpf_logerel", "cpf_deltaR", "cpf_charge", "cpf_isElectron",
                    "cpf_isMuon", "cpf_isChargedHadron", "cpf_tanhdxy", "cpf_dxyError", "cpf_tanhdz",
                    "cpf_dzError", "cpf_jetIdx"]:
                df = df.Define(f"{var}_sel", f"{var}[cpf_matchedToMatchedJet == 1]")
                branches += [f"{var}_sel"]
            for var in ["npf_deta", "npf_dphi", "npf_logpt", "npf_loge", "npf_logptrel",
                    "npf_logerel", "npf_deltaR", "npf_isNeutralHadron", "npf_isGamma", "npf_jetIdx"]:
                df = df.Define(f"{var}_sel", f"{var}[npf_matchedToMatchedJet == 1]")
                branches += [f"{var}_sel"]

            return df, branches


def PNetVarRDF(*args, **kwargs):
    return lambda: PNetVarRDFProducer(*args, **kwargs)
