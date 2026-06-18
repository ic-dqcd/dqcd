import os
from analysis_tools.utils import import_root
ROOT = import_root()

class DQCDMuonSVSelectionRDFProducer():
    def __init__(self, *args, **kwargs):
        self.gen_mass = kwargs.pop("gen_mass", 20)

        ROOT.gInterpreter.Declare("""
            #include "DataFormats/Math/interface/deltaR.h"
            using Vint = const ROOT::RVec<int>&;
            using Vfloat = const ROOT::RVec<float>&;

            struct output_multivertices {
                ROOT::RVec<float> mass;
                ROOT::RVec<float> chi2;
                ROOT::RVec<int> indexes;
            };

            output_multivertices get_multivertices(
                    int nmuonSV,
                    Vfloat muonSV_mass, Vfloat muonSV_chi2,
                    Vfloat muonSV_mu1eta, Vfloat muonSV_mu1phi,
                    Vfloat muonSV_mu2eta, Vfloat muonSV_mu2phi,
                    Vint muonSV_mu1index, Vint muonSV_mu2index) {

                ROOT::RVec<float> mass_multivertices;
                ROOT::RVec<float> chi2_multivertices;
                ROOT::RVec<int> indexes_multivertices;

                std::vector<std::pair<int, int>> index_pairs;

                if (nmuonSV > 1) {
                    for (size_t imuonSV = 0; imuonSV < nmuonSV - 1; imuonSV++) {
                        if (muonSV_chi2[imuonSV] > 10 ||
                                muonSV_mu1eta[imuonSV] == 0 || muonSV_mu2eta[imuonSV] == 0 ||
                                reco::deltaR(muonSV_mu1eta[imuonSV], muonSV_mu1phi[imuonSV],
                                    muonSV_mu2eta[imuonSV], muonSV_mu2phi[imuonSV]) > 1.2)
                            continue;
                        for (size_t imuonSV1 = imuonSV + 1; imuonSV1 < nmuonSV; imuonSV1++) {
                            if (muonSV_chi2[imuonSV1] > 10 ||
                                    muonSV_mu1eta[imuonSV1] == 0 || muonSV_mu2eta[imuonSV1] == 0 ||
                                    reco::deltaR(muonSV_mu1eta[imuonSV], muonSV_mu1phi[imuonSV],
                                        muonSV_mu2eta[imuonSV], muonSV_mu2phi[imuonSV]) > 1.2)
                                continue;

                            // fractional mass difference within 3 sigma (sigma = 1% of the mass)
                            if ((fabs(muonSV_mass[imuonSV] - muonSV_mass[imuonSV1]) / muonSV_mass[imuonSV]) < 3 * 0.01) {
                                if (muonSV_mu1index[imuonSV] != muonSV_mu1index[imuonSV1] &&
                                        muonSV_mu1index[imuonSV] != muonSV_mu2index[imuonSV1] &&
                                        muonSV_mu2index[imuonSV] != muonSV_mu1index[imuonSV1] &&
                                        muonSV_mu2index[imuonSV] != muonSV_mu2index[imuonSV1]) {
                                    index_pairs.push_back(std::make_pair(imuonSV, imuonSV1));
                                } // end if muon indexes
                            } // end if mass diff
                        } // end loop over imuonSV1
                    } // end loop over imuonSV
                }

                // cleaning
                // if two pairs share one muonSV, only the one with the smallest chi2
                // (from the other muonSV) remains
                std::vector<bool> valid(index_pairs.size(), true);
                if (index_pairs.size() > 1) {
                    for (int ipair = 0; ipair < index_pairs.size() - 1; ipair++) {
                        if (!valid[ipair])
                            continue;
                        for (int ipair2 = ipair + 1; ipair2 < index_pairs.size(); ipair2++) {
                            if (!valid[ipair2])
                                continue;
                            if (index_pairs[ipair].first == index_pairs[ipair2].first) {
                                if (muonSV_chi2[index_pairs[ipair].second] >
                                        muonSV_chi2[index_pairs[ipair2].second]) {
                                    valid[ipair] = false;
                                    break;
                                } else {
                                    valid[ipair2] = false;
                                }
                            } else if (index_pairs[ipair].second == index_pairs[ipair2].second) {
                                if (muonSV_chi2[index_pairs[ipair].first] >
                                        muonSV_chi2[index_pairs[ipair2].first]) {
                                    valid[ipair] = false;
                                    break;
                                } else {
                                    valid[ipair2] = false;
                                }
                            }
                        }
                    }
                }
                for (int ipair = 0; ipair < index_pairs.size(); ipair++) {
                    if (valid[ipair]) {
                        if (std::find(indexes_multivertices.begin(), indexes_multivertices.end(),
                                index_pairs[ipair].first) == indexes_multivertices.end()) {
                            // index wasn't previously stored, we do it now
                            // this could happen if we have multiv associations like 0<->1, 1<->2
                            mass_multivertices.push_back(muonSV_mass[index_pairs[ipair].first]);
                            chi2_multivertices.push_back(muonSV_chi2[index_pairs[ipair].first]);
                            indexes_multivertices.push_back(index_pairs[ipair].first);
                        }
                        if (std::find(indexes_multivertices.begin(), indexes_multivertices.end(),
                                index_pairs[ipair].second) == indexes_multivertices.end()) {
                            // index wasn't previously stored, we do it now
                            // this could happen if we have multiv associations like 0<->1, 1<->2
                            mass_multivertices.push_back(muonSV_mass[index_pairs[ipair].second]);
                            chi2_multivertices.push_back(muonSV_chi2[index_pairs[ipair].second]);
                            indexes_multivertices.push_back(index_pairs[ipair].second);
                        }

                    }
                }

                if (indexes_multivertices.size() == 0) {
                    // Fill with the element with the smallest chi2 (if available)
                    ROOT::RVec<float> chi2;
                    ROOT::RVec<int> indexes;
                    for (size_t imuonSV = 0; imuonSV < nmuonSV; imuonSV++) {
                        if (muonSV_chi2[imuonSV] > 10 ||
                                muonSV_mu1eta[imuonSV] == 0 || muonSV_mu2eta[imuonSV] == 0 ||
                                reco::deltaR(muonSV_mu1eta[imuonSV], muonSV_mu1phi[imuonSV],
                                    muonSV_mu2eta[imuonSV], muonSV_mu2phi[imuonSV]) > 1.2)
                            continue;
                        indexes.push_back(imuonSV);
                        chi2.push_back(muonSV_chi2[imuonSV]);
                    }
                    if (indexes.size() > 0) {
                        auto min_index = ROOT::VecOps::ArgMin(chi2);
                        mass_multivertices.push_back(muonSV_mass[indexes[min_index]]);
                        chi2_multivertices.push_back(muonSV_chi2[indexes[min_index]]);
                        indexes_multivertices.push_back(indexes[min_index]);
                    }
                }
                return output_multivertices({mass_multivertices, chi2_multivertices, indexes_multivertices});
            } // end function

            //
            // function to get deltaR. Assuming all vectors have the same length
            //
            ROOT::RVec<float> get_deltaR(int n, Vfloat eta1, Vfloat phi1, Vfloat eta2, Vfloat phi2) {
                ROOT::RVec<float> dR(n, 0);
                for (size_t i = 0; i < n; i++) {
                    dR[i] = reco::deltaR(eta1[i], phi1[i], eta2[i], phi2[i]);
                }
                return dR;
            }

            //
            // get_multivertices returns positions WITHIN the neutral subset of muonSVs.
            // This helper maps those neutral-subset positions back to positions in the
            // FULL muonSV_* collection, so all downstream consumers (which index the full
            // arrays) read the correct vertex.
            //
            using Vbool = const ROOT::RVec<bool>&;
            ROOT::RVec<int> remap_neutral_to_full(Vint neutral_indexes, Vbool isNeutral) {
                ROOT::RVec<int> full_positions;
                for (size_t i = 0; i < isNeutral.size(); i++)
                    if (isNeutral[i])
                        full_positions.push_back((int) i);
                ROOT::RVec<int> out;
                for (auto ni: neutral_indexes)
                    out.push_back(full_positions[ni]);
                return out;
            }
        """)

    def run(self, df):

        # Filter out events that have *no* neutral SVs
        df = df.Define("MuonSV_isNeutral", "muonSV_charge == 0")
        df = df.Filter("Sum(MuonSV_isNeutral) > 0", "Require at least one neutral muonSV")

        # Redifining variables so that only neutral SVs from all collections are kept
        df = df.Define("muonSVNeutral_charge", "muonSV_charge[MuonSV_isNeutral]")
        df = df.Define("muonSVNeutral_mass",   "muonSV_mass[MuonSV_isNeutral]")
        df = df.Define("muonSVNeutral_chi2",   "muonSV_chi2[MuonSV_isNeutral]")
        df = df.Define("muonSVNeutral_mu1eta", "muonSV_mu1eta[MuonSV_isNeutral]")
        df = df.Define("muonSVNeutral_mu1phi", "muonSV_mu1phi[MuonSV_isNeutral]")
        df = df.Define("muonSVNeutral_mu2eta", "muonSV_mu2eta[MuonSV_isNeutral]")
        df = df.Define("muonSVNeutral_mu2phi", "muonSV_mu2phi[MuonSV_isNeutral]")
        df = df.Define("muonSVNeutral_mu1index", "muonSV_mu1index[MuonSV_isNeutral]")
        df = df.Define("muonSVNeutral_mu2index", "muonSV_mu2index[MuonSV_isNeutral]")
        df = df.Define("nmuonSVNeutral", "Sum(MuonSV_isNeutral)")  # update the count


        #df = df.Filter("nmuonSV > 0")
        df = df.Filter("nmuonSVNeutral > 0")

        #TODO testing neutral SV variables
        sigma = self.gen_mass * 0.01
        df = df.Define("nmuonSV_3sigma",
            f"muonSVNeutral_mass[abs(muonSVNeutral_mass - {self.gen_mass}) < 3 * {sigma}].size()")

        #TODO testing neutral SV variables
        df = df.Define("multivertices_vars", """get_multivertices(nmuonSVNeutral, muonSVNeutral_mass, muonSVNeutral_chi2,
            muonSVNeutral_mu1eta, muonSVNeutral_mu1phi, muonSVNeutral_mu2eta, muonSVNeutral_mu2phi,
            muonSVNeutral_mu1index, muonSVNeutral_mu2index)""")
        df = df.Define("mass_multivertices", "multivertices_vars.mass")
        df = df.Define("chi2_multivertices", "multivertices_vars.chi2")
        # multivertices_vars.indexes are positions WITHIN the neutral subset (the arrays
        # passed to get_multivertices). Remap them to positions in the FULL muonSV_*
        # collection, because every downstream consumer (min_chi2_index, DummyMinChi2RDF's
        # .at(), the trigger/loose modules' std::find, AdditionalMuonDQCDRDF, and the
        # category selections) indexes the full muonSV_* arrays. Without this remap, any
        # event with a charged muonSV ordered before the selected neutral one reads the
        # wrong (possibly charged) vertex.
        df = df.Define("indexes_multivertices",
            "remap_neutral_to_full(multivertices_vars.indexes, MuonSV_isNeutral)")

        # chi2_multivertices should have at least 1 element
        df = df.Filter("chi2_multivertices.size() > 0", "muonSV selection")

        df = df.Define("cat_index", "int(mass_multivertices.size() / 2)")

        df = df.Define("min_chi2", "Min(chi2_multivertices)")
        df = df.Define("min_chi2_index", "indexes_multivertices[ArgMin(chi2_multivertices)]")

        df = df.Define("muonSV_dR", "get_deltaR("
            "nmuonSV, muonSV_mu1eta, muonSV_mu1phi, muonSV_mu2eta, muonSV_mu2phi)")
        # df = df.Filter("muonSV_dR.at(min_chi2_index) < 1.2")
        df = df.Filter("ROOT::VecOps::Sum(muonSV_dR[muonSV_dR < 1.2]) > 0", "muonSV deltaR")

        # return df, []

        return df, ["nmuonSV_3sigma",
            "mass_multivertices", "chi2_multivertices", "indexes_multivertices",
            "min_chi2", "min_chi2_index", "cat_index", "muonSV_dR"]


