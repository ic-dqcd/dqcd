import json
import luigi
from collections import OrderedDict
import numpy as np
import operator

from analysis_tools.utils import create_file_dir

from cmt.base_tasks.base import CategoryWrapperTask
from cmt.base_tasks.plotting import FeaturePlot
from cmt.base_tasks.analysis import Fit, CombineCategoriesTask
from tasks.analysis import ProcessGroupNameWrapper, ScanCombineDQCD, DQCDBaseTask, FitConfigBaseTask


class FeaturePlotDQCD(FeaturePlot):
    tight_region = luigi.Parameter(default="tight_bdt", description="region_name with the "
        "tighter bdt cut, default: tight_bdt")
    loose_region = luigi.Parameter(default="loose_bdt", description="region_name with the "
        "looser bdt cut, default: loose_bdt")

    def __init__(self, *args, **kwargs):
        super(FeaturePlotDQCD, self).__init__(*args, **kwargs)
        assert "tight" in self.region_name

    def requires(self):
        reqs = FeaturePlot.requires(self)

        # Move background's region name to loose
        plotting_loose_region = self.region.name.replace("tight", "loose")
        for dataset in self.processes_datasets[self.config.processes.get("background")]:
            reqs["data"][(dataset.name, self.category_name)].region_name = plotting_loose_region

        # FeaturePlots used for scaling the background, base category name, regions can be
        # added by the user
        reqs["tight"] = FeaturePlot.req(self, version="muonsv_calibration", category_name="base",
            region_name=self.tight_region, save_yields=True, save_pdf=False,
            feature_names=("muonSV_bestchi2_mass_fullrange",),
            process_group_name="background",
            _exclude=['include_fit', 'counting'])
        reqs["loose"] = FeaturePlot.req(self, version="muonsv_calibration", category_name="base",
            region_name=self.loose_region, save_yields=True, save_pdf=False,
            feature_names=("muonSV_bestchi2_mass_fullrange",),
            process_group_name="background",
            _exclude=['include_fit', 'counting'])

        return reqs

    def run(self):
        inputs = self.input()
        assert self.feature_names[0].startswith("muonSV_bestchi2_mass")
        with open(inputs["tight"]["yields"].targets["muonSV_bestchi2_mass_fullrange"].path) as f:
            d_tight = json.load(f)
        with open(inputs["loose"]["yields"].targets["muonSV_bestchi2_mass_fullrange"].path) as f:
            d_loose = json.load(f)

        self.additional_scaling = {"background": d_tight["background"]["Total yield"] /\
            d_loose["background"]["Total yield"]}

        super(FeaturePlotDQCD, self).run()


class FeaturePlotDQCDWrapper(CategoryWrapperTask):
    def atomic_requires(self, category_name):
        return FeaturePlotDQCD.req(self, category_name=category_name)


