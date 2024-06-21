import os
from analysis_tools.utils import import_root
ROOT = import_root()

class DQCDReweighingRDFProducer():
    def __init__(self, *args, **kwargs):
        self.do_reweighing = kwargs.pop("do_reweighing", True)
        if self.do_reweighing:
            self.input_ctau = kwargs.pop("input_ctau", 100.)
            self.output_ctau = kwargs.pop("output_ctau", 100.)
            self.displaced_pdgid = kwargs.pop("displaced_pdgid", 9900015)

            if not os.getenv("_rew_dqcd"):
                os.environ["_rew_dqcd"] = "1"

                ROOT.gInterpreter.Declare("""
                    #include <cmath>
                    using Vfloat = const ROOT::RVec<float>&;
                    using Vint = const ROOT::RVec<int>&;

                    float get_weight_dqcd(int displaced_pdgid, float input_ctau, float output_ctau,
                        Vint GenPart_pdgId, Vint GenPart_genPartIdxMother, Vfloat GenPart_mass,
                        Vfloat GenPart_pt, Vfloat GenPart_vertex_x, Vfloat GenPart_vertex_y,
                        Vfloat GenPart_phi)
                    {
                        float weight = -1.;
                        std::vector<int> indexes;
                        for (size_t i = 0; i < GenPart_pdgId.size(); i++) {
                            if (abs(GenPart_pdgId[i]) != 13) {
                                continue;
                            }
                            auto mother_index = GenPart_genPartIdxMother[i];
                            if (mother_index == -1)
                                continue;
                            if (std::find(indexes.begin(), indexes.end(), mother_index) != std::end(indexes)) {
                                // Avoid considering the same LLP more than once
                                continue;
                            }
                            if (GenPart_pt[mother_index] < 15)
                                continue;
                            // Is the mother particle the LLP we are looking for?
                            if (abs(GenPart_pdgId[mother_index]) == displaced_pdgid) {
                                indexes.push_back(mother_index);

                                //auto lxy = std::sqrt(
                                //    std::pow(GenPart_vertex_x[i] - GenPart_vertex_x[mother_index], 2) +
                                //    std::pow(GenPart_vertex_y[i] - GenPart_vertex_y[mother_index], 2)
                                //);
                                //auto factor = (input_ctau / output_ctau) * std::exp(
                                //    ((1. / input_ctau) - (1. / output_ctau)) * (lxy * GenPart_mass[mother_index] / GenPart_pt[mother_index])
                                //    ((1. / input_ctau) - (1. / output_ctau)) * (lxy / (GenPart_mass[mother_index] * GenPart_pt[mother_index]))
                                //);

                                auto px = GenPart_pt[mother_index] * cos(GenPart_phi[mother_index]);
                                auto py = GenPart_pt[mother_index] * sin(GenPart_phi[mother_index]);

                                auto lxy_pt = (
                                    (GenPart_vertex_x[i] - GenPart_vertex_x[mother_index]) * px +
                                    (GenPart_vertex_y[i] - GenPart_vertex_y[mother_index]) * py
                                );
                                auto factor = (input_ctau / output_ctau) * std::exp(
                                    ((1. / input_ctau) - (1. / output_ctau)) * (lxy_pt * GenPart_mass[mother_index] / std::pow(GenPart_pt[mother_index], 2))
                                );
                                if (factor > weight)
                                    weight = factor;
                            }
                        }
                        if (weight >= 0)
                            return weight;
                        return 1;
                    }
                """)

    def run(self, df):
        # df = df.Filter("event == 190778")
        if not self.do_reweighing:
            df = df.Define("ctau_reweighing", "1.")
        else:
            df = df.Define("ctau_reweighing", "get_weight_dqcd("
                f"{self.displaced_pdgid}, {self.input_ctau}, {self.output_ctau}, "
                "GenPart_pdgId, GenPart_genPartIdxMother, GenPart_mass, "
                "GenPart_pt, GenPart_vertex_x, GenPart_vertex_y, GenPart_phi)")
        return df, ["ctau_reweighing"]


def DQCDReweighingRDF(*args, **kwargs):
    return lambda: DQCDReweighingRDFProducer(*args, **kwargs)