def DQCDMuonSVSelectionRDF(*args, **kwargs):
    return lambda: DQCDMuonSVSelectionRDFProducer(*args, **kwargs)


class DQCDFourMuonSVSelectionRDFProducer():
    """Identifies a four-muon vertex (fourmuonSV) whose four muons are reconstructed as two
    charge-neutral dimuon vertices (muonSV) -- the "quadv" group.

    Defines the per-event flag isFourMuonPlusDimuonSV, the indices of the selected
    fourmuonSV and its two dimuon vertices, and flat fourmuonSV_selected_* variables
    (mass/chi2/dxy/pAngle) of the selected four-muon vertex.

    The four-muon vertex must be charge neutral (fourmuonSV_charge == 0) and each of the two
    dimuon vertices must be charge neutral (muonSV_charge == 0). The module does NOT filter
    events: events without such a configuration get isFourMuonPlusDimuonSV == 0 and
    fourmuonSV_selected_* == -1. Selection follows
    https://github.com/ponvie/EXO/blob/main/analysis/4flags_inclusive.py#L82-L189
    """
    def __init__(self, *args, **kwargs):
        if not os.getenv("_DQCDFourMuonSVSelection"):
            os.environ["_DQCDFourMuonSVSelection"] = "DQCDFourMuonSVSelection"
            ROOT.gInterpreter.Declare("""
                #include <set>
                #include <cmath>
                #include <algorithm>
                #include "DataFormats/Math/interface/deltaR.h"
                using Vfloat = const ROOT::RVec<float>&;
                using Vint = const ROOT::RVec<int>&;

                struct fourmuon_dimuon_t {
                    int is_quadv;
                    int fourmuonSV_index;
                    int muonSV1_index;
                    int muonSV2_index;
                };

                fourmuon_dimuon_t select_fourmuon_plus_dimuon(
                        Vfloat fourmuonSV_chi2, Vint fourmuonSV_charge,
                        Vint fourmuonSV_mu1index, Vint fourmuonSV_mu2index,
                        Vint fourmuonSV_mu3index, Vint fourmuonSV_mu4index,
                        Vfloat muonSV_chi2, Vfloat muonSV_mass, Vint muonSV_charge,
                        Vfloat muonSV_mu1eta, Vfloat muonSV_mu1phi,
                        Vfloat muonSV_mu2eta, Vfloat muonSV_mu2phi,
                        Vint muonSV_mu1index, Vint muonSV_mu2index) {

                    fourmuon_dimuon_t res({0, -1, -1, -1});
                    for (size_t i = 0; i < fourmuonSV_chi2.size(); ++i) {
                        // four-muon vertex: quality + charge neutrality
                        if (fourmuonSV_chi2[i] >= 10 || fourmuonSV_charge[i] != 0)
                            continue;
                        ROOT::RVec<int> fourMuons = {
                            fourmuonSV_mu1index[i], fourmuonSV_mu2index[i],
                            fourmuonSV_mu3index[i], fourmuonSV_mu4index[i]};

                        for (size_t a = 0; a < muonSV_mu1index.size(); ++a) {
                            if (muonSV_charge[a] != 0 || muonSV_chi2[a] >= 10)
                                continue;
                            if (reco::deltaR(muonSV_mu1eta[a], muonSV_mu1phi[a],
                                    muonSV_mu2eta[a], muonSV_mu2phi[a]) >= 1.2)
                                continue;
                            int mu1a = muonSV_mu1index[a], mu2a = muonSV_mu2index[a];
                            if (std::find(fourMuons.begin(), fourMuons.end(), mu1a) == fourMuons.end() ||
                                    std::find(fourMuons.begin(), fourMuons.end(), mu2a) == fourMuons.end())
                                continue;

                            for (size_t b = a + 1; b < muonSV_mu1index.size(); ++b) {
                                if (muonSV_charge[b] != 0 || muonSV_chi2[b] >= 10)
                                    continue;
                                if (reco::deltaR(muonSV_mu1eta[b], muonSV_mu1phi[b],
                                        muonSV_mu2eta[b], muonSV_mu2phi[b]) >= 1.2)
                                    continue;
                                int mu1b = muonSV_mu1index[b], mu2b = muonSV_mu2index[b];
                                if (std::find(fourMuons.begin(), fourMuons.end(), mu1b) == fourMuons.end() ||
                                        std::find(fourMuons.begin(), fourMuons.end(), mu2b) == fourMuons.end())
                                    continue;

                                // the two dimuon vertices must use four distinct muons
                                // covering exactly the four-muon vertex's muons
                                std::set<int> combined = {mu1a, mu2a, mu1b, mu2b};
                                if (combined.size() != 4)
                                    continue;

                                // mass coherence between the two dimuon vertices (3%)
                                float mA = muonSV_mass[a], mB = muonSV_mass[b];
                                if (mA <= 0.f || mB <= 0.f)
                                    continue;
                                if (std::fabs(mA - mB) / mA < 0.03f) {
                                    res.is_quadv = 1;
                                    res.fourmuonSV_index = (int) i;
                                    res.muonSV1_index = (int) a;
                                    res.muonSV2_index = (int) b;
                                    return res;
                                }
                            }
                        }
                    }
                    return res;
                }
            """)

    def run(self, df):
        df = df.Define("fourmuon_dimuon_vars", """select_fourmuon_plus_dimuon(
            fourmuonSV_chi2, fourmuonSV_charge,
            fourmuonSV_mu1index, fourmuonSV_mu2index,
            fourmuonSV_mu3index, fourmuonSV_mu4index,
            muonSV_chi2, muonSV_mass, muonSV_charge,
            muonSV_mu1eta, muonSV_mu1phi,
            muonSV_mu2eta, muonSV_mu2phi,
            muonSV_mu1index, muonSV_mu2index)""")
        df = df.Define("isFourMuonPlusDimuonSV", "fourmuon_dimuon_vars.is_quadv")
        df = df.Define("selected_fourmuonSV_index", "fourmuon_dimuon_vars.fourmuonSV_index")
        df = df.Define("selected_muonSV1_index", "fourmuon_dimuon_vars.muonSV1_index")
        df = df.Define("selected_muonSV2_index", "fourmuon_dimuon_vars.muonSV2_index")

        # of the two matched dimuon vertices, pick the one with the smaller chi2
        # (same convention as multiv's min_chi2_index)
        df = df.Define("selected_quadv_muonSV_index",
            "selected_muonSV1_index < 0 ? -1 : ("
            "muonSV_chi2.at(selected_muonSV1_index) <= muonSV_chi2.at(selected_muonSV2_index)"
            " ? selected_muonSV1_index : selected_muonSV2_index)")

        branches = ["isFourMuonPlusDimuonSV", "selected_fourmuonSV_index",
            "selected_muonSV1_index", "selected_muonSV2_index", "selected_quadv_muonSV_index"]

        # flat per-event variables of the selected four-muon vertex (-1 if no quadv);
        # kept for monitoring and a future fourmuonSV-trained BDT
        for v in ["mass", "chi2", "dxy", "pAngle"]:
            df = df.Define("fourmuonSV_selected_%s" % v,
                "selected_fourmuonSV_index >= 0 ? "
                "fourmuonSV_%s.at(selected_fourmuonSV_index) : -1.f" % v)
            branches.append("fourmuonSV_selected_%s" % v)

        # dxy/pAngle from the matched dimuon vertex (used for the quadv category binning,
        # so all three groups bin on the same muonSV quantity)
        for v in ["dxy", "pAngle"]:
            df = df.Define("quadv_muonSV_%s" % v,
                "selected_quadv_muonSV_index >= 0 ? "
                "muonSV_%s.at(selected_quadv_muonSV_index) : -1.f" % v)
            branches.append("quadv_muonSV_%s" % v)

        return df, branches


