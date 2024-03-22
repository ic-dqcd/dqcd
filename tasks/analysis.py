import json
import luigi
import law
from copy import deepcopy as copy

from analysis_tools.utils import create_file_dir, import_root

from cmt.base_tasks.base import DatasetWrapperTask
from cmt.base_tasks.plotting import FeaturePlot
from cmt.base_tasks.analysis import (
    FitBase, CombineBase, CombineCategoriesTask, Fit, InspectFitSyst, CreateDatacards,
    CombineDatacards, CreateWorkspace, RunCombine, PullsAndImpacts, MergePullsAndImpacts,
    PlotPullsAndImpacts, ValidateDatacards
)

class DQCDBaseTask(DatasetWrapperTask):
    tight_region = luigi.Parameter(default="tight_bdt", description="region_name with the "
        "tighter bdt cut, default: tight_bdt")
    loose_region = luigi.Parameter(default="loose_bdt", description="region_name with the "
        "looser bdt cut, default: loose_bdt")
    mass_point = luigi.FloatParameter(default=1.33, description="mass point to be used to "
        "define the fit ranges and blinded regions")

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
                new_models[signal_process]["x_range"] = str(self.fit_range)[1:-1]
                if "fit_parameters" not in new_models[signal_process]:
                    new_models[signal_process]["fit_parameters"] = {}
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


