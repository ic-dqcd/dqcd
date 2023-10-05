from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.legacy_2018 import Config as legacy_config


class Config(legacy_config):

    def add_datasets(self):
        sample_path = "/vols/cms/mc3909/bparkProductionAll_V1p3/tmp/"

        datasets = [
            Dataset("data_2018d",
                folder=sample_path + "ParkingBPH1_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p3_generationSync",
                process=self.processes.get("data"),
                merging={
                    "base": 20,
                },
            ),
        ]
        return ObjectCollection(datasets)

    # other methods

# config = Config("base", year=2018, ecm=13, lumi_pb=59741)
config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True)
