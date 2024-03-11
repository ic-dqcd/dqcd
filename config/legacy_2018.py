from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from cmt.config.base_config import Config as cmt_config
from cmt.base_tasks.base import Task


class Config(cmt_config):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.regions = self.add_regions()

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
            # Category("dum", "dummy category", selection="event == 220524669"),
            Category("dum", "dummy category", selection="event == 3"),

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

        ]
        return ObjectCollection(categories)

    def add_processes(self):
        processes = [
            Process("background", Label("Background"), color=(255, 153, 0)),

            Process("qcd", Label("QCD"), color=(255, 153, 0), parent_process="background"),
            Process("qcd_1000toInf", Label("QCD (1000-)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_120to170", Label("QCD (120-170)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_15to20", Label("QCD (15-20)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_170to300", Label("QCD (170-300)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_20to30", Label("QCD (20-30)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_300to470", Label("QCD (300-470)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_30to50", Label("QCD (30-50)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_470to600", Label("QCD (470-600)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_50to80", Label("QCD (50-80)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_600to800", Label("QCD (600-800)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_80to120", Label("QCD (80-120)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_800to1000", Label("QCD (800-1000)"), color=(255, 153, 0), parent_process="qcd"),
            Process("qcd_15to7000", Label("QCD (15-7000)"), color=(255, 153, 0), parent_process="qcd"),

            Process("QCD_Pt-15to7000_TuneCP5_Flat2018", Label("QCD (15to7000)"), color=(255, 153, 0), parent_process="qcd"),

            Process("signal", Label("Signal"), color=(0, 0, 0), isSignal=True),

            Process("scenarioA", Label("scenarioA"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_0p1", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_10", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_100", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_1_mA_0p33_ctau_1p0", Label(latex="sc.A, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_0p1", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_10", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_100", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_2_mA_0p67_ctau_1p0", Label(latex="sc.A, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_0p40_ctau_0p1", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_0p40_ctau_10", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_0p40_ctau_100", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_0p40_ctau_1p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=0.40$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_0p1", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_10", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_100", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_4_mA_1p33_ctau_1p0", Label(latex="sc.A, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_1p00_ctau_0p1", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_1p00_ctau_10", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_1p00_ctau_100", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_1p00_ctau_1p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=1$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_3p33_ctau_0p1", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_3p33_ctau_10", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_3p33_ctau_100", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),
            Process("scenarioA_mpi_10_mA_3p33_ctau_1p0", Label(latex="sc.A, $m_{\pi}=10$, $m_{A}=3.33$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioA"),

            Process("scenarioB1", Label("scenarioB1"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("scenarioB1_mpi_1_mA_0p33_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_1_mA_0p33_ctau_10", Label(latex="sc.B1, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_1_mA_0p33_ctau_100", Label(latex="sc.B1, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_1_mA_0p33_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=1$, $m_{A}=0.33$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.4$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_10", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.4$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_100", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.4$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p40_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.4$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p67_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p67_ctau_10", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p67_ctau_100", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_2_mA_0p67_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=2$, $m_{A}=0.67$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_0p80_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=0.8$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_0p80_ctau_10", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=0.8$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_0p80_ctau_100", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=0.8$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_0p80_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=0.8$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_1p33_ctau_0p1", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_1p33_ctau_10", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_1p33_ctau_100", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),
            Process("scenarioB1_mpi_4_mA_1p33_ctau_1p0", Label(latex="sc.B1, $m_{\pi}=4$, $m_{A}=1.33$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB1"),

            Process("scenarioB2", Label("scenarioB2"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("scenarioB2_mpi_1_mA_0p60_ctau_0p1", Label(latex="sc.B2, $m_{\pi}=1$, $m_{A}=0.6$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_1_mA_0p60_ctau_10", Label(latex="sc.B2, $m_{\pi}=1$, $m_{A}=0.6$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_1_mA_0p60_ctau_100", Label(latex="sc.B2, $m_{\pi}=1$, $m_{A}=0.6$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_1_mA_0p60_ctau_1p0", Label(latex="sc.B2, $m_{\pi}=1$, $m_{A}=0.6$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_2_mA_1p10_ctau_0p1", Label(latex="sc.B2, $m_{\pi}=2$, $m_{A}=1.1$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_2_mA_1p10_ctau_10", Label(latex="sc.B2, $m_{\pi}=2$, $m_{A}=1.1$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_2_mA_1p10_ctau_100", Label(latex="sc.B2, $m_{\pi}=2$, $m_{A}=1.1$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_2_mA_1p10_ctau_1p0", Label(latex="sc.B2, $m_{\pi}=2$, $m_{A}=1.1$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_4_mA_2p10_ctau_0p1", Label(latex="sc.B2, $m_{\pi}=4$, $m_{A}=2.1$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_4_mA_2p10_ctau_10", Label(latex="sc.B2, $m_{\pi}=4$, $m_{A}=2.1$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_4_mA_2p10_ctau_100", Label(latex="sc.B2, $m_{\pi}=4$, $m_{A}=2.1$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),
            Process("scenarioB2_mpi_4_mA_2p10_ctau_1p0", Label(latex="sc.B2, $m_{\pi}=4$, $m_{A}=2.1$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioB2"),

            Process("scenarioC", Label("scenarioC"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("scenarioC_mpi_10_mA_8p00_ctau_0p1", Label(latex="sc.C, $m_{\pi}=10$, $m_{A}=8$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_10_mA_8p00_ctau_10", Label(latex="sc.C, $m_{\pi}=10$, $m_{A}=8$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_10_mA_8p00_ctau_100", Label(latex="sc.C, $m_{\pi}=10$, $m_{A}=8$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_10_mA_8p00_ctau_1p0", Label(latex="sc.C, $m_{\pi}=10$, $m_{A}=8$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_2_mA_1p60_ctau_0p1", Label(latex="sc.C, $m_{\pi}=2$, $m_{A}=1.6$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_2_mA_1p60_ctau_10", Label(latex="sc.C, $m_{\pi}=2$, $m_{A}=1.6$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_2_mA_1p60_ctau_100", Label(latex="sc.C, $m_{\pi}=2$, $m_{A}=1.6$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_2_mA_1p60_ctau_1p0", Label(latex="sc.C, $m_{\pi}=2$, $m_{A}=1.6$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_4_mA_3p20_ctau_0p1", Label(latex="sc.C, $m_{\pi}=4$, $m_{A}=3.2$, $c\\tau=0.1$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_4_mA_3p20_ctau_10", Label(latex="sc.C, $m_{\pi}=4$, $m_{A}=3.2$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_4_mA_3p20_ctau_100", Label(latex="sc.C, $m_{\pi}=4$, $m_{A}=3.2$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),
            Process("scenarioC_mpi_4_mA_3p20_ctau_1p0", Label(latex="sc.C, $m_{\pi}=4$, $m_{A}=3.2$, $c\\tau=1.0$"), color=(0, 0, 0), isSignal=True, parent_process="scenarioC"),

            Process("vector", Label("vector"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("hiddenValleyGridPack_vector_m_10_ctau_100_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_10_ctau_10_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_10_ctau_1_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_10_ctau_500_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=500$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_10_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=10$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_15_ctau_100_xiO_1_xiL_1", Label(latex="vector, $m=15$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_15_ctau_10_xiO_1_xiL_1", Label(latex="vector, $m=15$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_15_ctau_1_xiO_1_xiL_1", Label(latex="vector, $m=15$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_15_ctau_500_xiO_1_xiL_1", Label(latex="vector, $m=15$, $c\\tau=500$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_15_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=15$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_20_ctau_100_xiO_1_xiL_1", Label(latex="vector, $m=20$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_20_ctau_10_xiO_1_xiL_1", Label(latex="vector, $m=20$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_20_ctau_1_xiO_1_xiL_1", Label(latex="vector, $m=20$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_20_ctau_500_xiO_1_xiL_1", Label(latex="vector, $m=20$, $c\\tau=500$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_20_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=20$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_2_ctau_100_xiO_1_xiL_1", Label(latex="vector, $m=2$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_2_ctau_10_xiO_1_xiL_1", Label(latex="vector, $m=2$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_2_ctau_1_xiO_1_xiL_1", Label(latex="vector, $m=2$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_2_ctau_500_xiO_1_xiL_1", Label(latex="vector, $m=2$, $c\\tau=500$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_2_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=2$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_5_ctau_100_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_5_ctau_10_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_5_ctau_1_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_5_ctau_500_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=500$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),
            Process("hiddenValleyGridPack_vector_m_5_ctau_50_xiO_1_xiL_1", Label(latex="vector, $m=5$, $c\\tau=50$"), color=(0, 0, 0), isSignal=True, parent_process="vector"),


            Process("hzdzd", Label("$H\\to$$Z_dZ_d$"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("hzdzd_mzd_8_ctau_100", Label("$H\\to$ $Z_dZ_d$, $m_{Z_d}=8$, $c\\tau=100$"), color=(0, 0, 0), isSignal=True, parent_process="hzdzd"),
            Process("hzdzd_mzd_8_ctau_1", Label("$H\\to$ $Z_dZ_d$, $m_{Z_d}=8$, $c\\tau=1$"), color=(0, 0, 0), isSignal=True, parent_process="hzdzd"),

            Process("zprime", Label("$Z^'$"), color=(0, 0, 0), isSignal=True, parent_process="signal"),
            Process("zprime_mpi_2_ctau_10", Label("$Z^{'}$, $m_{\pi}=2$, $c\\tau=10$"), color=(0, 0, 0), isSignal=True, parent_process="zprime"),

            Process("data", Label("Data"), color=(0, 0, 0), isData=True),

            Process("dum", Label("dum"), color=(0, 0, 0)),

            Process("egamma", Label("Data"), color=(0, 0, 0), isData=True, parent_process="data"),
            Process("SingleMuon", Label("Data"), color=(0, 0, 0), isData=True, parent_process="data"),
            Process("LambdaBToJpsiLambda", Label("LambdaBToJpsiLambda"), color=(0, 0, 0), parent_process="background"),
            Process("BToJpsiJPsiToMuMu", Label("BToJpsiJPsiToMuMu"), color=(0, 0, 0), parent_process="background"),
            Process("BuToJpsiK", Label("BuToJpsiK"), color=(0, 0, 0), parent_process="background"),
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

        return ObjectCollection(processes), process_group_names, process_training_names

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

            Feature("nmuon", "nMuonBPark", binning=(10, -0.5, 9.5),
                x_title=Label("nMuon")),
            Feature("muon_pt", "MuonBPark_pt", binning=(30, 0, 150),
                x_title=Label("muon p_{T}"),
                units="GeV"),
            Feature("muon_eta", "MuonBPark_eta", binning=(50, -5, 5),
                x_title=Label("muon #eta"),),
            Feature("muon_phi", "MuonBPark_phi", binning=(48, -6, 6),
                x_title=Label("muon #phi"),),
            Feature("muon_mass", "MuonBPark_mass", binning=(120, 0, 4),
                x_title=Label("muon mass"),
                units="GeV"),

            Feature("muon_ptErr", "MuonBPark_ptErr", binning=(20, 0, 1),
                x_title=Label("muon ptErr")),
            Feature("muon_dxy", "MuonBPark_dxy", binning=(20, -2, 2),
                x_title=Label("muon dxy")),
            Feature("muon_dxyErr", "MuonBPark_dxyErr", binning=(20, 0, 0.5),
                x_title=Label("muon dxyErr")),
            Feature("muon_dz", "MuonBPark_dz", binning=(50, -10, 10),
                x_title=Label("muon dz")),
            Feature("muon_dzErr", "MuonBPark_dzErr", binning=(20, 0, 0.5),
                x_title=Label("muon dzErr")),
            Feature("muon_ip3d", "MuonBPark_ip3d", binning=(50, 0, 5),
                x_title=Label("muon ip3d")),
            Feature("muon_sip3d", "MuonBPark_sip3d", binning=(50, 0, 4000),
                x_title=Label("muon sip3d")),
            Feature("muon_charge", "MuonBPark_charge", binning=(3, -1.5, 1.5),
                x_title=Label("muon charge")),
            Feature("muon_tightId", "MuonBPark_tightId > 0", binning=(2, -0.5, 1.5),
                x_title=Label("muon tightId")),
            # softmva not available for MuonBPark col
            Feature("muon_pfRelIso03_all", "MuonBPark_pfRelIso03_all", binning=(70, 0, 7),
                x_title=Label("muon pfRelIso03_all")),
            # Feature("muon_miniPFRelIso_all", "MuonBPark_miniPFRelIso_all", binning=(70, 0, 7),
                # x_title=Label("muon miniPFRelIso_all")),
            # MuonBPark_jetIdx not available

            Feature("min_chi2_index", "min_chi2_index", binning=(10, -0.5, 9.5),
                x_title=Label("min_chi2_index")),
            Feature("muonSV_chi2", "muonSV_chi2", binning=(50, 0, 1500),
                x_title=Label("muonSV chi2")),
            Feature("muonSV_pAngle", "muonSV_pAngle", binning=(70, 0, 3.5),
                x_title=Label("muonSV pAngle")),
            Feature("muonSV_dlen", "muonSV_dlen", binning=(80, 0, 20),
                x_title=Label("muonSV dlen")),
            Feature("muonSV_dlenSig", "muonSV_dlenSig", binning=(100, 0, 1500),
                x_title=Label("muonSV dlenSig")),
            Feature("muonSV_dxy", "muonSV_dxy", binning=(40, 0, 20),
                x_title=Label("muonSV dxy")),
            Feature("muonSV_dxySig", "muonSV_dxySig", binning=(100, 0, 2500),
                x_title=Label("muonSV dxySig")),

            Feature("muonSV_mu1pt", "muonSV_mu1pt", binning=(30, 0, 150),
                x_title=Label("muonSV muon1 p_{T}"),
                units="GeV"),
            Feature("muonSV_mu1eta", "muonSV_mu1eta", binning=(50, -5, 5),
                x_title=Label("muonSV muon1 #eta"),),
            Feature("muonSV_mu1phi", "muonSV_mu1phi", binning=(48, -6, 6),
                x_title=Label("muonSV muon1 #phi"),),
            Feature("muonSV_mu2pt", "muonSV_mu2pt", binning=(30, 0, 150),
                x_title=Label("muonSV muon2 p_{T}"),
                units="GeV"),
            Feature("muonSV_mu2eta", "muonSV_mu2eta", binning=(50, -5, 5),
                x_title=Label("muonSV muon2 #eta"),),
            Feature("muonSV_mu2phi", "muonSV_mu2phi", binning=(48, -6, 6),
                x_title=Label("muonSV muon2 #phi"),),
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
            Feature("muonSV_bestchi2_chi2", "muonSV_bestchi2_chi2", binning=(100, 0, 10),
                x_title=Label("muonSV chi2 (min #chi^2)"), tags=["lbn_light", "lbn"]),
            Feature("muonSV_bestchi2_chi2_with_mass_cut", "muonSV_bestchi2_chi2", selection="muonSV_bestchi2_mass > 5.0", binning=(100, 0, 10),
                x_title=Label("muonSV chi2 (min #chi^2)"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_pAngle_bestchi2", "muonSV_pAngle.at(min_chi2_index)", binning=(70, 0, 3.5),
            Feature("muonSV_bestchi2_pAngle", "muonSV_bestchi2_pAngle", binning=(100, 0, 3.5),
                x_title=Label("muonSV pAngle (min #chi^2)"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_dlen_bestchi2", "muonSV_dlen.at(min_chi2_index)", binning=(80, 0, 20),
            Feature("muonSV_bestchi2_dlen", "muonSV_bestchi2_dlen", binning=(80, 0, 20),
                x_title=Label("muonSV dlen"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_dlenSig_bestchi2", "muonSV_dlenSig.at(min_chi2_index)", binning=(100, 0, 1500),
            Feature("muonSV_bestchi2_dlenSig", "muonSV_bestchi2_dlenSig", binning=(100, 0, 1500),
                x_title=Label("muonSV dlenSig (min #chi^2)"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_dxy_bestchi2", "muonSV_dxy.at(min_chi2_index)", binning=(40, 0, 20),
            Feature("muonSV_bestchi2_dxy", "muonSV_bestchi2_dxy", binning=(100, 0, 25),
                x_title=Label("muonSV dxy"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_dxySig_bestchi2", "muonSV_dxySig.at(min_chi2_index)", binning=(100, 0, 2500),
            Feature("muonSV_bestchi2_dxySig", "muonSV_bestchi2_dxySig", binning=(100, 0, 1000),
                x_title=Label("muonSV dxySig (min #chi^2)"), tags=["lbn_light", "lbn"]),

            Feature("muonSV_x", "muonSV_x", binning=(50, -10, 10),
                x_title=Label("muonSV x")),
            Feature("muonSV_y", "muonSV_y", binning=(50, -10, 10),
                x_title=Label("muonSV y")),
            Feature("muonSV_z", "muonSV_z", binning=(100, -20, 20),
                x_title=Label("muonSV z")),

            # Feature("muonSV_x_bestchi2", "muonSV_x.at(min_chi2_index)", binning=(50, -10, 10),
            Feature("muonSV_bestchi2_x", "muonSV_bestchi2_x", binning=(50, -10, 10),
                x_title=Label("muonSV x (min #chi^2)"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_y_bestchi2", "muonSV_y.at(min_chi2_index)", binning=(50, -10, 10),
            Feature("muonSV_bestchi2_y", "muonSV_bestchi2_y", binning=(50, -10, 10),
                x_title=Label("muonSV y (min #chi^2)"), tags=["lbn_light", "lbn"]),
            # Feature("muonSV_z_bestchi2", "muonSV_z.at(min_chi2_index)", binning=(100, -20, 20),
            Feature("muonSV_bestchi2_z", "muonSV_bestchi2_z", binning=(100, -20, 20),
                x_title=Label("muonSV z (min #chi^2)"), tags=["lbn_light", "lbn"]),

            Feature("sv_pt", "SV_pt", binning=(30, 0, 150),
                x_title=Label("SV p_{T}"),
                units="GeV"),
            Feature("sv_eta", "SV_eta", binning=(50, -5, 5),
                x_title=Label("SV #eta"),),
            Feature("sv_phi", "SV_phi", binning=(48, -6, 6),
                x_title=Label("SV #phi"),),
            Feature("sv_mass", "SV_mass", binning=(120, 0, 4),
                x_title=Label("SV mass"),
                units="GeV",
                blinded_range=[1.5, 2.5]),
                # blinded_range=[[0.2, 0.4], [1.5, 2.5]]),
            Feature("sv_x", "SV_x", binning=(50, -4, 4),
                x_title=Label("muonSV x"),),
            Feature("sv_y", "SV_y", binning=(50, -4, 4),
                x_title=Label("muonSV y"),),
            Feature("sv_z", "SV_z", binning=(100, -20, 20),
                x_title=Label("muonSV z"),),
            Feature("sv_dxy", "SV_dxy", binning=(40, 0, 10),
                x_title=Label("SV dxy")),
            Feature("sv_dxySig", "SV_dxySig", binning=(100, 0, 750),
                x_title=Label("SV dxySig")),
            Feature("sv_dlen", "SV_dlen", binning=(72, 0, 12),
                x_title=Label("SV dlen")),
            Feature("sv_dlenSig", "SV_dlenSig", binning=(100, 0, 1000),
                x_title=Label("SV dlenSig")),
            Feature("sv_chi2", "SV_chi2", binning=(50, 0, 100),
                x_title=Label("SV chi2")),
            Feature("sv_pAngle", "SV_pAngle", binning=(70, 0, 3.5),
                x_title=Label("SV pAngle")),
            Feature("sv_ndof", "SV_ndof", binning=(15, -0.5, 14.5),
                x_title=Label("SV ndof")),

            Feature("nsv", "nsv", binning=(10, -0.5, 9.5),
                x_title=Label("nsv")),

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
            Feature("bdt", "bdt_scenarioA", binning=(20, 0, 1),
                x_title=Label("BDT score"),
            ),
            #Feature("bdt_scenarioA", "bdt_scenarioA_nojetsel", binning=(20, 0, 1),
            Feature("bdt_scenarioA", "bdt_scenarioA", binning=(20, 0, 1),
            #Feature("bdt_scenarioA", "bdt_new_scenarioA", binning=(20, 0, 1),
                x_title=Label("BDT score (scenario A)"),
            ),
            Feature("bdt_scenarioB1", "bdt_scenarioB1", binning=(20, 0, 1),
                x_title=Label("BDT score (scenario B1)"),
            ),
            Feature("bdt_scenarioB2", "bdt_new_scenarioB2", binning=(20, 0, 1),
                x_title=Label("BDT score (scenario B2)"),
            ),
            Feature("bdt_scenarioC", "bdt_new_scenarioC", binning=(20, 0, 1),
                x_title=Label("BDT score (scenario C)"),
            ),

            # Feature("muonSV_mass_min_chi2", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 22),
            # Feature("muonSV_bestchi2_mass", "muonSV_bestchi2_mass", binning=(1000, 0, 4),
            Feature("muonSV_bestchi2_mass", "muonSV_bestchi2_mass", binning=(50, 1.2635, 1.3965),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            Feature("muonSV_bestchi2_mass_0p33", "muonSV_bestchi2_mass",
                binning=(50, 0.333 - 5 * 0.01 * 0.333, 0.333 + 5 * 0.01 * 0.333),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange", "muonSV_bestchi2_mass", binning=(8270, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            Feature("muonSV_bestchi2_mass_fullrange_fewer_bins", "muonSV_bestchi2_mass", binning=(100, 0, 22),
                x_title=Label("muonSV mass (Min. #chi^{2})"),
                units="GeV"),
            # Feature("muonSV_mass_min_chi2_bdt", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 22),
            Feature("muonSV_mass_min_chi2_maxbdt", "muonSV_mass.at(min_chi2_index)", binning=(100, 0, 4),
                x_title=Label("muonSV mass (Min. #chi^{2}), BDT < 0.85"),
                selection="xgb0__m_2p0_ctau_10p0_xiO_1p0_xiL_1p0 < 0.85",
                units="GeV",
                blinded_range=[1.5, 2.5]),
            Feature("nmuonSV_3sigma", "nmuonSV_3sigma", binning=(11, -0.5, 10.5),
                x_title=Label("nmuonSV_3sigma"), tags=["lbn"]),

            Feature("puWeight", "puWeight", binning=(20, 0, 2),
                x_title=Label("puWeight"),
                systematics=["pu"]),
            Feature("idWeight", "idWeight", binning=(20, 0, 2),
                x_title=Label("idWeight"),
                systematics=["id"]),
            Feature("trigSF", "trigSF", binning=(20, 0, 2),
                x_title=Label("trigSF"),
                systematics=["trig"]),
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
            Systematic("pu", "", up="Up", down="Down"),
            Systematic("id", ""),
            Systematic("trig", ""),
            Systematic("jer", "_smeared", affected_categories=self.categories.names(),
                module_syst_type={
                    "jet_syst": {"up": "smeared_up", "down": "smeared_down"},
                    "met_syst": {"up": "up", "down": "down"},  # smearing included in the met_smear_tag
                }),
            # Systematic("tes", "_corr",
                # affected_categories=self.categories.names(),
                # module_syst_type="tau_syst"),
            # Systematic("empty", "", up="", down="")
        ]
        return ObjectCollection(systematics)

    def add_default_module_files(self):
        defaults = {}
        defaults["PreprocessRDF"] = "modules"
        defaults["PreCounter"] = "weights"
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
                    for children_process in self.get_children_from_process(process.name):
                        if children_process.name in syst.SystProcesses[isy]:
                            if syst_name not in systematics:
                                systematics[syst_name] = {}
                            iproc = syst.SystProcesses[isy].index(children_process.name)
                            systVal = syst.SystValues[isy][iproc]
                            systematics[syst_name][original_process.name] = eval(systVal)
                            break
        return systematics

# config = Config("base", year=2018, ecm=13, lumi_pb=59741)
config = Config("legacy_2018", year=2018, ecm=13, lumi_pb=33600)
