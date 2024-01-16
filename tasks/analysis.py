import json
import luigi

from cmt.base_tasks.analysis import Fit, CreateDatacards


class CreateDatacardsDQCD(CreateDatacards):
    tight_region = luigi.Parameter(default="tight_bdt", description="region_name with the "
        "tighter bdt cut, default: tight_bdt")
    loose_region = luigi.Parameter(default="loose_bdt", description="region_name with the "
        "looser bdt cut, default: loose_bdt")

    def __init__(self, *args, **kwargs):
        super(CreateDatacardsDQCD, self).__init__(*args, **kwargs)

    def requires(self):
        reqs = CreateDatacards.requires(self)
        for process in reqs:
            if process == "background":
                reqs[process].region_name = self.loose_region
            else:
                reqs[process].region_name = self.tight_region

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
                        "region_name=self.tight_region, feature_names=self.feature_names)")
                    reqs["loose"] =  eval(f"Fit.vreq(self, {params}, _exclude=['include_fit'], "
                        "region_name=self.loose_region, feature_names=self.feature_names)")
        return reqs

    def run(self):
        inputs = self.input()
        assert self.feature_names == ("muonSV_bestchi2_mass",)
        print(inputs["tight"])
        with open(inputs["tight"]["muonSV_bestchi2_mass"]["json"].path) as f:
            d_tight = json.load(f)
        with open(inputs["loose"]["muonSV_bestchi2_mass"]["json"].path) as f:
            d_loose = json.load(f)

        self.additional_scaling = {"background": d_tight[""]["integral"] /\
            d_loose[""]["integral"]}

        super(CreateDatacardsDQCD, self).run()
