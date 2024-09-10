import json
import luigi
import law
import math
import itertools
from copy import deepcopy as copy
from collections import OrderedDict

from analysis_tools.utils import create_file_dir, import_root

from cmt.base_tasks.combine import (
    CreateWorkspaceSL, SimplifiedLikelihood, MakeSLInputs, ConvertSLInputs, PlotSimplifiedLikelihood
)
from tasks.analysis import DQCDBaseTask, FitConfigBaseTask, CreateDatacardsDQCD, CombineDatacardsDQCD

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