class DQCDRecoReweighingRDFProducer():
    def __init__(self, *args, **kwargs):
        self.do_reweighing = kwargs.pop("do_reweighing", True)
        if self.do_reweighing:
            self.input_ctau = kwargs.pop("input_ctau", 100.)
            self.output_ctau = kwargs.pop("output_ctau", 100.)
            self.displaced_pdgid = kwargs.pop("displaced_pdgid", 9900015)

            if not os.getenv("_recorew_dqcd"):
                os.environ["_recorew_dqcd"] = "1"

                ROOT.gInterpreter.Declare("""
                    #include "DataFormats/Math/interface/deltaR.h"
                    #include <cmath>
                    using Vfloat = const ROOT::RVec<float>&;
                    using Vint = const ROOT::RVec<int>&;

                    bool muonSV_sort (const std::pair<size_t, float>& svA,
                        const std::pair<size_t, float>& svB)
                    {
                      return (svA.second < svB.second);
                    }

                    float get_reco_weight_dqcd(int displaced_pdgid, float input_ctau, float output_ctau,
                        Vfloat muonSV_chi2, Vfloat muonSV_mu1eta, Vfloat muonSV_mu1phi,
                        Vfloat muonSV_mu2eta, Vfloat muonSV_mu2phi,
                        Vint GenPart_pdgId, Vint GenPart_genPartIdxMother, Vfloat GenPart_mass,
                        Vfloat GenPart_pt, Vfloat GenPart_vertex_x, Vfloat GenPart_vertex_y,
                        Vfloat GenPart_eta, Vfloat GenPart_phi)
                    {
                        // std::cout << "********************************" << std::endl;
                        // std::cout << "********************************" << std::endl;
                        // Trying to find the muonSV with the best chi2 that is matched to a gen LLP
                        // First, store index and chi2 to sort them
                        std::vector<std::pair<size_t, float>> index_chi2;
                        float weight = -1.;
                        bool muonSV_matches_gen = false;
                        for (size_t imuonSV = 0; imuonSV < muonSV_chi2.size(); imuonSV++) {
                            index_chi2.push_back(std::make_pair(imuonSV, muonSV_chi2[imuonSV]));
                        }
                        // std::cout << "muonSV_chi2.size()=" << muonSV_chi2.size() << std::endl;
                        if (index_chi2.size() >= 1) {
                            std::stable_sort(index_chi2.begin(), index_chi2.end(), muonSV_sort);
                            // once ordered, try to match them to a gen LLP
                            for (auto & elem: index_chi2) {
                                // std::cout << "imuonSV: " << elem.first << std::endl;
                                auto muon1_eta = muonSV_mu1eta[elem.first];
                                auto muon1_phi = muonSV_mu1phi[elem.first];
                                auto muon2_eta = muonSV_mu2eta[elem.first];
                                auto muon2_phi = muonSV_mu2phi[elem.first];
                                
                                // std::cout << muon1_eta << " " << muon1_phi << " ";
                                // std::cout << muon2_eta << " " << muon2_phi << std::endl;
                                
                                int saved_mother_index = -1;
                                std::vector<float> dR = {999., 999.,};
                                std::vector<int> genmuon_indexes = {-1, -1,};
                                for (size_t i = 0; i < GenPart_pdgId.size(); i++) {
                                    // std::cout << "Matching, iGenPart: " << i << std::endl;
                                    if (abs(GenPart_pdgId[i]) != 13) {
                                        continue;
                                    }
                                    // std::cout << GenPart_eta[i] << " " << GenPart_phi[i] << std::endl;
                                    bool matched = false;
                                    // match
                                    auto dR_mu1 = reco::deltaR(muon1_eta, muon1_phi,
                                        GenPart_eta[i], GenPart_phi[i]);
                                    auto dR_mu2 = reco::deltaR(muon2_eta, muon2_phi,
                                        GenPart_eta[i], GenPart_phi[i]);
                                    if ((dR_mu1 < 0.3) && (dR_mu1 < dR[0])) {
                                        // std::cout << "mu1 matched with " << i << std::endl;
                                        dR[0] = dR_mu1;
                                        genmuon_indexes[0] = i;
                                    }
                                    if ((dR_mu2 < 0.3) && (dR_mu2 < dR[1])) {
                                        // std::cout << "mu2 matched with " << i << std::endl;
                                        dR[1] = dR_mu2;
                                        genmuon_indexes[1] = i;
                                    }
                                }
                                // std::cout << "Final indexes " << genmuon_indexes[0] << " " << genmuon_indexes[1] << std::endl;
                                if (
                                    (genmuon_indexes[0] != -1) &&
                                    (genmuon_indexes[1] != -1) &&
                                    (genmuon_indexes[0] != genmuon_indexes[1])
                                ) {
                                    auto mother_index = GenPart_genPartIdxMother[genmuon_indexes[0]];
                                    if (mother_index != GenPart_genPartIdxMother[genmuon_indexes[1]]) {
                                        // std::cout << "Wrong muonSV assignment" << std::endl;
                                        continue;
                                    }
                                    // both muons belong to the same muonSV and gen particle
                                    muonSV_matches_gen = true;
                                    // extract the weight from it if it's the LLP
                                    // we are looking for (scenarioA, VP). If not (scenarioB, C),
                                    // find the corresponding LLP
                                    while (true) {
                                        if (mother_index == -1) {
                                            muonSV_matches_gen = false;
                                            break;
                                        } else if (abs(GenPart_pdgId[mother_index]) == displaced_pdgid) {
                                            auto px = GenPart_pt[mother_index] * cos(GenPart_phi[mother_index]);
                                            auto py = GenPart_pt[mother_index] * sin(GenPart_phi[mother_index]);

                                            auto lxy_pt = (
                                                (GenPart_vertex_x[genmuon_indexes[0]] - GenPart_vertex_x[mother_index]) * px +
                                                (GenPart_vertex_y[genmuon_indexes[0]] - GenPart_vertex_y[mother_index]) * py
                                            );
                                            weight = (input_ctau / output_ctau) * std::exp(
                                                ((1. / input_ctau) - (1. / output_ctau)) * (lxy_pt * GenPart_mass[mother_index] / std::pow(GenPart_pt[mother_index], 2))
                                            );
                                            break;
                                        } else {
                                            mother_index = GenPart_genPartIdxMother[mother_index];
                                        }
                                    }
                                }
                                if (muonSV_matches_gen) {
                                    // std::cout << weight << std::endl;
                                    break;
                                }
                            } // loop over ordered muonSVs
                        }
                        if (!muonSV_matches_gen) {
                            // we couldn't find a gen-matched muonSV. Let's extract the weight from
                            // the mean of the weights from all LLPs that end up decaying into muons
                            std::vector<float> weights;
                            std::vector<int> indexes;
                            for (size_t i = 0; i < GenPart_pdgId.size(); i++) {
                                // std::cout << "iGenPart: " << i << std::endl;
                                if (abs(GenPart_pdgId[i]) != 13) {
                                    continue;
                                }
                                auto mother_index = GenPart_genPartIdxMother[i];
                                // find the LLP
                                while (true) {
                                    // std::cout << "mother_index: " << mother_index << std::endl;
                                    if (mother_index == -1)
                                        break;
                                    if (std::find(indexes.begin(), indexes.end(), mother_index) != std::end(indexes)) {
                                        // Avoid considering the same LLP more than once
                                        break;
                                    }
                                    if (abs(GenPart_pdgId[mother_index]) == displaced_pdgid) {
                                        indexes.push_back(mother_index);
                                        auto px = GenPart_pt[mother_index] * cos(GenPart_phi[mother_index]);
                                        auto py = GenPart_pt[mother_index] * sin(GenPart_phi[mother_index]);

                                        auto lxy_pt = (
                                            (GenPart_vertex_x[i] - GenPart_vertex_x[mother_index]) * px +
                                            (GenPart_vertex_y[i] - GenPart_vertex_y[mother_index]) * py
                                        );
                                        auto w = (input_ctau / output_ctau) * std::exp(
                                            ((1. / input_ctau) - (1. / output_ctau)) * (lxy_pt * GenPart_mass[mother_index] / std::pow(GenPart_pt[mother_index], 2))
                                        );
                                        // std::cout << w << std::endl;
                                        weights.push_back(w);
                                        break;
                                    } else {
                                        mother_index = GenPart_genPartIdxMother[mother_index];
                                    }
                                }
                            }
                            // std::cout << "Size: " << weights.size() << std::endl;
                            if (weights.size() > 0) {
                                // get the final weight from the mean of all weights
                                for (auto &w: weights) {
                                    // std::cout << "w " << w << std::endl;
                                    if (weight == -1.)
                                        weight = w;
                                    else
                                        weight += w;
                                }
                                weight /= weights.size();
                            } else {
                                weight = 5.;
                            }
                        }
                        // std::cout << weight << std::endl;
                        return weight;
                    }
                """)

    def run(self, df):
        # df = df.Filter("event == 827601")
        if not self.do_reweighing:
            df = df.Define("ctau_reweighing", "1.")
        else:
            df = df.Define("ctau_reweighing", "get_reco_weight_dqcd("
                f"{self.displaced_pdgid}, {self.input_ctau}, {self.output_ctau}, "
                "muonSV_chi2, muonSV_mu1eta, muonSV_mu1phi, muonSV_mu2eta,  muonSV_mu2phi, "
                "GenPart_pdgId, GenPart_genPartIdxMother, GenPart_mass, "
                "GenPart_pt, GenPart_vertex_x, GenPart_vertex_y, GenPart_eta, GenPart_phi)")
        return df, ["ctau_reweighing"]


