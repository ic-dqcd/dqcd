import json
import luigi
import law
from copy import deepcopy as copy

from analysis_tools.utils import create_file_dir

from cmt.base_tasks.analysis import (
    Fit, CreateDatacards, CombineDatacards, CreateWorkspace, RunCombine
)


class CreateDatacardsDQCD(CreateDatacards):
    tight_region = luigi.Parameter(default="tight_bdt", description="region_name with the "
        "tighter bdt cut, default: tight_bdt")
    loose_region = luigi.Parameter(default="loose_bdt", description="region_name with the "
        "looser bdt cut, default: loose_bdt")
    mass_point = luigi.FloatParameter(default=1.33, description="mass point to be used to "
        "define the fit ranges and blinded regions")

    calibration_feature_name = "muonSV_bestchi2_mass_fullrange"

    def __init__(self, *args, **kwargs):
        super(CreateDatacardsDQCD, self).__init__(*args, **kwargs)
        assert "tight" in self.region_name
        assert len(self.config.process_group_names[self.process_group_name]) == 3
        for process in self.config.process_group_names[self.process_group_name]:
            if self.config.processes.get(process).isSignal:
                signal_process = process
                break
        for model in self.models:
            process_name = self.models[model]["process_name"]
            if process_name != signal_process and self.config.processes.get(process_name).isSignal:
                self.models[model]["process_name"] = signal_process
                self.models[signal_process] = copy(self.models[model])
                del self.models[model]

    def requires(self):
        reqs = CreateDatacards.requires(self)
        sigma = self.mass_point * 0.01
        fit_range = (self.mass_point - 5 * sigma, self.mass_point + 5 * sigma)

        loose_region = self.region.name.replace("tight", "loose")
        for process in reqs["fits"]:
            reqs["fits"][process].x_range = fit_range
            if process == "background":
                reqs["fits"][process].region_name = loose_region
            else:
                reqs["fits"][process].region_name = self.region_name  # probably redundant

            for model, fit_params in self.models.items():
                fit_params["x_range"] = str(fit_range)[1:-1]
                if fit_params["process_name"] == "background":
                    params = ", ".join([f"{param}='{value}'"
                        for param, value in fit_params.items() if param != "fit_parameters"])
                    if "fit_parameters" in fit_params:
                        params += ", fit_parameters={" + ", ".join([f"'{param}': '{value}'"
                        for param, value in fit_params["fit_parameters"].items()]) + "}"

                        reqs["tight"] =  eval("Fit.vreq(self,version=self.version + '_calib', "
                            f"{params}, _exclude=['include_fit'], "
                            "region_name=self.tight_region, "
                            f"feature_names=('{self.calibration_feature_name}',), "
                            "category_name='base')")
                        reqs["loose"] =  eval(f"Fit.vreq(self, version=self.version + '_calib', "
                            f"{params}, _exclude=['include_fit'], "
                            "region_name=self.loose_region, "
                            f"feature_names=('{self.calibration_feature_name}',), "
                            "category_name='base')")

        if self.counting:  # counting
            blind_range = (str(self.mass_point - 2 * sigma), str(self.mass_point + 2 * sigma))
            for process in reqs["fits"]:
                if process == "background":
                    reqs["fits"][process].x_range = (str(fit_range[0]), str(fit_range[1]))
                    reqs["fits"][process].blind_range = blind_range
                else:
                    reqs["fits"][process].x_range = blind_range

        return reqs

    def run(self):
        inputs = self.input()
        with open(inputs["tight"][self.calibration_feature_name]["json"].path) as f:
            d_tight = json.load(f)
        with open(inputs["loose"][self.calibration_feature_name]["json"].path) as f:
            d_loose = json.load(f)
        additional_scaling = d_tight[""]["integral"] / d_loose[""]["integral"]

        if not self.counting:
            self.additional_scaling = {"background": additional_scaling}
        else:
            self.additional_scaling = {"background": additional_scaling * 2/3}

        super(CreateDatacardsDQCD, self).run()


class CombineDatacardsDQCD(CombineDatacards, CreateDatacardsDQCD):
    fit_config_file = luigi.Parameter(default="fit_config", description="file including "
        "fit configuration, default: fit_config.yaml")
    category_name = "base"
    category_names = ("base",)

    def __init__(self, *args, **kwargs):
        super(CombineDatacardsDQCD, self).__init__(*args, **kwargs)
        self.fit_config = self.config.get_fit_config(self.fit_config_file)
        self.category_names = self.fit_config[self.process_group_name].keys()

    def requires(self):
        return {
            category_name: CreateDatacardsDQCD.vreq(self, category_name=category_name,
                counting=self.fit_config[self.process_group_name][category_name],
                _exclude=["category_names"])
            for category_name in self.category_names
        }


class CreateWorkspaceDQCD(CreateWorkspace, CombineDatacardsDQCD):
    def requires(self):
        return CombineDatacardsDQCD.vreq(self)


class RunCombineDQCD(RunCombine, CreateWorkspaceDQCD):
    method = "limits"

    def requires(self):
        return CreateWorkspaceDQCD.vreq(self)


class ScanCombineDQCD(RunCombineDQCD):
    process_group_names = law.CSVParameter(default=(), description="process_group_names to be used, "
        "empty means all scenarios, default: empty")
    process_group_name = "scenarioA_mpi_4_mA_1p33_ctau_10"  # placeholder

    def __init__(self, *args, **kwargs):
        super(ScanCombineDQCD, self).__init__(*args, **kwargs)
        if not self.process_group_names:
            self.process_group_names = self.fit_config.keys()

    def requires(self):
        reqs = {}
        for process_group_name in self.process_group_names:
            i = process_group_name.find("mA_")
            f = process_group_name.find("_ctau")
            mass_point = float(process_group_name[i + 3:f].replace("p", "."))
            reqs[process_group_name] = RunCombineDQCD.vreq(self, mass_point=mass_point,
                process_group_name=process_group_name)
        return reqs

    def output(self):
        return {
            process_group_name: {
                feature.name: self.local_target("results_{}{}.json".format(
                    feature.name, self.get_output_postfix(process_group_name=process_group_name)))
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
                with open(create_file_dir(self.output()[pgn][feature.name].path), "w+") as f:
                    json.dump(res, f, indent=4)