def DQCDFourMuonSVSelectionRDF(*args, **kwargs):
    return lambda: DQCDFourMuonSVSelectionRDFProducer(*args, **kwargs)


class DQCDMuonSVRDFProducer():
    def __init__(self, *args, **kwargs):
        ROOT.gInterpreter.Declare("""
            #include <TLorentzVector.h>
            const float muon_mass = 0.1057;
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            ROOT::RVec<float> get_muonsv_mass(
                int nmuonSV, int nMuon, Vfloat Muon_pt, Vfloat Muon_phi, Vfloat Muon_eta,
                Vint muonSV_mu1index, Vint muonSV_mu2index)
            {
                ROOT::RVec<float> muonSV_m;
                if (nmuonSV == 0)
                    return muonSV_m;
                    for (size_t imuonSV = 0; imuonSV < nmuonSV; imuonSV++) {
                    auto muon1 = TLorentzVector();
                    auto muon2 = TLorentzVector();
                    muon1.SetPtEtaPhiM(
                        Muon_pt[muonSV_mu1index[imuonSV]],
                        Muon_eta[muonSV_mu1index[imuonSV]],
                        Muon_phi[muonSV_mu1index[imuonSV]],
                        muon_mass
                    );
                    muon2.SetPtEtaPhiM(
                        Muon_pt[muonSV_mu2index[imuonSV]],
                        Muon_eta[muonSV_mu2index[imuonSV]],
                        Muon_phi[muonSV_mu2index[imuonSV]],
                        muon_mass
                    );
                    auto muonSV = muon1 + muon2;
                    muonSV_m.push_back(muonSV.M());
                }
                return muonSV_m;
            }
        """)

    def run(self, df):
        df = df.Define("muonSV_m", """get_muonsv_mass(
            nmuonSV, nMuon, Muon_pt, Muon_phi, Muon_eta,
            muonSV_mu1index, muonSV_mu2index)""")
        return df, ["muonSV_m"]


