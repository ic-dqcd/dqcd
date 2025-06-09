from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from cmt.config.base_config import Config as cmt_config
from cmt.base_tasks.base import Task


class Config(cmt_config):
    def __init__(self, *args, **kwargs):
        self.dxy_cut_all = ("!((muonSV_dxy >= 6.7 && muonSV_dxy <= 7.3) || "
            "(muonSV_dxy >= 10.5 && muonSV_dxy <= 11.5) || "
            "(muonSV_dxy >= 15.6 && muonSV_dxy <= 16.6))")
        self.dxy_cut = ("!((muonSV_bestchi2_dxy > 6.7 && muonSV_bestchi2_dxy < 7.3) || "
            "(muonSV_bestchi2_dxy > 10.5 && muonSV_bestchi2_dxy < 11.5) || "
            "(muonSV_bestchi2_dxy > 15.6 && muonSV_bestchi2_dxy < 16.6))")
        self.dz_cut = "abs(muonSV_bestchi2_z) < 27 || abs(muonSV_bestchi2_z) > 52"

        super(Config, self).__init__(*args, **kwargs)

        self.single_column_width = 0.4
        self.double_column_width = 0.375

        self.resonance_masses = {
            "ks": (0.43, 0.49),
            "eta": (0.52, 0.58),
            "rho": (0.73, 0.84),  # rho/omega
            "phi": (0.96, 1.08),
            "jpsi": (2.91, 3.27),
            "psi2s": (3.47, 3.89),
            "upsilon1s": (8.99, 9.87),
            "upsilon2s": (9.61, 10.39),
            "upsilon3s": (9.87, 10.77),
        }
        self.resonance_mass_sel = "(%s)" % jrs(
            ["{{muonSV_bestchi2_mass}} > %s && {{muonSV_bestchi2_mass}} < %s" % (elem[0], elem[1])
                for elem in self.resonance_masses.values()],
            op="or"
        )

        self.resonance_mass_veto = "(%s)" % jrs(
            ["{{muonSV_bestchi2_mass}} < %s && {{muonSV_bestchi2_mass}} > %s" % (elem[0], elem[1])
                for elem in self.resonance_masses.values()],
            op="and"
        )

        self.regions = self.add_regions()

        # self.qcd_var1 = DotDict({"nominal": "os", "inverted": "ss"})
        self.qcd_var1 = DotDict({"nominal": "bdt_tight", "inverted": "bdt_loose"})
        self.qcd_var2 = DotDict({"nominal": "chi2_tight", "inverted": "chi2_loose"})

        # add new process_group_name for each signal sample, avoiding "wrapper" processes
        for process in self.processes:
            if process.isSignal and "_" in process.name:
                self.process_group_names["sig_" + process.name] = [
                    process.name
                ]

                self.process_group_names[process.name] = [
                    "data",
                    "background",
                    process.name
                ]

                self.process_group_names["data_" + process.name] = [
                    "data",
                    process.name
                ]

                self.process_group_names["qcd_" + process.name] = [
                    "data",
                    "qcd_1000toInf",
                    "qcd_120to170",
                    "qcd_15to20",
                    "qcd_170to300",
                    "qcd_20to30",
                    "qcd_300to470",
                    "qcd_30to50",
                    "qcd_470to600",
                    "qcd_50to80",
                    "qcd_600to800",
                    "qcd_80to120",
                    "qcd_800to1000",
                    process.name
                ]


    def add_regions(self, **kwargs):
        regions = [
            Category("signal", "Signal region", selection="{{bdt}} > 0.85"),
            Category("background", "Background region",
                selection="{{bdt}} > 0.3 && {{bdt}} < 0.85"),
                ]
        return ObjectCollection(regions)

    def add_categories(self, **kwargs):
        single_sel = """cat_index == 0 &&
                muonSV_mu1eta.at(min_chi2_index) != 0 && muonSV_mu2eta.at(min_chi2_index) != 0"""
        categories = [
            Category("base", "base", selection="event >= 0"),
            Category("nodarkphotons", "nodarkphotons",
                selection="GenPart_pdgId[GenPart_pdgId == 9900015].size() == 0"),
            Category("base_puw", "base", selection="event >= 0"),
            Category("nosel", "No selection", selection="event >= 0"),
            Category("trigsel", "Only trigger selection applied",
                selection="""((HLT_Mu9_IP6_part0 == 1) ||
                    (HLT_Mu9_IP6_part1 == 1) || (HLT_Mu9_IP6_part2 == 1) ||
                    (HLT_Mu9_IP6_part3 == 1) || (HLT_Mu9_IP6_part4 == 1))"""),
            Category("gen", "gen", selection="event >= 0"),
            Category("gen0", "gen0", selection="event >= 0"),
            Category("gen1", "gen1", selection="event >= 0"),
            Category("gen2", "gen2", selection="event >= 0"),
            Category("gen3", "gen3", selection="event >= 0"),
            Category("gen4", "gen4", selection="event >= 0"),
            Category("gen5", "gen5", selection="event >= 0"),
            Category("gen6", "gen6", selection="event >= 0"),
            Category("gen7", "gen7", selection="event >= 0"),
            Category("gen8", "gen8", selection="event >= 0"),
            # Category("dum", "dummy category", selection="event == 220524669"),
            Category("dum", "dummy category", selection="event == 3"),
            Category("jpsi", "jpsi events",
                selection="""(GenPart_pdgId[abs(GenPart_pdgId) == 443].size() > 0)
                    && ((HLT_Mu9_IP6_part0 == 1) ||
                        (HLT_Mu9_IP6_part1 == 1) || (HLT_Mu9_IP6_part2 == 1) ||
                        (HLT_Mu9_IP6_part3 == 1) || (HLT_Mu9_IP6_part4 == 1))"""),
            Category("nojpsi", "nojpsi events",
                 selection="""(GenPart_pdgId[abs(GenPart_pdgId) == 443].size() == 0)
                    && ((HLT_Mu9_IP6_part0 == 1) ||
                        (HLT_Mu9_IP6_part1 == 1) || (HLT_Mu9_IP6_part2 == 1) ||
                        (HLT_Mu9_IP6_part3 == 1) || (HLT_Mu9_IP6_part4 == 1))"""),

            # analysis categories
            # multi-vertex
            Category("multiv", "Multivertices", selection="cat_index != 0"),
            Category("multiv_cat1", "Multivertices, cat. 1",
                selection="""cat_index > 0 && muonSV_dxy.at(min_chi2_index) < 1 &&
                    muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("multiv_cat2", "Multivertices, cat. 2",
                selection="""cat_index > 0 && muonSV_dxy.at(min_chi2_index) < 1 &&
                    muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("multiv_cat3", "Multivertices, cat. 3",
                selection="""cat_index > 0 && muonSV_dxy.at(min_chi2_index) > 1 &&
                    muonSV_dxy.at(min_chi2_index) < 10 && muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("multiv_cat4", "Multivertices, cat. 4",
                selection="""cat_index > 0 && muonSV_dxy.at(min_chi2_index) > 1 &&
                    muonSV_dxy.at(min_chi2_index) < 10 && muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("multiv_cat5", "Multivertices, cat. 5",
                selection="""cat_index > 0 && muonSV_dxy.at(min_chi2_index) > 10 &&
                    muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("multiv_cat6", "Multivertices, cat. 6",
                selection="""cat_index > 0 && muonSV_dxy.at(min_chi2_index) > 10 &&
                    muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("multiv_new1", "Multivertices, new cat. 1",
                selection="cat_index > 0 && muonSV_dxy.at(min_chi2_index) < 1"),
            Category("multiv_new2", "Multivertices, new cat. 2",
                selection="cat_index > 0 && muonSV_dxy.at(min_chi2_index) > 1"),

            # single-vertex
            Category("singlev", "Single vertex", selection=single_sel),
            Category("singlev_cat1", "Single vertex, cat. 1",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) < 1 &&
                    muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("singlev_cat2", "Single vertex, cat. 2",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) < 1 &&
                    muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("singlev_cat3", "Single vertex, cat. 3",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) > 1 &&
                    muonSV_dxy.at(min_chi2_index) < 10 && muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("singlev_cat4", "Single vertex, cat. 4",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) > 1 &&
                    muonSV_dxy.at(min_chi2_index) < 10 && muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("singlev_cat5", "Single vertex, cat. 5",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) > 10 &&
                    muonSV_pAngle.at(min_chi2_index) < 0.2"""),
            Category("singlev_cat6", "Single vertex, cat. 6",
                selection=single_sel + """ && muonSV_dxy.at(min_chi2_index) > 10 &&
                    muonSV_pAngle.at(min_chi2_index) > 0.2"""),
            Category("singlev_new1", "Single vertex, new cat. 1",
                selection=single_sel + " && muonSV_dxy.at(min_chi2_index) < 1"),
            Category("singlev_new2", "Single vertex, new cat. 2",
                selection=single_sel + " && muonSV_dxy.at(min_chi2_index) > 1"),
            Category("muonSV_simple_sel", "Require at least one muon SV", selection="nmuonSV >= 1"),
            Category("bdt_preselections", "BDT pre-selections",
                selection="""
                (HLT_Mu9_IP6_part0 || HLT_Mu9_IP6_part1 || HLT_Mu9_IP6_part2 || HLT_Mu9_IP6_part3 || HLT_Mu9_IP6_part4) &&
                (nmuonSV > 0) &&
                (Sum(muonSV_mu1pt > 5.0)  > 0 || Sum(muonSV_mu2pt > 5.0) > 0)
            """),
            Category("bdt_preselections_with_eta_cut", "BDT pre-selections",
                selection="""
                (HLT_Mu9_IP6_part0 || HLT_Mu9_IP6_part1 || HLT_Mu9_IP6_part2 || HLT_Mu9_IP6_part3 || HLT_Mu9_IP6_part4) &&
                (nmuonSV > 0) &&
                (Sum(muonSV_mu1pt > 5.0 && abs(muonSV_mu1eta) < 2.4)  > 0 || Sum(muonSV_mu2pt > 5.0 && abs(muonSV_mu2eta) < 2.4) > 0)
            """)

        ]
        return ObjectCollection(categories)

    def add_processes(self):
        processes = [
            Process("background", Label("Simulation"), color=(0, 0, 255)),

            Process("qcd", Label("QCD"), color=(255, 0, 0), parent_process="background"),
            Process("qcd_1000toInf", Label("QCD (1000-)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_120to170", Label("QCD (120-170)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_15to20", Label("QCD (15-20)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_170to300", Label("QCD (170-300)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_20to30", Label("QCD (20-30)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_300to470", Label("QCD (300-470)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_30to50", Label("QCD (30-50)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_470to600", Label("QCD (470-600)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_50to80", Label("QCD (50-80)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_600to800", Label("QCD (600-800)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_80to120", Label("QCD (80-120)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_800to1000", Label("QCD (800-1000)"), color=(255, 0, 0), parent_process="qcd"),
            Process("qcd_15to7000", Label("QCD (15-7000)"), color=(255, 0, 0), parent_process="qcd"),

            Process("QCD_Pt-15to7000_TuneCP5_Flat2018", Label("QCD (15to7000)"), color=(255, 153, 0)),

            Process("signal", Label("Signal"), color=(255, 0, 0), isSignal=True),

            Process("scenarioA", Label("scenarioA"), color=(0, 0, 0), isSignal=True, parent_process="signal"),

            ###########
            # mpi = 1 #
            ###########
            Process("scenarioA_mpi_1_mA_0p25_ctau_0p1", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p25_ctau_10", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p25_ctau_100", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p25_ctau_1p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            #Process("scenarioA_mpi_1_mA_0p33_ctau_0p1", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            #Process("scenarioA_mpi_1_mA_0p33_ctau_10", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            #Process("scenarioA_mpi_1_mA_0p33_ctau_100", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            #Process("scenarioA_mpi_1_mA_0p33_ctau_1p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_0p1", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_10", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_100", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_1p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),

            # Process("scenarioA_mpi_1_mA_0p33_ctau_0p25", Label(latex="sc.A, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=0.25mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_1_mA_0p33_ctau_0p3", Label(latex="sc.A, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=0.3mm$"), color=(0, 255, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_1_mA_0p33_ctau_0p6", Label(latex="sc.A, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=0.6mm$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_1_mA_0p33_ctau_25p0", Label(latex="sc.A, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=25mm$"), color=(255, 255, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_1_mA_0p33_ctau_2p5", Label(latex="sc.A, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=2.5mm$"), color=(255, 0, 255), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_1_mA_0p33_ctau_30", Label(latex="sc.A, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=30mm$"), color=(0, 255, 255), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_1_mA_0p33_ctau_3p0", Label(latex="sc.A, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=3.0mm$"), color=(128, 0, 128), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_1_mA_0p33_ctau_60p0", Label(latex="sc.A, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=60mm$"), color=(255, 165, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_1_mA_0p33_ctau_6p0", Label(latex="sc.A, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=6mm$"), color=(255, 165, 0), isSignal=True, parent_process="scenarioA"),

            # rew
            Process("scenarioA_mpi_1_mA_0p25_ctau_80", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p25_ctau_50", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p25_ctau_20", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p25_ctau_8p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=8.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p25_ctau_5p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=5.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p25_ctau_2p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.25$, $c\\tau=2.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_80", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_50", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_20", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_8p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=8.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_5p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=5.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_2p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=2.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_80", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_50", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_20", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_8p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=8.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_5p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=5.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p45_ctau_2p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.45$, $c\\tau=2.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),

            ###########
            # mpi = 2 #
            ###########
            Process("scenarioA_mpi_2_mA_0p25_ctau_0p1", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p25_ctau_10", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p25_ctau_100", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p25_ctau_1p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_0p1", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_10", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_100", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_1p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_0p1", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_10", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_100", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_1p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_0p1", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_10", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_100", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_1p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),

            # Process("scenarioA_mpi_2_mA_0p67_ctau_0p25", Label(latex="sc.A, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=0.25mm$"), color=(128, 128, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_0p3", Label(latex="sc.A, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=0.3mm$"), color=(0, 128, 128), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_0p6", Label(latex="sc.A, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=0.6mm$"), color=(255, 105, 180), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_25p0", Label(latex="sc.A, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=25mm$"), color=(255, 0, 255), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_2p5", Label(latex="sc.A, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=2.5mm$"), color=(240, 128, 128), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_30", Label(latex="sc.A, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=30mm$"), color=(106, 90, 205), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_60p0", Label(latex="sc.A, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=60mm$"), color=(0, 100, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_6p0", Label(latex="sc.A, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=6.0mm$"), color=(255, 140, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_2_mA_0p67_ctau_3p0", Label(latex="sc.A, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=3.0mm$"), color=(255, 140, 0), isSignal=True, parent_process="scenarioA"),

            # rew
            Process("scenarioA_mpi_2_mA_0p25_ctau_80", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p25_ctau_50", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p25_ctau_20", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p25_ctau_8p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=8.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p25_ctau_5p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=5.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p25_ctau_2p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.25$, $c\\tau=2.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_80", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_50", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_20", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_8p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=8.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_5p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=5.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p40_ctau_2p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.40$, $c\\tau=2.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_80", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_50", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_20", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_8p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=8.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_5p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=5.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_2p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=2.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_80", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_50", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_20", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_8p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=8.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_5p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=5.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p90_ctau_2p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.90$, $c\\tau=2.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),

            ###########
            # mpi = 4 #
            ###########
            # Process("scenarioA_mpi_4_mA_0p40_ctau_0p1", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_10", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_100", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_1p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=1.0$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_0p80_ctau_0p1", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_0p80_ctau_10", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_0p80_ctau_100", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_0p80_ctau_1p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            #Process("scenarioA_mpi_4_mA_1p33_ctau_0p1", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=0.1$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_10_old", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10$ old"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            #Process("scenarioA_mpi_4_mA_1p33_ctau_10", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_10_new", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10$ new"), color=(0, 255, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_10_nocp5", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10$ (No CP5)"), color=(0, 255, 255), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_10_nofilter", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10$ (No Filter)"), color=(255, 255, 0), isSignal=True, parent_process="scenarioA"),
            #Process("scenarioA_mpi_4_mA_1p33_ctau_100", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=100$ "), color=(255, 128, 0), isSignal=True, parent_process="scenarioA"),
            #Process("scenarioA_mpi_4_mA_1p33_ctau_1p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p90_ctau_0p1", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p90_ctau_10", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=10mm$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p90_ctau_100", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=100mm$"), color=(255, 128, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p90_ctau_1p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=1mm$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),

            # Process("scenarioA_mpi_4_mA_0p40_ctau_0p25", Label(latex="sc.A, $m_{\pi}=4$, $m_A=0.40$, $c\\tau=0.25mm$"), color=(0, 255, 255), isSignal=True, parent_process="scenarioA"),
            # #Process("scenarioA_mpi_4_mA_0p40_ctau_0p3", Label(latex="sc.A, $m_{\pi}=4$, $m_A=0.40$, $c\\tau=0.3mm$"), color=(135, 206, 235), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_0p6", Label(latex="sc.A, $m_{\pi}=4$, $m_A=0.40$, $c\\tau=0.6mm$"), color=(100, 149, 237), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_25p0", Label(latex="sc.A, $m_{\pi}=4$, $m_A=0.40$, $c\\tau=25mm$"), color=(210, 105, 30), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_2p5", Label(latex="sc.A, $m_{\pi}=4$, $m_A=0.40$, $c\\tau=2.5mm$"), color=(255, 69, 0), isSignal=True, parent_process="scenarioA"),
            # #Process("scenarioA_mpi_4_mA_0p40_ctau_30", Label(latex="sc.A, $m_{\pi}=4$, $m_A=0.40$, $c\\tau=30mm$"), color=(255, 99, 71), isSignal=True, parent_process="scenarioA"),
            # #Process("scenarioA_mpi_4_mA_0p40_ctau_3p0", Label(latex="sc.A, $m_{\pi}=4$, $m_A=0.40$, $c\\tau=3.0mm$"), color=(123, 104, 238), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_60p0", Label(latex="sc.A, $m_{\pi}=4$, $m_A=0.40$, $c\\tau=60mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_6p0", Label(latex="sc.A, $m_{\pi}=4$, $m_A=0.40$, $c\\tau=6.0mm$"), color=(255, 99, 71), isSignal=True, parent_process="scenarioA"),

            # Process("scenarioA_mpi_4_mA_1p33_ctau_0p25", Label(latex="sc.A, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=0.25mm$"), color=(0, 255, 0), isSignal=True, parent_process="scenarioA"),
            # #Process("scenarioA_mpi_4_mA_1p33_ctau_0p3", Label(latex="sc.A, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=0.3mm$"), color=(255, 140, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_0p6", Label(latex="sc.A, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=0.6mm$"), color=(75, 0, 130), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_25p0", Label(latex="sc.A, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=25mm$"), color=(123, 104, 238), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_2p5", Label(latex="sc.A, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=2.5mm$"), color=(138, 43, 226), isSignal=True, parent_process="scenarioA"),
            # #Process("scenarioA_mpi_4_mA_1p33_ctau_30", Label(latex="sc.A, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=30mm$"), color=(255, 165, 0), isSignal=True, parent_process="scenarioA"),
            # #Process("scenarioA_mpi_4_mA_1p33_ctau_3p0", Label(latex="sc.A, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=3.0mm$"), color=(255, 0, 255), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_60p0", Label(latex="sc.A, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=60mm$"), color=(70, 130, 180), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_6p0", Label(latex="sc.A, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=6.0mm$"), color=(0, 100, 0), isSignal=True, parent_process="scenarioA"),
            
            # rew
            # Process("scenarioA_mpi_4_mA_0p40_ctau_8p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=8mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_5p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=5mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_2p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=2mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_80", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_50", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p40_ctau_20", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p80_ctau_8p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=8mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p80_ctau_5p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=5mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p80_ctau_2p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=2mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p80_ctau_80", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p80_ctau_50", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_0p80_ctau_20", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.80$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_0p1_rew", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=0.1mm$ (1->0.1)"), color=(127, 0, 255), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_20", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=20mm$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_50", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=50mm$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_80", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=80mm$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_10_rew_short", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10mm$ (100->10)"), color=(127, 0, 255), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_10_rew", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10mm$ (100->10)"), color=(0, 255, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_10_short", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10mm$ (100K ev)"), color=(0, 153, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_33p3_large", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=33.3mm$ (100->33.3)"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_33p3_small", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=33.3mm$ (10->33.3)"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_100_short", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=100mm$ (100K)"), color=(0, 153, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_3p33_large", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=3.33mm$ (10->3.33)"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_3p33_small", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=3.33mm$ (1.0->3.33)"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_2p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=2mm$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_5p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=5mm$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p33_ctau_8p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=8mm$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_1p0_rew", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=1mm$ (10->1)"), color=(255, 128, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p90_ctau_8p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=8mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p90_ctau_5p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=5mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p90_ctau_2p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=2mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p90_ctau_80", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p90_ctau_50", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_4_mA_1p90_ctau_20", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.90$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),

            ############
            # mpi = 10 #
            ############
            # Process("scenarioA_mpi_10_mA_1p00_ctau_0p1", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_1p00_ctau_10", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_1p00_ctau_100", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_1p00_ctau_1p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_0p1", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_10", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_100", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_1p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_0p1", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_10", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=10mm$"), color=(255, 128, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_100", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_1p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_0p1", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=0.1mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_10", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=10mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_100", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=100mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_1p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=1.0mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),

            # rew
            # Process("scenarioA_mpi_10_mA_1p00_ctau_8p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1.0$, $c\\tau=8mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_1p00_ctau_5p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1.0$, $c\\tau=5mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_1p00_ctau_2p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1.0$, $c\\tau=2mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_1p00_ctau_80", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1.0$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_1p00_ctau_50", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1.0$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_1p00_ctau_20", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1.0$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_8p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2.0$, $c\\tau=8mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_5p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2.0$, $c\\tau=5mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_2p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2.0$, $c\\tau=2mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_80", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2.0$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_50", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2.0$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_2p00_ctau_20", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=2.0$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_8p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=8mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_5p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=5mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_2p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=2mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_80", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_50", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            # Process("scenarioA_mpi_10_mA_3p33_ctau_20", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_8p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=8mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_5p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=5mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_2p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=2mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_80", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=80mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_50", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=50mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_4p90_ctau_20", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=4.90$, $c\\tau=20mm$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioA"),

            ###############
            # scenario B1 #
            ###############
            Process("scenarioB1", Label("scenarioB1"), color=(0, 0, 255), isSignal=True, parent_process="signal"),
            
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=0.1$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_10", Label(latex="sc.B1, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=10$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_100", Label(latex="sc.B1, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=100$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=1.0$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_1_mA_0p33_ctau_1p0_new", Label(latex="sc.B1, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=1.0$ new"), color=(0, 255, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.4$, $c\\tau=0.1$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_10", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.4$, $c\\tau=10$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_100", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.4$, $c\\tau=100$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.4$, $c\\tau=1.0$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=0.1$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_10", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=10$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_100", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=100$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=1.0$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_0p80_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=0.8$, $c\\tau=0.1$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_0p80_ctau_10", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=0.8$, $c\\tau=10$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_0p80_ctau_100", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=0.8$, $c\\tau=100$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_0p80_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=0.8$, $c\\tau=1.0$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=0.1$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_10", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10$"), color=(0, 153, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_100", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=100$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=1.0$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),

            # Process("scenarioB1_mpi_1_mA_0p33_ctau_0p25", Label(latex="sc.B1, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=0.25$"), color=(0, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_0p3", Label(latex="sc.B1, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=0.3$"), color=(255, 0, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_0p6", Label(latex="sc.B1, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=0.6$"), color=(0, 255, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_25p0", Label(latex="sc.B1, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=25$"), color=(0, 255, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_2p5", Label(latex="sc.B1, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=2.5$"), color=(255, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_30", Label(latex="sc.B1, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=30$"), color=(255, 165, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_3p0", Label(latex="sc.B1, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=3$"), color=(255, 140, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_6p0", Label(latex="sc.B1, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=6$"), color=(255, 105, 180), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_1_mA_0p33_ctau_60p0", Label(latex="sc.B1, $m_{\pi}=1$, $m_A=0.33$, $c\\tau=60$"), color=(255, 105, 180), isSignal=True, parent_process="scenarioB1"),

            Process("scenarioB1_mpi_2_mA_0p40_ctau_0p25", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.40$, $c\\tau=0.25$"), color=(255, 69, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_0p3", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.40$, $c\\tau=0.3$"), color=(255, 99, 71), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_0p6", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.40$, $c\\tau=0.6$"), color=(210, 105, 30), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_25p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.40$, $c\\tau=25$"), color=(138, 43, 226), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_2p5", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.40$, $c\\tau=2.5$"), color=(240, 128, 128), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_30", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.40$, $c\\tau=30$"), color=(123, 104, 238), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_3p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.40$, $c\\tau=3$"), color=(0, 100, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_60p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.40$, $c\\tau=60$"), color=(255, 140, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_6p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.40$, $c\\tau=6$"), color=(106, 90, 205), isSignal=True, parent_process="scenarioB1"),

            # Process("scenarioB1_mpi_2_mA_0p67_ctau_0p25", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=0.25$"), color=(75, 0, 130), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_0p3", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=0.3$"), color=(123, 104, 238), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_0p6", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=0.6$"), color=(106, 90, 205), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_25p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=25$"), color=(255, 165, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_2p5", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=2.5$"), color=(0, 255, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_30", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=30$"), color=(0, 255, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_3p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=3$"), color=(255, 0, 255), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_60p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=60$"), color=(255, 105, 180), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_2_mA_0p67_ctau_6p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_A=0.67$, $c\\tau=6$"), color=(138, 43, 226), isSignal=True, parent_process="scenarioB1"),

            # Process("scenarioB1_mpi_4_mA_1p33_ctau_0p25", Label(latex="sc.B1, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=0.25$"), color=(255, 140, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_0p3", Label(latex="sc.B1, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=0.3$"), color=(123, 104, 238), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_0p6", Label(latex="sc.B1, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=0.6$"), color=(75, 0, 130), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_25p0", Label(latex="sc.B1, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=25$"), color=(255, 69, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_2p5", Label(latex="sc.B1, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=2.5$"), color=(255, 99, 71), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_30", Label(latex="sc.B1, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=30$"), color=(106, 90, 205), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_3p0", Label(latex="sc.B1, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=3$"), color=(0, 100, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_60p0", Label(latex="sc.B1, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=60$"), color=(255, 165, 0), isSignal=True, parent_process="scenarioB1"),
            # Process("scenarioB1_mpi_4_mA_1p33_ctau_6p0", Label(latex="sc.B1, $m_{\pi}=4$, $m_A=1.33$, $c\\tau=6$"), color=(255, 0, 255), isSignal=True, parent_process="scenarioB1"),


            Process("scenarioB2", Label("scenarioB2"), color=(0, 204, 0), isSignal=True, parent_process="signal"),
            Process("scenarioB2_mpi_1_mA_0p60_ctau_0p1", Label(latex="sc.B2, $m_{\pi}=1$, $m_{A}=0.6$, $c\\tau=0.1$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_1_mA_0p60_ctau_10", Label(latex="sc.B2, $m_{\pi}=1$, $m_{A}=0.6$, $c\\tau=10$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_1_mA_0p60_ctau_100", Label(latex="sc.B2, $m_{\pi}=1$, $m_{A}=0.6$, $c\\tau=100$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_1_mA_0p60_ctau_1p0", Label(latex="sc.B2, $m_{\pi}=1$, $m_{A}=0.6$, $c\\tau=1.0$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_2_mA_1p10_ctau_0p1", Label(latex="sc.B2, $m_{\pi}=2$, $m_{A}=1.1$, $c\\tau=0.1$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_2_mA_1p10_ctau_10", Label(latex="sc.B2, $m_{\pi}=2$, $m_{A}=1.1$, $c\\tau=10$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_2_mA_1p10_ctau_100", Label(latex="sc.B2, $m_{\pi}=2$, $m_{A}=1.1$, $c\\tau=100$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_2_mA_1p10_ctau_1p0", Label(latex="sc.B2, $m_{\pi}=2$, $m_{A}=1.1$, $c\\tau=1.0$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_4_mA_2p10_ctau_0p1", Label(latex="sc.B2, $m_{\pi}=4$, $m_{A}=2.1$, $c\\tau=0.1$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_4_mA_2p10_ctau_10", Label(latex="sc.B2, $m_{\pi}=4$, $m_{A}=2.1$, $c\\tau=10$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_4_mA_2p10_ctau_100", Label(latex="sc.B2, $m_{\pi}=4$, $m_{A}=2.1$, $c\\tau=100$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_4_mA_2p10_ctau_1p0", Label(latex="sc.B2, $m_{\pi}=4$, $m_{A}=2.1$, $c\\tau=1.0$"), color=(0, 204, 0), isSignal=True, parent_process="scenarioB2"),

            Process("scenarioC", Label("scenarioC"), color=(255, 153, 51), isSignal=True, parent_process="signal"),
            Process("scenarioC_mpi_10_mA_8p00_ctau_0p1", Label(latex="sc.C, $m_{\pi}=10$, $m_{A}=8$, $c\\tau=0.1$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_10_mA_8p00_ctau_10", Label(latex="sc.C, $m_{\pi}=10$, $m_{A}=8$, $c\\tau=10$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_10_mA_8p00_ctau_100", Label(latex="sc.C, $m_{\pi}=10$, $m_{A}=8$, $c\\tau=100$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_10_mA_8p00_ctau_1p0", Label(latex="sc.C, $m_{\pi}=10$, $m_{A}=8$, $c\\tau=1.0$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_2_mA_1p60_ctau_0p1", Label(latex="sc.C, $m_{\pi}=2$, $m_{A}=1.6$, $c\\tau=0.1$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_2_mA_1p60_ctau_10", Label(latex="sc.C, $m_{\pi}=2$, $m_{A}=1.6$, $c\\tau=10$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_2_mA_1p60_ctau_100", Label(latex="sc.C, $m_{\pi}=2$, $m_{A}=1.6$, $c\\tau=100$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_2_mA_1p60_ctau_1p0", Label(latex="sc.C, $m_{\pi}=2$, $m_{A}=1.6$, $c\\tau=1.0$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_4_mA_3p20_ctau_0p1", Label(latex="sc.C, $m_{\pi}=4$, $m_{A}=3.2$, $c\\tau=0.1$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_4_mA_3p20_ctau_10", Label(latex="sc.C, $m_{\pi}=4$, $m_{A}=3.2$, $c\\tau=10$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_4_mA_3p20_ctau_100", Label(latex="sc.C, $m_{\pi}=4$, $m_{A}=3.2$, $c\\tau=100$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_4_mA_3p20_ctau_1p0", Label(latex="sc.C, $m_{\pi}=4$, $m_{A}=3.2$, $c\\tau=1.0$"), color=(255, 153, 51), isSignal=True, parent_process="scenarioC"),

            Process("vector", Label(latex="vector"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("vector_m_10_ctau_100_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_10_ctau_10_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_10_ctau_1_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_10_ctau_500_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=500$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_10_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_15_ctau_100_xiO_1_xiL_1", Label(latex="$c\\tau=100$ mm"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_15_ctau_10_xiO_1_xiL_1", Label(latex="$c\\tau=10$ mm"), color=(153, 153, 255), isSignal=True, parent_process="vector"),
            Process("vector_m_15_ctau_1_xiO_1_xiL_1", Label(latex="$c\\tau=1$ mm"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_15_ctau_500_xiO_1_xiL_1", Label(latex="$c\\tau=500$ mm"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_15_ctau_50_xiO_1_xiL_1", Label(latex="$c\\tau=50$ mm"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_20_ctau_100_xiO_1_xiL_1", Label(latex="vector, $m=20$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_20_ctau_10_xiO_1_xiL_1", Label(latex="Vector portal, $m=20$ GeV, $c\\tau=10$ mm"), color=(0, 153, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_20_ctau_1_xiO_1_xiL_1", Label(latex="vector, $m=20$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_20_ctau_500_xiO_1_xiL_1", Label(latex="vector, $m=20$, $c\\tau=500$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_20_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=20$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_2_ctau_100_xiO_1_xiL_1", Label(latex="vector, $m=2$, $c\\tau=100$"), color=(0, 255, 255), isSignal=True, parent_process="vector"),
            Process("vector_m_2_ctau_10_xiO_1_xiL_1", Label(latex="Vector portal, $m=2$ GeV, $c\\tau=10$ mm"), color=(255, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_2_ctau_10_xiO_1_xiL_1_old", Label(latex="vector, $m=2$ GeV, $c\\tau=10$ mm (Legacy sample)"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_2_ctau_1_xiO_1_xiL_1", Label(latex="vector, $m=2$, $c\\tau=1$"), color=(204, 204, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_2_ctau_500_xiO_1_xiL_1", Label(latex="vector, $m=2$, $c\\tau=500$"), color=(0, 153, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_2_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=2$, $c\\tau=50$"), color=(96, 96, 96), isSignal=True, parent_process="vector"),
            Process("vector_m_5_ctau_100_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_5_ctau_10_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_5_ctau_1_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_5_ctau_500_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=500$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_5_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_12_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=12$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_14_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=14$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_17_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=17$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_19_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=19$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("vector_m_3_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=3$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),

            Process("hzdzd", Label("$H\\to$$Z_dZ_d$"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("hzdzd_mzd_8_ctau_100", Label("$H\\to$ $Z_dZ_d$, $m_{Z_d}=8$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="hzdzd"),
            Process("hzdzd_mzd_8_ctau_1", Label("$H\\to$ $Z_dZ_d$, $m_{Z_d}=8$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="hzdzd"),

            Process("zprime", Label("$Z^'$"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("zprime_mpi_2_ctau_10", Label("$Z^{'}$, $m_{\pi}=2$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="zprime"),

            Process("btophi", Label("$B\\to$$\PhiX$"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("btophi_m_2_ctau_10", Label("$B\\to$$\PhiX$, $m=2$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="btophi"),

            Process("alp_dimuon", Label("ALP"), color=(0, 0, 0), isSignal=True, parent_process="signal"),

            Process("data", Label("Data"), color=(0, 0, 0), isData=True),

            Process("dum", Label("dum"), color=(0, 0, 0)),

            Process("egamma", Label("Data"), color=(0, 0, 0), isData=True, parent_process="data"),
            Process("SingleMuon", Label("Data"), color=(0, 0, 0), isData=True, parent_process="data"),
            Process("LambdaBToJpsiLambda", Label("LambdaBToJpsiLambda"), color=(0, 0, 0), parent_process="background"),
            Process("BToJpsiJPsiToMuMu", Label("BToJpsiJPsiToMuMu"), color=(0, 0, 0), parent_process="background"),
            Process("BuToJpsiK", Label("BuToJpsiK"), color=(0, 0, 0)),
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
            "background": [
                "background",
            ],
            "data": [
                "data",
            ],
            "full": [
                # "ggf_sm",
                # "data_tau",
                # "dy_high",
                # "tt_dl",
                "data",
                "qcd",
                "ww",
                "signal"
            ],
            "sigbkg": [
                # "ggf_sm",
                # "data_tau",
                # "dy_high",
                # "tt_dl",
                "signal",
                "background",
                "data"
            ],
            "sigbkgall": [
                "background",
                "vector_m_2_ctau_10_xiO_1_xiL_1",
                "scenarioA_mpi_10_mA_3p33_ctau_10",
                "scenarioB1_mpi_4_mA_1p33_ctau_10",
                "scenarioB2_mpi_4_mA_2p10_ctau_10",
                "scenarioC_mpi_10_mA_8p00_ctau_10"
            ],
            "vectorbkg": [
               #"vector_m_2_ctau_1_xiO_1_xiL_1",
               "vector_m_2_ctau_10_xiO_1_xiL_1",
               #"vector_m_2_ctau_50_xiO_1_xiL_1",
               #"vector_m_2_ctau_100_xiO_1_xiL_1",
               #"vector_m_2_ctau_500_xiO_1_xiL_1",
               "vector_m_20_ctau_10_xiO_1_xiL_1",
               #"background",
               "data"
            ],
            "scAbkg":[
               "scenarioA_mpi_4_mA_1p33_ctau_10",
               "scenarioA_mpi_4_mA_1p33_ctau_1p0",
               "scenarioA_mpi_1_mA_0p33_ctau_10",
               "scenarioA_mpi_4_mA_0p40_ctau_0p1",
               "data"
            ],
            "scB1bkg":[
               "scenarioB1_mpi_4_mA_1p33_ctau_10",
               "scenarioB1_mpi_1_mA_0p33_ctau_10",
               "data"
            ],
            "sigdata": [
                # "ggf_sm",
                # "data_tau",
                # "dy_high",
                # "tt_dl",
                "signal",
                "data"
            ],
            "bkgscenario": [
                "background",
                "scenarioA_mpi_4_mA_1p33_ctau_10",
                #"scenarioB1_mpi_2_mA_0p40_ctau_1p0",
                "scenarioB1_mpi_4_mA_1p33_ctau_10"
                # "scenarioB2_mpi_2_mA_1p10_ctau_100",
                # "scenarioC_mpi_4_mA_3p20_ctau_0p1"
            ],
            "qcd_background": [
                "qcd_1000toInf",
                "qcd_120to170",
                "qcd_15to20",
                "qcd_170to300",
                "qcd_20to30",
                "qcd_300to470",
                "qcd_30to50",
                "qcd_470to600",
                "qcd_50to80",
                "qcd_600to800",
                "qcd_80to120",
                "qcd_800to1000",
            ],
            "sig": [
                "signal"
            ],
            "jpsi": [
                "data",
                "BuToJpsiK"
            ],
            "jpsi_and_bkg": [
                "data",
                "qcd",
                "BuToJpsiK"
            ],
            "scA_jpsi": [
                "scenarioA_mpi_4_mA_1p33_ctau_10",
                "BuToJpsiK"
            ],
            "rew": [
                "scenarioA_mpi_4_mA_1p33_ctau_0p1",
                "scenarioA_mpi_4_mA_1p33_ctau_0p1_rew",
                "scenarioA_mpi_4_mA_1p33_ctau_1p0",
                "scenarioA_mpi_4_mA_1p33_ctau_1p0_rew",
                "scenarioA_mpi_4_mA_1p33_ctau_10",
                "scenarioA_mpi_4_mA_1p33_ctau_10_rew",
                # "scenarioA_mpi_4_mA_1p33_ctau_100",
            ],
            "rew_test": [
                "scenarioA_mpi_4_mA_1p33_ctau_3p33_large",
                "scenarioA_mpi_4_mA_1p33_ctau_3p33_small",
            ],
            "rew_test_new": [
                "scenarioA_mpi_4_mA_1p33_ctau_33p3_large",
                "scenarioA_mpi_4_mA_1p33_ctau_33p3_small",
            ],
            "stats": [
                "scenarioA_mpi_4_mA_1p33_ctau_100_short",
                "scenarioA_mpi_4_mA_1p33_ctau_100",
            ],
            # "rew": [
                # "scenarioA_mpi_4_mA_1p33_ctau_10",
                # "scenarioA_mpi_4_mA_1p33_ctau_100",
                # "scenarioA_mpi_4_mA_0p40_ctau_1p0",
                # "scenarioA_mpi_4_mA_0p40_ctau_10",
                # "scenarioA_mpi_4_mA_1p33_ctau_0p1",
                # # "scenarioA_mpi_4_mA_1p33_ctau_1p0_rew",
                # "scenarioA_mpi_4_mA_1p33_ctau_1p0",
            # ],
            "scenarioA_mpi_4_mA_1p33_ctau": [
                "scenarioA_mpi_4_mA_1p33_ctau_10",
                "scenarioA_mpi_4_mA_1p33_ctau_1p0",
                "scenarioA_mpi_4_mA_1p33_ctau_100",
                "scenarioA_mpi_4_mA_1p33_ctau_0p1",
            ],
            "alp_dimuon": [
                "alp_dimuon"
            ],
            "scenarioA": [
                "scenarioA"
            ],
            "matveto": [
                "data",
                "data_matveto"
            ],
            "signal_benchmarks": [
                "vector_m_2_ctau_10_xiO_1_xiL_1",
                "scenarioA_mpi_4_mA_1p33_ctau_10",
                "scenarioB1_mpi_4_mA_1p33_ctau_10"
            ],
            "scenarioA_benchmarks":[
              "scenarioA_mpi_4_mA_1p33_ctau_0p1",      
              "scenarioA_mpi_4_mA_1p33_ctau_1p0",  
              "scenarioA_mpi_4_mA_1p33_ctau_10",
              "scenarioA_mpi_4_mA_1p33_ctau_100"
            ],
            "vector":[
              "vector_m_10_ctau_100_xiO_1_xiL_1",
              "vector_m_10_ctau_10_xiO_1_xiL_1",
              "vector_m_10_ctau_1_xiO_1_xiL_1",
              "vector_m_10_ctau_500_xiO_1_xiL_1",
              "vector_m_10_ctau_50_xiO_1_xiL_1",
              "vector_m_15_ctau_100_xiO_1_xiL_1",
              "vector_m_15_ctau_10_xiO_1_xiL_1",
              "vector_m_15_ctau_1_xiO_1_xiL_1",
              "vector_m_15_ctau_500_xiO_1_xiL_1",
              "vector_m_15_ctau_50_xiO_1_xiL_1",
              "vector_m_20_ctau_100_xiO_1_xiL_1",
              "vector_m_20_ctau_10_xiO_1_xiL_1",
              "vector_m_20_ctau_1_xiO_1_xiL_1",
              "vector_m_20_ctau_500_xiO_1_xiL_1",
              "vector_m_20_ctau_50_xiO_1_xiL_1",
              "vector_m_2_ctau_100_xiO_1_xiL_1",
              "vector_m_2_ctau_10_xiO_1_xiL_1",
              "vector_m_2_ctau_1_xiO_1_xiL_1",
              "vector_m_2_ctau_500_xiO_1_xiL_1",
              "vector_m_2_ctau_50_xiO_1_xiL_1",
              "vector_m_5_ctau_100_xiO_1_xiL_1",
              "vector_m_5_ctau_10_xiO_1_xiL_1",
              "vector_m_5_ctau_1_xiO_1_xiL_1",
              "vector_m_5_ctau_500_xiO_1_xiL_1",
              "vector_m_5_ctau_50_xiO_1_xiL_1"
            ],
            "vector_m_10_ctau_100_xiO_1_xiL_1":[
                "vector_m_10_ctau_100_xiO_1_xiL_1"
            ],
            "vector_m_2_ctau_10_validation":[
              "vector_m_2_ctau_10_xiO_1_xiL_1_old",
              "vector_m_2_ctau_10_xiO_1_xiL_1"
            ],
            "scenario_B1_benchmarks":[
               "scenarioB1_mpi_4_mA_1p33_ctau_0p1",
               "scenarioB1_mpi_4_mA_1p33_ctau_100",
               "scenarioB1_mpi_1_mA_0p33_ctau_0p1",
               "scenarioB1_mpi_1_mA_0p33_ctau_100"
            ],
            "scenario_B1_benchmarks_mA_0p33":[
                "scenarioB1_mpi_1_mA_0p33_ctau_1p0",
                "scenarioB1_mpi_1_mA_0p33_ctau_1p0_new"
            ],
            "scenario_A_benchmarks_mA_1p33":[
                "scenarioA_mpi_4_mA_1p33_ctau_10_old",
                "scenarioA_mpi_4_mA_1p33_ctau_10",
                "scenarioA_mpi_4_mA_1p33_ctau_10_new",
                "scenarioA_mpi_4_mA_1p33_ctau_10_nocp5",
                "scenarioA_mpi_4_mA_1p33_ctau_10_nofilter"
            ],
            "test":  [
                "vector_m_2_ctau_10_xiO_1_xiL_1",
                "scenarioB1_mpi_1_mA_0p33_ctau_1p0_new"
            ]
        }

        process_training_names = {
            "default": DotDict(
                processes=[
                    "qcd_15to20",
                    "qcd_1000toInf",
                    "signal"
                ],
                process_group_ids=(
                    (1.0, (0, 1)),
                    (1.0, (2,)),
                )
            )
        }

        # adding reweighed processes
        processes = ObjectCollection(processes)
        processes = self.add_vp_grid_processes(processes)
        processes = self.add_scenario_grid_processes(processes)
        #processes = self.add_rew_processes(processes)

        return processes, process_group_names, process_training_names

    def add_vp_grid_processes(self, processes):
        from config.datasets_vp_grid import d
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

    def add_scenario_grid_processes(self, processes):
        from config.datasets_scenario_grid import d
        for key in d:
            sc = key.split("scenario")[1].split("_")[0]
            mpi = key.split("mpi_")[1].split("_")[0].replace("p", ".")
            mA = key.split("mA_")[1].split("_")[0].replace("p", ".")
            ctau = key.split("ctau_")[1].split("_")[0].replace("p", ".")

            processes.add(
                Process(key,
                    Label(latex="sc.%s, $m_{\pi}=%s$, $m_A=%s$, $c\\tau=%s$" % (sc, mpi, mA, ctau)),
                    color=(0, 0, 0), isSignal=True, parent_process=f"scenario{sc}"),
            )

        return processes

    def add_rew_processes(self, processes):
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
                        orig_process = processes.get(
                            f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_orig}")
                        for ctau_rew in new_ctaus:
                            processes.add(Process(
                                f"scenario{scenario}_mpi_{m1}_mA_{m2}_ctau_{ctau_rew}",
                                Label(latex=(
                                    "sc.{%s}, $m_{\pi}={%s}$, $m_{A}={%s}$, $c\\tau=%smm$" % (
                                        scenario, m1, m2, ctau_rew.replace('p', '.')))),
                                color=(255, 0, 0), isSignal=True, parent_process="scenarioA"
                            ))
        return processes

    def create_signal_dataset(self, name, dataset, xs, tags):
        process_name = name
        for key in ["_rew", "_ext"]:
            process_name = process_name.replace(key, "")

        return Dataset(name=name,
            dataset=dataset,
            process=self.processes.get(process_name),
            check_empty=False,
            prefix="gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/cms",
            xs=xs,
            tags=tags,
        )

    def add_datasets(self):
        sample_path = "/vols/cms/mc3909/bparkProductionAll_V1p0/"
        bdt_path = ("/vols/cms/mmieskol/icenet/output/dqcd/deploy/modeltag__vector_all/"
            "vols/cms/mc3909/bparkProductionAll_V1p0/")

        samples = {
            "qcd_1000toInf": ("QCD_Pt-1000toInf_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_120to170": ("QCD_Pt-120to170_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_120to170_ext": ("QCD_Pt-120to170_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_15to20": ("QCD_Pt-15to20_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_170to300": ("QCD_Pt-170to300_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_20to30": ("QCD_Pt-20to30_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v4"
                "_MINIAODSIM_v1p0_generationSync"),
            # "qcd_20toInf": ("QCD_Pt-20toInf_MuEnrichedPt15_TuneCP5_13TeV_pythia8"
                # "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                # "_MINIAODSIM_v1p0_generationSync"),
            "qcd_300to470": ("QCD_Pt-300to470_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_300to470_ext": ("QCD_Pt-300to470_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext3-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_30to50": ("QCD_Pt-30to50_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_470to600": ("QCD_Pt-470to600_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_470to600_ext": ("QCD_Pt-470to600_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_50to80": ("QCD_Pt-50to80_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v3"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_600to800": ("QCD_Pt-600to800_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_800to1000": ("QCD_Pt-800to1000_MuEnrichedPt5_TuneCP5_13TeV_pythia8_"
                "RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext3-v2_"
                "MINIAODSIM_v1p0_generationSync"),
            "qcd_80to120": ("QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1"
                "_MINIAODSIM_v1p0_generationSync"),
            "qcd_80to120_ext": ("QCD_Pt-80to120_MuEnrichedPt5_TuneCP5_13TeV_pythia8"
                "_RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2"
                "_MINIAODSIM_v1p0_generationSync"),

            # signal
            "m_2_ctau_10_xiO_1_xiL_1": ("HiddenValley_vector_m_2_ctau_10_xiO_1_xiL_1"
                "_privateMC_11X_NANOAODSIM_v1p0_generationSync"),
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
                    for i in range(1, 11)],
                process=self.processes.get("qcd_1000toInf"),
                xs=xs["qcd_1000toInf"],
                friend_datasets="qcd_1000toInf_friend",
                merging={
                    "base": 10,
                },),
            Dataset("qcd_1000toInf_friend",
                folder=bdt_path + samples["qcd_1000toInf"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_120to170",
                folder=[
                    sample_path + samples["qcd_120to170"],
                    sample_path + samples["qcd_120to170_ext"],
                ],
                skipFiles=["{}/output_{}.root".format(
                        sample_path + samples["qcd_120to170"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(
                        sample_path + samples["qcd_120to170_ext"], i)
                        for i in range(1, 11)],
                process=self.processes.get("qcd_120to170"),
                xs=xs["qcd_120to170"],
                friend_datasets="qcd_120to170_friend",
                merging={
                    "base": 10,
                },),
            Dataset("qcd_120to170_friend",
                folder=[
                    bdt_path + samples["qcd_120to170"],
                    bdt_path + samples["qcd_120to170_ext"],
                ],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_15to20",
                folder=sample_path + samples["qcd_15to20"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_15to20"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd_15to20"),
                xs=xs["qcd_15to20"],
                friend_datasets="qcd_15to20_friend"),
            Dataset("qcd_15to20_friend",
                folder=bdt_path + samples["qcd_15to20"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_170to300",
                folder=sample_path + samples["qcd_170to300"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_170to300"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd_170to300"),
                xs=xs["qcd_170to300"],
                friend_datasets="qcd_170to300_friend",
                merging={
                    "base": 10,
                },),
            Dataset("qcd_170to300_friend",
                folder=bdt_path + samples["qcd_170to300"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_20to30",
                folder=sample_path + samples["qcd_20to30"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_20to30"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd_20to30"),
                xs=xs["qcd_20to30"],
                friend_datasets="qcd_20to30_friend"),
            Dataset("qcd_20to30_friend",
                folder=bdt_path + samples["qcd_20to30"],
                process=self.processes.get("dum"),
                tags=["friend"]),

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
                folder=[
                    sample_path + samples["qcd_300to470"],
                    sample_path + samples["qcd_300to470_ext"],
                ],
                skipFiles=["{}/output_{}.root".format(
                        sample_path + samples["qcd_300to470"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(
                        sample_path + samples["qcd_300to470_ext"], i)
                        for i in range(1, 11)],
                process=self.processes.get("qcd_300to470"),
                xs=xs["qcd_300to470"],
                friend_datasets="qcd_300to470_friend",
                merging={
                    "base": 10,
                },),
            Dataset("qcd_300to470_friend",
                folder=[
                    bdt_path + samples["qcd_300to470"],
                    bdt_path + samples["qcd_300to470_ext"],
                ],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_30to50",
                folder=sample_path + samples["qcd_30to50"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_30to50"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd_30to50"),
                xs=xs["qcd_30to50"],
                friend_datasets="qcd_30to50_friend"),
            Dataset("qcd_30to50_friend",
                folder=bdt_path + samples["qcd_30to50"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_470to600",
                folder=[
                    sample_path + samples["qcd_470to600"],
                    sample_path + samples["qcd_470to600_ext"],
                ],
                skipFiles=["{}/output_{}.root".format(
                        sample_path + samples["qcd_470to600"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(
                        sample_path + samples["qcd_470to600_ext"], i)
                        for i in range(1, 11)],
                process=self.processes.get("qcd"),
                xs=xs["qcd_470to600"],
                friend_datasets="qcd_470to600_friend",
                merging={
                    "base": 10,
                },),
            Dataset("qcd_470to600_friend",
                folder=[
                    bdt_path + samples["qcd_470to600"],
                    bdt_path + samples["qcd_470to600_ext"],
                ],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_50to80",
                folder=sample_path + samples["qcd_50to80"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_50to80"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd_50to80"),
                xs=xs["qcd_50to80"],
                friend_datasets="qcd_50to80_friend"),
            Dataset("qcd_50to80_friend",
                folder=bdt_path + samples["qcd_50to80"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_600to800",
                folder=sample_path + samples["qcd_600to800"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_600to800"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd_600to800"),
                xs=xs["qcd_600to800"],
                friend_datasets="qcd_600to800_friend",
                merging={
                    "base": 10,
                },),
            Dataset("qcd_600to800_friend",
                folder=bdt_path + samples["qcd_600to800"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_80to120",
                folder=[
                    sample_path + samples["qcd_80to120"],
                    sample_path + samples["qcd_80to120_ext"],
                ],
                skipFiles=["{}/output_{}.root".format(
                        sample_path + samples["qcd_80to120"], i)
                        for i in range(1, 11)] +
                    ["{}/output_{}.root".format(
                        sample_path + samples["qcd_80to120_ext"], i)
                        for i in range(1, 11)],
                process=self.processes.get("qcd_80to120"),
                xs=xs["qcd_80to120"],
                friend_datasets="qcd_80to120_friend",
                merging={
                    "base": 10,
                },),
            Dataset("qcd_80to120_friend",
                folder=[
                    bdt_path + samples["qcd_80to120"],
                    bdt_path + samples["qcd_80to120_ext"],
                ],
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("qcd_800to1000",
                folder=sample_path + samples["qcd_800to1000"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["qcd_800to1000"], i)
                    for i in range(1, 11)],
                process=self.processes.get("qcd_800to1000"),
                xs=xs["qcd_800to1000"],
                friend_datasets="qcd_800to1000_friend",
                merging={
                    "base": 10,
                },),
            Dataset("qcd_800to1000_friend",
                folder=bdt_path + samples["qcd_800to1000"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            # Dataset("ww",
                # folder="/vols/cms/jleonhol/samples/ww/",
                # process=self.processes.get("ww"),
                # xs=12.178),

            ## signal
            Dataset("m_2_ctau_10_xiO_1_xiL_1",
                folder=sample_path + samples["m_2_ctau_10_xiO_1_xiL_1"],
                skipFiles=["{}/output_{}.root".format(
                    sample_path + samples["m_2_ctau_10_xiO_1_xiL_1"], i)
                    for i in range(1, 6)],
                process=self.processes.get("signal"),
                xs=43.9 * 0.01,# FIXME
                friend_datasets="m_2_ctau_10_xiO_1_xiL_1_friend"),
            Dataset("m_2_ctau_10_xiO_1_xiL_1_friend",
                folder=bdt_path + samples["m_2_ctau_10_xiO_1_xiL_1"],
                process=self.processes.get("dum"),
                tags=["friend"]),

            ## data
            Dataset("data_2018b",
                folder=sample_path + "ParkingBPH1_Run2018B-05May2019-v2_MINIAOD_v1p0_generationSync/",
                process=self.processes.get("data"),
                friend_datasets="data_2018b_friend",
                merging={
                    "base": 20,
                },),
            Dataset("data_2018b_friend",
                folder=bdt_path + "ParkingBPH1_Run2018B-05May2019-v2_MINIAOD_v1p0_generationSync/",
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("data_2018c",
                folder=sample_path + "ParkingBPH1_Run2018C-05May2019-v1_MINIAOD_v1p0_generationSync/",
                process=self.processes.get("data"),
                friend_datasets="data_2018c_friend",
                merging={
                    "base": 20,
                },),
            Dataset("data_2018c_friend",
                folder=bdt_path + "ParkingBPH1_Run2018C-05May2019-v1_MINIAOD_v1p0_generationSync",
                process=self.processes.get("dum"),
                tags=["friend"]),

            Dataset("data_2018d",
                folder=sample_path + "tmp",
                process=self.processes.get("data"),
                friend_datasets="data_2018d_friend",
                merging={
                    "base": 20,
                },),
            Dataset("data_2018d_friend",
                folder=bdt_path + "tmp",
                process=self.processes.get("dum"),
                tags=["friend"]),
        ]
        return ObjectCollection(datasets)

    def add_features(self):

        resonance_masses = {
            "ks": (0.43, 0.49),
            "eta": (0.52, 0.58),
            "rho": (0.73, 0.84),  # rho/omega
            "phi": (0.96, 1.08),
            "jpsi": (2.91, 3.27),
            "psi2s": (3.47, 3.89),
            "upsilon1s": (8.99, 9.87),
            "upsilon2s": (9.61, 10.39),
            "upsilon3s": (9.87, 10.77),
        }
        '''
        resonance_mass_veto = "(%s)" % jrs(
            ["{{muonSV_bestchi2_mass}} < %s && {{muonSV_bestchi2_mass}} > %s" % (elem[0], elem[1])
                for elem in resonance_masses.values()],
            op="and"
        )
        '''
        resonance_mass_veto = ("muonSV_bestchi2_mass < 0.43 || (muonSV_bestchi2_mass > 0.49 && muonSV_bestchi2_mass < 0.52)||" 
                              "(muonSV_bestchi2_mass > 0.58 && muonSV_bestchi2_mass < 0.73)||"
                              "(muonSV_bestchi2_mass > 0.84 && muonSV_bestchi2_mass < 0.96)||"
                              "(muonSV_bestchi2_mass > 1.08 && muonSV_bestchi2_mass < 2.91)||"
                              "(muonSV_bestchi2_mass > 3.27 && muonSV_bestchi2_mass < 3.47)||"
                              "(muonSV_bestchi2_mass > 3.89 && muonSV_bestchi2_mass < 8.99)||"
                              "(muonSV_bestchi2_mass > 9.87 && muonSV_bestchi2_mass < 9.61)||"
                              "muonSV_bestchi2_mass > 10.77")
                            
        features = [
            Feature("event", "event", binning=(100, -0.5, 10000),
                x_title=Label("nJet")),

            Feature("njet", "nJet", binning=(10, -0.5, 9.5),
                x_title=Label("nJet")),
            Feature("jet_pt", "Jet_pt", binning=(30, 0, 150),
                x_title=Label("jet p_{T}"),
                units="GeV",
                central="jet_smearing"),
            Feature("jet_eta", "Jet_eta", binning=(50, -5, 5),
                x_title=Label("jet #eta"),),
            Feature("jet_phi", "Jet_phi", binning=(48, -6, 6),
                x_title=Label("jet #phi"),),
            Feature("jet_mass", "Jet_mass", binning=(30, 0, 150),
                x_title=Label("jet mass"),
                units="GeV"),

            Feature("jet_chEmEF", "Jet_chEmEF", binning=(20, 0, 2),
                x_title=Label("jet chEmEF")),
            Feature("jet_chHEF", "Jet_chHEF", binning=(20, 0, 2),
                x_title=Label("jet chHEF")),
            Feature("jet_neEmEF", "Jet_neEmEF", binning=(20, 0, 2),
                x_title=Label("jet neEmEF")),
            Feature("jet_neHEF", "Jet_neHEF", binning=(20, 0, 2),
                x_title=Label("jet neHEF")),
            Feature("jet_muEF", "Jet_muEF", binning=(20, 0, 2),
                x_title=Label("jet muEF")),
            Feature("jet_muonSubtrFactor", "Jet_muonSubtrFactor", binning=(20, 0, 1),
                x_title=Label("jet muonSubtrFactor")),
            Feature("jet_chFPV0EF", "Jet_chFPV0EF", binning=(20, 0, 2),
                x_title=Label("jet chFPV0EF")),
            Feature("jet_nMuons", "Jet_nMuons", binning=(5, -0.5, 4.5),
                x_title=Label("jet nMuons")),
            Feature("jet_nElectrons", "Jet_nElectrons", binning=(5, -0.5, 4.5),
                x_title=Label("jet nElectrons")),
            Feature("jet_nConstituents", "Jet_nConstituents", binning=(20, 0.5, 40.5),
                x_title=Label("jet nConstituents")),
            Feature("jet_btagDeepB", "Jet_btagDeepB", binning=(20, 0, 1),
                x_title=Label("jet btagDeepB")),
            Feature("jet_btagDeepC", "Jet_btagDeepC", binning=(20, 0, 1),
                x_title=Label("jet btagDeepC")),
            Feature("jet_qgl", "Jet_qgl", binning=(20, 0, 1),
                x_title=Label("jet qgl"), ),#selection="Jet_qgl >= 0"),
            Feature("Jet_puIdDisc", "Jet_puIdDisc", binning=(50, -1, 1),
                x_title=Label("jet puIdDisc")),
            Feature("jet_muonIdx1", "Jet_muonIdx1", binning=(10, -0.5, 9.5),
                x_title=Label("jet muonIdx1")),
            Feature("jet_muonIdx2", "Jet_muonIdx2", binning=(10, -0.5, 9.5),
                x_title=Label("jet muonIdx2")),

            Feature("jet_selected", "{{jet_pt}}[Jet_selected > 0].size()", binning=(6, -0.5, 5.5),
                x_title=Label("Number of selected jets")),

            Feature("nmuon", "nMuon", binning=(11, -0.5, 10.5),
                x_title=Label("nMuon"), tags=["bdt"]),
            Feature("muon_pt", "Muon_pt", binning=(100, 0, 200),
                x_title=Label("muon p_{T}"),
                units="GeV", tags=["bdt"]),
            Feature("muon_pt_3", "Muon_pt.at(3)", selection = "nMuon >= 4", binning=(50, 0, 150),
                x_title=Label("muon_p_{T}_3"),
                units="GeV"),
            Feature("muon_pt_2", "Muon_pt.at(2)", selection = "nMuon >= 3",  binning=(50, 0, 150),
                x_title=Label("muon_p_{T}_2"),
                units="GeV"),
            Feature("muon_pt_1", "Muon_pt.at(1)", selection = "nMuon >= 2", binning=(50, 0, 150),
                x_title=Label("muon_p_{T}_1"),
                units="GeV"),
            Feature("muon_pt_0", "Muon_pt.at(0)", binning=(80, 0, 80),
                x_title=Label("Leading muon p_{T}"),
                units="GeV"),
            Feature("muon_eta", "Muon_eta", binning=(100, -3.0, 3.0),
                x_title=Label("muon #eta"), tags=["bdt"]),
            Feature("muon_eta_3", "Muon_eta.at(3)", selection = "nMuon >= 4", binning=(50, -5, 5),
                x_title=Label("muon_#eta_3"),),
            Feature("muon_phi", "MuonBPark_phi", binning=(48, -6, 6),
                x_title=Label("muon #phi"), tags=["bdt"]),
            Feature("muon_phi_3", "Muon_phi.at(3)", selection = "nMuon >= 4", binning=(50, -6, 6),
                x_title=Label("muon_#phi_3"),),
            Feature("muon_mass", "MuonBPark_mass", binning=(120, 0, 4),
                x_title=Label("muon mass"),
                units="GeV"),

            Feature("muon_ptErr", "MuonBPark_ptErr", binning=(20, 0, 1),
                x_title=Label("muon ptErr"), tags=["bdt"]),
            Feature("muon_dxy_1", "Muon_dxy.at(1)", selection = "nMuon >= 2", binning=(50, -5, 5),
                x_title=Label("muon dxy_1")),
            Feature("muon_dxy_3", "Muon_dxy.at(3)", selection = "nMuon >= 4", binning=(50, -5, 5),
                x_title=Label("muon_dxy_3")),
            Feature("muon_dxy", "Muon_dxy", binning=(100, -5.5, 5.5),
                x_title=Label("muon_dxy"), tags=["bdt"]),
            Feature("muon_dxy_abs", "abs(Muon_dxy)", binning=(50, 0.0, 5.5),
                x_title=Label("muon_dxy_abs")),   
            Feature("muon_dxyErr", "Muon_dxyErr", binning=(100, 0, 0.14),
                x_title=Label("muon dxyErr")),
            Feature("muon_dxyErr_0", "Muon_dxyErr.at(0)", binning=(50, 0, 0.5),
                x_title=Label("muon dxyErr_0")),
            Feature("muon_dxysig", "Muon_dxy/Muon_dxyErr", binning=(100, 0, 2500),
                x_title=Label("muon_dxy")),
            Feature("muon_dz", "Muon_dz", binning=(100, -36, 36),
                x_title=Label("muon dz"), tags=["bdt"]),
            Feature("muon_dz_3", "Muon_dz.at(3)", selection = "nMuon >= 4", binning=(50, -25, 25),
                x_title=Label("muon_dz_3")),
            Feature("muon_dzErr", "Muon_dzErr", binning=(100, 0, 5.4),
                x_title=Label("muon dzErr"), tags=["bdt"]),
            Feature("muon_dzErr_0", "Muon_dzErr.at(0)", binning=(50, 0, 0.5),
                x_title=Label("muon dzErr_0")),
            Feature("muon_ip3d", "Muon_ip3d", binning=(100, 0, 30),
                x_title=Label("muon ip3d"), tags=["bdt"]),
            Feature("muon_ip3d_0", "Muon_ip3d.at(0)", binning=(50, 0, 5),
                x_title=Label("muon ip3d_0")),
            Feature("muon_sip3d", "Muon_sip3d", binning=(100, 0, 5000),
                x_title=Label("muon sip3d"), tags=["bdt"]),
            Feature("muon_sip3d_0", "Muon_sip3d.at(0)", binning=(100, 0, 1500),
                x_title=Label("muon sip3d_0")),
            Feature("muon_charge", "MuonBPark_charge", binning=(3, -1.5, 1.5),
                x_title=Label("muon charge"), tags=["bdt"]),
            Feature("muon_tightId", "Muon_tightId", binning=(2, -0.5, 1.5),
                x_title=Label("muon_tightId"), tags=["bdt"]),
            Feature("muon_tightId_0", "Muon_tightId.at(0)", binning=(2, -0.5, 1.5),
                x_title=Label("muon_tightId_0")),
            # softmva not available for MuonBPark col
            Feature("muon_pfRelIso03_all", "Muon_pfRelIso03_all", binning=(70, 0, 7),
                x_title=Label("muon pfRelIso03_all"), tags=["bdt"]),
            Feature("muon_pfRelIso03_all_0", "Muon_pfRelIso03_all.at(0)", binning=(70, 0, 7),
                x_title=Label("muon pfRelIso03_all_0")),
            Feature("muon_pfRelIso03_all_1", "Muon_pfRelIso03_all.at(1)", binning=(70, 0, 7),
                x_title=Label("muon pfRelIso03_all_1")),
            # Feature("muon_miniPFRelIso_all", "MuonBPark_miniPFRelIso_all", binning=(70, 0, 7),
                # x_title=Label("muon miniPFRelIso_all")),
            Feature("muon_softMva", "Muon_softMva", binning=(50, 0, 1),
                x_title=Label("muon_softMva"), tags=["bdt"]),
            Feature("muon_softMva_2", "Muon_softMva.at(2)", selection = "nMuon >= 3", binning=(50, 0, 1),
                x_title=Label("muon_softMva_2")),
            Feature("muon_softMva_3", "Muon_softMva.at(3)", selection = "nMuon >= 4", binning=(50, 0, 1),
                x_title=Label("muon_softMva_3")),
            Feature("muon_jetIdx_0", "Muon_jetIdx.at(0)", binning=(5, 0, 5),
                x_title=Label("muon_jetIdx_0")),
            Feature("muon_miniPFRelIso_all", "Muon_miniPFRelIso_all", binning=(50, 0, 20),
                x_title=Label("muon_miniPFRelIso_all"), tags=["bdt"]),
            Feature("muon_miniPFRelIso_all_0", "Muon_miniPFRelIso_all.at(0)", binning=(50, 0, 20),
                x_title=Label("muon_miniPFRelIso_all_0")),
            Feature("muonBPark_trigger_matched_pt", "MuonBPark_pt[MuonBPark_fired_HLT_Mu9_IP6 > 0 || MuonBPark_fired_HLT_Mu7_IP4 > 0 || MuonBPark_fired_HLT_Mu8_IP3 > 0 || MuonBPark_fired_HLT_Mu8_IP5 > 0 || MuonBPark_fired_HLT_Mu8_IP6 > 0 || MuonBPark_fired_HLT_Mu9_IP4 > 0 || MuonBPark_fired_HLT_Mu9_IP5 > 0 || MuonBPark_fired_HLT_Mu12_IP6 > 0]", 
                binning=(100, 0, 100),
                x_title=Label("muon p_{T}"),
                units="GeV"),
            Feature("muonBPark_not_trigger_matched_pt", "MuonBPark_pt[MuonBPark_fired_HLT_Mu9_IP6 == 0 && MuonBPark_fired_HLT_Mu7_IP4 == 0 && MuonBPark_fired_HLT_Mu8_IP3 == 0 && MuonBPark_fired_HLT_Mu8_IP5 == 0 && MuonBPark_fired_HLT_Mu8_IP6 == 0 && MuonBPark_fired_HLT_Mu9_IP4 == 0 && MuonBPark_fired_HLT_Mu9_IP5 == 0 && MuonBPark_fired_HLT_Mu12_IP6 == 0]", 
                binning=(100, 0, 100),
                x_title=Label("muon p_{T}"),
                units="GeV"),
            Feature("muonBPark_pt", "MuonBPark_pt", 
                binning=(100, 0, 100),
                x_title=Label("muon p_{T}"),
                units="GeV"),
            
            
            # MuonBPark_jetIdx not available

            Feature("min_chi2_index", "min_chi2_index", binning=(10, -0.5, 9.5),
                x_title=Label("min_chi2_index")),
            Feature("muonSV_chi2", "muonSV_chi2", binning=(50, 0, 1500),
                x_title=Label("muonSV chi2"), tags=["bdt"]),
            Feature("muonSV_chi2_0", "muonSV_chi2.at(ArgMin(muonSV_chi2))", binning=(50, 0, 10),
                x_title=Label("muonSV_chi2_0")),
            Feature("muonSV_chi2_1", "muonSV_chi2.at(Argsort(muonSV_chi2)[1])", selection = "nmuonSV >= 2", binning=(50, 0, 1500),
                x_title=Label("muonSV_chi2_1")),
            Feature("muonSV_pAngle", "muonSV_pAngle", binning=(50, 0, 3.5),
                x_title=Label("muonSV pAngle"), tags=["bdt"]),
            Feature("muonSV_pAngle_0", "muonSV_pAngle.at(ArgMin(muonSV_chi2))", binning=(50, 0, 3.5),
                x_title=Label("muonSV pAngle_0")),
            Feature("muonSV_dlen", "muonSV_dlen", binning=(50, 0, 25),
                x_title=Label("muonSV dlen"), tags=["bdt"]),
            Feature("muonSV_dlen_0", "muonSV_dlen.at(ArgMin(muonSV_chi2))", binning=(50, 0, 25),
                x_title=Label("muonSV_dlen_0")),
            Feature("muonSV_dlenSig", "muonSV_dlenSig", binning=(100, 0, 1500),
                x_title=Label("muonSV dlenSig"), tags=["bdt"]),
            Feature("muonSV_dxy_with_material_veto", "muonSV_dxy.at(ArgMin(muonSV_chi2))", binning=(1000, 0, 50), 
                selection = "(muonSV_bestchi2_dxy > 0.0 && muonSV_bestchi2_dxy < 6.7) ||"
                         "(muonSV_bestchi2_dxy > 7.3 && muonSV_bestchi2_dxy < 10.5) ||" 
                         "(muonSV_bestchi2_dxy > 11.5 && muonSV_bestchi2_dxy < 15.6) ||" 
                         "(muonSV_bestchi2_dxy > 16.6)",
                x_title=Label("muonSV lxy (cm)")),
            Feature("muonSV_dxy_without_material_veto", "muonSV_dxy[muonSV_chi2==Min(muonSV_chi2)]", binning=(1000, 0, 50),
                x_title=Label("muonSV lxy (cm)")),
            Feature("muonSV_dxy", "muonSV_dxy", binning=(100, 0, 25), x_title=Label("muonSV lxy (cm)"), tags=["bdt"]),
            Feature("muonSV_dxy_0", "muonSV_dxy.at(ArgMin(muonSV_chi2))", binning=(100, 0, 25),
                x_title=Label("muonSV_dxy_0 (cm)")),
            Feature("muonSV_dz", "abs(muonSV_bestchi2_z - PV_z)", binning=(200, 0, 70),
                x_title=Label("muonSV lz (cm)")),
            Feature("muonSV_dy", "muonSV_bestchi2_y - PV_y", selection = resonance_mass_veto, binning=(100, 0, 25),
                x_title=Label("muonSV ly (cm)")),
            Feature("muonSV_dx", "muonSV_bestchi2_x - PV_x", selection = resonance_mass_veto, binning=(100, 0, 25),
                x_title=Label("muonSV lx (cm)")),
            Feature("muonSV_dxySig", "muonSV_dxySig", binning=(100, 0, 2500),
                x_title=Label("muonSV dxySig"), tags=["bdt"]),
            Feature("muonSV_dxySig_0", "muonSV_dxySig.at(ArgMin(muonSV_chi2))", binning=(100, 0, 2500),
                x_title=Label("muonSV_dxySig_0")),
            Feature("muonSV_dxy_minchi2", "muonSV_dxy[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(40, 0, 20),
                x_title=Label("muonSV dxy"),
                units="cm"),
            Feature("muonSV_dxy_minchi2_matveto", "muonSV_dxy.at(ArgMin(muonSV_chi2[muonSV_material_veto == 1]))",
                binning=(40, 0, 20),
                x_title=Label("muonSV dxy"),
                units="cm"),
            Feature("muonSV_z_minchi2", "abs(muonSV_z[muonSV_chi2==Min(muonSV_chi2)])",
                binning=(900, 0, 300),
                x_title=Label("muonSV z"),
                units="cm"),
            Feature("muonSV_z_minchi2_lowrange", "muonSV_z[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(200, -10, 10),
                x_title=Label("muonSV z"),
                units="cm"),
            Feature("muonSV_z_minchi2_dxy_cut", "abs(muonSV_z[muonSV_chi2==Min(muonSV_chi2) && !( "
                    "(muonSV_dxy > 6.7 && muonSV_dxy < 7.3) || "
                    "(muonSV_dxy > 10.5 && muonSV_dxy < 11.5) || "
                    "(muonSV_dxy > 15.6 && muonSV_dxy < 16.6)"
                ")])",
                binning=(900, 0, 300),
                x_title=Label("muonSV z (dxy cut)"),
                units="cm"),

            Feature("muonSV_x_minchi2", "muonSV_x[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(500, -12, 12),
                x_title=Label("muonSV x"),
                units="cm"),
            Feature("muonSV_y_minchi2", "muonSV_y[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(500, -12, 12),
                x_title=Label("muonSV y"),
                units="cm"),
            Feature("muonSV_x_minchi2_matveto_final", "muonSV_x[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(500, -12, 12),
                selection = "(muonSV_dxy[ArgMin(muonSV_chi2)] > 0.0 && muonSV_dxy[ArgMin(muonSV_chi2)] < 6.4 && (abs(muonSV_z[ArgMin(muonSV_chi2)]) < 27.0 || abs(muonSV_z[ArgMin(muonSV_chi2)]) > 52.0)) ||"
                         "(muonSV_dxy[ArgMin(muonSV_chi2)] > 7.3 && muonSV_dxy[ArgMin(muonSV_chi2)] < 10.5 && (abs(muonSV_z[ArgMin(muonSV_chi2)]) < 27.0 || abs(muonSV_z[ArgMin(muonSV_chi2)]) > 52.0))||" 
                         "(muonSV_dxy[ArgMin(muonSV_chi2)] > 11.5 && muonSV_dxy[ArgMin(muonSV_chi2)] < 15.6 && (abs(muonSV_z[ArgMin(muonSV_chi2)]) < 27.0 || abs(muonSV_z[ArgMin(muonSV_chi2)]) > 52.0))||" 
                         "(muonSV_dxy[ArgMin(muonSV_chi2)] > 16.6 && (abs(muonSV_z[ArgMin(muonSV_chi2)]) < 27.0 || abs(muonSV_z[ArgMin(muonSV_chi2)]) > 52.0))",
                x_title=Label("muonSV x (material veto applied)"),
                units="cm"),
            Feature("muonSV_y_minchi2_matveto_final", "muonSV_y[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(500, -12, 12),
                selection = "(muonSV_dxy[ArgMin(muonSV_chi2)] > 0.0 && muonSV_dxy[ArgMin(muonSV_chi2)] < 6.4 && (abs(muonSV_z[ArgMin(muonSV_chi2)]) < 27.0 || abs(muonSV_z[ArgMin(muonSV_chi2)]) > 52.0)) ||"
                         "(muonSV_dxy[ArgMin(muonSV_chi2)] > 7.3 && muonSV_dxy[ArgMin(muonSV_chi2)] < 10.5 && (abs(muonSV_z[ArgMin(muonSV_chi2)]) < 27.0 || abs(muonSV_z[ArgMin(muonSV_chi2)]) > 52.0))||" 
                         "(muonSV_dxy[ArgMin(muonSV_chi2)] > 11.5 && muonSV_dxy[ArgMin(muonSV_chi2)] < 15.6 && (abs(muonSV_z[ArgMin(muonSV_chi2)]) < 27.0 || abs(muonSV_z[ArgMin(muonSV_chi2)]) > 52.0))||" 
                         "(muonSV_dxy[ArgMin(muonSV_chi2)] > 16.6 && (abs(muonSV_z[ArgMin(muonSV_chi2)]) < 27.0 || abs(muonSV_z[ArgMin(muonSV_chi2)]) > 52.0))",
                x_title=Label("muonSV y (material veto applied)"),
                units="cm"),
            Feature("muonSV_x_minchi2_matveto", "muonSV_x.at(ArgMin(muonSV_chi2[muonSV_material_veto == 1]))",
                binning=(500, -12, 12),
                x_title=Label("muonSV x (min #chi^2, Mat. veto applied)"),
                units="cm"),
            Feature("muonSV_y_minchi2_matveto", "muonSV_y.at(ArgMin(muonSV_chi2[muonSV_material_veto == 1]))",
                binning=(500, -12, 12),
                x_title=Label("muonSV y (min #chi^2, Mat. veto applied)"),
                units="cm"),
            Feature("muonSV_x_matveto", "muonSV_x[muonSV_material_veto == 1]",
                binning=(500, -20, 20),
                x_title=Label("muonSV x (Mat. veto applied)"),
                units="cm"),
            Feature("muonSV_y_matveto", "muonSV_y[muonSV_material_veto == 1]",
                binning=(500, -20, 20),
                x_title=Label("muonSV y (Mat. veto applied)"),
                units="cm"),
            Feature("muonSV_material_veto_minchi2", "muonSV_material_veto[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(2, -0.5, 1.5),
                x_title=Label("muonSV material veto)")
                ),

            Feature("muonSV_dxy_minchi2_lowrange", "muonSV_dxy[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(100, 0, 2),
                x_title=Label("muonSV dxy"),
                units="cm"),
            Feature("muonSV_dxy_minchi2_chi2_10_lowrange",
                "muonSV_dxy[(muonSV_chi2 < 10) && (muonSV_chi2==Min(muonSV_chi2))]",
                binning=(100, 0, 2),
                x_title=Label("muonSV dxy, #chi^{2}<10"),
                units="cm"),
            Feature("muonSV_dxysig_minchi2", "muonSV_dxySig[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(100, 0, 2500),
                x_title=Label("muonSV dxysig")),
            Feature("muonSV_dxysig_minchi2_lowrange", "muonSV_dxySig[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(100, 0, 20),
                x_title=Label("muonSV dxysig")),


            # material veto distances
            Feature("muonSV_min_material_dxy_minchi2", "muonSV_min_material_dxy[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(1000, 0, 1),
                x_title=Label("muonSV min material dxy (min #chi^{2})"),
                units="cm"),
            Feature("muonSV_min_material_dz_minchi2", "muonSV_min_material_z[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(1000, 0, 1),
                x_title=Label("muonSV min material z (min #chi^{2})"),
                units="cm"),
            Feature("muonSV_min_material_dz_minchi2_long", "muonSV_min_material_z[muonSV_chi2==Min(muonSV_chi2)]",
                binning=(1000, 0, 50),
                x_title=Label("muonSV min material z (min #chi^{2})"),
                units="cm"),
            Feature("muonSV_min_material_dz_minchi2_long_eta0p5", "muonSV_min_material_z["
                "muonSV_chi2==Min(muonSV_chi2) &&"
                "abs(muonSV_mu1eta) < 0.5 && abs(muonSV_mu2eta) < 0.5"
                "]",
                binning=(1000, 0, 50),
                x_title=Label("muonSV min material z (min #chi^{2}), #eta(#mu_{1})<0.5, #eta(#mu_{2})<0.5"),
                units="cm"),
            Feature("muonSV_min_material_dz_minchi2_long_eta1p0", "muonSV_min_material_z["
                    "muonSV_chi2==Min(muonSV_chi2) &&"
                    "abs(muonSV_mu1eta) < 1.0 && abs(muonSV_mu2eta) < 1.0"
                "]",
                binning=(1000, 0, 50),
                x_title=Label("muonSV min material z (min #chi^{2}), #eta(#mu_{1})<1.0, #eta(#mu_{2})<1.0"),
                units="cm"),
            Feature("muonSV_min_material_dz_long", "muonSV_min_material_z",
                binning=(1000, 0, 50),
                x_title=Label("muonSV min material z5"),
                units="cm"),
            Feature("muonSV_min_material_dz_long_dxy0p2", "muonSV_min_material_z["
                    "muonSV_min_material_dxy < 0.2"
                "]",
                binning=(1000, 0, 50),
                x_title=Label("muonSV min material z, muonSV_min_material_dxy < 0.2"),
                units="cm"),

            Feature("muonSV_dxy_matveto", "muonSV_dxy[muonSV_material_veto == 1]", binning=(100, 0, 25),
                x_title=Label("muonSV dxy (mat. veto)"),
                units="cm", selection_name="mat. veto applied"),
            Feature("muonSV_z_matveto", "muonSV_z[muonSV_material_veto == 1]", binning=(200, -50, 50),
                x_title=Label("muonSV z (mat. veto)"), units="cm"),

            Feature("material_z", "tracker_mat_z",
                binning=(1000, -50, 50),
                x_title=Label("Pixel tracker z"),
                units="cm"),

            Feature("material_xy", "tracker_mat_xy",
                binning=(1000, 0, 25),
                x_title=Label("Pixel tracker r"),
                units="cm"),

            # local distances
            Feature("muonSV_min_d_x", "muonSV_min_d_x",
                binning=(1000, 0, 5),
                x_title=Label("muonSV - pixel module min #Delta x"),
                units="cm"),
            Feature("muonSV_min_d_y", "muonSV_min_d_y",
                binning=(1000, 0, 5),
                x_title=Label("muonSV - pixel module min #Delta y"),
                units="cm"),
            Feature("muonSV_min_d_z", "muonSV_min_d_z",
                binning=(1000, 0, 5),
                x_title=Label("muonSV - pixel module min #Delta z"),
                units="cm"),
            Feature("muonSV_min_d_x_dxyrange", f"muonSV_min_d_x[!({self.dxy_cut_all})]",
                binning=(1000, 0, 5),
                x_title=Label("muonSV - pixel module min #Delta x (In material dxy regions)"),
                units="cm"),
            Feature("muonSV_min_d_y_dxyrange", f"muonSV_min_d_y[!({self.dxy_cut_all})]",
                binning=(1000, 0, 5),
                x_title=Label("muonSV - pixel module min #Delta y (In material dxy regions)"),
                units="cm"),
            Feature("muonSV_min_d_z_dxyrange", f"muonSV_min_d_z[!({self.dxy_cut_all})]",
                binning=(1000, 0, 5),
                x_title=Label("muonSV - pixel module min #Delta z (In material dxy regions)"),
                units="cm"),

            Feature("muonSV_mu1pt", "muonSV_mu1pt", binning=(30, 0, 150),
                x_title=Label("muonSV muon1 p_{T}"),
                units="GeV", tags=["bdt"]),
            Feature("muonSV_mu1pt_3", "muonSV_mu1pt", "muonSV_mu1pt.at(Argsort(muonSV_chi2)[3])", selection = "nmuonSV >= 4",binning=(30, 0, 150),
                x_title=Label("muonSV_muon1_p_{T}_3"),
                units="GeV"),
            Feature("muonSV_mu1eta", "muonSV_mu1eta", binning=(50, -5, 5),
                x_title=Label("muonSV muon1 #eta"), tags=["bdt"]),
            Feature("muonSV_mu1phi", "muonSV_mu1phi", binning=(48, -6, 6),
                x_title=Label("muonSV muon1 #phi"), tags=["bdt"]),
            Feature("muonSV_mu2pt", "muonSV_mu2pt", binning=(30, 0, 150),
                x_title=Label("muonSV muon2 p_{T}"),
                units="GeV", tags=["bdt"]),
            Feature("muonSV_mu2pt_3", "muonSV_mu2pt", "muonSV_chi2.at(Argsort(muonSV_chi2)[3])", selection = "nmuonSV >= 4", binning=(30, 0, 150),
                x_title=Label("muonSV_muon2_p_{T}_3"),
                units="GeV"),
            Feature("muonSV_mu2eta", "muonSV_mu2eta", binning=(50, -5, 5),
                x_title=Label("muonSV muon2 #eta"), tags=["bdt"]),
            Feature("muonSV_mu2phi", "muonSV_mu2phi", binning=(48, -6, 6),
                x_title=Label("muonSV muon2 #phi"), tags=["bdt"]),
            # Feature("muonSV_deltaR", "muonSV_deltaR", binning=(48, -6, -6),
                # x_title=Label("muonSV #DeltaR"),),

            # Feature("muon1_sv_bestchi2_pt", "muonSV_mu1pt.at(min_chi2_index)",
            Feature("muon1_sv_bestchi2_pt", "muon1_sv_bestchi2_pt",
                binning=(100, 0, 200), x_title=Label("muonSV muon1 #p_{T} (min #chi^2)"),
                units="GeV", tags=["lbn", "lbn_pt"]),
            # Feature("muon1_sv_bestchi2_eta", "muonSV_mu1eta.at(min_chi2_index)",
            Feature("muon1_sv_bestchi2_eta", "muon1_sv_bestchi2_eta",
                binning=(50, -5, 5), x_title=Label("muonSV muon1 #eta (min #chi^2)"),
                tags=["lbn", "lbn_eta"]),
            # Feature("muon1_sv_bestchi2_phi", "muonSV_mu1phi.at(min_chi2_index)",
            Feature("muon1_sv_bestchi2_phi", "muon1_sv_bestchi2_phi",
                binning=(48, -6, 6), x_title=Label("muonSV muon1 #phi (min #chi^2)"),
                tags=["lbn", "lbn_phi"]),
            # Feature("muon1_sv_bestchi2_mass", "0.1057", binning=(50, 0, 0.2),
            Feature("muon1_sv_bestchi2_mass", "muon1_sv_bestchi2_mass", binning=(50, 0, 0.2),
                x_title=Label("muonSV muon1 mass (min #chi^2)"),
                tags=["lbn", "lbn_m"]),

            # Feature("muon2_sv_bestchi2_pt", "muonSV_mu2pt.at(min_chi2_index)",
            Feature("muon2_sv_bestchi2_pt", "muon2_sv_bestchi2_pt",
                binning=(100, 0, 200), x_title=Label("muonSV muon2 #p_{T} (min #chi^2)"),
                units="GeV", tags=["lbn", "lbn_pt"]),
            # Feature("muon2_sv_bestchi2_eta", "muonSV_mu2eta.at(min_chi2_index)",
            Feature("muon2_sv_bestchi2_eta", "muon2_sv_bestchi2_eta",
                binning=(50, -5, 5), x_title=Label("muonSV muon2 #eta (min #chi^2)"),
                tags=["lbn", "lbn_eta"]),
            # Feature("muon2_sv_bestchi2_phi", "muonSV_mu2phi.at(min_chi2_index)",
            Feature("muon2_sv_bestchi2_phi", "muon2_sv_bestchi2_phi",
                binning=(48, -6, 6), x_title=Label("muonSV muon2 #phi (min #chi^2)"),
                tags=["lbn", "lbn_phi"]),
            # Feature("muon2_sv_bestchi2_mass", "0.1057", binning=(50, 0, 0.2),
            Feature("muon2_sv_bestchi2_mass", "muon2_sv_bestchi2_mass", binning=(50, 0, 0.2),
                x_title=Label("muonSV muon2 mass (min #chi^2)"),
                tags=["lbn", "lbn_m"]),

            # Feature("muonSV_chi2_bestchi2", "muonSV_chi2.at(min_chi2_index)", binning=(50, 0, 1500),
            Feature("muonSV_minchi2", "Min(muonSV_chi2)", binning=(100, 0, 10),
                x_title=Label("minimum muonSV chi2"), tags=["lbn_light", "lbn"]),
            Feature("muonSV_bestchi2_chi2", "muonSV_bestchi2_chi2", binning=(100, 0, 10),
                x_title=Label("muonSV chi2 (min #chi^{2})"), tags=["lbn_light", "lbn"]),
            Feature("muonSV_bestchi2_chi2_with_mass_cut", "muonSV_bestchi2_chi2", selection="muonSV_bestchi2_mass > 5.0", binning=(100, 0, 10),
                x_title=Label("muonSV chi2 (min #chi^{2})"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_pAngle_bestchi2", "muonSV_pAngle.at(min_chi2_index)", binning=(70, 0, 3.5),
            Feature("muonSV_bestchi2_pAngle", "muonSV_bestchi2_pAngle", binning=(100, 0, 3.5),
                x_title=Label("muonSV pAngle (min #chi^{2})"), tags=["lbn_light", "lbn"]),
            Feature("muonSV_bestchi2_pAngle_cut", "muonSV_bestchi2_pAngle > 0.2", binning=(2, -0.5, 1.5),
                x_title=Label("muonSV pAngle (min #chi^{2}) > 0.2"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_dlen_bestchi2", "muonSV_dlen.at(min_chi2_index)", binning=(80, 0, 20),
            Feature("muonSV_bestchi2_dlen", "muonSV_bestchi2_dlen", binning=(80, 0, 20),
                x_title=Label("muonSV dlen"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_dlenSig_bestchi2", "muonSV_dlenSig.at(min_chi2_index)", binning=(100, 0, 1500),
            Feature("muonSV_bestchi2_dlenSig", "muonSV_bestchi2_dlenSig", binning=(100, 0, 1500),
                x_title=Label("muonSV dlenSig (min #chi^{2})"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_dxy_bestchi2", "muonSV_dxy.at(min_chi2_index)", binning=(40, 0, 20),
            Feature("muonSV_bestchi2_dxy", "muonSV_bestchi2_dxy", binning=(100, 0, 25),
                x_title=Label("muonSV lxy (min #chi^{2})"), tags=["lbn_light", "lbn"], units="cm"),
            Feature("muonSV_bestchi2_dxy_Jpsi", "muonSV_bestchi2_dxy", selection="muonSV_mass[ArgMin(muonSV_chi2)] > 2.7 && muonSV_mass[ArgMin(muonSV_chi2)] < 3.3", binning=(100, 0, 25),
                x_title=Label("muonSV lxy (min #chi^{2})"), tags=["lbn_light", "lbn"], units="cm"),
            Feature("muonSV_bestchi2_dxy_lowrange_Jpsi", "muonSV_bestchi2_dxy", selection="muonSV_mass[ArgMin(muonSV_chi2)] > 2.7 && muonSV_mass[ArgMin(muonSV_chi2)] < 3.3", binning=(100, 0, 2),
                x_title=Label("muonSV lxy (min #chi^{2})"), tags=["lbn_light", "lbn"], units="cm"),
            Feature("muonSV_bestchi2_dxy_lowrange", "muonSV_bestchi2_dxy", binning=(100, 0, 2),
                x_title=Label("muonSV lxy (min #chi^{2})"), tags=["lbn_light", "lbn"], units="cm"),
            Feature("muonSV_bestchi2_dxy_lowrange_dxy0p2", "muonSV_bestchi2_dxy", binning=(100, 0.2, 2),
                x_title=Label("muonSV lxy (min #chi^{2})"), tags=["lbn_light", "lbn"], units="cm"),
            Feature("muonSV_bestchi2_dxy_lowrange_dxy0p3", "muonSV_bestchi2_dxy", binning=(100, 0.3, 2),
                x_title=Label("muonSV lxy (min #chi^{2})"), tags=["lbn_light", "lbn"], units="cm"),
            # Feature("muonSV_dxySig_bestchi2", "muonSV_dxySig.at(min_chi2_index)", binning=(100, 0, 2500),
            Feature("muonSV_bestchi2_dxySig", "muonSV_bestchi2_dxySig", binning=(100, 0, 1000),
                x_title=Label("muonSV dxySig (min #chi^2)"), tags=["lbn_light", "lbn"]),

            Feature("muonSV_x", "muonSV_x", binning=(500, -20, 20),
                x_title=Label("muonSV x"), tags=["bdt"]),
            Feature("muonSV_y", "muonSV_y", binning=(500, -20, 20),
                x_title=Label("muonSV y"), tags=["bdt"]),
            Feature("muonSV_z", "muonSV_z", binning=(200, -50, 50),
                x_title=Label("muonSV z"), tags=["bdt"]),

            # Feature("muonSV_x_bestchi2", "muonSV_x.at(min_chi2_index)", binning=(50, -10, 10),
            Feature("muonSV_bestchi2_x", "muonSV_bestchi2_x", binning=(500, -12, 12),
                x_title=Label("muonSV x (min #chi^2)"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_y_bestchi2", "muonSV_y.at(min_chi2_index)", binning=(50, -10, 10),
            Feature("muonSV_bestchi2_y", "muonSV_bestchi2_y", binning=(500, -12, 12),
                x_title=Label("muonSV y (min #chi^2)"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_z_bestchi2", "muonSV_z.at(min_chi2_index)", binning=(100, -20, 20),
            Feature("muonSV_bestchi2_z", "muonSV_bestchi2_z", binning=(400, -70, 70),
                x_title=Label("muonSV z (min #chi^2)"), tags=["lbn_light", "lbn"]),

            Feature("sv_pt", "SV_pt", binning=(30, 0, 150),
                x_title=Label("SV p_{T}"),
                units="GeV", tags=["bdt"]),
            Feature("sv_eta", "SV_eta", binning=(50, -5, 5),
                x_title=Label("SV #eta"), tags=["bdt"]),
            Feature("sv_phi", "SV_phi", binning=(48, -6, 6),
                x_title=Label("SV #phi"), tags=["bdt"]),
            Feature("sv_mass", "SV_mass", binning=(120, 0, 4),
                x_title=Label("SV mass"),
                units="GeV",
                blinded_range=[1.5, 2.5]),
                # blinded_range=[[0.2, 0.4], [1.5, 2.5]]),
            Feature("sv_x", "SV_x", binning=(50, -4, 4),
                x_title=Label("SV x"), tags=["bdt"]),
            Feature("sv_y", "SV_y", binning=(50, -4, 4),
                x_title=Label("SV y"), tags=["bdt"]),
            Feature("sv_z", "SV_z", binning=(200, -50, 50),
                x_title=Label("SV z"), tags=["bdt"]),
            Feature("sv_dxy", "SV_dxy", binning=(100, 0, 25),
                x_title=Label("SV dxy"), tags=["bdt"]),
            Feature("sv_dxySig", "SV_dxySig", binning=(100, 0, 750),
                x_title=Label("SV dxySig"), tags=["bdt"]),
            Feature("sv_dlen", "SV_dlen", binning=(72, 0, 12),
                x_title=Label("SV dlen"), tags=["bdt"]),
            Feature("sv_dlenSig", "SV_dlenSig", binning=(100, 0, 1000),
                x_title=Label("SV dlenSig"), tags=["bdt"]),
            Feature("sv_chi2", "SV_chi2", binning=(50, 0, 100),
                x_title=Label("SV chi2"), tags=["bdt"]),
            Feature("sv_pAngle", "SV_pAngle", binning=(70, 0, 3.5),
                x_title=Label("SV pAngle"), tags=["bdt"]),
            Feature("sv_ndof", "SV_ndof", binning=(15, -0.5, 14.5),
                x_title=Label("SV ndof"), tags=["bdt"]),

            Feature("nSV", "nSV", binning=(11, -0.5, 10.5),
                x_title=Label("nSV"), tags=["bdt"]),

            Feature("met_pt", "MET_pt", binning=(15, 0, 150),
                x_title=Label("MET p_{T}"),
                units="GeV"),
            Feature("met_phi", "MET_phi", binning=(32, -4, 4),
                x_title=Label("MET #phi"),
                units="GeV"),
            Feature("jet_btag", "Jet_btagDeepFlavB", binning=(20, 0, 1),
                x_title=Label("Jet btag (DeepFlavour b)")),
            Feature("max_jet_btag", "Max(Jet_btagDeepFlavB)", binning=(20, 0, 1),
                x_title=Label("Max Jet btag (DeepFlavour b)"), tags=["skip_shards"]),
            Feature("nbjets", "Jet_btagDeepFlavB[Jet_btagDeepFlavB > 0.2770].size()", binning=(6, -0.5, 5.5),
                x_title=Label("nbjets"), tags=["skip_shards"]),

            # BDT features
            Feature("bdt", "bdt_scenarioA", binning=(100, 0, 1),
                x_title=Label("BDT score"),
            ),
            Feature("bdt_JPsi", "bdt_scenarioA_onlymu", selection="muonSV_bestchi2_mass > 2.7 && muonSV_bestchi2_mass < 3.3", binning=(100, 0.0, 1),
                x_title=Label("BDT score in J/Psi region"),
            ),
            Feature("bdt_JPsi_vector", "bdt_vector_onlymu", selection="muonSV_mass[ArgMin(muonSV_chi2)] > 2.7 && muonSV_mass[ArgMin(muonSV_chi2)] < 3.3", binning=(100, 0.0, 1),
                x_title=Label("BDT score in J/Psi region (vector portal)"),
            ),
            Feature("bdt_JPsi_vector_with_dxysig_cut", "bdt_vector_onlymu", selection="muonSV_mass[ArgMin(muonSV_chi2)] > 2.7 && muonSV_mass[ArgMin(muonSV_chi2)] < 3.3 && muonSV_dxySig[ArgMin(muonSV_chi2)] > 100", binning=(100, 0.0, 1),
                x_title=Label("BDT score in J/Psi region (vector portal)"),
            ),
            Feature("bdt_Ks_vector", "bdt_vector_onlymu", selection="muonSV_mass[ArgMin(muonSV_chi2)] > 0.43 && muonSV_mass[ArgMin(muonSV_chi2)] < 0.49", binning=(100, 0.0, 1),
                x_title=Label("BDT score in Ks region (vector portal)"),
            ),
            Feature("bdt_Psi2s_vector", "bdt_vector_onlymu", selection="muonSV_mass[ArgMin(muonSV_chi2)] > 3.47 && muonSV_mass[ArgMin(muonSV_chi2)] < 3.89", binning=(100, 0.0, 1),
                x_title=Label("BDT score in Ks region (vector portal)"),
            ),
            Feature("bdt_Z_vector", "bdt_vector_onlymu", selection="muonSV_mass[ArgMin(muonSV_chi2)] > 83.7 && muonSV_mass[ArgMin(muonSV_chi2)] < 98.7", binning=(100, 0.0, 1),
                x_title=Label("BDT score in Z region (vector portal)"),
            ),
            #Feature("bdt_scenarioA", "bdt_scenarioA_nojetsel", binning=(20, 0, 1),
            Feature("bdt_scenarioA", "bdt_scenarioA_onlymu", binning=(100, 0, 1),
            #Feature("bdt_scenarioA", "bdt_scenarioA_final", binning=(100, 0, 1),
            # Feature("bdt_scenarioA", "bdt_scenarioA", binning=(100, 0, 1),
                x_title=Label("BDT score (scenario A)"),
            ),

            Feature("bdt_scenarioA_da", "bdt_scenarioA_onlymu_da", binning=(100, 0, 1),
                x_title=Label("BDT score (scenario A, DA)"),
            ),

            Feature("bdt_scenarioA_0p8_1p0", "bdt_scenarioA", binning=(40, 0.8, 1),
                x_title=Label("BDT score (scenario A)"),
            ),

            Feature("bdt_scenarioA_0p95_1p0", "bdt_scenarioA_onlymu_da", binning=(25, 0.95, 1),
                x_title=Label("BDT score (scenario A)"),
            ),
            Feature("bdt_scenarioA_da_0p95_1p0", "bdt_scenarioA_onlymu_da", binning=(25, 0.95, 1),
                x_title=Label("BDT score (scenario A, DA)"),
            ),

            Feature("bdt_scenarioB1", "bdt_scenarioB1_onlymu", binning=(30, -2, 1),
                x_title=Label("BDT score (scenario B1)"),
            ),
            Feature("bdt_scenarioB2", "bdt_new_scenarioB2", binning=(20, 0, 1),
                x_title=Label("BDT score (scenario B2)"),
            ),
            Feature("bdt_scenarioC", "bdt_new_scenarioC", binning=(20, 0, 1),
                x_title=Label("BDT score (scenario C)"),
            ),

            Feature("bdt_vector", "bdt_vector_onlymu", binning=(100, 0, 1),
            # Feature("bdt_vector", "bdt_vector_final", binning=(20, 0, 1),
                x_title=Label("BDT score (vector portal)"),
            ),
            

            #Feature("bdt_vector", "bdt_vector_full_m_2p0_ctau_1p0_xi0_1p0_xiL_1p0", binning=(100, 0, 1),
                #x_title=Label("BDT score (vector portal)"),
            #),

            # Feature("muonSV_mass_min_chi2", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 22),
            # Feature("muonSV_bestchi2_mass", "muonSV_bestchi2_mass", binning=(1000, 0, 4),
            Feature("muonSV_bestchi2_mass", "muonSV_bestchi2_mass", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            Feature("muonSV_bestchi2_mass_sidebands", "muonSV_bestchi2_mass", selection = "muonSV_bestchi2_mass < 19.6 || muonSV_bestchi2_mass > 20.4", binning=(50, 19.0, 21.0),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            Feature("muonSV_bestchi2_mass_dxy0p2", "muonSV_bestchi2_mass", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_dxy > 0.2"),
            Feature("muonSV_bestchi2_mass_dxy0p3", "muonSV_bestchi2_mass", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_dxy > 0.3"),
            Feature("muonSV_bestchi2_mass_matched", "muonSV_bestchi2_mass", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_gen_matched.at(min_chi2_index) == 1"),
            Feature("muonSV_bestchi2_mass_jpsi", "muonSV_bestchi2_mass", binning=(50, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27"),
            Feature("muonSV_bestchi2_mass_jpsi_fewer_bins", "muonSV_bestchi2_mass", binning=(20, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27"),
            Feature("muonSV_bestchi2_mass_upsilon1s", "muonSV_bestchi2_mass", binning=(50, 8.99, 9.87),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 8.99 && muonSV_bestchi2_mass < 9.87"),
            Feature("muonSV_bestchi2_mass_jpsi_0p1_1", "muonSV_bestchi2_mass", binning=(50, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27 && muonSV_bestchi2_dxy > 0.1 && muonSV_bestchi2_dxy < 1.0 && muonSV_bestchi2_chi2 < 6.635"),
            Feature("muonSV_bestchi2_mass_jpsi_0p1_2", "muonSV_bestchi2_mass", binning=(50, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27 && muonSV_bestchi2_dxy > 0.1 && muonSV_bestchi2_dxy < 2.0"),
            Feature("muonSV_bestchi2_mass_jpsi_0p1_0p5", "muonSV_bestchi2_mass", binning=(50, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27 && muonSV_bestchi2_dxy > 0.1 && muonSV_bestchi2_dxy < 0.5"),
            Feature("muonSV_bestchi2_mass_jpsi_0p5_1", "muonSV_bestchi2_mass", binning=(50, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27 && muonSV_bestchi2_dxy > 0.5 && muonSV_bestchi2_dxy < 1.0"),
            Feature("muonSV_bestchi2_mass_jpsi_1_3", "muonSV_bestchi2_mass", binning=(50, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27 && muonSV_bestchi2_dxy > 1.0 && muonSV_bestchi2_dxy < 3.0"),
            Feature("muonSV_bestchi2_mass_jpsi_3_10", "muonSV_bestchi2_mass", binning=(50, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27 && muonSV_bestchi2_dxy > 3.0 && muonSV_bestchi2_dxy < 10.0"),
            Feature("muonSV_bestchi2_mass_jpsi_1_10", "muonSV_bestchi2_mass", binning=(50, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27 && muonSV_bestchi2_dxy > 1.0 && muonSV_bestchi2_dxy < 10.0"),
            Feature("muonSV_bestchi2_mass_jpsi_2_10", "muonSV_bestchi2_mass", binning=(50, 2.91, 3.27),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection="muonSV_bestchi2_mass > 2.91 && muonSV_bestchi2_mass < 3.27 && muonSV_bestchi2_dxy > 2.0 && muonSV_bestchi2_dxy < 10.0"),
            Feature("muonSV_bestchi2_mass_0p33", "muonSV_bestchi2_mass",
                binning=(50, 0.333 - 5 * 0.01 * 0.333, 0.333 + 5 * 0.01 * 0.333),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            Feature("muonSV_bestchi2_mass_0p42", "muonSV_bestchi2_mass",
                binning=(50, 0.42 - 5 * 0.01 * 0.42, 0.42 + 5 * 0.01 * 0.42),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            Feature("muonSV_bestchi2_mass_7p8_9p0", "muonSV_bestchi2_mass",
                binning=(50, 7.8, 9.0),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection = "(muonSV_bestchi2_dxy > 0.0 && muonSV_bestchi2_dxy < 6.4 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0)) ||"
                         "(muonSV_bestchi2_dxy > 7.3 && muonSV_bestchi2_dxy < 10.5 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 11.5 && muonSV_bestchi2_dxy < 15.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 16.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))"),
            Feature("muonSV_bestchi2_mass_3p9_4p3", "muonSV_bestchi2_mass",
                binning=(50, 3.9, 4.3),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection = "(muonSV_bestchi2_dxy > 0.0 && muonSV_bestchi2_dxy < 6.4 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0)) ||"
                         "(muonSV_bestchi2_dxy > 7.3 && muonSV_bestchi2_dxy < 10.5 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 11.5 && muonSV_bestchi2_dxy < 15.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 16.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))"),
            Feature("muonSV_bestchi2_mass_6_8", "muonSV_bestchi2_mass",
                binning=(150, 6.0, 8.0),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection = "(muonSV_bestchi2_dxy > 0.0 && muonSV_bestchi2_dxy < 6.4 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0)) ||"
                         "(muonSV_bestchi2_dxy > 7.3 && muonSV_bestchi2_dxy < 10.5 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 11.5 && muonSV_bestchi2_dxy < 15.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 16.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))"),
            Feature("muonSV_bestchi2_mass_1p08_2p0", "muonSV_bestchi2_mass",
                binning=(280, 1.08, 2.0),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection = "(muonSV_bestchi2_dxy > 0.0 && muonSV_bestchi2_dxy < 6.4 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0)) ||"
                         "(muonSV_bestchi2_dxy > 7.3 && muonSV_bestchi2_dxy < 10.5 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 11.5 && muonSV_bestchi2_dxy < 15.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 16.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))"),
            Feature("muonSV_bestchi2_mass_fullrange_100_bins", "muonSV_bestchi2_mass", binning=(100, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV",
                selection = "(muonSV_bestchi2_dxy > 0.0 && muonSV_bestchi2_dxy < 6.4 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0)) ||"
                         "(muonSV_bestchi2_dxy > 7.3 && muonSV_bestchi2_dxy < 10.5 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 11.5 && muonSV_bestchi2_dxy < 15.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))||" 
                         "(muonSV_bestchi2_dxy > 16.6 && (abs(muonSV_bestchi2_z) < 27.0 || abs(muonSV_bestchi2_z) > 52.0))"),
            Feature("muonSV_bestchi2_mass_fullrange", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),

            # chi2 cuts
            Feature("muonSV_bestchi2_mass_fullrange_bdtA_0p65", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.65",
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_bdtA_0p8", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.8",
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_bdtA_0p9", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.9",
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_bdtA_0p95", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.95",
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_bdtA_0p98", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.98",
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_bdtA_0p985", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.985",
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_bdtA_0p99", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.99",
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_bdtA_0p995", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.995",
                units="GeV"),

            Feature("muonSV_bestchi2_mass_fullrange_with_mass_cut", "muonSV_bestchi2_mass", selection = "muonSV_bestchi2_mass > 5.0", binning=(100, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_dxy0p3", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2}, l_{xy} > 0.3)"),
                units="GeV",
                selection="muonSV_bestchi2_dxy > 0.3"),
            Feature("muonSV_bestchi2_mass_fullrange_dxy0p2", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2}, l_{xy} > 0.2)"),
                units="GeV",
                selection="muonSV_bestchi2_dxy > 0.2"),
            Feature("muonSV_bestchi2_mass_fullrange_fewer_bins", "muonSV_bestchi2_mass", binning=(100, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_dxy0p3_fewer_bins", "muonSV_bestchi2_mass", binning=(100, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2}, l_{xy} > 0.3)"),
                units="GeV",
                selection="muonSV_bestchi2_dxy > 0.3"),
            Feature("muonSV_bestchi2_mass_fullrange_dxy0p2_fewer_bins", "muonSV_bestchi2_mass", binning=(100, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2}, l_{xy} > 0.2)"),
                units="GeV",
                selection="muonSV_bestchi2_dxy > 0.2"),
            Feature("muonSV_bestchi2_mass_fullrange_dxy0p1_fewer_bins", "muonSV_bestchi2_mass", binning=(100, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2}, l_{xy} > 0.1)"),
                units="GeV",
                selection="muonSV_bestchi2_dxy > 0.1"),
            # Feature("muonSV_mass_min_chi2_bdt", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 22),
            Feature("muonSV_mass_min_chi2_maxbdt", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 4),
                x_title=Label("muonSV mass (Min. #chi^{2}), BDT < 0.85"),
                selection="xgb0__m_2p0_ctau_10p0_xiO_1p0_xiL_1p0 < 0.85",
                units="GeV",
                blinded_range=[1.5, 2.5]),

            Feature("muonSV_bestchi2_mass_fullrange_bdt_0p8", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.8",
                units="GeV"),

            Feature("muonSV_bestchi2_mass_fullrange_bdt_0p9", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.9",
                units="GeV"),

            Feature("muonSV_bestchi2_mass_fullrange_bdt_0p95", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.95",
                units="GeV"),

            Feature("muonSV_bestchi2_mass_fullrange_bdt_0p98", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="{{bdt_scenarioA}} > 0.98",
                units="GeV"),

            # all muonSVs
            Feature("all_muonSV_mass",
                # "get_all_masses(cat_index, muonSV_bestchi2_mass, mass_multivertices)", binning=(8270, 0, 22),
                "mass_multivertices", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass"),
                units="GeV"),
            Feature("all_muonSV_mass_fullrange",
                # "get_all_masses(cat_index, muonSV_bestchi2_mass, mass_multivertices)", binning=(8270, 0, 22),
                "mass_multivertices", binning=(8270, 0, 22),
                x_title=Label("muonSV mass"),
                units="GeV"),

            Feature("nmuonSV_3sigma", "nmuonSV_3sigma", binning=(11, -0.5, 10.5),
                x_title=Label("nmuonSV_3sigma"), tags=["lbn"]),
            
            Feature("nmuonSV", "nmuonSV", binning=(11, -0.5, 10.5),
                x_title=Label("nmuonSV"), tags=["bdt"]),

            # additional muons
            Feature("muonSV_bestchi2_mass_addeta", "muonSV_bestchi2_mass", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                    "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4"
                "].size() > 0",
                units="GeV"),
            Feature("muonSV_bestchi2_mass_addloose_eta", "muonSV_bestchi2_mass", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                    "get_intvar_additional_muons(Muon_looseId, add_muon_indexes) == 1 && "
                    "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4"
                "].size() > 0",
                units="GeV"),

            Feature("muonSV_bestchi2_mass_addeta_dr", "muonSV_bestchi2_mass", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                    "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4 &&"
                    "min_add_muon_deltaR > 0.1"
                "].size() > 0",
                units="GeV"),
            Feature("muonSV_bestchi2_mass_addloose_eta_dr", "muonSV_bestchi2_mass", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                selection="get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                    "get_intvar_additional_muons(Muon_looseId, add_muon_indexes) == 1 && "
                    "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4 &&"
                    "min_add_muon_deltaR > 0.1"
                "].size() > 0",
                units="GeV"),

            Feature("add_muon_pt_loose_eta", "get_floatvar_additional_muons(Muon_pt, add_muon_indexes)", binning=(20, 0, 20),
                x_title=Label("Add. muon p_{T}"),
                selection="get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                    "get_intvar_additional_muons(Muon_looseId, add_muon_indexes) == 1 && "
                    "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4"
                "].size() > 0",
                units="GeV"),
            Feature("add_muon_pt_eta", "get_floatvar_additional_muons(Muon_pt, add_muon_indexes)", binning=(20, 0, 20),
                x_title=Label("Add. muon p_{T}"),
                selection="get_intvar_additional_muons(Muon_looseId, add_muon_indexes)["
                    "abs(get_floatvar_additional_muons(Muon_eta, add_muon_indexes)) <= 2.4"
                "].size() > 0",
                units="GeV"),
            Feature("min_add_muon_deltar", "min_add_muon_deltaR", binning=(100, 0, 7),
                x_title=Label("min Delta R (Add. muon, muonSV muons)")),

            # gen
            # Feature("gen_dark_photon_pt", "GenPart_pt[GenPart_is_dark_photon_into_muons == 1]", binning=(50, 0, 50),
                # x_title=Label("Gen A'#rightarrow#mu#mu p_{T}"),
                # units="GeV"
            # ),
            # Feature("gen_dark_photon_pt_eff", "GenPart_pt[GenPart_is_dark_photon_into_muons_eff == 1]", binning=(50, 0, 50),
                # x_title=Label("Gen A'#rightarrow#mu#mu p_{T} (eff)"),
                # units="GeV"
            # ),

            Feature("ngendarkphoton",
                "GenPart_pdgId[GenPart_pdgId == 9900015].size()",
                binning=(16, -0.5, 15.5),
                x_title=Label("Number of dark photons per event"),
            ),

            Feature("gen_dark_photon_pt", "GenPart_pt[GenPart_lxy >= 0]",
                binning=[5., 9., 10., 11., 12., 13., 14., 17., 20., 25., 30., 50., 75., 100., 150.],
                x_title=Label("Gen A'#rightarrow#mu#mu p_{T}"),
                units="GeV"
            ),

            Feature("gen_dark_photon_lxy", "GenPart_lxy[GenPart_lxy >= 0]",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"),
            ),

            Feature("gen_dark_photon_lxy_low", "GenPart_lxy[GenPart_lxy >= 0]",
                binning=(100, 0, 2),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"),
            ),

            Feature("gen_dark_photon_lxy_verylow", "GenPart_lxy[GenPart_lxy >= 0]",
                binning=(100, 0, 0.01),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"),
            ),

            Feature("gen_dark_photon_lxyz", "GenPart_lxyz[GenPart_lxyz >= 0]",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"),
            ),

            Feature("gen_dark_photon_pt_eff",
                "GenPart_pt[GenPart_lxy >= 0 && GenPart_is_dark_photon_into_muons_triggereff_bestchi2 >= 1]",
                binning=[5., 9., 10., 11., 12., 13., 14., 17., 20., 25., 30., 50., 75., 100., 150.],
                x_title=Label("Gen A'#rightarrow#mu#mu p_{T}"),
                units="GeV"
            ),

            Feature("gen_dark_photon_lxy_eff",
                "GenPart_lxy[GenPart_lxy >= 0 && GenPart_is_dark_photon_into_muons_triggereff_bestchi2 >= 1]",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"),
            ),

            Feature("gen_dark_photon_lxy_pt_ratio_eff",
                "GenPart_lxy[GenPart_lxy >= 0 && GenPart_is_dark_photon_into_muons_triggereff_bestchi2 >= 1] / GenPart_pt[GenPart_lxy >= 0 && GenPart_is_dark_photon_into_muons_triggereff_bestchi2 >= 1]",
                binning=(50, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}/p_{T}"),
            ),

            Feature("gen_dark_photon_lxy_pt_ratio",
                "GenPart_lxy[GenPart_lxy >= 0] / GenPart_pt[GenPart_lxy >= 0]",
                binning=(50, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}/p_{T}"),
            ),

            Feature("gen_dark_photon_lxyz_pt_ratio",
                "GenPart_lxyz[GenPart_lxyz >= 0] / GenPart_pt[GenPart_lxyz >= 0]",
                binning=(500, 0, 10),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xyz}/p_{T}"),
            ),

            Feature("gen_dark_photon_lxy_p_ratio_eff",
                "GenPart_lxy[GenPart_lxy >= 0 && GenPart_is_dark_photon_into_muons_triggereff_bestchi2 >= 1] / GenPart_p[GenPart_lxy >= 0 && GenPart_is_dark_photon_into_muons_triggereff_bestchi2 >= 1]",
                binning=(50, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}/p_{T}"),
            ),

            Feature("ngen_dark_photon",
                "GenPart_lxy[GenPart_lxy >= 0].size()",
                binning=(16, -0.5, 15.5),
                x_title=Label("Number of dark photons per event"),
            ),
            
            Feature("gen_dark_photon_lxy_p_ratio",
                "GenPart_lxy[GenPart_lxy >= 0] / GenPart_p[GenPart_lxy >= 0]",
                binning=(50, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}/p_{T}"),
            ),

            Feature("gen_dark_photon_lxyz_p_ratio",
                "GenPart_lxyz[GenPart_lxyz >= 0] / GenPart_p[GenPart_lxyz >= 0]",
                binning=(500, 0, 10),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xyz}/p_{T}"),
            ),

            Feature("gen_dark_photon_lxy_p_eff",
                "GenPart_lxy[GenPart_lxy >= 0 && GenPart_is_dark_photon_into_muons_triggereff_bestchi2 >= 1] * GenPart_p[GenPart_lxy >= 0 && GenPart_is_dark_photon_into_muons_triggereff_bestchi2 >= 1]",
                binning=(50, 0, 50),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy} * p"),
            ),

            Feature("gen_dark_photon_lxy_low_0",
                "GenDark_lxy_0",
                binning=(100, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_low_1",
                "GenDark_lxy_1",
                binning=(100, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_low_2",
                "GenDark_lxy_2",
                binning=(100, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_low_3",
                "GenDark_lxy_3",
                binning=(100, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_low_4",
                "GenDark_lxy_4",
                binning=(100, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_low_5",
                "GenDark_lxy_5",
                binning=(100, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_low_6",
                "GenDark_lxy_6",
                binning=(100, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_low_7",
                "GenDark_lxy_7",
                binning=(100, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_low_8",
                "GenDark_lxy_8",
                binning=(100, 0, 5),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_0",
                "GenDark_lxy_0",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_1",
                "GenDark_lxy_1",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_2",
                "GenDark_lxy_2",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_3",
                "GenDark_lxy_3",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_4",
                "GenDark_lxy_4",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_5",
                "GenDark_lxy_5",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_6",
                "GenDark_lxy_6",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_7",
                "GenDark_lxy_7",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("gen_dark_photon_lxy_8",
                "GenDark_lxy_8",
                binning=(40, 0, 20),
                x_title=Label("Gen A'#rightarrow#mu#mu L_{xy}"), units="cm",
            ),

            Feature("ngoodmuonSV",
                "muonSV_chi2[muonSV_chi2 < 10].size()",
                binning=(10, 0.5, 10.5),
                x_title=Label("Number of muonSV/event with #chi^{2} < 10"),
            ),

            Feature("ngen_muons",
                "GenPart_pt[abs(GenPart_pdgId) == 13].size()",
                binning=(16, -0.5, 15.5),
                x_title=Label("Number of Gen muons per event"),
            ),

            Feature("ngen_dark_photons_new",
                "GenPart_pt[abs(GenPart_pdgId) == 999999].size()",
                binning=(16, -0.5, 15.5),
                x_title=Label("Number of Gen dark photons per event"),
            ),

            Feature("puWeight", "puWeight", binning=(20, 0, 2),
                x_title=Label("puWeight"),
                # systematics=["CMS_parking_pileup_2018"]),
                systematics=["pu"]),
            Feature("idWeight", "idWeight", binning=(20, 0, 2),
                x_title=Label("idWeight"),
                # systematics=["CMS_m_displaced_id_2018"]),
                systematics=["id"]),
            Feature("trigSF", "trigSF", binning=(20, 0, 2),
                x_title=Label("trigSF"),
                # systematics=["CMS_eff_parking_trigger_2018"]),
                systematics=["trig"]),
            # Feature("ctau_reweighing", "ctau_reweighing", binning=(20, 0, 10),
            Feature("ctau_reweighing", "muonSV_ctau_rew.at(min_chi2_index)", binning=(20, 0, 10),
                x_title=Label("ctau_reweighing")),
        ]
        return ObjectCollection(features)

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        weights.total_events_weights = ["genWeight", "puWeight"]
        # weights.total_events_weights = ["genWeight"]
        # weights.total_events_weights = ["1"]

        weights.base = ["genWeight", "puWeight", "PUjetID_SF", "idWeight", "trigSF"]  # others needed
        # weights.base = ["1"]  # others needed

        for category in self.categories:
            weights[category.name] = weights.base

        return weights

    def add_systematics(self):
        systematics = [
            Systematic("jet_smearing", "_nom"),
            # Systematic("met_smearing", ("MET", "MET_smeared")),
            # Systematic("CMS_parking_pileup_2018", "", up="Up", down="Down"),
            Systematic("pu", "", up="Up", down="Down", alias="CMS_parking_pileup_2018"),
            Systematic("id", "", alias="CMS_m_displaced_id_2018"),
            Systematic("trig", "", alias="CMS_eff_parking_trigger_2018"),
            Systematic("jer", "_smeared", affected_categories=self.categories.names(),
                module_syst_type={
                    "jet_syst": {"up": "smeared_up", "down": "smeared_down"},
                    "met_syst": {"up": "up", "down": "down"},  # smearing included in the met_smear_tag
                }),
            # Systematic("tes", "_corr",
                # affected_categories=self.categories.names(),
                # module_syst_type="tau_syst"),
            Systematic("empty", "", up="", down="", affected_categories=["base"])
        ]
        return ObjectCollection(systematics)

    def add_default_module_files(self):
        defaults = {}
        # defaults["PreprocessRDF"] = "modules"
        # defaults["PreCounter"] = "weights"
        return defaults

    # other methods
    def get_norm_systematics(self, processes_datasets, region):
        """
        Method to extract all normalization systematics from the KLUB files.
        It considers the processes given by the process_group_name and their parents.
        """
        # systematics
        systematics = {}
        all_signal_names = []
        all_background_names = []
        for p in self.processes:
            if p.isSignal:
                all_signal_names.append(p.get_aux("llr_name")
                    if p.get_aux("llr_name", None) else p.name)
            elif not p.isData:
                all_background_names.append(p.get_aux("llr_name")
                    if p.get_aux("llr_name", None) else p.name)

        from cmt.analysis.systReader import systReader
        syst_folder = "config/systematics/"
        filename = f"systematics_{self.year}.cfg"
        if self.get_aux("isUL", False):
            filename = f"systematics_UL{str(self.year)[2:]}.cfg"
        syst = systReader(Task.retrieve_file(self, syst_folder + filename),
            all_signal_names, all_background_names, None)
        syst.writeOutput(False)
        syst.verbose(False)
        syst.writeSystematics()
        for isy, syst_name in enumerate(syst.SystNames):
            if "CMS_scale_t" in syst.SystNames[isy] or "CMS_scale_j" in syst.SystNames[isy]:
                continue
            for process in processes_datasets:
                original_process = process
                found = False
                while True:
                    process_name = (process.get_aux("llr_name")
                        if process.get_aux("llr_name", None) else process.name)
                    if process_name in syst.SystProcesses[isy]:
                        iproc = syst.SystProcesses[isy].index(process_name)
                        systVal = syst.SystValues[isy][iproc]
                        if syst_name not in systematics:
                            systematics[syst_name] = {}
                        systematics[syst_name][original_process.name] = eval(systVal)
                        found = True
                        break
                    elif process.parent_process:
                        process=self.processes.get(process.parent_process)
                    else:
                        break
                if not found:
                    for children_process in self.get_children_from_process(original_process.name):
                        if children_process.name in syst.SystProcesses[isy]:
                            if syst_name not in systematics:
                                systematics[syst_name] = {}
                            iproc = syst.SystProcesses[isy].index(children_process.name)
                            systVal = syst.SystValues[isy][iproc]
                            systematics[syst_name][original_process.name] = eval(systVal)
                            break
        return systematics

    def get_ctau_from_dataset_name(self, sample, final_char="_"):
        try:
            if "ctau" not in sample:
                return -1
        except:
            return -1
        subs = sample[sample.find("ctau") + len("ctau_"):]
        final_index = subs.find(final_char)
        if final_index != -1:
            subs = subs[:final_index]
        return float(subs.replace("p", "."))

    #def get_feature_mass(self, mass):
    def get_feature_mass(self, mass):
        return Feature(f"muonSV_bestchi2_mass_{str(mass).replace('.', 'p')}",
            "muonSV_bestchi2_mass", binning=(50, 0.95 * mass, 1.05 * mass),
            blinded_range=(0.98 * mass, 1.02 * mass),
            x_title=Label("muonSV mass (Min. #chi^{2})"),
            units="GeV")

    def get_feature_mass_dxyzcut(self, mass):
        return Feature(f"muonSV_bestchi2_mass_{str(mass).replace('.', 'p')}",
            "muonSV_bestchi2_mass", binning=(50, 0.95 * mass, 1.05 * mass),
            blinded_range=(0.98 * mass, 1.02 * mass),
            selection = jrs([self.dxy_cut, self.dz_cut,
                "(({{bdt_vector}} > 0.998) && (%s <= 5)) || (({{bdt_vector}} > 0.993) && (%s > 5))" % (mass, mass)
            ]),
            x_title=Label("muonSV mass (Min. #chi^{2})"),
            units="GeV")

    def get_feature_mass_dxycut(self, mass):
        return Feature(f"muonSV_bestchi2_mass_{str(mass).replace('.', 'p')}",
            "muonSV_bestchi2_mass", binning=(50, 0.95 * mass, 1.05 * mass),
            blinded_range=(0.98 * mass, 1.02 * mass),
            x_title=Label("muonSV mass (Min. #chi^{2})"),
            selection=self.dxy_cut,
            units="GeV")

    #def get_feature_mass_dxyzcut(self, mass):
        #return Feature(f"muonSV_bestchi2_mass_{str(mass).replace('.', 'p')}",
            #"muonSV_bestchi2_mass", binning=(50, 0.95 * mass, 1.05 * mass),
            #blinded_range=(0.98 * mass, 1.02 * mass),
            #x_title=Label("muonSV mass (Min. #chi^{2})"),
            #selection=jrs(self.dxy_cut, self.dz_cut),
            #units="GeV")

    def get_feature_mass_dxyz_lowdxy_cut(self, mass):
        return Feature(f"muonSV_bestchi2_mass_{str(mass).replace('.', 'p')}",
            "muonSV_bestchi2_mass", binning=(50, 0.95 * mass, 1.05 * mass),
            blinded_range=(0.98 * mass, 1.02 * mass),
            x_title=Label("muonSV mass (Min. #chi^{2})"),
            selection=jrs([self.dxy_cut, self.dz_cut, "muonSV_bestchi2_dxy > 0.2"]),
            units="GeV")

# config = Config("base", year=2018, ecm=13, lumi_pb=59741)
#config = Config("legacy_2018", year=2018, ecm=13, lumi_pb=33600)
config = Config("legacy_2018", year=2018, ecm=13, lumi_pb=1000)
#config = Config("legacy_2018", year=2018, ecm=13, lumi_pb=4184)