def DQCDRecoReweighingRDF(*args, **kwargs):
    return lambda: DQCDRecoReweighingRDFProducer(*args, **kwargs)



class DQCDGenEffRDFProducer():
    def __init__(self, *args, **kwargs):
        self.displaced_pdgid = kwargs.pop("displaced_pdgid", 9900015)

        ROOT.gInterpreter.Declare("""
            #include <cmath>
            #include "DataFormats/Math/interface/deltaR.h"
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            using Vbool = const ROOT::RVec<bool>&;

            std::vector<std::vector<int>> get_eff(
                int displaced_pdgid, Vint GenPart_pdgId, Vint GenPart_genPartIdxMother,
                Vfloat GenPart_vertex_x, Vfloat GenPart_vertex_y, Vfloat GenPart_vertex_z,
                Vfloat muonSV_x, Vfloat muonSV_y, Vfloat muonSV_z,
                Vint muonSV_mu1index, Vint muonSV_mu2index,
                Vfloat muonSV_mu1eta, Vfloat muonSV_mu1phi,
                Vfloat muonSV_mu2eta, Vfloat muonSV_mu2phi,
                Vfloat muonSV_chi2, Vbool Muon_looseId,
                int nMuonBPark, Vfloat MuonBPark_eta, Vfloat MuonBPark_phi,
                Vbool MuonBPark_fired_HLT_Mu9_IP6
            )
            {
                // start by filtering muonSVs by chi2 and loose muons
                std::vector<float> good_muonSV_vertex_x, good_muonSV_vertex_y, good_muonSV_vertex_z;
                std::vector<bool> good_muonSV_triggered;
                float bestchi2 = 999;
                int ibestchi2 = -1;
                for (size_t imuonSV = 0; imuonSV < muonSV_x.size(); imuonSV++) {
                    if (!(Muon_looseId[muonSV_mu1index[imuonSV]])
                            || !(Muon_looseId[muonSV_mu2index[imuonSV]]))
                        continue;
                    if (muonSV_chi2[imuonSV] > 10)
                        continue;

                    auto mu1eta = muonSV_mu1eta[imuonSV];
                    auto mu1phi = muonSV_mu1phi[imuonSV];
                    auto mu2eta = muonSV_mu2eta[imuonSV];
                    auto mu2phi = muonSV_mu2phi[imuonSV];
                    bool is_triggersv = false;
                    for (size_t iMuonBPark = 0; iMuonBPark < nMuonBPark; iMuonBPark++) {
                        // std::cout << "MuonBPark " <<  iMuonBPark
                        //     << MuonBPark_eta[iMuonBPark] << " "
                        //     << MuonBPark_phi[iMuonBPark] << " "
                        //     << MuonBPark_fired_HLT_Mu9_IP6[iMuonBPark] << std::endl;
                        if (!MuonBPark_fired_HLT_Mu9_IP6[iMuonBPark])
                            continue;
                        if ((reco::deltaR(mu1eta, mu1phi,
                            MuonBPark_eta[iMuonBPark], MuonBPark_phi[iMuonBPark]) < 0.1)
                            || 
                            (reco::deltaR(mu2eta, mu2phi,
                            MuonBPark_eta[iMuonBPark], MuonBPark_phi[iMuonBPark]) < 0.1)
                        ) {
                            is_triggersv = true;
                            break;
                        }
                    }

                    if (muonSV_chi2[imuonSV] < bestchi2 && is_triggersv) {
                        bestchi2 = muonSV_chi2[imuonSV];
                        ibestchi2 = imuonSV;
                    }
                    good_muonSV_vertex_x.push_back(muonSV_x[imuonSV]);
                    good_muonSV_vertex_y.push_back(muonSV_y[imuonSV]);
                    good_muonSV_vertex_z.push_back(muonSV_z[imuonSV]);
                    good_muonSV_triggered.push_back(is_triggersv);
                }
                
                std::vector <int> is_muon_decay;
                std::vector <int> is_sv_efficient;
                std::vector <int> is_triggersv_efficient;
                std::vector <int> is_triggersv_bestchi2_efficient;
                for (size_t i = 0; i < GenPart_pdgId.size(); i++) {
                    if (abs(GenPart_pdgId[i]) != displaced_pdgid) {
                        is_muon_decay.push_back(0);
                        is_sv_efficient.push_back(0);
                        is_triggersv_efficient.push_back(0);
                        is_triggersv_bestchi2_efficient.push_back(0);
                        continue;
                    }
                    bool found_muon_decay = false;
                    bool found_sv = false;
                    bool found_triggered_sv = false;
                    bool found_bestchi2_triggered_sv = false;
                    for (size_t idau = i + 1; idau < GenPart_pdgId.size(); idau++) {
                        if (abs(GenPart_pdgId[idau]) != 13)
                            continue;
                        if (GenPart_genPartIdxMother[idau] != i)
                            continue;
                        // we have found a muon coming from the decay of the dark photon
                        found_muon_decay = true;
                        // let's match its vertex to a muonSV vertex to compute the reco efficiency
                        // std::cout << "GenVertex " << GenPart_vertex_x[idau] << " "
                        //    << GenPart_vertex_y[idau] << " " << GenPart_vertex_z[idau] << std::endl;
                        for (size_t imuonSV = 0; imuonSV < good_muonSV_vertex_x.size(); imuonSV++) {
                            // std::cout << "Reco vertex: " << muonSV_x[imuonSV] << " "
                            //     << muonSV_y[imuonSV] << " "
                            //     << muonSV_z[imuonSV] << std::endl;
                            if (abs(GenPart_vertex_x[idau] - good_muonSV_vertex_x[imuonSV]) < 0.05 &&
                                abs(GenPart_vertex_y[idau] - good_muonSV_vertex_y[imuonSV]) < 0.05 &&
                                abs(GenPart_vertex_z[idau] - good_muonSV_vertex_z[imuonSV]) < 0.05
                            ) {
                                // std::cout << "Loose muon " << Muon_looseId[muonSV_mu1index[imuonSV]]
                                //     << " " << Muon_looseId[muonSV_mu1index[imuonSV]] << std::endl;
                                found_sv = true;
                                if (good_muonSV_triggered[imuonSV])
                                    found_triggered_sv = true;
                                
                                if (imuonSV == ibestchi2)
                                    found_bestchi2_triggered_sv = true;
                                break;
                            }
                        }
                        break;
                    }

                    is_muon_decay.push_back(found_muon_decay ? 1 : 0);
                    is_sv_efficient.push_back(found_sv ? 1 : 0);
                    is_triggersv_efficient.push_back(found_triggered_sv ? 1 : 0);
                    is_triggersv_bestchi2_efficient.push_back(found_bestchi2_triggered_sv ? 1 : 0);

                }
                return {is_muon_decay, is_sv_efficient,
                    is_triggersv_efficient, is_triggersv_bestchi2_efficient};
            }
        """)

    def run(self, df):
        # df = df.Filter("event == 827502")
        df = df.Define("tmp", "get_eff("
            f"{self.displaced_pdgid}, GenPart_pdgId, GenPart_genPartIdxMother, "
            "GenPart_vertex_x, GenPart_vertex_y, GenPart_vertex_z, "
            "muonSV_x, muonSV_y, muonSV_z, "
            "muonSV_mu1index, muonSV_mu2index, "
            "muonSV_mu1eta, muonSV_mu1phi, muonSV_mu2eta, muonSV_mu2phi, "
            "muonSV_chi2, Muon_looseId, "
            "nMuonBPark, MuonBPark_eta, MuonBPark_phi, "
            "MuonBPark_fired_HLT_Mu9_IP6)").Define(
                "GenPart_is_dark_photon_into_muons",
                "ROOT::RVec<int>(tmp[0].data(), tmp[0].size())"
            ).Define(
                "GenPart_is_dark_photon_into_muons_eff",
                "ROOT::RVec<int>(tmp[1].data(), tmp[1].size())"
            ).Define(
                "GenPart_is_dark_photon_into_muons_triggereff",
                "ROOT::RVec<int>(tmp[2].data(), tmp[2].size())"
            ).Define(
                "GenPart_is_dark_photon_into_muons_triggereff_bestchi2",
                "ROOT::RVec<int>(tmp[3].data(), tmp[3].size())"
            )
        return df, ["GenPart_is_dark_photon_into_muons", "GenPart_is_dark_photon_into_muons_eff",
            "GenPart_is_dark_photon_into_muons_triggereff", "GenPart_is_dark_photon_into_muons_triggereff_bestchi2"]


