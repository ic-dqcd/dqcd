from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.legacy_2018 import Config as legacy_config


class Config(legacy_config):

    def add_datasets(self):

        datasets = [
            Dataset("LambdaBToJpsiLambda",
                dataset = "/LambdaBToJpsiLambda_JpsiToMuMu_TuneCP5_13TeV-pythia8-evtgen/jleonhol-JPsiMC-5b19687ea081767d75d2860ff4c16949/USER", 
                process=self.processes.get("LambdaBToJpsiLambda"),
                check_empty=False,
            ),
            Dataset("egamma",
                dataset = "/EGamma/jleonhol-egamma-6838dccfc09128c984377350a24eba4a/USER",
                process=self.processes.get("egamma"),
                check_empty=False,
            ),
            Dataset("egamma_eraA",
                dataset = "/EGamma/jleonhol-egammaA-6838dccfc09128c984377350a24eba4a/USER",
                process=self.processes.get("egamma"),
                check_empty=False,
            ),
            Dataset("egamma_eraB",
                dataset = "/EGamma/jleonhol-egammaB-6838dccfc09128c984377350a24eba4a/USER",
                process=self.processes.get("egamma"),
                check_empty=False,
            ),
            Dataset("egamma_eraC",
                dataset = "/EGamma/jleonhol-egammaC-6838dccfc09128c984377350a24eba4a/USER" ,
                process=self.processes.get("egamma"),
                check_empty=False,
            ),

        ]
        return ObjectCollection(datasets)

    # other methods

# config = Config("base", year=2018, ecm=13, lumi_pb=59741)
config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True)