def DQCDMuonSVRDF(*args, **kwargs):
    return lambda: DQCDMuonSVRDFProducer(*args, **kwargs)


class DQCDTriggerSelectionRDFProducer():
    def __init__(self, *args, **kwargs):
        if not os.getenv("_DQCDTriggerSelection"):
            os.environ["_DQCDTriggerSelection"] = "DQCDTriggerSelection"
            ROOT.gInterpreter.Declare("""
                #include <algorithm>    // std::find
                #include <vector>       // std::vector
                #include "DataFormats/Math/interface/deltaR.h"
                struct muonsv_struct {
                    size_t i;
                    float chi2;
                    int muonBPark_trigger_index_1;
                    int muonBPark_trigger_index_2;
                };

                bool muonSVChi2Sort (const muonsv_struct& a, const muonsv_struct& b)
                {
                  return (a.chi2 < b.chi2);
                }

                using Vfloat = const ROOT::RVec<float>&;
                using Vint = const ROOT::RVec<int>&;
                using Vbool = const ROOT::RVec<bool>&;
                std::vector<int> get_triggering_muonsv_and_muon_indexes(
                    int nmuonSV, Vfloat muonSV_chi2, Vfloat muonSV_dR,
                    Vfloat muonSV_mu1eta, Vfloat muonSV_mu1phi,
                    Vfloat muonSV_mu2eta, Vfloat muonSV_mu2phi,
                    int nMuonBPark, Vfloat MuonBPark_eta, Vfloat MuonBPark_phi,
                    Vbool MuonBPark_trigger_matched, Vbool MuonBPark_isMuonWithTighterEtaAndPtReq,
                    int nMuon, Vfloat Muon_eta, Vfloat Muon_phi,
                    Vint indexes_multivertices
                )
                {
                    std::vector<int> indexes(5, -999);
                    std::vector<muonsv_struct> muonsvs;
                    for (size_t imuonSV = 0; imuonSV < nmuonSV; imuonSV++) {
                        if (muonSV_dR[imuonSV] > 1.2)
                            continue;
                        if (indexes_multivertices.size() > 0) {
                            // index has to be selected by the DQCDMuonSVSelectionRDF module
                            if (std::find(indexes_multivertices.begin(), indexes_multivertices.end(),
                                    imuonSV) == indexes_multivertices.end())
                                // imuonSV not in the ones selected from the multivertices
                                continue;
                        }
                        auto muonsv = muonsv_struct({imuonSV, muonSV_chi2[imuonSV], -999, -999});
                        // matching muonSV's muons with MuonBPark muons firing HLT_Mu9_Ip6 and other
                        // kinematic requirements
                        float mindeltaR1 = 999.;
                        float mindeltaR2 = 999.;
                        for (size_t iMuonBPark = 0; iMuonBPark < nMuonBPark; iMuonBPark++) {
                            if (!MuonBPark_trigger_matched[iMuonBPark] ||
                                    !MuonBPark_isMuonWithTighterEtaAndPtReq[iMuonBPark])
                                continue;
                            auto dr1 = reco::deltaR(muonSV_mu1eta[imuonSV], muonSV_mu1phi[imuonSV],
                                MuonBPark_eta[iMuonBPark], MuonBPark_phi[iMuonBPark]);
                            auto dr2 = reco::deltaR(muonSV_mu2eta[imuonSV], muonSV_mu2phi[imuonSV],
                                MuonBPark_eta[iMuonBPark], MuonBPark_phi[iMuonBPark]);
                            if (dr1 < 0.05 && dr1 < mindeltaR1) {
                                muonsv.muonBPark_trigger_index_1 = iMuonBPark;
                                mindeltaR1 = dr1;
                            }
                            if (dr2 < 0.05 && dr2 < mindeltaR2) {
                                muonsv.muonBPark_trigger_index_2 = iMuonBPark;
                                mindeltaR2 = dr2;
                            }
                        }
                        // Requires one muon from the SV to be matched to a trigger muon
                        if (muonsv.muonBPark_trigger_index_1 != -999
                                || muonsv.muonBPark_trigger_index_2 != -999)
                            muonsvs.push_back(muonsv);
                    }
                    if (muonsvs.size() > 1)
                        std::stable_sort(muonsvs.begin(), muonsvs.end(), muonSVChi2Sort);
                    if (muonsvs.size() > 0) {
                        indexes[0] = muonsvs[0].i;
                        indexes[1] = muonsvs[0].muonBPark_trigger_index_1;
                        indexes[2] = muonsvs[0].muonBPark_trigger_index_2;
                        auto MuonBPark2_trig_eta = MuonBPark_eta[indexes[2]];
                        auto MuonBPark2_trig_phi = MuonBPark_phi[indexes[2]];
                        float mindeltaR1 = 999.;
                        float mindeltaR2 = 999.;
                        for (size_t iMuon = 0; iMuon < nMuon; iMuon++) {
                            if (indexes[1] != -999) {
                                auto MuonBPark1_trig_eta = MuonBPark_eta[indexes[1]];
                                auto MuonBPark1_trig_phi = MuonBPark_phi[indexes[1]];
                                auto dr1 = reco::deltaR(MuonBPark1_trig_eta, MuonBPark1_trig_phi,
                                    Muon_eta[iMuon], Muon_phi[iMuon]);
                                if (dr1 < 0.05 && dr1 < mindeltaR1) {
                                    indexes[3] = iMuon;
                                    mindeltaR1 = dr1;
                                }
                            }
                            if (indexes[2] != -999) {
                                auto MuonBPark2_trig_eta = MuonBPark_eta[indexes[2]];
                                auto MuonBPark2_trig_phi = MuonBPark_phi[indexes[2]];
                                auto dr2 = reco::deltaR(MuonBPark2_trig_eta, MuonBPark2_trig_phi,
                                    Muon_eta[iMuon], Muon_phi[iMuon]);
                                if (dr2 < 0.05 && dr2 < mindeltaR2) {
                                    indexes[4] = iMuon;
                                    mindeltaR2 = dr2;
                                }
                            }
                        }
                    }
                    return indexes;
                }
            """)

    def run(self, df):
        branches = ["muonSV_chi2_trig_index",
            "muonSV_chi2_trig_muonBPark1_index", "muonSV_chi2_trig_muonBPark2_index",
            "muonSV_chi2_trig_muon1_index", "muonSV_chi2_trig_muon2_index"]
        df = df.Define("muonsv_indexes", """get_triggering_muonsv_and_muon_indexes(
            nmuonSV, muonSV_chi2, muonSV_dR,
            muonSV_mu1eta, muonSV_mu1phi,
            muonSV_mu2eta, muonSV_mu2phi,
            nMuonBPark, MuonBPark_eta, MuonBPark_phi,
            MuonBPark_trigger_matched, MuonBPark_isMuonWithTighterEtaAndPtReq,
            nMuon, Muon_eta, Muon_phi,
            indexes_multivertices)
        """)
        for ib, branch in enumerate(branches):
            df = df.Define(branch, f"muonsv_indexes.at({ib})")

        df = df.Filter("muonSV_chi2_trig_index >= 0", "MuonSV has trigger-matched muon")

        return df, branches