def DQCDGenEffRDF(*args, **kwargs):
    return lambda: DQCDGenEffRDFProducer(*args, **kwargs)


class DQCDGenVarRDFProducer():
    def __init__(self, *args, **kwargs):
        self.is_llp_signal = kwargs.pop("is_llp_signal", True)
        if self.is_llp_signal:
            self.displaced_pdgid = kwargs.pop("displaced_pdgid", 9900015)
            self.do_reweighing = kwargs.pop("do_reweighing", False)
            self.input_ctau = kwargs.pop("input_ctau", 100.)
            self.output_ctau = kwargs.pop("output_ctau", 100.)

            if not os.getenv("_gen_dqcd"):
                os.environ["_gen_dqcd"] = "1"

                ROOT.gInterpreter.Declare("""
                    #include <cmath>
                    using Vfloat = const ROOT::RVec<float>&;
                    using Vint = const ROOT::RVec<int>&;
                    std::vector<std::vector<float>> get_gen_lxy(
                        int displaced_pdgid, Vint GenPart_pdgId, Vint GenPart_genPartIdxMother,
                        Vfloat GenPart_vertex_x, Vfloat GenPart_vertex_y, Vfloat GenPart_vertex_z,
                        Vfloat GenPart_pt, Vfloat GenPart_eta, Vfloat GenPart_phi, Vfloat GenPart_mass,
                        bool do_reweighing, float input_ctau, float output_ctau
                    ) {
                        std::vector<float> gen_lxy, gen_lxyz, gen_ct, gen_p, gen_rew_weight;
                        for (size_t i = 0; i < GenPart_pdgId.size(); i++) {
                            gen_p.push_back(GenPart_pt[i] * cosh(GenPart_eta[i]));
                            if (abs(GenPart_pdgId[i]) != displaced_pdgid) {
                                gen_lxy.push_back(-1);
                                gen_lxyz.push_back(-1);
                                gen_ct.push_back(-1);
                                gen_rew_weight.push_back(0);
                                continue;
                            }
                            bool mumatched = false;
                            for (size_t idau = i + 1; idau < GenPart_pdgId.size(); idau++) {
                                if (abs(GenPart_pdgId[idau]) != 13)
                                    continue;
                                if (GenPart_genPartIdxMother[idau] != i)
                                    continue;
                                // we have found a muon coming from the decay of the dark photon
                                gen_lxy.push_back(std::sqrt(
                                    std::pow(GenPart_vertex_x[idau] - GenPart_vertex_x[i], 2) +
                                    std::pow(GenPart_vertex_y[idau] - GenPart_vertex_y[i], 2)
                                ));
                                auto lxyz = std::sqrt(
                                    std::pow(GenPart_vertex_x[idau] - GenPart_vertex_x[i], 2) +
                                    std::pow(GenPart_vertex_y[idau] - GenPart_vertex_y[i], 2) +
                                    std::pow(GenPart_vertex_z[idau] - GenPart_vertex_z[i], 2)
                                );
                                gen_lxyz.push_back(lxyz);
                                auto px = GenPart_pt[i] * cos(GenPart_phi[i]);
                                auto py = GenPart_pt[i] * sin(GenPart_phi[i]);
                                auto p = GenPart_pt[i] * cosh(GenPart_eta[i]);
                                auto lxy_pt = (
                                    (GenPart_vertex_x[idau] - GenPart_vertex_x[i]) * px +
                                    (GenPart_vertex_y[idau] - GenPart_vertex_y[i]) * py
                                );
                                auto ct = GenPart_mass[i] * 10 * lxyz / p;
                                gen_ct.push_back(lxy_pt * GenPart_mass[i] / std::pow(GenPart_pt[i], 2));
                                mumatched = true;
                                if (do_reweighing) {
                                    auto weight = ((1. / output_ctau) * std::exp(-ct/output_ctau)) /
                                        ((1. / input_ctau) * std::exp(-ct/input_ctau));
                                    gen_rew_weight.push_back(weight);
                                } else {
                                    gen_rew_weight.push_back(1.);
                                }
                                break;
                            }
                            if (!mumatched) {
                                gen_lxy.push_back(-1);
                                gen_lxyz.push_back(-1);
                                gen_ct.push_back(-1);
                                gen_rew_weight.push_back(0);
                            }
                        }
                        return {gen_lxy, gen_lxyz, gen_ct, gen_p, gen_rew_weight};
                    }
                """)

    def run(self, df):
        df = df.Define("tmp_gen", "get_gen_lxy("
            f"{self.displaced_pdgid}, GenPart_pdgId, GenPart_genPartIdxMother, "
                "GenPart_vertex_x, GenPart_vertex_y, GenPart_vertex_z, "
                "GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass, "
                f"{str(self.do_reweighing).lower()}, {self.input_ctau}, {self.output_ctau})"
            ).Define("GenPart_lxy", "ROOT::RVec<float>(tmp_gen[0].data(), tmp_gen[0].size())"
            ).Define("GenPart_lxyz", "ROOT::RVec<float>(tmp_gen[1].data(), tmp_gen[1].size())"
            ).Define("GenPart_ct", "ROOT::RVec<float>(tmp_gen[2].data(), tmp_gen[2].size())"
            ).Define("GenPart_p", "ROOT::RVec<float>(tmp_gen[3].data(), tmp_gen[3].size())"
            ).Define("GenPart_rew_weight", "ROOT::RVec<float>(tmp_gen[4].data(), tmp_gen[4].size())"
            )
        return df, ["GenPart_lxy", "GenPart_lxyz", "GenPart_ct", "GenPart_p", "GenPart_rew_weight"]


