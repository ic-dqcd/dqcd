import json
import luigi
import law
from copy import deepcopy as copy

from analysis_tools.utils import create_file_dir, import_root

from cmt.base_tasks.base import DatasetWrapperTask
from cmt.base_tasks.plotting import FeaturePlot
from cmt.base_tasks.analysis import (
    CombineBase, Fit, CreateDatacards, CombineDatacards, CreateWorkspace, RunCombine,
    PullsAndImpacts, MergePullsAndImpacts, PlotPullsAndImpacts
)

class DQCDBaseTask():
    tight_region = luigi.Parameter(default="tight_bdt", description="region_name with the "
        "tighter bdt cut, default: tight_bdt")
    loose_region = luigi.Parameter(default="loose_bdt", description="region_name with the "
        "looser bdt cut, default: loose_bdt")
    mass_point = luigi.FloatParameter(default=1.33, description="mass point to be used to "
        "define the fit ranges and blinded regions")

class CreateDatacardsDQCD(CreateDatacards, DQCDBaseTask):

    calibration_feature_name = "muonSV_bestchi2_mass_fullrange"

    def __init__(self, *args, **kwargs):
        super(CreateDatacardsDQCD, self).__init__(*args, **kwargs)
        if self.process_group_name != "default":
            self.models = self.modify_models()

    def modify_models(self):
        new_models = {}
        for process in self.config.process_group_names[self.process_group_name]:
            if self.config.processes.get(process).isSignal:
                signal_process = process
                break
        for model in self.models:
            process_name = self.models[model]["process_name"]
            if process_name != signal_process and self.config.processes.get(process_name).isSignal:
                # swap signal appearing in the model with the signal of this process_group_name
                new_models[signal_process] = copy(self.models[model])
                new_models[signal_process]["process_name"] = signal_process
            elif not self.config.processes.get(process_name).isSignal and \
                    not self.config.processes.get(process_name).isData and self.counting:
                # swap background appearing in the model with all separate qcd samples
                for process in self.config.process_group_names[self.process_group_name]:
                    if not self.config.processes.get(process).isSignal and \
                            not self.config.processes.get(process).isData:
                        new_models[process] = copy(self.models[model])
                        new_models[process]["process_name"] = process
            else:
                new_models[model] = copy(self.models[model])
        return new_models

    def requires(self):
        reqs = CreateDatacards.requires(self)
        sigma = self.mass_point * 0.01
        fit_range = (self.mass_point - 5 * sigma, self.mass_point + 5 * sigma)

        loose_region = self.region.name.replace("tight", "loose")
        for process in reqs["fits"]:
            reqs["fits"][process].x_range = fit_range
            if process == "data_obs":
                continue  # FIXME
            if not self.config.processes.get(process).isSignal and \
                    not self.config.processes.get(process).isData:
                reqs["fits"][process].region_name = loose_region
                reqs["inspections"][process].region_name = loose_region
            else:
                reqs["fits"][process].region_name = self.region_name  # probably redundant

        # get models for background scaling
        background_model_found = False
        for model, fit_params in self.models.items():
            fit_params["x_range"] = str(fit_range)[1:-1]
            # look for background or qcd_*
            if model == "data_obs": # FIXME
                continue
            process = fit_params["process_name"]
            if not self.config.processes.get(process).isSignal and \
                    not self.config.processes.get(process).isData and not background_model_found:
                background_model_found = True  # avoid looping over all qcd processes
                new_fit_params = copy(fit_params)
                new_fit_params["process_name"] = "background"
                params = ", ".join([f"{param}='{value}'"
                    for param, value in new_fit_params.items() if param != "fit_parameters"])
                if "fit_parameters" in new_fit_params:
                    params += ", fit_parameters={" + ", ".join([f"'{param}': '{value}'"
                    for param, value in new_fit_params["fit_parameters"].items()]) + "}"

                reqs["tight"] =  eval("Fit.vreq(self, version='muonsv_calibration_v2', "
                    f"{params}, _exclude=['include_fit'], "
                    "region_name=self.tight_region, "
                    "process_group_name='background', "
                    f"feature_names=('{self.calibration_feature_name}',), "
                    "category_name='base')")
                reqs["loose"] =  eval(f"Fit.vreq(self, version='muonsv_calibration_v2', "
                    f"{params}, _exclude=['include_fit'], "
                    "region_name=self.loose_region, "
                    "process_group_name='background', "
                    f"feature_names=('{self.calibration_feature_name}',), "
                    "category_name='base')")

        if self.counting:  # counting
            blind_range = (str(self.mass_point - 2 * sigma), str(self.mass_point + 2 * sigma))
            for process in reqs["fits"]:
                if process == "data_obs": # FIXME
                    reqs["fits"][process].x_range = (str(fit_range[0]), str(fit_range[1]))
                elif not self.config.processes.get(process).isSignal and \
                        not self.config.processes.get(process).isData:
                    reqs["fits"][process].x_range = (str(fit_range[0]), str(fit_range[1]))
                    reqs["fits"][process].blind_range = blind_range
                    reqs["inspections"][process].x_range = (str(fit_range[0]), str(fit_range[1]))
                    reqs["inspections"][process].region_name = self.loose_region
                    reqs["inspections"][process].blind_range = blind_range
                    reqs["inspections"][process].process_name = "background"
                    reqs["inspections"][process].process_group_name = self.process_group_name[len("qcd_"):]
                else:
                    reqs["fits"][process].x_range = blind_range
                    reqs["inspections"][process].x_range = blind_range
        return reqs

    def run(self):
        assert "tight" in self.region_name
        inputs = self.input()
        with open(inputs["tight"][self.calibration_feature_name]["json"].path) as f:
            d_tight = json.load(f)
        with open(inputs["loose"][self.calibration_feature_name]["json"].path) as f:
            d_loose = json.load(f)
        additional_scaling = d_tight[""]["integral"] / d_loose[""]["integral"]

        if not self.counting:
            self.additional_scaling = {"background": additional_scaling}
        else:
            self.additional_scaling = {}
            for process in self.config.process_group_names[self.process_group_name]:
                if not self.config.processes.get(process).isSignal and \
                        not self.config.processes.get(process).isData:
                    self.additional_scaling[process] = additional_scaling * 2/3

        super(CreateDatacardsDQCD, self).run()