def DQCDTriggerSelectionRDF(*args, **kwargs):
    return lambda: DQCDTriggerSelectionRDFProducer(*args, **kwargs)


class DQCDTriggerSelection2024RDFProducer():
    def __init__(self, *args, **kwargs):
        if not os.getenv("_DQCDTriggerSelection"):
            os.environ["_DQCDTriggerSelection"] = "DQCDTriggerSelection"
            ROOT.gInterpreter.Declare("""
                #include <algorithm>    // std::find
                #include <vector>       // std::vector
                #include "DataFormats/Math/interface/deltaR.h"
                struct muonsv_struct {
                    size_t i;
                    float chi2;
                    int muonBPark_trigger_index_1;
                    int muonBPark_trigger_index_2;
                };

                bool muonSVChi2Sort (const muonsv_struct& a, const muonsv_struct& b)
                {
                  return (a.chi2 < b.chi2);
                }

                using Vfloat = const ROOT::RVec<float>&;
                using Vint = const ROOT::RVec<int>&;
                using Vbool = const ROOT::RVec<bool>&;
                std::vector<int> get_triggering_muonsv_and_muon_indexes(
                    int nmuonSV, Vfloat muonSV_chi2, Vfloat muonSV_dR,
                    Vfloat muonSV_mu1eta, Vfloat muonSV_mu1phi,
                    Vfloat muonSV_mu2eta, Vfloat muonSV_mu2phi,
                    int nMuonBPark, Vfloat MuonBPark_eta, Vfloat MuonBPark_phi,
                    Vbool MuonBPark_SingleMuon_trigger_matched, Vbool MuonBPark_DoubleMuon_trigger_matched,
                    Vbool MuonBPark_isMuonWithTighterEtaAndPtReq,
                    Vbool MuonBPark_passSingleMuonLike, Vbool MuonBPark_passDoubleMuonLike,
                    bool passSingleMuonExclusive, bool passDoubleMuonExclusive,
                    int nMuon, Vfloat Muon_eta, Vfloat Muon_phi,
                    Vint indexes_multivertices
                )
                {
                    std::vector<int> indexes(5, -999);
                    std::vector<muonsv_struct> muonsvs;

                    for (size_t imuonSV = 0; imuonSV < nmuonSV; imuonSV++) {
                        if (muonSV_dR[imuonSV] > 1.2)
                            continue;
                        if (!indexes_multivertices.empty()) {
                            // index has to be selected by the DQCDMuonSVSelectionRDF module
                            if (std::find(indexes_multivertices.begin(), indexes_multivertices.end(), imuonSV)
                                    == indexes_multivertices.end())
                                // imuonSV not in the ones selected from the multivertices
                                continue;
                        }

                        auto muonsv = muonsv_struct({imuonSV, muonSV_chi2[imuonSV], -999, -999});

                        // matching muonSV's muons with MuonBPark muons firing HLT_Mu9_Ip6 and other
                        // kinematic requirements
                        float mindeltaR1 = 999.;
                        float mindeltaR2 = 999.;

                        for (size_t iMuonBPark = 0; iMuonBPark < nMuonBPark; iMuonBPark++) {
                            if (!MuonBPark_SingleMuon_trigger_matched[iMuonBPark] && !MuonBPark_DoubleMuon_trigger_matched[iMuonBPark])
                                continue;

                            // Select based on category
                            if (passSingleMuonExclusive && !MuonBPark_passSingleMuonLike[iMuonBPark]) continue;
                            if (passDoubleMuonExclusive && !MuonBPark_passDoubleMuonLike[iMuonBPark]) continue;

                            auto dr1 = reco::deltaR(muonSV_mu1eta[imuonSV], muonSV_mu1phi[imuonSV],
                                                    MuonBPark_eta[iMuonBPark], MuonBPark_phi[iMuonBPark]);
                            auto dr2 = reco::deltaR(muonSV_mu2eta[imuonSV], muonSV_mu2phi[imuonSV],
                                                    MuonBPark_eta[iMuonBPark], MuonBPark_phi[iMuonBPark]);

                            if (dr1 < 0.05 && dr1 < mindeltaR1) {
                                muonsv.muonBPark_trigger_index_1 = iMuonBPark;
                                mindeltaR1 = dr1;
                            }
                            if (dr2 < 0.05 && dr2 < mindeltaR2) {
                                muonsv.muonBPark_trigger_index_2 = iMuonBPark;
                                mindeltaR2 = dr2;
                            }
                        }

                        // Decide whether to keep this SV
                        bool keep = false;
                        // single muons need AT LEAST ONE muon that matches
                        if (passSingleMuonExclusive) {
                            keep = (muonsv.muonBPark_trigger_index_1 != -999 ||
                                    muonsv.muonBPark_trigger_index_2 != -999);
                        }
                        // double muons requiere that both muons match
                        if (passDoubleMuonExclusive) {
                            keep = (muonsv.muonBPark_trigger_index_1 != -999 &&
                                    muonsv.muonBPark_trigger_index_2 != -999);
                        }

                        if (keep) muonsvs.push_back(muonsv);
                    }

                    if (muonsvs.size() > 1)
                        std::stable_sort(muonsvs.begin(), muonsvs.end(), muonSVChi2Sort);

                    if (!muonsvs.empty()) {
                        indexes[0] = muonsvs[0].i;
                        indexes[1] = muonsvs[0].muonBPark_trigger_index_1;
                        indexes[2] = muonsvs[0].muonBPark_trigger_index_2;

                        float mindeltaR1 = 999.;
                        float mindeltaR2 = 999.;

                        for (size_t iMuon = 0; iMuon < nMuon; iMuon++) {
                            if (indexes[1] != -999) {
                                auto MuonBPark1_trig_eta = MuonBPark_eta[indexes[1]];
                                auto MuonBPark1_trig_phi = MuonBPark_phi[indexes[1]];
                                auto dr1 = reco::deltaR(MuonBPark1_trig_eta, MuonBPark1_trig_phi,
                                                        Muon_eta[iMuon], Muon_phi[iMuon]);
                                if (dr1 < 0.05 && dr1 < mindeltaR1) {
                                    indexes[3] = iMuon;
                                    mindeltaR1 = dr1;
                                }
                            }
                            if (indexes[2] != -999) {
                                auto MuonBPark2_trig_eta = MuonBPark_eta[indexes[2]];
                                auto MuonBPark2_trig_phi = MuonBPark_phi[indexes[2]];
                                auto dr2 = reco::deltaR(MuonBPark2_trig_eta, MuonBPark2_trig_phi,
                                                        Muon_eta[iMuon], Muon_phi[iMuon]);
                                if (dr2 < 0.05 && dr2 < mindeltaR2) {
                                    indexes[4] = iMuon;
                                    mindeltaR2 = dr2;
                                }
                            }
                        }
                    }
                    return indexes;
                }
            """)

    def run(self, df):
        branches = ["muonSV_chi2_trig_index",
            "muonSV_chi2_trig_muonBPark1_index",
            "muonSV_chi2_trig_muonBPark2_index",
            "muonSV_chi2_trig_muon1_index",
            "muonSV_chi2_trig_muon2_index"
        ]

        #TODO for the future (e.g. to apply triggerSF), should store whether the vertex was accepted because it passes SingleMuon or DoubleMuon
        df = df.Define("muonsv_indexes", """get_triggering_muonsv_and_muon_indexes(
            nmuonSV, muonSV_chi2, muonSV_dR,
            muonSV_mu1eta, muonSV_mu1phi,
            muonSV_mu2eta, muonSV_mu2phi,
            nMuonBPark, MuonBPark_eta, MuonBPark_phi,
            MuonBPark_SingleMuon_trigger_matched,
            MuonBPark_DoubleMuon_trigger_matched,
            MuonBPark_isMuonWithTighterEtaAndPtReq,
            MuonBPark_passSingleMuonLike, MuonBPark_passDoubleMuonLike,
            passSingleMuonExclusive, passDoubleMuonExclusive,
            nMuon, Muon_eta, Muon_phi,
            indexes_multivertices)
        """)
        for ib, branch in enumerate(branches):
            df = df.Define(branch, f"muonsv_indexes.at({ib})")

        df = df.Filter("muonSV_chi2_trig_index >= 0", "MuonSV has trigger-matched muon")

        return df, branches


