import os

from Corrections.JME.PUjetID_SF import PUjetID_SFRDFProducer
from analysis_tools.utils import import_root
import correctionlib

ROOT = import_root()
correctionlib.register_pyroot_binding()

class DQCDPUjetID_SFRDFProducer(PUjetID_SFRDFProducer):
    def __init__(self, year, *args, **kwargs):
        super(DQCDPUjetID_SFRDFProducer, self).__init__(year, *args, **kwargs)
        if not self.isUL:
            raise ValueError("DQCDPUjetID_SFRDF is not correctly implemented for legacy samples")

        self.lep_pt = f"muon_from_muonsv_pt{self.systs}"
        self.lep_eta = "muon_from_muonsv_eta"
        self.lep_phi = "muon_from_muonsv_phi"
        self.lep_mass = f"muon_from_muonsv_mass{self.systs}"

        if not os.getenv("_DQCDPUjetID_SF"):
            os.environ["_DQCDPUjetID_SF"] = "DQCDPUjetID_SF"
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


class DQCDIdSF_RDFProducer():
    def __init__(self, *args, **kwargs):
        # self.year = int(kwargs.pop("year"))
        self.isMC = kwargs.pop("isMC")
        self.isUL = kwargs.pop("isUL")

        filename = "${CMT_BASE}/../data/scale_factor2D_NUM_LooseID_DEN_SAMuons_absdxy_pt_TnP_2018_syst.json"

        if self.isMC and not self.isUL:
            raise ValueError("DQCDIdSF_RDF module only available for UL samples")

        if self.isMC:
            if "/libCorrectionsWrapper.so" not in ROOT.gSystem.GetLibraries():
                ROOT.gInterpreter.Load("libCorrectionsWrapper.so")
            ROOT.gInterpreter.Declare(os.path.expandvars(
                '#include "$CMSSW_BASE/src/Corrections/Wrapper/interface/custom_sf.h"'))
            ROOT.gInterpreter.ProcessLine(
                f'auto corr_dqcdid = MyCorrections("{os.path.expandvars(filename)}", '
                    '"NUM_LooseID_DEN_SAMuons_absdxy_pt_TnP_2018_syst");'
            )

            if not os.getenv("_DQCDIdSF"):
                os.environ["_DQCDIdSF"] = "DQCDIdSF"
                ROOT.gInterpreter.Declare("""
                    using Vfloat = const ROOT::RVec<float>&;
                    using Vint = const ROOT::RVec<int>&;
                    using Vbool = const ROOT::RVec<bool>&;
                    float get_dqcd_id_sf(Vint indexes_multivertices,
                        Vint muonSV_mu1index, Vint muonSV_mu2index,
                        Vfloat Muon_pt, Vfloat Muon_dxy, std::string syst)
                    {
                        float sf = 1.;
                        for (auto &index: indexes_multivertices) {
                            auto mu1_index = muonSV_mu1index[index];
                            auto mu2_index = muonSV_mu2index[index];
                            sf *= corr_dqcdid.eval({fabs(Muon_dxy[mu1_index]), Muon_pt[mu1_index], syst});
                            sf *= corr_dqcdid.eval({fabs(Muon_dxy[mu2_index]), Muon_pt[mu2_index], syst});
                        }
                        return sf;
                    }
                """)

    def run(self, df):
        if self.isMC:
            branches = ['idWeight', 'idWeight_up', 'idWeight_down']
            for branch_name, syst in zip(branches, ["sf", "systup", "systdown"]):
                df = df.Define(branch_name, """get_dqcd_id_sf(indexes_multivertices,
                    muonSV_mu1index, muonSV_mu2index, Muon_pt, Muon_dxy, "%s")""" % syst)
        else:
            branches = []
        return df, branches


