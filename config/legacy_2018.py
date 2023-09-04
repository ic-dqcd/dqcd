from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from cmt.config.base_config import Config as cmt_config


class Config(cmt_config):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    def add_categories(self, **kwargs):
        categories = [
            Category("base", "base category", selection="event >= 0"),
            Category("base_selection", "base category",
                nt_selection="(Sum$(Tau_pt->fElements > 17) > 0"
                    " && ((Sum$(Muon_pt->fElements > 17) > 0"
                    " || Sum$(Electron_pt->fElements > 17) > 0)"
                    " || Sum$(Tau_pt->fElements > 17) > 1)"
                    " && Sum$(Jet_pt->fElements > 17) > 1)",
                selection="Tau_pt[Tau_pt > 10].size() > 0 "
                    "&& ((Muon_pt[Muon_pt > 17].size() > 0"
                    "|| Electron_pt[Electron_pt > 17].size() > 0)"
                    "|| Tau_pt[Tau_pt > 10].size() > 1)"
                    "&& Jet_pt[Jet_pt > 17].size() > 0"),
            # Category("dum", "dummy category", selection="event == 220524669"),
            Category("dum", "dummy category", selection="event == 74472670"),
        ]
        return ObjectCollection(categories)

    def add_processes(self):
        processes = [
            Process("Background", Label("Background"), color=(255, 153, 0)),
            Process("QCD", Label("QCD"), color=(255, 153, 0), parent_process="background"),

            Process("data", Label("Data"), color=(0, 0, 0), isData=True),

            Process("dum", Label("dum"), color=(0, 0, 0)),
        ]

        process_group_names = {
            "default": [
                # "ggf_sm",
                # "data_tau",
                # "dy_high",
                # "tt_dl",
                "data",
                "background",
            ],
        }

        process_training_names = {}
            # "default": []
        # }

        return ObjectCollection(processes), process_group_names, process_training_names

    def add_datasets(self):
        sample_path = "/vols/cms/mc3909/bparkProductionAll_V1p0/"
        bdt_path = ("/vols/cms/mmieskol/icenet/output/dqcd/deploy/modeltag__vector_all/"
            "vols/cms/mc3909/bparkProductionAll_V1p0/")

        samples = {
            "qcd_80to120": ("QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_80to120_ext1": ("QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_800to1000": ("QCD_Pt-800to1000_MuEnrichedPt5_TuneCP5_13TeV_pythia8_"
                "RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext3-v2_"
                "MINIAODSIM_v1p0_generationSync"),
        }

        datasets = [
            Dataset("qcd_80to120",
                folder=[
                    sample_path + samples["qcd_80to120"],
                    sample_path + samples["qcd_80to120_ext1"],
                ],
                skipFiles=["{}/output_{}.root".format(sample_path + samples["qcd_80to120"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(sample_path + samples["qcd_80to120_ext1"], i)
                        for i in range(1, 11)],
                process=self.processes.get("QCD"),
                xs=0.03105, #FIXME
                friend_datasets="qcd_80to120_friend"),
            Dataset("qcd_80to120_friend",
                folder=[
                    bdt_path + samples["qcd_80to120"],
                    bdt_path + samples["qcd_80to120_ext1"],
                ],
                process=self.processes.get("dum"),
                xs=0.03105, # FIXME
                tags=["friend"]),

            Dataset("qcd_800to1000",
                folder=[
                    sample_path + samples["qcd_800to1000"],
                ],
                skipFiles=["{}/output_{}.root".format(sample_path + samples["qcd_800to1000"], i)
                    for i in range(1, 11)],
                process=self.processes.get("QCD"),
                xs=0.03105, # FIXME
                friend_datasets="qcd_800to1000_friend"),
            Dataset("qcd_800to1000_friend",
                folder=[
                    bdt_path + samples["qcd_800to1000"],
                ],
                process=self.processes.get("dum"),
                xs=0.03105, # FIXME
                tags=["friend"]),

            ## data
            Dataset("data_2018b",
                folder=sample_path + "ParkingBPH1_Run2018B-05May2019-v2_MINIAOD_v1p0_generationSync/",
                process=self.processes.get("data"),
                friend_datasets="data_2018b_friend"),
            Dataset("data_2018b_friend",
                folder=bdt_path + "ParkingBPH1_Run2018B-05May2019-v2_MINIAOD_v1p0_generationSync/",
                process=self.processes.get("dum"),),
        ]
        return ObjectCollection(datasets)

    def add_features(self):
        features = [
            Feature("njet", "nJet", binning=(10, -0.5, 9.5),
                x_title=Label("nJet")),
            Feature("jet_pt", "Jet_pt", binning=(10, 50, 150),
                x_title=Label("jet p_{T}"),
                units="GeV"),

            # BDT features
            Feature("bdt", "xgb0__m_2p0_ctau_10p0_xiO_1p0_xiL_1p0", binning=(20, 0, 1),
                x_title=Label("BDT score")),

        ]
        return ObjectCollection(features)

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        # weights.total_events_weights = ["genWeight", "puWeight"]
        weights.total_events_weights = ["genWeight"]

        # weights.base = ["genWeight", "puWeight"]  # others needed
        weights.base = ["1"]  # others needed
        weights.base_selection = weights.base

        return weights

    def add_systematics(self):
        systematics = [
            Systematic("jet_smearing", "_nom"),
            Systematic("met_smearing", ("MET", "MET_smeared")),
            Systematic("prefiring", "_Nom"),
            Systematic("prefiring_syst", "", up="_Up", down="_Dn"),
            Systematic("pu", "", up="Up", down="Down"),
            Systematic("tes", "_corr",
                affected_categories=self.categories.names(),
                module_syst_type="tau_syst"),
            Systematic("empty", "", up="", down="")
        ]
        return ObjectCollection(systematics)

    # other methods

config = Config("base", year=2018, ecm=13, lumi_pb=59741)
