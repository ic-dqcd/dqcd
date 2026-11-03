import os
import re
import json
from analysis_tools.utils import import_root

ROOT = import_root()


class DQCDLumiMaskRDFProducer():
    """Golden-JSON lumisection mask, applied to data only (MC passes through untouched).

    The certification JSON is passed from the yaml module block, so the input lives in the dqcd
    repo (data/lumi/) and another year is another yaml block, not new code:

        lumimask:
            name: DQCDLumiMaskRDF
            path: modules.lumi_mask
            parameters:
                isMC: self.dataset.process.isMC
                jsonFile: ${CMT_BASE}/../data/lumi/<file>.json

    Filters on (run, luminosityBlock): an event is kept if its run is in the JSON and its
    lumisection falls in one of the certified [first, last] ranges (inclusive). The mask must be
    lumisection-level: 29% of the 2024 runs are certified as several disjoint intervals
    (_tools/goldenjson.py, which implements the same rule for the standalone studies).
    """
    def __init__(self, *args, **kwargs):
        self.isMC = kwargs.pop("isMC")
        self.jsonFile = os.path.expandvars(kwargs.pop("jsonFile"))

        if self.isMC:
            return

        if not os.path.isfile(self.jsonFile):
            raise FileNotFoundError(f"DQCDLumiMaskRDFProducer: golden JSON not found: {self.jsonFile}")

        self.tag = re.sub(r"\W", "_", os.path.splitext(os.path.basename(self.jsonFile))[0])

        if not os.getenv("_DQCDLumiMask"):
            os.environ["_DQCDLumiMask"] = "DQCDLumiMask"
            ROOT.gInterpreter.Declare("""
                #include <map>
                #include <vector>
                #include <utility>
                using dqcd_lumi_map_t = std::map<unsigned int, std::vector<std::pair<unsigned int, unsigned int>>>;
                bool dqcd_pass_golden(unsigned int run, unsigned int ls, const dqcd_lumi_map_t& cert) {
                    auto it = cert.find(run);
                    if (it == cert.end())
                        return false;
                    for (const auto& range : it->second)
                        if (ls >= range.first && ls <= range.second)
                            return true;
                    return false;
                }
            """)

        if not os.getenv(f"_DQCDLumiMask_{self.tag}"):
            os.environ[f"_DQCDLumiMask_{self.tag}"] = "DQCDLumiMask"
            with open(self.jsonFile) as f:
                cert = json.load(f)
            entries = ", ".join(
                "{%d, {%s}}" % (int(run), ", ".join("{%d, %d}" % (int(lo), int(hi)) for lo, hi in ranges))
                for run, ranges in sorted(cert.items(), key=lambda x: int(x[0])))
            ROOT.gInterpreter.Declare(
                f"const dqcd_lumi_map_t dqcd_lumi_map_{self.tag} = {{{entries}}};")

    def run(self, df):
        if self.isMC:
            return df, []
        df = df.Filter(f"dqcd_pass_golden(run, luminosityBlock, dqcd_lumi_map_{self.tag})", "Golden JSON")
        return df, []


def DQCDLumiMaskRDF(*args, **kwargs):
    return lambda: DQCDLumiMaskRDFProducer(*args, **kwargs)
