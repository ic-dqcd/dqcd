from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.legacy_2018 import Config as legacy_config

signal_xs = 43.9 * 0.01


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

            Category("vvloose_bdt_scenarioA", "VVLoose bdt (A) region", selection="{{bdt_scenarioA}} > 0.55"),
            Category("vloose_bdt_scenarioA", "VLoose bdt (A) region", selection="{{bdt_scenarioA}} > 0.6"),
            #Category("loose_bdt_scenarioA", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.65"),
            Category("loose_bdt_scenarioA", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.6"),
            #Category("loose_bdt_scenarioA", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.7"),
            Category("medium_bdt_scenarioA", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.75"),
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.15"),   #1E-1 threshold
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.2"),    #between 1E-1 and 1E-2 threshold
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.6"),    #1E-2 threshold
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.7"),    #between 1E-2 and 1E-3 threshold
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.92"),   #1E-3 threshold
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.945"),   #between 1E-3 and 1E-4 threshold
            Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.98"),   #1E-4 threshold
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.985"),   #1E-5 threshold
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.987"),
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} >= 0"),

            Category("tight_bdt_scenarioA_1", "BDT > 0.9", selection="{{bdt_scenarioA}} > 0.9"),

            Category("bdt_scenarioA_0_0p05", "bdt (A) < 0.05 region",
                selection="{{bdt_scenarioA}} < 0.05"),
            Category("bdt_scenarioA_0p05_0p2", "0.05 < bdt (A) < 0.2 region",
                selection="{{bdt_scenarioA}} > 0.05 && {{bdt_scenarioA}} < 0.2"),
            Category("bdt_scenarioA_0p2_0p4", "0.2 < bdt (A) < 0.4 region",
                selection="{{bdt_scenarioA}} > 0.2 && {{bdt_scenarioA}} < 0.4"),
            Category("bdt_scenarioA_0p4_0p6", "0.4 < bdt (A) < 0.6 region",
                selection="{{bdt_scenarioA}} > 0.4 && {{bdt_scenarioA}} < 0.6"),
            Category("bdt_scenarioA_0p6_0p8", "0.6 < bdt (A) < 0.8 region",
                selection="{{bdt_scenarioA}} > 0.6 && {{bdt_scenarioA}} < 0.8"),
            Category("bdt_scenarioA_0p8_1p0", "0.8 < bdt (A) < 1.0 region",
                selection="{{bdt_scenarioA}} > 0.8 && {{bdt_scenarioA}} < 1.0"),
            Category("bdt_scenarioA_0p8_0p9", "0.8 < bdt (A) < 0.9 region",
                selection="{{bdt_scenarioA}} > 0.8 && {{bdt_scenarioA}} < 0.9"),
            Category("bdt_scenarioA_0p9_0p95", "0.9 < bdt (A) < 0.95 region",
                selection="{{bdt_scenarioA}} > 0.9 && {{bdt_scenarioA}} < 0.95"),
            Category("bdt_scenarioA_0p95_1p0", "0.95 < bdt (A) < 1.0 region",
                selection="{{bdt_scenarioA}} > 0.95 && {{bdt_scenarioA}} < 1.0"),

            Category("bdt_vector_0_0p05", "bdt (vector) < 0.05 region",
                selection="{{bdt_vector}} < 0.05"),
            Category("bdt_vector_0p05_0p2", "0.05 < bdt (vector) < 0.2 region",
                selection="{{bdt_vector}} > 0.05 && {{bdt_vector}} < 0.2"),
            Category("bdt_vector_0p2_0p4", "0.2 < bdt (vector) < 0.4 region",
                selection="{{bdt_vector}} > 0.2 && {{bdt_vector}} < 0.4"),
            Category("bdt_vector_0p4_0p6", "0.4 < bdt (vector) < 0.6 region",
                selection="{{bdt_vector}} > 0.4 && {{bdt_vector}} < 0.6"),
            Category("bdt_vector_0p6_0p8", "0.6 < bdt (vector) < 0.8 region",
                selection="{{bdt_vector}} > 0.6 && {{bdt_vector}} < 0.8"),
            Category("bdt_vector_0p8_1p0", "0.8 < bdt (vector) < 1.0 region",
                selection="{{bdt_vector}} > 0.8 && {{bdt_vector}} < 1.0"),
            Category("bdt_vector_0p8_0p9", "0.8 < bdt (vector) < 0.9 region",
                selection="{{bdt_vector}} > 0.8 && {{bdt_vector}} < 0.9"),
            Category("bdt_vector_0p9_0p95", "0.9 < bdt (vector) < 0.95 region",
                selection="{{bdt_vector}} > 0.9 && {{bdt_vector}} < 0.95"),
            Category("bdt_vector_0p95_1p0", "0.95 < bdt (vector) < 1.0 region",
                selection="{{bdt_vector}} > 0.95 && {{bdt_vector}} < 1.0"),
            Category("bdt_vector_1E-1_1E-2", "0.1 < bdt (vector) < 0.7 region",
                selection="{{bdt_vector}} > 0.1 && {{bdt_vector}} < 0.7"),
            Category("bdt_vector_1E-2_1E-3", "0.7 < bdt (vector) < 0.955 region",
                selection="{{bdt_vector}} > 0.7 && {{bdt_vector}} < 0.955"),
            Category("bdt_vector_1E-3_1E-4", "0.955 < bdt (vector) < 0.993 region",
                selection="{{bdt_vector}} > 0.955 && {{bdt_vector}} < 0.993"),
            Category("bdt_vector_1E-4_1E-5", "0.993 < bdt (vector) < 0.998 region",
                selection="{{bdt_vector}} > 0.993 && {{bdt_vector}} < 0.998"),
            
            
            

            Category("loose_bdt_scenarioB1", "Loose bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.5"),
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.15"),   #1E-1 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.2"),   #between 1E-1 and 1E-2 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.5"),   #1E-2 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.65"),   #between 1E-2 and 1E-3 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.8"),   #1E-3 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.9"),   #between 1E-3 and 1E-4 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.97"),   #1E-4 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.98"),   #in between 1E-4 and 1E-5 threshold
            Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.99"),   #1E-5 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.99"),

            Category("loose_bdt_scenarioB2", "Loose bdt (B2) region", selection="{{bdt_scenarioB2}} > 0.55"),
            Category("tight_bdt_scenarioB2", "Tight bdt (B2) region", selection="{{bdt_scenarioB2}} > 0.92"),

            Category("loose_bdt_scenarioC", "Loose bdt (C) region", selection="{{bdt_scenarioC}} > 0.55"),
            Category("tight_bdt_scenarioC", "Tight bdt (C) region", selection="{{bdt_scenarioC}} > 0.8"),

            # for the new H->ZdZd samples, using scenario A since the signature in similar
            #Category("loose_bdt_hzdzd", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.65"),
            Category("loose_bdt_hzdzd", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.7"), #old BDT
            #Category("tight_bdt_hzdzd", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.93"),
            Category("tight_bdt_hzdzd", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.96"), #old BDT optimal
            #Category("tight_bdt_hzdzd", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.98"),
            #Category("tight_bdt_hzdzd", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.985"),
            #Category("tight_bdt_hzdzd", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.994"),

            #try using vector portal BDT for H->ZdZd
            #Category("loose_bdt_hzdzd", "Loose bdt (VP) region", selection="{{bdt_vector}} > 0.6"),
            #Category("tight_bdt_hzdzd", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.993"),

            # for the new Z' samples, using scenario A since the signature in similar
            Category("loose_bdt_zprime", "Loose bdt (A) region", selection="{{bdt_scenarioA}} > 0.65"),
            Category("tight_bdt_zprime", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.98"),

            # for the vector portal central samples!
            Category("loose_bdt_vector", "Loose bdt (VP) region", selection="{{bdt_vector}} > 0.8"),     #1E-2 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.1"),  #1E-1 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.4"),   #between 1E-1 and 1E-2 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.8"),   #1E-2 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9"),   #between 1E-2 and 1E-3 threshold
            #Category("tight_bdt_vector", "Loose bdt (VP) region", selection="{{bdt_vector}} > 0.98"),    #1E-3 threshold
            #Category("tight_bdt_vector", "Loose bdt (VP) region", selection="{{bdt_vector}} > 0.99"),    #between 1E-3 and 1E-4 threshold
            Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.997"),  #1E-4 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9975"),   #between 1E-4 and 1E-5
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9985"),   #3E-5 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.999"),  #1E-5 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9998"),  #1E-6 threshold
            
            
            # for the vector portal samples, using dedicated BDT
            #Category("loose_bdt_vector", "Loose bdt (VP) region", selection="{{bdt_vector}} > 0.7"),     #1E-2 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.1"),  #1E-1 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.15"),   #between 1E-1 and 1E-2 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.7"),   #1E-2 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.75"),   #between 1E-2 and 1E-3 threshold
            #Category("tight_bdt_vector", "Loose bdt (VP) region", selection="{{bdt_vector}} > 0.955"),    #1E-3 threshold
            #Category("tight_bdt_vector", "Loose bdt (VP) region", selection="{{bdt_vector}} > 0.97"),    #between 1E-3 and 1E-4 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.993"),  #1E-4 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.994"),  #7E-5 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.996"),   #between 1E-4 and 1E-5
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.997"),   #3E-5 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.998"),  #1E-5 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9993"),  #1E-6 threshold
            #Category("loose_bdt_vector", "Loose bdt (VP) region", selection="{{bdt_vector}} > 0.55"),
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9945"),
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9985"),

            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9995"),
            #Category("tight_bdt_vector_1E-3", "bdt (VP) 10^-3 WP", selection="{{bdt_vector}} > 0.955"),
            #Category("tight_bdt_vector_1E-5", "bdt (VP) 10^-5 WP", selection="{{bdt_vector}} > 0.9985"),
            #Category("tight_bdt_vector_1E-6", "bdt (VP) 10^-6 WP", selection="{{bdt_vector}} > 0.9995"),

            Category("tight_bdt_vector_1", "BDT > 0.9", selection="{{bdt_vector}} > 0.9"),
            Category("tight_bdt_vector_2", "BDT > 0.95", selection="{{bdt_vector}} > 0.95"),
            Category("tight_bdt_vector_3", "BDT > 0.99", selection="{{bdt_vector}} > 0.99"),

            # for the B->PhiX samples
            Category("loose_bdt_btophi", "Loose bdt (B->PhiX) region", selection="{{bdt_scenarioA}} > 0.65"),
            Category("tight_bdt_btophi", "Tight bdt (B->PhiX) region", selection="{{bdt_scenarioA}} > 0.98"),
            Category("bdt_preselections", "Basic selections",
            selection="""
            (HLT_Mu9_IP6_part0 || HLT_Mu9_IP6_part1 || HLT_Mu9_IP6_part2 || HLT_Mu9_IP6_part3 || HLT_Mu9_IP6_part4) &&
            (nmuonSV > 0) &&
            (Sum(muonSV_mu1pt > 5.0)  > 0 || Sum(muonSV_mu2pt > 5.0) > 0)
            """),
            Category("tight_bdt_vector_custom", "", selection="(({{bdt_vector}} > 0.999) && (muonSV_bestchi2_mass <= 5)) || (({{bdt_vector}} > 0.997) && (muonSV_bestchi2_mass > 5))"),

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

            # DATA datasets to use in final unblinding

             Dataset("data_2018d_bph1_full",
                folder=[
                    sample_path + "ParkingBPH1_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p3_generationSync",
                    # sample_path + "ParkingBPH2_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                    # sample_path + "ParkingBPH3_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                    # sample_path + "ParkingBPH4_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                ],
                process=self.processes.get("data"),
                merging={
                    "base": 20,
                    "singlev_cat1": 30
                },
                tags=["ul"],
            ),

            Dataset("data_2018d_bph1_full_matveto",
                dataset="/ParkingBPH1/jleonhol-nanotron_mv-8570e29278f985b83289e6d44303ab3a/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 40,
                },
                tags=["ul"],
                runPeriod="D",
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                check_empty=False
            ),

            Dataset("data_2018d_bph1_full_matveto_v2",
                dataset="/ParkingBPH1/jleonhol-nanotron_mv_v2-8570e29278f985b83289e6d44303ab3a/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 40,
                },
                tags=["ul"],
                runPeriod="D",
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                check_empty=False
            ),

            Dataset("data_2018d_bph1_full_matveto_v3",
                dataset="/ParkingBPH1/jleonhol-nanotron_mv_v3-8570e29278f985b83289e6d44303ab3a/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 40,
                },
                tags=["ul"],
                runPeriod="D",
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                check_empty=False
            ),

            Dataset("data_2018d_bph1_full_matveto_v4",
                dataset="/ParkingBPH1/jleonhol-nanotron_mv_v4-8570e29278f985b83289e6d44303ab3a/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 40,
                },
                tags=["ul"],
                runPeriod="D",
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                check_empty=False
            ),

            Dataset("data_2018d_bph1234",
                folder=[
                    sample_path + "ParkingBPH1_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p3_generationSync",
                    sample_path + "ParkingBPH2_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                    sample_path + "ParkingBPH3_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                    sample_path + "ParkingBPH4_Run2018D-UL2018_MiniAODv2-v1_MINIAOD_v1p5_generationSync",
                ],
                process=self.processes.get("data"),
                merging={
                    "base": 250,
                    "singlev_cat1": 250,
                    "singlev_cat2": 75,
                    "singlev_cat3": 50,
                    "singlev_cat4": 50,
                    "singlev_cat5": 50,
                    "singlev_cat6": 50,
                    "multiv_cat1": 50,
                    "multiv_cat2": 50,
                    "multiv_cat3": 50,
                    "multiv_cat4": 50,
                    "multiv_cat5": 50,
                    "multiv_cat6": 50,
                },
                tags=["ul"],
            ),

            Dataset("data_2018_bph1",
                dataset="/ParkingBPH1/jleonhol-nanotron-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 25,
                    "singlev_cat1": 45,
                    "singlev_cat2": 15,
                    "singlev_cat3": 9,
                },
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            ),

            Dataset("data_2018_bph2",
                dataset="/ParkingBPH2/jleonhol-nanotron-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 25,
                    "singlev_cat1": 45,
                    "singlev_cat2": 15,
                    "singlev_cat3": 9,
                },
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            ),

            Dataset("data_2018_bph3",
                dataset="/ParkingBPH3/jleonhol-nanotron-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 25,
                    "singlev_cat1": 45,
                    "singlev_cat2": 15,
                    "singlev_cat3": 9,
                },
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            ),

            Dataset("data_2018_bph4",
                dataset="/ParkingBPH4/jleonhol-nanotron-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 25,
                    "singlev_cat1": 45,
                    "singlev_cat2": 15,
                    "singlev_cat3": 9,
                },
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            ),

            Dataset("data_2018_bph5",
                dataset="/ParkingBPH5/jleonhol-nanotron-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 25,
                    "singlev_cat1": 125,
                    "singlev_cat2": 25,
                    "singlev_cat3": 25,
                    "singlev_cat4": 5,
                },
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            ),

            Dataset("data_2018_bph6",
                dataset="/ParkingBPH6/jleonhol-nanotron-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 25,
                },
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_10",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_10_short"),
                # check_empty=False,
                # skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_10/nanotron/231124_165003/0000/nano_{i}.root"
                    # for i in range(1, 21)],
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
            # ),

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

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_100",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron-3b50327cf5b3a9483d26e0670720126c/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_100_short"),
                # check_empty=False,
                # skipFiles=[f"/store/user/jleonhol/samples/nanotron/scenarioA_mpi_4_mA_1p33_ctau_100/nanotron/231124_165326/0000/nano_{i}.root"
                    # for i in range(1, 21)],
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
            # ),

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

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_8p0_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_8p0"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_5p0_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_5p0"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_2p0_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_2p0"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

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

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_20_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_20"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_50_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_50"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_80_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_1p33_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_80"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

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

            # Dataset("scenarioA_mpi_4_mA_0p40_ctau_8p0_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_0p40_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_8p0"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_0p40_ctau_5p0_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_0p40_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_5p0"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_0p40_ctau_2p0_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_0p40_ctau_10/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_2p0"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_100_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_100"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            # Dataset("scenarioA_mpi_4_mA_0p40_ctau_80_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_80"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_0p40_ctau_50_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_50"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_0p40_ctau_20_rew_ext",
                # dataset = "/scenarioA_mpi_4_mA_0p40_ctau_100/jleonhol-nanotron_ext-571c6e4dc467acb2f3a7892cb8ebd34e/USER",
                # process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_20"),
                # check_empty=False,
                # prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                # xs=signal_xs,
                # tags=["ext", "rew"]
            # ),

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

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_0p1_ext_new",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_0p1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_0p1"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_0p25_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_0p25/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_0p25"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_0p3_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_0p3/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_0p3"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_0p6_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_0p6/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_0p6"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_100_ext_new",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_100/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_100"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_25p0_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_25p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_25p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_2p5_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_2p5/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_2p5"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_30_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_30/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_30"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_3p0_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_3p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_3p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_60p0_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_60p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_60p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_1_mA_0p33_ctau_6p0_ext",
                dataset = "/scenarioA_mpi_1_mA_0p33_ctau_6p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_1_mA_0p33_ctau_6p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_0p25_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_0p25/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_0p25"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_0p3_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_0p3/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_0p3"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_0p6_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_0p6/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_0p6"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_25p0_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_25p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_25p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_2p5_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_2p5/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_2p5"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_30_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_30/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_30"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_3p0_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_3p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_3p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_60p0_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_60p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_60p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_2_mA_0p67_ctau_6p0_ext",
                dataset = "/scenarioA_mpi_2_mA_0p67_ctau_6p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_2_mA_0p67_ctau_6p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_0p25_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_0p25/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_0p25"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_0p3_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_0p3/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_0p3"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_0p6_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_0p6/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_0p6"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_25p0_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_25p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_25p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_2p5_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_2p5/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_2p5"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_30_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_30/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_30"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_3p0_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_3p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_3p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_60p0_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_60p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_60p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_0p40_ctau_6p0_ext",
                dataset = "/scenarioA_mpi_4_mA_0p40_ctau_6p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_0p40_ctau_6p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_0p1_ext_new",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_0p1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_0p1"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_0p25_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_0p25/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_0p25"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_0p3_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_0p3/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_0p3"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_0p6_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_0p6/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_0p6"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_10_ext_new",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_10"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_25p0_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_25p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_25p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_2p5_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_2p5/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_2p5"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_30_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_30/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_30"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_3p0_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_3p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_3p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_60p0_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_60p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_60p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                tags=["ext"]
            ),

            Dataset("scenarioA_mpi_4_mA_1p33_ctau_6p0_ext",
                dataset = "/scenarioA_mpi_4_mA_1p33_ctau_6p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_6p0"),
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

            #Dataset("scenarioB1_mpi_1_mA_0p33_ctau_0p1_new",
                #dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_0p1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                #process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_0p1"),
                #check_empty=False,
                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                #xs=signal_xs
            #),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_0p25",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_0p25/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_0p25"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_0p3",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_0p3/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_0p3"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_0p6",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_0p6/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_0p6"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            #Dataset("scenarioB1_mpi_1_mA_0p33_ctau_10_new",
                #dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_10/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                #process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_10"),
                #check_empty=False,
                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                #xs=signal_xs
            #),

            #Dataset("scenarioB1_mpi_1_mA_0p33_ctau_100_new",
                #dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_100/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                #process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_100"),
                #check_empty=False,
                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                #xs=signal_xs
            #),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_1p0_new",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_1p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_1p0_new"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_25p0",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_25p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_25p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_2p5",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_2p5/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_2p5"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_30",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_30/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_30"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_3p0",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_3p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_3p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_60p0",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_60p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_60p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_1_mA_0p33_ctau_6p0",
                dataset = "/scenarioB1_mpi_1_mA_0p33_ctau_6p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_1_mA_0p33_ctau_6p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_0p25",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_0p25/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_0p25"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_0p3",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_0p3/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_0p3"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_0p6",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_0p6/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_0p6"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_25p0",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_25p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_25p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_2p5",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_2p5/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_2p5"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_30",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_30/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_30"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_3p0",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_3p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_3p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_60p0",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_60p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_60p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p40_ctau_6p0",
                dataset = "/scenarioB1_mpi_2_mA_0p40_ctau_6p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p40_ctau_6p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_0p25",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_0p25/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_0p25"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),     

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_0p3",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_0p3/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_0p3"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),       

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_0p6",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_0p6/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_0p6"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_25p0",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_25p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_25p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_2p5",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_2p5/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_2p5"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_30",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_30/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_30"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_3p0",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_3p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_3p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_60p0",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_60p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_60p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_2_mA_0p67_ctau_6p0",
                dataset = "/scenarioB1_mpi_2_mA_0p67_ctau_6p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_2_mA_0p67_ctau_6p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_0p25",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_0p25/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_0p25"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_0p3",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_0p3/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_0p3"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_0p6",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_0p6/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_0p6"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_25p0",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_25p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_25p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_2p5",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_2p5/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_2p5"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_30",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_30/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_30"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_3p0",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_3p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_3p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_60p0",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_60p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_60p0"),
                check_empty=False,
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs
            ),

            Dataset("scenarioB1_mpi_4_mA_1p33_ctau_6p0",
                dataset = "/scenarioB1_mpi_4_mA_1p33_ctau_6p0/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("scenarioB1_mpi_4_mA_1p33_ctau_6p0"),
                check_empty=False,
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

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1_old",
                folder="/vols/cms/mc3909/bparkProductionV3/HiddenValley_vector_m_2_ctau_10_xiO_1_xiL_1_privateMC_11X_NANOAODSIM_v3_generationForBParking",
                skipFiles=["{}/output_{}.root".format(
                    "/vols/cms/mc3909/bparkProductionV3/HiddenValley_vector_m_2_ctau_10_xiO_1_xiL_1_privateMC_11X_NANOAODSIM_v3_generationForBParking", i)
                    for i in range(1, 51)],
                process=self.processes.get("vector_m_2_ctau_10_xiO_1_xiL_1_old"),
                xs=signal_xs,
                skipped_files_must_be_in_dataset=False,
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

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_100_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-10_ctau-100_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-10_ctau-100_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111130/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_10_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-10_ctau-10_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-10_ctau-10_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111152/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_1_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-10_ctau-1_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-10_ctau-1_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111213/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_500_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-10_ctau-500_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-10_ctau-500_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111236/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_50_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-10_ctau-50_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-10_ctau-50_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111258/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_100_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-15_ctau-100_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-15_ctau-100_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111319/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_10_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-15_ctau-10_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-15_ctau-10_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111342/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_1_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-15_ctau-1_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-15_ctau-1_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111404/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_500_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-15_ctau-500_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-15_ctau-500_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111425/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_50_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-15_ctau-50_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-15_ctau-50_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111448/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_100_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-20_ctau-100_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-20_ctau-100_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111509/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_10_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-20_ctau-10_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-20_ctau-10_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111530/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_1_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-20_ctau-1_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-20_ctau-1_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111554/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_500_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-20_ctau-500_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-20_ctau-500_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111616/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_50_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-20_ctau-50_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-20_ctau-50_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111640/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_100_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-2_ctau-100_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-2_ctau-100_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111704/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-2_ctau-10_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-2_ctau-10_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111726/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_1_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-2_ctau-1_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-2_ctau-1_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111802/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_500_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-2_ctau-500_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-2_ctau-500_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111825/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_50_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-2_ctau-50_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-2_ctau-50_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111845/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_100_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-5_ctau-100_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_100_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-5_ctau-100_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111905/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_10_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-5_ctau-10_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_10_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-5_ctau-10_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111929/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_1_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-5_ctau-1_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-5_ctau-1_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_111951/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_500_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-5_ctau-500_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_500_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-5_ctau-500_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_112013/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_50_xiO_1_xiL_1_new",
                dataset="/GluGluHToDarkShowers_VP_mA-5_ctau-50_TuneCP5_13TeV_pythia8/jleonhol-nanotron_ext_off-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
                skipFiles=[f"/store/user/jleonhol/samples/nanotron/GluGluHToDarkShowers_VP_mA-5_ctau-50_TuneCP5_13TeV_pythia8/nanotron_ext_off/250212_112036/0000/nano_{i}.root"
                    for i in range(1, 7)],
            ),

            Dataset("hiddenValleyGridPack_vector_m_11_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_11_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_11_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_12_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_12_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_12_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_13_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_13_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_13_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),
            
            Dataset("hiddenValleyGridPack_vector_m_14_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_14_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_14_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_16_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_16_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_16_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_17_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_17_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_17_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_18_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_18_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_18_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_19_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_19_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_19_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_3_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_3_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_3_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_4_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_4_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_4_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_6_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_6_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_6_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_7_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_7_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_7_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_8_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_8_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_8_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_9_ctau_50_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_9_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_9_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_0p1_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_0p1_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_0p1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_0p3_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_0p3_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_0p3_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_0p65_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_0p65_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_0p65_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_200_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_200_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_200_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_20_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_20_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_20_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_2_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_2_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_2_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_35_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_35_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_35_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_4_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_4_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_4_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_60_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_60_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_60_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_6p5_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_6_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_6p5_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_75_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_75_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_75_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_0p1_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_0p1_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_0p1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_0p3_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_0p3_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_0p3_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_0p65_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_0p65_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_0p65_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_200_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_200_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_200_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_20_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_20_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_20_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_2_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_2_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_2_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_350_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_350_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_350_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_35_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_35_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_35_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_4_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_4_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_4_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_60_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_60_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_60_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_6p5_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_6_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_6p5_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_75_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_75_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_75_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_0p1_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_0p1_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_0p1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_0p3_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_0p3_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_0p3_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_0p65_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_0p65_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_0p65_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_200_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_200_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_200_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_20_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_20_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_20_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            #Dataset("hiddenValleyGridPack_vector_m_20_ctau_2_xiO_1_xiL_1_new",
                #dataset="/hiddenValleyGridPack_vector_m_20_ctau_2_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                #process=self.processes.get("vector_m_20_ctau_2_xiO_1_xiL_1"),
                #check_empty=False,
                #tags=["ul"],
                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                #xs=signal_xs,
            #),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_350_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_350_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_350_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_35_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_35_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_35_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_4_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_4_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_4_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_60_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_60_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_60_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_6p5_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_6_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_6p5_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_75_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_75_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_75_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_0p1_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_0p1_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_0p1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_0p3_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_0p3_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_0p3_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_0p65_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_0p65_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_0p65_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_200_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_200_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_200_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_20_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_20_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_20_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            #Dataset("hiddenValleyGridPack_vector_m_2_ctau_2_xiO_1_xiL_1_new",
                #dataset="/hiddenValleyGridPack_vector_m_2_ctau_2_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                #process=self.processes.get("vector_m_2_ctau_2_xiO_1_xiL_1"),
                #check_empty=False,
                #tags=["ul"],
                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                #xs=signal_xs,
            #),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_350_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_350_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_350_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            #Dataset("hiddenValleyGridPack_vector_m_2_ctau_35_xiO_1_xiL_1_new",
                #dataset="/hiddenValleyGridPack_vector_m_2_ctau_35_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                #process=self.processes.get("vector_m_2_ctau_35_xiO_1_xiL_1"),
                #check_empty=False,
                #tags=["ul"],
                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                #xs=signal_xs,
            #),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_4_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_4_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_4_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_60_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_60_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_60_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_6p5_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_6_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_6p5_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_75_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_75_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_75_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_0p1_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_0p1_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_0p1_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            #Dataset("hiddenValleyGridPack_vector_m_5_ctau_0p3_xiO_1_xiL_1_new",
                #dataset="/hiddenValleyGridPack_vector_m_5_ctau_0p3_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                #process=self.processes.get("vector_m_5_ctau_0p3_xiO_1_xiL_1"),
                #check_empty=False,
                #tags=["ul"],
                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                #xs=signal_xs,
            #),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_0p65_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_0p65_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_0p65_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_200_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_200_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_200_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_20_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_20_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_20_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_2_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_2_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_2_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_350_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_350_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_350_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_35_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_35_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_35_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_4_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_4_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_4_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            #Dataset("hiddenValleyGridPack_vector_m_5_ctau_60_xiO_1_xiL_1_new",
                #dataset="/hiddenValleyGridPack_vector_m_5_ctau_60_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                #process=self.processes.get("vector_m_5_ctau_60_xiO_1_xiL_1"),
                #check_empty=False,
                #tags=["ul"],
                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                #xs=signal_xs,
            #),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_6p5_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_6_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_6p5_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_75_xiO_1_xiL_1_new",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_75_xiO_1_xiL_1/jleonhol-nanotron_grid-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_75_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_2_ctau_50_xiO_1_xiL_1_new_private",
                dataset="/hiddenValleyGridPack_vector_m_2_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_2_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_5_ctau_50_xiO_1_xiL_1_new_private",
                dataset="/hiddenValleyGridPack_vector_m_5_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_5_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_10_ctau_50_xiO_1_xiL_1_new_private",
                dataset="/hiddenValleyGridPack_vector_m_10_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_10_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_15_ctau_50_xiO_1_xiL_1_new_private",
                dataset="/hiddenValleyGridPack_vector_m_15_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_15_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
            ),

            Dataset("hiddenValleyGridPack_vector_m_20_ctau_50_xiO_1_xiL_1_new_private",
                dataset="/hiddenValleyGridPack_vector_m_20_ctau_50_xiO_1_xiL_1/jleonhol-nanotron_ext_off_private-03c1abd2c21af5f26f47f89f556a9cfa/USER",
                process=self.processes.get("vector_m_20_ctau_50_xiO_1_xiL_1"),
                check_empty=False,
                tags=["ul"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                xs=signal_xs,
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
            # if name.endswith("10"):
                # input_ctau = "ctau_10"
                # ctaus = ["2p0", "5p0", "8p0"]
            # elif name.endswith("100"):
                # input_ctau = "ctau_100"
                # ctaus = ["20", "50", "80"]
            # else:
                # ctaus = []
            # for ctau in ctaus:
                # datasets.append(self.create_signal_dataset(
                    # name.replace(input_ctau, "ctau_%s_rew" % ctau) + "_ext",
                    # dataset, signal_xs, tags=["ext", "ul", "rew"]))

        datasets = ObjectCollection(datasets)
        
        datasets = self.add_rew_datasets(datasets)
        #datasets = self.add_rew_test_datasets(datasets)

        return datasets

    def add_rew_datasets(self, datasets):
        d = {
            "A": {
                "4": {
                    "masses": ["0p40", "0p80", "1p33", "1p90"],
                    "ctaus": {
                        "1p0": ["0p12", "0p13", "0p15", "0p18", "0p2", "0p3", "0p5", "0p8"],
                        "10": ["1p1", "1p3", "1p5", "1p8", "2p0", "3p0", "5p0", "8p0"],
                        "100": ["11", "13", "15", "18", "20", "30", "50", "80"],
                    }
                }
            }
        }

        for scenario in d:
            for m1 in d[scenario]:
                for m2 in d[scenario][m1]["masses"]:
                    for ctau_orig, new_ctaus in d[scenario][m1]["ctaus"].items():
                        orig_dataset = datasets.get(
                            f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_orig}_ext")
                        for ctau_rew in new_ctaus:
                            datasets.add(Dataset(
                                f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}_rew_ext",
                                dataset = orig_dataset.dataset,
                                process=self.processes.get(f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}"),
                                check_empty=False,
                                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                                xs=signal_xs,
                                tags=["ext", "rew"]
                            ))
        return datasets

    def add_rew_test_datasets(self, datasets):
        ctaus = {
            "1p0": ["0p1"],
            "10": ["1p0"],
            "100": ["10"],
        }
        d = {
            "A": {
                "4": {
                    "masses": ["0p40", "0p80", "1p90"],
                },
                "10": {
                    "masses": ["3p33"],
                },
                "2": {
                    "masses": ["0p25"],
                },
            }
        }

        for scenario in d:
            for m1 in d[scenario]:
                for m2 in d[scenario][m1]["masses"]:
                    for ctau_orig, new_ctaus in ctaus.items():
                        orig_dataset = datasets.get(
                            f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_orig}_ext")
                        for ctau_rew in new_ctaus:
                            datasets.add(Dataset(
                                f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}_rew_ext",
                                dataset = orig_dataset.dataset,
                                process=self.processes.get(f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}_rew"),
                                check_empty=False,
                                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                                xs=signal_xs,
                                tags=["ext", "rew", "rewtest"]
                            ))
        return datasets

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        weights.total_events_weights = ["puWeight", "filter_efficiency"]
        # weights.total_events_weights = ["genWeight"]
        # weights.total_events_weights = ["1"]

        weights.base = ["puWeight", "idWeight", "trigSF", "BDT_SF", "ctau_reweighing", "prescaleWeight"]
        #weights.base = ["puWeight", "idWeight", "trigSF", "BDT_SF", "ctau_reweighing"]
        #weights.base = ["puWeight", "idWeight", "trigSF", "ctau_reweighing", "prescaleWeight"]
        #weights.base = ["puWeight", "idWeight", "trigSF", "BDT_SF", "ctau_reweighing"]
        #weights.base = ["puWeight", "idWeight", "BDT_SF"]
        # weights.base = ["1"]  # others needed

        for category in self.categories:
            weights[category.name] = weights.base

        weights.nosel = ["puWeight", "ctau_reweighing"]
        weights.trigsel = ["puWeight", "ctau_reweighing"]
        weights.base_puw = ["puWeight", "ctau_reweighing"]
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

        weights.muonSV_simple_sel = ["puWeight"]

        return weights

    # other methods

config = Config("base", year=2018, ecm=13, lumi_pb=41600, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=13000, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=4184, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=1000, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True, xrd_redir='gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms')
