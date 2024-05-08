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


class DQCDGenEffRDFProducer():
    def __init__(self, *args, **kwargs):
        self.displaced_pdgid = kwargs.pop("displaced_pdgid", 9900015)

        ROOT.gInterpreter.Declare("""
        #include <cmath>
        using Vfloat = const ROOT::RVec<float>&;
        using Vint = const ROOT::RVec<int>&;

        std::vector<std::vector<int>> get_eff(
            int displaced_pdgid, Vint GenPart_pdgId, Vint GenPart_genPartIdxMother,
            Vfloat GenPart_vertex_x, Vfloat GenPart_vertex_y, Vfloat GenPart_vertex_z,
            Vfloat muonSV_x, Vfloat muonSV_y, Vfloat muonSV_z)
        {
            std::vector <int> is_muon_decay;
            std::vector <int> is_sv_efficient;
            for (size_t i = 0; i < GenPart_pdgId.size(); i++) {
                if (abs(GenPart_pdgId[i]) != displaced_pdgid) {
                    is_muon_decay.push_back(0);
                    is_sv_efficient.push_back(0);
                    continue;
                }
                bool found_muon_decay = false;
                bool found_sv = false;
                for (size_t idau = i + 1; idau < GenPart_pdgId.size(); idau++) {
                    if (abs(GenPart_pdgId[idau]) != 13)
                        continue;
                    if (GenPart_genPartIdxMother[idau] != i)
                        continue;
                    // we have found a muon coming from the decay of the dark photon
                    found_muon_decay = true;
                    // let's match its vertex to a muonSV vertex to compute the reco efficiency
                    for (size_t imuonSV = 0; imuonSV < muonSV_x.size(); imuonSV++) {
                        if (abs(GenPart_vertex_x[idau] - muonSV_x[imuonSV]) < 0.05 &&
                            abs(GenPart_vertex_y[idau] - muonSV_y[imuonSV]) < 0.05 &&
                            abs(GenPart_vertex_z[idau] - muonSV_z[imuonSV]) < 0.05
                        ) {
                            found_sv = true;
                            break;
                        }
                    }
                    break;
                }
                if (!found_muon_decay) {
                    is_muon_decay.push_back(0);
                    is_sv_efficient.push_back(0);
                } else {
                    is_muon_decay.push_back(1);
                    if (found_sv)
                        is_sv_efficient.push_back(1);
                    else
                        is_sv_efficient.push_back(0);
                }
            }
            return {is_muon_decay, is_sv_efficient};
        }
    """)

    def run(self, df):
        df = df.Define("tmp", "get_eff("
            f"{self.displaced_pdgid}, GenPart_pdgId, GenPart_genPartIdxMother, "
            "GenPart_vertex_x, GenPart_vertex_y, GenPart_vertex_z,"
            "muonSV_x, muonSV_y, muonSV_z)").Define(
                "GenPart_is_dark_photon_into_muons", "ROOT::RVec<int>(tmp[0].data(), tmp[0].size())"
            ).Define(
                "GenPart_is_dark_photon_into_muons_eff", "ROOT::RVec<int>(tmp[1].data(), tmp[1].size())"
            )
        return df, ["GenPart_is_dark_photon_into_muons", "GenPart_is_dark_photon_into_muons_eff"]


def DQCDGenEffRDF(*args, **kwargs):
    return lambda: DQCDGenEffRDFProducer(*args, **kwargs)