class FitConfigBaseTask(law.Task):
    fit_config_file = luigi.Parameter(default="fit_config", description="file including "
        "fit configuration, default: fit_config.yaml")

    def __init__(self, *args, **kwargs):
        super(FitConfigBaseTask, self).__init__(*args, **kwargs)
        self.fit_config = self.get_fit_config(self.fit_config_file)
        if self.fit_config.get(self.process_group_name, False):
            self.category_names = self.fit_config[self.process_group_name].keys()
            self.category_name = list(self.category_names)[0]

    def get_fit_config(self, filename):
        import yaml
        import os
        from cmt.utils.yaml_utils import ordered_load
        with open(os.path.expandvars("$CMT_BASE/../config/{}.yaml".format(filename))) as f:
            return ordered_load(f, yaml.SafeLoader)


class CombineDatacardsDQCD(CombineDatacards, DQCDBaseTask, FitConfigBaseTask):
    category_name = "base"  # placeholder
    category_names = ("singlev", "multiv")  # placeholder

    def requires(self):
        reqs = {}
        for category_name in self.category_names:
            counting = self.fit_config[self.process_group_name][category_name]
            process_group_name = (self.process_group_name if not counting
                else "qcd_" + self.process_group_name)
            reqs[category_name] = CreateDatacardsDQCD.vreq(self, category_name=category_name,
                counting=counting, process_group_name=process_group_name,
                _exclude=["category_names"])

        return reqs


class CreateWorkspaceDQCD(CreateWorkspace, DQCDBaseTask, FitConfigBaseTask):
    def requires(self):
        if self.combine_categories:
            return CombineDatacardsDQCD.vreq(self)
        reqs = {}
        for category_name in self.category_names:
            counting = self.fit_config[self.process_group_name][category_name]
            process_group_name = (self.process_group_name if not counting
                else "qcd_" + self.process_group_name)
            reqs[category_name] = CreateDatacardsDQCD.vreq(self, category_name=category_name,
                counting=counting, process_group_name=process_group_name)
        return reqs

    def workflow_requires(self):
        if self.combine_categories:
            return {"data": CombineDatacardsDQCD.vreq(self)}
        reqs = {"data": {}}
        for category_name in self.category_names:
            counting = self.fit_config[self.process_group_name][category_name]
            process_group_name = (self.process_group_name if not counting
                else "qcd_" + self.process_group_name)
            reqs["data"][category_name] = CreateDatacardsDQCD.vreq(self, category_name=category_name,
                counting=counting, process_group_name=process_group_name)
        return reqs