def DQCDGenVarRDF(*args, **kwargs):
    return lambda: DQCDGenVarRDFProducer(*args, **kwargs)


class DQCDGenVarPerVertexRDFProducer():
    def run(self, df):
        df = df.Define("tmp_lxy", "GenPart_lxy[GenPart_lxy > 0]")
        df = df.Define("tmp_rew_weight", "GenPart_rew_weight[GenPart_lxy > 0]")

        df = df.Define("GenDark_lxy_0", "tmp_lxy.size() > 0 ? tmp_lxy.at(0) : -1")
        df = df.Define("GenDark_lxy_1", "tmp_lxy.size() > 1 ? tmp_lxy.at(1) : -1")
        df = df.Define("GenDark_lxy_2", "tmp_lxy.size() > 2 ? tmp_lxy.at(2) : -1")
        df = df.Define("GenDark_lxy_3", "tmp_lxy.size() > 3 ? tmp_lxy.at(3) : -1")
        df = df.Define("GenDark_lxy_4", "tmp_lxy.size() > 4 ? tmp_lxy.at(4) : -1")
        df = df.Define("GenDark_lxy_5", "tmp_lxy.size() > 5 ? tmp_lxy.at(5) : -1")
        df = df.Define("GenDark_lxy_6", "tmp_lxy.size() > 6 ? tmp_lxy.at(6) : -1")
        df = df.Define("GenDark_lxy_7", "tmp_lxy.size() > 7 ? tmp_lxy.at(7) : -1")
        df = df.Define("GenDark_lxy_8", "tmp_lxy.size() > 8 ? tmp_lxy.at(8) : -1")

        df = df.Define("GenDark_rew_weight_0", "tmp_rew_weight.size() > 0 ? tmp_rew_weight.at(0) : -1")
        df = df.Define("GenDark_rew_weight_1", "tmp_rew_weight.size() > 1 ? tmp_rew_weight.at(1) : -1")
        df = df.Define("GenDark_rew_weight_2", "tmp_rew_weight.size() > 2 ? tmp_rew_weight.at(2) : -1")
        df = df.Define("GenDark_rew_weight_3", "tmp_rew_weight.size() > 3 ? tmp_rew_weight.at(3) : -1")
        df = df.Define("GenDark_rew_weight_4", "tmp_rew_weight.size() > 4 ? tmp_rew_weight.at(4) : -1")
        df = df.Define("GenDark_rew_weight_5", "tmp_rew_weight.size() > 5 ? tmp_rew_weight.at(5) : -1")
        df = df.Define("GenDark_rew_weight_6", "tmp_rew_weight.size() > 6 ? tmp_rew_weight.at(6) : -1")
        df = df.Define("GenDark_rew_weight_7", "tmp_rew_weight.size() > 7 ? tmp_rew_weight.at(7) : -1")
        df = df.Define("GenDark_rew_weight_8", "tmp_rew_weight.size() > 8 ? tmp_rew_weight.at(8) : -1")

        return df, [f"GenDark_lxy_{i}" for i in range(9)] + [f"GenDark_rew_weight_{i}" for i in range(9)]


