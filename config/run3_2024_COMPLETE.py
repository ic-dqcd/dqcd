from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.legacy_2018 import Config as legacy_config

#signal_xs = 43.9 * 0.01 # 2018
signal_xs = 43.9 * 0.01 #TODO what's this doing


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
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.98"),   #1E-4 threshold #TODO original default
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.985"),   #1E-5 threshold
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.987"),
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} >= 0"),

            #TODO 2024, no MET
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.9971"),   #1E-4 threshold #TODO Mu10 || DoubleMu, noMET; v1 (before: 0.9959)
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.9969"),   #1E-4 threshold #TODO Mu10, noMET; v1 (before: 0.9958)
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.9978"),   #1E-4 threshold #TODO DoubleMu, noMET; v1 (before: 0.9962)

            #TODO 2024, with MET, v1
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.9975"),   #1E-4 threshold #TODO Mu10 || DoubleMu, withMET; v1 (before: 0.9968)
            Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.9971"),   #1E-4 threshold #TODO Mu10, withMET; v1 (before: 0.9924)
            #Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.9980"),   #1E-4 threshold #TODO DoubleMu, withMET; v1 (before: 0.9946)

            #TODO 2024, with MET and muonSV_delta_phi_MET, v2
            ##Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.9949"),   #1E-4 threshold #TODO Mu10 || DoubleMu, withMET; v2 (threshold estimated from training)
            ##Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.9945"),   #1E-4 threshold #TODO Mu10, withMET; v2 (threshold estimated from training)
            ##Category("tight_bdt_scenarioA", "Tight bdt (A) region", selection="{{bdt_scenarioA}} > 0.9954"),   #1E-4 threshold #TODO DoubleMu, withMET; v2 (threshold estimated from training)

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
            (HLT_Mu10_Barrel_L1HP11_IP6 || HLT_Mu9_Barrel_L1HP10_IP6 || HLT_Mu8_Barrel_L1HP9_IP6 || HLT_Mu7_Barrel_L1HP8_IP6 || HLT_Mu6_Barrel_L1HP7_IP6 || HLT_Mu0_Barrel_L1HP6_IP6 || HLT_Mu0_Barrel_L1HP11 || HLT_Mu0_Barrel || HLT_Mu0_Barrel_L1HP10 || HLT_Mu0_Barrel_L1HP9 || HLT_Mu0_Barrel_L1HP8 || HLT_Mu0_Barrel_L1HP7 || HLT_Mu0_Barrel_L1HP6 ||
            HLT_DoubleMu4_3_LowMass || HLT_DoubleMu4_LowMass_Displaced) &&
            (nmuonSV > 0) &&
            (Sum(muonSV_mu1pt > 5.0)  > 0 || Sum(muonSV_mu2pt > 5.0) > 0)
            """),
            Category("tight_bdt_vector_custom", "", selection="(({{bdt_vector}} > 0.999) && (muonSV_bestchi2_mass <= 5)) || (({{bdt_vector}} > 0.997) && (muonSV_bestchi2_mass > 5))"),

        ]
        return ObjectCollection(regions)


    def add_datasets(self):

        sample_path = "/vols/cms/mc3909/bparkProductionAll_V1p3/tmp/"#from 2018

        sample_path_2024 = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024/"
        # ORIGINAL PATH+REDIRECTOR -> davs://gfe02.grid.hep.ph.ic.ac.uk:2880/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024/


        #TODO adjust these
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

        #TODO qcd background needs tags?
        tags = ["run3_2024", "qcd"]

        datasets = [
        #TODO adjust these

            Dataset("qcd_15to20",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-15to20_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-15to20_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_15to20"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_15to20"),
                check_empty=False,
                xs=xs["qcd_15to20"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_20to30",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-20to30_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-20to30_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_20to30"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_20to30"),
                check_empty=False,
                xs=xs["qcd_20to30"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_30to50",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-30to50_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-30to50_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_30to50"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_30to50"),
                check_empty=False,
                xs=xs["qcd_30to50"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_50to80",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-50to80_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-50to80_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_50to80"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_50to80"),
                check_empty=False,
                xs=xs["qcd_50to80"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_80to120",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-80to120_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-80to120_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_80to120"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_80to120"),
                check_empty=False,
                xs=xs["qcd_80to120"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_120to170",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-120to170_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-120to170_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_120to170"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_120to170"),
                check_empty=False,
                xs=xs["qcd_120to170"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_170to300",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-170to300_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-170to300_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_170to300"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_170to300"),
                check_empty=False,
                xs=xs["qcd_170to300"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_300to470",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-300to470_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-300to470_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_300to470"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_300to470"),
                check_empty=False,
                xs=xs["qcd_300to470"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_470to600",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-470to600_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-470to600_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_470to600"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_470to600"),
                check_empty=False,
                xs=xs["qcd_470to600"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_600to800",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-600to800_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-600to800_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_600to800"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_600to800"),
                check_empty=False,
                xs=xs["qcd_600to800"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_800to1000",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-800to1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-800to1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_800to1000"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_800to1000"),
                check_empty=False,
                xs=xs["qcd_800to1000"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),

            Dataset("qcd_1000toInf",
                 ### Read from GRID
                #dataset="/QCD_Bin-PT-1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/tafoyava-nanotron-v15_2024-RunIII2024Summer24-150X_mcRun3_2024_realistic-v2-31b42c6e5c2cc21a79e8dc5d0bc54970/USER",
                #prefix="redirector.t2.ucsd.edu:1095/",
                 ### Read from DCACHE
                folder=sample_path_2024 + "QCD_Bin-PT-1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8",
                prefix="gfe02.grid.hep.ph.ic.ac.uk",
                # TODO must adapt next lines to work on GRID
                #skipFiles=["{}/output_{}.root".format(
                #    sample_path + samples["qcd_1000toInf"], i)
                #    for i in range(1, 51)],
                process=self.processes.get("qcd_1000toInf"),
                check_empty=False,
                xs=xs["qcd_1000toInf"],
                merging={
                    "base": 10,
                },
                #tags=tags,
                #skipped_files_must_be_in_dataset=False,
            ),











        #TODO adjust these


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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
            ),

            Dataset("data_2018d_bph1_full_matveto",
                dataset="/ParkingBPH1/jleonhol-nanotron_mv-8570e29278f985b83289e6d44303ab3a/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 40,
                },
                tags=["ul_2018"],
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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
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
                tags=["ul_2018"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            ),

            Dataset("data_2018_bph6",
                dataset="/ParkingBPH6/jleonhol-nanotron-205145b8a3c6bd3ea858a0dbe549c313/USER",
                process=self.processes.get("data"),
                merging={
                    "base": 25,
                },
                tags=["ul_2018"],
                prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            ),

            
            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_10_ext_nocp5",
            #     dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-noCP5-00000000000000000000000000000000/USER",
            #     process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_10_nocp5"),
            #     check_empty=False,
            #     prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            #     xs=signal_xs,
            #     tags=["ext"]
            # ),

            # Dataset("scenarioA_mpi_4_mA_1p33_ctau_10_ext_nofilter",
            #     dataset = "/scenarioA_mpi_4_mA_1p33_ctau_10/jleonhol-noFilter-00000000000000000000000000000000/USER",
            #     process=self.processes.get("scenarioA_mpi_4_mA_1p33_ctau_10_nofilter"),
            #     check_empty=False,
            #     prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            #     xs=signal_xs,
            #     tags=["ext"]
            # ),


            # Pending DATA GOES HERE
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

        ]

        # for name, dataset in signal_samples.items():
        #     datasets.append(self.create_signal_dataset(name + "_ext", dataset, signal_xs,
        #         tags=["ext", "run3_2024", "limits_scA", "third"]))
        #     if name.endswith("10"):
        #         input_ctau = "ctau_10"
        #         ctaus = ["2p0", "5p0", "8p0"]
        #     elif name.endswith("100"):
        #         input_ctau = "ctau_100"
        #         ctaus = ["20", "50", "80"]
        #     else:
        #         ctaus = []
        #     for ctau in ctaus:
        #         datasets.append(self.create_signal_dataset(
        #             name.replace(input_ctau, "ctau_%s_rew" % ctau) + "_ext",
        #             dataset, signal_xs, tags=["ext", "run3_2024", "rew"]))

        datasets = ObjectCollection(datasets)
        
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
                Dataset(key + ("_ext" if sc == "A" else ""),
                    dataset=dataset,
                    process=self.processes.get(key),
                    check_empty=False,
                    tags=tags,
                    #prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
                    prefix="redirector.t2.ucsd.edu:1095/",
                    xs=signal_xs,
                    #TODO remove pattern when not useful anymore
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
                Dataset(key + ("_ext" if sc == "A" else ""),
                    folder=sample_path_2024 + sample_name_2024,
                    prefix="gfe02.grid.hep.ph.ic.ac.uk",
                    process=self.processes.get(key),
                    check_empty=False,
                    tags=tags,
                    xs=signal_xs,
                    #TODO remove pattern when not useful anymore
                    file_pattern="nano_(.{1}|.{2}|.{3}|10.{2}|1100|1101).root",
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
                            f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_orig}_ext")
                        for ctau_rew in new_ctaus:
                            datasets.add(Dataset(
                                f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}_rew_ext",
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
                            f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_orig}_ext")
                        for ctau_rew in new_ctaus:
                            datasets.add(Dataset(
                                f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}_rew_ext",
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
        weights.base = ["1"]  # others needed

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

config = Config("base", year=2024, ecm=13.6, lumi_pb=1000)
#config = Config("base", year=2018, ecm=13, lumi_pb=41600, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=13000, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=4184, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=1000, isUL=True)
#config = Config("base", year=2018, ecm=13, lumi_pb=33600, isUL=True, xrd_redir='gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms')