def DQCDTriggerSelection2024RDF(*args, **kwargs):
    return lambda: DQCDTriggerSelection2024RDFProducer(*args, **kwargs)


class DQCDLooseMuonSelectionRDFProducer():
    def __init__(self, *args, **kwargs):
        if not os.getenv("_DQCDLooseMuonSelection"):
            os.environ["_DQCDLooseMuonSelection"] = "DQCDLooseMuonSelection"
            ROOT.gInterpreter.Declare("""
                #include <algorithm>    // std::find
                #include <vector>       // std::vector
                #include "DataFormats/Math/interface/deltaR.h"

                using Vfloat = const ROOT::RVec<float>&;
                using Vint = const ROOT::RVec<int>&;
                using Vbool = const ROOT::RVec<bool>&;
                int are_all_muonsv_loose(
                    int nmuonSV, Vfloat muonSV_chi2, Vfloat muonSV_dR,
                    Vint muonSV_mu1index, Vint muonSV_mu2index, 
                    Vbool Muon_looseId,
                    Vint indexes_multivertices
                )
                {
                    if (indexes_multivertices.size() == 0)
                        return 0;
                    for (size_t imuonSV = 0; imuonSV < nmuonSV; imuonSV++) {
                        if (muonSV_dR[imuonSV] > 1.2)
                            continue;
                        if (indexes_multivertices.size() > 0) {
                            // index has to be selected by the DQCDMuonSVSelectionRDF module
                            if (std::find(indexes_multivertices.begin(), indexes_multivertices.end(),
                                    imuonSV) == indexes_multivertices.end())
                                // imuonSV not in the ones selected from the multivertices
                                continue;
                        }

                        // Requires both muons from the SV to be loose muon
                        if (!((Muon_looseId[muonSV_mu1index[imuonSV]] == 1)
                                && (Muon_looseId[muonSV_mu2index[imuonSV]] == 1)))
                            return 0;
                    }
                    return 1;
                }
            """)

    def run(self, df):
        df = df.Filter(
            "are_all_muonsv_loose(nmuonSV, muonSV_chi2, muonSV_dR, "
                "muonSV_mu1index, muonSV_mu2index, Muon_looseId, indexes_multivertices) == 1",
            "MuonSV(s) has/ve two loose muons"
        )
        return df, []