def DQCDIdSF_RDF(**kwargs):
    """
    Module to compute muon Id scale factors for the DQCD analysis.
    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: DQCDIdSF_RDF
            path: modules.DQCD_SF
            parameters:
                isMC: self.dataset.process.isMC
                isUL: self.dataset.has_tag('ul')
    """
    return lambda: DQCDIdSF_RDFProducer(**kwargs)


class DQCDTrigSF_RDFProducer():
    def __init__(self, *args, **kwargs):
        # self.year = int(kwargs.pop("year"))
        self.isMC = kwargs.pop("isMC")
        self.isUL = kwargs.pop("isUL")

        # filename = "${CMT_BASE}/../data/scale_factor2D_trigger_absdxy_pt_TnP_2018_syst.json"
        filename = "${CMT_BASE}/../data/dqcd_sf_bestdrtag.json"

        if self.isMC and not self.isUL:
            raise ValueError("DQCDTrigSF_RDF module only available for UL samples")

        if self.isMC:
            if "/libBaseModules.so" not in ROOT.gSystem.GetLibraries():
                ROOT.gInterpreter.Load("libBaseModules.so")
            ROOT.gInterpreter.Declare(os.path.expandvars(
                '#include "$CMSSW_BASE/src/Base/Modules/interface/correctionWrapper.h"'))
            ROOT.gInterpreter.ProcessLine(
                f'auto corr_dqcdtrig = MyCorrections("{os.path.expandvars(filename)}", '
                    '"scale_factor2D_trigger_absdxy_pt_TnP_2018_syst");'
            )

            if not os.getenv("_DQCDTrigSF"):
                os.environ["_DQCDTrigSF"] = "DQCDTrigSF"
                ROOT.gInterpreter.Declare("""
                    using Vfloat = const ROOT::RVec<float>&;
                    using Vint = const ROOT::RVec<int>&;
                    using Vbool = const ROOT::RVec<bool>&;
                    float get_dqcd_trig_sf(
                        int muonSV_chi2_trig_muon1_index,
                        int muonSV_chi2_trig_muon2_index,
                        Vfloat Muon_pt, Vfloat Muon_dxy, std::string syst)
                    {
                        auto mu1_pt = -1., mu2_pt = -1., mu1_dxy = -1., mu2_dxy = -1.;
                        if (muonSV_chi2_trig_muon1_index >= 0) {
                            mu1_pt = Muon_pt[muonSV_chi2_trig_muon1_index];
                            mu1_dxy = Muon_dxy[muonSV_chi2_trig_muon1_index];
                        }
                        if (muonSV_chi2_trig_muon2_index >= 0) {
                            mu2_pt = Muon_pt[muonSV_chi2_trig_muon2_index];
                            mu2_dxy = Muon_dxy[muonSV_chi2_trig_muon2_index];
                        }
                        // this check should not be needed, as there is a filter in the trigger module to prevent this
                        if (mu1_pt == -1 && mu2_pt == -1)
                            return 1;
                        if (mu1_pt > mu2_pt)
                            return corr_dqcdtrig.eval({fabs(mu1_dxy), mu1_pt, syst});
                        return corr_dqcdtrig.eval({fabs(mu2_dxy), mu2_pt, syst});
                    }
                """)

    def run(self, df):
        if self.isMC:
            branches = ['trigSF', 'trigSF_up', 'trigSF_down']
            for branch_name, syst in zip(branches, ["sf", "systup", "systdown"]):
                df = df.Define(branch_name, """get_dqcd_trig_sf(
                    muonSV_chi2_trig_muon1_index, muonSV_chi2_trig_muon2_index,
                    Muon_pt, Muon_dxy, "%s")""" % syst)
        else:
            branches = []
        return df, branches


def DQCDTrigSF_RDF(**kwargs):
    """
    Module to compute muon Id scale factors for the DQCD analysis.
    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: DQCDIdSF_RDF
            path: modules.DQCD_SF
            parameters:
                isMC: self.dataset.process.isMC
                isUL: self.dataset.has_tag('ul')
    """
    return lambda: DQCDTrigSF_RDFProducer(**kwargs)
