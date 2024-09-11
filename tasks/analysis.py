import json
import luigi
import law
import math
import itertools
from copy import deepcopy as copy
from collections import OrderedDict

from analysis_tools.utils import create_file_dir, import_root

from cmt.base_tasks.base import DatasetWrapperTask, HTCondorWorkflow, SGEWorkflow, SlurmWorkflow
from cmt.base_tasks.plotting import FeaturePlot
from cmt.base_tasks.analysis import (
    FitBase, CombineBase, CombineCategoriesTask, Fit, InspectFitSyst, CreateDatacards,
    CombineDatacards, CreateWorkspace, RunCombine, PullsAndImpacts, MergePullsAndImpacts,
    PlotPullsAndImpacts, ValidateDatacards
)

ROOT = import_root()

class DQCDBaseTask(DatasetWrapperTask):
    tight_region = luigi.Parameter(default="tight_bdt_scenarioA", description="region_name with the "
        "tighter bdt cut, default: tight_bdt")
    loose_region = luigi.Parameter(default="loose_bdt_scenarioA", description="region_name with the "
        "looser bdt cut, default: loose_bdt")
    mass_point = luigi.FloatParameter(default=1.33, description="mass point to be used to "
        "define the fit ranges and blinded regions")
    use_refit = luigi.BoolParameter(default=False, description="whether to extract the sigmas "
        "from the base category, default: True")
    custom_signal_fit_parameters = luigi.DictParameter(default={}, description="Initial values for "
        "the parameters involved in the fit, defaults depend on the method. Should be included as "
        "--custom-signal-fit-parameters '{\"mean\": \"(20, -100, 100)\"}'")

    default_process_group_name = "sigbkg"

    def modify_models(self):
        new_models = {}
        try:
            # if it's a signal coming from the grid, it won't be defined as a process_group_name
            # in the config, so we don't have to look for it
            for process in self.config.process_group_names[self.process_group_name.replace("data_", "")]:
                if self.config.processes.get(process).isSignal:
                    signal_process = process
                    break
        except KeyError:
            signal_process = self.process_group_name
            # self.process_group_name = "sigbkg"

        for model in self.models:
            process_name = self.models[model]["process_name"]
            if process_name != signal_process and self.config.processes.get(process_name).isSignal:
                # swap signal appearing in the model with the signal of this process_group_name
                new_models[signal_process] = copy(self.models[model])
                new_models[signal_process]["process_name"] = signal_process
                new_models[signal_process]["x_range"] = str(self.fit_range)[1:-1]
                if "fit_parameters" not in new_models[signal_process]:
                    new_models[signal_process]["fit_parameters"] = {}
                if len(self.custom_signal_fit_parameters) > 0:
                    new_models[signal_process]["fit_parameters"] = self.custom_signal_fit_parameters
                else:
                    new_models[signal_process]["fit_parameters"]["mean"] = "{}, {}, {}".format(
                        self.mass_point, self.mass_point - 1, self.mass_point + 1)
            elif not self.config.processes.get(process_name).isSignal and \
                    not self.config.processes.get(process_name).isData and self.counting:
                # swap background appearing in the model with all separate qcd samples
                for process in self.config.process_group_names[self.process_group_name]:
                    if not self.config.processes.get(process).isSignal and \
                            not self.config.processes.get(process).isData:
                        new_models[process] = copy(self.models[model])
                        new_models[process]["process_name"] = process
                        new_models[process]["x_range"] = str(self.fit_range)[1:-1]
            else:
                new_models[model] = copy(self.models[model])
                new_models[model]["x_range"] = str(self.fit_range)[1:-1]

        return new_models

    def get_output_postfix(self, **kwargs):
        postfix = super(DQCDBaseTask, self).get_output_postfix(**kwargs)
        if self.use_refit:
            postfix += "__refit"
        return postfix


class FitDQCD(Fit, DQCDBaseTask):
    calibration_feature_name = "muonSV_bestchi2_mass_fullrange"
    calibration_category_name = "base"

    def requires(self):
        reqs = super(FitDQCD, self).requires()
        reqs["tight"] = Fit.vreq(self,
            x_range=(0, 22),
            region_name=self.tight_region,
            feature_names=(self.calibration_feature_name,),
            category_name=self.calibration_category_name)
        reqs["loose"] = Fit.vreq(self,
            x_range=(0, 22),
            region_name=self.loose_region,
            feature_names=(self.calibration_feature_name,),
            category_name=self.calibration_category_name)
        return reqs

    def get_additional_scaling(self):
        inputs = self.input()
        with open(inputs["tight"][self.calibration_feature_name]["json"].path) as f:
            d_tight = json.load(f)
        with open(inputs["loose"][self.calibration_feature_name]["json"].path) as f:
            d_loose = json.load(f)
        additional_scaling = d_tight[""]["integral"] / d_loose[""]["integral"]
        self.additional_scaling = {self.process_name: additional_scaling}
        return self.additional_scaling

    def run(self):
        self.get_additional_scaling()
        super(FitDQCD, self).run()


