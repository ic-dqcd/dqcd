import json
import luigi
import law
import math
import itertools
from copy import deepcopy as copy
import numpy as np

from analysis_tools.utils import create_file_dir, import_root

from cmt.base_tasks.base import DatasetWrapperTask
from cmt.base_tasks.plotting import FeaturePlot
from cmt.base_tasks.analysis import (
    Fit, InspectFitSyst, CombineCategoriesTask, CreateWorkspace, RunCombine
)
from tasks.analysis import (
    DQCDBaseTask, CreateDatacardsDQCD, CombineDatacardsDQCD, InterpolationTestDQCD,
    ProcessGroupNameWrapper, FitConfigBaseTask, BaseScanTask, FitDQCD
)
from tasks.plotting import PlotCombineDQCD
from collections import OrderedDict


class BaseDQCDGridTask(DQCDBaseTask, ProcessGroupNameWrapper):
    default_process_group_name = "sigbkg"
    def __init__(self, *args, **kwargs):
        super(BaseDQCDGridTask, self).__init__(*args, **kwargs)
        self.ctau = self.get_ctau(self.process_group_name)


class CreateDatacardsGridDQCD(BaseDQCDGridTask, CreateDatacardsDQCD):
    refit_signal_with_syst = False

    def __init__(self, *args, **kwargs):
        super(CreateDatacardsGridDQCD, self).__init__(*args, **kwargs)
        self.interpolation_model = None
        self.non_data_names = [elem.replace("signal", self.process_group_name.replace("data_", ""))
            for elem in self.non_data_names]
        self.empty_background = False
        # avoid using a different ctau than the one in the process_group_name
        
    def requires(self):
        reqs = {"fits": {}, "inspections": {}}
        loose_region_name = self.region.name.replace("tight", "loose")

        # background fit
        bkg_process_name = "data"  # move to data when the unblinding strategy is in place
        self.model_processes = [bkg_process_name]
        fit_params = self.models["background"]
        fit_params["x_range"] = str(self.fit_range)[1:-1]
        if bkg_process_name != "background":
            fit_params["blind_range"] = str(self.blind_range)[1:-1]

        params = ", ".join([f"{param}='{value}'"
            for param, value in fit_params.items() if param != "fit_parameters"])
        if "fit_parameters" in fit_params:
            params += ", fit_parameters={" + ", ".join([f"'{param}': '{value}'"
            for param, value in fit_params["fit_parameters"].items()]) + "}"

        if bkg_process_name == "background":
            reqs["fits"]["background"] = eval(f"FitDQCD.vreq(self, {params}, region_name=loose_region_name, "
                "process_group_name='background')")#, _exclude=['include_fit', 'save_pdf', 'save_png'])")
        else:
            reqs["fits"]["data"] = eval(f"Fit.vreq(self, {params}, region_name=self.region_name, "
                "process_group_name='data')")#, _exclude=['include_fit', 'save_pdf', 'save_png'])")
            params = params.replace(fit_params["method"], "constant")
            reqs["constant_fit"] = eval(f"Fit.vreq(self, {params}, region_name=self.region_name, "
                "process_group_name='data')")
                #, _exclude=['include_fit', 'save_pdf', 'save_png'])")
        # reqs["inspections"]["background"] = eval(f"InspectFitSyst.vreq(self, {params}, "
            # "region_name=loose_region_name, process_group_name='background',"
            # "_exclude=['include_fit', 'save_pdf', 'save_png'])")

        # data_obs fit (to obtain the yield)
        # we may need to fix this later on if we apply any blinding on the background fit
        fit_params = copy(self.models["background"])
        fit_params["process_name"] = "data"
        params = ", ".join([f"{param}='{value}'"
            for param, value in fit_params.items() if param != "fit_parameters"])
        if "fit_parameters" in fit_params:
            params += ", fit_parameters={" + ", ".join([f"'{param}': '{value}'"
            for param, value in fit_params["fit_parameters"].items()]) + "}"

        # data_obs
        if bkg_process_name != "background":
            fit_params["x_range"] = str(self.blind_range)[1:-1]
            del fit_params["blind_range"]
            params = ", ".join([f"{param}='{value}'"
                for param, value in fit_params.items() if param != "fit_parameters"])
            if "fit_parameters" in fit_params:
                params += ", fit_parameters={" + ", ".join([f"'{param}': '{value}'"
                for param, value in fit_params["fit_parameters"].items()]) + "}"

        reqs["fits"]["data_obs"] = eval(f"Fit.vreq(self, {params}, region_name=self.region.name, "
            "process_group_name='data', _exclude=['include_fit', 'save_pdf', 'save_png'])")
        reqs["signal"] = InterpolationTestDQCD.vreq(self, category_names=(self.category_name,), 
            process_group_names=self.process_group_names)

        return reqs

    def process_is_signal(self, p_name):
        try:
            return super(CreateDatacardsGridDQCD, self).process_is_signal(p_name)
        except:
            return True

    def get_rate_from_process_in_fit(self, feature, p_name):
        try:
            if not self.config.processes.get(p_name).isSignal:
                return super(CreateDatacardsGridDQCD, self).get_rate_from_process_in_fit(feature, p_name)
            else:
                raise ValueError
        except ValueError:
            if self.interpolation_model == None:
                import pickle
                # with open(self.input()["signal"][feature.name][self.category_name]["interp2d_model"].path, "rb") as f:
                with open(self.input()["signal"][feature.name][self.category_name]["interp_model"].path, "rb") as f:
                    self.interpolation_model = pickle.load(f)
            try:  # interp2d
                return float(self.interpolation_model(self.mass_point, self.ctau)[0])
            except IndexError:  # interp
                return float(self.interpolation_model(self.mass_point, self.ctau))

    def get_norm_systematics_from_inspect(self, feature_name):
        # structure: systematics[syst_name][process_name] = syst_value
        systematics = {}
        for name in self.non_data_names:
            is_signal = False
            try:
                is_signal = self.config.processes.get(name).isSignal
            except ValueError:
                is_signal = True
            if not is_signal:
                continue  # Avoid bkg systematics for now
                path = self.input()["inspections"][name][feature_name]["json"].path
                with open(path) as f:
                    d = json.load(f)
                for syst_name, values in d.items():
                    up_value = values["integral"]["up"]
                    down_value = values["integral"]["down"]
                    if up_value == -999 or down_value == -999:
                        continue
                    if abs(up_value) > self.norm_syst_threshold or \
                            abs(down_value) > self.norm_syst_threshold:
                        if syst_name not in systematics:
                            systematics[syst_name] = {}
                        # symmetric?
                        if abs(up_value + down_value) < self.norm_syst_threshold_sym:
                            systematics[syst_name][name] = "{:.2f}".format(1 + up_value)
                        else:
                            systematics[syst_name][name] = "{:.2f}/{:.2f}".format(1 + up_value,
                                1 + down_value)
            else:
                systematics["pu"] = {name: "1.04"}
                systematics["id"] = {name: "1.07"}
                systematics["trig"] = {name: "1.04"}
        return systematics

    def get_shape_systematics_from_inspect(self, feature_name):
        def round_unc(num):
            if num == 0:
                return num
            exp = 0
            while True:
                if num * 10 ** exp > 1:
                    return round(num, exp + 1)
                exp += 1
        # structure: systematics[syst_name][process_name][parameter] = syst_value
        systematics = {}
        for name in self.non_data_names:
            is_signal = False
            try:
                is_signal = self.config.processes.get(name).isSignal
            except ValueError:
                is_signal = True
            if not is_signal:
                continue  # Avoid bkg systematics for now
                path = self.input()["inspections"][name][feature_name]["json"].path
                with open(path) as f:
                    d = json.load(f)
                for syst_name, values in d.items():
                    for param in values:
                        if param == "integral":
                            continue
                        up_value = round_unc(abs(values[param]["up"]))
                        down_value = round_unc(abs(values[param]["down"]))
                        if up_value == -999 or down_value == -999:
                            continue
                        if abs(up_value) > self.norm_syst_threshold or \
                                abs(down_value) > self.norm_syst_threshold:
                            if name not in systematics:
                                systematics[name] = {}
                            if param not in systematics[name]:
                                systematics[name][param] = {}
                            systematics[name][param][syst_name] = max(up_value, down_value)
            else:
                systematics[name] = {
                    "sigma":
                        {
                            "pu": 0.05,
                            "id": 0.04,
                            "trig": 0.01
                        }
                }
        return systematics

    def update_parameters_for_fitting_signal(self, feature, fit_params, fit_parameters,
            workspace_is_available):
        if workspace_is_available:  # shouldn't be called ever
            return super(CreateDatacardsGridDQCD, self).update_parameters_for_fitting_signal(
                feature, fit_params, fit_parameters, workspace_is_available
            )
        fit_parameters.update({"sigma": (0.01 * self.mass_point,), "gamma": (0.005,)})
        return fit_parameters