class RunCombineDQCD(RunCombine, DQCDBaseTask, FitConfigBaseTask):
    method = "limits"

    def workflow_requires(self):
        return {"data": CreateWorkspaceDQCD.vreq(self)}

    def requires(self):
        return CreateWorkspaceDQCD.vreq(self)


class ProcessGroupNameWrapper(law.Task):
    process_group_names = law.CSVParameter(default=(), description="process_group_names to be used, "
        "empty means all scenarios, default: empty")
    process_group_name = "default"  # placeholder

    def __init__(self, *args, **kwargs):
        super(ProcessGroupNameWrapper, self).__init__(*args, **kwargs)
        if not self.process_group_names:
            self.process_group_names = list(self.fit_config.keys())
        self.process_group_name = self.process_group_names[0]
        self.category_names = list(self.fit_config[self.process_group_name].keys())
        self.category_name = self.category_names[0]


class ScanCombineDQCD(ProcessGroupNameWrapper, DQCDBaseTask, FitConfigBaseTask):
    def requires(self):
        reqs = {}
        for process_group_name in self.process_group_names:
            if "scenario" in process_group_name:
                signal_tag = "A"
            else:
                signal_tag = "zd"
            i = process_group_name.find(f"m{signal_tag}_")
            f = process_group_name.find("_ctau")
            mass_point = float(process_group_name[i + 2 + len(signal_tag):f].replace("p", "."))
            if mass_point == 0.33:
                mass_point = 0.333
            elif mass_point == 0.67:
                mass_point = 0.667
            signal = process_group_name[:process_group_name.find("_")]
            reqs[process_group_name] = RunCombineDQCD.vreq(self, mass_point=mass_point,
                process_group_name=process_group_name, region_name=f"tight_bdt_{signal}",
                category_names = self.fit_config[self.process_group_name].keys())
        return reqs

    def workflow_requires(self):
        reqs = {"data": {}}
        for process_group_name in self.process_group_names:
            if "scenario" in process_group_name:
                signal_tag = "A"
            else:
                signal_tag = "zd"
            i = process_group_name.find(f"m{signal_tag}_")
            f = process_group_name.find("_ctau")
            mass_point = float(process_group_name[i + 2 + len(signal_tag):f].replace("p", "."))
            if mass_point == 0.33:
                mass_point = 0.333
            elif mass_point == 0.67:
                mass_point = 0.667
            signal = process_group_name[:process_group_name.find("_")]
            reqs["data"][process_group_name] = RunCombineDQCD.vreq(self, mass_point=mass_point,
                process_group_name=process_group_name, region_name=f"tight_bdt_{signal}",
                category_names = self.fit_config[self.process_group_name].keys())
        return reqs

    def output(self):
        assert not self.combine_categories or (
            self.combine_categories and len(self.category_names) > 1)
        return {
            process_group_name: {
                feature.name: self.local_target("results_{}{}.json".format(
                    feature.name, self.get_output_postfix(process_group_name=process_group_name,
                        category_names=self.fit_config[self.process_group_name].keys())))
                for feature in self.features
            } for process_group_name in self.process_group_names
        }

    def combine_parser(self, filename):
        import os
        res = {}
        with open(os.path.expandvars(filename), "r") as f:
            lines = f.readlines()
            for line in lines:
                if "Observed" in line:
                    res["observed"] = float(line.split(" ")[-1][0:-1])
                elif "Expected" in line:
                    index = line.find("%")
                    res[float(line[index - 4: index])] = float(line.split(" ")[-1][0:-1])
        return res

    def run(self):
        inputs = self.input()
        for pgn in self.process_group_names:
            for feature in self.features:
                res = self.combine_parser(inputs[pgn][feature.name]["txt"].path)
                if not res:
                    print("Fit for %s did not converge. Filling with dummy values." % pgn)
                    res = {
                        "2.5": 1.,
                        "16.0": 1.,
                        "50.0": 1.,
                        "84.0": 1.,
                        "97.5": 1.
                    }
                with open(create_file_dir(self.output()[pgn][feature.name].path), "w+") as f:
                    json.dump(res, f, indent=4)