class CreateDatacardsDQCD(DQCDBaseTask, CreateDatacards):

    calibration_feature_name = "muonSV_bestchi2_mass_fullrange"
    refit_signal_with_syst = False
    min_events_for_fitting = 0
    norm_bkg_to_data = True
    save_proper_norm = False

    def __init__(self, *args, **kwargs):
        super(CreateDatacardsDQCD, self).__init__(*args, **kwargs)
        self.mass_point = ProcessGroupNameWrapper.get_mass_point(self, self.process_group_name)
        self.sigma = self.mass_point * 0.01
        self.fit_range = (self.mass_point - 5 * self.sigma, self.mass_point + 5 * self.sigma)
        self.blind_range = (self.mass_point - 2 * self.sigma, self.mass_point + 2 * self.sigma)
        # if self.process_group_name != "default":
        self.models = self.modify_models()
        self.cls = Fit if not self.use_refit else ReFitDQCD

        self.use_data = any("data" in model["process_name"] for model in self.models.values())

    def requires(self):
        reqs = super(CreateDatacardsDQCD, self).requires()

        loose_region = self.region.name.replace("tight", "loose")
        if not self.counting:
            for process in reqs["fits"]:
                x_range = self.fit_range
                if process == "data_obs":
                    # print("*******************************************************")
                    # print("WARNING: You are using loose_region to fit data histo")
                    # print("*******************************************************")
                    reqs["fits"][process] = Fit.vreq(reqs["fits"][process],
                        region_name=self.region.name, x_range=x_range, process_group_name="data",
                        save_pdf=False)
                        # region_name=loose_region, x_range=x_range, process_group_name="data")
                    continue  # FIXME
                if not self.config.processes.get(process).isSignal and \
                        not self.config.processes.get(process).isData:  # MC Background
                    region_name = loose_region
                    process_group_name = "background"
                    cls = FitDQCD
                elif self.config.processes.get(process).isData:
                    reqs["fits"][process] = Fit.vreq(reqs["fits"][process],
                        # region_name=loose_region, x_range=x_range, blind_range=self.blind_range,
                        region_name=self.region.name, x_range=x_range, blind_range=self.blind_range,
                        process_group_name="data")
                    reqs["constant_fit"] = Fit.vreq(reqs["fits"][process],
                        # region_name=loose_region, x_range=x_range, blind_range=self.blind_range,
                        region_name=self.region.name, x_range=x_range, blind_range=self.blind_range,
                        process_group_name="data", method="constant")
                    del reqs["inspections"][process]
                    continue
                else:
                    region_name = self.region_name  # probably redundant
                    # region_name = loose_region  # probably redundant
                    process_group_name = "sig_" + self.process_group_name.replace("data_", "")
                    cls = self.cls

                if cls == Fit:
                    reqs["fits"][process] = cls.vreq(reqs["fits"][process], region_name=region_name,
                        x_range=x_range, process_group_name=process_group_name)
                else:
                    reqs["fits"][process] = cls.vreq(reqs["fits"][process], region_name=region_name,
                        x_range=x_range, process_group_name=process_group_name,
                        tight_region=self.tight_region, loose_region=self.loose_region)
                reqs["inspections"][process] = InspectFitSyst.vreq(reqs["inspections"][process],
                    region_name=region_name, x_range=x_range, process_group_name=process_group_name)

        else:  # counting
            process_tag = "qcd_" if not "data" in self.process_group_name else "data_"
            self.additional_scaling = {"background": 2./3.}
            for process in reqs["fits"]:
                blind_range = (str(self.mass_point - 2 * self.sigma), str(self.mass_point + 2 * self.sigma))
                if process == "data_obs": # FIXME
                    x_range = blind_range
                    process_group_name = "data"
                    blind_range = ("-1", "-1")
                    region_name = self.region_name
                    cls = Fit
                elif not self.config.processes.get(process).isSignal and \
                        not self.config.processes.get(process).isData:  # Background from MC
                    x_range = (str(self.fit_range[0]), str(self.fit_range[1]))
                    blind_range = blind_range
                    process_group_name = "qcd_background"
                    ins_process_group_name = "background"
                    ins_process_name = "background"
                    region_name = loose_region
                    cls = FitDQCD
                elif self.config.processes.get(process).isData: # Background from Data
                    x_range = (str(self.fit_range[0]), str(self.fit_range[1]))
                    blind_range = blind_range
                    process_group_name = self.process_group_name
                    region_name = self.region_name
                    cls = Fit
                else:
                    x_range = blind_range
                    blind_range = ("-1", "-1")
                    process_group_name = "sig_" + self.process_group_name[len(process_tag):]
                    ins_process_group_name = "sig_" + self.process_group_name[len(process_tag):]
                    ins_process_name = self.process_group_name[len(process_tag):]
                    region_name = self.region_name
                    cls = self.cls

                reqs["fits"][process] = cls.vreq(reqs["fits"][process], region_name=region_name,
                    x_range=x_range, process_group_name=process_group_name, blind_range=blind_range)
                if process != "data_obs" and not self.config.processes.get(process).isData:
                    reqs["inspections"][process] = InspectFitSyst.vreq(reqs["inspections"][process],
                        region_name=region_name, x_range=x_range,
                        process_group_name=ins_process_group_name, blind_range=blind_range,
                        process_name=ins_process_name)

        # # get models for background scaling
        # if not self.use_data:
            # background_model_found = False
            # for model, fit_params in self.models.items():
                # fit_params["x_range"] = str(self.fit_range)[1:-1]
                # # look for background or qcd_*
                # if model == "data_obs": # FIXME
                    # continue
                # process = fit_params["process_name"]
                # # if not self.config.processes.get(process).isSignal and \
                        # # not self.config.processes.get(process).isData and not background_model_found:
                # if not self.config.processes.get(process).isSignal and not background_model_found:
                    # background_model_found = True  # avoid looping over all qcd processes
                    # new_fit_params = copy(fit_params)
                    # if not self.config.processes.get(process).isData:
                        # new_fit_params["process_name"] = "background"
                    # params = ", ".join([f"{param}='{value}'"
                        # for param, value in new_fit_params.items() if param != "fit_parameters"])
                    # if "fit_parameters" in new_fit_params:
                        # params += ", fit_parameters={" + ", ".join([f"'{param}': '{value}'"
                        # for param, value in new_fit_params["fit_parameters"].items()]) + "}"
                    # reqs["tight"] =  eval("Fit.vreq(self, "
                        # f"{params}, _exclude=['include_fit'], "
                        # "region_name=self.tight_region, "
                        # f"process_group_name='{process}', "
                        # f"feature_names=('{self.calibration_feature_name}',), "
                        # "category_name='base')")
                    # reqs["loose"] =  eval(f"Fit.vreq(self, "
                        # f"{params}, _exclude=['include_fit'], "
                        # "region_name=self.loose_region, "
                        # f"process_group_name='{process}', "
                        # f"feature_names=('{self.calibration_feature_name}',), "
                        # "category_name='base')")

        # from pprint import pprint
        # pprint(reqs)
        # import sys
        # sys.exit()

        return reqs

    # def get_additional_scaling(self):
        # if self.use_data:
            # return {}
        # inputs = self.input()
        # with open(inputs["tight"][self.calibration_feature_name]["json"].path) as f:
            # d_tight = json.load(f)
        # with open(inputs["loose"][self.calibration_feature_name]["json"].path) as f:
            # d_loose = json.load(f)
        # additional_scaling = d_tight[""]["integral"] / d_loose[""]["integral"]

        # if not self.counting:
            # self.additional_scaling = {"background": additional_scaling}
        # else:
            # self.additional_scaling = {}
            # for process in self.config.process_group_names[self.process_group_name]:
                # if not self.config.processes.get(process).isSignal and \
                        # not self.config.processes.get(process).isData:
                    # self.additional_scaling[process] = additional_scaling * 2/3
        # return self.additional_scaling

    def get_fit_path(self, fit_params, feature):
        if not isinstance(fit_params, str):
            if fit_params["process_name"] == "data":
                # if the number of events in the unblinded region is smaller than 10, use the constant
                # fit instead
                p = self.input()["fits"][fit_params["process_name"]][feature.name]["json"].path
                with open(p) as f:
                    d = json.load(f)
                if d[""]["integral"] < self.min_events_for_fitting:
                    self.log.write(f"Data histogram has {d['']['integral']} events, smaller than "
                        f"the threshold ({self.min_events_for_fitting}) -> constant fit is "
                        "considered for the data\n")
                    return self.input()["constant_fit"][feature.name]["root"].path
        elif fit_params == "data_obs" and not self.use_data:
            for p_name in self.non_data_names:
                if not self.config.processes.get(p_name).isSignal:
                    break
            return super(CreateDatacardsDQCD, self).get_fit_path(p_name, feature)
        return super(CreateDatacardsDQCD, self).get_fit_path(fit_params, feature)

    def model_uses_envelope(self, fit_params, feature):
        if fit_params["process_name"] == "data":
            p = self.input()["fits"][fit_params["process_name"]][feature.name]["json"].path
            with open(p) as f:
                d = json.load(f)
            if d[""]["integral"] < self.min_events_for_fitting:
                return False
        return fit_params.get("method") == "envelope"

    def get_data_obs_workspace(self, feature):
        if self.use_data:
            return super(CreateDatacardsDQCD, self).get_data_obs_workspace(feature)
        for p_name in self.non_data_names:
            if not self.config.processes.get(p_name).isSignal:
                break
        model_tf = ROOT.TFile.Open(self.get_fit_path(p_name, feature))
        return model_tf.Get("workspace_" + p_name)

    def get_shape_line(self, process_in_datacard, bin_name, process_name, feature):
        if process_name == "data_obs" and not self.use_data:
            return super(CreateDatacardsDQCD, self).get_shape_line(
                "data_obs", bin_name, "background", feature)
        return super(CreateDatacardsDQCD, self).get_shape_line(
            process_in_datacard, bin_name, process_name, feature)

    def run(self):
        # assert "tight" in self.region_name
        # self.get_additional_scaling()
        super(CreateDatacardsDQCD, self).run()


class FitConfigBaseTask(DatasetWrapperTask):
    fit_config_file = luigi.Parameter(default="fit_config", description="file including "
        "fit configuration, default: fit_config.yaml")

    def __init__(self, *args, **kwargs):
        super(FitConfigBaseTask, self).__init__(*args, **kwargs)
        self.fit_config = self.get_fit_config(self.fit_config_file)
        # if self.fit_config.get(self.process_group_name, False):
            # self.category_names = self.fit_config[self.process_group_name].keys()
            # self.category_name = list(self.category_names)[0]

    def get_fit_config(self, filename):
        import yaml
        import os
        from cmt.utils.yaml_utils import ordered_load
        with open(os.path.expandvars("$CMT_BASE/../config/{}.yaml".format(filename))) as f:
            return ordered_load(f, yaml.SafeLoader)


class CombineDatacardsDQCD(CombineDatacards, DQCDBaseTask, FitConfigBaseTask):

    def requires(self):
        reqs = {}
        # print("************************************************")
        # print("WARNING: counting=False regardless of fit_config")
        # print("************************************************")
        # Fixes needed both here and in CreateWorkspaceDQCD
        for category_name in self.category_names:
            counting = self.fit_config[self.process_group_name.replace("data_", "")][category_name]
            # counting = False
            process_group_name = (self.process_group_name
                if not counting or "data" in self.process_group_name
                else "qcd_" + self.process_group_name)
            reqs[category_name] = CreateDatacardsDQCD.vreq(self, category_name=category_name,
                counting=counting, process_group_name=process_group_name,
                _exclude=["category_names"])

        return reqs

class CreateWorkspaceDQCD(DQCDBaseTask, FitConfigBaseTask, CreateWorkspace):
    def requires(self):
        if self.combine_categories:
            return CombineDatacardsDQCD.vreq(self)
        reqs = {}
        for category_name in self.category_names:
            # counting = self.fit_config[self.process_group_name][category_name]
            counting = False
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
            # counting = self.fit_config[self.process_group_name][category_name]
            counting = False
            process_group_name = (self.process_group_name if not counting
                else "qcd_" + self.process_group_name)
            reqs["data"][category_name] = CreateDatacardsDQCD.vreq(self, category_name=category_name,
                counting=counting, process_group_name=process_group_name)
        return reqs


class ValidateDatacardsDQCD(ValidateDatacards, DQCDBaseTask, FitConfigBaseTask):
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


class ProcessGroupNameWrapper(FitConfigBaseTask):
    process_group_names = law.CSVParameter(default=(), description="process_group_names to be used, "
        "empty means all scenarios, default: empty")
    use_data = luigi.BoolParameter(default=True, description="whether to extract the background from "
        "the data sidebands, default: True")

    def get_mass_point(self, process_group_name, signal_tag=None):
        if signal_tag:
            signal_tag = signal_tag
        elif "scenario" in process_group_name:
            signal_tag = "A"
        elif "hzdzd" in process_group_name:
            signal_tag = "zd"
        elif "zprime" in process_group_name:
            signal_tag = "pi"
        elif "vector" in process_group_name or "btophi" in process_group_name:
            signal_tag = ""
        else:
            raise ValueError(f"{process_group_name} can't be handled by ProcessGroupNameWrapper")
        i = process_group_name.find(f"m{signal_tag}_")
        f = process_group_name.find("_ctau")
        mass_point = float(process_group_name[i + 2 + len(signal_tag):f].replace("p", "."))
        if mass_point == 0.33:
            mass_point = 0.333
        elif mass_point == 0.67:
            mass_point = 0.667
        return mass_point

    def get_ctau(self, process_group_name):
        ctau = process_group_name.split("_ctau_")[1].replace("p", ".")
        try:
            ctau = float(ctau)
        except ValueError:  # vector portal has _xiO_1_xiL_1 after ctau, need to remove it
            ctau = float(ctau.split("_")[0])
        return ctau

    def __init__(self, *args, **kwargs):
        super(ProcessGroupNameWrapper, self).__init__(*args, **kwargs)
        if not self.process_group_names:
            self.process_group_names = list(self.fit_config.keys())
        # self.process_group_name = self.process_group_names[0]
        # self.category_names = list(self.fit_config[self.process_group_name].keys())
        # self.category_name = self.category_names[0]


