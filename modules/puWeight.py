import os
from Corrections.LUM.puWeight import puWeightRDFProducer, puWeightDummyRDFProducer

# pufile_dataParking2018 = "%s/../modules/dataParkingPileupHistogram.root" % os.environ['CMT_BASE']
pufile_dataParking2018 = "%s/../modules/parking_pu2018.root" % os.environ['CMT_BASE']
pufile_mc2018 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/mcPileup2018.root" % os.environ[
    'CMSSW_BASE']

puWeight_parking2018RDF = lambda: puWeightRDFProducer(
    pufile_mc2018, pufile_dataParking2018, "pu_mc", "pileup", verbose=False, doSysVar=False)


def puWeightParkingRDF(**kwargs):
    isMC = kwargs.pop("isMC")
    year = int(kwargs.pop("year"))
    isUL = kwargs.pop("isUL")
    ul = "" if not isUL else "UL"

    if not isMC:
        return lambda: puWeightDummyRDFProducer()
    else:
        return eval("puWeight_parking%s%sRDF" % (ul, year))
