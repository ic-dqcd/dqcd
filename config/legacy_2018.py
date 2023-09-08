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
            Process("background", Label("Background"), color=(255, 153, 0)),
            Process("qcd", Label("QCD"), color=(255, 153, 0), parent_process="background"),

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
            "qcd_1000toInf": ("QCD_Pt-1000toInf_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_120to170": ("QCD_Pt-120to170_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_120to170_ext": ("QCD_Pt-120to170_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_15to20": ("QCD_Pt-15to20_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_170to300": ("QCD_Pt-170to300_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_20to30": ("QCD_Pt-20to30_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v4"
                "_MINIAODSIM_v1p0_generationSync"),
            # "qcd_20toInf": ("QCD_Pt-20toInf_MuEnrichedPt15_TuneCP5_13TeV_pythia8"
                # "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                # "_MINIAODSIM_v1p0_generationSync"),
            "qcd_300to470": ("QCD_Pt-300to470_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_300to470_ext": ("QCD_Pt-300to470_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext3-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_30to50": ("QCD_Pt-30to50_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_470to600": ("QCD_Pt-470to600_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_470to600_ext": ("QCD_Pt-470to600_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_50to80": ("QCD_Pt-50to80_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_600to800": ("QCD_Pt-600to800_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_800to1000": ("QCD_Pt-800to1000_MuEnrichedPt5_TuneCP5_13TeV_pythia8_"
                "RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext3-v2_"
                "MINIAODSIM_v1p0_generationSync"),
            "qcd_80to120": ("QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_80to120_ext": ("QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2"
                "_MINIAODSIM_v1p0_generationSync"),

            # signal
            "m_2_ctau_10_xiO_1_xiL_1": ("HiddenValley_vector_m_2_ctau_10_xiO_1_xiL_1"
                "_privateMC_11X_NANOAODSIM_v1p0_generationSync"),
        }

        datasets = [
            Dataset("qcd_1000toInf",
                folder=sample_path + samples["qcd_1000toInf"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_1000toInf"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=0.001078,
                friend_datasets="qcd_1000toInf_friend"),
            Dataset("qcd_1000toInf_friend",
                folder=bdt_path + samples["qcd_1000toInf"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_120to170",
                folder=[
                    sample_path + samples["qcd_120to170"],
                    sample_path + samples["qcd_120to170_ext"],
                ],
                skipFiles=["{}/output_{}.root".format(
                        sample_path + samples["qcd_120to170"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(
                        sample_path + samples["qcd_120to170_ext"], i)
                        for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=21.23,
                friend_datasets="qcd_120to170_friend"),
            Dataset("qcd_120to170_friend",
                folder=[
                    bdt_path + samples["qcd_120to170"],
                    bdt_path + samples["qcd_120to170_ext"],
                ],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_15to20",
                folder=sample_path + samples["qcd_15to20"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_15to20"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=2799,
                friend_datasets="qcd_15to20_friend"),
            Dataset("qcd_15to20_friend",
                folder=bdt_path + samples["qcd_15to20"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_170to300",
                folder=sample_path + samples["qcd_170to300"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_170to300"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=7.055,
                friend_datasets="qcd_170to300_friend"),
            Dataset("qcd_170to300_friend",
                folder=bdt_path + samples["qcd_170to300"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_20to30",
                folder=sample_path + samples["qcd_20to30"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_20to30"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=2526,
                friend_datasets="qcd_20to30_friend"),
            Dataset("qcd_20to30_friend",
                folder=bdt_path + samples["qcd_20to30"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            # Dataset("qcd_20toInf",
                # folder=sample_path + samples["qcd_20toInf"],
                # # skipFiles=["{}/output_{}.root".format(
                    # # sample_path + samples["qcd_20toInf"], i)
                    # # for i in range(1, 11)],
                # process=self.processes.get("qcd"),
                # xs=0.03105, # FIXME
                # friend_datasets="qcd_20toInf_friend"),
            # Dataset("qcd_20toInf_friend",
                # folder=bdt_path + samples["qcd_20toInf"],
                # process=self.processes.get("dum"),
                # xs=0.03105, # FIXME
                # tags=["friend"]),

            Dataset("qcd_300to470",
                folder=[
                    sample_path + samples["qcd_300to470"],
                    sample_path + samples["qcd_300to470_ext"],
                ],
                skipFiles=["{}/output_{}.root".format(
                        sample_path + samples["qcd_300to470"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(
                        sample_path + samples["qcd_300to470_ext"], i)
                        for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=0.6193,
                friend_datasets="qcd_300to470_friend"),
            Dataset("qcd_300to470_friend",
                folder=[
                    bdt_path + samples["qcd_300to470"],
                    bdt_path + samples["qcd_300to470_ext"],
                ],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_30to50",
                folder=sample_path + samples["qcd_30to50"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_30to50"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=1362,
                friend_datasets="qcd_30to50_friend"),
            Dataset("qcd_30to50_friend",
                folder=bdt_path + samples["qcd_30to50"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_470to600",
                folder=[
                    sample_path + samples["qcd_470to600"],
                    sample_path + samples["qcd_470to600_ext"],
                ],
                skipFiles=["{}/output_{}.root".format(
                        sample_path + samples["qcd_470to600"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(
                        sample_path + samples["qcd_470to600_ext"], i)
                        for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=0.05924,
                friend_datasets="qcd_470to600_friend"),
            Dataset("qcd_470to600_friend",
                folder=[
                    bdt_path + samples["qcd_470to600"],
                    bdt_path + samples["qcd_470to600_ext"],
                ],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_50to80",
                folder=sample_path + samples["qcd_50to80"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_50to80"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=376.6,
                friend_datasets="qcd_50to80_friend"),
            Dataset("qcd_50to80_friend",
                folder=bdt_path + samples["qcd_50to80"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_600to800",
                folder=sample_path + samples["qcd_600to800"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_600to800"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=0.01821,
                friend_datasets="qcd_600to800_friend"),
            Dataset("qcd_600to800_friend",
                folder=bdt_path + samples["qcd_600to800"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_80to120",
                folder=[
                    sample_path + samples["qcd_80to120"],
                    sample_path + samples["qcd_80to120_ext"],
                ],
                skipFiles=["{}/output_{}.root".format(
                        sample_path + samples["qcd_80to120"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(
                        sample_path + samples["qcd_80to120_ext"], i)
                        for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=88.930,
                friend_datasets="qcd_80to120_friend"),
            Dataset("qcd_80to120_friend",
                folder=[
                    bdt_path + samples["qcd_80to120"],
                    bdt_path + samples["qcd_80to120_ext"],
                ],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_800to1000",
                folder=sample_path + samples["qcd_800to1000"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_800to1000"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=0.003275,
                friend_datasets="qcd_800to1000_friend"),
            Dataset("qcd_800to1000_friend",
                folder=bdt_path + samples["qcd_800to1000"],
                process=self.processes.get("dum"),
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
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("data_2018c",
                folder=sample_path + "ParkingBPH1_Run2018C-05May2019-v1_MINIAOD_v1p0_generationSync/",
                process=self.processes.get("data"),
                friend_datasets="data_2018b_friend"),
            Dataset("data_2018c_friend",
                folder=bdt_path + "ParkingBPH1_Run2018C-05May2019-v1_MINIAOD_v1p0_generationSync",
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("data_2018d",
                folder=sample_path + "ParkingBPH1_Run2018D-05May2019promptD-v1_MINIAOD_v1p0_generationSync",
                process=self.processes.get("data"),
                friend_datasets="data_2018b_friend"),
            Dataset("data_2018d_friend",
                folder=bdt_path + "ParkingBPH1_Run2018D-05May2019promptD-v1_MINIAOD_v1p0_generationSync",
                process=self.processes.get("dum"),
                tags=["friend"]),
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
        # weights.total_events_weights = ["genWeight"]
        weights.total_events_weights = ["1"]

        # weights.base = ["genWeight", "puWeight"]  # others needed

        for category in self.categories:
            weights[category.name] = ["1"]

        return weights

    def add_systematics(self):
        systematics = [
            # Systematic("jet_smearing", "_nom"),
            # Systematic("met_smearing", ("MET", "MET_smeared")),
            # Systematic("prefiring", "_Nom"),
            # Systematic("prefiring_syst", "", up="_Up", down="_Dn"),
            # Systematic("pu", "", up="Up", down="Down"),
            # Systematic("tes", "_corr",
                # affected_categories=self.categories.names(),
                # module_syst_type="tau_syst"),
            # Systematic("empty", "", up="", down="")
        ]
        return ObjectCollection(systematics)

    def add_default_module_files(self):
        defaults = {}
        defaults["PreprocessRDF"] = "modules"
        defaults["PreCounter"] = "weights"
        return defaults

    # other methods

# config = Config("base", year=2018, ecm=13, lumi_pb=59741)
config = Config("base", year=2018, ecm=13, lumi_pb=33600)
