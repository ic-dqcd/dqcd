from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.legacy_2018 import Config as legacy_config

#signal_xs = 43.9 * 0.01 # 2018
signal_xs = 52.23 * 0.01 # Run 3 (TODO full run3 or just 2024?), 52.23 pb is ggH at 13.6 TeV, BR(H→dark shower) = 1% = 0.01


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
            # 2024, scenarioA, trained with Mu-enriched pT-binned QCD
            #Category("tight_bdt_scenarioA_Mu10orDoubleMu", "Tight bdt (A), Mu10 || DoubleMu", selection="{{bdt_scenarioA}} > 0.3103"),	#1E-1 threshold # Mu10 || DoubleMu
            #Category("tight_bdt_scenarioA_Mu10", "Tight bdt (A), Mu10", selection="{{bdt_scenarioA}} > 0.1169"),			#1E-1 threshold # Mu10
            #Category("tight_bdt_scenarioA_DoubleMu", "Tight bdt (A), DoubleMu", selection="{{bdt_scenarioA}} > 0.3083"),		#1E-1 threshold # DoubleMu

            #Category("tight_bdt_scenarioA_Mu10orDoubleMu", "Tight bdt (A), Mu10 || DoubleMu", selection="{{bdt_scenarioA}} > 0.8386"),	#1E-2 threshold # Mu10 || DoubleMu
            #Category("tight_bdt_scenarioA_Mu10", "Tight bdt (A), Mu10", selection="{{bdt_scenarioA}} > 0.7433"),			#1E-2 threshold # Mu10
            #Category("tight_bdt_scenarioA_DoubleMu", "Tight bdt (A), DoubleMu", selection="{{bdt_scenarioA}} > 0.8364"),		#1E-2 threshold # DoubleMu

            #Category("tight_bdt_scenarioA_Mu10orDoubleMu", "Tight bdt (A), Mu10 || DoubleMu", selection="{{bdt_scenarioA}} > 0.9719"),	#1E-3 threshold # Mu10 || DoubleMu
            #Category("tight_bdt_scenarioA_Mu10", "Tight bdt (A), Mu10", selection="{{bdt_scenarioA}} > 0.9711"),			#1E-3 threshold # Mu10
            #Category("tight_bdt_scenarioA_DoubleMu", "Tight bdt (A), DoubleMu", selection="{{bdt_scenarioA}} > 0.9741"),		#1E-3 threshold # DoubleMu

            Category("tight_bdt_scenarioA_Mu10orDoubleMu", "Tight bdt (A), Mu10 || DoubleMu", selection="{{bdt_scenarioA}} > 0.9945"),	#1E-4 threshold # Mu10 || DoubleMu
            Category("tight_bdt_scenarioA_Mu10", "Tight bdt (A), Mu10", selection="{{bdt_scenarioA}} > 0.9953"),			#1E-4 threshold # Mu10
            Category("tight_bdt_scenarioA_DoubleMu", "Tight bdt (A), DoubleMu", selection="{{bdt_scenarioA}} > 0.9958"),		#1E-4 threshold # DoubleMu

            # 2024, scenarioB1, trained with Mu-enriched pT-binned QCD
            #Category("tight_bdt_scenarioB1_Mu10orDoubleMu", "Tight bdt (B1), Mu10 || DoubleMu", selection="{{bdt_scenarioB1}} > 0.3551"),	#1E-1 threshold # Mu10 || DoubleMu
            #Category("tight_bdt_scenarioB1_Mu10", "Tight bdt (B1), Mu10", selection="{{bdt_scenarioB1}} > 0.1844"),				#1E-1 threshold # Mu10
            #Category("tight_bdt_scenarioB1_DoubleMu", "Tight bdt (B1), DoubleMu", selection="{{bdt_scenarioB1}} > 0.3616"),			#1E-1 threshold # DoubleMu

            #Category("tight_bdt_scenarioB1_Mu10orDoubleMu", "Tight bdt (B1), Mu10 || DoubleMu", selection="{{bdt_scenarioB1}} > 0.8420"),	#1E-2 threshold # Mu10 || DoubleMu
            #Category("tight_bdt_scenarioB1_Mu10", "Tight bdt (B1), Mu10", selection="{{bdt_scenarioB1}} > 0.7423"),				#1E-2 threshold # Mu10
            #Category("tight_bdt_scenarioB1_DoubleMu", "Tight bdt (B1), DoubleMu", selection="{{bdt_scenarioB1}} > 0.8446"),			#1E-2 threshold # DoubleMu

            #Category("tight_bdt_scenarioB1_Mu10orDoubleMu", "Tight bdt (B1), Mu10 || DoubleMu", selection="{{bdt_scenarioB1}} > 0.9724"),	#1E-3 threshold # Mu10 || DoubleMu
            #Category("tight_bdt_scenarioB1_Mu10", "Tight bdt (B1), Mu10", selection="{{bdt_scenarioB1}} > 0.9519"),				#1E-3 threshold # Mu10
            #Category("tight_bdt_scenarioB1_DoubleMu", "Tight bdt (B1), DoubleMu", selection="{{bdt_scenarioB1}} > 0.9750"),			#1E-3 threshold # DoubleMu

            Category("tight_bdt_scenarioB1_Mu10orDoubleMu", "Tight bdt (B1), Mu10 || DoubleMu", selection="{{bdt_scenarioB1}} > 0.9948"),	#1E-4 threshold # Mu10 || DoubleMu
            Category("tight_bdt_scenarioB1_Mu10", "Tight bdt (B1), Mu10", selection="{{bdt_scenarioB1}} > 0.9910"),				#1E-4 threshold # Mu10
            Category("tight_bdt_scenarioB1_DoubleMu", "Tight bdt (B1), DoubleMu", selection="{{bdt_scenarioB1}} > 0.9955"),			#1E-4 threshold # DoubleMu


            # Following from the 2018 setup
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
            
            
            

            Category("loose_bdt_scenarioB1", "Loose bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.75"),
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.3"),   #1E-1 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.4"),   #between 1E-1 and 1E-2 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.75"),   #1E-2 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.85"),   #between 1E-2 and 1E-3 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.96"),   #1E-3 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.97"),    #7E-3 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.975"),   #between 1E-3 and 1E-4 threshold
            Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.991"),   #1E-4 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.993"),
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.994"),   #in between 1E-4 and 1E-5 threshold
            #Category("tight_bdt_scenarioB1", "Tight bdt (B1) region", selection="{{bdt_scenarioB1}} > 0.996"),   #1E-5 threshold


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
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.997"),  #1E-4 threshold
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9975"),   #between 1E-4 and 1E-5
            #Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.9985"),   #3E-5 threshold
            Category("tight_bdt_vector", "Tight bdt (VP) region", selection="{{bdt_vector}} > 0.999"),  #1E-5 threshold
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
            #TODO must define selection for 2024. For now, using all of the relevant triggers in an OR just to fill the space
            selection="""
            (HLT_Mu10_Barrel_L1HP11_IP6 || HLT_Mu9_Barrel_L1HP10_IP6 || HLT_Mu8_Barrel_L1HP9_IP6 || HLT_Mu7_Barrel_L1HP8_IP6 || HLT_Mu6_Barrel_L1HP7_IP6 ||
            HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced) &&
            (nmuonSV > 0) &&
            (Sum(muonSV_mu1pt > 4.0)  > 0 || Sum(muonSV_mu2pt > 3.0) > 0)
            """),

            Category("tight_bdt_vector_custom", "", selection="(({{bdt_vector}} > 0.999) && (muonSV_bestchi2_mass <= 5)) || (({{bdt_vector}} > 0.997) && (muonSV_bestchi2_mass > 5))"),

        ]
        return ObjectCollection(regions)

    def add_categories(self, **kwargs):
        # Inherit base + singlev_cat* + multiv_cat* (and the rest) from legacy_2018, then
        # build the third analysis group "quadv": a four-muon vertex (fourmuonSV)
        # reconstructed as two charge-neutral dimuon vertices (see
        # DQCDFourMuonSVSelectionRDF). The three groups are mutually exclusive:
        #   singlev : a single muonSV (cat_index == 0), without a four-muon vertex
        #   multiv  : two muonSVs WITHOUT a four-muon vertex
        #   quadv   : a four-muon vertex + its two dimuon vertices
        categories = list(super(Config, self).add_categories(**kwargs))

        fourmuon_sel = "isFourMuonPlusDimuonSV == 1"

        # Make the multi-vertex categories exclusive from quadv. singlev (cat_index == 0) is
        # now automatically disjoint from quadv: with get_multivertices and quadv using the
        # same 3% fractional mass window, any quadv event has a compatible muonSV pair, so
        # cat_index != 0 and it never falls into singlev.
        for cat in categories:
            if cat.name.startswith("multiv"):
                cat.selection = jrs(cat.selection, "!(%s)" % fourmuon_sel)

        # quadv group, binned in the FOUR-MUON vertex's own dxy/pAngle -- the common-vertex
        # fit of all four muons -- rather than in one of the two matched dimuon vertices.
        # This deliberately differs from singlev/multiv, which bin on
        # muonSV_dxy.at(min_chi2_index) (see config/legacy_2018.py): the quadv topology has
        # its own four-muon vertex, and that is the object the group is defined by.
        # fourmuonSV_selected_{dxy,pAngle} are the flat per-event values of the selected
        # fourmuonSV, produced by DQCDFourMuonSVSelectionRDF; they are -1 for non-quadv
        # events, which the isFourMuonPlusDimuonSV == 1 gate removes.
        fdxy = "fourmuonSV_selected_dxy"
        fpa = "fourmuonSV_selected_pAngle"
        categories += [
            Category("quadv", "Four-muon + dimuon vertices", selection=fourmuon_sel),
            Category("quadv_cat1", "Quadvertex, cat. 1",
                selection="%s && %s < 1 && %s < 0.2" % (fourmuon_sel, fdxy, fpa)),
            Category("quadv_cat2", "Quadvertex, cat. 2",
                selection="%s && %s < 1 && %s > 0.2" % (fourmuon_sel, fdxy, fpa)),
            Category("quadv_cat3", "Quadvertex, cat. 3",
                selection="%s && %s > 1 && %s < 10 && %s < 0.2" % (fourmuon_sel, fdxy, fdxy, fpa)),
            Category("quadv_cat4", "Quadvertex, cat. 4",
                selection="%s && %s > 1 && %s < 10 && %s > 0.2" % (fourmuon_sel, fdxy, fdxy, fpa)),
            Category("quadv_cat5", "Quadvertex, cat. 5",
                selection="%s && %s > 10 && %s < 0.2" % (fourmuon_sel, fdxy, fpa)),
            Category("quadv_cat6", "Quadvertex, cat. 6",
                selection="%s && %s > 10 && %s > 0.2" % (fourmuon_sel, fdxy, fpa)),
        ]
        return ObjectCollection(categories)

    def add_features(self):
        # Inherit the legacy/2018 features and add the flat four-muon-vertex variables
        # produced by DQCDFourMuonSVSelectionRDF (the quadv group / future fourmuonSV BDT).
        features = list(super(Config, self).add_features())
        features += [
            Feature("fourmuonSV_selected_mass", "fourmuonSV_selected_mass", binning=(8270, 0, 22),
                x_title=Label("fourmuonSV mass (4#mu + 2#mu match)"), units="GeV",
                tags=["lbn_light", "lbn"]),
            Feature("fourmuonSV_selected_chi2", "fourmuonSV_selected_chi2", binning=(100, 0, 10),
                x_title=Label("fourmuonSV #chi^{2}"), tags=["lbn_light", "lbn"]),
            Feature("fourmuonSV_selected_dxy", "fourmuonSV_selected_dxy", binning=(100, 0, 25),
                x_title=Label("fourmuonSV lxy"), units="cm", tags=["lbn_light", "lbn"]),
            Feature("fourmuonSV_selected_pAngle", "fourmuonSV_selected_pAngle", binning=(100, 0, 3.5),
                x_title=Label("fourmuonSV pAngle"), tags=["lbn_light", "lbn"]),
            Feature("isFourMuonPlusDimuonSV", "isFourMuonPlusDimuonSV", binning=(2, -0.5, 1.5),
                x_title=Label("is four-muon + dimuon SV"), tags=["lbn_light", "lbn"]),
        ]
        return ObjectCollection(features)


    def add_processes(self):
        # legacy_2018 defines the whole tree; only the 2024-only MinBias background is added here, so the 2018 config is left exactly as it was.
        processes, process_group_names, process_training_names = \
            super(Config, self).add_processes()

        # Hangs off "background" directly, NOT off "qcd". Datasets are grouped by walking up parent_process until a name in the active process group is found
        # (cmt/base_tasks/base.py:930-945), and every dataset landing on the same process is SUMMED. With parent_process="qcd" this sample and the 12 pT-hat bins would
        # both resolve to "qcd" and the same background would be counted twice -- silently, because the framework only refuses a group holding two processes of one chain.
        # As a sibling of "qcd" the double count is at least visible as two stack entries.
        processes.add(
            Process("qcdMinBias", Label("QCD (incl. dilepton MinBias)"),
                color=(255, 153, 0), parent_process="background")
        )

        # One-or-the-other groups. Never put "qcdMinBias" and the pT-hat bins (or "qcd") in the same group: they are alternative estimates of one background.
        process_group_names["qcd_minbias_background"] = ["qcdMinBias"]
        process_group_names["data_qcd_minbias"] = ["data", "qcdMinBias"]

        # Per-signal groups, the MinBias counterpart of legacy_2018's "qcd_<signal>".
        # Without these the only group that reaches qcdMinBias AND a signal is one naming "background", which resolves MinBias to the generic "Simulation" label -- so the
        # MinBias plots could not be read the way the pT-hat ones already are. Naming "qcdMinBias" explicitly stops the walk one level early and gives it its own legend entry and colour.
        #
        # Complement to legacy_2018's own per-signal loop since MinBias is not defined there
        for process in processes:
            if process.isSignal and "_" in process.name:
                process_group_names["qcdminbias_" + process.name] = [
                    "data",
                    "qcdMinBias",
                    process.name
                ]

        return processes, process_group_names, process_training_names


    def add_datasets(self):

        sample_path = "/vols/cms/mc3909/bparkProductionAll_V1p3/tmp/" #from 2018

        sample_path_2024 = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024/"
        # FULL PATH+REDIRECTOR -> davs://gfe02.grid.hep.ph.ic.ac.uk:2880/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024/


        xs = {
            # Mu-enriched pT-binned QCD samples
            # from https://xsecdb-xsdb-official.app.cern.ch/xsdb/?columns=67108863&currentPage=0&ordDirection=1&ordFieldName=process_name&pageSize=10&searchQuery=DAS%3DQCD_Bin-PT-1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8
            "qcd_15to20": 3018000,
            "qcd_20to30": 2701000,
            "qcd_30to50": 1461000,
            "qcd_50to80": 407600,
            "qcd_80to120": 96070,
            "qcd_120to170": 23140,
            "qcd_170to300": 7754,
            "qcd_300to470": 699.6,
            "qcd_470to600": 67.67,
            "qcd_600to800": 21.27,
            "qcd_800to1000": 3.89,
            "qcd_1000toInf": 1.323,

            # InclusiveDileptonMinBias with the DoubleMuOS43 generator filter
            # from https://cms-pub-talk.web.cern.ch/uploads/short-url/utPGgokD7yPcGPQS4KFgg20vezU.pdf
            # TODO estimated from back-of-the-envelope factors -> needs to be properly estimated eventually
            "qcdMinBias": 2.691e5,
        }

        # Adding tags to QCD foreseeing different background samples for different years
        tags = ["run3_2024", "qcd"]

        datasets = [
        #TODO adjust these

            Dataset("qcdDileptonMinBias",
                 ### Read from DCACHE, processed by Prijith on 2026-07-30
                folder="/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/ppradeep/samples/Parking/Run3/Nanotronv14/InclusiveDileptonMinBias_Fil-DoubleMuOS43_TuneCP5Plus_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcdMinBias"),
                check_empty=False,
                xs=xs["qcdMinBias"],
                merging={
                    "base": 20,
                    "singlev_cat1": 13,
                    "singlev_cat2": 8,
                    "singlev_cat3": 9,
                    "singlev_cat4": 3,
                    "singlev_cat5": 2,
                },
                tags=list(tags) + ["qcd_minbias"],
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_15to20"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_15to20",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-15to20_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-15to20_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_15to20"),
                check_empty=False,
                xs=xs["qcd_15to20"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_15to20"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_20to30",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-20to30_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-20to30_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_20to30"),
                check_empty=False,
                xs=xs["qcd_20to30"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_20to30"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_30to50",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-30to50_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-30to50_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_30to50"),
                check_empty=False,
                xs=xs["qcd_30to50"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_30to50"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_50to80",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-50to80_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-50to80_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_50to80"),
                check_empty=False,
                xs=xs["qcd_50to80"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_50to80"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_80to120",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-80to120_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-80to120_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_80to120"),
                check_empty=False,
                xs=xs["qcd_80to120"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_80to120"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_120to170",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-120to170_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-120to170_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_120to170"),
                check_empty=False,
                xs=xs["qcd_120to170"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_120to170"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_170to300",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-170to300_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-170to300_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_170to300"),
                check_empty=False,
                xs=xs["qcd_170to300"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_170to300"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_300to470",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-300to470_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-300to470_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_300to470"),
                check_empty=False,
                xs=xs["qcd_300to470"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_300to470"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_470to600",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-470to600_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-470to600_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_470to600"),
                check_empty=False,
                xs=xs["qcd_470to600"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_470to600"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_600to800",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-600to800_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-600to800_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_600to800"),
                check_empty=False,
                xs=xs["qcd_600to800"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_600to800"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_800to1000",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-800to1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-800to1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_800to1000"),
                check_empty=False,
                xs=xs["qcd_800to1000"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_800to1000"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_1000toInf",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("qcd_1000toInf"),
                check_empty=False,
                xs=xs["qcd_1000toInf"],
                merging={
                    "base": 4,
                    "singlev_cat1": 3,
                    "singlev_cat2": 2,
                    "singlev_cat3": 2,
                },
                tags=list(tags),
                # TODO must adapt next lines to work on DCACHE
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_1000toInf"], i)
                #    for i in range(1, 51)],
                #skipped_files_must_be_in_dataset=False,
            ),



            # ------
            # DATA datasets to use in intermediate studies, account for ~1% of the samples

            # TODO eventually need to ad a join dataset including single and double muon sampels WITHOUT double counting
            # Possible solution: keep SingleMuon inclusive, and in DoubleMuonLowMass require !(HLT_Mu10_Barrel_L1HP11_IP6). The sum is then disjoint by construction.

            Dataset("data_2024_singlemu_1percent",
                folder=[
                    sample_path_2024 + "ParkingSingleMuon0",
                    sample_path_2024 + "ParkingSingleMuon1",
                    sample_path_2024 + "ParkingSingleMuon2",
                    sample_path_2024 + "ParkingSingleMuon3",
                    sample_path_2024 + "ParkingSingleMuon4",
                    sample_path_2024 + "ParkingSingleMuon5",
                    sample_path_2024 + "ParkingSingleMuon6",
                    sample_path_2024 + "ParkingSingleMuon7",
                    sample_path_2024 + "ParkingSingleMuon8",
                    sample_path_2024 + "ParkingSingleMuon9",
                    sample_path_2024 + "ParkingSingleMuon10",
                    sample_path_2024 + "ParkingSingleMuon11",
                ],
                process=self.processes.get("data"),
                check_empty=False,
                tags=["run3_2024"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                file_pattern="nano_([1-9]|1[0-5]).root",
                merging={
                    "base": 9,
                    "singlev_cat1": 5,
                    "singlev_cat2": 4,
                    "singlev_cat3": 4,
                    "singlev_cat4": 1,
                    "singlev_cat5": 1,
                    "singlev_cat6": 1,
                },
            ),

            Dataset("data_2024_doublemu_1percent",
                folder=[
                    sample_path_2024 + "ParkingDoubleMuonLowMass0",
                    sample_path_2024 + "ParkingDoubleMuonLowMass1",
                    sample_path_2024 + "ParkingDoubleMuonLowMass2",
                    sample_path_2024 + "ParkingDoubleMuonLowMass3",
                    sample_path_2024 + "ParkingDoubleMuonLowMass4",
                    sample_path_2024 + "ParkingDoubleMuonLowMass5",
                    sample_path_2024 + "ParkingDoubleMuonLowMass6",
                    sample_path_2024 + "ParkingDoubleMuonLowMass7",
                ],
                process=self.processes.get("data"),
                check_empty=False,
                tags=["run3_2024"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                file_pattern="nano_([1-9]|1[0-5]).root",
                merging={
                    "base": 130,
                    "singlev_cat1": 83,
                    "singlev_cat2": 50,
                    "singlev_cat3": 60,
                    "singlev_cat4": 15,
                    "singlev_cat5": 8,
                    "singlev_cat6": 2,
                },
            ),
            # ------

            # ------
            # DATA datasets to use in  initial studies, processes a single file per epoch branch

            Dataset("data_2024_singlemu_HalfPerMil",
                folder=[
                    sample_path_2024 + "ParkingSingleMuon0",
                    sample_path_2024 + "ParkingSingleMuon1",
                    sample_path_2024 + "ParkingSingleMuon2",
                    sample_path_2024 + "ParkingSingleMuon3",
                    sample_path_2024 + "ParkingSingleMuon4",
                    sample_path_2024 + "ParkingSingleMuon5",
                    sample_path_2024 + "ParkingSingleMuon6",
                    sample_path_2024 + "ParkingSingleMuon7",
                    sample_path_2024 + "ParkingSingleMuon8",
                    sample_path_2024 + "ParkingSingleMuon9",
                    sample_path_2024 + "ParkingSingleMuon10",
                    sample_path_2024 + "ParkingSingleMuon11",
                ],
                process=self.processes.get("data"),
                check_empty=False,
                tags=["run3_2024"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                file_pattern="nano_1.root",
                merging={
                    "base": 1,
                },
            ),

            Dataset("data_2024_doublemu_HalfPerMil",
                folder=[
                    sample_path_2024 + "ParkingDoubleMuonLowMass0",
                    sample_path_2024 + "ParkingDoubleMuonLowMass1",
                    sample_path_2024 + "ParkingDoubleMuonLowMass2",
                    sample_path_2024 + "ParkingDoubleMuonLowMass3",
                    sample_path_2024 + "ParkingDoubleMuonLowMass4",
                    sample_path_2024 + "ParkingDoubleMuonLowMass5",
                    sample_path_2024 + "ParkingDoubleMuonLowMass6",
                    sample_path_2024 + "ParkingDoubleMuonLowMass7",
                ],
                process=self.processes.get("data"),
                check_empty=False,
                tags=["run3_2024"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                file_pattern="nano_1.root",
                merging={
                    "base": 9,
                    "singlev_cat1": 5,
                    "singlev_cat2": 3,
                    "singlev_cat3": 4,
                },
            ),
            # ------

            # TODO 2018 leftover, single period?
            Dataset("data_2018d_bph1",
                dataset="/ParkingBPH1/jleonhol-nanotronv2-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 20,
                },
                tags=["ul_2018"],
                runPeriod="D",
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            ),
            # ------


            # ------
            # Full DATA datasets to use in final unblinding

            Dataset("data_2024_singlemu",
                folder=[
                    sample_path_2024 + "ParkingSingleMuon0",
                    sample_path_2024 + "ParkingSingleMuon1",
                    sample_path_2024 + "ParkingSingleMuon2",
                    sample_path_2024 + "ParkingSingleMuon3",
                    sample_path_2024 + "ParkingSingleMuon4",
                    sample_path_2024 + "ParkingSingleMuon5",
                    sample_path_2024 + "ParkingSingleMuon6",
                    sample_path_2024 + "ParkingSingleMuon7",
                    sample_path_2024 + "ParkingSingleMuon8",
                    sample_path_2024 + "ParkingSingleMuon9",
                    sample_path_2024 + "ParkingSingleMuon10",
                    sample_path_2024 + "ParkingSingleMuon11",
                ],
                process=self.processes.get("data"),
                check_empty=False,
                tags=["run3_2024"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                merging={
                    "base": 1000,
                    "singlev_cat1": 560,
                    "singlev_cat2": 470,
                    "singlev_cat3": 510,
                    "singlev_cat4": 155,
                    "singlev_cat5": 123,
                    "singlev_cat6": 38,
                    "multiv_cat1": 5,
                    "multiv_cat2": 23,
                    "multiv_cat3": 5,
                    "multiv_cat4": 2,
                    "multiv_cat5": 1,
                    "multiv_cat6": 1,
                    "quadv_cat1": 4,
                    "quadv_cat2": 16,
                    "quadv_cat3": 3,
                    "quadv_cat4": 1,
                    "quadv_cat5": 1,
                    "quadv_cat6": 1,
                },
            ),

            Dataset("data_2024_doublemu",
                folder=[
                    sample_path_2024 + "ParkingDoubleMuonLowMass0",
                    sample_path_2024 + "ParkingDoubleMuonLowMass1",
                    sample_path_2024 + "ParkingDoubleMuonLowMass2",
                    sample_path_2024 + "ParkingDoubleMuonLowMass3",
                    sample_path_2024 + "ParkingDoubleMuonLowMass4",
                    sample_path_2024 + "ParkingDoubleMuonLowMass5",
                    sample_path_2024 + "ParkingDoubleMuonLowMass6",
                    sample_path_2024 + "ParkingDoubleMuonLowMass7",
                ],
                process=self.processes.get("data"),
                check_empty=False,
                tags=["run3_2024"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                merging={
                    "base": 15000,
                    "singlev_cat1": 9000,
                    "singlev_cat2": 5600,
                    "singlev_cat3": 6800,
                    "singlev_cat4": 1700,
                    "singlev_cat5": 860,
                    "singlev_cat6": 260,
                    "multiv_cat1": 43,
                    "multiv_cat2": 109,
                    "multiv_cat3": 38,
                    "multiv_cat4": 8,
                    "multiv_cat5": 4,
                    "multiv_cat6": 3,
                    "quadv_cat1": 30,
                    "quadv_cat2": 77,
                    "quadv_cat3": 27,
                    "quadv_cat4": 6,
                    "quadv_cat5": 3,
                    "quadv_cat6": 2,
                },
            ),
            # ------



            # TODO Pending DATA GOES HERE
            #Dataset("hiddenValleyGridPack_vector_m_10_ctau_100_xiO_1_xiL_1",
#            Dataset("GluGluHToDarkShowers-ScenarioA_Par-ctau-0p1-mA-0p25-mpi-1_TuneCP5_13p6TeV_powheg-pythia8",
#                dataset="/GluGluHToDarkShowers-ScenarioA_Par-ctau-0p1-mA-0p25-mpi-1_TuneCP5_13p6TeV_powheg-pythia8/tafoyava-RunIII2024Summer24_nanotron_v15-150X_mcrun3_2024_realistic-435ba2bfbd0ec63e168d4b47aa00e957/USER",
#                process=self.processes.get("GluGluHToDarkShowers-ScenarioA_Par-ctau-0p1-mA-0p25-mpi-1_TuneCP5_13p6TeV_powheg-pythia8"),
#                check_empty=False,
#                tags=["run3_2024"],
#                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
#                xs=signal_xs,
#                skipFiles=[f"/ceph/cms/store/user/tafoyava/samples/nanotron/GluGluHToDarkShowers-ScenarioA_Par-ctau-0p1-mA-0p25-mpi-1_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24_nanotron_v15-150X_mcrun3_2024_realistic/250812_093711/0000/nano_{i}.root"
#                    for i in range(1, 1)],
#                    #for i in range(1, 21)],
#            ),

            Dataset("BuToJpsiK",
                 ### Read from DCACHE
                folder=sample_path_2024 + "BuToJpsiK_Fil-BMuon_Par-SoftQCDnonD_TuneCP5_13p6TeV_pythia8-evtgen",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                process=self.processes.get("BuToJpsiK"),
                check_empty=False,
                tags=["run3_2024"],
            ),

        ]

        datasets = ObjectCollection(datasets)

        # ------
        # Place to add additional datasets

        #datasets = self.add_vp_grid_datasets_2024(datasets)

        #datasets = self.add_scenario_grid_datasets_2024(datasets)
        datasets = self.add_scenario_dcache_datasets_2024(datasets)

        #datasets = self.add_rew_datasets(datasets)
        #datasets = self.add_rew_test_datasets(datasets)

        return datasets

    # TODO this function overwrites the one in legacy_2018 and loads the 2024 processes. May need to look for a better place to put it
    def add_vp_grid_processes(self, processes):
        from config.datasets_vp_grid_2024 import d
        for key in d:
            # naming bug
            key = key.replace("ctau_6_", "ctau_6p5_")
            key = key.replace("m_11_", "m_11p5_")
            m = key.split("m_")[1].split("_")[0].replace("p", ".")
            ctau = key.split("ctau_")[1].split("_")[0]

            processes.add(
                Process(key.replace("hiddenValleyGridPack_", ""),
                    Label(latex=f"vector, $m={m}$, $c\\tau={ctau}$"),
                    color=(0, 0, 0), isSignal=True, parent_process="vector"),
            )
        
        return processes

    # TODO this function overwrites the one in legacy_2018 and loads the 2024 processes. May need to look for a better place to put it
    def add_scenario_grid_processes(self, processes):
        from config.datasets_scenario_2024 import d
        for key in d:
            sc = key.split("scenario")[1].split("_")[0]
            mpi = key.split("mpi_")[1].split("_")[0].replace("p", ".")
            mA = key.split("mA_")[1].split("_")[0].replace("p", ".")
            ctau = key.split("ctau_")[1].split("_")[0].replace("p", ".")

            if abs(float(mA) / float(mpi) - 1./3.) < 0.01:
                processes.add(
                    Process(key,
                        Label(latex="sc.%s, $m_{\pi}=%s$, $m_A=%s$, $c\\tau=%s$" % (sc, mpi, mA, ctau)),
                        color=(255, 0, 0), isSignal=True, parent_process=f"scenario{sc}"),
                )

            else:
                processes.add(
                    Process(key,
                        Label(latex="sc.%s, $m_{\pi}=%s$, $m_A=%s$, $c\\tau=%s$" % (sc, mpi, mA, ctau)),
                        color=(0, 255, 0), isSignal=True, parent_process=f"scenario{sc}"),
                )

        return processes


    def add_scenario_grid_datasets_2024(self, datasets):
        from config.datasets_scenario_2024 import d
        for key, dataset in d.items():
            sc = key.split("scenario")[1].split("_")[0]
            mpi = key.split("mpi_")[1].split("_")[0].replace("p", ".")
            mA = key.split("mA_")[1].split("_")[0].replace("p", ".")
            ctau = key.split("ctau_")[1].split("_")[0]

            tags = ["run3_2024", f"limits_sc{sc}"]
            if abs(float(mA) / float(mpi) - 1./3.) < 0.01:
                tags.append("third")
            elif abs(float(mA) / float(mpi) - 1./10.) < 0.01:
                tags.append("tenth")

            datasets.add(
                # 2018 was using a suffix "_ext" for scenario A. Leaving the line here in case it's useful in the future
                #Dataset(key + ("_ext" if sc == "A" else ""),
                Dataset(key,
                    dataset=dataset,
                    process=self.processes.get(key),
                    check_empty=False,
                    tags=list(tags),
                    #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                    prefix="redirector.t2.ucsd.edu:1095/",
                    xs=signal_xs,
                    #Pattern restricts to a subset of the sample\
                    file_pattern="nano_(.{1}|.{2}|.{3}|10.{2}|1100|1101).root",
                )
            )
        return datasets

    def add_scenario_dcache_datasets_2024(self, datasets):
        sample_path_2024 = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024/"

        from config.datasets_scenario_2024 import d
        for key, dataset in d.items():
            sc = key.split("scenario")[1].split("_")[0]
            mpi = key.split("mpi_")[1].split("_")[0].replace("p", ".")
            mA = key.split("mA_")[1].split("_")[0].replace("p", ".")
            ctau = key.split("ctau_")[1].split("_")[0]
            sample_name_2024 = dataset.split("/")[1]

            tags = ["run3_2024", f"limits_sc{sc}"]
            if abs(float(mA) / float(mpi) - 1./3.) < 0.01:
                tags.append("third")
            elif abs(float(mA) / float(mpi) - 1./10.) < 0.01:
                tags.append("tenth")

            datasets.add(
                # 2018 was using a suffix "_ext" for scenario A. Leaving the line here in case it's useful in the future
                #Dataset(key + ("_ext" if sc == "A" else ""),
                Dataset(key,
                    folder=sample_path_2024 + sample_name_2024,
                    prefix="gfe02.grid.hep.ph.ic.ac.uk",
                    process=self.processes.get(key),
                    check_empty=False,
                    tags=list(tags),
                    xs=signal_xs,
                    #Pattern restricts to a subset of the sample\
                    #file_pattern="nano_(.{1}|.{2}|.{3}|10.{2}|1100|1101).root",
                )
            )
        return datasets

    # TODO must adapt for 2024 (currently not used)
    def add_vp_grid_datasets_2024(self, datasets):
        # TODO must provide the real dictionary in config/datasets_vp_grid_2024.py
        from config.datasets_vp_grid_2024 import d
        for key, dataset in d.items():
            # naming bug
            # TODO remove these lines once 2024 samples are available
            key = key.replace("m_11_", "m_11p5_")
            key = key.replace("ctau_6_", "ctau_6p5_")

            datasets.add(
                Dataset(key + "_new",
                    dataset=dataset,
                    process=self.processes.get(key.replace("hiddenValleyGridPack_", "")),
                    check_empty=False,
                    tags=["run3_2024", "limits_vp"],
                    prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                    #prefix="redirector.t2.ucsd.edu:1095/", #TODO use this redirect when 2024 are ready
                    xs=signal_xs,
                )
            )
        return datasets

    # TODO must adapt for 2024 (currently not used)
    def add_rew_datasets_2024(self, datasets):
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
                            f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_orig}")
                        for ctau_rew in new_ctaus:
                            datasets.add(Dataset(
                                f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}_rew",
                                dataset = orig_dataset.dataset,
                                process=self.processes.get(f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}"),
                                check_empty=False,
                                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                                prefix="redirector.t2.ucsd.edu:1095/",
                                xs=signal_xs,
                                tags=["ext", "rew"]
                            ))
        return datasets

    # TODO must adapt for 2024 (currently not used) (remove if not useful!)
    def add_rew_test_datasets_2024(self, datasets):
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
                            f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_orig}")
                        for ctau_rew in new_ctaus:
                            datasets.add(Dataset(
                                f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}_rew",
                                dataset = orig_dataset.dataset,
                                process=self.processes.get(f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}_rew"),
                                check_empty=False,
                                #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                                prefix="redirector.t2.ucsd.edu:1095/",
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

        #weights.base = ["puWeight", "idWeight", "trigSF", "BDT_SF", "ctau_reweighing", "prescaleWeight"]#TODO enable for 2024
        #weights.base = ["puWeight", "idWeight", "trigSF", "BDT_SF", "ctau_reweighing"]
        #weights.base = ["puWeight", "idWeight", "trigSF", "ctau_reweighing", "prescaleWeight"]
        #weights.base = ["puWeight", "idWeight", "trigSF", "BDT_SF", "ctau_reweighing"]
        #weights.base = ["puWeight", "idWeight", "BDT_SF"]
        weights.base = ["1"]  # others needed, TODO enabled for 2024

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

#TODO adjust this for 2024
# Uncomment ONE. The reduced-lumi lines exist because MC is normalised as
# xs * lumi_pb / N_gen (FeaturePlot.get_normalization_factor, plotting.py:1683) while
# data is simply counted -- nothing scales for "I only read some of the files". Running
# a subset data dataset at full lumi therefore puts data ~100x (resp. ~1700x) below MC
# in any ratio plot, with nothing to warn you.
#
# Fractions measured 2026-07-27 by counting .root files under
#   /pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024
# against each dataset's file_pattern (SingleMuon + DoubleMuonLowMass combined):
#   _1percent    (nano_([1-9]|1[0-5]).root)  3299 / 360235 = 0.9157 %
#   _HalfPerMil  (nano_1.root)                212 / 360235 = 0.0589 %  (i.e. 0.59 permil)
# The two primary datasets agree to 0.2% on both, so one number covers each case.
# Re-measure if the production layout changes: the fraction is set by the number of
# files per CRAB task directory, not by design.
config = Config("base", year=2024, ecm=13.6, lumi_pb=109950)      # Full data sample
#config = Config("base", year=2024, ecm=13.6, lumi_pb=1006.8)     # _1percent datasets   (0.9157 % of 109950)
#config = Config("base", year=2024, ecm=13.6, lumi_pb=64.7)       # _HalfPerMil datasets (0.0589 % of 109950)

# 2018
#config = Config("base", year=2018, ecm=13, lumi_pb=41600, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=13000, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=4184, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=1000, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True, xrd_redir='gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms')
