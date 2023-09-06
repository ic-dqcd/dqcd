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
        single_sel = """cat_index == 0 &&
                muonSV_mu1eta.at(min_chi2_index) != 0 && muonSV_mu2eta.at(min_chi2_index) != 0"""
        categories = [
            Category("base", "base category", selection="event >= 0"),
            # Category("dum", "dummy category", selection="event == 220524669"),
            Category("dum", "dummy category", selection="event == 3"),

            # analysis categories
            # multi-vertex
            Category("multiv", "Multivertices", selection="cat_index != 0"),
            Category("multiv_cat1", "Multivertices, cat. 1",
                selection="""cat_index == 0 && muonSV_dxy.at(min_chi2_index) < 1 &&
                    muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("multiv_cat2", "Multivertices, cat. 2",
                selection="""cat_index == 0 && muonSV_dxy.at(min_chi2_index) < 1 &&
                    muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("multiv_cat3", "Multivertices, cat. 3",
                selection="""cat_index == 0 && muonSV_dxy.at(min_chi2_index) > 1 &&
                    muonSV_dxy.at(min_chi2_index) < 10 && muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("multiv_cat4", "Multivertices, cat. 4",
                selection="""cat_index == 0 && muonSV_dxy.at(min_chi2_index) > 1 &&
                    muonSV_dxy.at(min_chi2_index) < 10 && muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("multiv_cat5", "Multivertices, cat. 5",
                selection="""cat_index == 0 && muonSV_dxy.at(min_chi2_index) > 10 &&
                    muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("multiv_cat6", "Multivertices, cat. 6",
                selection="""cat_index == 0 && muonSV_dxy.at(min_chi2_index) > 10 &&
                    muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("multiv_new1", "Multivertices, new cat. 1",
                selection="cat_index == 0 && muonSV_dxy.at(min_chi2_index) < 1"),
            Category("multiv_new2", "Multivertices, new cat. 2",
                selection="cat_index == 0 && muonSV_dxy.at(min_chi2_index) > 1"),

            # single-vertex
            Category("singlev", "Single vertex", selection=single_sel),
            Category("singlev_cat1", "Single vertex, cat. 1",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) < 1 &&
                    muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("singlev_cat2", "Single vertex, cat. 2",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) < 1 &&
                    muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("singlev_cat3", "Single vertex, cat. 3",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) > 1 &&
                    muonSV_dxy.at(min_chi2_index) < 10 && muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("singlev_cat4", "Single vertex, cat. 4",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) > 1 &&
                    muonSV_dxy.at(min_chi2_index) < 10 && muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("singlev_cat5", "Single vertex, cat. 5",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) > 10 &&
                    muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("singlev_cat6", "Single vertex, cat. 6",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) > 10 &&
                    muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("singlev_new1", "Single vertex, new cat. 1",
                selection=single_sel + " && muonSV_dxy.at(min_chi2_index) < 1"),
            Category("singlev_new2", "Single vertex, new cat. 2",
                selection=single_sel + " && muonSV_dxy.at(min_chi2_index) > 1"),

        ]
        return ObjectCollection(categories)

    def add_processes(self):
        processes = [
            Process("Background", Label("Background"), color=(255, 153, 0)),
            Process("QCD", Label("QCD"), color=(255, 153, 0), parent_process="background"),

            Process("signal", Label("Signal"), color=(0, 0, 0), isSignal=True),

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
            "m_2_ctau_10_xiO_1_xiL_1": ("HiddenValley_vector_m_2_ctau_10_xiO_1_xiL_1"
                "_privateMC_11X_NANOAODSIM_v1p0_generationSync"),
        }

        datasets = [
            Dataset("qcd_80to120",
                folder=[
                    sample_path + samples["qcd_80to120"],
                    sample_path + samples["qcd_80to120_ext1"],
                ],
                skipFiles=["{}/output_{}.root".format(
                        sample_path + samples["qcd_80to120"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(
                        sample_path + samples["qcd_80to120_ext1"], i)
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
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_800to1000"], i)
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

            ## signal
            Dataset("m_2_ctau_10_xiO_1_xiL_1",
                folder=sample_path + samples["m_2_ctau_10_xiO_1_xiL_1"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["m_2_ctau_10_xiO_1_xiL_1"], i)
                    for i in range(1, 6)],
                process=self.processes.get("signal"),
                xs=1.,# FIXME
                friend_datasets="m_2_ctau_10_xiO_1_xiL_1_friend"),
            Dataset("m_2_ctau_10_xiO_1_xiL_1_friend",
                folder=bdt_path + samples["m_2_ctau_10_xiO_1_xiL_1"],
                process=self.processes.get("dum"),
                xs=1., # FIXME
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

            Feature("muonSV_mass_min_chi2", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2}"),
                units="GeV"),
            Feature("nmuonSV_3sigma", "nmuonSV_3sigma", binning=(11, -0.5, 10.5),
                x_title=Label("BDT score")),

        ]
        return ObjectCollection(features)

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        # weights.total_events_weights = ["genWeight", "puWeight"]
        weights.total_events_weights = ["genWeight"]

        # weights.base = ["genWeight", "puWeight"]  # others needed

        for category in self.categories:
            weights[category.name] = ["1"]

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