def DQCDLooseMuonSelectionRDF(*args, **kwargs):
    return lambda: DQCDLooseMuonSelectionRDFProducer(*args, **kwargs)


class DummyMinChi2RDFProducer():

    def run(self, df):
        branches = [
            "muon1_sv_bestchi2_pt",
            "muon1_sv_bestchi2_eta",
            "muon1_sv_bestchi2_phi",
            "muon1_sv_bestchi2_mass",
            "muon2_sv_bestchi2_pt",
            "muon2_sv_bestchi2_eta",
            "muon2_sv_bestchi2_phi",
            "muon2_sv_bestchi2_mass",
            "muonSV_bestchi2_chi2",
            "muonSV_bestchi2_pAngle",
            "muonSV_bestchi2_dlen",
            "muonSV_bestchi2_dlenSig",
            "muonSV_bestchi2_dxy",
            "muonSV_bestchi2_dxySig",
            "muonSV_bestchi2_x",
            "muonSV_bestchi2_y",
            "muonSV_bestchi2_z",
            "muonSV_bestchi2_mass"
        ]
        df = df.Define("muon1_sv_bestchi2_pt", "muonSV_mu1pt.at(min_chi2_index)")
        df = df.Define("muon1_sv_bestchi2_eta", "muonSV_mu1eta.at(min_chi2_index)")
        df = df.Define("muon1_sv_bestchi2_phi", "muonSV_mu1phi.at(min_chi2_index)")
        df = df.Define("muon1_sv_bestchi2_mass", "0.1057")
        df = df.Define("muon2_sv_bestchi2_pt", "muonSV_mu2pt.at(min_chi2_index)")
        df = df.Define("muon2_sv_bestchi2_eta", "muonSV_mu2eta.at(min_chi2_index)")
        df = df.Define("muon2_sv_bestchi2_phi", "muonSV_mu2phi.at(min_chi2_index)")
        df = df.Define("muon2_sv_bestchi2_mass", "0.1057")

        for v in ["chi2", "pAngle", "dlen", "dlenSig", "dxy", "dxySig", "x", "y", "z", "mass"]:
            df = df.Define("muonSV_bestchi2_%s" % v, "muonSV_%s.at(min_chi2_index)" % v)
            branches.append("muonSV_bestchi2_%s" % v)

        return df, branches


def DummyMinChi2RDF(*args, **kwargs):
    return lambda: DummyMinChi2RDFProducer()