class CombineDatacardsGridDQCD(BaseDQCDGridTask, CombineDatacardsDQCD):
    def requires(self):
        reqs = {}
        for category_name in self.category_names:
            reqs[category_name] = CreateDatacardsGridDQCD.vreq(self, category_name=category_name,
                process_group_name=self.process_group_name, _exclude=["category_names"])

        return reqs


class CreateWorkspaceGridDQCD(BaseDQCDGridTask, FitConfigBaseTask, CreateWorkspace):
    def requires(self):
        if self.combine_categories:
            return CombineDatacardsGridDQCD.vreq(self)
        reqs = {}
        for category_name in self.category_names:
            reqs[category_name] = CreateDatacardsGridDQCD.vreq(self, category_name=category_name,
                process_group_name=self.process_group_name)
        return reqs

    def workflow_requires(self):
        if self.combine_categories:
            return {"data": CombineDatacardsGridDQCD.vreq(self)}
        reqs = {"data": {}}
        for category_name in self.category_names:
            reqs["data"][category_name] = CreateDatacardsGridDQCD.vreq(self, category_name=category_name,
                process_group_name=self.process_group_name)
        return reqs


class RunCombineGridDQCD(BaseDQCDGridTask, FitConfigBaseTask, RunCombine):
    method = "limits"

    def workflow_requires(self):
        return {"data": CreateWorkspaceGridDQCD.vreq(self)}

    def requires(self):
        return CreateWorkspaceGridDQCD.vreq(self)


