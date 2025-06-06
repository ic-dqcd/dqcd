import json
import luigi
from collections import OrderedDict
import itertools
import numpy as np
import operator
import re

from analysis_tools.utils import create_file_dir, import_root

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

    feature_names = ("muonSV_bestchi2_mass",)

    def requires(self):
        return ScanCombineDQCD.vreq(self, combine_categories=True)

    def output(self):
        return {
            feature.name: {
                ext: self.local_target("plot__{}__{}.{}".format(
                    feature.name, self.fit_config_file, ext))
                for ext in ["pdf", "png"]
            }
            for feature in self.requires().features
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

    def set_cms_labels(self, plt, ax):
        plt.text(0, 1.01, r"\textbf{CMS} \textit{Private Work}", transform=ax.transAxes)
        plt.text(1., 1.01, r"%s%s, %s fb${}^{-1} (%s $TeV)" % (
            self.config.year,
            (" Simulation" if not self.unblind and "data" not in self.fit_models else ""),
            self.config.lumi_fb,
            self.config.ecm),
            transform=ax.transAxes, ha="right")

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
                color="#607641")
            plt.fill_between((ival - 0.25, ival + 0.25),
                scale(values["84.0"]), scale(values["97.5"]),
                # color="y", alpha=.5)
                color="#F5BB54")
            plt.fill_between((ival - 0.25, ival + 0.25),
                scale(values["16.0"]), scale(values["2.5"]),
                # color="y", alpha=.5)
                color="#F5BB54")

            plt.plot([ival - 0.25, ival + 0.25], [scale(values["50.0"]), scale(values["50.0"])],
                "--", color="k")

            if "observed" in values and self.unblind:
                plt.plot([ival - 0.25, ival + 0.25],
                    [scale(values["observed"]), scale(values["observed"])], "-", color="k")
                plt.plot(ival, scale(values["observed"]), "o", color="k")

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

        self.set_cms_labels(plt, ax)
        plt.ylabel(self.get_y_axis_label(self.fit_config_file))
        if True:
            plt.yscale('log')
        plt.savefig(create_file_dir(output_file["pdf"].path), bbox_inches='tight')
        plt.savefig(create_file_dir(output_file["png"].path), bbox_inches='tight')
        plt.close('all')

    def run(self):
        inputs = self.input()
        for feature in self.requires().features:
            results = OrderedDict()
            for ip, process_group_name in enumerate(self.process_group_names):
                with open(inputs[process_group_name][feature.name].path) as f:
                    results[process_group_name] = json.load(f)
            self.plot(results, self.output()[feature.name])