class BaseScanTask(CombineCategoriesTask, ProcessGroupNameWrapper): #law.LocalWorkflow,
        # HTCondorWorkflow, SGEWorkflow, SlurmWorkflow):

    def combine_parser(self, filename):
        import os
        res = {}
        with open(os.path.expandvars(filename), "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("Observed"):
                    res["observed"] = float(line.split(" ")[-1][0:-1])
                elif line.startswith("Expected"):
                    index = line.find("%")
                    res[float(line[index - 4: index])] = float(line.split(" ")[-1][0:-1])
        if len(res) <= 1:
            res = {}
        return res

    def run(self):
        for pgn in self.process_group_names:
            for feature, feature_to_save in zip(self.requires()[pgn].features, self.features):
                if self.combine_categories:
                    res = self.combine_parser(
                        self.input()[pgn]["collection"].targets[0][feature.name]["txt"].path)
                    if not res:
                        print("Fit did not converge. Filling with dummy values.")
                        res = {
                            "2.5": 1.,
                            "16.0": 1.,
                            "50.0": 1.,
                            "84.0": 1.,
                            "97.5": 1.
                        }
                    with open(create_file_dir(
                            self.output()[pgn][feature_to_save.name].path), "w+") as f:
                        json.dump(res, f, indent=4)
                else:
                    for icat, cat in enumerate(self.fit_config[pgn].keys()):
                        res = self.combine_parser(
                            self.input()[pgn]["collection"].targets[icat][feature.name]["txt"].path)
                        if not res:
                            print("Fit did not converge. Filling with dummy values.")
                            res = {
                                "2.5": 1.,
                                "16.0": 1.,
                                "50.0": 1.,
                                "84.0": 1.,
                                "97.5": 1.
                            }
                        with open(create_file_dir(
                                self.output()[pgn][cat][feature_to_save.name].path), "w+") as f:
                            json.dump(res, f, indent=4)


class ScanCombineDQCD(BaseScanTask):
    feature_names = ("muonSV_bestchi2_mass",)
    features_to_compute = lambda self, m: (f"self.config.get_feature_mass({m})",)

    def __init__(self, *args, **kwargs):
        super(ScanCombineDQCD, self).__init__(*args, **kwargs)
        # assert(
            # self.combine_categories or len(self.process_group_names)
        # )
        assert (len(self.feature_names) == len(self.features_to_compute(1)))

    def requires(self):
        reqs = {}
        for pgn in self.process_group_names:
            mass_point = self.get_mass_point(pgn)
            mass_point_str = str(mass_point).replace(".", "p")
            signal = pgn[:pgn.find("_")]
            reqs[pgn] = RunCombineDQCD.vreq(self, version=self.version + f"_m{mass_point_str}",
                feature_names=self.features_to_compute(mass_point),
                mass_point=mass_point,
                process_group_name=("data_" if self.use_data else "") + pgn,
                region_name=f"tight_bdt_{signal}",
                tight_region=f"tight_bdt_{signal}",
                loose_region=f"loose_bdt_{signal}",
                category_names=list(self.fit_config[pgn].keys()))
        return reqs


    # def create_branch_map(self):
        # if self.combine_categories:
            # return self.process_group_names
        # else:
            # process_group_name = self.process_group_names[0]
            # return list(self.fit_config[process_group_name].keys())

    # def requires(self):
        # if self.combine_categories:
            # process_group_name=self.process_group_names[self.branch]
            # mass_point = self.get_mass_point(process_group_name)
            # signal = process_group_name[:process_group_name.find("_")]
            # return RunCombineDQCD.vreq(self, version=self.version + f"_m{mass_point}",
                # feature_names=(f"self.config.get_feature_mass({mass_point})",),
                # mass_point=mass_point,
                # process_group_name=("data_" if self.use_data else "") + process_group_name,
                # region_name=f"tight_bdt_{signal}",
                # tight_region=f"tight_bdt_{signal}",
                # loose_region=f"loose_bdt_{signal}",
                # category_names=self.fit_config[process_group_name].keys(),
                # _exclude=["branches", "branch"])
        # else:
            # process_group_name=self.process_group_names[0]
            # mass_point = self.get_mass_point(process_group_name)
            # signal = process_group_name[:process_group_name.find("_")]
            # return RunCombineDQCD.vreq(self, version=self.version + f"_m{mass_point}",
                # feature_names=(f"self.config.get_feature_mass({mass_point})",),
                # mass_point=mass_point,
                # process_group_name=("data_" if self.use_data else "") + process_group_name,
                # region_name=f"tight_bdt_{signal}",
                # tight_region=f"tight_bdt_{signal}",
                # loose_region=f"loose_bdt_{signal}",
                # category_names=self.fit_config[process_group_name].keys(),
                # _exclude=["branches", "branch"])

    # def workflow_requires(self):
        # if self.combine_categories:
            # process_group_name=self.process_group_names[self.branch]
            # mass_point = self.get_mass_point(process_group_name)
            # signal = process_group_name[:process_group_name.find("_")]
            # return {"data": RunCombineDQCD.vreq(self, version=self.version + f"_m{mass_point}",
                # feature_names=(f"self.config.get_feature_mass({mass_point})",),
                # mass_point=mass_point,
                # process_group_name=("data_" if self.use_data else "") + process_group_name,
                # region_name=f"tight_bdt_{signal}",
                # tight_region=f"tight_bdt_{signal}",
                # loose_region=f"loose_bdt_{signal}",
                # category_names=self.fit_config[process_group_name].keys(),
                # _exclude=["branches", "branch"])}
        # else:
            # process_group_name=self.process_group_names[0]
            # mass_point = self.get_mass_point(process_group_name)
            # signal = process_group_name[:process_group_name.find("_")]
            # return {"data": RunCombineDQCD.vreq(self, version=self.version + f"_m{mass_point}",
                # feature_names=(f"self.config.get_feature_mass({mass_point})",),
                # mass_point=mass_point,
                # process_group_name=("data_" if self.use_data else "") + process_group_name,
                # region_name=f"tight_bdt_{signal}",
                # tight_region=f"tight_bdt_{signal}",
                # loose_region=f"loose_bdt_{signal}",
                # category_names=self.fit_config[process_group_name].keys(),
                # _exclude=["branches", "branch"])}

    def output(self):
        if self.combine_categories:
            return {
                pgn: {
                    feature.name: self.local_target("results_{}_{}.json".format(
                        feature.name, pgn))
                    for feature in self.features
                } for pgn in self.process_group_names
            }
        else:
            return {
                pgn: {
                    category_name: {
                        feature.name: self.local_target("results_{}_{}_{}.json".format(
                            feature.name, pgn, category_name))
                        for feature in self.features
                    } for category_name in self.fit_config[pgn].keys()
                } for pgn in self.process_group_names
            }


class InspectPlotDQCD(CombineBase, DQCDBaseTask, ProcessGroupNameWrapper):
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
        self.category_names = self.fit_config[self.process_group_name].keys()

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


class FitStudyDQCD(ProcessGroupNameWrapper, DQCDBaseTask, FitBase):

    category_names = (
        "base", # required at first position
        "singlev_cat1", "singlev_cat2", "singlev_cat3",
        "singlev_cat4", "singlev_cat5", "singlev_cat6",
        "multiv_cat1", "multiv_cat2", "multiv_cat3",
        "multiv_cat4", "multiv_cat5", "multiv_cat6",
    )
    # feature_names = ("muonSV_bestchi2_mass_fullrange",)
    feature_names = (
        # "muonSV_bestchi2_mass_fullrange_bdt_0p8",
        # "muonSV_bestchi2_mass_fullrange_bdt_0p9",
        # "muonSV_bestchi2_mass_fullrange_bdt_0p95",
        "muonSV_bestchi2_mass_fullrange_bdt_0p98",
    )
    params = ["integral", "mean", "sigma", "gamma", "chi2"]

    def requires(self):
        reqs = {}
        for process_group_name in self.process_group_names:
            signal = process_group_name[:process_group_name.find("_")]
            # tight_region = f"tight_bdt_{signal}"
            tight_region = law.NO_STR
            # loose_region = f"loose_bdt_{signal}"
            mass_point = self.get_mass_point(process_group_name)
            sigma = mass_point * 0.01
            fit_range = (mass_point - 5 * sigma, mass_point + 5 * sigma)

            reqs[process_group_name] = {}
            for category_name in self.category_names:
                reqs[process_group_name][category_name] = Fit.vreq(
                    self, process_group_name="sig_" + process_group_name, region_name=tight_region,
                    category_name=category_name, x_range=fit_range, method="voigtian",
                    process_name=process_group_name, feature_names=self.feature_names,
                    fit_parameters={"mean": (mass_point, mass_point - 0.1, mass_point + 0.1),
                        "gamma": (0.005,)})
        return reqs

    def output(self):
        out = {}
        for feature_name in self.feature_names:
            out[feature_name] = {}
            out[feature_name]["tables"] = {
                cat: {
                    ext: self.local_target(f"{feature_name}/table_{cat}_{self.fit_config_file}.{ext}")
                    for ext in ["txt", "tex", "json"]
                } for cat in self.category_names
            }
            out[feature_name]["sigma_mass_ratio"] = {
                cat: {
                    ext: self.local_target(f"{feature_name}/sigma_mass_ratio_{cat}_{self.fit_config_file}.{ext}")
                    for ext in ["pdf"]
                } for cat in self.category_names
            }
            for param in self.params:
                if param == "chi2":
                    out[feature_name][param] = self.local_target(f"{feature_name}/{param}/{param}_{self.fit_config_file}.pdf")
                out[feature_name][f"{param}_cat"] = {
                    cat: self.local_target(f"{feature_name}/{param}/{param}_{cat}_{self.fit_config_file}.pdf")
                    for cat in self.category_names
                }
                out[feature_name][f"{param}_cat_ratio"] = {
                    cat: self.local_target(f"{feature_name}/{param}/{param}_{cat}_ratio_{self.fit_config_file}.pdf")
                    for cat in self.category_names
                }
                out[feature_name][f"{param}_cat_wrtbase"] = {
                    cat: self.local_target(f"{feature_name}/{param}/{param}_{cat}_wrtbase_{self.fit_config_file}.pdf")
                    for cat in self.category_names
                }
                if param == "integral":
                    out[feature_name][f"{param}_cat_unc"] = {
                        cat: self.local_target(f"{feature_name}/{param}/{param}_{cat}_rel_unc_{self.fit_config_file}.pdf")
                        for cat in self.category_names
                    }
        return out

    def run(self):
        def round_unc(num):
            if num == 0:
                return num
            exp = 0
            while True:
                if num * 10 ** exp > 1:
                    return round(num, exp + 1)
                exp += 1

        import tabulate
        import math
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt

        inputs = self.input()

        for feature_name in self.feature_names:
            plot = []
            d_param = {cat: {} for cat in self.category_names}
            d_param_ratio = {cat: {} for cat in self.category_names}
            d_param_unc = {cat: {} for cat in self.category_names}
            for icat, cat in enumerate(self.category_names):
                table = []
                outd = {}
                d_param[cat] = {param: {} for param in self.params}
                d_param[cat]["sigma_mass_ratio"] = {}
                d_param_ratio[cat] = {param: {} for param in self.params}
                d_param_unc[cat] = {"integral": {}}
                for pgn in self.process_group_names:
                    mass_point = self.get_mass_point(pgn)
                    ctau = self.get_ctau(pgn)

                    with open(inputs[pgn][cat][feature_name]["json"].path) as f:
                        d = json.load(f)
                    table.append([pgn] + [d[""][param] for param in self.params])
                    outd[pgn] = {param: d[""][param] for param in self.params}
                    for param in self.params:
                        if param == "chi2":
                            if math.isnan(float(d[""]["chi2"])):
                                d_param[cat]["chi2"][(mass_point, ctau)] = ("nan", d[""]["Number of non-zero bins"])
                            else:
                                d_param[cat]["chi2"][(mass_point, ctau)] = (
                                    round(d[""]["chi2"], 2), d[""]["Number of non-zero bins"])
                            if d[""]["chi2"] > 10.5 or math.isnan(float(d[""]["chi2"])):
                                plot.append((icat, -1))
                            else:
                                plot.append((icat, d[""]["chi2"]))
                        else:
                            d_param[cat][param][(mass_point, ctau)] = (
                                round_unc(d[""][param]), round_unc(d[""][param + "_error"])
                            )
                            d_param_ratio[cat][param][(mass_point, ctau)] = round_unc(d[""][param] /
                                d_param["base"][param][(mass_point, ctau)][0])
                            if param == "integral":
                                d_param_unc[cat][param][(mass_point, ctau)] = round_unc(
                                    d[""]["integral_error"] / d[""]["integral"] if d[""]["integral"] != 0
                                    else 0.
                                )
                    d_param[cat]["sigma_mass_ratio"][mass_point, ctau]= (
                        d[""]["sigma"] / mass_point, d[""]["sigma_error"] / mass_point
                    )

                fancy_table = tabulate.tabulate(table, headers=["process"] + self.params)
                with open(create_file_dir(self.output()[feature_name]["tables"][cat]["txt"].path), "w+") as f:
                    f.write(fancy_table)
                fancy_table_tex = tabulate.tabulate(table, headers=["process"] + self.params, tablefmt="latex")
                with open(create_file_dir(self.output()[feature_name]["tables"][cat]["tex"].path), "w+") as f:
                    f.write(fancy_table_tex)
                with open(create_file_dir(self.output()[feature_name]["tables"][cat]["json"].path), "w+") as f:
                    json.dump(outd, f, indent=4)

                # for key, d in zip(["cat", "cat_ratio", "cat_unc"], [d_param, d_param_ratio, d_param_unc]):
                    # for param in self.params:
                        # # if param != "integral" and key in ["cat_ratio", "cat_unc"]:
                        # if param != "integral" and key in ["cat_unc"]:
                            # continue
                        # ax = plt.subplot()
                        # plt.plot([x for (x,y) in d[cat][param].keys()],
                            # [y for (x,y) in d[cat][param].keys()], ".")
                        # for (x, y), z in d[cat][param].items():
                            # if isinstance(z, tuple):
                                # z = z[0]
                            # plt.annotate(z, # this is the text
                                # (x, y), # this is the point to label
                                # textcoords="offset points", # how to position the text
                                # xytext=(0,10), # distance from text to points (x,y)
                                # ha='center',
                                # fontsize=5) # horizontal alignment can be left, right or center
                        # plt.xlabel(f"mass")
                        # plt.ylabel(f"ctau")
                        # plt.yscale('log')
                        # plt.savefig(create_file_dir(self.output()[feature_name][f"{param}_{key}"][cat].path),
                            # bbox_inches='tight')
                        # plt.close()

                # categories w.r.t. base
                for key, d in zip(["cat_wrtbase"], [d_param]):
                    for param in self.params:
                        npoints = len(d[cat][param].items())
                        ax = plt.subplot()

                        # results for the base category
                        for ival, values in enumerate(d["base"][param].values()):
                            plt.fill_between((ival - 0.25, ival + 0.25),
                            (1 - values[1]/values[0] if "nan" not in values else 0),
                            (1 + values[1]/values[0] if "nan" not in values else 0),
                            # color="y", alpha=.5)
                            color="0.8")

                        # results for the category under study
                        y = [(elem[0]/base[0] if elem[0] != 'nan' and base[0] != 'nan' else 0)
                            for elem, base in zip(d[cat][param].values(), d["base"][param].values())]
                        yerr = [(elem[1]/base[0] if elem[1] != 'nan' and base[0] != 'nan' else 0)
                            for elem, base in zip(d[cat][param].values(), d["base"][param].values())]
                        ax.errorbar(range(npoints), y, yerr, fmt='.')

                        ax.set_ybound(0, 2)
                        ax.set_ylim(0, 2)

                        plt.ylabel("%s %s/No categorisation" % (param, cat))
                        plt.xlabel("(mass, ctau)")

                        labels = list(d["base"][param].keys())
                        ax.set_xticks(list(range(len(labels))))
                        if len(labels) <= 4:
                            ax.set_xticklabels(labels)
                        else:
                            ax.set_xticklabels(labels, rotation=60, rotation_mode="anchor", ha="right")

                        plt.savefig(create_file_dir(self.output()[feature_name][f"{param}_{key}"][cat].path),
                            bbox_inches='tight')
                        plt.close()

                    # sigma-mass ratio
                    npoints = len(d[cat]["sigma_mass_ratio"].keys())
                    ax = plt.subplot()
                    for i, (value, error) in enumerate(d[cat]["sigma_mass_ratio"].values()):
                        plt.errorbar(i, value, yerr=error, color="k", marker="o")
                    ax.set_xticks(list(range(npoints)))
                    ax.set_xticklabels(list(d[cat]["sigma_mass_ratio"].keys()), rotation=60,
                        rotation_mode="anchor", ha="right")
                    plt.savefig(create_file_dir(self.output()[feature_name][f"sigma_mass_ratio"][cat]["pdf"].path),
                        bbox_inches='tight')
                    plt.close()

            ax = plt.subplot()
            ax.set_xticks(list(range(len(self.category_names))))
            ax.set_xticklabels(self.category_names, rotation=60, rotation_mode="anchor", ha="right")
            im = plt.hist2d([elem[0] for elem in plot], [elem[1] for elem in plot],
                bins=(len(self.category_names), 12),
                range=[[-0.5, len(self.category_names) - 0.5],[-1.5, 10.5]])
            ax.set_xbound(-0.5, len(self.category_names) - 0.5)
            ax.set_ybound(-1.5, 10.5)
            plt.colorbar(im[3])
            plt.yscale("linear")
            plt.ylabel(f"chi2/ndf")
            plt.savefig(create_file_dir(self.output()[feature_name]["chi2"].path), bbox_inches='tight')


class ReFitDQCD(Fit):
    def requires(self):
        reqs = {
            "histos": super(ReFitDQCD, self).requires(),
            "base_fit": Fit.vreq(self, category_name="base")
        }
        return reqs

    def get_input(self):
        return self.input()["histos"]

    def run(self):
        inp = self.input()["base_fit"]
        for feature in self.features:
            with open(inp[feature.name]["json"].path) as f:
                d = json.load(f)
            self.fit_parameters = dict(self.fit_parameters)
            # self.fit_parameters["sigma"] = (d[""]["sigma"],)

        super(ReFitDQCD, self).run()


class ReFitStudyDQCD(ProcessGroupNameWrapper, DQCDBaseTask, FitBase):

    category_names = (
        "base", # required at first position
        "singlev_cat1", "singlev_cat2", "singlev_cat3",
        "singlev_cat4", "singlev_cat5", "singlev_cat6",
        "multiv_cat1", "multiv_cat2", "multiv_cat3",
        "multiv_cat4", "multiv_cat5", "multiv_cat6",
    )
    # feature_names = ("muonSV_bestchi2_mass_fullrange",)
    feature_names = ("muonSV_bestchi2_mass_fullrange_bdt_0p98",)
    params = ["integral", "mean", "sigma", "gamma", "chi2"]

    def requires(self):
        reqs = {"old": {}, "new": {}}
        for process_group_name in self.process_group_names:
            signal = process_group_name[:process_group_name.find("_")]
            # tight_region = f"tight_bdt_{signal}"
            tight_region = law.NO_STR
            # loose_region = f"loose_bdt_{signal}"
            mass_point = self.get_mass_point(process_group_name)
            sigma = mass_point * 0.01
            fit_range = (mass_point - 5 * sigma, mass_point + 5 * sigma)

            reqs["old"][process_group_name] = {}
            reqs["new"][process_group_name] = {}
            for category_name in self.category_names:
                reqs["new"][process_group_name][category_name] = ReFitDQCD.vreq(
                    self, process_group_name="sig_" + process_group_name, region_name=tight_region,
                    category_name=category_name, x_range=fit_range, method="voigtian",
                    process_name=process_group_name, feature_names=self.feature_names,
                    fit_parameters={"mean": (mass_point, mass_point - 0.1, mass_point + 0.1),
                        "gamma": (0.005,)})
                reqs["old"][process_group_name][category_name] = Fit.vreq(
                    self, process_group_name="sig_" + process_group_name, region_name=tight_region,
                    category_name=category_name, x_range=fit_range, method="voigtian",
                    process_name=process_group_name, feature_names=self.feature_names,
                    fit_parameters={"mean": (mass_point, mass_point - 0.1, mass_point + 0.1),
                        "gamma": (0.005,)})
        return reqs

    def output(self):
        return {
            "percat": {
                cat: self.local_target(f"{self.feature_names[0]}_{cat}_{self.fit_config_file}.pdf")
                for cat in self.category_names
            },
            "summary": self.local_target(f"{self.feature_names[0]}_{self.fit_config_file}.txt")
        }

    def run(self):
        import tabulate
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt

        def round_unc(num):
            if math.isnan(num):
                return num
            if num == 0:
                return num
            exp = 0
            while True:
                if num * 10 ** exp > 1:
                    return round(num, exp + 1)
                exp += 1

        inp = self.input()
        chi2_old = {}
        chi2_new = {}
        for cat in self.category_names:
            chi2_old[cat] = {}
            chi2_new[cat] = {}
            for pgn in self.process_group_names:
                with open(inp["old"][pgn][cat][self.feature_names[0]]["json"].path) as f:
                    d = json.load(f)
                chi2_old[cat][pgn] = d[""]["chi2"]
                with open(inp["new"][pgn][cat][self.feature_names[0]]["json"].path) as f:
                    d = json.load(f)
                chi2_new[cat][pgn] = d[""]["chi2"]

            npoints = len(self.process_group_names)
            ax = plt.subplot()
            plt.plot(list(range(npoints)), chi2_old[cat].values(), color="b", label="Categ-custom fit")
            plt.plot(list(range(npoints)), chi2_new[cat].values(), color="r", label="No-categ fit")

            plt.legend(title=cat)
            plt.xlabel("(mass, ctau)")
            plt.ylabel("$\chi^2$")

            labels = list(chi2_old[cat].keys())
            ax.set_xticks(list(range(len(labels))))
            if len(labels) <= 4:
                ax.set_xticklabels(labels)
            else:
                ax.set_xticklabels(labels, rotation=60, rotation_mode="anchor", ha="right")

            plt.savefig(create_file_dir(self.output()["percat"][cat].path), bbox_inches='tight')
            plt.close()

        table = []
        for pgn in self.process_group_names:
            table.append([pgn] + [str((round_unc(chi2_old[cat][pgn]), round_unc(chi2_new[cat][pgn])))
                for cat in self.category_names])
        table_txt = tabulate.tabulate(table, headers=[""] + list(self.category_names))
        with open(create_file_dir(self.output()["summary"].path), "w+") as f:
            f.write(table_txt)


# class CompareReFitDQCD(ProcessGroupNameWrapper, CombineDatacardsDQCD):
class CompareReFitDQCD(ProcessGroupNameWrapper, CombineCategoriesTask):
    default_categories = [
        "singlev_cat1", "singlev_cat2", "singlev_cat3",
        "singlev_cat4", "singlev_cat5", "singlev_cat6",
        "multiv_cat1", "multiv_cat2", "multiv_cat3",
        "multiv_cat4", "multiv_cat5", "multiv_cat6",
    ]
    keys = ["2.5", "16.0", "50.0", "84.0", "97.5"]

    def requires(self):
        return {
            "no_refit": {
                # "cat": {
                    # pgn: ScanCombineDQCD.vreq(self, combine_categories=False,
                        # process_group_names=[pgn], use_refit=False, _exclude=["branches"])
                    # for pgn in self.process_group_names
                # },
                "combined": ScanCombineDQCD.vreq(self, combine_categories=True,
                    use_refit=False, _exclude=["branches"]),
            },
            "refit": {
                # "cat": {
                    # pgn: ScanCombineDQCD.vreq(self, combine_categories=False,
                        # process_group_names=[pgn], use_refit=True, _exclude=["branches"])
                    # for pgn in self.process_group_names
                # },
                "combined": ScanCombineDQCD.vreq(self, combine_categories=True,
                    use_refit=True, _exclude=["branches"]),
            }
        }

    def output(self):
        return {
            feature.name: {
                f"{ext}_{key}": self.local_target("plot__{}__{}_{}.{}".format(
                    feature.name, self.fit_config_file, key, ext))
                for ext, key in itertools.product(["txt", "pdf"], self.keys)
            }
            for feature in self.features
        }

    def run(self):
        import tabulate
        inputs = self.input()

        for feature in self.features:
            tables = {key: [] for key in self.keys}
            for ip, process_group_name in enumerate(self.process_group_names):
                lines = {key: [process_group_name] for key in self.keys}
                # for category_name in self.default_categories:
                    # try:
                        # ic = list(self.fit_config[process_group_name].keys()).index(category_name)
                    # except ValueError:
                        # for key in self.keys:
                            # lines[key].append(-1)
                            # continue
                    # with open(inputs["no_refit"]["cat"][process_group_name]["collection"].targets[ic][feature.name].path) as f:
                        # val = json.load(f)
                    # with open(inputs["refit"]["cat"][process_group_name]["collection"].targets[ic][feature.name].path) as f:
                        # val_refit = json.load(f)
                    # for key in self.keys:
                        # try:
                            # lines[key].append(val_refit[key] / val[key])
                        # except ValueError:
                            # lines[key].append(-1)
                with open(inputs["no_refit"]["combined"]["collection"].targets[ip][feature.name].path) as f:
                    val = json.load(f)
                with open(inputs["refit"]["combined"]["collection"].targets[ip][feature.name].path) as f:
                    val_refit = json.load(f)
                for key in self.keys:
                    try:
                        lines[key].append(val_refit[key] / val[key])
                    except ValueError:
                        lines[key].append(-1)
                    tables[key].append(lines[key])

        for key in self.keys:
            # txt = tabulate.tabulate(tables[key], headers=self.default_categories + ["Combined"])
            txt = tabulate.tabulate(tables[key], headers=["Combined"])
            with open(create_file_dir(self.output()[feature.name]["txt_" + key].path), "w+") as f:
                f.write(txt)


# class InterpolationTestDQCD(ProcessGroupNameWrapper, CombineDatacardsDQCD):
class InterpolationTestDQCD(ProcessGroupNameWrapper, CombineCategoriesTask):
    # default_categories = [
        # "singlev_cat1", "singlev_cat2", "singlev_cat3",
        # "singlev_cat4", "singlev_cat5", "singlev_cat6",
        # "multiv_cat1", "multiv_cat2", "multiv_cat3",
        # "multiv_cat4", "multiv_cat5", "multiv_cat6",
    # ]
    default_categories = [
        "singlev_cat3", "multiv_cat3"
    ]

    def __init__(self, *args, **kwargs):
        super(InterpolationTestDQCD, self).__init__(*args, **kwargs)
        if len(self.category_names) == 0:
            self.category_names = self.default_categories

    def requires(self):
        reqs = {}
        for process_group_name in self.process_group_names:
            signal = process_group_name[:process_group_name.find("_")]
            tight_region = f"tight_bdt_{signal}"
            mass_point = self.get_mass_point(process_group_name)
            sigma = mass_point * 0.01
            fit_range = (mass_point - 5 * sigma, mass_point + 5 * sigma)

            reqs[process_group_name] = {}
            for category_name in self.category_names:
                reqs[process_group_name][category_name] = ReFitDQCD.vreq(
                    self, process_group_name="sig_" + process_group_name, region_name=tight_region,
                    category_name=category_name, x_range=fit_range, method="voigtian",
                    process_name=process_group_name, feature_names=self.feature_names,
                    fit_parameters={"mean": (mass_point, mass_point - 0.1, mass_point + 0.1),
                        "gamma": (0.005,)})
        return reqs

    def output(self):
        ctaus = []
        mass_points = []
        for pgn in self.process_group_names:
            mass_points.append(self.get_mass_point(pgn))
            ctaus.append(pgn.split("_ctau_")[1].replace("p", "."))
            try:
                ctaus[-1] = float(ctaus[-1])
            except ValueError:  # vector portal has _xiO_1_xiL_1 after ctau, need to remove it
                ctaus[-1] = float(ctaus[-1].split("_")[0])
        mass_points = set(mass_points)
        ctaus = set(ctaus)

        return {
            feature.name: {
                cat: {
                    "values": self.local_target(f"values_{feature.name}_{cat}.pdf"),
                    "interp": self.local_target(f"interp_{feature.name}_{cat}.pdf"),
                    "interp_model": self.local_target(f"interp_{feature.name}_{cat}_model.pkl"),
                    "interp2d_model": self.local_target(f"interp2d_{feature.name}_{cat}_model.pkl"),
                    # "interp_clough": self.local_target(f"clough_{feature.name}_{cat}.pdf"),
                    "interp2d": self.local_target(f"interp2d_{feature.name}_{cat}.pdf"),
                    "ratio": self.local_target(f"ratio_{feature.name}_{cat}.pdf"),
                    "ratio2d": self.local_target(f"ratio2d_{feature.name}_{cat}.pdf"),
                    # "dum": self.local_target(f"dum_{feature.name}_{cat}.pdf"),

                    "interp_test": {
                        (m, ctau): self.local_target(f"interp_test/{feature.name}_{cat}_{m}_{ctau}.pdf")
                        for (m, ctau) in itertools.product(mass_points, ctaus)
                        if not (m in [min(mass_points), max(mass_points)] and \
                            ctau in [min(ctaus), max(ctaus)])
                    },
                    "interp2d_test": {
                        (m, ctau): self.local_target(f"interp2d_test/{feature.name}_{cat}_{m}_{ctau}.pdf")
                        for (m, ctau) in itertools.product(mass_points, ctaus)
                        if not (m in [min(mass_points), max(mass_points)] and \
                            ctau in [min(ctaus), max(ctaus)])
                    },
                    "interp_m": {
                        m: self.local_target(f"interp_per_mass/{feature.name}_{cat}_{m}.pdf")
                        for m in mass_points
                    },
                    # "interp_ctau": {
                        # ctau: self.local_target(f"interp_per_ctau/{feature.name}_{cat}_{ctau}.pdf")
                        # for ctau in ctaus
                    # },
                    "interp2d_m": {
                        m: self.local_target(f"interp2d_per_mass/{feature.name}_{cat}_{m}.pdf")
                        for m in mass_points
                    },
                    # "interp2d_ctau": {
                        # ctau: self.local_target(f"interp2d_per_ctau/{feature.name}_{cat}_{ctau}.pdf")
                        # for ctau in ctaus
                    # }
                } for cat in self.category_names
            } for feature in self.features
        }

    def load_inputs(self, feature, cat):
        values = {}
        for pgn in self.process_group_names:
            with open(self.input()[pgn][cat][feature.name]["json"].path) as f:
                d = json.load(f)
            mass_point = self.get_mass_point(pgn)
            ctau = pgn.split("_ctau_")[1].replace("p", ".")
            try:
                ctau = float(ctau)
            except ValueError:  # vector portal has _xiO_1_xiL_1 after ctau, need to remove it
                ctau = float(ctau.split("_")[0])
            values[(mass_point, ctau)] = (d[""]["integral"], d[""]["integral_error"])
        return values

    def run(self):
        from scipy.interpolate import LinearNDInterpolator
        from scipy.interpolate import CloughTocher2DInterpolator
        # from scipy.interpolate import interp2d as Interpolator2D
        from scipy.interpolate import SmoothBivariateSpline as Interpolator2D
        import numpy as np
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        import pickle

        for feature in self.features:
            for cat in self.category_names:
                values = self.load_inputs(feature, cat)
                mass_points = set([elem[0] for elem in values.keys()])
                ctaus = set([elem[1] for elem in values.keys()])

                mass_points = sorted(mass_points)
                ctaus = sorted(ctaus)
                grid_x, grid_y = np.meshgrid(mass_points, ctaus)

                @np.vectorize
                def func(x, y):
                    return values[(x, y)][0]

                # train with the whole sample
                X = np.array([(m, ctau) for (m, ctau) in itertools.product(mass_points, ctaus)])
                Y = np.array([values[elem][0] for elem in itertools.product(mass_points, ctaus)])
                interp = LinearNDInterpolator(X, Y)
                # interp2d = Interpolator2D(X[:, 0], X[:, 1], Y, kind="linear")
                # interp2d = Interpolator2D(X[:, 0], X[:, 1], Y, s=0.0)
                interp2d = CloughTocher2DInterpolator(X, np.array([values[elem]
                    for elem in itertools.product(mass_points, ctaus)]))

                ctau_range = (min(ctaus), max(ctaus))
                m_range = (min(mass_points), max(mass_points))
                n_points = 100
                for name, method in [("interp", interp), ("interp2d", interp2d)]:
                    for m in mass_points:
                        ax = plt.subplot()
                        X_to_plot = np.array([e[1] for e in values.keys() if e[0] == m])
                        Y_to_plot = np.array([v[0] for e, v in values.items() if e[0] == m])
                        plt.scatter(X_to_plot, Y_to_plot, label="Observations")
                        x_m = np.geomspace(start=ctau_range[0], stop=ctau_range[1], num=n_points)
                        X_m = np.array(list(itertools.product([m], x_m)))
                        # if name == "interp":
                        X_1, X_2 = np.meshgrid(X_m[:, 0], X_m[:, 1])
                        prediction = method(X_1, X_2)
                        prediction = prediction[:, 1]
                        if name == "interp2d":
                            prediction = prediction[:, 0]
                            # print(prediction)
                        # else:
                            # prediction = method(np.array([m]), x_m)
                            # prediction = prediction[0, :]
                            # print(prediction)

                        plt.plot(X_m[:, 1], prediction, label="Mean prediction")
                        plt.legend(title=f"Mass = {m} GeV")
                        plt.xscale('log')
                        plt.savefig(create_file_dir(self.output()[feature.name][cat]["%s_m" % name][m].path),
                            bbox_inches='tight')
                        plt.close()
                    with open(create_file_dir(
                            self.output()[feature.name][cat]["%s_model" % name].path), 'wb') as f:
                        pickle.dump(method, f)

                res_interp = {}
                res_interp2d = {}
                # res_interp_clough = {}

                for m_skip, ctau_skip in itertools.product(mass_points, ctaus):
                    # avoid skipping the corners of the grid
                    if m_skip in [min(mass_points), max(mass_points)] and \
                            ctau_skip in [min(ctaus), max(ctaus)]:
                        res_interp[(m_skip, ctau_skip)] = -999
                        res_interp2d[(m_skip, ctau_skip)] = -999
                        # res_interp_clough[(m_skip, ctau_skip)] = -999
                        continue
                    points = [(m, ctau)
                        for (m, ctau) in itertools.product(mass_points, ctaus)
                        if not(m == m_skip and ctau == ctau_skip)]
                    results = [values[elem][0] for elem in points]
                    points = np.array(points)
                    results = np.array(results)

                    interp = LinearNDInterpolator(points, results)
                    # interp2d = Interpolator2D(points[:, 0], points[:, 1], results, kind="linear")
                    # interp2d = Interpolator2D(points[:, 0], points[:, 1], results, s=0.0)
                    interp2d = CloughTocher2DInterpolator(points, results)
                    res_interp[(m_skip, ctau_skip)] = interp(*np.meshgrid([m_skip], [ctau_skip]))
                    res_interp2d[(m_skip, ctau_skip)] = interp2d(*np.meshgrid([m_skip], [ctau_skip]))[0][0]
                    # print(res_interp[(m_skip, ctau_skip)], values[(m_skip, ctau_skip)])
                    # print(res_interp2d[(m_skip, ctau_skip)], values[(m_skip, ctau_skip)])
                    # res_interp2d[(m_skip, ctau_skip)] = interp2d([m_skip], [ctau_skip])
                    # res_interp_clough[(m_skip, ctau_skip)] = interp_clough(*np.meshgrid([m_skip], [ctau_skip]))

                    for (name, z) in zip(
                            ["interp_test", "interp2d_test"],
                            # [interp(grid_x, grid_y), interp2d(mass_points, ctaus)]):
                            [interp(grid_x, grid_y), interp2d(grid_x, grid_y)]):
                            # [interp(grid_x, grid_y), interp2d(grid_x, grid_y)[:, 0]]):
                        ax = plt.subplot()
                        if "ratio" not in name:
                            plt.pcolor(grid_x, grid_y, z, shading='auto', vmin=0, vmax=100)
                        else:
                            plt.pcolor(grid_x, grid_y, z, shading='auto', vmin=0, vmax=2)
                        for ix, iy in itertools.product(range(grid_x.shape[0]), range(grid_x.shape[1])):
                            plt.text(grid_x[ix, iy], grid_y[ix, iy],
                                '%.4f->%.4f' % (
                                    values[(grid_x[ix, iy], grid_y[ix, iy])][0], z[ix, iy]),
                                horizontalalignment='center',
                                verticalalignment='center',
                                fontsize=5
                            )
                        plt.colorbar()
                        ax.set_ybound(0.05, 120)
                        ax.set_ylim(0.05, 120)
                        # ax.set_zbound(0, 100)
                        # ax.set_zlim(0, 100)
                        plt.yscale('log')
                        plt.savefig(create_file_dir(
                                self.output()[feature.name][cat][name][(m_skip, ctau_skip)].path),
                            bbox_inches='tight')
                        plt.close()

                # from pprint import pprint
                # pprint(diffs)
                # pprint(diffs_clough)

                grid_z = func(grid_x, grid_y)
                @np.vectorize
                def func_interp(x, y):
                    return res_interp[(x, y)]
                grid_z_interp = func_interp(grid_x, grid_y)
                @np.vectorize
                def func_interp2d(x, y):
                    return res_interp2d[(x, y)]
                grid_z_interp2d = func_interp2d(grid_x, grid_y)

                ratio_z_interp = (func_interp(grid_x, grid_y) - func(grid_x, grid_y)) / func_interp(grid_x, grid_y)
                ratio_z_interp2d = (func_interp2d(grid_x, grid_y) - func(grid_x, grid_y)) / func_interp2d(grid_x, grid_y)

                # @np.vectorize
                # def func_clough(x, y):
                    # return res_interp_clough[(x, y)]
                # grid_z_clough = func_clough(grid_x, grid_y)

                # print(grid_x)
                # print(func(grid_x, grid_y))

                for (name, z) in zip(
                        ["values", "interp", "interp2d",
                            # "interp_clough", "ratio", "ratio2d"],
                            "ratio", "ratio2d"],
                        [grid_z, grid_z_interp, grid_z_interp2d,
                            # grid_z_clough, ratio_z_interp, ratio_z_interp2d]):
                            ratio_z_interp, ratio_z_interp2d]):
                    ax = plt.subplot()
                    if "ratio" not in name:
                        plt.pcolor(grid_x, grid_y, z, shading='auto', vmin=0, vmax=100)
                    else:
                        plt.pcolor(grid_x, grid_y, z, shading='auto', vmin=0, vmax=2)
                    for ix, iy in itertools.product(range(grid_x.shape[0]), range(grid_x.shape[1])):
                        plt.text(grid_x[ix, iy], grid_y[ix, iy],
                            '%.4f->%.4f' % (
                                values[(grid_x[ix, iy], grid_y[ix, iy])][0], z[ix, iy]),
                            horizontalalignment='center',
                            verticalalignment='center',
                            fontsize=5
                        )
                    plt.colorbar()
                    ax.set_ybound(0.05, 120)
                    ax.set_ylim(0.05, 120)
                    # ax.set_zbound(0, 100)
                    # ax.set_zlim(0, 100)
                    plt.yscale('log')
                    plt.savefig(create_file_dir(self.output()[feature.name][cat][name].path),
                        bbox_inches='tight')
                    plt.close()


class InterpolationGPDQCD(InterpolationTestDQCD):
    # default_categories = [
        # "singlev_cat1", "singlev_cat2", "singlev_cat3",
        # "singlev_cat4", "singlev_cat5", "singlev_cat6",
        # "multiv_cat1", "multiv_cat2", "multiv_cat3",
        # "multiv_cat4", "multiv_cat5", "multiv_cat6",
    # ]
    default_categories = ["singlev_cat3"]
    def output(self):
        ctaus = []
        mass_points = []
        for pgn in self.process_group_names:
            mass_points.append(self.get_mass_point(pgn))
            ctaus.append(pgn.split("_ctau_")[1].replace("p", "."))
            try:
                ctaus[-1] = float(ctaus[-1])
            except ValueError:  # vector portal has _xiO_1_xiL_1 after ctau, need to remove it
                ctaus[-1] = float(ctaus[-1].split("_")[0])
        mass_points = set(mass_points)
        ctaus = set(ctaus)

        return {
            feature.name: {
                cat: {
                    "values": self.local_target(f"values_{feature.name}_{cat}.pdf"),
                    "interp": self.local_target(f"interp_{feature.name}_{cat}.pdf"),
                    "interp1d": self.local_target(f"interp1d_{feature.name}_{cat}.pdf"),
                    "m": {
                        m: self.local_target(f"interp_per_mass/{feature.name}_{cat}_{m}.pdf")
                        for m in mass_points
                    },
                    "ctau": {
                        ctau: self.local_target(f"interp_per_ctau/{feature.name}_{cat}_{ctau}.pdf")
                        for ctau in ctaus
                    }
                } for cat in self.category_names
            } for feature in self.features
        }

    def run(self):
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, RationalQuadratic, DotProduct, Exponentiation, Matern
        import numpy as np
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt

        kernel = 1 * RBF(length_scale=1.0, length_scale_bounds=(1e-2, 1e2))
        # kernel = 1 * RBF(length_scale=1.0)
        # kernel = 1 * RBF(length_scale=1.4)
        # kernel = 1 * Matern()
        # kernel = 1 * RationalQuadratic(length_scale=100)
        # kernel = Exponentiation(DotProduct(), exponent=4)
        # gaussian_process = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=9)
        gaussian_process = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=100)

        for feature in self.features:
            for cat in self.category_names:
                values = self.load_inputs(feature, cat)
                mass_points = set([elem[0] for elem in values.keys()])
                ctaus = set([elem[1] for elem in values.keys()])

                grid_x, grid_y = np.meshgrid(sorted(mass_points), sorted(ctaus))

                X = np.array(list(values.keys()))
                Y = np.array(list([e[0] for e in values.values()]))

                # train with the whole sample
                gaussian_process.fit(X, Y)
                ctau_range = (min(ctaus), max(ctaus))
                m_range = (min(mass_points), max(mass_points))
                n_points = 100
                for m in mass_points:
                    ax = plt.subplot()
                    X_to_plot = np.array([e[1] for e in values.keys() if e[0] == m])
                    Y_to_plot = np.array([v[0] for e, v in values.items() if e[0] == m])
                    plt.scatter(X_to_plot, Y_to_plot, label="Observations")
                    x_m = np.geomspace(start=ctau_range[0], stop=ctau_range[1], num=n_points)
                    X_m = np.array(list(itertools.product([m], x_m)))
                    mean_prediction, std_prediction = gaussian_process.predict(X_m, return_std=True)
                    plt.plot(X_m[:, 1], mean_prediction, label="Mean prediction")
                    plt.fill_between(
                        x_m,
                        mean_prediction - 1.96 * std_prediction,
                        mean_prediction + 1.96 * std_prediction,
                        alpha=0.5,
                        label=r"95% confidence interval",
                    )
                    plt.legend(title=f"Mass = {m} GeV")
                    plt.xscale('log')
                    plt.savefig(create_file_dir(self.output()[feature.name][cat]["m"][m].path),
                        bbox_inches='tight')
                    plt.close()

                output = {}
                for i, (m_skip, ctau_skip) in enumerate(X):
                    # avoid skipping the corners of the grid
                    if m_skip in [min(mass_points), max(mass_points)] and \
                            ctau_skip in [min(ctaus), max(ctaus)]:
                        output[(m_skip, ctau_skip)] = (1, 0)
                        continue
                    # print(X)

                    X_train = np.array([e for e in values.keys() if e != (m_skip, ctau_skip)])
                    Y_train = np.array([v[0] for e, v in values.items() if e != (m_skip, ctau_skip)])

                    # X_train = np.ma.array(X, mask=False)
                    # X_train.mask[i]
                    # Y_train = np.ma.array(Y, mask=False)
                    # Y_train.mask[i]

                    gaussian_process.fit(X_train, Y_train)
                    output[(m_skip, ctau_skip)] = gaussian_process.predict(np.array([X[i]]),
                        return_std=True)
                    res = gaussian_process.predict(X, return_std=True)

                @np.vectorize
                def func_interp(x, y):
                    return output[(x, y)][0]
                @np.vectorize
                def func_interp_error(x, y):
                    return output[(x, y)][1]
                grid_z = func_interp(grid_x, grid_y)
                grid_z_eror = func_interp_error(grid_x, grid_y)

                ax = plt.subplot()
                plt.pcolor(grid_x, grid_y, grid_z, shading='auto', vmin=0, vmax=100)
                for ix, iy in itertools.product(range(grid_x.shape[0]), range(grid_x.shape[1])):
                    plt.text(grid_x[ix, iy], grid_y[ix, iy], '%.4f->%.4f' % (
                            values[(grid_x[ix, iy], grid_y[ix, iy])][0], grid_z[ix, iy]),
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=5
                    )
                plt.colorbar()
                ax.set_ybound(0.05, 120)
                ax.set_ylim(0.05, 120)
                # ax.set_zbound(0, 100)
                # ax.set_zlim(0, 100)
                plt.yscale('log')
                plt.savefig(create_file_dir(self.output()[feature.name][cat]["interp"].path),
                    bbox_inches='tight')
                plt.close()

                ax = plt.subplot()

                keys = [(m, ctau) for (m, ctau) in itertools.product(mass_points, ctaus)]
                for i, (m, ctau) in enumerate(keys):
                    plt.fill_between((i - 0.25, i + 0.25),
                        output[(m, ctau)][0] + 1.96 * output[(m, ctau)][1],
                        output[(m, ctau)][0] - 1.96 * output[(m, ctau)][1],
                        color="g",
                    )
                    plt.errorbar(i, values[(m, ctau)][0], yerr=values[(m, ctau)][1], color="k", marker="o")
                ax.set_xticks(list(range(len(keys))))
                ax.set_xticklabels(keys, rotation=60, rotation_mode="anchor", ha="right")
                plt.savefig(create_file_dir(self.output()[feature.name][cat]["interp1d"].path),
                    bbox_inches='tight')
                plt.close('all')


