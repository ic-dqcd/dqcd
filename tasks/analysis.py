import json
import luigi

from cmt.base_tasks.analysis import Fit, CreateDatacards, CombineDatacards


class CreateDatacardsDQCD(CreateDatacards):
    tight_region = luigi.Parameter(default="tight_bdt", description="region_name with the "
        "tighter bdt cut, default: tight_bdt")
    loose_region = luigi.Parameter(default="loose_bdt", description="region_name with the "
        "looser bdt cut, default: loose_bdt")

    def __init__(self, *args, **kwargs):
        super(CreateDatacardsDQCD, self).__init__(*args, **kwargs)
        assert "tight" in self.region_name

    def requires(self):
        reqs = CreateDatacards.requires(self)
        loose_region = self.region.name.replace("tight", "loose")
        for process in reqs["fits"]:
            if process == "background":
                reqs["fits"][process].region_name = loose_region
            else:
                reqs["fits"][process].region_name = self.region_name

        import yaml
        from cmt.utils.yaml_utils import ordered_load
        with open(self.retrieve_file("config/{}.yaml".format(self.fit_models))) as f:
            self.models = ordered_load(f, yaml.SafeLoader)
        for model, fit_params in self.models.items():
            if fit_params["process_name"] == "background":
                params = ", ".join([f"{param}='{value}'"
                    for param, value in fit_params.items() if param != "fit_parameters"])
                if "fit_parameters" in fit_params:
                    params += ", fit_parameters={" + ", ".join([f"'{param}': '{value}'"
                    for param, value in fit_params["fit_parameters"].items()]) + "}"

                    reqs["tight"] =  eval(f"Fit.vreq(self, {params}, _exclude=['include_fit'], "
                        "region_name=self.tight_region, feature_names=self.feature_names, "
                        "category_name='base')")
                    reqs["loose"] =  eval(f"Fit.vreq(self, {params}, _exclude=['include_fit'], "
                        "region_name=self.loose_region, feature_names=self.feature_names,"
                        "category_name='base')")
        return reqs

    def run(self):
        inputs = self.input()
        assert self.feature_names == ("muonSV_bestchi2_mass",)
        with open(inputs["tight"]["muonSV_bestchi2_mass"]["json"].path) as f:
            d_tight = json.load(f)
        with open(inputs["loose"]["muonSV_bestchi2_mass"]["json"].path) as f:
            d_loose = json.load(f)

        self.additional_scaling = {"background": d_tight[""]["integral"] /\
            d_loose[""]["integral"]}

        super(CreateDatacardsDQCD, self).run()


class CombineDatacardsDQCD(CombineDatacards):
    fit_config_file = luigi.Parameter(default="fit_config", description="file including "
        "fit configuration, default: fit_config.yaml")

    def requires(self):
        d = self.config.get_fit_config(self.fit_config_file)
        self.category_names = d[self.process_group_name].keys()
        return {
            category_name: CreateDatacardsDQCD.vreq(self, category_name=category_name,
                counting=d[self.process_group_name][category_name],
                _exclude=["category_names", "log_file"])
            for category_name in self.category_names
        }
