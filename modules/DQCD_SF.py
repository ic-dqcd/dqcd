import os

#from Corrections.JME.PUjetID_SF import PUjetID_SFRDFProducer
from analysis_tools.utils import import_root
import correctionlib

ROOT = import_root()
correctionlib.register_pyroot_binding()
'''
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
'''

class DQCDIdSF_RDFProducer():
    def __init__(self, *args, **kwargs):
        # self.year = int(kwargs.pop("year"))
        self.isMC = kwargs.pop("isMC")
        self.isUL = kwargs.pop("isUL")

        # filename = "${CMT_BASE}/../data/scale_factor2D_NUM_LooseID_DEN_SAMuons_absdxy_pt_TnP_2018_syst.json"
        filename = "${CMT_BASE}/../data/id_sf.json"

        if self.isMC and not self.isUL:
            raise ValueError("DQCDIdSF_RDF module only available for UL samples")

        if self.isMC:
            if "/libBaseModules.so" not in ROOT.gSystem.GetLibraries():
                ROOT.gInterpreter.Load("libBaseModules.so")
            ROOT.gInterpreter.Declare(os.path.expandvars(
                '#include "$CMSSW_BASE/src/Base/Modules/interface/correctionWrapper.h"'))
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
                        Vfloat Muon_pt, Vfloat muonSV_dxy, std::string syst)
                    {
                        float sf = 1.;
                        for (auto &index: indexes_multivertices) {
                            auto mu1_index = muonSV_mu1index[index];
                            auto mu2_index = muonSV_mu2index[index];
                            sf *= corr_dqcdid.eval({fabs(muonSV_dxy[index]), Muon_pt[mu1_index], syst});
                            sf *= corr_dqcdid.eval({fabs(muonSV_dxy[index]), Muon_pt[mu2_index], syst});
                        }
                        return sf;
                    }
                """)

    def run(self, df):
        if self.isMC:
            branches = ['idWeight', 'idWeight_up', 'idWeight_down']
            for branch_name, syst in zip(branches, ["sf", "systup", "systdown"]):
                df = df.Define(branch_name, """get_dqcd_id_sf(indexes_multivertices,
                    muonSV_mu1index, muonSV_mu2index, Muon_pt, muonSV_dxy, "%s")""" % syst)
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
        # filename = "${CMT_BASE}/../data/dqcd_sf_bestdrtag.json"
        filename = "${CMT_BASE}/../data/trigger_sf.json"

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
                        int muonSV_chi2_trig_index,
                        Vfloat Muon_pt, Vfloat muonSV_dxy, std::string syst)
                    {
                        auto mu1_pt = -1., mu2_pt = -1.;
                        if (muonSV_chi2_trig_muon1_index >= 0) {
                            mu1_pt = Muon_pt[muonSV_chi2_trig_muon1_index];
                        }
                        if (muonSV_chi2_trig_muon2_index >= 0) {
                            mu2_pt = Muon_pt[muonSV_chi2_trig_muon2_index];
                        }
                        // this check should not be needed, as there is a filter in the trigger module to prevent this
                        if (mu1_pt == -1 && mu2_pt == -1)
                            return 1;
                        if (mu1_pt > mu2_pt)
                            return corr_dqcdtrig.eval({fabs(muonSV_dxy[muonSV_chi2_trig_index]), mu1_pt, syst});
                        return corr_dqcdtrig.eval({fabs(muonSV_dxy[muonSV_chi2_trig_index]), mu2_pt, syst});
                    }
                """)

    def run(self, df):
        if self.isMC:
            branches = ['trigSF', 'trigSF_up', 'trigSF_down']
            for branch_name, syst in zip(branches, ["sf", "systup", "systdown"]):
                df = df.Define(branch_name, """get_dqcd_trig_sf(
                    muonSV_chi2_trig_muon1_index, muonSV_chi2_trig_muon2_index,
                    muonSV_chi2_trig_index, Muon_pt, muonSV_dxy, "%s")""" % syst)
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