class PlotGridBaseDQCD(law.Task):
    signal_template = luigi.Parameter(default="scenarioA_mpi_4_mA_{}_ctau_{}", description="signal "
        "process template, default: scenarioA_mpi_4_mA_{}_ctau_{}")
    min_mass = luigi.FloatParameter(default=0.4, description="minimum mass to be considered in the "
        "grid, default: 0.4")
    max_mass = luigi.FloatParameter(default=1.9, description="maximum mass to be considered in the "
        "grid, default: 1.9")
    n_masses = luigi.IntParameter(default=20, description="number of mass points to be considered, "
        "default: 20")
    min_ctau = luigi.FloatParameter(default=0.1, description="minimum ctau to be considered in the "
        "grid, default: 0.1")
    max_ctau = luigi.FloatParameter(default=100, description="maximum ctau to be considered in the "
        "grid, default: 100")
    n_ctaus = luigi.IntParameter(default=20, description="number of ctau points to be considered, "
        "default: 20")


class ScanCombineGridDQCD(BaseScanTask, PlotGridBaseDQCD):
    feature_names = ("muonSV_bestchi2_mass",)
    features_to_compute = lambda self, m: (f"self.config.get_feature_mass_dxyzcut({m})",)
    category_names = (
        "singlev_cat1", "singlev_cat2", "singlev_cat3",
        "singlev_cat4", "singlev_cat5", "singlev_cat6",
        "multiv_cat1", "multiv_cat2", "multiv_cat3",
        "multiv_cat4", "multiv_cat5", "multiv_cat6",
    )

    def __init__(self, *args, **kwargs):
        super(ScanCombineGridDQCD, self).__init__(*args, **kwargs)

        masses = np.linspace(start=self.min_mass, stop=self.max_mass, num=self.n_masses)
        # remove masses within the resonance ranges
        for resonance_mass_range in self.config.resonance_masses.values():
            masses = [elem for elem in masses 
                if elem < resonance_mass_range[0] or elem > resonance_mass_range[1]]
        ctaus = np.geomspace(start=self.min_ctau, stop=self.max_ctau, num=self.n_ctaus)

        self.params = {i: elem for i, elem in enumerate(itertools.product(masses, ctaus))}
        assert(self.combine_categories or len(self.params) == 1)

    def get_processes_to_scan(self):
        return [self.signal_template.format(*params) for params in self.params.values()]

    def requires(self):
        reqs = {}
        for params in self.params.values():
            pgn = self.signal_template.format(*params)
            mass_point = self.get_mass_point(pgn)
            mass_point_str = str(mass_point).replace(".", "p")
            signal = pgn[:pgn.find("_")]
            reqs[pgn] = RunCombineGridDQCD.vreq(self, version=self.version + f"_m{mass_point_str}",
                feature_names=self.features_to_compute(mass_point),
                mass_point=mass_point,
                process_group_name=("data_" if self.use_data else "") + pgn,
                region_name=f"tight_bdt_{signal}",
                category_names=self.category_names,
                custom_output_tag="_" + pgn)
        return reqs

    def output(self):
        if self.combine_categories:
            return {
                self.signal_template.format(*params): {
                    feature.name: self.local_target("results_{}_{}.json".format(
                        feature.name, self.signal_template.format(*params)))
                    for feature in self.features
                } for params in self.params.values()
            }
        else:
            return {
                self.signal_template.format(*params): {
                    category_name: {
                        feature.name: self.local_target("results_{}_{}_{}.json".format(
                            feature.name, self.signal_template.format(*params), category_name))
                        for feature in self.features
                    } for category_name in self.category_names
                } for params in self.params.values()
            }


