from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.legacy_2018 import Config as legacy_config


class Config(legacy_config):

    def add_regions(self, **kwargs):
        regions = [
            Category("loose_bdt", "Loose bdt region", selection="{{bdt}} > 0.45"),
            Category("tight_bdt", "Tight bdt region", selection="{{bdt}} > 0.99"),
                ]
        return ObjectCollection(regions)

    def add_datasets(self):
        sample_path = "/vols/cms/mc3909/bparkProductionAll_V1p3/tmp/"

        samples = {
            "qcd_1000toInf": ("QCD_Pt-1000_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_120to170": ("QCD_Pt-120To170_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_15to20": ("QCD_Pt-15To20_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_170to300": ("QCD_Pt-170To300_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_20to30": ("QCD_Pt-20To30_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            # "qcd_20toInf": ("QCD_Pt-20toInf_MuEnrichedPt15_TuneCP5_13TeV_pythia8"
                # "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                # "_MINIAODSIM_v1p0_generationSync"),
            "qcd_300to470": ("QCD_Pt-300To470_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_30to50": ("QCD_Pt-30To50_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_470to600": ("QCD_Pt-470To600_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_50to80": ("QCD_Pt-50To80_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_600to800": ("QCD_Pt-600To800_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_800to1000": ("QCD_Pt-800To1000_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
            "qcd_80to120": ("QCD_Pt-80To120_MuEnrichedPt5_TuneCP5_13TeV-pythia8"
                "_RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2"
                "_MINIAODSIM_v1p1_generationSync"),
        }

        xs = {
            "qcd_15to20": 2799000,
            "qcd_20to30": 2526000,
            "qcd_30to50": 1362000,
            "qcd_50to80": 376600,
            "qcd_80to120": 88930,
            "qcd_120to170": 21230,
            "qcd_170to300": 7055,
            "qcd_300to470": 619,
            "qcd_470to600": 59.24,
            "qcd_600to800": 18.21,
            "qcd_800to1000": 3.275,
            "qcd_1000toInf": 1.078,
        }

        datasets = [
            Dataset("qcd_1000toInf",
                folder=sample_path + samples["qcd_1000toInf"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_1000toInf"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_1000toInf"),
                xs=xs["qcd_1000toInf"],
                merging={
                    "base": 10,
                },
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_120to170",
                folder=sample_path + samples["qcd_120to170"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_120to170"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_120to170"),
                xs=xs["qcd_120to170"],
                merging={
                    "base": 10,
                },
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_15to20",
                folder=sample_path + samples["qcd_15to20"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_15to20"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_15to20"),
                xs=xs["qcd_15to20"],
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_170to300",
                folder=sample_path + samples["qcd_170to300"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_170to300"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_170to300"),
                xs=xs["qcd_170to300"],
                merging={
                    "base": 10,
                },
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_20to30",
                folder=sample_path + samples["qcd_20to30"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_20to30"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_20to30"),
                xs=xs["qcd_20to30"],
                skipped_files_must_be_in_dataset=False,
            ),

            # Dataset("qcd_20toInf",
                # folder=sample_path + samples["qcd_20toInf"],
                # # skipFiles=["{}/output_{}.root".format(
                    # # sample_path + samples["qcd_20toInf"], i)
                    # # for i in range(1, 11)],
                # process=self.processes.get("qcd"),
                # xs=0.03105, # FIXME
                # friend_datasets="qcd_20toInf_friend"),
            # Dataset("qcd_20toInf_friend",
                # folder=bdt_path + samples["qcd_20toInf"],
                # process=self.processes.get("dum"),
                # xs=0.03105, # FIXME
                # tags=["friend"]),

            Dataset("qcd_300to470",
                folder=sample_path + samples["qcd_300to470"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_300to470"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_300to470"),
                xs=xs["qcd_300to470"],
                merging={
                    "base": 10,
                },
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_30to50",
                folder=sample_path + samples["qcd_30to50"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_30to50"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_30to50"),
                xs=xs["qcd_30to50"],
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_470to600",
                folder=sample_path + samples["qcd_470to600"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_470to600"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd"),
                xs=xs["qcd_470to600"],
                merging={
                    "base": 10,
                },
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_50to80",
                folder=sample_path + samples["qcd_50to80"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_50to80"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_50to80"),
                xs=xs["qcd_50to80"],
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_600to800",
                folder=sample_path + samples["qcd_600to800"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_600to800"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_600to800"),
                xs=xs["qcd_600to800"],
                merging={
                    "base": 10,
                },
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_80to120",
                folder=sample_path + samples["qcd_80to120"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_80to120"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_80to120"),
                xs=xs["qcd_80to120"],
                merging={
                    "base": 10,
                },
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_800to1000",
                folder=sample_path + samples["qcd_800to1000"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_800to1000"], i)
                    for i in range(1, 51)],
                process=self.processes.get("qcd_800to1000"),
                xs=xs["qcd_800to1000"],
                merging={
                    "base": 10,
                },
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("data_2018d_bph1",
                folder=[
                    sample_path + "ParkingBPH1_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p3_generationSync",
                    # sample_path + "ParkingBPH2_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p3_generationSync",
                    # sample_path + "ParkingBPH3_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                    # sample_path + "ParkingBPH4_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                ],
                process=self.processes.get("data"),
                merging={
                    "base": 20,
                },
                tags=["ul"],
                runPeriod="D",
            ),

            Dataset("data_2018d_bph1_1fb",
                folder=[
                    sample_path + "ParkingBPH1_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p3_generationSync",
                    # sample_path + "ParkingBPH2_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p3_generationSync",
                    # sample_path + "ParkingBPH3_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                    # sample_path + "ParkingBPH4_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                ],
                process=self.processes.get("data"),
                merging={
                    "base": 20,
                },
                tags=["ul"],
                runPeriod="D",
                file_pattern="output_(.{1}|.{2}|.{3}|10.{2}|1100|1101).root"
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_10",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_10/nanotron/231124_165003/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_0p1",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_0p1/nanotron/231124_165316/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_1p0",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_1p0/nanotron/231124_165335/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_100",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_100/nanotron/231124_165326/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_0p1",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_0p40_ctau_0p1/nanotron/231124_165240/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_1p0",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_0p40_ctau_1p0/nanotron/231124_165307/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_100",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_0p40_ctau_100/nanotron/231124_165258/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_10",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_0p40_ctau_10/nanotron/231124_165249/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_0p1",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_1_mA_0p33_ctau_0p1/nanotron/231124_165126/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_1p0",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_1_mA_0p33_ctau_1p0/nanotron/231124_165154/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_10",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_1_mA_0p33_ctau_10/nanotron/231124_165135/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),
     
            Dataset("scenarioA_mpi_1_mA_0p33_ctau_100",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_1_mA_0p33_ctau_100/nanotron/231124_165144/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_0p1",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_2_mA_0p67_ctau_0p1/nanotron/231124_165203/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_1p0",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_2_mA_0p67_ctau_1p0/nanotron/231124_165231/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_10",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_2_mA_0p67_ctau_10/nanotron/231124_165213/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_100",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_2_mA_0p67_ctau_100/nanotron/231124_165222/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_0p1",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_1p00_ctau_0p1/nanotron/231124_165012/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_1p0",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_1p00_ctau_1p0/nanotron/231124_165040/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_10",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_1p00_ctau_10/nanotron/231124_165021/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_100",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_1p00_ctau_100/nanotron/231124_165030/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_10_mA_3p33_ctau_0p1",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_3p33_ctau_0p1/nanotron/231124_165049/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioA_mpi_10_mA_3p33_ctau_1p0",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_3p33_ctau_1p0/nanotron/231124_165117/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),
            Dataset("scenarioA_mpi_10_mA_3p33_ctau_10",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_3p33_ctau_10/nanotron/231124_165058/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),
            Dataset("scenarioA_mpi_10_mA_3p33_ctau_100",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("signal"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_3p33_ctau_100/nanotron/231124_165108/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_10",
                folder="/vols/cms/jleonhol/samples/ul_pu_v3/scenarioB1_mpi_4_mA_1p33_ctau_10/",
                process=self.processes.get("signal"),
                file_pattern="nano_.*root",
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),
            Dataset("scenarioB2_mpi_4_mA_2p10_ctau_10",
                folder="/vols/cms/jleonhol/samples/ul_pu_v3/scenarioB2_mpi_4_mA_2p10_ctau_10/",
                process=self.processes.get("signal"),
                file_pattern="nano_.*root",
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),
            Dataset("scenarioC_mpi_10_mA_8p00_ctau_10",
                folder="/vols/cms/jleonhol/samples/ul_pu_v3/scenarioC_mpi_10_mA_8p00_ctau_10/",
                process=self.processes.get("signal"),
                file_pattern="nano_.*root",
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms"
            ),
            Dataset("hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1_new",
                folder="/vols/cms/jleonhol/samples/ul_pu/hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1/",
                process=self.processes.get("signal"),
                file_pattern="nano.root",
                tags=["ul"]
            ),
        ]
        return ObjectCollection(datasets)

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        weights.total_events_weights = ["puWeight"]
        # weights.total_events_weights = ["genWeight"]
        # weights.total_events_weights = ["1"]

        weights.base = ["puWeight", "PUjetID_SF", "idWeight", "trigSF"]  # others needed
        # weights.base = ["1"]  # others needed

        for category in self.categories:
            weights[category.name] = weights.base

        return weights

    # other methods

# config = Config("base", year=2018, ecm=13, lumi_pb=59741)
config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True, xrd_redir='gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms')