def DQCDGenVarPerVertexRDF(*args, **kwargs):
    return lambda: DQCDGenVarPerVertexRDFProducer()


class DQCDFullReweighingRDFProducer():
    def __init__(self, *args, **kwargs):
        self.do_reweighing = kwargs.pop("do_reweighing", True)
        # filename = os.path.expandvars("$CMT_BASE/../data/eff_gen.json")
        filename = os.path.expandvars("$CMT_BASE/../data/eff_gen_chi2.json")
        if self.do_reweighing:
            self.input_ctau = kwargs.pop("input_ctau", 100.)
            self.output_ctau = kwargs.pop("output_ctau", 100.)
            self.displaced_pdgid = kwargs.pop("displaced_pdgid", 9900015)

            if not os.getenv("_rew_dqcd"):
                os.environ["_rew_dqcd"] = "1"
                print(filename)
                ROOT.gSystem.Load("libDQCDModules.so")
                ROOT.gROOT.ProcessLine(f".L {os.path.expandvars('$CMSSW_BASE')}/src/DQCD/Modules/interface/EffGen.h")
                ROOT.gInterpreter.Declare("""
                    auto eff = EffGen("%s", "%s");
                """ % (filename, "geneff"))

    def run(self, df):
        # df = df.Filter("event == 827541")
        if not self.do_reweighing:
            df = df.Define("ctau_reweighing", "1.")
        else:
            # df = df.Define("ctau_reweighing", "eff.get_weight("
            df = df.Define("ctau_reweighing", "eff.get_weight_noeff("
                f"{self.displaced_pdgid}, {self.input_ctau}, {self.output_ctau}, "
                "GenPart_pdgId, GenPart_genPartIdxMother, GenPart_mass, "
                "GenPart_pt, GenPart_vertex_x, GenPart_vertex_y, GenPart_vertex_z, "
                "GenPart_eta, GenPart_phi)")
        return df, ["ctau_reweighing"]


def DQCDFullReweighingRDF(*args, **kwargs):
    return lambda: DQCDFullReweighingRDFProducer(*args, **kwargs)