class ParamPlotDQCD(PlotCombineDQCD):
    def __init__(self, *args, **kwargs):
        super(ParamPlotDQCD, self).__init__(*args, **kwargs)
        masses = []
        ctaus = []
        for pgn in self.process_group_names:
            if "scenario" in pgn:
                pattern = r"scenario(.*)_mpi_(.*)_mA_(.*)_ctau_(.*)"
                match = re.fullmatch(pattern, pgn)
                masses.append((float(match.group(2)), float(match.group(3).replace("p", "."))))
                ctaus.append(self.get_ctau(pgn))
            elif "vector" in pgn:
                pattern = r"vector_m_(.*)_ctau_(.*)_xiO_1_xiL_1"
                match = re.fullmatch(pattern, pgn)
                masses.append(float(match.group(1)))
                ctaus.append(self.get_ctau(pgn))
            else:
                raise ValueError(f"{pgn} can't be considered as a process_group_name")
        self.masses = set(masses)
        self.ctaus = set(ctaus)

    def output(self):
        out = {
            feature.name:
                {
                    "txt": self.local_target("limits__{}__{}.csv".format(
                        feature.name, self.fit_config_file)),
                }
            for feature in self.requires().features
        }
        for feature in self.requires().features:
            if "scenario" in self.fit_config_file:
                out[feature.name]["mass"] = {
                    (mm, m): {
                        key: self.local_target("fixed_mass/limits__{}__{}__mm_{}_m_{}.{}".format(
                            feature.name, self.fit_config_file, mm, m, key))
                        for key in ["png", "pdf"]
                    }
                    for (mm, m) in self.masses
                }
                out[feature.name]["ctau"] = {
                    (mm, ctau): {
                        key: self.local_target("fixed_ctau/limits__{}__{}__mm_{}_ctau_{}.{}".format(
                            feature.name, self.fit_config_file, mm, ctau, key))
                        for key in ["png", "pdf"]
                    }
                    for (mm, ctau) in itertools.product([e[0] for e in self.masses], self.ctaus)
                }
            else:
                out[feature.name]["mass"] = {
                    m: {
                        key: self.local_target("fixed_mass/limits__{}__{}__m_{}.{}".format(
                            feature.name, self.fit_config_file, m, key))
                        for key in ["png", "pdf"]
                    }
                    for m in self.masses
                }
                out[feature.name]["ctau"] = {
                    ctau: {
                        key: self.local_target("fixed_ctau/limits__{}__{}__ctau_{}.{}".format(
                            feature.name, self.fit_config_file, ctau, key))
                        for key in ["png", "pdf"]
                    }
                    for ctau in self.ctaus
                }

        return out

    def plot(self, results, output_file, **kwargs):
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
            color="#607641",
            label="68\% expected"
        )
        plt.fill_between(
            results.keys(),
            [scale(elem["84.0"]) for elem in results.values()],
            [scale(elem["97.5"]) for elem in results.values()],
            color="#F5BB54",
            label="95\% expected"
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
            color="k", linestyle="dashed",
            label="Median expected"
        )
        plt.plot(
            results.keys(),
            [scale(elem["observed"]) for elem in results.values()],
            "o-", color="k",
            label="Observed"
        )

        plt.ylabel(self.get_y_axis_label(self.fit_config_file))

        x_label = kwargs.pop("x_label")
        plt.xlabel(x_label)
        self.set_cms_labels(plt, ax)

        # inner_text = (f"$m{llp_type}={self.fixed_mass}$ GeV" if self.fixed_mass != law.NO_FLOAT
            # else f"$c\\tau={self.fixed_ctau}$ mm")
        inner_text = kwargs.pop("inner_text")
        inner_text_height = 1.0 - 0.05 * len(inner_text)
        plt.text(0.5, inner_text_height, "\n".join(inner_text), transform=ax.transAxes, ha="center")

        leg = ax.legend()

        plt.yscale('log')
        if kwargs.pop("log", False):
            plt.xscale('log')
        plt.savefig(create_file_dir(output_file["pdf"].path), bbox_inches='tight')
        plt.savefig(create_file_dir(output_file["png"].path), bbox_inches='tight')
        plt.close('all')

    def run(self):
        inputs = self.input()
        for feature in self.requires().features:
            results = OrderedDict()
            table = []
            observed_is_available = False
            for ip, process_group_name in enumerate(self.process_group_names):
                with open(inputs[process_group_name][feature.name].path) as f:
                # with open(inputs["collection"].targets[ip][feature.name].path) as f:
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
                res = [
                    params["mass"], params["lifetime"],
                    results[process_group_name]["2.5"], results[process_group_name]["16.0"],
                    results[process_group_name]["50.0"], results[process_group_name]["84.0"],
                    results[process_group_name]["97.5"],
                ]
                if self.unblind and "observed" in results[process_group_name]:
                    observed_is_available = True
                    res.append(results[process_group_name]["observed"])
                table.append(res)
            table = sorted(table, key=operator.itemgetter(1))
            table = sorted(table, key=operator.itemgetter(0))
            keys = [
                "mass", "lifetime", "Expected 2.5%", "Expected 16.0%",
                "Expected 50%", "Expected 84.0%", "Expected 97.5%",
            ]
            if self.unblind and observed_is_available:
                keys.append("Observed")

            table = keys + table
            with open(create_file_dir(self.output()[feature.name]["txt"].path), "w+") as fout:
                for line in table:
                    fout.write(",".join([str(elem) for elem in line]) + "\n")

            # limit plots per parameter
            if "scenario" in self.fit_config_file:
                pattern = r"scenario(.*)_mpi_(.*)_mA_(.*)_ctau_(.*)"

                d_mass = {(mm, m): {} for mm, m in self.masses}
                d_ctau = {(mm, ctau): {}
                    for mm, ctau in itertools.product([elem[0] for elem in self.masses], self.ctaus)}
                for pgn, value in results.items():
                    match = re.fullmatch(pattern, pgn)
                    mm = float(match.group(2))
                    m = float(match.group(3).replace("p", "."))
                    ctau = float(match.group(4).replace("p", "."))
                    d_mass[(mm, m)][ctau] = value
                    d_ctau[(mm, ctau)][m] = value

                # llp_type = ""
                # if self.fit_config_file.startswith("scenario"):
                llp_type="_{A'}"
                for key, val in d_mass.items():
                    self.plot(dict(sorted(val.items())), self.output()[feature.name]["mass"][key],
                        x_label="$c\\tau$ [mm]",
                        log=True,
                        inner_text=[
                            f"Scenario {match.group(1)}",
                            f"$m_\\pi$={key[0]} GeV",
                            f"$m{llp_type}$={key[1]} GeV"]
                    )
                for key, val in d_ctau.items():
                    self.plot(dict(sorted(val.items())), self.output()[feature.name]["ctau"][key],
                        x_label=f"$m{llp_type}$ [GeV]",
                        inner_text=[
                            f"Scenario {match.group(1)}",
                            f"$m_\\pi$={key[0]} GeV",
                            f"$c\\tau=${key[1]} mm"]
                    )

            elif "vector" in self.fit_config_file:
                pattern = r"vector_m_(.*)_ctau_(.*)_xiO_1_xiL_1"
                d_mass = {m: {} for m in self.masses}
                d_ctau = {ctau: {} for ctau in self.ctaus}
                for pgn, value in results.items():
                    match = re.fullmatch(pattern, pgn)
                    m = float(match.group(1).replace("p", "."))
                    ctau = float(match.group(2).replace("p", "."))
                    d_mass[m][ctau] = value
                    d_ctau[ctau][m] = value

                for key, val in d_mass.items():
                    self.plot(dict(sorted(val.items())), self.output()[feature.name]["mass"][key],
                        x_label="$c\\tau$ [mm]",
                        log=True,
                        inner_text=[
                            f"Vector portal",
                            f"$m$={key} GeV"]
                    )
                for key, val in d_ctau.items():
                    self.plot(dict(sorted(val.items())), self.output()[feature.name]["ctau"][key],
                        x_label=f"$m$ [GeV]",
                        inner_text=[
                            f"Vector portal",
                            f"$c\\tau=${key} mm"]
                    )

            else:
                raise ValueError(f"Rename {self.fit_config_name} so it can be considered inside "
                    f"{type(self)}")