class PlotDQCDGrid1D(PlotGridBaseDQCD, PlotCombineDQCD):
    fixed_ctau = luigi.FloatParameter(default=law.NO_FLOAT, description="fixed ctau")
    fixed_mass = luigi.FloatParameter(default=law.NO_FLOAT, description="fixed mass")

    combine_categories = True

    def __init__(self, *args, **kwargs):
        super(PlotDQCDGrid1D, self).__init__(*args, **kwargs)
        assert(
            (self.fixed_ctau != law.NO_FLOAT and self.fixed_mass == law.NO_FLOAT) or
            (self.fixed_ctau == law.NO_FLOAT and self.fixed_mass != law.NO_FLOAT)
        ),  "Either fixed_ctau or fixed_mass must be included"

    def requires(self):
        if self.fixed_ctau != law.NO_FLOAT:
            self.min_ctau = self.fixed_ctau
            self.max_ctau = self.fixed_ctau
            self.n_ctaus = 1
        else:
            self.min_mass = self.fixed_mass
            self.max_mass = self.fixed_mass
            self.n_masses = 1
        return ScanCombineGridDQCD.vreq(self, combine_categories=True)

    def output(self):
        if self.fixed_ctau != law.NO_FLOAT:
            postfix = f"ctau_{self.fixed_ctau}"
        else:
            postfix = f"m_{self.fixed_mass}"

        return {
            feature.name: {
                ext: self.local_target("plot__{}__{}__{}.{}".format(
                    feature.name, self.fit_config_file, postfix, ext))
                for ext in ["pdf", "png"]
            }
            for feature in self.requires().features
        }

    def get_extra_signal_mass_from_template(self, template):
        elems = template.split("_")
        for ielem, elem in enumerate(elems):
            if elem.startswith("m"):
                try:
                    mass = float(elems[ielem + 1])
                    obj = elem.split("m")[1]
                    return mass, obj
                except:
                    continue
        return -1, ""
        

    def plot(self, results, output_file):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        plt.rcParams['text.usetex'] = True

        ax = plt.subplot()

        def scale(val):
            return val * 0.01

        plt.fill_between(
            results.keys(),
            [scale(elem["16.0"]) for elem in results.values()],
            [scale(elem["84.0"]) for elem in results.values()],
            color="#607641"
        )
        plt.fill_between(
            results.keys(),
            [scale(elem["84.0"]) for elem in results.values()],
            [scale(elem["97.5"]) for elem in results.values()],
            color="#F5BB54"
        )
        plt.fill_between(
            results.keys(),
            [scale(elem["16.0"]) for elem in results.values()],
            [scale(elem["2.5"]) for elem in results.values()],
            color="#F5BB54"
        )
        plt.plot(
            results.keys(),
            [scale(elem["50.0"]) for elem in results.values()],
            color="r", linestyle="dashed"
        )

        plt.ylabel(self.get_y_axis_label(self.fit_config_file))

        llp_type = ""
        if self.signal_template.startswith("scenarioA"):
            llp_type="_{A'}"

        x_label = f"$m{llp_type}$ [GeV]" if self.fixed_ctau != law.NO_FLOAT else "$c\\tau$ [mm]"
        plt.xlabel(x_label)
        plt.text(0, 1.01, r"\textbf{CMS} \textit{Private Work}", transform=ax.transAxes)
        plt.text(1., 1.01, r"%s Simulation, %s fb${}^{-1}$" % (
            self.config.year, self.config.lumi_fb),
            transform=ax.transAxes, ha="right")

        inner_text = (f"$m{llp_type}={self.fixed_mass}$ GeV" if self.fixed_mass != law.NO_FLOAT
            else f"$c\\tau={self.fixed_ctau}$ mm")
        inner_text_height = 0.95
        add_mass, add_obj = self.get_extra_signal_mass_from_template(self.signal_template)
        if add_obj != "":
            inner_text_height -= 0.05
            if add_obj == "pi":
                inner_text += f"\n$m_\\pi={add_mass}$ GeV"
        plt.text(0.5, inner_text_height, inner_text, transform=ax.transAxes, ha="center")

        plt.yscale('log')
        if self.fixed_ctau == law.NO_FLOAT:
            plt.xscale('log')
        plt.savefig(create_file_dir(output_file["pdf"].path), bbox_inches='tight')
        plt.savefig(create_file_dir(output_file["png"].path), bbox_inches='tight')
        plt.close('all')

    def run(self):
        inputs = self.input()
        for feature in self.requires().features:
            results = OrderedDict()
            index_to_store = 0 if self.fixed_ctau != law.NO_FLOAT else 1
            for params in self.requires().params.values():
                with open(inputs[self.signal_template.format(*params)][feature.name].path) as f:
                    results[params[index_to_store]] = json.load(f)
            self.plot(results, self.output()[feature.name])
