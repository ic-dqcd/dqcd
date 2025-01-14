import os
from analysis_tools.utils import import_root

ROOT = import_root()

class DQCDPrescaleWeight_RDFProducer():
    def __init__(self, *args, **kwargs):
        self.isMC = kwargs.pop("isMC")

        if self.isMC:
            if not os.getenv("_DQCDPrescaleWeight"):
                os.environ["_DQCDPrescaleWeight"] = "DQCDPrescaleWeight"
                ROOT.gInterpreter.Declare("""
                    float get_trigger_lumi_weight (bool L1_SingleMu7er1p5, bool L1_SingleMu8er1p5, bool L1_SingleMu9er1p5, bool L1_SingleMu10er1p5, bool L1_SingleMu12er1p5, bool HLT_Mu7_IP4_part0, bool HLT_Mu8_IP3_part0, bool HLT_Mu8_IP5_part0, bool HLT_Mu9_IP5_part0, bool HLT_Mu9_IP6_part0, bool HLT_Mu12_IP6_part0) {
                        float weight = 0.0;
                        if (L1_SingleMu12er1p5 * HLT_Mu12_IP6_part0) {
                            weight += 0.1953;
                        }
                        if (L1_SingleMu10er1p5 * HLT_Mu9_IP6_part0) {
                            weight += 0.2019;
                        }
                        if (L1_SingleMu10er1p5 * HLT_Mu9_IP5_part0) {
                            weight += 0.0394;
                        }
                        if (L1_SingleMu9er1p5 * HLT_Mu9_IP6_part0) {
                            weight += 0.0382;
                        }
                        if (L1_SingleMu9er1p5 * HLT_Mu9_IP5_part0) {
                            weight += 0.1252;
                        }
                        if (L1_SingleMu9er1p5 * HLT_Mu8_IP5_part0) {
                            weight += 0.0395;
                        }
                        if (L1_SingleMu8er1p5 * HLT_Mu9_IP6_part0) {
                            weight += 0.0421;
                        }
                        if (L1_SingleMu8er1p5 * HLT_Mu9_IP5_part0) {
                            weight += 0.0923;
                        }
                        if (L1_SingleMu8er1p5 * HLT_Mu8_IP5_part0) {
                            weight += 0.0402;
                        }
                        if (L1_SingleMu8er1p5 * HLT_Mu7_IP4_part0) {
                            weight += 0.0357;
                        }
                        if (L1_SingleMu7er1p5 * HLT_Mu8_IP3_part0) {
                            weight += 0.0192;
                        }
                        if (L1_SingleMu7er1p5 * HLT_Mu7_IP4_part0) {
                            weight += 0.1310;
                        }
                        return weight;
                    }
                """)

    def run(self, df):
        if not self.isMC:
            return df, []
        df = df.Define("prescaleWeight", """get_trigger_lumi_weight(
            L1_SingleMu7er1p5, L1_SingleMu8er1p5, L1_SingleMu9er1p5, L1_SingleMu10er1p5, L1_SingleMu12er1p5, HLT_Mu7_IP4_part0, HLT_Mu8_IP3_part0, HLT_Mu8_IP5_part0, HLT_Mu9_IP5_part0, HLT_Mu9_IP6_part0, HLT_Mu12_IP6_part0
        )""")
        return df, ["prescaleWeight"]


def DQCDPrescaleWeight_RDF(*args, **kwargs):
    return lambda: DQCDPrescaleWeight_RDFProducer(*args, **kwargs)