class InspectReFitSystDQCD(InspectFitSyst):
    def requires(self):
        """
        Needs as input the json file provided by the Fit task
        """
        return ReFitDQCD.vreq(self)


class SummariseSystResultsDQCD(ProcessGroupNameWrapper, CombineCategoriesTask):
    # default_categories = [
        # "singlev_cat1", "singlev_cat2", "singlev_cat3",
        # "singlev_cat4", "singlev_cat5", "singlev_cat6",
        # "multiv_cat1", "multiv_cat2", "multiv_cat3",
        # "multiv_cat4", "multiv_cat5", "multiv_cat6",
    # ]
    default_categories = [
        "singlev_cat3", "multiv_cat3"
    ]
    params = ["sigma", "mean", "integral"]

    def __init__(self, *args, **kwargs):
        super(SummariseSystResultsDQCD, self).__init__(*args, **kwargs)
        if len(self.category_names) == 0:
            self.category_names = self.default_categories
        ctaus = [self.get_ctau(pgn) for pgn in self.process_group_names]
        self.ctaus = list(set(ctaus)) + ["incl"]

    def requires(self):
        reqs = {}
        for process_group_name in self.process_group_names:
            signal = process_group_name[:process_group_name.find("_")]
            tight_region = f"tight_bdt_{signal}"
            mass_point = self.get_mass_point(process_group_name)
            sigma = mass_point * 0.01
            fit_range = (mass_point - 5 * sigma, mass_point + 5 * sigma)

            reqs[process_group_name] = {}
            for category_name in self.category_names:
                reqs[process_group_name][category_name] = InspectReFitSystDQCD.vreq(
                    self, process_group_name="sig_" + process_group_name, region_name=tight_region,
                    category_name=category_name, x_range=fit_range, method="voigtian",
                    process_name=process_group_name, feature_names=self.feature_names,
                    fit_parameters={"mean": (mass_point, mass_point - 0.1, mass_point + 0.1),
                        "gamma": (0.005,)})
        return reqs

    def output(self):
        return {
            feature.name: {
                cat: {
                    ctau: {
                        param: {
                            syst: {
                                ext: self.local_target(
                                    f"{feature.name}_{cat}_{syst}_{param}"
                                        f"_{str(ctau).replace('.', 'p')}.{ext}")
                                for ext in ["pdf", "txt"]
                            } for syst in self.get_unique_systs(
                                self.get_systs(feature, True,
                                    category=self.config.categories.get(cat))
                                + self.config.get_weights_systematics(
                                    self.config.weights[cat], True)
                            )
                        } for param in self.params
                    } for ctau in self.ctaus
                } for cat in self.category_names
            } for feature in self.features
        }

    def run(self):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        plt.rcParams['text.usetex'] = True

        for feature in self.features:
            for cat in self.category_names:
                systs = self.get_unique_systs(
                    self.get_systs(feature, True,
                        category=self.config.categories.get(cat))
                    + self.config.get_weights_systematics(self.config.weights[cat], True))
                results = dict([(syst, {}) for syst in systs])
                for pgn in self.process_group_names:
                    ctau = self.get_ctau(pgn)
                    path = self.input()[pgn][cat][feature.name]["json"].path
                    with open(path) as f:
                        d = json.load(f)
                    for syst in systs:
                        if "incl" not in results[syst]:
                            results[syst]["incl"] = dict([(param, []) for param in self.params])
                        if ctau not in results[syst]:
                            results[syst][ctau] = dict([(param, []) for param in self.params])
                        for param in self.params:
                            results[syst][ctau][param].append(abs(d[syst][param]["up"]))
                            results[syst][ctau][param].append(abs(d[syst][param]["down"]))
                            results[syst]["incl"][param].append(abs(d[syst][param]["up"]))
                            results[syst]["incl"][param].append(abs(d[syst][param]["down"]))
                # Create histos
                for syst in systs:
                    for ctau in self.ctaus:
                        for param in self.params:
                            ax = plt.subplot()
                            plt.hist(results[syst][ctau][param], bins=100)

                            plt.xlabel(f"Deviation in {param}")
                            plt.ylabel(f"Number of samples")
                            plt.text(0, 1.01, r"\textbf{CMS} \textit{Private Work}",
                                transform=ax.transAxes)
                            plt.text(1., 1.01, r"%s Simulation, %s fb${}^{-1}$" % (
                                self.config.year, self.config.lumi_fb),
                                transform=ax.transAxes, ha="right")
                            inner_text = "\n".join([cat, syst])
                            plt.text(0.5, 0.90, inner_text, transform=ax.transAxes, ha="center")

                            plt.savefig(create_file_dir(
                                    self.output()[feature.name][cat][ctau][param][syst]["pdf"].path),
                                bbox_inches='tight')

                            plt.close('all')


