from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.legacy_2018 import Config as legacy_config

class Config(legacy_config):

    def add_regions(self, **kwargs):
        os_sel =  "muonSV_charge.at(min_chi2_index) == 0"
        ss_sel =  "muonSV_charge.at(min_chi2_index) != 0"
        bdt_scA_loose = "{{bdt_scenarioA}} <= 0.7"
        bdt_scA_tight = "{{bdt_scenarioA}} > 0.7"
        # bdt_scA_tight = "{{bdt_scenarioA}} > 0.98"
        chi2_loose = "{{muonSV_bestchi2_chi2}} > 5"
        chi2_tight = "{{muonSV_bestchi2_chi2}} <= 5"

        chi2_vvloose = "{{muonSV_bestchi2_chi2}} > 7.5"
        chi2_vloose = "{{muonSV_bestchi2_chi2}} > 5 && {{muonSV_bestchi2_chi2}} <= 7.5"

        regions = [
            Category("loose_bdt", "Loose bdt region", selection="{{bdt}} > 0.45"),
            Category("tight_bdt", "Tight bdt region", selection="{{bdt}} > 0.99"),

            Category("os", "OS region", selection=os_sel),
            Category("ss", "SS region", selection=ss_sel),
            Category("bdt_tight", "Tight bdt region", selection=bdt_scA_tight),
            Category("bdt_tight_nores", "Tight bdt region, no resonances",
                selection=jrs(bdt_scA_tight, "!" + self.resonance_mass_sel)),
            Category("bdt_loose", "Loose bdt region", selection=bdt_scA_loose),
            Category("chi2_tight", "Tight bdt region", selection=chi2_tight),
            Category("chi2_loose", "Loose bdt region", selection=chi2_loose),

            Category("os_loose", "OS, Loose bdt region", selection=jrs(bdt_scA_loose, os_sel)),
            Category("ss_loose", "SS, Loose bdt region", selection=jrs(bdt_scA_loose, ss_sel)),
            Category("os_tight", "OS, Tight bdt region", selection=jrs(bdt_scA_tight, os_sel)),
            Category("ss_tight", "SS, Tight bdt region", selection=jrs(bdt_scA_tight, ss_sel)),

            # Category("bdt_tight_chi2_loose", "BDT > 0.7, chi2 > 5", selection=jrs(chi2_loose, bdt_scA_tight)),
            # Category("bdt_loose_chi2_loose", "BDT <= 0.7, chi2 > 5", selection=jrs(chi2_loose, bdt_scA_loose)),
            # Category("bdt_tight_chi2_tight", "BDT > 0.7, chi2 <= 5", selection=jrs(chi2_tight, bdt_scA_tight)),
            # Category("bdt_loose_chi2_tight", "LBDT <= 0.7, chi2 <= 5", selection=jrs(chi2_tight, bdt_scA_loose)),
            # Category("bdt_tight_chi2_loose", "BDT > 0.7, chi2 > 7.5", selection=jrs(chi2_vvloose, bdt_scA_tight)),
            # Category("bdt_loose_chi2_loose", "BDT <= 0.7, chi2 > 7.5", selection=jrs(chi2_vvloose, bdt_scA_loose)),
            # Category("bdt_tight_chi2_tight", "BDT > 0.7, 5 < chi2 <= 7.5", selection=jrs(chi2_vloose, bdt_scA_tight)),
            # Category("bdt_loose_chi2_tight", "LBDT <= 0.7, 5 < chi2 <= 7.5", selection=jrs(chi2_vloose, bdt_scA_loose)),

            Category("bdt_tight_chi2_loose", "BDT > 0.7, chi2 > 7.5, no resonances",
                selection=jrs("!" + self.resonance_mass_sel, jrs(chi2_vvloose, bdt_scA_tight))),
            Category("bdt_loose_chi2_loose", "BDT <= 0.7, chi2 > 7.5, no resonances",
                selection=jrs("!" + self.resonance_mass_sel, jrs(chi2_vvloose, bdt_scA_loose))),
            Category("bdt_tight_chi2_tight", "BDT > 0.7, 5 < chi2 <= 7.5, no resonances",
                selection=jrs("!" + self.resonance_mass_sel, jrs(chi2_vloose, bdt_scA_tight))),
            Category("bdt_loose_chi2_tight", "LBDT <= 0.7, 5 < chi2 <= 7.5, no resonances",
                selection=jrs("!" + self.resonance_mass_sel, jrs(chi2_vloose, bdt_scA_loose))),

            Category("os_chi2_loose", "OS, Loose chi2 region", selection=jrs(chi2_loose, os_sel)),
            Category("ss_chi2_loose", "SS, Loose chi2 region", selection=jrs(chi2_loose, ss_sel)),
            Category("os_chi2_tight", "OS, Tight chi2 region", selection=jrs(chi2_tight, os_sel)),
            Category("ss_chi2_tight", "SS, Tight chi2 region", selection=jrs(chi2_tight, ss_sel)),

            Category("loose_bdt_scenarioA", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.7"),
            Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.98"),

            Category("bdt_scenarioA_0_0p2", "bdt (A) < 0.2 region",
                selection="{{bdt_scenarioA}} < 0.2"),
            Category("bdt_scenarioA_0p2_0p4", "0.2 < bdt (A) < 0.4 region",
                selection="{{bdt_scenarioA}} > 0.2 && {{bdt_scenarioA}} < 0.4"),
            Category("bdt_scenarioA_0p4_0p6", "0.4 < bdt (A) < 0.6 region",
                selection="{{bdt_scenarioA}} > 0.4 && {{bdt_scenarioA}} < 0.6"),
            Category("bdt_scenarioA_0p6_0p8", "0.6 < bdt (A) < 0.8 region",
                selection="{{bdt_scenarioA}} > 0.6 && {{bdt_scenarioA}} < 0.8"),
            Category("bdt_scenarioA_0p8_1p0", "0.8 < bdt (A) < 1.0 region",
                selection="{{bdt_scenarioA}} > 0.8 && {{bdt_scenarioA}} < 1.0"),

            Category("loose_bdt_scenarioB1", "Loose bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.6"),
            Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.98"),

            Category("loose_bdt_scenarioB2", "Loose bdt (B2) region", selection="{{bdt_scenarioB2}} > 0.55"),
            Category("tight_bdt_scenarioB2", "Tight bdt (B2) region", selection="{{bdt_scenarioB2}} > 0.92"),

            Category("loose_bdt_scenarioC", "Loose bdt (C) region", selection="{{bdt_scenarioC}} > 0.55"),
            Category("tight_bdt_scenarioC", "Tight bdt (C) region", selection="{{bdt_scenarioC}} > 0.8"),

            # for the new H->ZdZd samples, using scenario A since the signature in similar
            Category("loose_bdt_hzdzd", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.65"),
            Category("tight_bdt_hzdzd", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.98"),

            # for the new Z' samples, using scenario A since the signature in similar
            Category("loose_bdt_zprime", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.65"),
            Category("tight_bdt_zprime", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.98"),

            # for the vector portal samples, using dedicated BDT
            Category("loose_bdt_vector", "Loose bdt (VP) region", selection="{{bdt_vector}} > 0.6"),
            Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.993"),

            # for the B->PhiX samples
            Category("loose_bdt_btophi", "Loose bdt (B->PhiX) region", selection="{{bdt_scenarioA}} > 0.65"),
            Category("tight_bdt_btophi", "Tight bdt (B->PhiX) region", selection="{{bdt_scenarioA}} > 0.98"),
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

        # signal samples (only the latest ones)
        signal_samples = {
            "scenarioA_mpi_10_mA_2p00_ctau_0p1": "/scenarioA_mpi_10_mA_2p00_ctau_0p1/jleonhol-nanotron_ext_pp-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_10_mA_2p00_ctau_10": "/scenarioA_mpi_10_mA_2p00_ctau_10/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_10_mA_2p00_ctau_100": "/scenarioA_mpi_10_mA_2p00_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_10_mA_2p00_ctau_1p0": "/scenarioA_mpi_10_mA_2p00_ctau_1p0/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_10_mA_4p90_ctau_0p1": "/scenarioA_mpi_10_mA_4p90_ctau_0p1/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_10_mA_4p90_ctau_10": "/scenarioA_mpi_10_mA_4p90_ctau_10/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_10_mA_4p90_ctau_100": "/scenarioA_mpi_10_mA_4p90_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_10_mA_4p90_ctau_1p0": "/scenarioA_mpi_10_mA_4p90_ctau_1p0/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_1_mA_0p25_ctau_0p1": "/scenarioA_mpi_1_mA_0p25_ctau_0p1/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_1_mA_0p25_ctau_10": "/scenarioA_mpi_1_mA_0p25_ctau_10/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_1_mA_0p25_ctau_100": "/scenarioA_mpi_1_mA_0p25_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_1_mA_0p25_ctau_1p0": "/scenarioA_mpi_1_mA_0p25_ctau_1p0/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_1_mA_0p45_ctau_0p1": "/scenarioA_mpi_1_mA_0p45_ctau_0p1/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_1_mA_0p45_ctau_10": "/scenarioA_mpi_1_mA_0p45_ctau_10/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_1_mA_0p45_ctau_100": "/scenarioA_mpi_1_mA_0p45_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_1_mA_0p45_ctau_1p0": "/scenarioA_mpi_1_mA_0p45_ctau_1p0/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p25_ctau_0p1": "/scenarioA_mpi_2_mA_0p25_ctau_0p1/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p25_ctau_10": "/scenarioA_mpi_2_mA_0p25_ctau_10/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p25_ctau_100": "/scenarioA_mpi_2_mA_0p25_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p25_ctau_1p0": "/scenarioA_mpi_2_mA_0p25_ctau_1p0/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p40_ctau_0p1": "/scenarioA_mpi_2_mA_0p40_ctau_0p1/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p40_ctau_10": "/scenarioA_mpi_2_mA_0p40_ctau_10/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p40_ctau_100": "/scenarioA_mpi_2_mA_0p40_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p40_ctau_1p0": "/scenarioA_mpi_2_mA_0p40_ctau_1p0/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p90_ctau_0p1": "/scenarioA_mpi_2_mA_0p90_ctau_0p1/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p90_ctau_10": "/scenarioA_mpi_2_mA_0p90_ctau_10/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p90_ctau_100": "/scenarioA_mpi_2_mA_0p90_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_2_mA_0p90_ctau_1p0": "/scenarioA_mpi_2_mA_0p90_ctau_1p0/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_4_mA_0p80_ctau_0p1": "/scenarioA_mpi_4_mA_0p80_ctau_0p1/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_4_mA_0p80_ctau_10": "/scenarioA_mpi_4_mA_0p80_ctau_10/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_4_mA_0p80_ctau_100": "/scenarioA_mpi_4_mA_0p80_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_4_mA_0p80_ctau_1p0": "/scenarioA_mpi_4_mA_0p80_ctau_1p0/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_4_mA_1p90_ctau_0p1": "/scenarioA_mpi_4_mA_1p90_ctau_0p1/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_4_mA_1p90_ctau_10": "/scenarioA_mpi_4_mA_1p90_ctau_10/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_4_mA_1p90_ctau_100": "/scenarioA_mpi_4_mA_1p90_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
            "scenarioA_mpi_4_mA_1p90_ctau_1p0": "/scenarioA_mpi_4_mA_1p90_ctau_1p0/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
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

        signal_xs = 43.9 * 0.01

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
                process=self.processes.get("qcd_470to600"),
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
                    "singlev_cat3": 10
                },
                skipped_files_must_be_in_dataset=False,
            ),

            Dataset("data_2018d_bph1",
                dataset="/ParkingBPH1/jleonhol-nanotronv2-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 20,
                },
                tags=["ul"],
                runPeriod="D",
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
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
                # file_pattern="output_(.{1}|.{2}|.{3}|100.{1}|101.{1}|102.{1}|103.{1}|104.{1}|1050|1051|1052|1053).root"
                file_pattern="output_(.{1}|.{2}|.{3}|10.{2}|1100|1101).root"
            ),

            Dataset("data_2018d_bph1_1fb_v2",
                dataset="/ParkingBPH1/jleonhol-nanotronv2-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 20,
                },
                tags=["ul"],
                runPeriod="D",
                # file_pattern="output_(.{1}|.{2}|.{3}|100.{1}|101.{1}|102.{1}|103.{1}|104.{1}|1050|1051|1052|1053).root"
                file_pattern="nano_(.{1}|.{2}|.{3}|10.{2}|1100|1101).root",
                check_empty=False,
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_10",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_10_short"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_10/nanotron/231124_165003/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_0p1",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_0p1/nanotron/231124_165316/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_1p0",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_1p0/nanotron/231124_165335/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_100",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_100_short"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_100/nanotron/231124_165326/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_0p1",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_0p40_ctau_0p1/nanotron/231124_165240/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_1p0",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_0p40_ctau_1p0/nanotron/231124_165307/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_100",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_0p40_ctau_100/nanotron/231124_165258/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_10",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_0p40_ctau_10/nanotron/231124_165249/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_0p1",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_1_mA_0p33_ctau_0p1/nanotron/231124_165126/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_1p0",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_1_mA_0p33_ctau_1p0/nanotron/231124_165154/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_10",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_1_mA_0p33_ctau_10/nanotron/231124_165135/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),
     
            Dataset("scenarioA_mpi_1_mA_0p33_ctau_100",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_1_mA_0p33_ctau_100/nanotron/231124_165144/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_0p1",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_2_mA_0p67_ctau_0p1/nanotron/231124_165203/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_1p0",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_2_mA_0p67_ctau_1p0/nanotron/231124_165231/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_10",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_2_mA_0p67_ctau_10/nanotron/231124_165213/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_100",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_2_mA_0p67_ctau_100/nanotron/231124_165222/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_0p1",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_1p00_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_1p00_ctau_0p1/nanotron/231124_165012/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_1p0",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_1p00_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_1p00_ctau_1p0/nanotron/231124_165040/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_10",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_1p00_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_1p00_ctau_10/nanotron/231124_165021/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_100",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_1p00_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_1p00_ctau_100/nanotron/231124_165030/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_10_mA_3p33_ctau_0p1",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_3p33_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_3p33_ctau_0p1/nanotron/231124_165049/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_10_mA_3p33_ctau_1p0",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_3p33_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_3p33_ctau_1p0/nanotron/231124_165117/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),
            Dataset("scenarioA_mpi_10_mA_3p33_ctau_10",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_3p33_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_3p33_ctau_10/nanotron/231124_165058/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),
            Dataset("scenarioA_mpi_10_mA_3p33_ctau_100",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_3p33_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_10_mA_3p33_ctau_100/nanotron/231124_165108/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_10_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_10"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_10_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext_p-0e3002d4b7c03a7b205e938b78dcfab2/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_10_rew"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew", "rewtest"],
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_8p0_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_8p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_5p0_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_5p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_2p0_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_2p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_3p33_rew_large_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_3p33_large"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_3p33_rew_small_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_1p0/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_3p33_small"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_1p0_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_1p0/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_1p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_1p0_ext_new",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_1p0/jleonhol-nanotron_ext_pp-0e3002d4b7c03a7b205e938b78dcfab2/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_1p0"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "new"]
            # ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_1p0_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_1p0_rew"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["rew", "ext", "rewtest"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_0p1_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_0p1/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_0p1"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_0p1_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_1p0/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_0p1_rew"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew", "rewtest"]
            ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_0p1_rew_ext_new",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_1p0/jleonhol-nanotron_ext_pp-0e3002d4b7c03a7b205e938b78dcfab2/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_0p1_rew"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew", "new"]
            # ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_100_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_100"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_33p3_rew_large_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_33p3_large"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_33p3_rew_small_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_33p3_small"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_0p1_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_0p1/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_0p1"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_20_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_20"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_50_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_50"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_80_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_80"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_1p0_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_1p0/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_1p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_10_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_10"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_8p0_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_8p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_5p0_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_5p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_2p0_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_2p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_100_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_100"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_80_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_80"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_50_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_50"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_20_rew_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_20"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext", "rew"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_0p1_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_0p1/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_0p1"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_1p0_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_1p0/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_1p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_10_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_10"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_100_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_100"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_0p1_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_0p1/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_0p1"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_1p0_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_1p0/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_1p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_10_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_10"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_100_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_100"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_0p1_ext",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_0p1/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_1p00_ctau_0p1"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_1p0_ext",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_1p0/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_1p00_ctau_1p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_10_ext",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_1p00_ctau_10"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_10_mA_1p00_ctau_100_ext",
                dataset = "/scenarioA_mpi_10_mA_1p00_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_1p00_ctau_100"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_10_mA_3p33_ctau_0p1_ext",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_0p1/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_3p33_ctau_0p1"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_10_mA_3p33_ctau_1p0_ext",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_1p0/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_3p33_ctau_1p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_10_mA_3p33_ctau_10_ext",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_3p33_ctau_10"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_10_mA_3p33_ctau_100_ext",
                dataset = "/scenarioA_mpi_10_mA_3p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_10_mA_3p33_ctau_100"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_0p1",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_1_mA_0p33_ctau_0p1/nanotron/231208_161423/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_10",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_1_mA_0p33_ctau_10/nanotron/231219_105434/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_100",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_1_mA_0p33_ctau_100/nanotron/231219_105447/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_1p0",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_1_mA_0p33_ctau_1p0/nanotron/231219_105458/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),
            
            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_0p1",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_2_mA_0p40_ctau_0p1/nanotron/231219_105511/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_10",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_2_mA_0p40_ctau_10/nanotron/231208_161434/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_100",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_2_mA_0p40_ctau_100/nanotron/231219_105523/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_1p0",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_2_mA_0p40_ctau_1p0/nanotron/231219_105534/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_0p1",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_2_mA_0p67_ctau_0p1/nanotron/231219_105545/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_10",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_2_mA_0p67_ctau_10/nanotron/231219_105556/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_100",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_2_mA_0p67_ctau_100/nanotron/231208_161443/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_1p0",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_2_mA_0p67_ctau_1p0/nanotron/231219_105607/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_0p80_ctau_0p1",
                dataset = "/scenarioB1_mpi_4_mA_0p80_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_0p80_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_4_mA_0p80_ctau_0p1/nanotron/231219_105618/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_0p80_ctau_10",
                dataset = "/scenarioB1_mpi_4_mA_0p80_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_0p80_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_4_mA_0p80_ctau_10/nanotron/231219_105629/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_0p80_ctau_100",
                dataset = "/scenarioB1_mpi_4_mA_0p80_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_0p80_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_4_mA_0p80_ctau_100/nanotron/231219_105640/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_0p80_ctau_1p0",
                dataset = "/scenarioB1_mpi_4_mA_0p80_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_0p80_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_4_mA_0p80_ctau_1p0/nanotron/231207_155247/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_0p1",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_0p1"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_4_mA_1p33_ctau_0p1/nanotron/231219_105652/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_10",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_10"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_4_mA_1p33_ctau_10/nanotron/231219_105703/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_100",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_100"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_4_mA_1p33_ctau_100/nanotron/231219_105715/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_1p0",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_1p0"),
                check_empty=False,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioB1_mpi_4_mA_1p33_ctau_1p0/nanotron/231219_105726/0000/nano_{i}.root"
                    for i in range(1, 21)],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_1_mA_0p60_ctau_0p1",
                dataset = "/scenarioB2_mpi_1_mA_0p60_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_1_mA_0p60_ctau_0p1"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_1_mA_0p60_ctau_10",
                dataset = "/scenarioB2_mpi_1_mA_0p60_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_1_mA_0p60_ctau_10"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_1_mA_0p60_ctau_100",
                dataset = "/scenarioB2_mpi_1_mA_0p60_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_1_mA_0p60_ctau_100"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_1_mA_0p60_ctau_1p0",
                dataset = "/scenarioB2_mpi_1_mA_0p60_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_1_mA_0p60_ctau_1p0"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_2_mA_1p10_ctau_0p1",
                dataset = "/scenarioB2_mpi_2_mA_1p10_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_2_mA_1p10_ctau_0p1"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_2_mA_1p10_ctau_10",
                dataset = "/scenarioB2_mpi_2_mA_1p10_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_2_mA_1p10_ctau_10"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_2_mA_1p10_ctau_100",
                dataset = "/scenarioB2_mpi_2_mA_1p10_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_2_mA_1p10_ctau_100"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_2_mA_1p10_ctau_1p0",
                dataset = "/scenarioB2_mpi_2_mA_1p10_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_2_mA_1p10_ctau_1p0"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_4_mA_2p10_ctau_0p1",
                dataset = "/scenarioB2_mpi_4_mA_2p10_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_4_mA_2p10_ctau_0p1"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_4_mA_2p10_ctau_10",
                dataset = "/scenarioB2_mpi_4_mA_2p10_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_4_mA_2p10_ctau_10"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_4_mA_2p10_ctau_100",
                dataset = "/scenarioB2_mpi_4_mA_2p10_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_4_mA_2p10_ctau_100"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB2_mpi_4_mA_2p10_ctau_1p0",
                dataset = "/scenarioB2_mpi_4_mA_2p10_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioB2_mpi_4_mA_2p10_ctau_1p0"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),
    
            Dataset("scenarioC_mpi_10_mA_8p00_ctau_0p1",
                dataset = "/scenarioC_mpi_10_mA_8p00_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_10_mA_8p00_ctau_0p1"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),
            
            Dataset("scenarioC_mpi_10_mA_8p00_ctau_10",
                dataset = "/scenarioC_mpi_10_mA_8p00_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_10_mA_8p00_ctau_10"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),
           
            Dataset("scenarioC_mpi_10_mA_8p00_ctau_100",
                dataset = "/scenarioC_mpi_10_mA_8p00_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_10_mA_8p00_ctau_100"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioC_mpi_10_mA_8p00_ctau_1p0",
                dataset = "/scenarioC_mpi_10_mA_8p00_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_10_mA_8p00_ctau_1p0"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioC_mpi_2_mA_1p60_ctau_0p1",
                dataset = "/scenarioC_mpi_2_mA_1p60_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_2_mA_1p60_ctau_0p1"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioC_mpi_2_mA_1p60_ctau_10",
                dataset = "/scenarioC_mpi_2_mA_1p60_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_2_mA_1p60_ctau_10"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioC_mpi_2_mA_1p60_ctau_100",
                dataset = "/scenarioC_mpi_2_mA_1p60_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_2_mA_1p60_ctau_100"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioC_mpi_2_mA_1p60_ctau_1p0",
                dataset = "/scenarioC_mpi_2_mA_1p60_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_2_mA_1p60_ctau_1p0"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioC_mpi_4_mA_3p20_ctau_0p1",
                dataset = "/scenarioC_mpi_4_mA_3p20_ctau_0p1/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_4_mA_3p20_ctau_0p1"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioC_mpi_4_mA_3p20_ctau_10",
                dataset = "/scenarioC_mpi_4_mA_3p20_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_4_mA_3p20_ctau_10"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioC_mpi_4_mA_3p20_ctau_100",
                dataset = "/scenarioC_mpi_4_mA_3p20_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_4_mA_3p20_ctau_100"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioC_mpi_4_mA_3p20_ctau_1p0",
                dataset = "/scenarioC_mpi_4_mA_3p20_ctau_1p0/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                process=self.processes.get("scenarioC_mpi_4_mA_3p20_ctau_1p0"),
                check_empty=False,
                skipFiles=[],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            #Dataset("hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1_new",
                #folder="/vols/cms/jleonhol/samples/ul_pu/hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1/",
                #process=self.processes.get("signal"),
                #file_pattern="nano.root",
                #tags=["ul"],
                #xs=signal_xs
            #),

            Dataset("hzdzd_mzd_8_ctau_1",
                dataset="/HToZdZdTo2Mu2X_MZd-8_ctau-1mm_TuneCP5_13TeV_powheg2_JHUGenV738_pythia8/jleonhol-nanotronv1-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("hzdzd_mzd_8_ctau_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("hzdzd_mzd_8_ctau_100",
                dataset="/HToZdZdTo2Mu2X_MZd-8_ctau-100mm_TuneCP5_13TeV_powheg2_JHUGenV738_pythia8/jleonhol-nanotronv1-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("hzdzd_mzd_8_ctau_100"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),
            
            #Dataset("qcd_15to7000",
                #dataset="/QCD_Pt-15to7000_TuneCP5_Flat2018_13TeV_pythia8/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                #process=self.processes.get("qcd_15to7000"),
                #check_empty=False,
                #skipFiles=[],
                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                #xs=1315000000
            #),

            Dataset("zprime_mpi_2_ctau_10",
                dataset="/testZPrime_ctau10/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("zprime_mpi_2_ctau_10"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_100_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_100_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_10_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_10_ctau_100_xiO_1_xiL_1/nanotron/240227_131223/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),  

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_10_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_10_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_10_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_10_ctau_10_xiO_1_xiL_1/nanotron/240227_131233/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),     

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_1_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_1_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_10_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_10_ctau_1_xiO_1_xiL_1/nanotron/240227_131243/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_500_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_500_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_10_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_10_ctau_500_xiO_1_xiL_1/nanotron/240227_131253/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_50_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_50_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_10_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_10_ctau_50_xiO_1_xiL_1/nanotron/240227_131303/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_100_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_100_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_15_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_15_ctau_100_xiO_1_xiL_1/nanotron/240227_131313/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_10_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_10_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_15_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_15_ctau_10_xiO_1_xiL_1/nanotron/240227_131324/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_1_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_1_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_15_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_15_ctau_1_xiO_1_xiL_1/nanotron/240227_131334/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_500_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_500_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_15_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_15_ctau_500_xiO_1_xiL_1/nanotron/240227_131344/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_50_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_50_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_15_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_15_ctau_50_xiO_1_xiL_1/nanotron/240227_131354/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_100_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_100_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_20_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_20_ctau_100_xiO_1_xiL_1/nanotron/240227_131404/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_10_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_10_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_20_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_20_ctau_10_xiO_1_xiL_1/nanotron/240227_131414/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),
            
            Dataset("hiddenValleyGridPack_vector_m_20_ctau_1_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_1_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_20_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_20_ctau_1_xiO_1_xiL_1/nanotron/240227_131425/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),
 
            Dataset("hiddenValleyGridPack_vector_m_20_ctau_500_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_500_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_20_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_20_ctau_500_xiO_1_xiL_1/nanotron/240227_131435/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_50_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_50_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_20_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_20_ctau_50_xiO_1_xiL_1/nanotron/240227_131445/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_100_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_100_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_2_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_2_ctau_100_xiO_1_xiL_1/nanotron/240227_131456/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_2_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1/nanotron/240227_131506/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_1_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_1_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_2_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_2_ctau_1_xiO_1_xiL_1/nanotron/240227_131516/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_500_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_500_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_2_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_2_ctau_500_xiO_1_xiL_1/nanotron/240227_131527/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_50_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_50_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_2_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_2_ctau_50_xiO_1_xiL_1/nanotron/240227_131537/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_100_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_100_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_5_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_5_ctau_100_xiO_1_xiL_1/nanotron/240227_131547/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_10_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_10_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_5_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_5_ctau_10_xiO_1_xiL_1/nanotron/240227_131557/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_1_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_1_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_5_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_5_ctau_1_xiO_1_xiL_1/nanotron/240227_131606/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_500_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_500_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_5_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_5_ctau_500_xiO_1_xiL_1/nanotron/240227_131616/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_50_xiO_1_xiL_1",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_50_xiO_1_xiL_1/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("vector_m_5_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/hiddenValleyGridPack_vector_m_5_ctau_50_xiO_1_xiL_1/nanotron/240227_131627/0000/nano_{i}.root"
                    for i in range(1, 21)],
            ),

            Dataset("BuToJpsiK",
                dataset = "/BuToJpsiK_BMuonFilter_SoftQCDnonD_TuneCP5_13TeV-pythia8-evtgen/jleonhol-BuToKJPsiMC-f7d89a2f103706ffd8ab9007e324774d/USER",
                process=self.processes.get("BuToJpsiK"),
                check_empty=False,
            ),

            Dataset("btophi_m_2_ctau_10",
                dataset = "/btophi_m_2_ctau_10/jleonhol-nanotron-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("btophi_m_2_ctau_10"),
                check_empty=False,
                tags=["ul"],
                # xs=8.293e+07,
                xs=1.,
            ),

            # Dataset("vector_test",
                # folder="/vols/cms/khl216/bparkProductionAll_V1p3/hiddenValleyGridPack_vector_m_10_ctau_100_xiO_1_xiL_1/",
                # process=self.processes.get("vector_m_10_ctau_100_xiO_1_xiL_1"),
                # check_empty=False,
                # tags=["ul"],
                # xs=signal_xs,
                # skipFiles=[f"/vols/cms/khl216/bparkProductionAll_V1p3/hiddenValleyGridPack_vector_m_10_ctau_100_xiO_1_xiL_1/data_{i}.root"
                    # for i in range(0, 21)],
            # ),
        ]

        for name, dataset in signal_samples.items():
            datasets.append(self.create_signal_dataset(name + "_ext", dataset, signal_xs,
                tags=["ext", "ul"]))
            if name.endswith("10"):
                input_ctau = "ctau_10"
                ctaus = ["2p0", "5p0", "8p0"]
            elif name.endswith("100"):
                input_ctau = "ctau_100"
                ctaus = ["20", "50", "80"]
            else:
                ctaus = []
            for ctau in ctaus:
                datasets.append(self.create_signal_dataset(
                    name.replace(input_ctau, "ctau_%s_rew" % ctau) + "_ext",
                    dataset, signal_xs, tags=["ext", "ul", "rew"]))

        return ObjectCollection(datasets)

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        weights.total_events_weights = ["puWeight", "filter_efficiency"]
        # weights.total_events_weights = ["genWeight"]
        # weights.total_events_weights = ["1"]

        # weights.base = ["puWeight", "idWeight", "trigSF"]  # others needed
        weights.base = ["puWeight", "idWeight", "trigSF", "ctau_reweighing"]  # others needed
        #weights.base = []  # others needed
        #weights.base = ["puWeight", "PUjetID_SF", "idWeight", "trigSF"]  # others needed
        # weights.base = ["1"]  # others needed

        for category in self.categories:
            weights[category.name] = weights.base

        weights.nosel = ["puWeight"]
        weights.trigsel = ["puWeight"]
        weights.base_puw = ["puWeight"]
        # weights.gen = ["puWeight", "idWeight", "trigSF", "ctau_reweighing"]  # others needed
        weights.gen0 = ["GenDark_rew_weight_0"]  # others needed
        weights.gen1 = ["GenDark_rew_weight_1"]  # others needed
        weights.gen2 = ["GenDark_rew_weight_2"]  # others needed
        weights.gen3 = ["GenDark_rew_weight_3"]  # others needed
        weights.gen4 = ["GenDark_rew_weight_4"]  # others needed
        weights.gen5 = ["GenDark_rew_weight_5"]  # others needed
        weights.gen6 = ["GenDark_rew_weight_6"]  # others needed
        weights.gen7 = ["GenDark_rew_weight_7"]  # others needed
        weights.gen8 = ["GenDark_rew_weight_8"]  # others needed

        return weights

    # other methods

# config = Config("base", year=2018, ecm=13, lumi_pb=59741)
config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=1000, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True, xrd_redir='gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms')