class DQCDTrigSF_mudxy_RDFProducer(DQCDTrigSF_RDFProducer):
    def __init__(self, *args, **kwargs):
        # self.year = int(kwargs.pop("year"))
        self.isMC = kwargs.pop("isMC")
        self.isUL = kwargs.pop("isUL")

        # filename = "${CMT_BASE}/../data/scale_factor2D_trigger_absdxy_pt_TnP_2018_syst.json"
        # filename = "${CMT_BASE}/../data/dqcd_sf_bestdrtag.json"
        filename = "${CMT_BASE}/../data/trigger_sf_mudxy.json"

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
                        auto mu1_pt = -1., mu2_pt = -1.;
                        if (muonSV_chi2_trig_muon1_index >= 0) {
                            mu1_pt = Muon_pt[muonSV_chi2_trig_muon1_index];
                        }
                        if (muonSV_chi2_trig_muon2_index >= 0) {
                            mu2_pt = Muon_pt[muonSV_chi2_trig_muon2_index];
                        }
                        // this check should not be needed, as there is a filter in the trigger module to prevent this
                        if (mu1_pt == -1 && mu2_pt == -1)
                            return 1;
                        if (mu1_pt > mu2_pt)
                            return corr_dqcdtrig.eval(
                                {fabs(Muon_dxy[muonSV_chi2_trig_muon1_index]), mu1_pt, syst});
                        return corr_dqcdtrig.eval(
                            {fabs(Muon_dxy[muonSV_chi2_trig_muon2_index]), mu2_pt, syst});
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


def DQCDTrigSF_mudxy_RDF(**kwargs):
    """
    Module to compute muon Id scale factors for the DQCD analysis.
    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: DQCDTrigSF_mudxy_RDF
            path: modules.DQCD_SF
            parameters:
                isMC: self.dataset.process.isMC
                isUL: self.dataset.has_tag('ul')
    """
    return lambda: DQCDTrigSF_mudxy_RDFProducer(**kwargs)


