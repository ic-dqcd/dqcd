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
    """filter_efficiency = 1 / (generator filter efficiency of this process).

    The weight defaults to 1 in every case; a per-year table may override it. The tables
    are year-specific because the productions differ: 2018 applied a generator filter,
    2024 did not (which is why modules/scenario_filter_effs_2024.py is all 1.0).
    """

    # year -> (scenario table, vector-portal table), as module paths
    TABLES = {
        2018: ("modules.scenario_filter_effs", "modules.vp_filter_effs"),
        2024: ("modules.scenario_filter_effs_2024", "modules.vp_filter_effs_2024"),
    }

    def __init__(self, *args, **kwargs):
        self.process_name = kwargs.pop("process_name", "")
        self.year = int(kwargs.pop("year", 2018))
        self.is_signal = bool(kwargs.pop("is_signal", False))

    def run(self, df):
        import importlib

        eff = 1.0

        # per-year tables; an unprepared year is an error, not a silent default
        if self.year not in self.TABLES:
            raise ValueError(
                "\n"
                "=================================================================\n"
                " DQCDFilterEfficiencyRDF: no filter-efficiency tables for year "
                f"{self.year}\n"
                "=================================================================\n"
                f"  process            : {self.process_name}\n"
                f"  is signal          : {self.is_signal}\n"
                f"  years prepared     : {sorted(self.TABLES)}\n"
                "\n"
                "  To add a year, create the two tables and register them in\n"
                "  DQCDFilterEfficiencyRDFProducer.TABLES:\n"
                f"      modules/scenario_filter_effs_{self.year}.py   (d = {{...}})\n"
                f"      modules/vp_filter_effs_{self.year}.py         (d = {{...}})\n"
                "\n"
                "  If that production applied NO generator filter, fill the scenario\n"
                "  table with 1.0 for every point (see scenario_filter_effs_2024.py)\n"
                "  rather than leaving the year unregistered -- the weight is then 1\n"
                "  by construction and provably so, not by accident.\n"
                "=================================================================")

        scenario_mod, vp_mod = self.TABLES[self.year]
        efficiencies = dict(importlib.import_module(vp_mod).d)
        efficiencies.update(importlib.import_module(scenario_mod).d)

        if self.process_name in efficiencies:
            eff = efficiencies[self.process_name]
        elif self.is_signal:
            # A signal process with no table entry falls back to 1, i.e. is treated as
            # UNFILTERED. Whether that is right depends on the production, so the alert
            # fires for every year rather than only the one we happen to have checked:
            #
            #   * production applied a filter (2018)  -> the fallback is WRONG. The number
            #     was never measured, not measured-as-1. Mis-normalises by up to a factor 3
            #     for the points where the efficiency IS known. 52 of the 504 points in
            #     config/datasets_scenario.py land here.
            #   * production applied no filter (2024) -> the fallback is numerically right,
            #     but the point is still absent from the table, so the table does not
            #     document the grid it claims to cover. Worth knowing, and cheap to fix by
            #     adding the point explicitly as 1.0.
            #
            # Either way the reader should be told which case they are in, so the message
            # states the situation and leaves the judgement to them.
            print(
                "\n"
                "*****************************************************************\n"
                "*** WARNING: no filter efficiency for a SIGNAL process        ***\n"
                "*****************************************************************\n"
                f"  process   : {self.process_name}\n"
                f"  year      : {self.year}\n"
                f"  tables    : {scenario_mod}\n"
                f"              {vp_mod}\n"
                f"              ({len(efficiencies)} keys, none matching)\n"
                "\n"
                "  Falling back to filter_efficiency = 1, i.e. treating this sample as\n"
                "  UNFILTERED.\n"
                "\n"
                "  If this production DID apply a generator filter, that fallback is\n"
                "  WRONG -- the efficiency was never measured, not measured as 1.\n"
                "  If it did NOT (as for 2024), the value is right but the point is\n"
                "  still missing from the table.\n"
                "\n"
                "  Fix either way: add the point to\n"
                f"      {scenario_mod.replace('.', '/')}.py\n"
                f'      "{self.process_name}": <efficiency, or 1.0 if unfiltered>,\n'
                "*****************************************************************\n",
                flush=True)

        df = df.Define("filter_efficiency", "1./%s" % eff)
        return df, ["filter_efficiency"]

        # 2018: one source of truth. The hardcoded dict that used to sit here was
        # merged UNDER these imports, so every key it shared with scenario_filter_effs
        # was already dead; its 150 unique keys now live at the bottom of that file.
        efficiencies = {}

        # vector portal grid in ctau and mass
        from modules.vp_filter_effs import d as effs_vp
        efficiencies.update(effs_vp)
        
        from modules.scenario_filter_effs import d as effs_sc
        efficiencies.update(effs_sc)

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


#TODO adapt for 2024
class DQCDBDTSFRDFProducer():
    TABLES = {
        2018: {"scenarioA": 1.0, "scenarioB1": 1.0, "vector": 1.0},	# Reseted to 1 by kai in a late commit
        2024: {"scenarioA": 1.0, "scenarioB1": 1.0},			# TODO for 2024
    }

    def __init__(self, *args, **kwargs):
        self.process_name = kwargs.pop("process_name", "")
        self.year = int(kwargs.pop("year", 2018))
        self.is_signal = bool(kwargs.pop("is_signal", False))

    def run(self, df):
        sf = 1.0                                  # default for every case
        if self.year not in self.TABLES:
            raise ValueError(
                "\n\n  DQCDBDTSFRDFProducer has no BDT scale factors for year "
                f"{self.year}.\n"
                f"  Prepared years: {sorted(self.TABLES)}\n"
                f"  process_name  : {self.process_name!r}\n"
                "  To add a year: measure the SF (J/psi yield ratio, data vs QCD MC,\n"
                "  before and after the BDT selection) and add a {scenario: value} entry\n"
                "  to DQCDBDTSFRDFProducer.TABLES, plus the matching [bdt] uncertainty in\n"
                f"  config/systematics/systematics_{self.year}.cfg.\n")

        table = self.TABLES[self.year]
        key = self.process_name.split("_")[0]
        if key in table:
            sf = table[key]
        elif self.is_signal:
            print("\n  *** WARNING: no BDT scale factor for SIGNAL process "
                  f"{self.process_name!r} (scenario key {key!r}) in year {self.year}.\n"
                  f"      Known scenarios: {sorted(table)}\n"
                  "      Falling back to BDT_SF = 1, which is NOT a measurement.\n")

        print("BDT_SF", self.year, self.process_name, sf)
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
