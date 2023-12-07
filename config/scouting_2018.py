from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.legacy_2018 import Config as legacy_config


class Config(legacy_config):

    def add_datasets(self):
        xs = {
            "qcd_15to20": 2799000,
            "qcd_20to30": 2526000,
            "qcd_30to50": 1362000,
            "qcd_50to80": 376600,
            "qcd_80to120": 88930,
            "qcd_120to170": 21230,
            "qcd_170to300": 7055,
            "qcd_300to470": 619,
            "qcd_470to600": 59.24,
            "qcd_600to800": 18.21,
            "qcd_800to1000": 3.275,
            "qcd_1000toInf": 1.078,
        }

        datasets = [
            Dataset("qcd_1000toInf",
                dataset="/QCD_PT-1000_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_1000toInf"),
                xs=xs["qcd_1000toInf"],
                merging={
                    "base": 10,
                },
            ),

            Dataset("qcd_120to170",
                dataset="/QCD_PT-120to170_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_120to170"),
                xs=xs["qcd_120to170"],
                merging={
                    "base": 10,
                },
            ),

            Dataset("qcd_15to20",
                dataset="/QCD_PT-15to20_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_15to20"),
                xs=xs["qcd_15to20"],
            ),

            Dataset("qcd_170to300",
                dataset="/QCD_PT-170to300_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_170to300"),
                xs=xs["qcd_170to300"],
                merging={
                    "base": 10,
                },
            ),

            Dataset("qcd_20to30",
                dataset="/QCD_PT-20to30_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_20to30"),
                xs=xs["qcd_20to30"],
            ),

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
                dataset="/QCD_PT-300to470_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_300to470"),
                xs=xs["qcd_300to470"],
                merging={
                    "base": 10,
                },
            ),

            Dataset("qcd_30to50",
                dataset="/QCD_PT-30to50_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_30to50"),
                xs=xs["qcd_30to50"],
            ),

            Dataset("qcd_470to600",
                dataset="/QCD_PT-470to600_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd"),
                xs=xs["qcd_470to600"],
                merging={
                    "base": 10,
                },
            ),

            Dataset("qcd_50to80",
                dataset="/QCD_PT-50to80_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_50to80"),
                xs=xs["qcd_50to80"],
            ),

            Dataset("qcd_600to800",
                dataset="/QCD_PT-600to800_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_600to800"),
                xs=xs["qcd_600to800"],
                merging={
                    "base": 10,
                },
            ),

            Dataset("qcd_80to120",
                dataset="/QCD_PT-80to120_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_80to120"),
                xs=xs["qcd_80to120"],
                merging={
                    "base": 10,
                },),

            Dataset("qcd_800to1000",
                dataset="/QCD_PT-800to1000_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/jleonhol-2022-34fb1e4890278e40567bdb707dc02eac/USER",
                process=self.processes.get("qcd_800to1000"),
                xs=xs["qcd_800to1000"],
                merging={
                    "base": 10,
                },),
        ]
        for dataset in datasets:
            dataset.check_empty = False
        return ObjectCollection(datasets)

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        weights.total_events_weights = ["puWeight"]
        # weights.total_events_weights = ["genWeight"]
        # weights.total_events_weights = ["1"]

        weights.base = ["puWeight", "PUjetID_SF"]  # others needed
        # weights.base = ["1"]  # others needed

        for category in self.categories:
            weights[category.name] = weights.base

        return weights

    # other methods

# config = Config("base", year=2018, ecm=13, lumi_pb=59741)
config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True)