class PlotCombineDQCD(ProcessGroupNameWrapper, CombineCategoriesTask, DQCDBaseTask, FitConfigBaseTask):
    def requires(self):
        return ScanCombineDQCD.vreq(self, combine_categories=True)

    def output(self):
        return {
            feature.name: {
                ext: self.local_target("plot__{}__{}.{}".format(
                    feature.name, self.fit_config_file, ext))
                for ext in ["pdf", "png"]
            }
            for feature in self.features
        }

    def get_signal_tag(self, results, ilabel):
        process_name = self.config.processes.get(list(results.keys())[ilabel]).name
        if process_name.startswith("scenario"):
            return "_{A}"
        elif process_name.startswith("hzdzd"):
            return "_{Z_d}"
        elif process_name.startswith("zprime"):
            return "_{\pi}"
        elif process_name.startswith("btophi") or process_name.startswith("vector"):
            return ""
        else:
            raise ValueError

    def get_y_axis_label(self, process_group_name):
        if process_group_name.startswith("btophi"):
            return r"95$\%$ CL on BR(pp$\to$B$\to\phi$X$\to2\mu$X)"
        elif process_group_name.startswith("scenario"):
            return r"95$\%$ CL on BR(H$\to\Psi\Psi$)"
        return r"95$\%$ CL on BR"

    def plot(self, results, output_file):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        plt.rcParams['text.usetex'] = True

        ax = plt.subplot()

        def scale(val):
            return val * 0.01

        for ival, values in enumerate(results.values()):
            plt.fill_between((ival - 0.25, ival + 0.25),
                scale(values["16.0"]), scale(values["84.0"]),
                # color="g", alpha=.5)
                color="g")
            plt.fill_between((ival - 0.25, ival + 0.25),
                scale(values["84.0"]), scale(values["97.5"]),
                # color="y", alpha=.5)
                color="y")
            plt.fill_between((ival - 0.25, ival + 0.25),
                scale(values["16.0"]), scale(values["2.5"]),
                # color="y", alpha=.5)
                color="y")

            plt.plot([ival - 0.25, ival + 0.25], [scale(values["50.0"]), scale(values["50.0"])],
                color="k")

        labels = ["%s" % self.config.processes.get(key).label.latex for key in results]
        ax.set_xticks(list(range(len(labels))))

        if len(labels) <= 4:
            for ilabel, label in enumerate(labels):
                signal_tag = self.get_signal_tag(results, ilabel)
                index = label.find("$m%s" % signal_tag)
                labels[ilabel] = label[:index] + "\n" + label[index:]
            ax.set_xticklabels(labels)
        else:
            ax.set_xticklabels(labels, rotation=60, rotation_mode="anchor", ha="right")

        plt.ylabel(self.get_y_axis_label(self.fit_config_file))
        plt.text(0, 1.01, r"\textbf{CMS} \textit{Private Work}", transform=ax.transAxes)
        plt.text(1., 1.01, r"%s Simulation, %s fb${}^{-1}$" % (
            self.config.year, self.config.lumi_fb),
            transform=ax.transAxes, ha="right")
        if True:
            plt.yscale('log')
        plt.savefig(create_file_dir(output_file["pdf"].path), bbox_inches='tight')
        plt.savefig(create_file_dir(output_file["png"].path), bbox_inches='tight')
        plt.close('all')

    def run(self):
        inputs = self.input()
        for feature in self.features:
            results = OrderedDict()
            for ip, process_group_name in enumerate(self.process_group_names):
                with open(inputs["collection"].targets[ip][feature.name].path) as f:
                    results[process_group_name] = json.load(f)
            self.plot(results, self.output()[feature.name])


class ParamPlotDQCD(PlotCombineDQCD):
    def output(self):
        return {
            feature.name: 
                {
                    "txt": self.local_target("limits__{}__{}.csv".format(
                        feature.name, self.fit_config_file))
                }
            for feature in self.features
        }

    def run(self):
        inputs = self.input()
        for feature in self.features:
            results = OrderedDict()
            table = []
            for ip, process_group_name in enumerate(self.process_group_names):
                with open(inputs["collection"].targets[ip][feature.name].path) as f:
                    results[process_group_name] = json.load(f)
                params = process_group_name.split("_")
                if process_group_name.startswith("scenario"):
                    indexes = (4, 6)
                elif process_group_name.startswith("vector"):
                    indexes = (2, 4)
                else:
                    raise ValueError("Need to implement that process_group_name")
                params = {
                    "mass": float(params[indexes[0]].replace("p", ".")),
                    "lifetime": float(params[indexes[1]].replace("p", ".")),
                }
                table.append([
                    params["mass"], params["lifetime"],
                    results[process_group_name]["2.5"], results[process_group_name]["16.0"],
                    results[process_group_name]["50.0"], results[process_group_name]["84.0"],
                    results[process_group_name]["97.5"], 
                ])
            table = sorted(table, key=operator.itemgetter(1))
            table = sorted(table, key=operator.itemgetter(0))
            table = [[
                "mass", "lifetime", "Expected 2.5%", "Expected 16.0%",
                "Expected 50%", "Expected 84.0%", "Expected 97.5%",
            ]] + table
            with open(create_file_dir(self.output()[feature.name]["txt"].path), "w+") as fout:
                for line in table:
                    fout.write(",".join([str(elem) for elem in line]) + "\n")