class DQCDTrigSF_alltriggers_RDFProducer(DQCDTrigSF_RDFProducer):
    def __init__(self, *args, **kwargs):
        # self.year = int(kwargs.pop("year"))
        self.isMC = kwargs.pop("isMC")
        self.isUL = kwargs.pop("isUL")

        # filename = "${CMT_BASE}/../data/scale_factor2D_trigger_absdxy_pt_TnP_2018_syst.json"
        # filename = "${CMT_BASE}/../data/dqcd_sf_bestdrtag.json"
        filename = "${CMT_BASE}/../data/trigger_sf_alltriggers.json"

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
                        Vfloat Muon_pt, Vfloat Muon_dxy, Vfloat Muon_dxyErr, std::string syst)
                    {
                        auto mu1_pt = -1., mu2_pt = -1.;
                        if (muonSV_chi2_trig_muon1_index >= 0) {
                            mu1_pt = Muon_pt[muonSV_chi2_trig_muon1_index];
                        }
                        if (muonSV_chi2_trig_muon2_index >= 0) {
                            mu2_pt = Muon_pt[muonSV_chi2_trig_muon2_index];
                        }
                        // this check should not be needed, as there is a filter in the trigger module to prevent this
                        if (mu1_pt == -1 && mu2_pt == -1)
                            return 1;
                        if (mu1_pt > mu2_pt)
                            return corr_dqcdtrig.eval(
                                {mu1_pt, fabs(Muon_dxy[muonSV_chi2_trig_muon1_index] / Muon_dxyErr[muonSV_chi2_trig_muon1_index]), syst});
                        return corr_dqcdtrig.eval(
                            {mu2_pt, fabs(Muon_dxy[muonSV_chi2_trig_muon2_index] / Muon_dxyErr[muonSV_chi2_trig_muon2_index]), syst});
                    }
                """)

    def run(self, df):
        if self.isMC:
            branches = ['trigSF', 'trigSF_up', 'trigSF_down']
            for branch_name, syst in zip(branches, ["sf", "systup", "systdown"]):
                df = df.Define(branch_name, """get_dqcd_trig_sf(
                    muonSV_chi2_trig_muon1_index, muonSV_chi2_trig_muon2_index,
                    Muon_pt, Muon_dxy, Muon_dxyErr, "%s")""" % syst)
        else:
            branches = []
        return df, branches


def DQCDTrigSF_alltriggers_RDF(**kwargs):
    """
    Module to compute muon Id scale factors for the DQCD analysis.
    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: DQCDTrigSF_alltriggers_RDF
            path: modules.DQCD_SF
            parameters:
                isMC: self.dataset.process.isMC
                isUL: self.dataset.has_tag('ul')
    """
    return lambda: DQCDTrigSF_alltriggers_RDFProducer(**kwargs)




class DQCDFilterEfficiencyRDFProducer():
    def __init__(self, *args, **kwargs):
        self.process_name = kwargs.pop("process_name", "")

    def run(self, df):
        efficiencies = {
            "scenarioA_mpi_10_mA_2p00_ctau_0p1": 0.350826,
            "scenarioA_mpi_10_mA_2p00_ctau_10": 0.350766,
            "scenarioA_mpi_1_mA_0p25_ctau_1p0": 0.779565,
            "scenarioA_mpi_1_mA_0p45_ctau_0p1": 0.807967,
            "scenarioA_mpi_1_mA_0p45_ctau_10": 0.807751,
            "scenarioA_mpi_1_mA_0p45_ctau_100": 0.808274,
            "scenarioA_mpi_1_mA_0p45_ctau_1p0": 0.807607,
            "scenarioA_mpi_2_mA_0p25_ctau_0p1": 0.772924,
            "scenarioA_mpi_2_mA_0p25_ctau_10": 0.773136,
            "scenarioA_mpi_2_mA_0p25_ctau_100": 0.772665,
            "scenarioA_mpi_2_mA_0p25_ctau_1p0": 0.774017,
            "scenarioA_mpi_2_mA_0p40_ctau_0p1": 0.80055,
            "scenarioA_mpi_10_mA_2p00_ctau_100": 0.349556,
            "scenarioA_mpi_2_mA_0p40_ctau_10": 0.800526,
            "scenarioA_mpi_2_mA_0p40_ctau_100": 0.800117,
            "scenarioA_mpi_2_mA_0p40_ctau_1p0": 0.800939,
            "scenarioA_mpi_2_mA_0p90_ctau_0p1": 0.690108,
            "scenarioA_mpi_2_mA_0p90_ctau_10": 0.689377,
            "scenarioA_mpi_2_mA_0p90_ctau_100": 0.689698,
            "scenarioA_mpi_2_mA_0p90_ctau_1p0": 0.689619,
            "scenarioA_mpi_4_mA_0p80_ctau_0p1": 0.376616,
            "scenarioA_mpi_4_mA_0p80_ctau_10": 0.377489,
            "scenarioA_mpi_4_mA_0p80_ctau_100": 0.378642,
            "scenarioA_mpi_10_mA_2p00_ctau_1p0": 0.350715,
            "scenarioA_mpi_4_mA_0p80_ctau_1p0": 0.377283,
            "scenarioA_mpi_4_mA_1p90_ctau_0p1": 0.58982,
            "scenarioA_mpi_4_mA_1p90_ctau_10": 0.590124,
            "scenarioA_mpi_4_mA_1p90_ctau_100": 0.589969,
            "scenarioA_mpi_4_mA_1p90_ctau_1p0": 0.58885,
            "scenarioA_mpi_10_mA_4p90_ctau_0p1": 0.321156,
            "scenarioA_mpi_10_mA_4p90_ctau_10": 0.322171,
            "scenarioA_mpi_10_mA_4p90_ctau_100": 0.321784,
            "scenarioA_mpi_10_mA_4p90_ctau_1p0": 0.321571,
            "scenarioA_mpi_1_mA_0p25_ctau_0p1": 0.780521,
            "scenarioA_mpi_1_mA_0p25_ctau_10": 0.779906,
            "scenarioA_mpi_1_mA_0p25_ctau_100": 0.779666,
            "vector_m_10_ctau_0p1_xiO_1_xiL_1": 0.52535,
            "vector_m_10_ctau_0p3_xiO_1_xiL_1": 0.52557,
            "vector_m_10_ctau_6_xiO_1_xiL_1": 0.52491,
            "vector_m_10_ctau_75_xiO_1_xiL_1": 0.52603,
            "vector_m_15_ctau_0p1_xiO_1_xiL_1": 0.47283,
            "vector_m_15_ctau_0p3_xiO_1_xiL_1": 0.47208,
            "vector_m_15_ctau_0p65_xiO_1_xiL_1": 0.47134,
            "vector_m_15_ctau_200_xiO_1_xiL_1": 0.47076,
            "vector_m_15_ctau_20_xiO_1_xiL_1": 0.47309,
            "vector_m_15_ctau_2_xiO_1_xiL_1": 0.47311,
            "vector_m_15_ctau_350_xiO_1_xiL_1": 0.4686,
            "vector_m_15_ctau_35_xiO_1_xiL_1": 0.47014,
            "vector_m_10_ctau_0p65_xiO_1_xiL_1": 0.52645,
            "vector_m_15_ctau_4_xiO_1_xiL_1": 0.46891,
            "vector_m_15_ctau_60_xiO_1_xiL_1": 0.46992,
            "vector_m_15_ctau_6_xiO_1_xiL_1": 0.47274,
            "vector_m_15_ctau_75_xiO_1_xiL_1": 0.47187,
            "vector_m_20_ctau_0p1_xiO_1_xiL_1": 0.42632,
            "vector_m_20_ctau_0p3_xiO_1_xiL_1": 0.42459,
            "vector_m_20_ctau_0p65_xiO_1_xiL_1": 0.42751,
            "vector_m_20_ctau_200_xiO_1_xiL_1": 0.42532,
            "vector_m_20_ctau_20_xiO_1_xiL_1": 0.42802,
            "vector_m_20_ctau_2_xiO_1_xiL_1": 0.42874,
            "vector_m_10_ctau_200_xiO_1_xiL_1": 0.52818,
            "vector_m_20_ctau_350_xiO_1_xiL_1": 0.42959,
            "vector_m_20_ctau_35_xiO_1_xiL_1": 0.42888,
            "vector_m_20_ctau_4_xiO_1_xiL_1": 0.42981,
            "vector_m_20_ctau_60_xiO_1_xiL_1": 0.427,
            "vector_m_20_ctau_6_xiO_1_xiL_1": 0.42912,
            "vector_m_20_ctau_75_xiO_1_xiL_1": 0.42513,
            "vector_m_2_ctau_0p1_xiO_1_xiL_1": 0.78131,
            "vector_m_2_ctau_0p3_xiO_1_xiL_1": 0.78148,
            "vector_m_2_ctau_0p65_xiO_1_xiL_1": 0.77889,
            "vector_m_2_ctau_200_xiO_1_xiL_1": 0.780616,
            "vector_m_10_ctau_20_xiO_1_xiL_1": 0.52219,
            "vector_m_2_ctau_20_xiO_1_xiL_1": 0.78213,
            "vector_m_2_ctau_2_xiO_1_xiL_1": 0.78181,
            "vector_m_2_ctau_350_xiO_1_xiL_1": 0.78054,
            "vector_m_2_ctau_35_xiO_1_xiL_1": 0.78132,
            "vector_m_2_ctau_4_xiO_1_xiL_1": 0.77872,
            "vector_m_2_ctau_60_xiO_1_xiL_1": 0.78462,
            "vector_m_2_ctau_6_xiO_1_xiL_1": 0.78039,
            "vector_m_2_ctau_75_xiO_1_xiL_1": 0.78055,
            "vector_m_5_ctau_0p1_xiO_1_xiL_1": 0.64237,
            "vector_m_5_ctau_0p3_xiO_1_xiL_1": 0.64505,
            "vector_m_10_ctau_2_xiO_1_xiL_1": 0.52757,
            "vector_m_5_ctau_0p65_xiO_1_xiL_1": 0.64537,
            "vector_m_5_ctau_200_xiO_1_xiL_1": 0.6453,
            "vector_m_5_ctau_20_xiO_1_xiL_1": 0.64688,
            "vector_m_5_ctau_2_xiO_1_xiL_1": 0.64396,
            "vector_m_5_ctau_350_xiO_1_xiL_1": 0.64539,
            "vector_m_5_ctau_35_xiO_1_xiL_1": 0.64529,
            "vector_m_5_ctau_4_xiO_1_xiL_1": 0.64329,
            "vector_m_5_ctau_60_xiO_1_xiL_1": 0.64534,
            "vector_m_5_ctau_6_xiO_1_xiL_1": 0.64331,
            "vector_m_5_ctau_75_xiO_1_xiL_1": 0.64391,
            "vector_m_10_ctau_350_xiO_1_xiL_1": 0.52376,
            "vector_m_10_ctau_35_xiO_1_xiL_1": 0.52396,
            "vector_m_10_ctau_4_xiO_1_xiL_1": 0.52732,
            "vector_m_10_ctau_60_xiO_1_xiL_1": 0.52586,

        }
        eff = efficiencies.get(self.process_name, 1.)
        df = df.Define("filter_efficiency", "1./%s" % eff)
        return df, ["filter_efficiency"]


def DQCDFilterEfficiencyRDF(**kwargs):
    """
    Module to extract the pythia efficiencies
    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: DQCDFilterEfficiencyRDF
            path: modules.DQCD_SF
            parameters:
                process_name: self.dataset.process.name
    """
    return lambda: DQCDFilterEfficiencyRDFProducer(**kwargs)


class DQCDBDTSFRDFProducer():
    def __init__(self, *args, **kwargs):
        self.process_name = kwargs.pop("process_name", "")

    def run(self, df):
        sfs = {
            "scenarioA": 0.983,
            "scenarioB1": 0.690,
            "vector": 0.966, 
        }
        sf = sfs.get(self.process_name.split("_")[0], 1.)
        print("BDT_SF", self.process_name, sf)
        df = df.Define("BDT_SF", str(sf))
        return df, ["BDT_SF"]


def DQCDBDTSFRDF(**kwargs):
    """
    Module to extract the pythia efficiencies
    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: DQCDBDTSFRDF
            path: modules.DQCD_SF
            parameters:
                process_name: self.dataset.process.name
    """
    return lambda: DQCDBDTSFRDFProducer(**kwargs)
