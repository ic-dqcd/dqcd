from analysis_tools.utils import import_root
ROOT = import_root()

class DQCDMuonSVSelectionRDFProducer():
    def __init__(self, *args, **kwargs):
        self.gen_mass = kwargs.pop("gen_mass", 20)

        ROOT.gInterpreter.Declare("""
            #include "DataFormats/Math/interface/deltaR.h"
            using Vint = const ROOT::RVec<int>&;
            using Vfloat = const ROOT::RVec<float>&;

            std::vector<ROOT::RVec<float>> get_multivertices(
                    int nmuonSV,
                    Vfloat muonSV_mass, Vfloat muonSV_chi2,
                    Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta,
                    Vint muonSV_mu1index, Vint muonSV_mu2index) {

                ROOT::RVec<float> mass_multivertices;
                ROOT::RVec<float> chi2_multivertices;
                if (nmuonSV > 0) {
                    for (size_t imuonSV = 0; imuonSV < nmuonSV - 1; imuonSV++) {
                        if (muonSV_chi2[imuonSV] > 10 ||
                                muonSV_mu1eta[imuonSV] == 0 || muonSV_mu2eta[imuonSV] == 0)
                            continue;
                        for (size_t imuonSV1 = imuonSV + 1; imuonSV1 < nmuonSV; imuonSV1++) {
                            if (muonSV_chi2[imuonSV1] > 10 ||
                                    muonSV_mu1eta[imuonSV1] == 0 || muonSV_mu2eta[imuonSV1] == 0)
                                continue;

                            if ((fabs(muonSV_mass[imuonSV] - muonSV_mass[imuonSV1]) / muonSV_mass[imuonSV]) < 3 * 0.01 * muonSV_mass[imuonSV]) {
                                if (muonSV_mu1index[imuonSV] != muonSV_mu1index[imuonSV1] &&
                                        muonSV_mu1index[imuonSV] != muonSV_mu2index[imuonSV1] &&
                                        muonSV_mu2index[imuonSV] != muonSV_mu1index[imuonSV1] &&
                                        muonSV_mu2index[imuonSV] != muonSV_mu2index[imuonSV1]) {
                                    mass_multivertices.push_back(muonSV_mass[imuonSV]);
                                    mass_multivertices.push_back(muonSV_mass[imuonSV1]);
                                    chi2_multivertices.push_back(muonSV_chi2[imuonSV]);
                                    chi2_multivertices.push_back(muonSV_chi2[imuonSV1]);
                                } // end if muon indexes
                            } // end if mass diff
                        } // end loop over imuonSV1
                    } // end loop over imuonSV
                }
                return {mass_multivertices, chi2_multivertices};
            } // end function

            //
            // function to get deltaR. Assuming all vectors have the same length n
            //
            ROOT::RVec<float> get_deltaR(int n, Vfloat eta1, Vfloat phi1, Vfloat eta2, Vfloat phi2) {
                ROOT::RVec<float> dR(n, 0);
                for (size_t i = 0; i < n; i++) {
                    dR[i] = reco::deltaR(eta1[i], phi1[i], eta2[i], phi2[i]);
                }
                return dR;
            }
            ROOT::RVec<float> get_bad_deltaR(int n, Vfloat eta1, Vfloat phi1, Vfloat eta2, Vfloat phi2) {
                ROOT::RVec<float> dR(n, 0);
                for (size_t i = 0; i < n; i++) {
                    dR[i] = sqrt(std::pow(phi1[i] - phi2[i], 2) + std::pow(eta1[i] - eta2[i], 2));
                }
                return dR;
            }

        """)

    def run(self, df):

        df = df.Filter("nmuonSV > 0")

        sigma = self.gen_mass * 0.01
        df = df.Define("nmuonSV_3sigma",
            f"muonSV_mass[abs(muonSV_mass - {self.gen_mass}) < 3 * {sigma}].size()")

        df = df.Define("multivertices_vars", """get_multivertices(nmuonSV, muonSV_mass, muonSV_chi2,
            muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1index, muonSV_mu2index)""")
        df = df.Define("mass_multivertices", "multivertices_vars[0]")
        df = df.Define("chi2_multivertices", "multivertices_vars[1]")

        df = df.Define("cat_index", "mass_multivertices.size() / 2")

        df = df.Define("min_chi2_multivertices", "Min(chi2_multivertices)")
        df = df.Define("min_chi2_index_multivertices", "ArgMin(chi2_multivertices)")
        df = df.Define("min_chi2_", "Min(muonSV_chi2)")
        df = df.Define("min_chi2_index", "ArgMin(muonSV_chi2)")

        df = df.Define("muonSV_dR", "get_deltaR(nmuonSV, muonSV_mu1eta, muonSV_mu1phi, muonSV_mu2eta, muonSV_mu2phi)")
        df = df.Define("muonSV_dR_bad", "get_bad_deltaR(nmuonSV, muonSV_mu1eta, muonSV_mu1phi, muonSV_mu2eta, muonSV_mu2phi)")
        df = df.Filter("muonSV_dR.at(min_chi2_index) < 1.2")

        # return df, []

        return df, ["nmuonSV_3sigma", "mass_multivertices", "chi2_multivertices",
            "min_chi2_index", "min_chi2_index_multivertices", "muonSV_dR", "muonSV_dR_bad"]


def DQCDMuonSVSelectionRDF(*args, **kwargs):
    return lambda: DQCDMuonSVSelectionRDFProducer(*args, **kwargs)