class PlotCombinePerCategoryDQCD(PlotCombineDQCD):
    combine_categories = True  # for the output tag

    def requires(self):
        return {
            "cat": ScanCombineDQCD.vreq(self, combine_categories=False),
            "combined": ScanCombineDQCD.vreq(self, combine_categories=True),
        }

    def output(self):
        return {
            process_group_name: {
                feature.name: self.local_target("plot__{}__{}.pdf".format(
                    feature.name, self.get_output_postfix(process_group_name=process_group_name)))
                for feature in self.requires()["combined"].features
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
                "--", color="k")

            if "observed" in values and self.unblind:
                plt.plot([ival - 0.25, ival + 0.25],
                    [scale(values["observed"]), scale(values["observed"])], "-", color="k")
                plt.plot(ival, scale(values["observed"]), "o", color="k")

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
        self.set_cms_labels(plt, ax)
        plt.text(0.5, 0.95, inner_text, transform=ax.transAxes, ha="center")
        if True:
            plt.yscale('log')
        plt.savefig(output_file, bbox_inches='tight')

        plt.close('all')

    def run(self):
        inputs = self.input()
        for feature in self.requires()["combined"].features:
            for ip, process_group_name in enumerate(self.process_group_names):
                results = OrderedDict()
                for ic, category_name in enumerate(self.fit_config[process_group_name].keys()):
                    with open(inputs["cat"][process_group_name][category_name][feature.name].path) as f:
                        results[category_name] = json.load(f)
                with open(inputs["combined"][process_group_name][feature.name].path) as f:
                    results["Combined"] = json.load(f)

                self.plot(results, create_file_dir(
                    self.output()[process_group_name][feature.name].path),
                    inner_text=self.config.processes.get(process_group_name).label.latex)


class BDTOptimizationDQCD(PlotCombineDQCD):
    plot_fits = luigi.BoolParameter(default=True, description="whether to plot signal-background "
        "distributions per category, default: True")

    combine_categories = True  # for the output tag

    category_names = [
        # "singlev_cat1",
        "singlev_cat1", "singlev_cat2", "singlev_cat3",
        "singlev_cat4", "singlev_cat5", "singlev_cat6",
        "multiv_cat1", "multiv_cat2", "multiv_cat3",
        "multiv_cat4", "multiv_cat5", "multiv_cat6",
    ]

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
        output = {
            "bdt": {
                category_name: {
                    ext: self.local_target(f"bdt/plot__{category_name}.{ext}")
                    for ext in ["png", "pdf"]
                }
                for category_name in self.category_names + ["combined"]
            },
        }
        if self.plot_fits:
            output["distributions"] = {
                category_name: {
                    pgn: {
                        f.name: {
                            ext: self.local_target(
                                f"distributions/{category_name}/{pgn}/{f.name}__{category_name}__{pgn}.{ext}")
                            for ext in ["png", "pdf"]
                        } for f in self.features
                    } for pgn in self.process_group_names
                } for category_name in self.category_names
            }
        return output

    def get_bdt_cut(self, feature_name):
        if "bdt" in feature_name:
            return feature_name.split("_")[-1].replace("p", ".")
        else:
            return "0"

    def plot(self, results, output_file, inner_text=None):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        plt.rcParams['text.usetex'] = True

        ax = plt.subplot()

        for pgn in results.keys():
            plt.plot(range(len(results[pgn].keys())), results[pgn].values(),
                label=self.config.processes.get(pgn).label.latex)
        ax.set_xticks(list(range(len(list(results.values())[0].keys()))))
        ax.set_xticklabels(
            [f"BDT $>$ {self.get_bdt_cut(key)}" for key in list(results.values())[0].keys()],
            rotation=60, rotation_mode="anchor", ha="right")

        plt.ylabel(self.get_y_axis_label(self.fit_config_file))
        plt.text(0, 1.01, r"\textbf{CMS} \textit{Private Work}", transform=ax.transAxes)
        plt.text(1., 1.01, r"%s Simulation, %s fb${}^{-1}$" % (
            self.config.year, self.config.lumi_fb),
            transform=ax.transAxes, ha="right")
        plt.text(0.5, 0.95, inner_text, transform=ax.transAxes, ha="center")
        legend = plt.legend()
        if True:
            plt.yscale('log')
        plt.savefig(create_file_dir(output_file["pdf"].path), bbox_inches='tight')
        plt.savefig(create_file_dir(output_file["png"].path), bbox_inches='tight')
        plt.close('all')

    def run(self):
        ROOT = import_root()

        def scale(val):
            return val * 0.01

        inputs = self.input()
        for ic, category_name in enumerate(self.category_names):
            results = {}
            for ip, process_group_name in enumerate(self.process_group_names):
                results[process_group_name] = OrderedDict()
                for feature in self.features:
                    with open(inputs["cat"][process_group_name]["collection"].targets[ic][feature.name].path) as f:
                        results[process_group_name][feature.name] = scale(json.load(f)["50.0"])
            self.plot(results, self.output()["bdt"][category_name],
                inner_text=self.config.categories.get(category_name).label)

        results = {}
        for ip, process_group_name in enumerate(self.process_group_names):
            results[process_group_name] = OrderedDict()
            for feature in self.features:
                with open(inputs["combined"]["collection"].targets[ip][feature.name].path) as f:
                    results[process_group_name][feature.name] = scale(json.load(f)["50.0"])
        self.plot(results, self.output()["bdt"]["combined"], inner_text="Combined categories")


        # distributions
        for ic, category_name in enumerate(self.category_names):
            for ip, process_group_name in enumerate(self.process_group_names):
                for f in self.features:
                    t = self.requires()["cat"][process_group_name].requires()["data"].requires()\
                        ["data"].requires()["data"][category_name].requires()["fits"]["data"]
                    p = self.requires()["cat"][process_group_name].requires()["data"].requires()\
                        ["data"].requires()["data"][category_name].input()["fits"]["data"]\
                        [f.name]["root"].path
                    model_tf = ROOT.TFile.Open(p)
                    w = model_tf.Get("workspace_data")
                    # w = model_tf.Get("workspace_SIGNALPROCESS")
                    data_obs = w.data("data_obs")

                    x_data, blind = self.get_x(t.x_range, t.blind_range)
                    frame = x_data.frame()
                    # if not blind:
                    nlowerbins, nupperbins = 0, 0
                    for ib in range(f.binning[0]):
                        bin_center = (f.binning[1] +
                            ((2 * ib + 1) / 2.) * (f.binning[2] - f.binning[1]) / (f.binning[0]))
                        if bin_center >= float(t.x_range[0]) and \
                                bin_center < float(t.blind_range[0]):
                            nlowerbins += 1
                        elif bin_center <= float(t.x_range[1]) and \
                                bin_center > float(t.blind_range[1]):
                            nupperbins += 1
                    x_data.setBins(nlowerbins, "loSB")
                    x_data.setBins(nupperbins, "hiSB")
                    data_obs.plotOn(frame, Name="data_lower_sideband", Binning="loSB")
                    data_obs.plotOn(frame, Name="data_higer_sideband", Binning="hiSB")

                    # model_data = w.pdf("model_data")
                    # model_data.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlack), ROOT.RooFit.Name(f"Data"))

                    p_signal = self.requires()["cat"][process_group_name].requires()["data"].requires()\
                        ["data"].requires()["data"][category_name].input()["fits"][process_group_name]\
                        [f.name]["root"].path
                    model_tf_signal = ROOT.TFile.Open(p_signal)
                    w_signal = model_tf_signal.Get(f"workspace_{process_group_name}")
                    signal_data = w_signal.data("data_obs")
                    signal_pdf = w_signal.pdf(f"model_{process_group_name}")
                    # frame_signal = x_data.frame()
                    signal_data.plotOn(frame, ROOT.RooFit.MarkerColor(ROOT.kRed),
                        ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name(f"Signal"), ROOT.RooFit.Rescale(100.))
                    signal_pdf.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Normalization(100.))

                    c = ROOT.TCanvas()
                    frame.Draw("sames")
                    # frame_signal.Draw("sames")
                    c.SaveAs(create_file_dir(self.output()["distributions"][category_name]\
                        [process_group_name][f.name]["pdf"].path))
