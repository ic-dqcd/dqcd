import json
import luigi
import law
import math
import itertools
from copy import deepcopy as copy
from collections import OrderedDict

from analysis_tools.utils import create_file_dir, import_root

from cmt.base_tasks.combine import (
    CreateWorkspaceSL, SimplifiedLikelihood, MakeSLInputs, ConvertSLInputs, PlotSimplifiedLikelihood,
    GOFProduction, GOFPlot
)
from tasks.analysis import (
    DQCDBaseTask, FitConfigBaseTask, CreateDatacardsDQCD, CombineDatacardsDQCD, CreateWorkspaceDQCD,
    BaseScanTask
)

ROOT = import_root()


class CreateWorkspaceSLDQCD(DQCDBaseTask, FitConfigBaseTask, CreateWorkspaceSL):
    def requires(self):
        if self.combine_categories:
            return CombineDatacardsDQCD.vreq(self)
        reqs = {}
        for category_name in self.category_names:
            counting = self.fit_config[self.process_group_name.replace("data_", "")][category_name]
            process_group_name = (self.process_group_name
                if not counting or "data" in self.process_group_name
                else "qcd_" + self.process_group_name)
            reqs[category_name] = CreateDatacardsDQCD.vreq(self, category_name=category_name,
                counting=counting, process_group_name=process_group_name)
        return reqs

    def workflow_requires(self):
        if self.combine_categories:
            return {"data": CombineDatacardsDQCD.vreq(self)}
        reqs = {"data": {}}
        for category_name in self.category_names:
            # counting = self.fit_config[self.process_group_name][category_name]
            counting = False
            process_group_name = (self.process_group_name if not counting
                else "qcd_" + self.process_group_name)
            reqs["data"][category_name] = CreateDatacardsDQCD.vreq(self, category_name=category_name,
                counting=counting, process_group_name=process_group_name)
        return reqs


class SimplifiedLikelihoodDQCD(SimplifiedLikelihood, DQCDBaseTask, FitConfigBaseTask):

    def workflow_requires(self):
        return {"data": CreateWorkspaceSLDQCD.vreq(self)}

    def requires(self):
        return CreateWorkspaceSLDQCD.vreq(self)


class MakeSLInputsDQCD(MakeSLInputs, DQCDBaseTask, FitConfigBaseTask):
    def workflow_requires(self):
        """
        Requires the root files produced by SimplifiedLikelihood.
        """
        return {"data": SimplifiedLikelihoodDQCD.vreq(self)}

    def requires(self):
        """
        Requires the root files produced by SimplifiedLikelihood.
        """
        return SimplifiedLikelihoodDQCD.vreq(self)


class ConvertSLInputsDQCD(ConvertSLInputs, DQCDBaseTask, FitConfigBaseTask):
    def workflow_requires(self):
        """
        Requires the root file produced by MakeSLInputsDQCD.
        """
        return {"data": MakeSLInputsDQCD.vreq(self)}

    def requires(self):
        """
        Requires the root file produced by MakeSLInputsDQCD.
        """
        return MakeSLInputsDQCD.vreq(self)


class PlotSimplifiedLikelihoodDQCD(PlotSimplifiedLikelihood, DQCDBaseTask, FitConfigBaseTask):
    def workflow_requires(self):
        """
        Requires the python model of the SL and the root file storing the full likelihood.
        """
        return {
            "data": {
                "model": ConvertSLInputsDQCD.vreq(self),
                "full_like": SimplifiedLikelihoodDQCD.vreq(self)
            }
        }

    def requires(self):
        """
        Requires the python model of the SL and the root file storing the full likelihood.
        """
        return {
            "model": ConvertSLInputsDQCD.vreq(self),
            "full_like": SimplifiedLikelihoodDQCD.vreq(self)
        }


class GOFProductionDQCD(GOFProduction, DQCDBaseTask, FitConfigBaseTask):

    def workflow_requires(self):
        return {"data": CreateWorkspaceDQCD.vreq(self)}

    def requires(self):
        return CreateWorkspaceDQCD.vreq(self)


class GOFPlotDQCD(GOFPlot, DQCDBaseTask, FitConfigBaseTask):

    def workflow_requires(self):
        return {"data": GOFProductionDQCD.vreq(self)}

    def requires(self):
        return GOFProductionDQCD.vreq(self)


class ScanGOFDQCD(BaseScanTask):
    feature_names = ("muonSV_bestchi2_mass",)
    features_to_compute = lambda self, m: (f"self.config.get_feature_mass({m})",)

    def __init__(self, *args, **kwargs):
        super(ScanGOFDQCD, self).__init__(*args, **kwargs)
        assert (len(self.feature_names) == len(self.features_to_compute(1)))

    def requires(self):
        reqs = {}
        for pgn in self.process_group_names:
            mass_point = self.get_mass_point(pgn)
            mass_point_str = str(mass_point).replace(".", "p")
            signal = pgn[:pgn.find("_")]
            reqs[pgn] = GOFPlotDQCD.vreq(self, version=self.version + f"_m{mass_point_str}",
                feature_names=self.features_to_compute(mass_point),
                mass_point=mass_point,
                process_group_name=("data_" if self.use_data else "") + pgn,
                region_name=f"tight_bdt_{signal}",
                tight_region=f"tight_bdt_{signal}",
                loose_region=f"loose_bdt_{signal}",
                category_names=list(self.fit_config[pgn].keys()))
        return reqs

    def output(self):
        return {
            pgn: self.requires()[pgn].output()
            for pgn in self.process_group_names
        }

    def run(self):
        pass
