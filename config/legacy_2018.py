from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from cmt.config.base_config import Config as cmt_config


class Config(cmt_config):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.regions = self.add_regions()

    def add_regions(self, **kwargs):
        regions = [
            Category("signal", "Signal region", selection="{{bdt}} > 0.85"),
            Category("background", "Background region", selection="{{bdt}} < 0.85"),
        ]
        return ObjectCollection(regions)

    def add_categories(self, **kwargs):
        single_sel = """cat_index == 0 &&
                muonSV_mu1eta.at(min_chi2_index) != 0 && muonSV_mu2eta.at(min_chi2_index) != 0"""
        categories = [
            Category("base", "base", selection="event >= 0"),
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
            Process("ww", Label("WW"), color=(131, 38, 10), parent_process="background"),

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
            "full": [
                # "ggf_sm",
                # "data_tau",
                # "dy_high",
                # "tt_dl",
                "data",
                "qcd",
                "ww",
                "signal"
            ],
            "sigbkg": [
                # "ggf_sm",
                # "data_tau",
                # "dy_high",
                # "tt_dl",
                "signal",
                "background",
                "data"
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

        xs = {
            "qcd_15to20": 2799,
            "qcd_20to30": 2526,
            "qcd_30to50": 1362,
            "qcd_50to80": 376.6,
            "qcd_80to120": 88.93,
            "qcd_120to170": 21.23,
            "qcd_170to300": 7.055,
            "qcd_300to470": 0.619,
            "qcd_470to600": 0.05924,
            "qcd_600to800": 0.01821,
            "qcd_800to1000": 0.003275,
            "qcd_1000toInf": 0.001078,
        }


        datasets = [
            Dataset("qcd_1000toInf",
                folder=sample_path + samples["qcd_1000toInf"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_1000toInf"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=xs["qcd_1000toInf"],
                friend_datasets="qcd_1000toInf_friend",
                merging={
                    "base": 10,
                },),
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
                xs=xs["qcd_120to170"],
                friend_datasets="qcd_120to170_friend",
                merging={
                    "base": 10,
                },),
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
                xs=xs["qcd_15to20"],
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
                xs=xs["qcd_170to300"],
                friend_datasets="qcd_170to300_friend",
                merging={
                    "base": 10,
                },),
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
                xs=xs["qcd_20to30"],
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
                xs=xs["qcd_300to470"],
                friend_datasets="qcd_300to470_friend",
                merging={
                    "base": 10,
                },),
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
                xs=xs["qcd_30to50"],
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
                xs=xs["qcd_470to600"],
                friend_datasets="qcd_470to600_friend",
                merging={
                    "base": 10,
                },),
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
                xs=xs["qcd_50to80"],
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
                xs=xs["qcd_600to800"],
                friend_datasets="qcd_600to800_friend",
                merging={
                    "base": 10,
                },),
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
                xs=xs["qcd_80to120"],
                friend_datasets="qcd_80to120_friend",
                merging={
                    "base": 10,
                },),
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
                xs=xs["qcd_800to1000"],
                friend_datasets="qcd_800to1000_friend",
                merging={
                    "base": 10,
                },),
            Dataset("qcd_800to1000_friend",
                folder=bdt_path + samples["qcd_800to1000"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            # Dataset("ww",
                # folder="/vols/cms/jleonhol/samples/ww/",
                # process=self.processes.get("ww"),
                # xs=12.178),

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
                friend_datasets="data_2018b_friend",
                merging={
                    "base": 20,
                },),
            Dataset("data_2018b_friend",
                folder=bdt_path + "ParkingBPH1_Run2018B-05May2019-v2_MINIAOD_v1p0_generationSync/",
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("data_2018c",
                folder=sample_path + "ParkingBPH1_Run2018C-05May2019-v1_MINIAOD_v1p0_generationSync/",
                process=self.processes.get("data"),
                friend_datasets="data_2018c_friend",
                merging={
                    "base": 20,
                },),
            Dataset("data_2018c_friend",
                folder=bdt_path + "ParkingBPH1_Run2018C-05May2019-v1_MINIAOD_v1p0_generationSync",
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("data_2018d",
                folder=sample_path + "ParkingBPH1_Run2018D-05May2019promptD-v1_MINIAOD_v1p0_generationSync",
                process=self.processes.get("data"),
                friend_datasets="data_2018d_friend",
                merging={
                    "base": 20,
                },),
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
            Feature("jet_pt", "Jet_pt", binning=(30, 0, 150),
                x_title=Label("jet p_{T}"),
                units="GeV"),
            Feature("jet_eta", "Jet_eta", binning=(50, -5, 5),
                x_title=Label("jet #eta"),),
            Feature("jet_phi", "Jet_phi", binning=(48, -6, 6),
                x_title=Label("jet #phi"),),
            Feature("jet_mass", "Jet_mass", binning=(30, 0, 150),
                x_title=Label("jet mass"),
                units="GeV"),

            Feature("jet_chEmEF", "Jet_chEmEF", binning=(20, 0, 2),
                x_title=Label("jet chEmEF")),
            Feature("jet_chHEF", "Jet_chHEF", binning=(20, 0, 2),
                x_title=Label("jet chHEF")),
            Feature("jet_neEmEF", "Jet_neEmEF", binning=(20, 0, 2),
                x_title=Label("jet neEmEF")),
            Feature("jet_neHEF", "Jet_neHEF", binning=(20, 0, 2),
                x_title=Label("jet neHEF")),
            Feature("jet_muEF", "Jet_muEF", binning=(20, 0, 2),
                x_title=Label("jet muEF")),
            Feature("jet_muonSubtrFactor", "Jet_muonSubtrFactor", binning=(20, 0, 1),
                x_title=Label("jet muonSubtrFactor")),
            Feature("jet_chFPV0EF", "Jet_chFPV0EF", binning=(20, 0, 2),
                x_title=Label("jet chFPV0EF")),
            Feature("jet_nMuons", "Jet_nMuons", binning=(5, -0.5, 4.5),
                x_title=Label("jet nMuons")),
            Feature("jet_nElectrons", "Jet_nElectrons", binning=(5, -0.5, 4.5),
                x_title=Label("jet nElectrons")),
            Feature("jet_nConstituents", "Jet_nConstituents", binning=(20, 0.5, 40.5),
                x_title=Label("jet nConstituents")),
            Feature("jet_btagDeepB", "Jet_btagDeepB", binning=(20, 0, 1),
                x_title=Label("jet btagDeepB")),
            Feature("jet_btagDeepC", "Jet_btagDeepC", binning=(20, 0, 1),
                x_title=Label("jet btagDeepC")),
            Feature("jet_qgl", "Jet_qgl", binning=(20, 0, 1),
                x_title=Label("jet qgl"), ),#selection="Jet_qgl >= 0"),
            Feature("Jet_puIdDisc", "Jet_puIdDisc", binning=(50, -1, 1),
                x_title=Label("jet puIdDisc")),
            Feature("jet_muonIdx1", "Jet_muonIdx1", binning=(10, -0.5, 9.5),
                x_title=Label("jet muonIdx1")),
            Feature("jet_muonIdx2", "Jet_muonIdx2", binning=(10, -0.5, 9.5),
                x_title=Label("jet muonIdx2")),

            Feature("nmuon", "nMuonBPark", binning=(10, -0.5, 9.5),
                x_title=Label("nMuon")),
            Feature("muon_pt", "MuonBPark_pt", binning=(30, 0, 150),
                x_title=Label("muon p_{T}"),
                units="GeV"),
            Feature("muon_eta", "MuonBPark_eta", binning=(50, -5, 5),
                x_title=Label("muon #eta"),),
            Feature("muon_phi", "MuonBPark_phi", binning=(48, -6, 6),
                x_title=Label("muon #phi"),),
            Feature("muon_mass", "MuonBPark_mass", binning=(120, 0, 4),
                x_title=Label("muon mass"),
                units="GeV"),

            Feature("muon_ptErr", "MuonBPark_ptErr", binning=(20, 0, 1),
                x_title=Label("muon ptErr")),
            Feature("muon_dxy", "MuonBPark_dxy", binning=(20, -2, 2),
                x_title=Label("muon dxy")),
            Feature("muon_dxyErr", "MuonBPark_dxyErr", binning=(20, 0, 0.5),
                x_title=Label("muon dxyErr")),
            Feature("muon_dz", "MuonBPark_dz", binning=(50, -10, 10),
                x_title=Label("muon dz")),
            Feature("muon_dzErr", "MuonBPark_dzErr", binning=(20, 0, 0.5),
                x_title=Label("muon dzErr")),
            Feature("muon_ip3d", "MuonBPark_ip3d", binning=(50, 0, 5),
                x_title=Label("muon ip3d")),
            Feature("muon_sip3d", "MuonBPark_sip3d", binning=(50, 0, 4000),
                x_title=Label("muon sip3d")),
            Feature("muon_charge", "MuonBPark_charge", binning=(3, -1.5, 1.5),
                x_title=Label("muon charge")),
            Feature("muon_tightId", "MuonBPark_tightId > 0", binning=(2, -0.5, 1.5),
                x_title=Label("muon tightId")),
            # softmva not available for MuonBPark col
            Feature("muon_pfRelIso03_all", "MuonBPark_pfRelIso03_all", binning=(70, 0, 7),
                x_title=Label("muon pfRelIso03_all")),
            # Feature("muon_miniPFRelIso_all", "MuonBPark_miniPFRelIso_all", binning=(70, 0, 7),
                # x_title=Label("muon miniPFRelIso_all")),
            # MuonBPark_jetIdx not available

            Feature("muonSV_chi2", "muonSV_chi2", binning=(50, 0, 1500),
                x_title=Label("muonSV chi2")),
            Feature("muonSV_pAngle", "muonSV_pAngle", binning=(70, 0, 3.5),
                x_title=Label("muonSV pAngle")),
            Feature("muonSV_dlen", "muonSV_dlen", binning=(80, 0, 20),
                x_title=Label("muonSV dlen")),
            Feature("muonSV_dlenSig", "muonSV_dlenSig", binning=(100, 0, 1500),
                x_title=Label("muonSV dlenSig")),
            Feature("muonSV_dxy", "muonSV_dxy", binning=(40, 0, 20),
                x_title=Label("muonSV dxy")),
            Feature("muonSV_dxySig", "muonSV_dxySig", binning=(100, 0, 2500),
                x_title=Label("muonSV dxySig")),

            Feature("muonSV_mu1pt", "muonSV_mu1pt", binning=(30, 0, 150),
                x_title=Label("muonSV muon1 p_{T}"),
                units="GeV"),
            Feature("muonSV_mu1eta", "muonSV_mu1eta", binning=(50, -5, 5),
                x_title=Label("muonSV muon1 #eta"),),
            Feature("muonSV_mu1phi", "muonSV_mu1phi", binning=(48, -6, 6),
                x_title=Label("muonSV muon1 #phi"),),
            Feature("muonSV_mu2pt", "muonSV_mu2pt", binning=(30, 0, 150),
                x_title=Label("muonSV muon2 p_{T}"),
                units="GeV"),
            Feature("muonSV_mu2eta", "muonSV_mu2eta", binning=(50, -5, 5),
                x_title=Label("muonSV muon2 #eta"),),
            Feature("muonSV_mu2phi", "muonSV_mu2phi", binning=(48, -6, 6),
                x_title=Label("muonSV muon2 #phi"),),
            # Feature("muonSV_deltaR", "muonSV_deltaR", binning=(48, -6, -6),
                # x_title=Label("muonSV #DeltaR"),),

            Feature("muonSV_x", "muonSV_x", binning=(50, -10, 10),
                x_title=Label("muonSV x"),),
            Feature("muonSV_y", "muonSV_y", binning=(50, -10, 10),
                x_title=Label("muonSV y"),),
            Feature("muonSV_z", "muonSV_z", binning=(100, -20, 20),
                x_title=Label("muonSV z"),),

            Feature("sv_pt", "SV_pt", binning=(30, 0, 150),
                x_title=Label("SV p_{T}"),
                units="GeV"),
            Feature("sv_eta", "SV_eta", binning=(50, -5, 5),
                x_title=Label("SV #eta"),),
            Feature("sv_phi", "SV_phi", binning=(48, -6, 6),
                x_title=Label("SV #phi"),),
            Feature("sv_mass", "SV_mass", binning=(120, 0, 4),
                x_title=Label("SV mass"),
                units="GeV"),
            Feature("sv_x", "SV_x", binning=(50, -4, 4),
                x_title=Label("muonSV x"),),
            Feature("sv_y", "SV_y", binning=(50, -4, 4),
                x_title=Label("muonSV y"),),
            Feature("sv_z", "SV_z", binning=(100, -20, 20),
                x_title=Label("muonSV z"),),
            Feature("sv_dxy", "SV_dxy", binning=(40, 0, 10),
                x_title=Label("SV dxy")),
            Feature("sv_dxySig", "SV_dxySig", binning=(100, 0, 750),
                x_title=Label("SV dxySig")),
            Feature("sv_dlen", "SV_dlen", binning=(72, 0, 12),
                x_title=Label("SV dlen")),
            Feature("sv_dlenSig", "SV_dlenSig", binning=(100, 0, 1000),
                x_title=Label("SV dlenSig")),
            Feature("sv_chi2", "SV_chi2", binning=(50, 0, 100),
                x_title=Label("SV chi2")),
            Feature("sv_pAngle", "SV_pAngle", binning=(70, 0, 3.5),
                x_title=Label("SV pAngle")),
             Feature("sv_ndof", "SV_ndof", binning=(15, -0.5, 14.5),
                x_title=Label("SV ndof")),

            Feature("nsv", "nsv", binning=(10, -0.5, 9.5),
                x_title=Label("nsv")),

            Feature("met_pt", "MET_pt", binning=(15, 0, 150),
                x_title=Label("MET p_{T}"),
                units="GeV"),
            Feature("met_phi", "MET_phi", binning=(32, -4, 4),
                x_title=Label("MET #phi"),
                units="GeV"),
            Feature("jet_btag", "Jet_btagDeepFlavB", binning=(20, 0, 1),
                x_title=Label("Jet btag (DeepFlavour b)")),
            Feature("max_jet_btag", "Max(Jet_btagDeepFlavB)", binning=(20, 0, 1),
                x_title=Label("Max Jet btag (DeepFlavour b)")),
            Feature("nbjets", "Jet_btagDeepFlavB[Jet_btagDeepFlavB > 0.2770].size()", binning=(6, -0.5, 5.5),
                x_title=Label("nbjets")),

            # BDT features
            Feature("bdt", "xgb0__m_2p0_ctau_10p0_xiO_1p0_xiL_1p0", binning=(20, 0, 1),
                x_title=Label("BDT score")),

            # Feature("muonSV_mass_min_chi2", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 22),
            Feature("muonSV_mass_min_chi2", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 4),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            # Feature("muonSV_mass_min_chi2_bdt", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 22),
            Feature("muonSV_mass_min_chi2_maxbdt", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 4),
                x_title=Label("muonSV mass (Min. #chi^{2}), BDT < 0.85"),
                selection="xgb0__m_2p0_ctau_10p0_xiO_1p0_xiL_1p0 < 0.85",
                units="GeV"),
            Feature("nmuonSV_3sigma", "nmuonSV_3sigma", binning=(11, -0.5, 10.5),
                x_title=Label("nmuonSV_3sigma")),

        ]
        return ObjectCollection(features)

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        weights.total_events_weights = ["genWeight", "puWeight"]
        # weights.total_events_weights = ["genWeight"]
        # weights.total_events_weights = ["1"]

        weights.base = ["genWeight", "puWeight"]  # others needed

        for category in self.categories:
            weights[category.name] = weights.base

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