class CreateDatacardsDQCD(CreateDatacards, DQCDBaseTask):

    calibration_feature_name = "muonSV_bestchi2_mass_fullrange"

    def __init__(self, *args, **kwargs):
        super(CreateDatacardsDQCD, self).__init__(*args, **kwargs)
        self.sigma = self.mass_point * 0.01
        self.fit_range = (self.mass_point - 5 * self.sigma, self.mass_point + 5 * self.sigma)
        if self.process_group_name != "default":
            self.models = self.modify_models()

    def requires(self):
        reqs = super(CreateDatacardsDQCD, self).requires()

        loose_region = self.region.name.replace("tight", "loose")
        if not self.counting:
            for process in reqs["fits"]:
                x_range = self.fit_range
                if process == "data_obs":
                    reqs["fits"][process] = Fit.vreq(reqs["fits"][process],
                        region_name=self.region_name, x_range=x_range, process_group_name="data")
                    continue  # FIXME
                if not self.config.processes.get(process).isSignal and \
                        not self.config.processes.get(process).isData:
                    region_name = loose_region
                    process_group_name = "background"
                else:
                    region_name = self.region_name  # probably redundant
                    process_group_name = "sig_" + self.process_group_name
                reqs["fits"][process] = Fit.vreq(reqs["fits"][process], region_name=region_name,
                    x_range=x_range, process_group_name=process_group_name)
                reqs["inspections"][process] = InspectFitSyst.vreq(reqs["inspections"][process],
                    region_name=region_name, x_range=x_range, process_group_name=process_group_name)

        else:  # counting
            blind_range = (str(self.mass_point - 2 * self.sigma), str(self.mass_point + 2 * self.sigma))
            for process in reqs["fits"]:
                if process == "data_obs": # FIXME
                    x_range = (str(self.fit_range[0]), str(self.fit_range[1]))
                    process_group_name = "data"
                    blind_range = ("-1", "-1")
                    region_name = loose_region
                elif not self.config.processes.get(process).isSignal and \
                        not self.config.processes.get(process).isData:
                    x_range = (str(self.fit_range[0]), str(self.fit_range[1]))
                    blind_range = blind_range
                    process_group_name = "qcd_background"
                    ins_process_group_name = "background"
                    ins_process_name = "background"
                    region_name = loose_region
                else:
                    x_range = blind_range
                    blind_range = ("-1", "-1")
                    process_group_name = "sig_" + self.process_group_name[len("qcd_"):]
                    ins_process_group_name = "sig_" + self.process_group_name[len("qcd_"):]
                    ins_process_name = self.process_group_name[len("qcd_"):]
                    region_name = self.region_name

                reqs["fits"][process] = Fit.vreq(reqs["fits"][process], region_name=region_name,
                    x_range=x_range, process_group_name=process_group_name, blind_range=blind_range)
                if process != "data_obs":
                    reqs["inspections"][process] = InspectFitSyst.vreq(reqs["inspections"][process],
                        region_name=region_name, x_range=x_range,
                        process_group_name=ins_process_group_name, blind_range=blind_range,
                        process_name=ins_process_name)

        # get models for background scaling
        background_model_found = False
        for model, fit_params in self.models.items():
            fit_params["x_range"] = str(self.fit_range)[1:-1]
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
        for category_name in self.category_names:
            counting = self.fit_config[self.process_group_name][category_name]
            process_group_name = (self.process_group_name if not counting
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

    def get_mass_point(self, process_group_name):
        if "scenario" in process_group_name:
            signal_tag = "A"
        elif "hzdzd" in process_group_name:
            signal_tag = "zd"
        elif "zprime" in process_group_name:
            signal_tag = "pi"
        elif "vector" in process_group_name or "btophi" in process_group_name:
            signal_tag = ""
        else:
            raise ValueError(f"{process_group_name} can't be handled by ScanCombineDQCD")
        i = process_group_name.find(f"m{signal_tag}_")
        f = process_group_name.find("_ctau")
        mass_point = float(process_group_name[i + 2 + len(signal_tag):f].replace("p", "."))
        if mass_point == 0.33:
            mass_point = 0.333
        elif mass_point == 0.67:
            mass_point = 0.667
        return mass_point

    def __init__(self, *args, **kwargs):
        super(ProcessGroupNameWrapper, self).__init__(*args, **kwargs)
        if not self.process_group_names:
            self.process_group_names = list(self.fit_config.keys())
        # self.process_group_name = self.process_group_names[0]
        # self.category_names = list(self.fit_config[self.process_group_name].keys())
        # self.category_name = self.category_names[0]


class ScanCombineDQCD(RunCombineDQCD, ProcessGroupNameWrapper):
    def __init__(self, *args, **kwargs):
        super(ScanCombineDQCD, self).__init__(*args, **kwargs)
        assert(
            self.combine_categories or len(self.process_group_names)
        )

    def create_branch_map(self):
        if self.combine_categories:
            return len(self.process_group_names)
        else:
            process_group_name = self.process_group_names[0]
            return len(list(self.fit_config[process_group_name].keys()))
          
    def requires(self):
        if self.combine_categories:
            process_group_name=self.process_group_names[self.branch]
            mass_point = self.get_mass_point(process_group_name)
            signal = process_group_name[:process_group_name.find("_")]
            return RunCombineDQCD.vreq(self, mass_point=mass_point,
                process_group_name=process_group_name,
                region_name=f"tight_bdt_{signal}",
                category_names=self.fit_config[process_group_name].keys(),
                _exclude=["branches", "branch"])
        else:
            process_group_name=self.process_group_names[0]
            mass_point = self.get_mass_point(process_group_name)
            signal = process_group_name[:process_group_name.find("_")]
            return RunCombineDQCD.vreq(self, mass_point=mass_point,
                process_group_name=process_group_name,
                region_name=f"tight_bdt_{signal}",
                category_names=self.fit_config[process_group_name].keys(),
                _exclude=["branches", "branch"])

    def workflow_requires(self):
        if self.combine_categories:
            process_group_name=self.process_group_names[self.branch]
            mass_point = self.get_mass_point(process_group_name)
            signal = process_group_name[:process_group_name.find("_")]
            return {"data": RunCombineDQCD.vreq(self, mass_point=mass_point,
                process_group_name=process_group_name,
                region_name=f"tight_bdt_{signal}",
                category_names=self.fit_config[process_group_name].keys(),
                _exclude=["branches", "branch"])}
        else:
            process_group_name=self.process_group_names[0]
            mass_point = self.get_mass_point(process_group_name)
            signal = process_group_name[:process_group_name.find("_")]
            return {"data": RunCombineDQCD.vreq(self, mass_point=mass_point,
                process_group_name=process_group_name,
                region_name=f"tight_bdt_{signal}",
                category_names=self.fit_config[process_group_name].keys(),
                _exclude=["branches", "branch"])}

    def output(self):
        if self.combine_categories:
            process_group_name=self.process_group_names[self.branch]
        else:
            process_group_name=self.process_group_names[0]

        return {
            feature.name: self.local_target("results_{}{}.json".format(
                feature.name, self.get_output_postfix(process_group_name=process_group_name,
                    category_names=self.fit_config[process_group_name].keys())))
            for feature in self.features
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
        if self.combine_categories:
            inputs = self.input()["collection"].targets[0]
        else:
            inputs = self.input()["collection"].targets[self.branch]
        for feature in self.features:
            res = self.combine_parser(inputs[feature.name]["txt"].path)
            if not res:
                print("Fit did not converge. Filling with dummy values.")
                res = {
                    "2.5": 1.,
                    "16.0": 1.,
                    "50.0": 1.,
                    "84.0": 1.,
                    "97.5": 1.
                }
            with open(create_file_dir(self.output()[feature.name].path), "w+") as f:
                json.dump(res, f, indent=4)


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
        "base",
        "singlev_cat1", "singlev_cat2", "singlev_cat3",
        "singlev_cat4", "singlev_cat5", "singlev_cat6",
        "multiv_cat1", "multiv_cat2", "multiv_cat3",
        "multiv_cat4", "multiv_cat5", "multiv_cat6",
    )
    feature_name = "muonSV_bestchi2_mass_fullrange"
    params = ["integral", "mean", "sigma", "gamma", "chi2"]

    def requires(self):
        reqs = {}
        for process_group_name in self.process_group_names:
            signal = process_group_name[:process_group_name.find("_")]
            tight_region = f"tight_bdt_{signal}"
            loose_region = f"loose_bdt_{signal}"
            mass_point = self.get_mass_point(process_group_name)
            sigma = mass_point * 0.01
            fit_range = (mass_point - 5 * sigma, mass_point + 5 * sigma)

            reqs[process_group_name] = {}
            for category_name in self.category_names:
                reqs[process_group_name][category_name] = Fit.vreq(
                    self, process_group_name="sig_" + process_group_name, region_name=tight_region,
                    category_name=category_name, feature_names=(self.feature_name,),
                    x_range=fit_range, method="voigtian", process_name=process_group_name,
                    fit_parameters={"mean": (mass_point, mass_point - 0.1, mass_point + 0.1)})
        return reqs

    def output(self):
        out = {}
        out["tables"] = {
            cat: {
                ext: self.local_target(f"table_{cat}_{self.fit_config_file}.{ext}")
                for ext in ["txt", "tex", "json"]
            } for cat in self.category_names
        }
        for param in self.params:
            if param == "chi2":
                out[param] = self.local_target(f"{param}/{param}_{self.fit_config_file}.pdf")
            out[f"{param}_cat"] = {
                cat: self.local_target(f"{param}/{param}_{cat}_{self.fit_config_file}.pdf")
                for cat in self.category_names
            }
            if param == "integral":
                out[f"{param}_cat_ratio"] = {
                    cat: self.local_target(f"{param}/{param}_{cat}_ratio_{self.fit_config_file}.pdf")
                    for cat in self.category_names
                }
                out[f"{param}_cat_unc"] = {
                    cat: self.local_target(f"{param}/{param}_{cat}_rel_unc_{self.fit_config_file}.pdf")
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

        plot = []
        d_param = {cat: {} for cat in self.category_names}
        d_param_ratio = {cat: {} for cat in self.category_names}
        d_param_unc = {cat: {} for cat in self.category_names}
        for icat, cat in enumerate(self.category_names):
            table = []
            outd = {}
            d_param[cat] = {param: {} for param in self.params}
            d_param_ratio[cat] = {param: {} for param in self.params}
            d_param_unc[cat] = {"integral": {}}
            for pgn in self.process_group_names:
                mass_point = self.get_mass_point(pgn)
                # ctau = float(pgn.split("_ctau_")[1].replace("p", "."))
                ctau = pgn.split("_ctau_")[1].replace("p", ".")
                try:
                    ctau = float(ctau)
                except ValueError:  # vector portal has _xiO_1_xiL_1 after ctau, need to remove it
                    ctau = float(ctau.split("_")[0])

                with open(inputs[pgn][cat][self.feature_name]["json"].path) as f:
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
                        d_param[cat][param][(mass_point, ctau)] = round_unc(d[""][param])
                        d_param_ratio[cat][param][(mass_point, ctau)] = round_unc(d[""][param] /
                            d_param["base"][param][(mass_point, ctau)])
                        if param == "integral":
                            d_param_unc[cat][param][(mass_point, ctau)] = round_unc(
                                d[""]["integral_error"] / d[""]["integral"] if d[""]["integral"] != 0
                                else 0.
                            )

            # fancy_table = tabulate.tabulate(table, headers=["process"] + self.params)
            # with open(create_file_dir(self.output()["tables"][cat]["txt"].path), "w+") as f:
                # f.write(fancy_table)
            # fancy_table_tex = tabulate.tabulate(table, headers=["process"] + self.params, tablefmt="latex")
            # with open(create_file_dir(self.output()["tables"][cat]["tex"].path), "w+") as f:
                # f.write(fancy_table_tex)
            # with open(create_file_dir(self.output()["tables"][cat]["json"].path), "w+") as f:
                # json.dump(d, f, indent=4)

            for key, d in zip(["cat", "cat_ratio", "cat_unc"], [d_param, d_param_ratio, d_param_unc]):
                for param in self.params:
                    if param != "integral" and key in ["cat_ratio", "cat_unc"]:
                        continue
                    ax = plt.subplot()
                    plt.plot([x for (x,y) in d[cat][param].keys()],
                        [y for (x,y) in d[cat][param].keys()], ".")
                    for (x, y), z in d[cat][param].items():
                        plt.annotate(z, # this is the text
                            (x, y), # this is the point to label
                            textcoords="offset points", # how to position the text
                            xytext=(0,10), # distance from text to points (x,y)
                            ha='center',
                            fontsize=5) # horizontal alignment can be left, right or center
                    plt.xlabel(f"mass")
                    plt.ylabel(f"ctau")
                    plt.yscale('log')
                    plt.savefig(create_file_dir(self.output()[f"{param}_{key}"][cat].path),
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
        plt.savefig(create_file_dir(self.output()["chi2"].path), bbox_inches='tight')
