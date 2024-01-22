import json
import luigi

from cmt.base_tasks.plotting import FeaturePlot
from cmt.base_tasks.analysis import Fit

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
        reqs["tight"] = FeaturePlot.req(self, category_name="base", region_name=self.tight_region,
            save_yields=True, save_pdf=False, _exclude=['include_fit', 'counting'])
        reqs["loose"] = FeaturePlot.req(self, category_name="base", region_name=self.loose_region,
            save_yields=True, save_pdf=False, _exclude=['include_fit', 'counting'])

        return reqs

    def run(self):
        inputs = self.input()
        assert self.feature_names == ("muonSV_bestchi2_mass",)
        with open(inputs["tight"]["yields"].targets["muonSV_bestchi2_mass"].path) as f:
            d_tight = json.load(f)
        with open(inputs["loose"]["yields"].targets["muonSV_bestchi2_mass"].path) as f:
            d_loose = json.load(f)

        self.additional_scaling = {"background": d_tight["background"]["Total yield"] /\
            d_loose["background"]["Total yield"]}

        super(FeaturePlotDQCD, self).run()