class DQCDOnlyRecoReweighingRDFProducer():
    def __init__(self, *args, **kwargs):
        self.do_reweighing = kwargs.pop("do_reweighing", True)
        if self.do_reweighing:
            self.input_ctau = kwargs.pop("input_ctau", 100.)
            self.output_ctau = kwargs.pop("output_ctau", 100.)

            if not os.getenv("_onlyrecorew_dqcd"):
                os.environ["_onlyrecorew_dqcd"] = "1"

                ROOT.gInterpreter.Declare("""
                    #include "DataFormats/Math/interface/deltaR.h"
                    #include <cmath>
                    using Vfloat = const ROOT::RVec<float>&;
                    using Vint = const ROOT::RVec<int>&;

                    float get_onlyreco_weight_dqcd(float input_ctau, float output_ctau,
                        int min_chi2_index, Vfloat muonSV_x, Vfloat muonSV_y, Vfloat muonSV_z,
                        Vfloat muonSV_pt, Vfloat muonSV_eta, Vfloat muonSV_mass)
                    {
                        auto lxyz = std::sqrt(
                            std::pow(muonSV_x[min_chi2_index], 2) +
                            std::pow(muonSV_y[min_chi2_index], 2) +
                            std::pow(muonSV_z[min_chi2_index], 2)
                        );
                        auto p = muonSV_pt[min_chi2_index] * cosh(muonSV_eta[min_chi2_index]);
                        auto ct = muonSV_mass[min_chi2_index] * 10 * lxyz / p;
                        auto weight = ((1. / output_ctau) * std::exp(-ct/output_ctau)) /
                            ((1. / input_ctau) * std::exp(-ct/input_ctau));

                        // float weight = (input_ctau / output_ctau) * std::exp(lxyz * ((1 / input_ctau) - (1 / output_ctau)));
                        // std::cout  << input_ctau << " " << output_ctau << " " << lxy << " " << weight << std::endl;
                        return weight;
                    }
                """)

    def run(self, df):
        # df = df.Filter("event == 827601")
        if not self.do_reweighing:
            df = df.Define("ctau_reweighing", "1.")
        else:
            df = df.Define("ctau_reweighing", "get_onlyreco_weight_dqcd("
                f"{self.input_ctau}, {self.output_ctau}, "
                "min_chi2_index, muonSV_x, muonSV_y, muonSV_z, muonSV_pt, muonSV_eta, muonSV_mass)")
        return df, ["ctau_reweighing"]


def DQCDOnlyRecoReweighingRDF(*args, **kwargs):
    return lambda: DQCDOnlyRecoReweighingRDFProducer(*args, **kwargs)


class DQCDMuonSVGenMatchedRDFProducer():
    def __init__(self, *args, **kwargs):
        self.is_signal = kwargs.pop("is_signal", True)
        if self.is_signal:
            self.displaced_pdgid = kwargs.pop("displaced_pdgid", 9900015)

            if not os.getenv("_genmuonsv_dqcd"):
                os.environ["_genmuonsv_dqcd"] = "1"

                ROOT.gInterpreter.Declare("""
                    #include <cmath>
                    #include "DataFormats/Math/interface/deltaR.h"
                    using Vfloat = const ROOT::RVec<float>&;
                    using Vint = const ROOT::RVec<int>&;

                    std::vector<int> are_muonSV_gen_matched(int displaced_pdgid,
                        Vint GenPart_pdgId, Vfloat GenPart_pt,
                        Vfloat GenPart_eta, Vfloat GenPart_phi,
                        Vfloat muonSV_eta, Vfloat muonSV_phi
                    ) {
                        std::vector<int> are_muonSV_gen_matched;
                        for (size_t i = 0; i < muonSV_eta.size(); i++) {
                            int is_muonSV_gen_matched = 0;
                            for (size_t igen = 0; igen < GenPart_pdgId.size(); igen++) {
                                if (abs(GenPart_pdgId[igen]) != displaced_pdgid)
                                    continue;
                                if (reco::deltaR(muonSV_eta[i], muonSV_phi[i],
                                        GenPart_eta[igen], GenPart_phi[igen]) < 0.1) {
                                    is_muonSV_gen_matched = 1;
                                    break;
                                }
                            }
                            are_muonSV_gen_matched.push_back(is_muonSV_gen_matched);
                        }
                        return are_muonSV_gen_matched;
                    }
                    
                """)

    def run(self, df):
        # df = df.Filter("event == 190778")
        if not self.is_signal:
            return df, []
        else:
            df = df.Define("muonSV_gen_matched", "are_muonSV_gen_matched("
                f"{self.displaced_pdgid}, "
                "GenPart_pdgId, GenPart_pt, GenPart_eta, GenPart_phi, "
                "muonSV_eta, muonSV_phi)")
        return df, ["muonSV_gen_matched"]


def DQCDMuonSVGenMatchedRDF(*args, **kwargs):
    return lambda: DQCDMuonSVGenMatchedRDFProducer(*args, **kwargs)


