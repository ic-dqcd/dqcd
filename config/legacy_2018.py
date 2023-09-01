from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from cmt.config.base_config import Config as cmt_config


class Config(cmt_config):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    def add_categories(self, **kwargs):
        categories = [
            Category("base", "base category", selection="event >= 0"),
            Category("base_selection", "base category",
                nt_selection="(Sum$(Tau_pt->fElements > 17) > 0"
                    " && ((Sum$(Muon_pt->fElements > 17) > 0"
                    " || Sum$(Electron_pt->fElements > 17) > 0)"
                    " || Sum$(Tau_pt->fElements > 17) > 1)"
                    " && Sum$(Jet_pt->fElements > 17) > 1)",
                selection="Tau_pt[Tau_pt > 10].size() > 0 "
                    "&& ((Muon_pt[Muon_pt > 17].size() > 0"
                    "|| Electron_pt[Electron_pt > 17].size() > 0)"
                    "|| Tau_pt[Tau_pt > 10].size() > 1)"
                    "&& Jet_pt[Jet_pt > 17].size() > 0"),
            # Category("dum", "dummy category", selection="event == 220524669"),
            Category("dum", "dummy category", selection="event == 74472670"),
        ]
        return ObjectCollection(categories)

    def add_processes(self):
        processes = [
            Process("Background", Label("Background"), color=(255, 153, 0)),
            Process("QCD", Label("QCD"), color=(255, 153, 0), parent_process="background"),

            Process("data", Label("Data"), color=(0, 0, 0), isData=True),

            Process("dum", Label("dum"), color=(0, 0, 0)),
        ]

        process_group_names = {
            "default": [
                # "ggf_sm",
                # "data_tau",
                # "dy_high",
                # "tt_dl",
                "data",
                "background",
            ],
        }

        process_training_names = {}
            # "default": []
        # }

        return ObjectCollection(processes), process_group_names, process_training_names

    def add_datasets(self):
        sample_path = "/vols/cms/mc3909/bparkProductionAll_V1p0/"
        bdt_path = ("/vols/cms/mmieskol/icenet/output/dqcd/deploy/modeltag__vector_all/"
            "vols/cms/mc3909/bparkProductionAll_V1p0/")
        
        datasets = [
            Dataset("qcd_80to120",
                folder=[
                    sample_path + "QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                        "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                        "_MINIAODSIM_v1p0_generationSync",
                    sample_path + "QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                        "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2"
                        "_MINIAODSIM_v1p0_generationSync",
                ],
                process=self.processes.get("QCD"),
                xs=0.03105,),
                # friend_datasets="qcd_80to120_friend"),
            # Dataset("qcd_80to120_friend",
                # folder=[
                    # bdt_path + "QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                        # "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                        # "_MINIAODSIM_v1p0_generationSync",
                    # bdt_path + "QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                        # "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2"
                        # "_MINIAODSIM_v1p0_generationSync",
                # ],
                # process=self.processes.get("dum"),
                # xs=0.03105,
                # tags=["friend"]),
            
            Dataset("qcd_800to1000",
                folder=[
                    sample_path + "QCD_Pt-800to1000_MuEnrichedPt5_TuneCP5_13TeV_pythia8_"
                        "RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext3-v2_"
                        "MINIAODSIM_v1p0_generationSync",
                ],
                process=self.processes.get("QCD"),
                xs=0.03105,),
                # friend_datasets="qcd_800to1000_friend"),
            # Dataset("qcd_800to1000_friend",
                # folder=[
                    # bdt_path + "QCD_Pt-800to1000_MuEnrichedPt5_TuneCP5_13TeV_pythia8_"
                        # "RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext3-v2_"
                        # "MINIAODSIM_v1p0_generationSync",
                # ],
                # process=self.processes.get("dum"),
                # xs=0.03105,
                # tags=["friend"]),
        ]
        return ObjectCollection(datasets)

    def add_features(self):
        features = [
            Feature("njet", "nJet", binning=(10, -0.5, 9.5),
                x_title=Label("nJet")),
            Feature("jet_pt", "Jet_pt", binning=(10, 50, 150),
                x_title=Label("jet p_{T}"),
                units="GeV"),

            # bjet features
            Feature("bjet1_pt", "Jet_pt.at(bjet1_JetIdx)", binning=(10, 50, 150),
                x_title=Label("b_{1} p_{T}"),
                units="GeV",
                central="jet_smearing"),
            Feature("bjet1_pt_eta2p1", "Jet_pt.at(bjet1_JetIdx)", binning=(10, 50, 150),
                x_title=Label("b_{1} p_{T}"),
                units="GeV",
                selection="abs({{bjet1_eta}}) < 2.1",
                central="jet_smearing"),
            Feature("bjet1_eta", "Jet_eta.at(bjet1_JetIdx)", binning=(20, -5., 5.),
                x_title=Label("b_{1} #eta")),
            Feature("bjet1_phi", "Jet_phi.at(bjet1_JetIdx)", binning=(20, -3.2, 3.2),
                x_title=Label("b_{1} #phi")),
            Feature("bjet1_mass", "Jet_mass.at(bjet1_JetIdx)", binning=(10, 50, 150),
                x_title=Label("b_{1} m"),
                units="GeV",
                central="jet_smearing"),
            Feature("bjet2_pt", "Jet_pt.at(bjet2_JetIdx)", binning=(10, 50, 150),
                x_title=Label("b_{2} p_{T}"),
                units="GeV",
                central="jet_smearing"),
            Feature("bjet2_eta", "Jet_eta.at(bjet2_JetIdx)", binning=(20, -5., 5.),
                x_title=Label("b_{2} #eta")),
            Feature("bjet2_phi", "Jet_phi.at(bjet2_JetIdx)", binning=(20, -3.2, 3.2),
                x_title=Label("b_{2} #phi")),
            Feature("bjet2_mass", "Jet_mass.at(bjet2_JetIdx)", binning=(10, 50, 150),
                x_title=Label("b_{2} m"),
                units="GeV",
                central="jet_smearing"),

            Feature("ctjet1_pt", "Jet_pt.at(ctjet_indexes.at(0))", binning=(10, 50, 150),
                x_title=Label("add. central jet 1 p_{t}"),
                units="GeV",
                central="jet_smearing",
                selection="ctjet_indexes.size() > 0"),
            Feature("ctjet1_eta", "Jet_eta.at(ctjet_indexes.at(0))", binning=(20, -5., 5.),
                x_title=Label("add. central jet 1 #eta"),
                selection="ctjet_indexes.size() > 0"),
            Feature("ctjet1_phi", "Jet_phi.at(ctjet_indexes.at(0))", binning=(20, -3.2, 3.2),
                x_title=Label("add. central jet 1 #phi"),
                selection="ctjet_indexes.size() > 0"),
            Feature("ctjet1_mass", "Jet_mass.at(ctjet_indexes.at(0))", binning=(10, 50, 150),
                x_title=Label("add. central jet 1 m"),
                units="GeV",
                central="jet_smearing",
                selection="ctjet_indexes.size() > 0"),
            Feature("fwjet1_pt", "Jet_pt.at(fwjet_indexes.at(0))", binning=(10, 50, 150),
                x_title=Label("add. forward jet 1 p_t"),
                units="GeV",
                central="jet_smearing",
                selection="fwjet_indexes.size() > 0"),
            Feature("fwjet1_eta", "Jet_eta.at(fwjet_indexes.at(0))", binning=(20, -5., 5.),
                x_title=Label("add. forward jet 1 #eta"),
                selection="fwjet_indexes.size() > 0"),
            Feature("fwjet1_phi", "Jet_phi.at(fwjet_indexes.at(0))", binning=(20, -3.2, 3.2),
                x_title=Label("add. forward jet 1  #phi"),
                selection="fwjet_indexes.size() > 0"),
            Feature("fwjet1_mass", "Jet_mass.at(fwjet_indexes.at(0))", binning=(10, 50, 150),
                x_title=Label("add. forward jet 1  m"),
                units="GeV",
                central="jet_smearing",
                selection="fwjet_indexes.size() > 0"),

            Feature("bjet_difpt", "abs({{bjet1_pt}} - {{bjet2_pt}})", binning=(10, 50, 150),
                x_title=Label("bb #Delta p_t"),
                units="GeV",
                central="jet_smearing"),

            # lepton features
             Feature("tau_pt", "Tau_pt", binning=(75, 0, 150),
                x_title=Label("#tau p_{t}"),
                units="GeV"),
            Feature("tau_pt_tes", "Tau_pt_corr", binning=(75, 0, 150),
                x_title=Label("#tau p_{t}"),
                units="GeV"),
            Feature("tau_mass", "Tau_mass", binning=(52, 0.2, 1.5),
                x_title=Label("#tau m"),
                units="GeV"),
            Feature("tau_mass_tes", "Tau_mass_corr", binning=(52, 0.2, 1.5),
                x_title=Label("#tau m"),
                units="GeV"),

            Feature("lep1_pt", "dau1_pt", binning=(10, 50, 150),
                x_title=Label("#tau_{1} p_{t}"),
                units="GeV",
                systematics=["tes"]),
            Feature("lep1_eta", "dau1_eta", binning=(20, -5., 5.),
                x_title=Label("#tau_{1} #eta")),
            Feature("lep1_phi", "dau1_phi", binning=(20, -3.2, 3.2),
                x_title=Label("#tau_{1} #phi")),
            Feature("lep1_mass", "dau1_mass", binning=(10, 50, 150),
                x_title=Label("#tau_{1} m"),
                units="GeV",
                systematics=["tes"]),

            Feature("lep2_pt", "dau2_pt", binning=(10, 50, 150),
                x_title=Label("#tau_{2} p_{t}"),
                units="GeV",
                systematics=["tes"]),
            Feature("lep2_eta", "dau2_eta", binning=(20, -5., 5.),
                x_title=Label("#tau_{2} #eta")),
            Feature("lep2_phi", "dau2_phi", binning=(20, -3.2, 3.2),
                x_title=Label("#tau_{2} #phi")),
            Feature("lep2_mass", "dau2_mass", binning=(10, 50, 150),
                x_title=Label("#tau_{2} m"),
                units="GeV",
                systematics=["tes"]),

            # MET
            Feature("met_pt", "MET_pt", binning=(10, 50, 150),
                x_title=Label("MET p_t"),
                units="GeV",
                central="met_smearing"),
            Feature("met_phi", "MET_phi", binning=(20, -3.2, 3.2),
                x_title=Label("MET #phi"),
                central="met_smearing"),

            # Hbb
            Feature("Hbb_pt", "Hbb_pt", binning=(10, 50, 150),
                x_title=Label("H(b #bar{b}) p_t"),
                units="GeV"),
            Feature("Hbb_eta", "Hbb_eta", binning=(20, -5., 5.),
                x_title=Label("H(b #bar{b}) #eta")),
            Feature("Hbb_phi", "Hbb_phi", binning=(20, -3.2, 3.2),
                x_title=Label("H(b #bar{b}) #phi")),
            Feature("Hbb_mass", "Hbb_mass", binning=(30, 0, 300),
                x_title=Label("H(b #bar{b}) m"),
                units="GeV"),

            # Htt
            Feature("Htt_pt", "Htt_pt", binning=(10, 50, 150),
                x_title=Label("H(#tau^{+} #tau^{-}) p_t"),
                units="GeV",
                systematics=["tes"]),
            Feature("Htt_eta", "Htt_eta", binning=(20, -5., 5.),
                x_title=Label("H(#tau^{+} #tau^{-}) #eta"),
                systematics=["tes"]),
            Feature("Htt_phi", "Htt_phi", binning=(20, -3.2, 3.2),
                x_title=Label("H(#tau^{+} #tau^{-}) #phi"),
                systematics=["tes"]),
            Feature("Htt_mass", "Htt_mass", binning=(30, 0, 300),
                x_title=Label("H(#tau^{+} #tau^{-}) m"),
                units="GeV"),
                #systematics=["tes"]),

            # Htt (SVFit)
            Feature("Htt_svfit_pt", "Htt_svfit_pt", binning=(10, 50, 150),
                x_title=Label("H(#tau^{+} #tau^{-}) p_t (SVFit)"),
                units="GeV",
                systematics=["tes"]),
            Feature("Htt_svfit_eta", "Htt_svfit_eta", binning=(20, -5., 5.),
                x_title=Label("H(#tau^{+} #tau^{-}) #eta (SVFit)"),
                systematics=["tes"]),
            Feature("Htt_svfit_phi", "Htt_svfit_phi", binning=(20, -3.2, 3.2),
                x_title=Label("H(#tau^{+} #tau^{-}) #phi (SVFit)"),
                systematics=["tes"]),
            Feature("Htt_svfit_mass", "Htt_svfit_mass", binning=(30, 0, 300),
                x_title=Label("H(#tau^{+} #tau^{-}) m (SVFit)"),
                units="GeV",
                systematics=["tes"]),

            # HH
            Feature("HH_pt", "HH_pt", binning=(10, 50, 150),
                x_title=Label("HH p_t"),
                units="GeV",
                systematics=["tes"]),
            Feature("HH_eta", "HH_eta", binning=(20, -5., 5.),
                x_title=Label("HH #eta"),
                systematics=["tes"]),
            Feature("HH_phi", "HH_phi", binning=(20, -3.2, 3.2),
                x_title=Label("HH #phi"),
                systematics=["tes"]),
            Feature("HH_mass", "HH_mass", binning=(50, 0, 1000),
                x_title=Label("HH m"),
                units="GeV",
                systematics=["tes"]),

            # HH (SVFit)
            Feature("HH_svfit_pt", "HH_svfit_pt", binning=(10, 50, 150),
                x_title=Label("HH p_t (SVFit)"),
                units="GeV",
                systematics=["tes"]),
            Feature("HH_svfit_eta", "HH_svfit_eta", binning=(20, -5., 5.),
                x_title=Label("HH #eta (SVFit)")),
                #systematics=["tes"]),
            Feature("HH_svfit_phi", "HH_svfit_phi", binning=(20, -3.2, 3.2),
                x_title=Label("HH #phi (SVFit)")),
                #systematics=["tes"]),
            Feature("HH_svfit_mass", "HH_svfit_mass", binning=(50, 0, 1000),
                x_title=Label("HH m (SVFit)"),
                units="GeV"),
                #systematics=["tes"]),

            # HH KinFit
            Feature("HHKinFit_mass", "HHKinFit_mass", binning=(50, 0, 1000),
                x_title=Label("HH m (Kin. Fit)"),
                units="GeV",
                systematics=["tes"]),
            Feature("HHKinFit_chi2", "HHKinFit_chi2", binning=(30, 0, 10),
                x_title=Label("HH #chi^2 (Kin. Fit)"),
                systematics=["tes"]),

            # VBFjet features
            Feature("vbfjet1_pt", "Jet_pt.at(VBFjet1_JetIdx)", binning=(10, 50, 150),
                x_title=Label("VBFjet1 p_{t}"),
                units="GeV",
                central="jet_smearing"),
            Feature("vbfjet1_eta", "Jet_eta.at(VBFjet1_JetIdx)", binning=(20, -5., 5.),
                x_title=Label("VBFjet1 #eta")),
            Feature("vbfjet1_phi", "Jet_phi.at(VBFjet1_JetIdx)", binning=(20, -3.2, 3.2),
                x_title=Label("VBFjet1 #phi")),
            Feature("vbfjet1_mass", "Jet_mass.at(VBFjet1_JetIdx)", binning=(10, 50, 150),
                x_title=Label("VBFjet1 m"),
                units="GeV",
                central="jet_smearing"),
            Feature("vbfjet2_pt", "Jet_pt.at(VBFjet2_JetIdx)", binning=(10, 50, 150),
                x_title=Label("VBFjet2 p_t"),
                units="GeV",
                central="jet_smearing"),
            Feature("vbfjet2_eta", "Jet_eta.at(VBFjet2_JetIdx)", binning=(20, -5., 5.),
                x_title=Label("VBFjet2 #eta")),
            Feature("vbfjet2_phi", "Jet_phi.at(VBFjet2_JetIdx)", binning=(20, -3.2, 3.2),
                x_title=Label("VBFjet2 #phi")),
            Feature("vbfjet2_mass", "Jet_mass.at(VBFjet2_JetIdx)", binning=(10, 50, 150),
                x_title=Label("VBFjet2 m"),
                units="GeV",
                central="jet_smearing"),

            # VBFjj
            Feature("VBFjj_mass", "VBFjj_mass", binning=(40, 0, 1000),
                x_title=Label("VBFjj mass"),
                units="GeV"),
            Feature("VBFjj_deltaEta", "VBFjj_deltaEta", binning=(40, -8, 8),
                x_title=Label("#Delta#eta(VBFjj)")),
            Feature("VBFjj_deltaPhi", "VBFjj_deltaPhi", binning=(40, -6.4, 6.4),
                x_title=Label("#Delta#phi(VBFjj)")),

            # Weights
            Feature("genWeight", "genWeight", binning=(20, 0, 2),
                x_title=Label("genWeight")),
            Feature("puWeight", "puWeight", binning=(20, 0, 2),
                x_title=Label("puWeight"),
                systematics=["pu"]),
            Feature("prescaleWeight", "prescaleWeight", binning=(20, 0, 2),
                x_title=Label("prescaleWeight")),
            Feature("trigSF", "trigSF", binning=(20, 0, 2),
                x_title=Label("trigSF")),
            Feature("L1PreFiringWeight", "L1PreFiringWeight", binning=(20, 0, 2),
                x_title=Label("L1PreFiringWeight"),
                central="prefiring",
                systematics=["prefiring_syst"]),
            Feature("PUjetID_SF", "PUjetID_SF", binning=(20, 0, 2),
                x_title=Label("PUjetID_SF")),

            Feature("genHH_mass", "genHH_mass", binning=(100, 0, 2500),
                x_title=Label("generator HH mass"),
                units="GeV"),

        ]
        return ObjectCollection(features)

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        # weights.total_events_weights = ["genWeight", "puWeight", "DYstitchWeight"]
        weights.total_events_weights = ["genWeight", "puWeight"]

        # weights.base = ["genWeight", "puWeight"]  # others needed
        weights.base = ["1"]  # others needed
        weights.base_selection = weights.base

        return weights

    def add_systematics(self):
        systematics = [
            Systematic("jet_smearing", "_nom"),
            Systematic("met_smearing", ("MET", "MET_smeared")),
            Systematic("prefiring", "_Nom"),
            Systematic("prefiring_syst", "", up="_Up", down="_Dn"),
            Systematic("pu", "", up="Up", down="Down"),
            Systematic("tes", "_corr",
                affected_categories=self.categories.names(),
                module_syst_type="tau_syst"),
            Systematic("empty", "", up="", down="")
        ]
        return ObjectCollection(systematics)

    # other methods

config = Config("base", year=2018, ecm=13, lumi_pb=59741)