class AdditionalMuonDQCDRDFProducer():
    def __init__(self, *args, **kwargs):
        ROOT.gInterpreter.Declare("""
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            std::vector<int> get_add_muon_indexes(
                Vint indexes_multivertices,
                Vint muonSV_mu1index, Vint muonSV_mu2index,
                int nMuon, Vfloat Muon_pt, Vfloat Muon_phi, Vfloat Muon_eta)
            {
                std::vector<int> add_muon_indexes;
                for (size_t iMuon = 0; iMuon < nMuon; iMuon++) {
                    bool found = false;
                    for (auto &muonSV_index: indexes_multivertices) {
                        if (muonSV_mu1index[muonSV_index] == iMuon || muonSV_mu2index[muonSV_index] == iMuon) {
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        add_muon_indexes.push_back(iMuon);
                    }
                }
                return add_muon_indexes;
            }
        """)

    def run(self, df):
        # df = df.Filter("event == 17031")
        df = df.Define("add_muon_indexes", "get_add_muon_indexes(indexes_multivertices, "
            "muonSV_mu1index, muonSV_mu2index, nMuon, Muon_pt, Muon_phi, Muon_eta)")
        return df, ["add_muon_indexes"]


def AdditionalMuonDQCDRDF(*args, **kwargs):
    return lambda: AdditionalMuonDQCDRDFProducer(*args, **kwargs)


class AdditionalMuonVarDQCDRDFProducer():
    def __init__(self, *args, **kwargs):
        ROOT.gInterpreter.Declare("""
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            ROOT::RVec<int> get_intvar_additional_muons(Vint vec, Vint muon_indexes) {
                std::vector<int> var_vec;
                for (auto &muon_index: muon_indexes) {
                    var_vec.push_back(vec[muon_index]);
                }
                return ROOT::RVec<int>(var_vec.data(), var_vec.size());
            }
            ROOT::RVec<float> get_floatvar_additional_muons(Vfloat vec, Vint muon_indexes) {
                std::vector<float> var_vec;
                for (auto &muon_index: muon_indexes) {
                    var_vec.push_back(vec[muon_index]);
                }
                return ROOT::RVec<float>(var_vec.data(), var_vec.size());
            }
        """)

    def run(self, df):
        return df, []


def AdditionalMuonVarDQCDRDF(*args, **kwargs):
    return lambda: AdditionalMuonVarDQCDRDFProducer(*args, **kwargs)


class AllMassDQCDRDFProducer():
    def __init__(self, *args, **kwargs):
        ROOT.gInterpreter.Declare("""
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            ROOT::RVec<float> get_all_masses(int cat_index, float muonSV_bestchi2_mass, Vfloat mass_multivertices) {
                std::vector<float> masses;
                if (cat_index == 0)
                    masses.push_back(muonSV_bestchi2_mass);
                else
                    for (auto &mass: mass_multivertices)
                        masses.push_back(mass);
                return ROOT::RVec<float>(masses.data(), masses.size());
            }
        """)

    def run(self, df):
        return df, []


def AllMassDQCDRDF(*args, **kwargs):
    return lambda: AllMassDQCDRDFProducer(*args, **kwargs)


class MuonDeltaRDQCDRDFProducer():
    def __init__(self, *args, **kwargs):
        ROOT.gInterpreter.Declare("""
            #include <algorithm>    // std::find
            #include <vector>       // std::vector
            #include "DataFormats/Math/interface/deltaR.h"
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            std::vector<float> get_deltaR_allmuons(Vint indexes_multivertices, Vint add_muon_indexes,
                Vfloat muonSV_mu1eta, Vfloat muonSV_mu1phi,
                Vfloat muonSV_mu2eta, Vfloat muonSV_mu2phi,
                Vfloat Muon_eta, Vfloat Muon_phi
            ) {
                std::vector<float> deltaR;
                for (auto &iadd_muon: add_muon_indexes) {
                    std::vector<float> deltaR_thismuon;
                    for (auto &imuonsv_muon: indexes_multivertices) {
                        deltaR_thismuon.push_back(reco::deltaR(
                            muonSV_mu1eta[imuonsv_muon], muonSV_mu1phi[imuonsv_muon],
                            Muon_eta[iadd_muon], Muon_phi[iadd_muon]
                        ));
                        deltaR_thismuon.push_back(reco::deltaR(
                            muonSV_mu2eta[imuonsv_muon], muonSV_mu2phi[imuonsv_muon],
                            Muon_eta[iadd_muon], Muon_phi[iadd_muon]
                        ));
                    }
                    if (deltaR_thismuon.size() > 0) {
                        auto elem = std::min_element(deltaR_thismuon.begin(), deltaR_thismuon.end());
                        deltaR.push_back(*elem);
                    }
                }
                return deltaR;
            }
        """)

    def run(self, df):
        df = df.Define("min_add_muon_deltaR_std", "get_deltaR_allmuons(indexes_multivertices, "
            "add_muon_indexes, muonSV_mu1eta, muonSV_mu1phi, muonSV_mu2eta, muonSV_mu2phi, "
            "Muon_eta, Muon_phi)").Define("min_add_muon_deltaR",
            "ROOT::RVec<float>(min_add_muon_deltaR_std.data(), min_add_muon_deltaR_std.size())")

        # df = df.Define("muonSV_bestchi2_mass_addeta",
            # "get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                # "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4"
            # "].size() > 0 ? muonSV_bestchi2_mass : -1")

        # df = df.Define("muonSV_bestchi2_mass_addloose_eta",
            # "get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                # "get_intvar_additional_muons(Muon_looseId, add_muon_indexes) == 1 && "
                # "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4"
            # "].size() > 0 ? muonSV_bestchi2_mass : -1")

        # df = df.Define("muonSV_bestchi2_mass_addeta_dr",
            # "get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                # "min_add_muon_deltaR > 0.1 && "
                # "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4"
            # "].size() > 0 ? muonSV_bestchi2_mass : -1")

        # df = df.Define("muonSV_bestchi2_mass_addloose_eta_dr",
            # "get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                # "min_add_muon_deltaR > 0.1 && "
                # "get_intvar_additional_muons(Muon_looseId, add_muon_indexes) == 1 && "
                # "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4"
            # "].size() > 0 ? muonSV_bestchi2_mass : -1")

        return df, ["min_add_muon_deltaR",
            # "muonSV_bestchi2_mass_addeta", "muonSV_bestchi2_mass_addloose_eta",
            # "muonSV_bestchi2_mass_addeta_dr", "muonSV_bestchi2_mass_addloose_eta_dr"
        ]


def MuonDeltaRDQCDRDF(*args, **kwargs):
    return lambda: MuonDeltaRDQCDRDFProducer(*args, **kwargs)