# law run BDTRatioTest --version prod_1007_inttest  --config-name ul_2018 --workers 100
#--MergeCategorizationStats-version prod_1201_bdt0p45
#--MergeCategorization-version prod_1302_nojet_nosel --PrePlot-workflow htcondor
#--PrePlot-preplot-modules-file chi2_nobdt --PrePlot-transfer-logs --PrePlot-allow-redefinition
from cmt.base_tasks.plotting import BasePlotTask
class BDTRatioTest(BasePlotTask):
    category_names=["base",
        "singlev_cat1", "singlev_cat2", "singlev_cat3",
        "singlev_cat4", "singlev_cat5", "singlev_cat6",
        "multiv_cat1", "multiv_cat2", "multiv_cat3",
        "multiv_cat4", "multiv_cat5", "multiv_cat6",
    ]
    region_names=["vvloose_bdt_scenarioA", "vloose_bdt_scenarioA", "loose_bdt_scenarioA", "medium_bdt_scenarioA"]
    feature_names=("muonSV_bestchi2_mass_fullrange_fewer_bins", "bdt_scenarioA")

    def requires(self):
        return {
            cat: {
                region: FeaturePlot.vreq(self, category_name=cat, region_name=region,
                    save_yields=True, dataset_names="data_2018d_bph1_1fb", process_group_name="data",
                    feature_names=self.feature_names, hide_data=False, stack=True)
                for region in self.region_names
            } for cat in self.category_names
        }

    def output(self):
        return {
            region: self.local_target(f"ratio__{region}.pdf")
            for region in self.region_names[1:]
        }

    def run(self):
        from tabulate import tabulate
        import math
        from matplotlib import pyplot as plt

        inp = self.input()
        results = {}
        for cat in self.category_names:
            results[cat] = {}
            for region in self.region_names:
                with open(inp[cat][region]["yields"].targets[self.feature_names[0]].path) as f:  # FIXME
                    results[cat][region] = json.load(f)

        for iregion in range(1, len(self.region_names)):

            this_reg_base = results["base"][self.region_names[iregion]]["data"]["Total yield"]
            this_reg_error_base = results["base"][self.region_names[iregion]]["data"]["Total yield error"]
            prev_reg_base = results["base"][self.region_names[iregion - 1]]["data"]["Total yield"]
            prev_reg_error_base = results["base"][self.region_names[iregion - 1]]["data"]["Total yield error"]

            ratio_base = this_reg_base / prev_reg_base if prev_reg_base != 0 else 0
            error_ratio_base = ratio_base * math.sqrt((this_reg_error_base / this_reg_base)**2 +
                (prev_reg_error_base / prev_reg_base)**2)

            values = []
            errors = []
            for cat in self.category_names[1:]:
                this_reg = results[cat][self.region_names[iregion]]["data"]["Total yield"]
                this_reg_error = results[cat][self.region_names[iregion]]["data"]["Total yield error"]
                prev_reg = results[cat][self.region_names[iregion - 1]]["data"]["Total yield"]
                prev_reg_error = results[cat][self.region_names[iregion - 1]]["data"]["Total yield error"]

                ratio = this_reg / prev_reg if prev_reg != 0 else 0
                values.append(ratio / ratio_base)
                errors.append(
                    0 if this_reg == 0 or prev_reg == 0
                    else (ratio / ratio_base) * math.sqrt(
                        (this_reg_error / this_reg) ** 2 + (prev_reg_error / prev_reg) ** 2)
                )

            ax = plt.subplot()
            ax.errorbar(range(len(self.category_names) - 1), values, errors, fmt='.')
            plt.fill_between(
                range(len(self.category_names) - 1),
                (ratio_base - error_ratio_base) / ratio_base,
                (ratio_base + error_ratio_base) / ratio_base,
                alpha=0.5
            )
            plt.ylabel(f"{self.region_names[iregion]}/{self.region_names[iregion - 1]}")
            ax.set_xticks(list(range(len(self.category_names) - 1)))
            ax.set_xticklabels(self.category_names[1:], rotation=60, rotation_mode="anchor", ha="right")
            ax.set_ybound(0, 2)
            ax.set_ylim(0, 2)
            plt.savefig(create_file_dir(self.output()[self.region_names[iregion]].path),
                bbox_inches='tight')
            plt.close()
