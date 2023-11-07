from Corrections.JME.PUjetID_SF import PUjetID_SFRDFProducer
from analysis_tools.utils import import_root
ROOT = import_root()

class DQCDPUjetID_SFRDFProducer(PUjetID_SFRDFProducer):
    def __init__(self, year, *args, **kwargs):
        super(DQCDPUjetID_SFRDFProducer, self).__init__(year, *args, **kwargs)
        if not self.isUL:
            raise ValueError("DQCDPUjetID_SFRDF is not correctly implemented for legacy samples")

        self.lep_pt = f"muon_from_muonsv_pt{self.systs}"
        self.lep_eta = "muon_from_muonsv_eta"
        self.lep_phi = "muon_from_muonsv_phi"
        self.lep_mass = f"muon_from_muonsv_mass{self.systs}"

        ROOT.gInterpreter.Declare("""
            const float muon_mass = 0.1057;
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            std::vector<ROOT::RVec<float>> get_muons_from_muonsv(
                int cat_index, Vint indexes_multivertices,
                Vfloat muonSV_mu1pt, Vfloat muonSV_mu2pt,
                Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta,
                Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi
            )
            {
                int nmuons = 2;
                if (cat_index != 0)
                    nmuons = 2 * 2 * cat_index;
                ROOT::RVec<float> muon_from_muonsv_pt(nmuons, 0);
                ROOT::RVec<float> muon_from_muonsv_eta(nmuons, 0);
                ROOT::RVec<float> muon_from_muonsv_phi(nmuons, 0);
                ROOT::RVec<float> muon_from_muonsv_mass(nmuons, muon_mass);
                for (size_t iMuonSV = 0; iMuonSV < indexes_multivertices.size(); iMuonSV++) {
                    muon_from_muonsv_pt[2 * iMuonSV] = muonSV_mu1pt[iMuonSV];
                    muon_from_muonsv_pt[2 * iMuonSV + 1] = muonSV_mu2pt[iMuonSV];
                    muon_from_muonsv_eta[2 * iMuonSV] = muonSV_mu1eta[iMuonSV];
                    muon_from_muonsv_eta[2 * iMuonSV + 1] = muonSV_mu2eta[iMuonSV];
                    muon_from_muonsv_phi[2 * iMuonSV] = muonSV_mu1phi[iMuonSV];
                    muon_from_muonsv_phi[2 * iMuonSV + 1] = muonSV_mu2phi[iMuonSV];
                }
                return {muon_from_muonsv_pt, muon_from_muonsv_eta,
                    muon_from_muonsv_phi, muon_from_muonsv_mass};
            }
        """)

    def run(self, df):
        df = df.Define(f"muon_sv_muons{self.systs}", """get_muons_from_muonsv(
            cat_index, indexes_multivertices, muonSV_mu1pt, muonSV_mu2pt,
            muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi
        )""")
        df = df.Define(f"muon_from_muonsv_pt{self.systs}", f"muon_sv_muons{self.systs}[0]")
        df = df.Define("muon_from_muonsv_eta", f"muon_sv_muons{self.systs}[1]")
        df = df.Define("muon_from_muonsv_phi", f"muon_sv_muons{self.systs}[2]")
        df = df.Define(f"muon_from_muonsv_mass{self.systs}", f"muon_sv_muons{self.systs}[3]")

        return super(DQCDPUjetID_SFRDFProducer, self).run(df)



def DQCDPUjetID_SFRDF(**kwargs):
    """
    Module to compute PU Jet Id scale factors for the DQCD analysis.
    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: DQCDPUjetID_SFRDF
            path: modules.DQCD_SF
            parameters:
                year: self.config.year
                isMC: self.dataset.process.isMC
                isUL: self.dataset.has_tag('ul')
                ispreVFP: self.config.get_aux("isPreVFP", False)

    """
    year = kwargs.pop("year")
    return lambda: DQCDPUjetID_SFRDFProducer(year, **kwargs)
