import os
import re
from analysis_tools.utils import import_root
from Corrections.LUM.puWeight import puWeightRDFProducer, puWeightDummyRDFProducer

ROOT = import_root()

# ---------------------------------------------------------------------------------------------
# Run 2 (2018): histogram-based weights (hand-derived parking PU profile)
# ---------------------------------------------------------------------------------------------
# pufile_dataParking2018 = "%s/../modules/dataParkingPileupHistogram.root" % os.environ['CMT_BASE']
# pufile_dataParking2018 = "%s/../modules/parking_pu2018.root" % os.environ['CMT_BASE']
pufile_dataParking2018 = "%s/../modules/data_parking18_with_var.root" % os.environ['CMT_BASE']
pufile_mc2018 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/mcPileup2018.root" % os.environ[
    'CMSSW_BASE']
puWeight_parking2018RDF = lambda: puWeightRDFProducer(
    pufile_mc2018, pufile_dataParking2018, "pu_mc", "pileup", verbose=False, doSysVar=True)

pufile_mcUL2018 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/mcPileupUL2018.root" % os.environ[
    'CMSSW_BASE']
puWeight_parkingUL2018RDF = lambda: puWeightRDFProducer(
    pufile_mcUL2018, pufile_dataParking2018, "pu_mc", "pileup", verbose=False, doSysVar=True)


# ---------------------------------------------------------------------------------------------
# Run 3 (2022-2026): correctionlib weights
# ---------------------------------------------------------------------------------------------
def _correctionlib_include_dir():
    """Directory holding correction.h (older correctionlib versions have no get_include())."""
    import subprocess
    try:
        import correctionlib
        inc = os.path.join(os.path.dirname(correctionlib.__file__), "include")
        if os.path.isfile(os.path.join(inc, "correction.h")):
            return inc
    except ImportError:
        pass
    inc = subprocess.run(["correction", "config", "--incdir"], capture_output=True, text=True,
        check=True).stdout.strip()
    if not os.path.isfile(os.path.join(inc, "correction.h")):
        raise FileNotFoundError("correctionlib include directory with correction.h not found")
    return inc


class puWeightRun3RDFProducer():
    """Pileup weights from a correctionlib json (Run 3).

    The correction file and its name are passed from the yaml module block, so the inputs live
    in the dqcd repo (data/pileup/) and a new year/era is a new yaml block, not new code:

        puweight:
            name: puWeightParkingRDF
            path: modules.puWeight
            parameters:
                isMC: self.dataset.process.isMC
                year: self.config.year
                isUL: self.config.get_aux('isUL', self.dataset.has_tag('ul'))
                fileName: ${CMT_BASE}/../data/pileup/<file>.json.gz
                corrName: <correction name inside the file>

    The correction must take inputs (NumTrueInteractions, weights in {nominal, up, down}), as the
    LUM POG / lum-corrections files do. Branches: puWeight, puWeightUp, puWeightDown -- the same
    names as the Run-2 histogram producer, so weights and the "pu" systematic (up="Up",
    down="Down") work unchanged. Data: no branches.
    """
    def __init__(self, *args, **kwargs):
        self.isMC = kwargs.pop("isMC")
        self.fileName = os.path.expandvars(kwargs.pop("fileName"))
        self.corrName = kwargs.pop("corrName")

        if not self.isMC:
            return

        if not os.path.isfile(self.fileName):
            raise FileNotFoundError(f"puWeightRun3RDFProducer: pileup file not found: {self.fileName}")

        # one evaluator per (file, correction): C++ identifiers built from the correction name
        self.tag = re.sub(r"\W", "_", self.corrName)

        # correction.h must be on the include path. setup.sh adds it (cmt_add_root_inc) but a
        # later `scramv1 runtime -sh` resets ROOT_INCLUDE_PATH, so register it here explicitly.
        if not os.getenv("_dqcd_correctionlib_inc"):
            os.environ["_dqcd_correctionlib_inc"] = "1"
            ROOT.gInterpreter.AddIncludePath(_correctionlib_include_dir())

        if not os.getenv("_corr"):
            os.environ["_corr"] = "_corr"
            if "/libBaseModules.so" not in ROOT.gSystem.GetLibraries():
                ROOT.gInterpreter.Load("libBaseModules.so")
            ROOT.gInterpreter.Declare(os.path.expandvars(
                '#include "$CMSSW_BASE/src/Base/Modules/interface/correctionWrapper.h"'))

        if not os.getenv(f"_dqcd_pu_{self.tag}"):
            os.environ[f"_dqcd_pu_{self.tag}"] = "_dqcd_pu"
            ROOT.gInterpreter.ProcessLine(
                f'auto dqcd_pu_corr_{self.tag} = MyCorrections("{self.fileName}", "{self.corrName}");')
            ROOT.gInterpreter.Declare(f"""
                Float_t dqcd_get_pu_weight_{self.tag}(Float_t NumTrueInteractions, std::string type) {{
                    return dqcd_pu_corr_{self.tag}.eval({{NumTrueInteractions, type}});
                }}
            """)

    def run(self, df):
        if not self.isMC:
            return df, []

        branches = []
        for suffix, syst in [("", "nominal"), ("Up", "up"), ("Down", "down")]:
            df = df.Define(f"puWeight{suffix}",
                f'dqcd_get_pu_weight_{self.tag}(Pileup_nTrueInt, "{syst}")')
            branches.append(f"puWeight{suffix}")
        return df, branches


def puWeightParkingRDF(**kwargs):
    isMC = kwargs.pop("isMC")
    year = int(kwargs.pop("year"))
    isUL = kwargs.pop("isUL", False)

    if year >= 2022:
        # Run 3: the correction file is configured in the yaml (fileName, corrName)
        if "fileName" not in kwargs or "corrName" not in kwargs:
            raise ValueError(f"puWeightParkingRDF: year {year} needs 'fileName' and 'corrName' "
                "parameters in the yaml module block (see puWeightRun3RDFProducer)")
        return lambda: puWeightRun3RDFProducer(isMC=isMC, **kwargs)

    ul = "" if not isUL else "UL"
    if not isMC:
        return lambda: puWeightDummyRDFProducer()
    else:
        return eval("puWeight_parking%s%sRDF" % (ul, year))