class DQCDReweighingWithRecoRDFProducer():
    def __init__(self, *args, **kwargs):
        self.do_reweighing = kwargs.pop("do_reweighing", True)
        if self.do_reweighing:
            self.input_ctau = kwargs.pop("input_ctau", 100.)
            self.output_ctau = kwargs.pop("output_ctau", 100.)
            self.displaced_pdgid = kwargs.pop("displaced_pdgid", 9900015)

            if not os.getenv("_recorew_dqcd"):
                os.environ["_recorew_dqcd"] = "1"

                ROOT.gInterpreter.Declare("""
                    #include "DataFormats/Math/interface/deltaR.h"
                    #include <cmath>
                    using Vfloat = const ROOT::RVec<float>&;
                    using Vint = const ROOT::RVec<int>&;

                    std::vector<float> get_reco_weights(int displaced_pdgid, float input_ctau, float output_ctau,
                        Vfloat muonSV_chi2, Vfloat muonSV_mu1eta, Vfloat muonSV_mu1phi,
                        Vfloat muonSV_mu2eta, Vfloat muonSV_mu2phi,
                        Vint GenPart_pdgId, Vint GenPart_genPartIdxMother, Vfloat GenPart_mass,
                        Vfloat GenPart_pt, Vfloat GenPart_vertex_x, Vfloat GenPart_vertex_y, Vfloat GenPart_vertex_z,
                        Vfloat GenPart_eta, Vfloat GenPart_phi)
                    {
                        std::vector<float> weights;
                        for (size_t i = 0; i < muonSV_chi2.size(); i++) {
                            auto muon1_eta = muonSV_mu1eta[i];
                            auto muon1_phi = muonSV_mu1phi[i];
                            auto muon2_eta = muonSV_mu2eta[i];
                            auto muon2_phi = muonSV_mu2phi[i];
                            
                            int saved_mother_index = -1;
                            std::vector<float> dR = {999., 999.,};
                            std::vector<int> genmuon_indexes = {-1, -1,};
                            for (size_t i = 0; i < GenPart_pdgId.size(); i++) {
                                // std::cout << "Matching, iGenPart: " << i << std::endl;
                                if (abs(GenPart_pdgId[i]) != 13) {
                                    continue;
                                }
                                // std::cout << GenPart_eta[i] << " " << GenPart_phi[i] << std::endl;
                                bool matched = false;
                                // match
                                auto dR_mu1 = reco::deltaR(muon1_eta, muon1_phi,
                                    GenPart_eta[i], GenPart_phi[i]);
                                auto dR_mu2 = reco::deltaR(muon2_eta, muon2_phi,
                                    GenPart_eta[i], GenPart_phi[i]);
                                if ((dR_mu1 < 0.3) && (dR_mu1 < dR[0])) {
                                    // std::cout << "mu1 matched with " << i << std::endl;
                                    dR[0] = dR_mu1;
                                    genmuon_indexes[0] = i;
                                }
                                if ((dR_mu2 < 0.3) && (dR_mu2 < dR[1])) {
                                    // std::cout << "mu2 matched with " << i << std::endl;
                                    dR[1] = dR_mu2;
                                    genmuon_indexes[1] = i;
                                }
                            }
                            // std::cout << "Final indexes " << genmuon_indexes[0] << " " << genmuon_indexes[1] << std::endl;
                            if ((genmuon_indexes[0] != -1) &&
                                (genmuon_indexes[1] != -1) &&
                                (genmuon_indexes[0] != genmuon_indexes[1])
                            ) {
                                auto mother_index = GenPart_genPartIdxMother[genmuon_indexes[0]];
                                if (mother_index != GenPart_genPartIdxMother[genmuon_indexes[1]]) {
                                    // std::cout << "Wrong muonSV assignment" << std::endl;
                                    weights.push_back(1.);
                                    continue;
                                }
                                // both muons belong to the same muonSV and gen particle
                                // extract the weight from it if it's the LLP
                                // we are looking for (scenarioA, VP). If not (scenarioB, C),
                                // find the corresponding LLP
                                while (true) {
                                    if (mother_index == -1) {
                                        weights.push_back(1.);
                                        break;
                                    } else if (abs(GenPart_pdgId[mother_index]) == displaced_pdgid) {
                                    
                                        auto lxyz = std::sqrt(
                                            std::pow(GenPart_vertex_x[genmuon_indexes[0]] - GenPart_vertex_x[mother_index], 2) +
                                            std::pow(GenPart_vertex_y[genmuon_indexes[0]] - GenPart_vertex_y[mother_index], 2) +
                                            std::pow(GenPart_vertex_z[genmuon_indexes[0]] - GenPart_vertex_z[mother_index], 2)
                                        );
                                        auto p = GenPart_pt[mother_index] * cosh(GenPart_eta[mother_index]);
                                        auto ct = GenPart_mass[mother_index] * 10 * lxyz / p;
                                        auto weight = ((1. / output_ctau) * std::exp(-ct/output_ctau)) /
                                            ((1. / input_ctau) * std::exp(-ct/input_ctau));
                                        weights.push_back(weight);
                                        break;
                                    } else {
                                        mother_index = GenPart_genPartIdxMother[mother_index];
                                    }
                                }
                            } else {
                                weights.push_back(1.);
                            }
                        }
                        return weights;
                    }
                """)

        else:
            if not os.getenv("_dummyrecorew_dqcd"):
                os.environ["_dummyrecorew_dqcd"] = "1"
                ROOT.gInterpreter.Declare("""
                    using Vfloat = const ROOT::RVec<float>&;
                    std::vector<float> get_dummy_reco_weights(Vfloat muonSV_chi2) {
                        std::vector<float> weights(muonSV_chi2.size(), 1.);
                        return weights;
                    }
                """)

    def run(self, df):
        # df = df.Filter("event == 970004")
        if not self.do_reweighing:
            df = df.Define("muonSV_ctau_rew", "get_dummy_reco_weights(muonSV_chi2)")
        else:
            df = df.Define("muonSV_ctau_rew", "get_reco_weights("
                f"{self.displaced_pdgid}, {self.input_ctau}, {self.output_ctau}, "
                "muonSV_chi2, muonSV_mu1eta, muonSV_mu1phi, muonSV_mu2eta,  muonSV_mu2phi, "
                "GenPart_pdgId, GenPart_genPartIdxMother, GenPart_mass, "
                "GenPart_pt, GenPart_vertex_x, GenPart_vertex_y, GenPart_vertex_z, "
                "GenPart_eta, GenPart_phi)")
        return df, ["muonSV_ctau_rew"]


def DQCDReweighingWithRecoRDF(*args, **kwargs):
    return lambda: DQCDReweighingWithRecoRDFProducer(*args, **kwargs)
