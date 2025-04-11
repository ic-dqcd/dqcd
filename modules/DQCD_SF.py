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

            # scenarioB1
            # "scenarioB1_mpi_1_mA_0p33_ctau_0p1": 0.83669,
            "scenarioB1_mpi_1_mA_0p33_ctau_0p25": 0.83442,
            "scenarioB1_mpi_1_mA_0p33_ctau_0p3": 0.83493,
            "scenarioB1_mpi_1_mA_0p33_ctau_0p6": 0.83651,
            # "scenarioB1_mpi_1_mA_0p33_ctau_10": 0.83921,
            # "scenarioB1_mpi_1_mA_0p33_ctau_100": 0.83591,
            # "scenarioB1_mpi_1_mA_0p33_ctau_1p0": 0.83658,
            "scenarioB1_mpi_1_mA_0p33_ctau_25p0": 0.83616,
            "scenarioB1_mpi_1_mA_0p33_ctau_2p5": 0.83607,
            "scenarioB1_mpi_1_mA_0p33_ctau_30": 0.83682,
            "scenarioB1_mpi_1_mA_0p33_ctau_3p0": 0.83878,
            "scenarioB1_mpi_1_mA_0p33_ctau_60p0": 0.83713,
            "scenarioB1_mpi_1_mA_0p33_ctau_6p0": 0.8363,
            "scenarioB1_mpi_1_mA_0p40_ctau_0p25": 0.83166,
            "scenarioB1_mpi_1_mA_0p40_ctau_0p3": 0.83152,
            "scenarioB1_mpi_1_mA_0p40_ctau_0p6": 0.83169,
            "scenarioB1_mpi_1_mA_0p40_ctau_25p0": 0.83238,
            "scenarioB1_mpi_1_mA_0p40_ctau_2p5": 0.83087,
            "scenarioB1_mpi_1_mA_0p40_ctau_30": 0.83261,
            "scenarioB1_mpi_1_mA_0p40_ctau_3p0": 0.83202,
            "scenarioB1_mpi_1_mA_0p40_ctau_60p0": 0.83052,
            "scenarioB1_mpi_1_mA_0p40_ctau_6p0": 0.83056,
            "scenarioB1_mpi_2_mA_0p33_ctau_0p25": 0.82603,
            "scenarioB1_mpi_2_mA_0p33_ctau_0p3": 0.82393,
            "scenarioB1_mpi_2_mA_0p33_ctau_0p6": 0.82468,
            "scenarioB1_mpi_2_mA_0p33_ctau_25p0": 0.826,
            "scenarioB1_mpi_2_mA_0p33_ctau_2p5": 0.82327,
            "scenarioB1_mpi_2_mA_0p33_ctau_30": 0.82474,
            "scenarioB1_mpi_2_mA_0p33_ctau_3p0": 0.82698,
            "scenarioB1_mpi_2_mA_0p33_ctau_60p0": 0.82625,
            "scenarioB1_mpi_2_mA_0p33_ctau_6p0": 0.82707,
            "scenarioB1_mpi_2_mA_0p40_ctau_0p25": 0.81633,
            "scenarioB1_mpi_2_mA_0p40_ctau_0p3": 0.81612,
            "scenarioB1_mpi_2_mA_0p40_ctau_0p6": 0.81608,
            "scenarioB1_mpi_2_mA_0p40_ctau_25p0": 0.81726,
            "scenarioB1_mpi_2_mA_0p40_ctau_2p5": 0.81767,
            "scenarioB1_mpi_2_mA_0p40_ctau_30": 0.81746,
            "scenarioB1_mpi_2_mA_0p40_ctau_3p0": 0.81558,
            "scenarioB1_mpi_2_mA_0p40_ctau_60p0": 0.81661,
            "scenarioB1_mpi_2_mA_0p40_ctau_6p0": 0.81656,
            "scenarioB1_mpi_2_mA_0p67_ctau_0p25": 0.52938,
            "scenarioB1_mpi_2_mA_0p67_ctau_0p3": 0.53141,
            "scenarioB1_mpi_2_mA_0p67_ctau_0p6": 0.52875,
            "scenarioB1_mpi_2_mA_0p67_ctau_25p0": 0.52744,
            "scenarioB1_mpi_2_mA_0p67_ctau_2p5": 0.529,
            "scenarioB1_mpi_2_mA_0p67_ctau_30": 0.52757,
            "scenarioB1_mpi_2_mA_0p67_ctau_3p0": 0.52611,
            "scenarioB1_mpi_2_mA_0p67_ctau_60p0": 0.52947,
            "scenarioB1_mpi_2_mA_0p67_ctau_6p0": 0.528232,
            "scenarioB1_mpi_2_mA_0p90_ctau_0p25": 0.70408,
            "scenarioB1_mpi_2_mA_0p90_ctau_0p3": 0.70535,
            "scenarioB1_mpi_2_mA_0p90_ctau_0p6": 0.7027,
            "scenarioB1_mpi_2_mA_0p90_ctau_25p0": 0.70386,
            "scenarioB1_mpi_2_mA_0p90_ctau_2p5": 0.70333,
            "scenarioB1_mpi_2_mA_0p90_ctau_30": 0.70405,
            "scenarioB1_mpi_2_mA_0p90_ctau_3p0": 0.7029,
            "scenarioB1_mpi_2_mA_0p90_ctau_60p0": 0.70183,
            "scenarioB1_mpi_2_mA_0p90_ctau_6p0": 0.70469,
            "scenarioB1_mpi_4_mA_0p67_ctau_0p25": 0.4299,
            "scenarioB1_mpi_4_mA_0p67_ctau_0p3": 0.4313,
            "scenarioB1_mpi_4_mA_0p67_ctau_0p6": 0.43064,
            "scenarioB1_mpi_4_mA_0p67_ctau_25p0": 0.43209,
            "scenarioB1_mpi_4_mA_0p67_ctau_2p5": 0.42906,
            "scenarioB1_mpi_4_mA_0p67_ctau_30": 0.43281,
            "scenarioB1_mpi_4_mA_0p67_ctau_3p0": 0.43039,
            "scenarioB1_mpi_4_mA_0p67_ctau_60p0": 0.43074,
            "scenarioB1_mpi_4_mA_0p67_ctau_6p0": 0.43251,
            "scenarioB1_mpi_4_mA_0p80_ctau_0p25": 0.38782,
            "scenarioB1_mpi_4_mA_0p80_ctau_0p3": 0.38626,
            "scenarioB1_mpi_4_mA_0p80_ctau_0p6": 0.38611,
            "scenarioB1_mpi_4_mA_0p80_ctau_25p0": 0.38467,
            "scenarioB1_mpi_4_mA_0p80_ctau_2p5": 0.38831,
            "scenarioB1_mpi_4_mA_0p80_ctau_30": 0.38717,
            "scenarioB1_mpi_4_mA_0p80_ctau_3p0": 0.38485,
            "scenarioB1_mpi_4_mA_0p80_ctau_60p0": 0.38712,
            "scenarioB1_mpi_4_mA_0p80_ctau_6p0": 0.38532,
            "scenarioB1_mpi_4_mA_1p33_ctau_0p25": 0.66305,
            "scenarioB1_mpi_4_mA_1p33_ctau_0p3": 0.66519,
            "scenarioB1_mpi_4_mA_1p33_ctau_0p6": 0.66562,
            "scenarioB1_mpi_4_mA_1p33_ctau_25p0": 0.6668,
            "scenarioB1_mpi_4_mA_1p33_ctau_2p5": 0.66347,
            "scenarioB1_mpi_4_mA_1p33_ctau_30": 0.66473,
            "scenarioB1_mpi_4_mA_1p33_ctau_3p0": 0.66571,
            "scenarioB1_mpi_4_mA_1p33_ctau_60p0": 0.66479,
            "scenarioB1_mpi_4_mA_1p33_ctau_6p0": 0.66478,
            "scenarioB1_mpi_4_mA_1p90_ctau_0p25": 0.60292,
            "scenarioB1_mpi_4_mA_1p90_ctau_0p3": 0.60298,
            "scenarioB1_mpi_4_mA_1p90_ctau_0p6": 0.60338,
            "scenarioB1_mpi_4_mA_1p90_ctau_25p0": 0.60357,
            "scenarioB1_mpi_4_mA_1p90_ctau_2p5": 0.60251,
            "scenarioB1_mpi_4_mA_1p90_ctau_30": 0.59828,
            "scenarioB1_mpi_4_mA_1p90_ctau_3p0": 0.60287,
            "scenarioB1_mpi_4_mA_1p90_ctau_60p0": 0.60582,
            "scenarioB1_mpi_4_mA_1p90_ctau_6p0": 0.60228,
            "scenarioB1_mpi_5_mA_0p83_ctau_0p25": 0.38565,
            "scenarioB1_mpi_5_mA_0p83_ctau_0p3": 0.38656,
            "scenarioB1_mpi_5_mA_0p83_ctau_0p6": 0.38474,
            "scenarioB1_mpi_5_mA_0p83_ctau_25p0": 0.38483,
            "scenarioB1_mpi_5_mA_0p83_ctau_2p5": 0.38631,
            "scenarioB1_mpi_5_mA_0p83_ctau_30": 0.38714,
            "scenarioB1_mpi_5_mA_0p83_ctau_3p0": 0.3879,
            "scenarioB1_mpi_5_mA_0p83_ctau_60p0": 0.38763,
            "scenarioB1_mpi_5_mA_0p83_ctau_6p0": 0.38486,
            "scenarioB1_mpi_5_mA_1p00_ctau_0p25": 0.59135,
            "scenarioB1_mpi_5_mA_1p00_ctau_0p3": 0.59116,
            "scenarioB1_mpi_5_mA_1p00_ctau_0p6": 0.58963,
            "scenarioB1_mpi_5_mA_1p00_ctau_25p0": 0.59037,
            "scenarioB1_mpi_5_mA_1p00_ctau_2p5": 0.58845,
            "scenarioB1_mpi_5_mA_1p00_ctau_30": 0.5877,
            "scenarioB1_mpi_5_mA_1p00_ctau_3p0": 0.59207,
            "scenarioB1_mpi_5_mA_1p00_ctau_60p0": 0.58908,
            "scenarioB1_mpi_5_mA_1p00_ctau_6p0": 0.58969,
            "scenarioB1_mpi_5_mA_1p67_ctau_0p25": 0.54058,
            "scenarioB1_mpi_5_mA_1p67_ctau_0p3": 0.53857,
            "scenarioB1_mpi_5_mA_1p67_ctau_0p6": 0.53983,
            "scenarioB1_mpi_5_mA_1p67_ctau_25p0": 0.54128,
            "scenarioB1_mpi_5_mA_1p67_ctau_2p5": 0.53729,
            "scenarioB1_mpi_5_mA_1p67_ctau_30": 0.53708,
            "scenarioB1_mpi_5_mA_1p67_ctau_3p0": 0.54198,
            "scenarioB1_mpi_5_mA_1p67_ctau_60p0": 0.53985,
            "scenarioB1_mpi_5_mA_1p67_ctau_6p0": 0.53989,
            "scenarioB1_mpi_5_mA_2p40_ctau_0p25": 0.54944,
            "scenarioB1_mpi_5_mA_2p40_ctau_0p3": 0.54776,
            "scenarioB1_mpi_5_mA_2p40_ctau_0p6": 0.54962,
            "scenarioB1_mpi_5_mA_2p40_ctau_25p0": 0.5504,
            "scenarioB1_mpi_5_mA_2p40_ctau_2p5": 0.54947,
            "scenarioB1_mpi_5_mA_2p40_ctau_30": 0.55057,
            "scenarioB1_mpi_5_mA_2p40_ctau_3p0": 0.55203,
            "scenarioB1_mpi_5_mA_2p40_ctau_60p0": 0.54996,
            "scenarioB1_mpi_5_mA_2p40_ctau_6p0": 0.54968,

            # scenarioA
            # "scenarioA_mpi_1_mA_0p33_ctau_0p1": 0.838152,
            "scenarioA_mpi_1_mA_0p33_ctau_0p25": 0.83951,
            "scenarioA_mpi_1_mA_0p33_ctau_6p0": 0.83554,
            "scenarioA_mpi_2_mA_0p67_ctau_0p25": 0.527516,
            "scenarioA_mpi_2_mA_0p67_ctau_0p3": 0.532191,
            "scenarioA_mpi_2_mA_0p67_ctau_0p6": 0.528227,
            "scenarioA_mpi_2_mA_0p67_ctau_25p0": 0.527222,
            "scenarioA_mpi_2_mA_0p67_ctau_2p5": 0.530802,
            "scenarioA_mpi_2_mA_0p67_ctau_30": 0.529195,
            "scenarioA_mpi_2_mA_0p67_ctau_3p0": 0.52866,
            "scenarioA_mpi_2_mA_0p67_ctau_60p0": 0.529542,
            "scenarioA_mpi_2_mA_0p67_ctau_6p0": 0.52486,
            "scenarioA_mpi_1_mA_0p33_ctau_0p3": 0.838296,
            "scenarioA_mpi_4_mA_0p40_ctau_0p25": 0.738966,
            "scenarioA_mpi_4_mA_0p40_ctau_0p3": 0.73735,
            "scenarioA_mpi_4_mA_0p40_ctau_0p6": 0.741609,
            "scenarioA_mpi_4_mA_0p40_ctau_25p0": 0.740237,
            "scenarioA_mpi_4_mA_0p40_ctau_2p5": 0.738247,
            "scenarioA_mpi_4_mA_0p40_ctau_30": 0.740862,
            "scenarioA_mpi_4_mA_0p40_ctau_3p0": 0.738898,
            "scenarioA_mpi_4_mA_0p40_ctau_60p0": 0.737063,
            "scenarioA_mpi_4_mA_0p40_ctau_6p0": 0.740011,
            # "scenarioA_mpi_4_mA_1p33_ctau_0p1": 0.666469,
            "scenarioA_mpi_1_mA_0p33_ctau_0p6": 0.836235,
            "scenarioA_mpi_4_mA_1p33_ctau_0p25": 0.66743,
            "scenarioA_mpi_4_mA_1p33_ctau_0p3": 0.665051,
            "scenarioA_mpi_4_mA_1p33_ctau_0p6": 0.662277,
            # "scenarioA_mpi_4_mA_1p33_ctau_10": 0.663329,
            "scenarioA_mpi_4_mA_1p33_ctau_25p0": 0.662415,
            "scenarioA_mpi_4_mA_1p33_ctau_2p5": 0.666575,
            "scenarioA_mpi_4_mA_1p33_ctau_30": 0.66263,
            "scenarioA_mpi_4_mA_1p33_ctau_3p0": 0.664612,
            "scenarioA_mpi_4_mA_1p33_ctau_60p0": 0.663396,
            "scenarioA_mpi_4_mA_1p33_ctau_6p0": 0.663663,
            # "scenarioA_mpi_1_mA_0p33_ctau_100": 0.838153,
            "scenarioA_mpi_1_mA_0p33_ctau_25p0": 0.837443,
            "scenarioA_mpi_1_mA_0p33_ctau_2p5": 0.836309,
            "scenarioA_mpi_1_mA_0p33_ctau_30": 0.835202,
            "scenarioA_mpi_1_mA_0p33_ctau_3p0": 0.838677,
            "scenarioA_mpi_1_mA_0p33_ctau_60p0": 0.836974,
        }

        # vector portal grid in ctau and mass
        from vp_filter_effs import d as effs_vp
        efficiencies.update(effs_vp)

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