class PlotCombinePerCategoryDQCD(PlotCombineDQCD):
    combine_categories = True  # for the output tag

    def requires(self):
        return {
            "cat": {
                pgn: ScanCombineDQCD.vreq(self, combine_categories=False,
                    process_group_names=[pgn], _exclude=["branches"])
                for pgn in self.process_group_names
            },
            "combined": ScanCombineDQCD.vreq(self, combine_categories=True, _exclude=["branches"]),
        }

    def output(self):
        return {
            process_group_name: {
                feature.name: self.local_target("plot__{}__{}.pdf".format(
                    feature.name, self.get_output_postfix(process_group_name=process_group_name)))
                for feature in self.features
            } for process_group_name in self.process_group_names
        }

    def plot(self, results, output_file, inner_text=None):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        plt.rcParams['text.usetex'] = True

        ax = plt.subplot()

        def scale(val):
            return val * 0.01

        vals = []

        for ival, values in enumerate(results.values()):
            plt.fill_between((ival - 0.25, ival + 0.25),
                scale(values["16.0"]), scale(values["84.0"]),
                # color="g", alpha=.5)
                color="g")
            plt.fill_between((ival - 0.25, ival + 0.25),
                scale(values["84.0"]), scale(values["97.5"]),
                # color="y", alpha=.5)
                color="y")
            plt.fill_between((ival - 0.25, ival + 0.25),
                scale(values["16.0"]), scale(values["2.5"]),
                # color="y", alpha=.5)
                color="y")

            plt.plot([ival - 0.25, ival + 0.25], [scale(values["50.0"]), scale(values["50.0"])],
                color="k")

            vals += list(values.values())

        min_val = scale(min(vals))
        max_val = scale(max(vals))

        labels = [f"{self.config.categories.get(key).label}"
            for key in list(results.keys())[:-1]]
        labels.append("Combined")
        plt.plot([len(labels) - 1.5, len(labels) - 1.5], [0, 100], color="k")
        ax.set_xticks(list(range(len(labels))))

        ax.set_ybound(0.5 * min_val, 2 * max_val)
        ax.set_ylim(0.5 * min_val, 2 * max_val)
        ax.set_xbound(-0.5, len(labels) - 0.5)
        ax.set_xlim(-0.5, len(labels) - 0.5)

        if len(labels) <= 4:
            for ilabel, label in enumerate(labels):
                signal_tag = self.get_signal_tag(results, ilabel)
                index = label.find("$m%s" % signal_tag)
                labels[ilabel] = label[:index] + "\n" + label[index:]
            ax.set_xticklabels(labels)
        else:
            ax.set_xticklabels(labels, rotation=60, rotation_mode="anchor", ha="right")

        plt.ylabel(self.get_y_axis_label(self.fit_config_file))
        plt.text(0, 1.01, r"\textbf{CMS} \textit{Private Work}", transform=ax.transAxes)
        plt.text(1., 1.01, r"%s Simulation, %s fb${}^{-1}$" % (
            self.config.year, self.config.lumi_fb),
            transform=ax.transAxes, ha="right")
        plt.text(0.5, 0.95, inner_text, transform=ax.transAxes, ha="center")
        if True:
            plt.yscale('log')
        plt.savefig(output_file, bbox_inches='tight')

        plt.close('all')

    def run(self):
        inputs = self.input()
        for feature in self.features:
            for ip, process_group_name in enumerate(self.process_group_names):
                results = OrderedDict()
                for ic, category_name in enumerate(self.fit_config[process_group_name].keys()):
                    with open(inputs["cat"][process_group_name]["collection"].targets[ic][feature.name].path) as f:
                        results[category_name] = json.load(f)
                with open(inputs["combined"]["collection"].targets[ip][feature.name].path) as f:
                    results["Combined"] = json.load(f)

                self.plot(results, create_file_dir(
                    self.output()[process_group_name][feature.name].path),
                    inner_text=self.config.processes.get(process_group_name).label.latex)