class InspectPlotDQCD(CombineBase, DQCDBaseTask, ProcessGroupNameWrapper, FitConfigBaseTask):
    def requires(self):
        reqs = {}
        for process_group_name in self.process_group_names:
            signal = process_group_name[:process_group_name.find("_")]
            tight_region = f"tight_bdt_{signal}"
            loose_region = f"loose_bdt_{signal}"

            reqs[process_group_name] = {}
            for category_name in self.fit_config[process_group_name].keys():
                reqs[process_group_name][category_name] = {
                    "signal": FeaturePlot.vreq(
                        self, save_root=True, stack=True, hide_data=False, normalize_signals=False,
                        process_group_name=process_group_name, region_name=tight_region,
                        category_name=category_name),
                    "background": FeaturePlot.vreq(
                        self, save_root=True, stack=True, hide_data=False, normalize_signals=False,
                        process_group_name=process_group_name, region_name=loose_region,
                        category_name=category_name)
                    }
        return reqs

    def output(self):
        return {
            process_group_name: {
                feature.name: self.local_target("results_{}{}.root".format(
                    feature.name, self.get_output_postfix(process_group_name=process_group_name)))
                for feature in self.features
            } for process_group_name in self.process_group_names
        }

    def run(self):
        ROOT = import_root()
        inputs = self.input()
        for pgn in self.process_group_names:
            for feature in self.features:
                out_tf = ROOT.TFile.Open(create_file_dir(self.output()[pgn][feature.name].path),
                    "RECREATE")
                for cat in self.fit_config[pgn].keys():
                    signal_tf = ROOT.TFile.Open(
                        inputs[pgn][cat]["signal"]["root"].targets[feature.name].path)
                    bkg_tf = ROOT.TFile.Open(
                        inputs[pgn][cat]["background"]["root"].targets[feature.name].path)
                    for process in self.config.process_group_names[pgn]:
                        if self.config.processes.get(process).isSignal:
                            signal_tf.cd()
                            signal_histo = copy(signal_tf.Get("histograms/" + process))
                            out_tf.cd()
                            signal_histo.Write(f"{process}__{cat}")
                        elif process == "background":
                            bkg_tf.cd()
                            bkg_histo = copy(bkg_tf.Get("histograms/" + process))
                            out_tf.cd()
                            bkg_histo.Write(f"{process}__{cat}")
                    signal_tf.Close()
                    bkg_tf.Close()
                out_tf.Close()


class PullsAndImpactsDQCD(PullsAndImpacts, FitConfigBaseTask, DQCDBaseTask):
    def __init__(self, *args, **kwargs):
        super(PullsAndImpactsDQCD, self).__init__(*args, **kwargs)


    @law.workflow_property(setter=False, empty_value=law.no_value, cache=True)
    def workspace_parameters(self):
        ws_input = CreateWorkspaceDQCD.vreq(self, branch=0).output()[self.features[0].name]
        if not ws_input.exists():
            return law.no_value
        return self.extract_nuisance_names(ws_input.path)

    def workflow_requires(self):
        return {"data": CreateWorkspaceDQCD.vreq(self, _exclude=["branches", "branch"])}

    def requires(self):
        return CreateWorkspaceDQCD.vreq(self, _exclude=["branches", "branch"])


class MergePullsAndImpactsDQCD(MergePullsAndImpacts, FitConfigBaseTask, DQCDBaseTask):
    def requires(self):
        return PullsAndImpactsDQCD.vreq(self)


class PlotPullsAndImpactsDQCD(PlotPullsAndImpacts, FitConfigBaseTask, DQCDBaseTask):
    def requires(self):
        return MergePullsAndImpactsDQCD.vreq(self)
