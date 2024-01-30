import json
import luigi
from collections import OrderedDict
import numpy as np

from analysis_tools.utils import create_file_dir

from cmt.base_tasks.base import CategoryWrapperTask
from cmt.base_tasks.plotting import FeaturePlot
from cmt.base_tasks.analysis import Fit
from tasks.analysis import ScanCombineDQCD


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


class PlotCombineDQCD(ScanCombineDQCD):
    def requires(self):
        return ScanCombineDQCD.vreq(self)

    def output(self):
        return {
            feature.name: self.local_target("plot__{}__{}.pdf".format(
                feature.name, self.fit_config_file))
            for feature in self.features
        }

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
        ax.set_xticklabels(labels, rotation=60, rotation_mode="anchor", ha="right")

        plt.ylabel(r"95$\%$ CL on BR(H$\to\Psi\Psi$)")
        plt.text(0, 1.01, r"\textbf{CMS} \textit{Private Work}", transform=ax.transAxes)
        plt.text(1., 1.01, r"%s Simulation, %s fb${}^{-1}$" % (
            self.config.year, self.config.lumi_fb),
            transform=ax.transAxes, ha="right")
        if True:
            plt.yscale('log')
        plt.savefig(output_file, bbox_inches='tight')
        plt.close('all')

    def run(self):
        inputs = self.input()
        for feature in self.features:
            results = OrderedDict()
            for process_group_name in self.process_group_names:
                with open(inputs[process_group_name][feature.name].path) as f:
                    results[process_group_name] = json.load(f)
            self.plot(results, create_file_dir(self.output()[feature.name].path))
