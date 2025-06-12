import law
import os

from cmt.base_tasks.base import DatasetTaskWithCategory, HTCondorWorkflow, SGEWorkflow, InputData

from analysis_tools.utils import create_file_dir, import_root
from cmt.base_tasks.preprocessing import PreprocessRDF

class TriggerSF(DatasetTaskWithCategory, law.LocalWorkflow, HTCondorWorkflow, SGEWorkflow):
    def create_branch_map(self):
        return len(self.dataset.get_files(
            os.path.expandvars("$CMT_TMP_DIR/%s/" % self.config_name), add_prefix=False,
            check_empty=True))

    def workflow_requires(self):
        #return {"data": PreprocessRDF.vreq(self)}
        return {"data": InputData.req(self)}
        

    def requires(self):
        #return PreprocessRDF.vreq(self)
        return {"data": InputData.req(self, file_index=self.branch)}

    def output(self):
        return self.local_target(f"data_{self.addendum}{self.branch}.root")

    def output(self):
        return self.local_target("histos_%s.root" % self.branch)
            
 
    def run(self):
        ROOT = import_root()
        def create_histos(path):
            
            df = ROOT.RDataFrame("Events", path)

            df = df.Filter("nMuon == 2").Filter("Muon_charge.at(0) != Muon_charge.at(1)").Filter("abs(Muon_eta.at(0)) < 2.4").Filter("abs(Muon_eta.at(1)) < 2.4").Filter("Muon_looseId.at(0) == 1").Filter("Muon_looseId.at(1) == 1")

            df = df.Filter("nmuonSV == 1").Filter("muonSV_dxySig.at(0) > 2").Filter("muonSV_chi2.at(0) < 5")

            df = df.Filter("muonSV_mass.at(0) > 2.9 && muonSV_mass.at(0) < 3.3")

            #df = df.Filter("HLT_Photon20 == 1")

            #df_trigger = df.Filter("HLT_Mu9_IP6_part0==1 || HLT_Mu9_IP6_part1==1 || HLT_Mu9_IP6_part2==1 || HLT_Mu9_IP6_part3==1 || HLT_Mu9_IP6_part4==1")
            #df_not_trigger =  df.Filter("HLT_Mu9_IP6_part0==0 && HLT_Mu9_IP6_part1==0 && HLT_Mu9_IP6_part2==0 && HLT_Mu9_IP6_part3==0 && HLT_Mu9_IP6_part4==0")
    

            df = df.Define("min_dxy", "Min(abs(Muon_dxy))").Define("min_pt", "Min(Muon_pt)")

            dxy_bin_1 = "min_dxy > 0.00001 && min_dxy < 0.001"
            dxy_bin_2 = "min_dxy > 0.001 && min_dxy < 0.1"
            dxy_bin_3 = "min_dxy > 0.1 && min_dxy < 1.0" 
            dxy_bin_4 = "min_dxy > 1.0 && min_dxy < 10.0"

            pt_bin_1 = "min_pt > 3.0 && min_pt < 4.0"
            pt_bin_2 = "min_pt > 4.0 && min_pt < 6.0"
            pt_bin_3 = "min_pt > 6.0 && min_pt < 10.0"
            pt_bin_4 = "min_pt > 10.0 && min_pt < 16.0"
            pt_bin_5 = "min_pt > 16.0 && min_pt < 30.0"

            dxy_bins = [dxy_bin_1, dxy_bin_2, dxy_bin_3, dxy_bin_4]
            pt_bins = [pt_bin_1, pt_bin_2, pt_bin_3, pt_bin_4, pt_bin_5]

            histos = {}   

            histos["h_dxy_pt"] = df.Histo2D(("h_dxy_pt", "; dxy (cm); pT (GeV)", 100, 0.00001, 10.0, 100, 3.0, 30.0), "min_dxy", "min_pt") 

            for i in dxy_bins:
                for j in pt_bins:
                   
                    dxy_index = dxy_bins.index(i)
                    pt_index = pt_bins.index(j)
         
                    histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] = df.Filter("HLT_Mu9_IP6_part0==1 || HLT_Mu9_IP6_part1==1 || HLT_Mu9_IP6_part2==1 || HLT_Mu9_IP6_part3==1 || HLT_Mu9_IP6_part4==1").Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass")     
                    histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] = df.Filter("HLT_Mu9_IP6_part0==0 && HLT_Mu9_IP6_part1==0 && HLT_Mu9_IP6_part2==0 && HLT_Mu9_IP6_part3==0 && HLT_Mu9_IP6_part4==0").Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_Fail" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass")   

            return histos
        
        path = self.input()["data"][0].path
        histos = create_histos(path)
        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()


'''
    h_dxy_1_pT_1_Pass = df_trigger.Filter(dxy_bin_1).Filter(pt_bin_1).histo1D(("h_dxy_1_pT_1_Pass", "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass") 

    h_dxy_1_pT_2_Pass = df_trigger.Filter(dxy_bin_1).Filter(pt_bin_2).histo1D(("h_dxy_1_pT_2_Pass", "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass")

    h_dxy_1_pT_3_Pass = df_trigger.Filter(dxy_bin_1).Filter(pt_bin_3).histo1D(("h_dxy_1_pT_3_Pass", "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass")

    h_dxy_1_pT_4_Pass = df_trigger.Filter(dxy_bin_1).Filter(pt_bin_4).histo1D(("h_dxy_1_pT_4_Pass", "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass")

    h_dxy_1_pT_5_Pass = df_trigger.Filter(dxy_bin_1).Filter(pt_bin_5).histo1D(("h_dxy_1_pT_5_Pass", "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass")
'''
     
 
class TriggerSFnew(TriggerSF):
    def add_to_root(self, root):
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"

            bool chi2sort (const std::pair<int, float>& a, const std::pair<int, float>& b)
            {
              return (a.second < b.second);
            }

            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            int get_muonsv_index(int nmuonSV, Vfloat muonSV_dxySig, Vfloat muonSV_chi2,
                Vfloat muonSV_mass, Vint Muon_looseId, Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta,
                Vint muonSV_mu1index, Vint muonSV_mu2index)
            {
                std::vector<std::pair<int, float>> index_chi2;
                for (int i = 0; i < nmuonSV; i++) {
                    if(muonSV_dxySig[i] < 2.0 || muonSV_chi2[i] > 5.0 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3) continue;
                    int index1 = muonSV_mu1index[i];
                    int index2 = muonSV_mu2index[i];
                    if(abs(muonSV_mu1eta[i]) > 2.4 || abs(muonSV_mu2eta[i]) > 2.4 ||
                        Muon_looseId[index1] == 0 || Muon_looseId[index2] == 0) continue;
                    index_chi2.push_back(std::make_pair(i, muonSV_chi2[i]));
                }
                if (index_chi2.size() > 0) {
                    std::stable_sort(index_chi2.begin(), index_chi2.end(), chi2sort);
                    return index_chi2[0].first;
                } else {
                    return -1;
                }
            }

            bool muon_pass(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)
                        return true;
                }
                return false;
            }
        
        """)
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)

        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)

        df = df.Filter("nmuonSV > 0")
        df = df.Define("muonSV_min_chi2_index", """
            get_muonsv_index(nmuonSV, muonSV_dxySig, muonSV_chi2,
                muonSV_mass, Muon_looseId, muonSV_mu1eta, muonSV_mu2eta,
                muonSV_mu1index, muonSV_mu2index)
        """).Filter("muonSV_min_chi2_index != -1")

        df = df.Define("muon1_index", "muonSV_mu1index.at(muonSV_min_chi2_index)")
        df = df.Define("muon2_index", "muonSV_mu2index.at(muonSV_min_chi2_index)")
        for var in ["dxy", "pt", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"Muon_{var}.at(muon1_index)")
            df = df.Define(f"muon2_{var}", f"Muon_{var}.at(muon2_index)")
        df = df.Define("muonSV_mass_minchi2", "muonSV_mass.at(muonSV_min_chi2_index)")

        df_pass1 = df.Filter("muon_pass(muon1_eta, muon1_phi, nMuonBPark, "
            "MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6)")
        df_pass2 = df.Filter("muon_pass(muon2_eta, muon2_phi, nMuonBPark, "
            "MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6)")

        muon1_dxy_bins = [
            "abs(muon1_dxy) > 0.001 && abs(muon1_dxy) < 0.1",
            "abs(muon1_dxy) > 0.1 && abs(muon1_dxy) < 1.0",
            "abs(muon1_dxy) > 1.0 && abs(muon1_dxy) < 10.0"
        ]

        muon1_pt_bins = [
            "muon1_pt > 3.0 && muon1_pt < 4.0",
            "muon1_pt > 4.0 && muon1_pt < 6.0",
            "muon1_pt > 6.0 && muon1_pt < 10.0",
            "muon1_pt > 10.0 && muon1_pt < 16.0",
            "muon1_pt > 16.0 && muon1_pt < 30.0"
        ]

        muon2_dxy_bins = [elem.replace("muon1", "muon2") for elem in muon1_dxy_bins]
        muon2_pt_bins = [elem.replace("muon1", "muon2") for elem in muon1_pt_bins]

        hist_tmp = {}
        for dxy_index, i in enumerate(muon1_dxy_bins):
            for pt_index, j in enumerate(muon1_pt_bins):
                a = muon2_dxy_bins[dxy_index]
                b = muon2_pt_bins[pt_index]
                hist_tmp[f"h_dxy_pT_muon1_{dxy_index}_{pt_index}"] = df.Filter(i).Filter(j).Histo1D(
                    ("h_dxy_%s_pT_%s_muon1" % (dxy_index, pt_index),
                        "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4),
                    "muonSV_mass_minchi2")
                hist_tmp[f"h_dxy_pT_muon2_{dxy_index}_{pt_index}"] = df.Filter(a).Filter(b).Histo1D(
                    ("h_dxy_%s_pT_%s_muon2" % (dxy_index, pt_index),
                    "   ; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4),
                    "muonSV_mass_minchi2")
                hist_tmp[f"h_dxy_pT_muon1_{dxy_index}_{pt_index}_pass"] = df_pass1.Filter(i).Filter(j).Histo1D(
                    ("h_dxy_%s_pT_%s_muon1" % (dxy_index, pt_index),
                        "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4),
                    "muonSV_mass_minchi2")
                hist_tmp[f"h_dxy_pT_muon2_{dxy_index}_{pt_index}_pass"] = df_pass2.Filter(a).Filter(b).Histo1D(
                    ("h_dxy_%s_pT_%s_muon2" % (dxy_index, pt_index),
                    "   ; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4),
                    "muonSV_mass_minchi2")


        histos = {}
        for dxy_index, i in enumerate(muon1_dxy_bins):
            for pt_index, j in enumerate(muon1_pt_bins):
                histos[f"h_dxy_pT_{dxy_index}_{pt_index}"] =\
                    hist_tmp[f"h_dxy_pT_muon1_{dxy_index}_{pt_index}"].Clone(
                        f"h_dxy_pT_{dxy_index}_{pt_index}")
                histos[f"h_dxy_pT_{dxy_index}_{pt_index}"].Add(
                    hist_tmp[f"h_dxy_pT_muon2_{dxy_index}_{pt_index}"].Clone())

                histos[f"h_dxy_pT_{dxy_index}_{pt_index}_pass"] =\
                    hist_tmp[f"h_dxy_pT_muon1_{dxy_index}_{pt_index}_pass"].Clone(
                        f"h_dxy_pT_{dxy_index}_{pt_index}_pass")
                histos[f"h_dxy_pT_{dxy_index}_{pt_index}_pass"].Add(
                    hist_tmp[f"h_dxy_pT_muon2_{dxy_index}_{pt_index}_pass"].Clone())

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()
        
        


class TriggerSFtnp(TriggerSF):
    def add_to_root(self, root):
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"

            bool chi2sort (const std::pair<int, float>& a, const std::pair<int, float>& b)
            {
              return (a.second < b.second);
            }

            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            int get_muonsv_index(int nmuonSV, Vfloat muonSV_dxySig, Vfloat muonSV_chi2, Vfloat muonSV_mass, Vint Muon_looseId, Vfloat Muon_sip3d, Vfloat muonSV_mu1pt, Vfloat muonSV_mu2pt, Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi, Vint muonSV_mu1index, Vint muonSV_mu2index)
            {
                std::vector<std::pair<int, float>> index_chi2;
                for (int i = 0; i < nmuonSV; i++) {
                    if(reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) > 1.2 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3) continue;
                    //if(muonSV_dxySig[i] < 2.0 || muonSV_chi2[i] > 5.0 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3) continue;
                    int index1 = muonSV_mu1index[i];
                    int index2 = muonSV_mu2index[i];
                    if(abs(muonSV_mu1eta[i]) > 1.5 || abs(muonSV_mu2eta[i]) > 1.5 || Muon_looseId[index1] == 0 || Muon_looseId[index2] == 0) continue;
                    index_chi2.push_back(std::make_pair(i, muonSV_chi2[i]));
                }
                if (index_chi2.size() > 0) {
                    std::stable_sort(index_chi2.begin(), index_chi2.end(), chi2sort);
                    return index_chi2[0].first;
                } else {
                    return -1;
                }
            }

            bool muon_pass(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)
                        return true;
                }
                return false;
            }

            bool muon_pass_tag(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)
                        return true;
                }
                return false;
            }

            ROOT::RVec<float> probe_values(float muon1_eta, float muon1_phi, float muon1_dxy, float muon1_pt, float muon1_sip3d,
                float muon2_eta, float muon2_phi, float muon2_dxy, float muon2_pt, float muon2_sip3d, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, Vfloat MuonBPark_fired_HLT_Mu20, Vfloat MuonBPark_fired_HLT_Mu27, Vfloat MuonBPark_fired_HLT_Mu50, Vfloat MuonBPark_fired_HLT_Mu55) 
            {
                ROOT::RVec<float> probe_dxy_pt_HLT(4);

                if (muon_pass_tag(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55]) && muon_pass_tag(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55])){
                    bool HLT = muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                }
                
                //if both muons are matched to the HLT_Mu20 trigger muon, choose the muon with highest pT (muon1) as the tag

                else if (muon_pass_tag(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55])){
                    bool HLT = muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                }
                else{ 
                    bool HLT = muon_pass(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon1_dxy;
                    probe_dxy_pt_HLT.at(1) = muon1_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                }
                return probe_dxy_pt_HLT;
            }

        
        """)
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)

        print(self.input()["data"])

        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)

        df = df.Filter("nmuonSV > 0")
        df = df.Define("muonSV_min_chi2_index", """
            get_muonsv_index(nmuonSV, muonSV_dxySig, muonSV_chi2, muonSV_mass, Muon_looseId, Muon_sip3d, muonSV_mu1pt, muonSV_mu2pt, muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index)
        """).Filter("muonSV_min_chi2_index != -1")

        df = df.Define("muon1_index", "muonSV_mu1index.at(muonSV_min_chi2_index)")
        df = df.Define("muon2_index", "muonSV_mu2index.at(muonSV_min_chi2_index)")
        for var in ["dxy", "pt", "sip3d", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"Muon_{var}.at(muon1_index)")
            df = df.Define(f"muon2_{var}", f"Muon_{var}.at(muon2_index)")
        df = df.Define("muonSV_mass_minchi2", "muonSV_mass.at(muonSV_min_chi2_index)")
 
        #for tag using HLT_Mu20
        
        df = df.Filter("muon_pass_tag(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55]) && muon_pass_tag(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55])")
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxy, muon1_pt, muon1_sip3d, muon2_eta, muon2_phi, muon2_dxy, muon2_pt, muon2_sip3d, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_fired_HLT_Mu20, MuonBPark_fired_HLT_Mu27, MuonBPark_fired_HLT_Mu50, MuonBPark_fired_HLT_Mu55)")
        
 
        #for tag using HLT_Mu12_IP6
        '''
        df = df.Filter("muon_pass(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu12_IP6) || muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu12_IP6)")
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxy, muon1_pt, muon2_eta, muon2_phi, muon2_dxy, muon2_pt, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_fired_HLT_Mu12_IP6)")
        '''

        df = df.Define("probe_dxy", "probe_quantities.at(0)").Define("probe_pt", "probe_quantities.at(1)").Define("probe_HLT", "probe_quantities.at(2)").Define("probe_sip3d", "probe_quantities.at(3)")

        df_pass = df.Filter("probe_HLT == 1")

        dxy_bins = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        
        pt_bins = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]
        
        '''
        pt_bins = [
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]
        '''
        histos = {}
        for dxy_index, i in enumerate(dxy_bins):
            for pt_index, j in enumerate(pt_bins):
                h_dxy_pT_total = df.Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_total" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_dxy_pT_pass = df_pass.Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
                h_dxy_pT_fail.SetName("h_dxy_%s_pT_%s_Fail"% (dxy_index, pt_index)) 

                histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] = h_dxy_pT_pass
                histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] = h_dxy_pT_fail


        #for 1D efficiency
        dxy_bins2 = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.5",
            "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]

        pt_bins2 = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 5.0",
            "probe_pt > 5.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 7.0",
            "probe_pt > 7.0 && probe_pt < 8.0",
            "probe_pt > 8.0 && probe_pt < 9.0",
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]

        IPsig_bins2 = [
            "probe_sip3d > 0.0 && probe_sip3d < 1.0",
            "probe_sip3d > 1.0 && probe_sip3d < 2.0",
            "probe_sip3d > 2.0 && probe_sip3d < 3.0",
            "probe_sip3d > 3.0 && probe_sip3d < 4.0",
            "probe_sip3d > 4.0 && probe_sip3d < 5.0",
            "probe_sip3d > 5.0 && probe_sip3d < 6.0",
            "probe_sip3d > 6.0 && probe_sip3d < 7.0",
            "probe_sip3d > 7.0 && probe_sip3d < 15.0",
            "probe_sip3d > 15.0 && probe_sip3d < 30.0"
        ]
 

        for dxy_index, i in enumerate(dxy_bins2):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_%s_pT_100_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_%s_pT_100_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_100_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_100_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_100_Fail" % (dxy_index)] = h_dxy_pT_fail

        for pt_index, i in enumerate(pt_bins2):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_100_pT_%s_total" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_100_pT_%s_Pass" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_100_pT_%s_Fail"% (pt_index)) 

            histos["h_dxy_100_pt_%s_Pass" % (pt_index)] = h_dxy_pT_pass
            histos["h_dxy_100_pt_%s_Fail" % (pt_index)] = h_dxy_pT_fail
        
        for dxy_index, i in enumerate(IPsig_bins2):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_%s_pT_1000_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_%s_pT_1000_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_1000_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_1000_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_1000_Fail" % (dxy_index)] = h_dxy_pT_fail

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()
        


class TriggerSFtnpbparking(TriggerSF):
    def add_to_root(self, root):
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"

            static double igf(double S, double Z)
            {
                if(Z < 0.0)
                {
	            return 0.0;
                }
                double Sc = (1.0 / S);
                Sc *= pow(Z, S);
                Sc *= exp(-Z);
 
                double Sum = 1.0;
                double Nom = 1.0;
                double Denom = 1.0;
 
                for(int I = 0; I < 200; I++)
                {
	            Nom *= Z;
	            S++;
	            Denom *= S;
	            Sum += (Nom / Denom);
                }
 
                return Sum * Sc;
            }

            double chisqr(int Dof, double Cv)
            {
                if(Cv < 0 || Dof < 1)
                {
                    return 0.0;
                }
                double K = ((double)Dof) * 0.5;
                double X = Cv * 0.5;
                if(Dof == 2)
                {
	            return exp(-1.0 * X);
                }
 
                double PValue = igf(K, X);
                if(std::isnan(PValue) || std::isinf(PValue) || PValue <= 1e-8)
                {
                    return 1e-14;
                } 

                PValue /= tgamma(K); 
            	
                return (1.0 - PValue);
            }

            bool chi2sort (const std::pair<int, float>& a, const std::pair<int, float>& b)
            {
              return (a.second < b.second);
            }

            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            int get_muonsv_index(int nmuonSV, Vfloat muonSV_dxySig, Vfloat muonSV_chi2, Vfloat muonSV_mass, Vint Muon_looseId, Vfloat Muon_sip3d, Vfloat muonSV_mu1pt, Vfloat muonSV_mu2pt, Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi, Vint muonSV_mu1index, Vint muonSV_mu2index)
            {
                std::cout << "call get_muonsv_index function" << std::endl;
                std::vector<std::pair<int, float>> index_chi2;
                for (int i = 0; i < nmuonSV; i++) {
                    if(reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) > 1.2 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3) continue;
                    //if(muonSV_dxySig[i] < 2.0 || muonSV_chi2[i] > 5.0 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3) continue;
                    int index1 = muonSV_mu1index[i];
                    int index2 = muonSV_mu2index[i];
                    if(abs(muonSV_mu1eta[i]) > 1.5 || abs(muonSV_mu2eta[i]) > 1.5 || Muon_looseId[index1] == 0 || Muon_looseId[index2] == 0) continue;
                    index_chi2.push_back(std::make_pair(i, muonSV_chi2[i]));
                }
                std::cout << "index_chi2.size = " << index_chi2.size() << std::endl;
                if (index_chi2.size() > 0) {
                    std::stable_sort(index_chi2.begin(), index_chi2.end(), chi2sort);
                    return index_chi2[0].first;
                } else {
                    return -1;
                }
            }

            bool muon_pass(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6)
            {
                std::cout << "call muon_pass function" << std::endl;
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3 && muon_pt > 10.0 && abs(muon_dxy)/muon_dxyErr > 8.0)
                    //if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)    
                        return true;
                }
                return false;
            }

            bool muon_pass_probe(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)
                        return true;
                }
                return false;
            }

            bool muon_pass_tag(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)
                        return true;
                }
                return false;
            }

            ROOT::RVec<float> probe_values(float muon1_eta, float muon1_phi, float muon1_dxy, float muon1_dxyErr, float muon1_pt, float muon1_sip3d,
                float muon2_eta, float muon2_phi, float muon2_dxy, float muon2_dxyErr, float muon2_pt, float muon2_sip3d, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, Vfloat MuonBPark_fired_HLT_Mu20) 
            {
                ROOT::RVec<float> probe_dxy_pt_HLT(4);

                if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu20) && muon_pass(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu20)){
                    bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                }
                
                //if both muons are matched to the HLT_Mu20 trigger muon, choose the muon with highest pT (muon1) as the tag

                else if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu20)){
                    bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                }
                else{ 
                    bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon1_dxy;
                    probe_dxy_pt_HLT.at(1) = muon1_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                }
                return probe_dxy_pt_HLT;
            }

        
        """)
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)

        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)

        df = df.Filter("nmuonSV > 0")
        df = df.Define("muonSV_min_chi2_index", """
            get_muonsv_index(nmuonSV, muonSV_dxySig, muonSV_chi2, muonSV_mass, Muon_looseId, Muon_sip3d, muonSV_mu1pt, muonSV_mu2pt, muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index)
        """).Filter("muonSV_min_chi2_index != -1")

        df = df.Define("muon1_index", "muonSV_mu1index.at(muonSV_min_chi2_index)")
        df = df.Define("muon2_index", "muonSV_mu2index.at(muonSV_min_chi2_index)")
        for var in ["dxy", "dxyErr", "pt", "sip3d", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"Muon_{var}.at(muon1_index)")
            df = df.Define(f"muon2_{var}", f"Muon_{var}.at(muon2_index)")
        df = df.Define("muonSV_mass_minchi2", "muonSV_mass.at(muonSV_min_chi2_index)")
 
        
        #for tag using HLT_Mu12_IP6
        
        df = df.Filter("muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu20) || muon_pass(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu20)")
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxy, muon1_dxyErr, muon1_pt, muon1_sip3d, muon2_eta, muon2_phi, muon2_dxy, muon2_dxyErr, muon2_pt, muon2_sip3d, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_fired_HLT_Mu20)")
        

        df = df.Define("probe_dxy", "probe_quantities.at(0)").Define("probe_pt", "probe_quantities.at(1)").Define("probe_HLT", "probe_quantities.at(2)").Define("probe_sip3d", "probe_quantities.at(3)")

        df_pass = df.Filter("probe_HLT == 1")

        dxy_bins = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        
        pt_bins = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]
        
        '''
        pt_bins = [
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]
        '''
        histos = {}
        for dxy_index, i in enumerate(dxy_bins):
            for pt_index, j in enumerate(pt_bins):
                h_dxy_pT_total = df.Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_total" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_dxy_pT_pass = df_pass.Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
                h_dxy_pT_fail.SetName("h_dxy_%s_pT_%s_Fail"% (dxy_index, pt_index)) 

                histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] = h_dxy_pT_pass
                histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] = h_dxy_pT_fail
        
        #for 1D efficiency
        dxy_bins2 = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.5",
            "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]

        pt_bins2 = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 5.0",
            "probe_pt > 5.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 7.0",
            "probe_pt > 7.0 && probe_pt < 8.0",
            "probe_pt > 8.0 && probe_pt < 9.0",
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]

        IPsig_bins2 = [
            "probe_sip3d > 0.0 && probe_sip3d < 1.0",
            "probe_sip3d > 1.0 && probe_sip3d < 2.0",
            "probe_sip3d > 2.0 && probe_sip3d < 3.0",
            "probe_sip3d > 3.0 && probe_sip3d < 4.0",
            "probe_sip3d > 4.0 && probe_sip3d < 5.0",
            "probe_sip3d > 5.0 && probe_sip3d < 6.0",
            "probe_sip3d > 6.0 && probe_sip3d < 7.0",
            "probe_sip3d > 7.0 && probe_sip3d < 15.0",
            "probe_sip3d > 15.0 && probe_sip3d < 30.0"
        ]       

        for dxy_index, i in enumerate(dxy_bins2):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_%s_pT_100_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_%s_pT_100_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_100_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_100_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_100_Fail" % (dxy_index)] = h_dxy_pT_fail

        for pt_index, i in enumerate(pt_bins2):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_100_pT_%s_total" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_100_pT_%s_Pass" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_100_pT_%s_Fail"% (pt_index)) 

            histos["h_dxy_100_pt_%s_Pass" % (pt_index)] = h_dxy_pT_pass
            histos["h_dxy_100_pt_%s_Fail" % (pt_index)] = h_dxy_pT_fail

        for dxy_index, i in enumerate(IPsig_bins2):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_%s_pT_1000_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_%s_pT_1000_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_1000_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_1000_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_1000_Fail" % (dxy_index)] = h_dxy_pT_fail

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()





class TriggerSFtnpRk(TriggerSF):
    def add_to_root(self, root):
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"
            #include <cmath>

            static double igf(double S, double Z)
            {
                if(Z < 0.0)
                {
	            return 0.0;
                }
                double Sc = (1.0 / S);
                Sc *= pow(Z, S);
                Sc *= exp(-Z);
 
                double Sum = 1.0;
                double Nom = 1.0;
                double Denom = 1.0;
 
                for(int I = 0; I < 200; I++)
                {
	            Nom *= Z;
	            S++;
	            Denom *= S;
	            Sum += (Nom / Denom);
                }
 
                return Sum * Sc;
            }

            double chisqr(int Dof, double Cv)
            {
                if(Cv < 0 || Dof < 1)
                {
                    return 0.0;
                }
                double K = ((double)Dof) * 0.5;
                double X = Cv * 0.5;
                if(Dof == 2)
                {
	            return exp(-1.0 * X);
                }
 
                double PValue = igf(K, X);
                if(std::isnan(PValue) || std::isinf(PValue) || PValue <= 1e-8)
                {
                    return 1e-14;
                } 

                PValue /= tgamma(K); 
            	
                return (1.0 - PValue);
            }

            bool chi2sort (const std::pair<int, float>& a, const std::pair<int, float>& b)
            {
              return (a.second < b.second);
            }

            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;

            int get_muonsv_index(int nmuonSV, Vfloat muonSV_chi2, Vfloat muonSV_z, float PV_z, Vfloat muonSV_mass, Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi, Vint muonSV_mu1index, Vint muonSV_mu2index)
            {
                //std::cout << "call get_muonsv_index function" << std::endl;
                std::vector<std::pair<int, float>> index_chi2;
                for (int i = 0; i < nmuonSV; i++) {
                    if (chisqr(1, muonSV_chi2[i]) < 0.01 || abs(muonSV_z[i] - PV_z) > 0.5 || reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) < 0.15 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3) continue;
                    int index1 = muonSV_mu1index[i];
                    int index2 = muonSV_mu2index[i];
                    index_chi2.push_back(std::make_pair(i, muonSV_chi2[i]));
                }
                //std::cout << "index_chi2.size = " << index_chi2.size() << std::endl;
                if (index_chi2.size() > 0) {
                    //std::cout << "before sort" << std::endl;
                    std::stable_sort(index_chi2.begin(), index_chi2.end(), chi2sort);
                    //std::cout << "after sort" << std::endl;
                    //std::cout << "index = " << index_chi2[0].first << std::endl;
                    return index_chi2[0].first;
                } else {
                    return -1;
                }
            }

            
            bool muon_pass(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_tightId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt, Vfloat TrigObjBPark_l1dR)
            {
                
                //std::cout << "call muon_pass function" << std::endl;
                
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    //std::cout << "pass trigger" << std::endl;    
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3 && muon_pt > 10.0 && abs(muon_dxy)/muon_dxyErr > 8.0 && muon_tightId == 1){
                        //std::cout << "before TrigObjBPark check" << std::endl;
                        
                        for (int j = 0; j < nTrigObjBPark; j++) {
                            if (reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) < 0.05 && TrigObjBPark_l1pt[j] > 10.0 && TrigObjBPark_l1dR[j] < 0.05){
                                //std::cout << "muon pass!" << std::endl;
                                return true;
                            }
                        }
                        
                    }
                }
                //std::cout << "don't pass trigger" << std::endl;
                

                return false;
            }
            


            bool muon_pass_probe(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_mediumId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3 && muon_mediumId == 1)       
                        return true;
                }
                return false;
            }

            bool muon_pass_tag(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)
                        return true;
                }
                return false;
            }

            ROOT::RVec<float> probe_values(float muon1_eta, float muon1_phi, float muon1_dxy, float muon1_dxyErr, float muon1_pt, float muon1_sip3d, int muon1_tightId, int muon1_mediumId,
                float muon2_eta, float muon2_phi, float muon2_dxy, float muon2_dxyErr, float muon2_pt, float muon2_sip3d, int muon2_tightId, int muon2_mediumId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt, Vfloat TrigObjBPark_l1dR) 
            {
                //std::cout << "call probe_values function" << std::endl;
                ROOT::RVec<float> probe_dxy_pt_HLT(6);

                if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) && muon_pass(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)){
                    bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon2_eta;
                }
                
                //if both muons are matched to the HLT_Mu20 trigger muon, choose the muon with highest pT (muon1) as the tag

                else if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)){
                    bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon2_eta;
                }
                else{ 
                    bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon1_dxy;
                    probe_dxy_pt_HLT.at(1) = muon1_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon1_dxy)/muon1_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon1_eta;
                }
                return probe_dxy_pt_HLT;
            }

        
        """)
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)

        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)

        df.Snapshot("Events", "all_ev.root")

        df = df.Filter("nmuonSV > 0")
        df = df.Define("muonSV_min_chi2_index", """
            get_muonsv_index(nmuonSV, muonSV_chi2, muonSV_z, PV_z, muonSV_mass, muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index)
        """).Filter("muonSV_min_chi2_index != -1")

        df = df.Define("muon1_index", "muonSV_mu1index.at(muonSV_min_chi2_index)")
        df = df.Define("muon2_index", "muonSV_mu2index.at(muonSV_min_chi2_index)")
        for var in ["dxy", "dxyErr", "pt", "sip3d", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"float var; var = Muon_{var}.at(muon1_index); return var;")
            df = df.Define(f"muon2_{var}", f"float var; var = Muon_{var}.at(muon2_index); return var;")

        for var in ["tightId", "mediumId"]:
            df = df.Define(f"muon1_{var}", f"int var; var = Muon_{var}.at(muon1_index); return var;")
            df = df.Define(f"muon2_{var}", f"int var; var = Muon_{var}.at(muon2_index); return var;")


        df = df.Define("muonSV_mass_minchi2", "muonSV_mass.at(muonSV_min_chi2_index)")
 
        
        

        #print("Finish defining muon qunatities")
        
        #for tag using HLT_Mu12_IP6
        
        df = df.Filter("muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) || muon_pass(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)")
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxy, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_tightId, muon1_mediumId, muon2_eta, muon2_phi, muon2_dxy, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_tightId, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)")
        

        df = df.Define("probe_dxy", "probe_quantities.at(0)").Define("probe_pt", "probe_quantities.at(1)").Define("probe_HLT", "probe_quantities.at(2)").Define("probe_sip3d", "probe_quantities.at(3)").Define("probe_dxysig", "probe_quantities.at(4)").Define("probe_eta", "probe_quantities.at(5)")

        df_pass = df.Filter("probe_HLT == 1")

        dxy_bins = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        
        pt_bins = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]
        
        eta_bins_bparking = "abs(probe_eta) < 1.5"

        '''
        pt_bins = [
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]
        '''
        histos = {}
        for dxy_index, i in enumerate(dxy_bins):
            for pt_index, j in enumerate(pt_bins):
                h_dxy_pT_total = df.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_%s_total" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_dxy_pT_pass = df_pass.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
                h_dxy_pT_fail.SetName("h_dxy_%s_pT_%s_Fail"% (dxy_index, pt_index)) 

                histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] = h_dxy_pT_pass
                histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] = h_dxy_pT_fail
        
        
        dxysig_bins3 = [
            "probe_dxysig > 4.5 && probe_dxysig < 5.5",
            "probe_dxysig > 5.5 && probe_dxysig < 6.5",
            "probe_dxysig > 6.5 && probe_dxysig < 7.5",
            "probe_dxysig > 7.5 && probe_dxysig < 8.5",
            "probe_dxysig > 8.5 && probe_dxysig < 10.0",
            "probe_dxysig > 10.0 && probe_dxysig < 15.0",
            "probe_dxysig > 15.0 && probe_dxysig < 20.0",
            "probe_dxysig > 20.0 && probe_dxysig < 50.0"
        ]
        
        pt_bins3 = [
            "probe_pt > 8.0 && probe_pt < 9.0",
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 12.0",
            "probe_pt > 12.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 20.0",
            "probe_pt > 20.0 && probe_pt < 30.0"
        ]

        eta_bins3 = "abs(probe_eta) < 0.4"
        #eta_bins3 = "abs(probe_eta) > 0.4 && abs(probe_eta) < 0.8"
        #eta_bins3 = "abs(probe_eta) > 0.8 && abs(probe_eta) < 1.5"


        for dxy_index, i in enumerate(dxysig_bins3):
            for pt_index, j in enumerate(pt_bins3):
                h_dxysig_pT_total = df.Filter(i).Filter(j).Filter(eta_bins3).Histo1D(("h_dxysig_%s_pT_%s_total" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_dxysig_pT_pass = df_pass.Filter(i).Filter(j).Filter(eta_bins3).Histo1D(("h_dxysig_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_dxysig_pT_fail = h_dxysig_pT_total.GetPtr() - h_dxysig_pT_pass.GetPtr()
                h_dxysig_pT_fail.SetName("h_dxysig_%s_pT_%s_Fail"% (dxy_index, pt_index)) 

                histos["h_dxysig_%s_pt_%s_Pass" % (dxy_index, pt_index)] = h_dxysig_pT_pass
                histos["h_dxysig_%s_pt_%s_Fail" % (dxy_index, pt_index)] = h_dxysig_pT_fail
        
        
        #for 1D efficiency
        dxy_bins2 = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.5",
            "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]

        pt_bins2 = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 5.0",
            "probe_pt > 5.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 7.0",
            "probe_pt > 7.0 && probe_pt < 8.0",
            "probe_pt > 8.0 && probe_pt < 9.0",
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]

        IPsig_bins2 = [
            "probe_sip3d > 0.0 && probe_sip3d < 1.0",
            "probe_sip3d > 1.0 && probe_sip3d < 2.0",
            "probe_sip3d > 2.0 && probe_sip3d < 3.0",
            "probe_sip3d > 3.0 && probe_sip3d < 4.0",
            "probe_sip3d > 4.0 && probe_sip3d < 5.0",
            "probe_sip3d > 5.0 && probe_sip3d < 6.0",
            "probe_sip3d > 6.0 && probe_sip3d < 7.0",
            "probe_sip3d > 7.0 && probe_sip3d < 15.0",
            "probe_sip3d > 15.0 && probe_sip3d < 30.0"
        ]       

        for dxy_index, i in enumerate(dxy_bins2):
            h_dxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_100_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_100_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_100_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_100_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_100_Fail" % (dxy_index)] = h_dxy_pT_fail

        for pt_index, i in enumerate(pt_bins2):
            h_dxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_100_pT_%s_total" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_100_pT_%s_Pass" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_100_pT_%s_Fail"% (pt_index)) 

            histos["h_dxy_100_pt_%s_Pass" % (pt_index)] = h_dxy_pT_pass
            histos["h_dxy_100_pt_%s_Fail" % (pt_index)] = h_dxy_pT_fail

        for dxy_index, i in enumerate(IPsig_bins2):
            h_dxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_1000_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_1000_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_1000_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_1000_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_1000_Fail" % (dxy_index)] = h_dxy_pT_fail

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()



class TriggerSFtnpRknew(TriggerSF):
    def add_to_root(self, root):
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"
            #include <cmath>

            static double igf(double S, double Z)
            {
                if(Z < 0.0)
                {
	            return 0.0;
                }
                double Sc = (1.0 / S);
                Sc *= pow(Z, S);
                Sc *= exp(-Z);
 
                double Sum = 1.0;
                double Nom = 1.0;
                double Denom = 1.0;
 
                for(int I = 0; I < 200; I++)
                {
	            Nom *= Z;
	            S++;
	            Denom *= S;
	            Sum += (Nom / Denom);
                }
 
                return Sum * Sc;
            }

            double chisqr(int Dof, double Cv)
            {
                if(Cv < 0 || Dof < 1)
                {
                    return 0.0;
                }
                double K = ((double)Dof) * 0.5;
                double X = Cv * 0.5;
                if(Dof == 2)
                {
	            return exp(-1.0 * X);
                }
 
                double PValue = igf(K, X);
                if(std::isnan(PValue) || std::isinf(PValue) || PValue <= 1e-8)
                {
                    return 1e-14;
                } 

                PValue /= tgamma(K); 
            	
                return (1.0 - PValue);
            }

            bool chi2sort (const std::pair<int, float>& a, const std::pair<int, float>& b)
            {
              return (a.second < b.second);
            }

            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;

            int get_muonsv_index(int nmuonSV, Vfloat muonSV_chi2, Vfloat muonSV_z, float PV_z, Vfloat muonSV_mass, Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi, Vint muonSV_mu1index, Vint muonSV_mu2index, Vint muonSV_charge)
            //int get_muonsv_index(int nmuonSV, Vfloat muonSV_chi2, Vfloat muonSV_z, float PV_z, Vfloat muonSV_mass, Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi, Vint muonSV_mu1index, Vint muonSV_mu2index)
            {
                //std::cout << "call get_muonsv_index function" << std::endl;
                std::vector<std::pair<int, float>> index_chi2;
                for (int i = 0; i < nmuonSV; i++) {
                    //if (chisqr(1, muonSV_chi2[i]) < 0.01 || abs(muonSV_z[i] - PV_z) > 0.5 || reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) < 0.15 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3 || muonSV_charge[i] != 0) continue;
                    if (chisqr(1, muonSV_chi2[i]) < 0.01 || reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) < 0.15 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3 || muonSV_charge[i] != 0) continue;
                    //if (chisqr(1, muonSV_chi2[i]) < 0.01 || reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) < 0.15) continue;

                    int index1 = muonSV_mu1index[i];
                    int index2 = muonSV_mu2index[i];
                    index_chi2.push_back(std::make_pair(i, muonSV_chi2[i]));
                }
                //std::cout << "index_chi2.size = " << index_chi2.size() << std::endl;
                if (index_chi2.size() > 0) {
                    //std::cout << "before sort" << std::endl;
                    std::stable_sort(index_chi2.begin(), index_chi2.end(), chi2sort);
                    //std::cout << "after sort" << std::endl;
                    //std::cout << "index = " << index_chi2[0].first << std::endl;
                    return index_chi2[0].first;
                } else {
                    return -1;
                }
            }

            
            bool muon_pass(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_tightId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt, Vfloat TrigObjBPark_l1dR)
            //bool muon_pass(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_tightId, int nMuonBPark, Vfloat MuonBPark_eta,
                //Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt)
            {
                
                //std::cout << "call muon_pass function" << std::endl;
                
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    //std::cout << "pass trigger" << std::endl; 
                    //std::cout<< "i = " << i << " " << reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) << " " << muon_pt << abs(muon_dxy)/muon_dxyErr << muon_tightId << std::endl;   
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.1 && muon_pt > 10.0 && abs(muon_dxy)/muon_dxyErr > 8.0 && muon_tightId == 1){
                        //std::cout << "before TrigObjBPark check" << std::endl;
                        
                        for (int j = 0; j < nTrigObjBPark; j++) {
                            //std::cout<< "j = " << j << " " << reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) << " " << TrigObjBPark_l1pt[j] << " " << TrigObjBPark_l1dR[j] << std::endl;
                            if (reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) < 0.05 && TrigObjBPark_l1pt[j] > 10.0 && TrigObjBPark_l1dR[j] < 0.05){
                            //if (reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) < 0.05 && TrigObjBPark_l1pt[j] > 10.0){
                                //std::cout << "muon pass!" << std::endl;
                                return true;
                            }
                        }
                        
                    }
                }
                //std::cout << "don't pass trigger" << std::endl;
                

                return false;
            }

            float muonBPark_matched_dR(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, Vfloat MuonBPark_matched_dr)
            {
                float dR = 999999;
                int index = -1;
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < dR){
                        dR = reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]);
                        index = i;
                    }
                }

                if (index != -1) 
                    return MuonBPark_matched_dr.at(index);
                else 
                    return -999.0;

            }    
            


            bool muon_pass_probe(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_mediumId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    //std::cout<< i << " "<< MuonBPark_fired_HLT_Mu9_IP6[i] << " " << reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) << std::endl;
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.1 && muon_mediumId == 1){  
                        for (int j = 0; j < nTrigObjBPark; j++) {
                            if (reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) < 0.2)
                                return true;
                        }
                    }
                }
                return false;
            }

            bool muon_pass_tag(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)
                        return true;
                }
                return false;
            }

            ROOT::RVec<float> probe_values(float muon1_eta, float muon1_phi, float muon1_dxy, float muon1_dxyErr, float muon1_pt, float muon1_sip3d, int muon1_tightId, int muon1_mediumId,
                float muon2_eta, float muon2_phi, float muon2_dxy, float muon2_dxyErr, float muon2_pt, float muon2_sip3d, int muon2_tightId, int muon2_mediumId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt, Vfloat TrigObjBPark_l1dR, Vfloat MuonBPark_matched_dr) 
            {
                //std::cout << "call probe_values function" << std::endl;
                ROOT::RVec<float> probe_dxy_pt_HLT(6);

                if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) && muon_pass(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)){
                    //std::cout<<"block 1"<<std::endl;

                    //if both muons are matched to the HLT_Mu9_IP6 trigger muon, choose the muon with highest pT (muon1) as the tag
                    //bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                    //probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    //probe_dxy_pt_HLT.at(1) = muon2_pt;
                    //probe_dxy_pt_HLT.at(2) = HLT;
                    //probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    //probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    //probe_dxy_pt_HLT.at(5) = muon2_eta;

                    float muon1_muonBPark_matched_dR = muonBPark_matched_dR(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_matched_dr);
                    float muon2_muonBPark_matched_dR = muonBPark_matched_dR(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_matched_dr);

                    if(abs(muon1_muonBPark_matched_dR) > abs(muon2_muonBPark_matched_dR)){
                        bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                        probe_dxy_pt_HLT.at(0) = muon1_dxy;
                        probe_dxy_pt_HLT.at(1) = muon1_pt;
                        probe_dxy_pt_HLT.at(2) = HLT;
                        probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                        probe_dxy_pt_HLT.at(4) = abs(muon1_dxy)/muon1_dxyErr;
                        probe_dxy_pt_HLT.at(5) = muon1_eta;
                    }

                    else{
                        bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                        probe_dxy_pt_HLT.at(0) = muon2_dxy;
                        probe_dxy_pt_HLT.at(1) = muon2_pt;
                        probe_dxy_pt_HLT.at(2) = HLT;
                        probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                        probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                        probe_dxy_pt_HLT.at(5) = muon2_eta;
                    }

                }
                
                

                else if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)){
                    //std::cout<<"block 2"<<std::endl;
                    bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon2_eta;
                }
                else{ 
                    //std::cout<<"block 3"<<std::endl;
                    bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                    probe_dxy_pt_HLT.at(0) = muon1_dxy;
                    probe_dxy_pt_HLT.at(1) = muon1_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon1_dxy)/muon1_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon1_eta;
                }

                //if (probe_dxy_pt_HLT.at(4) > 20.0 && probe_dxy_pt_HLT.at(4) < 50.0 && probe_dxy_pt_HLT.at(1) > 16.0 && probe_dxy_pt_HLT.at(1) < 30.0 && abs(probe_dxy_pt_HLT.at(5)) < 0.4){
                    //std::cout << "Probe_muon_dxy = " << probe_dxy_pt_HLT.at(0) << std::endl;
                    //std::cout << "Probe_muon_pt = " << probe_dxy_pt_HLT.at(1) << std::endl;
                    //std::cout << "Probe_muon_HLT = " << probe_dxy_pt_HLT.at(2) << std::endl;
                    //std::cout << "Probe_muon_sip3d = " << probe_dxy_pt_HLT.at(3) << std::endl;
                    //std::cout << "Probe_muon_dxysig = " << probe_dxy_pt_HLT.at(4) << std::endl;
                    //std::cout << "Probe_muon_eta = " << probe_dxy_pt_HLT.at(5) << std::endl;
                //}  
                return probe_dxy_pt_HLT;
            }

        
        """)
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)
        #print("path = ", self.input()["data"][0].path)
        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)
        
        df = df.Filter("nmuonSV > 0")

        #df = df.Filter("nmuonSV == 1")
        #df = df.Filter("nMuon == 2")


        df = df.Define("muonSV_min_chi2_index", """
            get_muonsv_index(nmuonSV, muonSV_chi2, muonSV_z, PV_z, muonSV_mass, muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index, muonSV_charge)
        """).Filter("muonSV_min_chi2_index != -1")

        df = df.Define("muon1_index", "muonSV_mu1index.at(muonSV_min_chi2_index)")
        df = df.Define("muon2_index", "muonSV_mu2index.at(muonSV_min_chi2_index)")
        for var in ["dxy", "dxybs", "dxyErr", "pt", "sip3d", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"float var; var = Muon_{var}.at(muon1_index); return var;")
            df = df.Define(f"muon2_{var}", f"float var; var = Muon_{var}.at(muon2_index); return var;")

        for var in ["tightId", "mediumId", "looseId"]:
            df = df.Define(f"muon1_{var}", f"int var; var = Muon_{var}.at(muon1_index); return var;")
            df = df.Define(f"muon2_{var}", f"int var; var = Muon_{var}.at(muon2_index); return var;")


        df = df.Define("muonSV_mass_minchi2", "muonSV_mass.at(muonSV_min_chi2_index)")

        df = df.Define("muonSV_lxy_minchi2", "muonSV_dxy.at(muonSV_min_chi2_index)")
 
        
        #df.Snapshot("Events",  "test_0p01_new.root")
        

        #print("Finish defining muon qunatities")
        
        #for tag using HLT_Mu12_IP6
        
        #loose ID fpr tag, pre-selection for probe
        df = df.Filter("(muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_looseId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) && muon2_looseId == 1) || (muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_looseId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) && muon1_looseId == 1)")
        
        #tight ID for tag
        #df = df.Filter("muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) || muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)")
        
        #df.Snapshot("Events", "test_pass_0p01_new_after_pass.root")

        #tight ID for tag, medium ID for probe
        #df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_tightId, muon1_mediumId, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_tightId, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR, MuonBPark_matched_dr)")
        
        #loose ID for tag, loose ID for probe
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_looseId, muon1_looseId, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_looseId, muon2_looseId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR, MuonBPark_matched_dr)")

        df = df.Define("probe_dxy", "probe_quantities.at(0)").Define("probe_pt", "probe_quantities.at(1)").Define("probe_HLT", "probe_quantities.at(2)").Define("probe_sip3d", "probe_quantities.at(3)").Define("probe_dxysig", "probe_quantities.at(4)").Define("probe_eta", "probe_quantities.at(5)")

        df_pass = df.Filter("probe_HLT == 1")

        #df_pass.Snapshot("Events", "test_pass_0p01_new.root")
        '''
        dxy_bins = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        '''

        dxy_bins = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.004",
            "abs(probe_dxy) > 0.004 && abs(probe_dxy) < 0.007",
            "abs(probe_dxy) > 0.007 && abs(probe_dxy) < 0.008",
            "abs(probe_dxy) > 0.008 && abs(probe_dxy) < 0.009",
            "abs(probe_dxy) > 0.009 && abs(probe_dxy) < 0.01",
            "abs(probe_dxy) > 0.01 && abs(probe_dxy) < 0.02",
            "abs(probe_dxy) > 0.02 && abs(probe_dxy) < 0.03",
            "abs(probe_dxy) > 0.03 && abs(probe_dxy) < 0.04",
            "abs(probe_dxy) > 0.04 && abs(probe_dxy) < 0.07",
            "abs(probe_dxy) > 0.07 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.2",
            "abs(probe_dxy) > 0.2 && abs(probe_dxy) < 0.3",
            "abs(probe_dxy) > 0.3 && abs(probe_dxy) < 0.4",
            "abs(probe_dxy) > 0.4 && abs(probe_dxy) < 0.5",
            "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 0.6",
            "abs(probe_dxy) > 0.6 && abs(probe_dxy) < 0.7",
            "abs(probe_dxy) > 0.7 && abs(probe_dxy) < 0.8",
            "abs(probe_dxy) > 0.8 && abs(probe_dxy) < 0.9",
            "abs(probe_dxy) > 0.9 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        

        pt_bins = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]

        lxy_bins = [
             "muonSV_lxy_minchi2 > 0.01 && muonSV_lxy_minchi2 < 0.04",
             "muonSV_lxy_minchi2 > 0.04 && muonSV_lxy_minchi2 < 0.07",
             "muonSV_lxy_minchi2 > 0.07 && muonSV_lxy_minchi2 < 0.1",
             "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 0.3",
             "muonSV_lxy_minchi2 > 0.3 && muonSV_lxy_minchi2 < 0.5",
             "muonSV_lxy_minchi2 > 0.5 && muonSV_lxy_minchi2 < 0.7",
             "muonSV_lxy_minchi2 > 0.7 && muonSV_lxy_minchi2 < 1.0",
             "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 2.0",
             "muonSV_lxy_minchi2 > 2.0 && muonSV_lxy_minchi2 < 3.0",
             "muonSV_lxy_minchi2 > 3.0 && muonSV_lxy_minchi2 < 10.0",
             "muonSV_lxy_minchi2 > 10.0 && muonSV_lxy_minchi2 < 20.0",
             "muonSV_lxy_minchi2 > 20.0 && muonSV_lxy_minchi2 < 55.0",
             "muonSV_lxy_minchi2 > 55.0 && muonSV_lxy_minchi2 < 100.0"
        ]
        
        eta_bins_bparking = "abs(probe_eta) < 1.5"

        '''
        pt_bins = [
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]
        '''
        histos = {}

        df = df.Define("tag_probe_dR", "reco::deltaR(muon1_eta, muon1_phi, muon2_eta, muon2_phi)")

        

        for dxy_index, i in enumerate(dxy_bins):
            for pt_index, j in enumerate(pt_bins):
                h_dxy_pT_total = df.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_%s_total" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_dxy_pT_pass = df_pass.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
                h_dxy_pT_fail.SetName("h_dxy_%s_pT_%s_Fail"% (dxy_index, pt_index)) 

                histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] = h_dxy_pT_pass
                histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] = h_dxy_pT_fail
        
        for lxy_index, i in enumerate(lxy_bins):
            for pt_index, j in enumerate(pt_bins):
                h_lxy_pT_total = df.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_lxy_%s_pT_%s_total" % (lxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_lxy_pT_pass = df_pass.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_lxy_%s_pT_%s_Pass" % (lxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_lxy_pT_fail = h_lxy_pT_total.GetPtr() - h_lxy_pT_pass.GetPtr()
                h_lxy_pT_fail.SetName("h_lxy_%s_pT_%s_Fail"% (lxy_index, pt_index)) 

                histos["h_lxy_%s_pt_%s_Pass" % (lxy_index, pt_index)] = h_lxy_pT_pass
                histos["h_lxy_%s_pt_%s_Fail" % (lxy_index, pt_index)] = h_lxy_pT_fail
        
        dxysig_bins3 = [
            "probe_dxysig > 0.5 && probe_dxysig < 1.5",
            "probe_dxysig > 1.5 && probe_dxysig < 2.5",
            "probe_dxysig > 2.5 && probe_dxysig < 3.5",
            "probe_dxysig > 3.5 && probe_dxysig < 4.5",
            "probe_dxysig > 4.5 && probe_dxysig < 5.5",
            "probe_dxysig > 5.5 && probe_dxysig < 6.5",
            "probe_dxysig > 6.5 && probe_dxysig < 7.5",
            "probe_dxysig > 7.5 && probe_dxysig < 8.5",
            "probe_dxysig > 8.5 && probe_dxysig < 10.0",
            "probe_dxysig > 10.0 && probe_dxysig < 15.0",
            "probe_dxysig > 15.0 && probe_dxysig < 20.0",
            "probe_dxysig > 20.0 && probe_dxysig < 50.0"
        ]
        
        pt_bins3 = [
            "probe_pt > 8.0 && probe_pt < 9.0",
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 12.0",
            "probe_pt > 12.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 20.0",
            "probe_pt > 20.0 && probe_pt < 30.0"
        ]

        eta_bins3 = "abs(probe_eta) < 0.4"
        #eta_bins3 = "abs(probe_eta) > 0.4 && abs(probe_eta) < 0.8"
        #eta_bins3 = "abs(probe_eta) > 0.8 && abs(probe_eta) < 1.5"

        histos["tag_and_probe_dR"] = df.Filter(eta_bins3).Histo1D(("h_tag_and_probe_dR", "; dR; Events", 100, 0.0, 7.0), "tag_probe_dR")


        for dxy_index, i in enumerate(dxysig_bins3):
            for pt_index, j in enumerate(pt_bins3):
                h_dxysig_pT_total = df.Filter(i).Filter(j).Filter(eta_bins3).Histo1D(("h_dxysig_%s_pT_%s_total" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_dxysig_pT_pass = df_pass.Filter(i).Filter(j).Filter(eta_bins3).Histo1D(("h_dxysig_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_dxysig_pT_fail = h_dxysig_pT_total.GetPtr() - h_dxysig_pT_pass.GetPtr()
                h_dxysig_pT_fail.SetName("h_dxysig_%s_pT_%s_Fail"% (dxy_index, pt_index)) 

                histos["h_dxysig_%s_pt_%s_Pass" % (dxy_index, pt_index)] = h_dxysig_pT_pass
                histos["h_dxysig_%s_pt_%s_Fail" % (dxy_index, pt_index)] = h_dxysig_pT_fail
        
        
        #for 1D efficiency
        '''
        dxy_bins2 = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.5",
            "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        '''
        dxy_bins2 = [
             "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.004",
             "abs(probe_dxy) > 0.004 && abs(probe_dxy) < 0.007",
             "abs(probe_dxy) > 0.007 && abs(probe_dxy) < 0.008",
             "abs(probe_dxy) > 0.008 && abs(probe_dxy) < 0.009",
             "abs(probe_dxy) > 0.009 && abs(probe_dxy) < 0.01",
             "abs(probe_dxy) > 0.01 && abs(probe_dxy) < 0.02",
             "abs(probe_dxy) > 0.02 && abs(probe_dxy) < 0.03",
             "abs(probe_dxy) > 0.03 && abs(probe_dxy) < 0.04",
             "abs(probe_dxy) > 0.04 && abs(probe_dxy) < 0.07",
             "abs(probe_dxy) > 0.07 && abs(probe_dxy) < 0.1",
             "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.2",
             "abs(probe_dxy) > 0.2 && abs(probe_dxy) < 0.3",
             "abs(probe_dxy) > 0.3 && abs(probe_dxy) < 0.4",
             "abs(probe_dxy) > 0.4 && abs(probe_dxy) < 0.5",
             "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 0.6",
             "abs(probe_dxy) > 0.6 && abs(probe_dxy) < 0.7",
             "abs(probe_dxy) > 0.7 && abs(probe_dxy) < 0.8",
             "abs(probe_dxy) > 0.8 && abs(probe_dxy) < 0.9",
             "abs(probe_dxy) > 0.9 && abs(probe_dxy) < 1.0",
             "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        '''
        lxy_bins2 = [
             "muonSV_lxy_minchi2 > 0.01 && muonSV_lxy_minchi2 < 0.04",
             "muonSV_lxy_minchi2 > 0.04 && muonSV_lxy_minchi2 < 0.07",
             "muonSV_lxy_minchi2 > 0.07 && muonSV_lxy_minchi2 < 0.1",
             "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 0.3",
             "muonSV_lxy_minchi2 > 0.3 && muonSV_lxy_minchi2 < 0.5",
             "muonSV_lxy_minchi2 > 0.5 && muonSV_lxy_minchi2 < 0.7",
             "muonSV_lxy_minchi2 > 0.7 && muonSV_lxy_minchi2 < 1.0",
             "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 3.0",
             "muonSV_lxy_minchi2 > 3.0 && muonSV_lxy_minchi2 < 5.0",
             "muonSV_lxy_minchi2 > 5.0 && muonSV_lxy_minchi2 < 7.0",
             "muonSV_lxy_minchi2 > 7.0 && muonSV_lxy_minchi2 < 10.0",
             "muonSV_lxy_minchi2 > 10.0 && muonSV_lxy_minchi2 < 20.0",
             "muonSV_lxy_minchi2 > 20.0 && muonSV_lxy_minchi2 < 55.0",
             "muonSV_lxy_minchi2 > 55.0 && muonSV_lxy_minchi2 < 100.0"
        ]
        '''
        lxy_bins2 = [
             "muonSV_lxy_minchi2 > 0.01 && muonSV_lxy_minchi2 < 0.04",
             "muonSV_lxy_minchi2 > 0.04 && muonSV_lxy_minchi2 < 0.07",
             "muonSV_lxy_minchi2 > 0.07 && muonSV_lxy_minchi2 < 0.1",
             "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 0.3",
             "muonSV_lxy_minchi2 > 0.3 && muonSV_lxy_minchi2 < 0.5",
             "muonSV_lxy_minchi2 > 0.5 && muonSV_lxy_minchi2 < 0.7",
             "muonSV_lxy_minchi2 > 0.7 && muonSV_lxy_minchi2 < 1.0",
             "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 2.0",
             "muonSV_lxy_minchi2 > 2.0 && muonSV_lxy_minchi2 < 3.0",
             "muonSV_lxy_minchi2 > 3.0 && muonSV_lxy_minchi2 < 10.0",
             "muonSV_lxy_minchi2 > 10.0 && muonSV_lxy_minchi2 < 20.0",
             "muonSV_lxy_minchi2 > 20.0 && muonSV_lxy_minchi2 < 55.0",
             "muonSV_lxy_minchi2 > 55.0 && muonSV_lxy_minchi2 < 100.0"
        ]


        pt_bins2 = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 5.0",
            "probe_pt > 5.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 7.0",
            "probe_pt > 7.0 && probe_pt < 8.0",
            "probe_pt > 8.0 && probe_pt < 9.0",
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]

        IPsig_bins2 = [
            "probe_sip3d > 0.0 && probe_sip3d < 1.0",
            "probe_sip3d > 1.0 && probe_sip3d < 2.0",
            "probe_sip3d > 2.0 && probe_sip3d < 3.0",
            "probe_sip3d > 3.0 && probe_sip3d < 4.0",
            "probe_sip3d > 4.0 && probe_sip3d < 5.0",
            "probe_sip3d > 5.0 && probe_sip3d < 6.0",
            "probe_sip3d > 6.0 && probe_sip3d < 7.0",
            "probe_sip3d > 7.0 && probe_sip3d < 15.0",
            "probe_sip3d > 15.0 && probe_sip3d < 30.0"
        ]       

        for dxy_index, i in enumerate(dxy_bins2):
            h_dxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Histo1D(("h_dxy_%s_pT_100_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Histo1D(("h_dxy_%s_pT_100_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_100_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_100_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_100_Fail" % (dxy_index)] = h_dxy_pT_fail

        for lxy_index, i in enumerate(lxy_bins2):
            h_lxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Histo1D(("h_lxy_%s_pT_100_total" % (lxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_lxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Histo1D(("h_lxy_%s_pT_100_Pass" % (lxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_lxy_pT_fail = h_lxy_pT_total.GetPtr() - h_lxy_pT_pass.GetPtr()
            h_lxy_pT_fail.SetName("h_lxy_%s_pT_100_Fail"% (lxy_index)) 

            histos["h_lxy_%s_pt_100_Pass" % (lxy_index)] = h_lxy_pT_pass
            histos["h_lxy_%s_pt_100_Fail" % (lxy_index)] = h_lxy_pT_fail

        for pt_index, i in enumerate(pt_bins2):
            h_dxy_pT_total = df.Filter(i).Filter("probe_dxysig > 8.0").Filter(eta_bins_bparking).Histo1D(("h_dxy_100_pT_%s_total" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter("probe_dxysig > 8.0").Filter(eta_bins_bparking).Histo1D(("h_dxy_100_pT_%s_Pass" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_100_pT_%s_Fail"% (pt_index)) 

            histos["h_dxy_100_pt_%s_Pass" % (pt_index)] = h_dxy_pT_pass
            histos["h_dxy_100_pt_%s_Fail" % (pt_index)] = h_dxy_pT_fail

        for dxy_index, i in enumerate(IPsig_bins2):
            h_dxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_1000_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_1000_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_1000_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_1000_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_1000_Fail" % (dxy_index)] = h_dxy_pT_fail

        for dxy_index, i in enumerate(dxysig_bins3):
            h_dxy_pT_total = df.Filter(i).Filter("probe_pt > 10.0").Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_2000_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter("probe_pt > 10.0").Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_2000_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_2000_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_2000_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_2000_Fail" % (dxy_index)] = h_dxy_pT_fail

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()

class TriggerSFtnpRknewsignal(TriggerSF):
    def add_to_root(self, root):
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"
            #include <cmath>

            static double igf(double S, double Z)
            {
                if(Z < 0.0)
                {
	            return 0.0;
                }
                double Sc = (1.0 / S);
                Sc *= pow(Z, S);
                Sc *= exp(-Z);
 
                double Sum = 1.0;
                double Nom = 1.0;
                double Denom = 1.0;
 
                for(int I = 0; I < 200; I++)
                {
	            Nom *= Z;
	            S++;
	            Denom *= S;
	            Sum += (Nom / Denom);
                }
 
                return Sum * Sc;
            }

            double chisqr(int Dof, double Cv)
            {
                if(Cv < 0 || Dof < 1)
                {
                    return 0.0;
                }
                double K = ((double)Dof) * 0.5;
                double X = Cv * 0.5;
                if(Dof == 2)
                {
	            return exp(-1.0 * X);
                }
 
                double PValue = igf(K, X);
                if(std::isnan(PValue) || std::isinf(PValue) || PValue <= 1e-8)
                {
                    return 1e-14;
                } 

                PValue /= tgamma(K); 
            	
                return (1.0 - PValue);
            }

            bool chi2sort (const std::pair<int, float>& a, const std::pair<int, float>& b)
            {
              return (a.second < b.second);
            }

            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;

            //int get_muonsv_index(int nmuonSV, Vfloat muonSV_chi2, Vfloat muonSV_z, float PV_z, Vfloat muonSV_mass, Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi, Vint muonSV_mu1index, Vint muonSV_mu2index, Vint muonSV_charge)
            int get_muonsv_index(int nmuonSV, Vfloat muonSV_chi2, Vfloat muonSV_z, float PV_z, Vfloat muonSV_mass, Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi, Vint muonSV_mu1index, Vint muonSV_mu2index)
            {
                //std::cout << "call get_muonsv_index function" << std::endl;
                std::vector<std::pair<int, float>> index_chi2;
                for (int i = 0; i < nmuonSV; i++) {
                    //if (chisqr(1, muonSV_chi2[i]) < 0.01 || abs(muonSV_z[i] - PV_z) > 0.5 || reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) < 0.15 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3 || muonSV_charge[i] != 0) continue;
                    //if (chisqr(1, muonSV_chi2[i]) < 0.01 || reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) < 0.15 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3 || muonSV_charge[i] != 0) continue;
                    if (chisqr(1, muonSV_chi2[i]) < 0.01 || reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) < 0.15) continue;

                    int index1 = muonSV_mu1index[i];
                    int index2 = muonSV_mu2index[i];
                    index_chi2.push_back(std::make_pair(i, muonSV_chi2[i]));
                }
                //std::cout << "index_chi2.size = " << index_chi2.size() << std::endl;
                if (index_chi2.size() > 0) {
                    //std::cout << "before sort" << std::endl;
                    std::stable_sort(index_chi2.begin(), index_chi2.end(), chi2sort);
                    //std::cout << "after sort" << std::endl;
                    //std::cout << "index = " << index_chi2[0].first << std::endl;
                    return index_chi2[0].first;
                } else {
                    return -1;
                }
            }

            
            //bool muon_pass(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_tightId, int nMuonBPark, Vfloat MuonBPark_eta,
                //Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt, Vfloat TrigObjBPark_l1dR)
            bool muon_pass(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_tightId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt)
            {
                
                //std::cout << "call muon_pass function" << std::endl;
                
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    //std::cout << "pass trigger" << std::endl; 
                    //std::cout<< "i = " << i << " " << reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) << " " << muon_pt << abs(muon_dxy)/muon_dxyErr << muon_tightId << std::endl;   
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.1 && muon_pt > 10.0 && abs(muon_dxy)/muon_dxyErr > 8.0 && muon_tightId == 1){
                        //std::cout << "before TrigObjBPark check" << std::endl;
                        //return true;
                        
                        for (int j = 0; j < nTrigObjBPark; j++) {
                            //std::cout<< "j = " << j << " " << reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) << " " << TrigObjBPark_l1pt[j] << " " << TrigObjBPark_l1dR[j] << std::endl;
                            //if (reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) < 0.05 && TrigObjBPark_l1pt[j] > 10.0 && TrigObjBPark_l1dR[j] < 0.05){
                            if (reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) < 0.05 && TrigObjBPark_l1pt[j] > 10.0){
                                //std::cout << "muon pass!" << std::endl;
                                return true;
                            }
                        }
                        
                    }
                }
                //std::cout << "don't pass trigger" << std::endl;
                

                return false;
            }

            float muonBPark_matched_dR(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, Vfloat MuonBPark_matched_dr)
            {
                float dR = 999999;
                int index = -1;
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < dR){
                        dR = reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]);
                        index = i;
                    }
                }

                if (index != -1) 
                    return MuonBPark_matched_dr.at(index);
                else 
                    return -999.0;

            }    
            


            bool muon_pass_probe(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_mediumId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    //std::cout<< i << " "<< MuonBPark_fired_HLT_Mu9_IP6[i] << " " << reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) << std::endl;
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.1 && muon_mediumId == 1){  
                        for (int j = 0; j < nTrigObjBPark; j++) {
                            if (reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) < 0.2)
                                return true;
                        }
                    }
                }
                return false;
            }

            bool muon_pass_tag(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)
                        return true;
                }
                return false;
            }

            ROOT::RVec<float> probe_values(float muon1_eta, float muon1_phi, float muon1_dxy, float muon1_dxyErr, float muon1_pt, float muon1_sip3d, int muon1_tightId, int muon1_mediumId,
                float muon2_eta, float muon2_phi, float muon2_dxy, float muon2_dxyErr, float muon2_pt, float muon2_sip3d, int muon2_tightId, int muon2_mediumId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt, Vfloat MuonBPark_matched_dr) 
            {
                //std::cout << "call probe_values function" << std::endl;
                ROOT::RVec<float> probe_dxy_pt_HLT(6);

                if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt) && muon_pass(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt)){
                    //std::cout<<"block 1"<<std::endl;

                    //if both muons are matched to the HLT_Mu9_IP6 trigger muon, choose the muon with highest pT (muon1) as the tag
                    //bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                    //probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    //probe_dxy_pt_HLT.at(1) = muon2_pt;
                    //probe_dxy_pt_HLT.at(2) = HLT;
                    //probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    //probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    //probe_dxy_pt_HLT.at(5) = muon2_eta;

                    float muon1_muonBPark_matched_dR = muonBPark_matched_dR(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_matched_dr);
                    float muon2_muonBPark_matched_dR = muonBPark_matched_dR(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_matched_dr);

                    if(abs(muon1_muonBPark_matched_dR) > abs(muon2_muonBPark_matched_dR)){
                        bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                        probe_dxy_pt_HLT.at(0) = muon1_dxy;
                        probe_dxy_pt_HLT.at(1) = muon1_pt;
                        probe_dxy_pt_HLT.at(2) = HLT;
                        probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                        probe_dxy_pt_HLT.at(4) = abs(muon1_dxy)/muon1_dxyErr;
                        probe_dxy_pt_HLT.at(5) = muon1_eta;
                    }

                    else{
                        bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                        probe_dxy_pt_HLT.at(0) = muon2_dxy;
                        probe_dxy_pt_HLT.at(1) = muon2_pt;
                        probe_dxy_pt_HLT.at(2) = HLT;
                        probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                        probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                        probe_dxy_pt_HLT.at(5) = muon2_eta;
                    }

                }
                
                

                else if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt)){
                    //std::cout<<"block 2"<<std::endl;
                    bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon2_eta;
                }
                else{ 
                    //std::cout<<"block 3"<<std::endl;
                    bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                    probe_dxy_pt_HLT.at(0) = muon1_dxy;
                    probe_dxy_pt_HLT.at(1) = muon1_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon1_dxy)/muon1_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon1_eta;
                }

                //if (probe_dxy_pt_HLT.at(4) > 20.0 && probe_dxy_pt_HLT.at(4) < 50.0 && probe_dxy_pt_HLT.at(1) > 16.0 && probe_dxy_pt_HLT.at(1) < 30.0 && abs(probe_dxy_pt_HLT.at(5)) < 0.4){
                    //std::cout << "Probe_muon_dxy = " << probe_dxy_pt_HLT.at(0) << std::endl;
                    //std::cout << "Probe_muon_pt = " << probe_dxy_pt_HLT.at(1) << std::endl;
                    //std::cout << "Probe_muon_HLT = " << probe_dxy_pt_HLT.at(2) << std::endl;
                    //std::cout << "Probe_muon_sip3d = " << probe_dxy_pt_HLT.at(3) << std::endl;
                    //std::cout << "Probe_muon_dxysig = " << probe_dxy_pt_HLT.at(4) << std::endl;
                    //std::cout << "Probe_muon_eta = " << probe_dxy_pt_HLT.at(5) << std::endl;
                //}  
                return probe_dxy_pt_HLT;
            }

        
        """)
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)
        #print("path = ", self.input()["data"][0].path)
        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)
        
        df = df.Filter("nmuonSV > 0")

        #df = df.Filter("nmuonSV == 1")
        #df = df.Filter("nMuon == 2")


        df = df.Define("muonSV_min_chi2_index", """
            get_muonsv_index(nmuonSV, muonSV_chi2, muonSV_z, PV_z, muonSV_mass, muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index)
        """).Filter("muonSV_min_chi2_index != -1")

        df = df.Define("muon1_index", "muonSV_mu1index.at(muonSV_min_chi2_index)")
        df = df.Define("muon2_index", "muonSV_mu2index.at(muonSV_min_chi2_index)")
        for var in ["dxy", "dxybs", "dxyErr", "pt", "sip3d", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"float var; var = Muon_{var}.at(muon1_index); return var;")
            df = df.Define(f"muon2_{var}", f"float var; var = Muon_{var}.at(muon2_index); return var;")

        for var in ["tightId", "mediumId", "looseId"]:
            df = df.Define(f"muon1_{var}", f"int var; var = Muon_{var}.at(muon1_index); return var;")
            df = df.Define(f"muon2_{var}", f"int var; var = Muon_{var}.at(muon2_index); return var;")


        df = df.Define("muonSV_mass_minchi2", "muonSV_mass.at(muonSV_min_chi2_index)")

        df = df.Define("muonSV_lxy_minchi2", "muonSV_dxy.at(muonSV_min_chi2_index)")
 
        
        #df.Snapshot("Events",  "test_0p01_new.root")
        

        #print("Finish defining muon qunatities")
        
        #for tag using HLT_Mu12_IP6
        
        #loose ID fpr tag, pre-selection for probe
        df = df.Filter("(muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_looseId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt) && muon2_looseId == 1) || (muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_looseId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt) && muon1_looseId == 1)")
        
        #tight ID for tag
        #df = df.Filter("muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) || muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)")
        
        #df.Snapshot("Events", "test_pass_0p01_new_after_pass.root")

        #tight ID for tag, medium ID for probe
        #df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_tightId, muon1_mediumId, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_tightId, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR, MuonBPark_matched_dr)")
        
        #loose ID for tag, loose ID for probe
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_looseId, muon1_looseId, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_looseId, muon2_looseId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, MuonBPark_matched_dr)")

        df = df.Define("probe_dxy", "probe_quantities.at(0)").Define("probe_pt", "probe_quantities.at(1)").Define("probe_HLT", "probe_quantities.at(2)").Define("probe_sip3d", "probe_quantities.at(3)").Define("probe_dxysig", "probe_quantities.at(4)").Define("probe_eta", "probe_quantities.at(5)")

        df_pass = df.Filter("probe_HLT == 1")

        #df_pass.Snapshot("Events", "test_pass_0p01_new.root")
        '''
        dxy_bins = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        '''

        dxy_bins = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.004",
            "abs(probe_dxy) > 0.004 && abs(probe_dxy) < 0.007",
            "abs(probe_dxy) > 0.007 && abs(probe_dxy) < 0.008",
            "abs(probe_dxy) > 0.008 && abs(probe_dxy) < 0.009",
            "abs(probe_dxy) > 0.009 && abs(probe_dxy) < 0.01",
            "abs(probe_dxy) > 0.01 && abs(probe_dxy) < 0.02",
            "abs(probe_dxy) > 0.02 && abs(probe_dxy) < 0.03",
            "abs(probe_dxy) > 0.03 && abs(probe_dxy) < 0.04",
            "abs(probe_dxy) > 0.04 && abs(probe_dxy) < 0.07",
            "abs(probe_dxy) > 0.07 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.2",
            "abs(probe_dxy) > 0.2 && abs(probe_dxy) < 0.3",
            "abs(probe_dxy) > 0.3 && abs(probe_dxy) < 0.4",
            "abs(probe_dxy) > 0.4 && abs(probe_dxy) < 0.5",
            "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 0.6",
            "abs(probe_dxy) > 0.6 && abs(probe_dxy) < 0.7",
            "abs(probe_dxy) > 0.7 && abs(probe_dxy) < 0.8",
            "abs(probe_dxy) > 0.8 && abs(probe_dxy) < 0.9",
            "abs(probe_dxy) > 0.9 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        

        pt_bins = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]

        lxy_bins = [
             "muonSV_lxy_minchi2 > 0.01 && muonSV_lxy_minchi2 < 0.04",
             "muonSV_lxy_minchi2 > 0.04 && muonSV_lxy_minchi2 < 0.07",
             "muonSV_lxy_minchi2 > 0.07 && muonSV_lxy_minchi2 < 0.1",
             "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 0.3",
             "muonSV_lxy_minchi2 > 0.3 && muonSV_lxy_minchi2 < 0.5",
             "muonSV_lxy_minchi2 > 0.5 && muonSV_lxy_minchi2 < 0.7",
             "muonSV_lxy_minchi2 > 0.7 && muonSV_lxy_minchi2 < 1.0",
             "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 2.0",
             "muonSV_lxy_minchi2 > 2.0 && muonSV_lxy_minchi2 < 3.0",
             "muonSV_lxy_minchi2 > 3.0 && muonSV_lxy_minchi2 < 10.0",
             "muonSV_lxy_minchi2 > 10.0 && muonSV_lxy_minchi2 < 20.0",
             "muonSV_lxy_minchi2 > 20.0 && muonSV_lxy_minchi2 < 55.0",
             "muonSV_lxy_minchi2 > 55.0 && muonSV_lxy_minchi2 < 100.0"
        ]
        
        eta_bins_bparking = "abs(probe_eta) < 1.5"

        '''
        pt_bins = [
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]
        '''
        histos = {}

        df = df.Define("tag_probe_dR", "reco::deltaR(muon1_eta, muon1_phi, muon2_eta, muon2_phi)")

        

        for dxy_index, i in enumerate(dxy_bins):
            for pt_index, j in enumerate(pt_bins):
                h_dxy_pT_total_size = df.Filter(i).Filter(j).Filter(eta_bins_bparking).Count().GetValue()
                h_dxy_pT_pass_size = df_pass.Filter(i).Filter(j).Filter(eta_bins_bparking).Count().GetValue()
                
                h_dxy_pT_fail_size = h_dxy_pT_total_size - h_dxy_pT_pass_size

                h_dxy_pT_Pass = ROOT.TH1D("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index), " ;;Events", 1, 0, 1)
                h_dxy_pT_Fail = ROOT.TH1D("h_dxy_%s_pT_%s_Fail" % (dxy_index, pt_index), " ;;Events", 1, 0, 1)

                for j in range(h_dxy_pT_pass_size):
                    h_dxy_pT_Pass.Fill(0.0)
                for k in range(h_dxy_pT_fail_size):
                    h_dxy_pT_Fail.Fill(0.0)

                histos["h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index)] = h_dxy_pT_Pass
                histos["h_dxy_%s_pT_%s_Fail" % (dxy_index, pt_index)] = h_dxy_pT_Fail
        
        
        #for 1D efficiency
        '''
        dxy_bins2 = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.5",
            "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        '''
        dxy_bins2 = [
             "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.004",
             "abs(probe_dxy) > 0.004 && abs(probe_dxy) < 0.007",
             "abs(probe_dxy) > 0.007 && abs(probe_dxy) < 0.008",
             "abs(probe_dxy) > 0.008 && abs(probe_dxy) < 0.009",
             "abs(probe_dxy) > 0.009 && abs(probe_dxy) < 0.01",
             "abs(probe_dxy) > 0.01 && abs(probe_dxy) < 0.02",
             "abs(probe_dxy) > 0.02 && abs(probe_dxy) < 0.03",
             "abs(probe_dxy) > 0.03 && abs(probe_dxy) < 0.04",
             "abs(probe_dxy) > 0.04 && abs(probe_dxy) < 0.07",
             "abs(probe_dxy) > 0.07 && abs(probe_dxy) < 0.1",
             "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.2",
             "abs(probe_dxy) > 0.2 && abs(probe_dxy) < 0.3",
             "abs(probe_dxy) > 0.3 && abs(probe_dxy) < 0.4",
             "abs(probe_dxy) > 0.4 && abs(probe_dxy) < 0.5",
             "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 0.6",
             "abs(probe_dxy) > 0.6 && abs(probe_dxy) < 0.7",
             "abs(probe_dxy) > 0.7 && abs(probe_dxy) < 0.8",
             "abs(probe_dxy) > 0.8 && abs(probe_dxy) < 0.9",
             "abs(probe_dxy) > 0.9 && abs(probe_dxy) < 1.0",
             "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
     
        lxy_bins2 = [
             "muonSV_lxy_minchi2 > 0.01 && muonSV_lxy_minchi2 < 0.04",
             "muonSV_lxy_minchi2 > 0.04 && muonSV_lxy_minchi2 < 0.07",
             "muonSV_lxy_minchi2 > 0.07 && muonSV_lxy_minchi2 < 0.1",
             "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 0.3",
             "muonSV_lxy_minchi2 > 0.3 && muonSV_lxy_minchi2 < 0.5",
             "muonSV_lxy_minchi2 > 0.5 && muonSV_lxy_minchi2 < 0.7",
             "muonSV_lxy_minchi2 > 0.7 && muonSV_lxy_minchi2 < 1.0",
             "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 2.0",
             "muonSV_lxy_minchi2 > 2.0 && muonSV_lxy_minchi2 < 3.0",
             "muonSV_lxy_minchi2 > 3.0 && muonSV_lxy_minchi2 < 10.0",
             "muonSV_lxy_minchi2 > 10.0 && muonSV_lxy_minchi2 < 20.0",
             "muonSV_lxy_minchi2 > 20.0 && muonSV_lxy_minchi2 < 55.0",
             "muonSV_lxy_minchi2 > 55.0 && muonSV_lxy_minchi2 < 100.0"
        ]


        pt_bins2 = [
            "probe_pt > 0.0 && probe_pt < 1.0",
            "probe_pt > 1.0 && probe_pt < 2.0",
            "probe_pt > 2.0 && probe_pt < 3.0",
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 5.0",
            "probe_pt > 5.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 7.0",
            "probe_pt > 7.0 && probe_pt < 8.0",
            "probe_pt > 8.0 && probe_pt < 9.0",
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]

        IPsig_bins2 = [
            "probe_sip3d > 0.0 && probe_sip3d < 1.0",
            "probe_sip3d > 1.0 && probe_sip3d < 2.0",
            "probe_sip3d > 2.0 && probe_sip3d < 3.0",
            "probe_sip3d > 3.0 && probe_sip3d < 4.0",
            "probe_sip3d > 4.0 && probe_sip3d < 5.0",
            "probe_sip3d > 5.0 && probe_sip3d < 6.0",
            "probe_sip3d > 6.0 && probe_sip3d < 7.0",
            "probe_sip3d > 7.0 && probe_sip3d < 15.0",
            "probe_sip3d > 15.0 && probe_sip3d < 30.0"
        ]       

        dxysig_bins2 = [
            "probe_dxysig > 0.5 && probe_dxysig < 1.5",
            "probe_dxysig > 1.5 && probe_dxysig < 2.5",
            "probe_dxysig > 2.5 && probe_dxysig < 3.5",
            "probe_dxysig > 3.5 && probe_dxysig < 4.5",
            "probe_dxysig > 4.5 && probe_dxysig < 5.5",
            "probe_dxysig > 5.5 && probe_dxysig < 6.5",
            "probe_dxysig > 6.5 && probe_dxysig < 7.5",
            "probe_dxysig > 7.5 && probe_dxysig < 8.5",
            "probe_dxysig > 8.5 && probe_dxysig < 10.0",
            "probe_dxysig > 10.0 && probe_dxysig < 15.0",
            "probe_dxysig > 15.0 && probe_dxysig < 20.0",
            "probe_dxysig > 20.0 && probe_dxysig < 50.0"
        ]

        for dxy_index, i in enumerate(dxy_bins2):
            h_dxy_pT_total_size = df.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Count().GetValue()
            h_dxy_pT_pass_size = df_pass.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Count().GetValue()
                
            h_dxy_pT_fail_size = h_dxy_pT_total_size - h_dxy_pT_pass_size
            h_dxy_pT_Pass = ROOT.TH1D("h_dxy_%s_pT_100_Pass" % (dxy_index), " ;;Events", 1, 0, 1)
            h_dxy_pT_Fail = ROOT.TH1D("h_dxy_%s_pT_100_Fail" % (dxy_index), " ;;Events", 1, 0, 1)

            for j in range(h_dxy_pT_pass_size):
                h_dxy_pT_Pass.Fill(0.0)
            for k in range(h_dxy_pT_fail_size):
                h_dxy_pT_Fail.Fill(0.0)

            histos["h_dxy_%s_pt_100_Pass" % (dxy_index)] = h_dxy_pT_Pass
            histos["h_dxy_%s_pt_100_Fail" % (dxy_index)] = h_dxy_pT_Fail

        for lxy_index, i in enumerate(lxy_bins2):
            h_lxy_pT_total_size = df.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Count().GetValue()
            h_lxy_pT_pass_size = df_pass.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Count().GetValue()
                
            h_lxy_pT_fail_size = h_lxy_pT_total_size - h_lxy_pT_pass_size
            h_lxy_pT_Pass = ROOT.TH1D("h_lxy_%s_pT_100_Pass" % (lxy_index), " ;;Events", 1, 0, 1)
            h_lxy_pT_Fail = ROOT.TH1D("h_lxy_%s_pT_100_Fail" % (lxy_index), " ;;Events", 1, 0, 1)

            for j in range(h_lxy_pT_pass_size):
                h_lxy_pT_Pass.Fill(0.0)
            for k in range(h_lxy_pT_fail_size):
                h_lxy_pT_Fail.Fill(0.0)
            
            histos["h_lxy_%s_pt_100_Pass" % (lxy_index)] = h_lxy_pT_Pass
            histos["h_lxy_%s_pt_100_Fail" % (lxy_index)] = h_lxy_pT_Fail

        for pt_index, i in enumerate(pt_bins2):
            h_dxy_pT_total_size = df.Filter(i).Filter("probe_dxysig > 8.0").Filter(eta_bins_bparking).Count().GetValue()
            h_dxy_pT_pass_size = df_pass.Filter(i).Filter("probe_dxysig > 8.0").Filter(eta_bins_bparking).Count().GetValue()
            #h_dxy_pT_total_size = df.Filter(i).Filter(eta_bins_bparking).Count().GetValue()
            #h_dxy_pT_pass_size = df_pass.Filter(i).Filter(eta_bins_bparking).Count().GetValue()
                
            h_dxy_pT_fail_size = h_dxy_pT_total_size - h_dxy_pT_pass_size
            h_dxy_pT_Pass = ROOT.TH1D("h_dxy_100_pT_%s_Pass" % (pt_index), " ;;Events", 1, 0, 1)
            h_dxy_pT_Fail = ROOT.TH1D("h_dxy_100_pT_%s_Fail" % (pt_index), " ;;Events", 1, 0, 1)

            for j in range(h_dxy_pT_pass_size):
                h_dxy_pT_Pass.Fill(0.0)
            for k in range(h_dxy_pT_fail_size):
                h_dxy_pT_Fail.Fill(0.0)

            histos["h_dxy_100_pt_%s_Pass" % (pt_index)] = h_dxy_pT_Pass
            histos["h_dxy_100_pt_%s_Fail" % (pt_index)] = h_dxy_pT_Fail

        for dxy_index, i in enumerate(IPsig_bins2):
            h_dxy_pT_total_size = df.Filter(i).Filter(eta_bins_bparking).Count().GetValue()
            h_dxy_pT_pass_size = df_pass.Filter(i).Filter(eta_bins_bparking).Count().GetValue()
                
            h_dxy_pT_fail_size = h_dxy_pT_total_size - h_dxy_pT_pass_size
            h_dxy_pT_Pass = ROOT.TH1D("h_dxy_%s_pT_1000_Pass" % (dxy_index), " ;;Events", 1, 0, 1)
            h_dxy_pT_Fail = ROOT.TH1D("h_dxy_%s_pT_1000_Fail" % (dxy_index), " ;;Events", 1, 0, 1)

            for j in range(h_dxy_pT_pass_size):
                h_dxy_pT_Pass.Fill(0.0)
            for k in range(h_dxy_pT_fail_size):
                h_dxy_pT_Fail.Fill(0.0)

            histos["h_dxy_%s_pt_1000_Pass" % (dxy_index)] = h_dxy_pT_Pass
            histos["h_dxy_%s_pt_1000_Fail" % (dxy_index)] = h_dxy_pT_Fail

        for dxy_index, i in enumerate(dxysig_bins2):
            h_dxy_pT_total_size = df.Filter(i).Filter("probe_pt > 10.0").Filter(eta_bins_bparking).Count().GetValue()
            h_dxy_pT_pass_size = df_pass.Filter(i).Filter("probe_pt > 10.0").Filter(eta_bins_bparking).Count().GetValue()

            #h_dxy_pT_total_size = df.Filter(i).Filter(eta_bins_bparking).Count().GetValue()
            #h_dxy_pT_pass_size = df_pass.Filter(i).Filter(eta_bins_bparking).Count().GetValue()
                
            h_dxy_pT_fail_size = h_dxy_pT_total_size - h_dxy_pT_pass_size
            h_dxy_pT_Pass = ROOT.TH1D("h_dxy_%s_pT_2000_Pass" % (dxy_index), " ;;Events", 1, 0, 1)
            h_dxy_pT_Fail = ROOT.TH1D("h_dxy_%s_pT_2000_Fail" % (dxy_index), " ;;Events", 1, 0, 1)

            for j in range(h_dxy_pT_pass_size):
                h_dxy_pT_Pass.Fill(0.0)
            for k in range(h_dxy_pT_fail_size):
                h_dxy_pT_Fail.Fill(0.0)

            histos["h_dxy_%s_pt_2000_Pass" % (dxy_index)] = h_dxy_pT_Pass
            histos["h_dxy_%s_pt_2000_Fail" % (dxy_index)] = h_dxy_pT_Fail

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()

class dzcheck(TriggerSF):
    def add_to_root(self, root):
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"
            #include <cmath>
            
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;

            ROOT::RVec<float> muon_dz_values(int nMuonBPark, Vfloat MuonBPark_eta, Vfloat MuonBPark_phi, Vfloat MuonBPark_vz, 
            int nTriggerMuon, Vfloat TriggerMuon_eta, Vfloat TriggerMuon_phi, Vfloat TriggerMuon_vz)
            {   
                ROOT::RVec<float> dz_final(nMuonBPark);

                for (int i = 0; i < nMuonBPark; i++) {
                    std::vector<float> dz;
                    std::vector<float> dR;
                    dz.clear();
                    dR.clear();
                    for (int j = 0; j < nTriggerMuon; j++){
                        if (reco::deltaR(MuonBPark_eta[i], MuonBPark_phi[i], TriggerMuon_eta[j], TriggerMuon_phi[j]) < 0.3){
                            dR.push_back(reco::deltaR(MuonBPark_eta[i], MuonBPark_phi[i], TriggerMuon_eta[j], TriggerMuon_phi[j]));
                            dz.push_back(fabs(MuonBPark_vz[i] - TriggerMuon_vz[j]));
                            }
                        }
                    if(dR.size() > 0){
                        auto result = std::min_element(dR.begin(), dR.end()); 
                        int min_dR_index = std::distance(dR.begin(), result);
                        dz_final.push_back(dz[min_dR_index]);
                    }
                    if(dR.size() == 0){
                        dz_final.push_back(-1.0);
                    }    
                }
                
                std::cout << "dz_final = " << dz_final << std::endl;

                return dz_final;
    
            }

            ROOT::RVec<float> muon_dz_values_new(int nMuonBPark, Vfloat MuonBPark_eta, Vfloat MuonBPark_phi, Vfloat MuonBPark_vz, 
            int nTriggerMuon, Vfloat TriggerMuon_eta, Vfloat TriggerMuon_phi, Vfloat TriggerMuon_vz)
            {   
                ROOT::RVec<float> dz_final(nMuonBPark*nTriggerMuon);

                for (int i = 0; i < nMuonBPark; i++) {
                    std::vector<float> dz;
                    dz.clear();
                    for (int j = 0; j < nTriggerMuon; j++){
                        dz.push_back(fabs(MuonBPark_vz[i] - TriggerMuon_vz[j]));
                        dz_final.push_back(fabs(MuonBPark_vz[i] - TriggerMuon_vz[j]));
                        }
                    
                        
                }

                return dz_final;
    
            }




            """)

    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)
        #print("path = ", self.input()["data"][0].path)
        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)

        df = df.Filter("nMuonBPark > 0").Filter("nTriggerMuon > 0")
        df = df.Define("dz_values", "muon_dz_values_new(nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_vz, nTriggerMuon, TriggerMuon_eta, TriggerMuon_phi, TriggerMuon_vz)")
        h_dz = df.Histo1D(("dz_histo", ";dz between muon BPark and trg muon (cm); Number of muons", 100, 0.0, 5.0), "dz_values")

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        h_dz.Write()
        histo_file.Close()

 
 
class overalleff(TriggerSF):
    def add_to_root(self, root):
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"
            #include <cmath>
            #include <algorithm>
            
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;

            bool chi2sort (const std::pair<int, float>& a, const std::pair<int, float>& b)
            {
              return (a.second < b.second);
            }

            int get_muonsv_index(int nmuonSV, Vfloat muonSV_chi2, Vint muonSV_mu1index, Vint muonSV_mu2index)
            {
                //std::cout << "call get_muonsv_index function" << std::endl;
                std::vector<std::pair<int, float>> index_chi2;
                for (int i = 0; i < nmuonSV; i++) {

                    int index1 = muonSV_mu1index[i];
                    int index2 = muonSV_mu2index[i];
                    index_chi2.push_back(std::make_pair(i, muonSV_chi2[i]));
                }
                //std::cout << "index_chi2.size = " << index_chi2.size() << std::endl;
                if (index_chi2.size() > 0) {
                    //std::cout << "before sort" << std::endl;
                    std::stable_sort(index_chi2.begin(), index_chi2.end(), chi2sort);
                    //std::cout << "after sort" << std::endl;
                    //std::cout << "index = " << index_chi2[0].first << std::endl;
                    return index_chi2[0].first;
                } else {
                    return -1;
                }
            }

            bool muon_pass_probe(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    //std::cout<< i << " "<< MuonBPark_fired_HLT_Mu9_IP6[i] << " " << reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) << std::endl;
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.1){  
                        return true;
                    }
                }
                return false;
            }


            ROOT::RVec<float>  gen_lxy_pT(Vfloat Muon_eta, Vfloat Muon_phi, int nMuonBPark, Vfloat MuonBPark_eta, Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, 
            int muonSV_index, int nMuon, int nGenPart, Vint muonSV_mu1index, Vint muonSV_mu2index, Vint Muon_genPartIdx, Vfloat GenPart_vertex_x, Vfloat GenPart_vertex_y, 
            Vfloat GenPart_vertex_z, Vint GenPart_pdgId, Vint Muon_charge, Vfloat GenPart_pt, Vfloat GenPart_eta, Vfloat GenPart_phi) 
            {
                int mu1_idx = muonSV_mu1index[muonSV_index];
                int mu2_idx = muonSV_mu2index[muonSV_index];

                float mu1_eta = Muon_eta[mu1_idx];
                float mu1_phi = Muon_phi[mu1_idx];
                float mu2_eta = Muon_eta[mu2_idx];
                float mu2_phi = Muon_phi[mu2_idx];

                int nmuon = nMuon;
                //cout << "Event " << i << endl;
                //cout << "mu1_idx = " << mu1_idx << endl;
                //cout << "mu2_idx = " << mu2_idx << endl;
                //cout << "nMuon = " << nmuon << endl;

                //if(abs(mu1_idx) > nmuon - 1 || abs(mu2_idx) > nmuon - 1) return -1.0;
 
                int mu1_genpartidx = Muon_genPartIdx[mu1_idx];
                int mu2_genpartidx = Muon_genPartIdx[mu2_idx];

                int ngenpart = nGenPart;
                //cout << "mu1_genpartidx = " << mu1_genpartidx << endl;
                //cout << "mu2_genpartidx = " << mu2_genpartidx << endl;
                //cout << "ngenpart = " << ngenpart << endl;

                //if(abs(mu1_genpartidx) > ngenpart - 1 || abs(mu2_genpartidx) > ngenpart - 1) return -1.0; 

                ROOT::Math::XYZVector genpart_muon_vertex;
                genpart_muon_vertex.SetXYZ(GenPart_vertex_x[mu1_genpartidx], GenPart_vertex_y[mu1_genpartidx], GenPart_vertex_z[mu1_genpartidx]);
                ROOT::Math::XYZVector genpart_muon_vertex1;
                genpart_muon_vertex1.SetXYZ(GenPart_vertex_x[mu2_genpartidx], GenPart_vertex_y[mu2_genpartidx], GenPart_vertex_z[mu2_genpartidx]);         

                ROOT::RVec<float> gen_vertex_lxy_pT(3);
                float gen_mu1_px, gen_mu1_py, gen_mu1_pz;
                float gen_mu2_px, gen_mu2_py, gen_mu2_pz;

                if(genpart_muon_vertex == genpart_muon_vertex1 && abs(GenPart_pdgId[mu1_genpartidx])==13 && abs(GenPart_pdgId[mu2_genpartidx])==13 && Muon_charge[mu1_idx] != Muon_charge[mu2_idx]
                   && abs(mu1_idx) <= nmuon - 1 && abs(mu2_idx) <= nmuon - 1 && abs(mu1_genpartidx) <= ngenpart - 1 && abs(mu2_genpartidx) <= ngenpart - 1 && GenPart_pt[mu1_genpartidx] > 3.0 && GenPart_pt[mu2_genpartidx] > 3.0 
                   && (abs(GenPart_eta[mu1_genpartidx]) < 2.4 && abs(GenPart_eta[mu2_genpartidx]) < 2.4)){
                    gen_vertex_lxy_pT.at(0) = genpart_muon_vertex.Rho();
                    gen_mu1_px = GenPart_pt[mu1_genpartidx]*cos(GenPart_phi[mu1_genpartidx]);
                    gen_mu1_py = GenPart_pt[mu1_genpartidx]*sin(GenPart_phi[mu1_genpartidx]);
                    gen_mu1_pz = GenPart_pt[mu1_genpartidx]*std::sinh(GenPart_eta[mu1_genpartidx]);

                    gen_mu2_px = GenPart_pt[mu2_genpartidx]*cos(GenPart_phi[mu2_genpartidx]);
                    gen_mu2_py = GenPart_pt[mu2_genpartidx]*sin(GenPart_phi[mu2_genpartidx]);
                    gen_mu2_pz = GenPart_pt[mu2_genpartidx]*std::sinh(GenPart_eta[mu2_genpartidx]);

                    gen_vertex_lxy_pT.at(1) = std::sqrt(pow((gen_mu1_px + gen_mu2_px), 2) + pow((gen_mu1_py+gen_mu2_py), 2));
                    
                    if (muon_pass_probe(mu1_eta, mu1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6) && muon_pass_probe(mu2_eta, mu2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6)){
                        gen_vertex_lxy_pT.at(2) = std::min(GenPart_pt[mu1_genpartidx], GenPart_pt[mu2_genpartidx]);
                    }
                    else if (muon_pass_probe(mu1_eta, mu1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6)){
                        gen_vertex_lxy_pT.at(2) = GenPart_pt[mu1_genpartidx];
                    }
                    else if (muon_pass_probe(mu2_eta, mu2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6)){
                        gen_vertex_lxy_pT.at(2) = GenPart_pt[mu2_genpartidx];
                    }
                    else{
                        gen_vertex_lxy_pT.at(2) = std::min(GenPart_pt[mu1_genpartidx], GenPart_pt[mu2_genpartidx]);
                    }


                }
                else{
                    gen_vertex_lxy_pT.at(0) = -1.0;
                    gen_vertex_lxy_pT.at(1) = -1.0;
                    gen_vertex_lxy_pT.at(2) = -1.0;

                }

                return gen_vertex_lxy_pT;
            }

            """)

    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)

        #print("path = ", self.input()["data"][0].path)
        #print(self.input())

        #for preprocessRDF
        #df = ROOT.RDataFrame("Events", self.input()["root"].path)
       
        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)

        #df.Filter("bdt_scenarioA > 0.98")
        #df.Filter("bdt_vector > 0.993")

        df = df.Define("muonSV_min_chi2_index", """
            get_muonsv_index(nmuonSV, muonSV_chi2, muonSV_mu1index, muonSV_mu2index)
        """).Filter("muonSV_min_chi2_index != -1")

        df = df.Define("muon1_index", "muonSV_mu1index.at(muonSV_min_chi2_index)")
        df = df.Define("muon2_index", "muonSV_mu2index.at(muonSV_min_chi2_index)")
        for var in ["dxy", "dxybs", "dxyErr", "pt", "sip3d", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"float var; var = Muon_{var}.at(muon1_index); return var;")
            df = df.Define(f"muon2_{var}", f"float var; var = Muon_{var}.at(muon2_index); return var;")

        df = df.Define("gen_muonSV_lxy_pT", "gen_lxy_pT(Muon_eta, Muon_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, muonSV_min_chi2_index, nMuon, nGenPart, muonSV_mu1index, muonSV_mu2index, Muon_genPartIdx, GenPart_vertex_x, GenPart_vertex_y, GenPart_vertex_z, GenPart_pdgId, Muon_charge, GenPart_pt, GenPart_eta, GenPart_phi)")
        df = df.Define("gen_muonSV_lxy", "gen_muonSV_lxy_pT.at(0)").Define("gen_muonSV_pT", "gen_muonSV_lxy_pT.at(1)").Define("gen_trailing_muon_pT", "gen_muonSV_lxy_pT.at(2)")


        '''
        lxy_bins2 = [
             "gen_muonSV_lxy > 0.01 && gen_muonSV_lxy < 0.04",
             "gen_muonSV_lxy > 0.04 && gen_muonSV_lxy < 0.07",
             "gen_muonSV_lxy > 0.07 && gen_muonSV_lxy < 0.1",
             "gen_muonSV_lxy > 0.1 && gen_muonSV_lxy < 0.3",
             "gen_muonSV_lxy > 0.3 && gen_muonSV_lxy < 0.5",
             "gen_muonSV_lxy > 0.5 && gen_muonSV_lxy < 0.7",
             "gen_muonSV_lxy > 0.7 && gen_muonSV_lxy < 1.0",
             "gen_muonSV_lxy > 1.0 && gen_muonSV_lxy < 20.0",
             "gen_muonSV_lxy > 20.0 && gen_muonSV_lxy < 55.0",
             "gen_muonSV_lxy > 55.0 && gen_muonSV_lxy < 100.0",
        ]
        '''
        '''
        lxy_bins2 = [
             "gen_muonSV_lxy > 0.01 && gen_muonSV_lxy < 0.04",
             "gen_muonSV_lxy > 0.04 && gen_muonSV_lxy < 0.07",
             "gen_muonSV_lxy > 0.07 && gen_muonSV_lxy < 0.1",
             "gen_muonSV_lxy > 0.1 && gen_muonSV_lxy < 0.3",
             "gen_muonSV_lxy > 0.3 && gen_muonSV_lxy < 0.5",
             "gen_muonSV_lxy > 0.5 && gen_muonSV_lxy < 0.7",
             "gen_muonSV_lxy > 0.7 && gen_muonSV_lxy < 1.0",
             "gen_muonSV_lxy > 1.0 && gen_muonSV_lxy < 10.0",
             "gen_muonSV_lxy > 10.0 && gen_muonSV_lxy < 20.0",
             "gen_muonSV_lxy > 20.0 && gen_muonSV_lxy < 55.0",
             "gen_muonSV_lxy > 55.0 && gen_muonSV_lxy < 100.0"
        ]
        '''
        #For overall efficiency

        lxy_bins2 = [
             "gen_muonSV_lxy > 0.01 && gen_muonSV_lxy < 0.1",
             "gen_muonSV_lxy > 0.1 && gen_muonSV_lxy < 1.0",
             "gen_muonSV_lxy > 1.0 && gen_muonSV_lxy < 10.0",
             "gen_muonSV_lxy > 10.0 && gen_muonSV_lxy < 20.0",
             "gen_muonSV_lxy > 20.0 && gen_muonSV_lxy < 55.0",
             "gen_muonSV_lxy > 55.0 && gen_muonSV_lxy < 100.0"
        ]
  

        #For trigger efficiency
        '''
        lxy_bins2 = [
             "gen_muonSV_lxy > 0.01 && gen_muonSV_lxy < 0.04",
             "gen_muonSV_lxy > 0.04 && gen_muonSV_lxy < 0.07",
             "gen_muonSV_lxy > 0.07 && gen_muonSV_lxy < 0.1",
             "gen_muonSV_lxy > 0.1 && gen_muonSV_lxy < 0.3",
             "gen_muonSV_lxy > 0.3 && gen_muonSV_lxy < 0.5",
             "gen_muonSV_lxy > 0.5 && gen_muonSV_lxy < 0.7",
             "gen_muonSV_lxy > 0.7 && gen_muonSV_lxy < 1.0",
             "gen_muonSV_lxy > 1.0 && gen_muonSV_lxy < 2.0",
             "gen_muonSV_lxy > 2.0 && gen_muonSV_lxy < 3.0",
             "gen_muonSV_lxy > 3.0 && gen_muonSV_lxy < 10.0",
             "gen_muonSV_lxy > 10.0 && gen_muonSV_lxy < 20.0",
             "gen_muonSV_lxy > 20.0 && gen_muonSV_lxy < 55.0",
             "gen_muonSV_lxy > 55.0 && gen_muonSV_lxy < 100.0"
        ]
        '''
        dxysig_bins3 = [
            "trig_muon_dxysig > 0.5 && trig_muon_dxysig < 1.5",
            "trig_muon_dxysig > 1.5 && trig_muon_dxysig < 2.5",
            "trig_muon_dxysig > 2.5 && trig_muon_dxysig < 3.5",
            "trig_muon_dxysig > 3.5 && trig_muon_dxysig < 4.5",
            "trig_muon_dxysig > 4.5 && trig_muon_dxysig < 5.5",
            "trig_muon_dxysig > 5.5 && trig_muon_dxysig < 6.5",
            "trig_muon_dxysig > 6.5 && trig_muon_dxysig < 7.5",
            "trig_muon_dxysig > 7.5 && trig_muon_dxysig < 8.5",
            "trig_muon_dxysig > 8.5 && trig_muon_dxysig < 10.0",
            "trig_muon_dxysig > 10.0 && trig_muon_dxysig < 15.0",
            "trig_muon_dxysig > 15.0 && trig_muon_dxysig < 20.0",
            "trig_muon_dxysig > 20.0 && trig_muon_dxysig < 50.0"
        ]

        pt_bins3 = [
            "trig_muon_pt > 3.0 && trig_muon_pt < 4.0",
            "trig_muon_pt > 4.0 && trig_muon_pt < 6.0",
            "trig_muon_pt > 6.0 && trig_muon_pt < 10.0",
            "trig_muon_pt > 10.0 && trig_muon_pt < 16.0",
            "trig_muon_pt > 16.0 && trig_muon_pt < 30.0"
        ]

        #For hzdzd trigger efficiency

        lxy_bins_hzdzd = [
              "gen_muonSV_lxy > 0.0 && gen_muonSV_lxy < 0.2",
              "gen_muonSV_lxy > 0.2 && gen_muonSV_lxy < 1.0",
              "gen_muonSV_lxy > 1.0 && gen_muonSV_lxy < 2.4",
              "gen_muonSV_lxy > 2.4 && gen_muonSV_lxy < 3.1",
              "gen_muonSV_lxy > 3.1 && gen_muonSV_lxy < 7.0",
              "gen_muonSV_lxy > 7.0 && gen_muonSV_lxy < 11.0",
        ]

        pT_bins_hzdzd = [
              "gen_muonSV_pT < 25.0",
              "gen_muonSV_pT >= 25.0"  
        ]

        trailing_pT_bins_hzdzd = [
              "gen_trailing_muon_pT > 3.0 && gen_trailing_muon_pT < 5.0",
              "gen_trailing_muon_pT > 5.0 && gen_trailing_muon_pT < 8.0",
              "gen_trailing_muon_pT > 8.0 && gen_trailing_muon_pT < 10.0",
              "gen_trailing_muon_pT > 10.0 && gen_trailing_muon_pT < 15.0",
              "gen_trailing_muon_pT > 15.0 && gen_trailing_muon_pT < 30.0",
              "gen_trailing_muon_pT > 30.0" 
        ]



        histos = {}

        for lxy_index, i in enumerate(lxy_bins_hzdzd):
            #df_Pass_size_with_trigger = df.Filter(i).Filter("HLT_Mu9_IP6_part0 == 1 || HLT_Mu9_IP6_part1 == 1 || HLT_Mu9_IP6_part2 == 1 || HLT_Mu9_IP6_part3 == 1 || HLT_Mu9_IP6_part4 == 1").Count().GetValue()
            df_Pass_size_with_trigger = df.Filter(i).Filter(j).Filter("muon_pass_probe(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6) || muon_pass_probe(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6)").Count().GetValue()
            df_Pass_size = df.Filter(i).Filter(j).Count().GetValue()
            df_Fail_size = df.Filter("gen_muonSV_lxy == -1.0").Count().GetValue()

            h_lxy_pT_Pass_with_trigger = ROOT.TH1D("h_lxy_%s_pT_%s_Pass_with_trigger" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)
            h_lxy_pT_Pass = ROOT.TH1D("h_lxy_%s_pT_%s_Pass" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)
            h_lxy_pT_Fail = ROOT.TH1D("h_lxy_%s_pT_%s_Fail" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)

            for j in range(df_Pass_size):
                h_lxy_pT_Pass.Fill(0.0)
            for l in range(df_Pass_size_with_trigger):
                h_lxy_pT_Pass_with_trigger.Fill(0.0)
            for k in range(df_Fail_size):
                h_lxy_pT_Fail.Fill(0.0)

            histos["h_lxy_%s_pT_%s_Pass" % (lxy_index, pt_index)] = h_lxy_pT_Pass
            histos["h_lxy_%s_pT_%s_Pass_with_trigger" % (lxy_index, pt_index)] = h_lxy_pT_Pass_with_trigger
            histos["h_lxy_%s_pT_%s_Fail" % (lxy_index, pt_index)] = h_lxy_pT_Fail

        '''
        for lxy_index, i in enumerate(lxy_bins_hzdzd):
            for pt_index, j in enumerate(trailing_pT_bins_hzdzd):
                #df_Pass_size_with_trigger = df.Filter(i).Filter("HLT_Mu9_IP6_part0 == 1 || HLT_Mu9_IP6_part1 == 1 || HLT_Mu9_IP6_part2 == 1 || HLT_Mu9_IP6_part3 == 1 || HLT_Mu9_IP6_part4 == 1").Count().GetValue()
                df_Pass_size_with_trigger = df.Filter(i).Filter(j).Filter("muon_pass_probe(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6) || muon_pass_probe(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6)").Count().GetValue()
                df_Pass_size = df.Filter(i).Filter(j).Count().GetValue()
                df_Fail_size = df.Filter("gen_muonSV_lxy == -1.0").Count().GetValue()

                h_lxy_pT_Pass_with_trigger = ROOT.TH1D("h_lxy_%s_pT_%s_Pass_with_trigger" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)
                h_lxy_pT_Pass = ROOT.TH1D("h_lxy_%s_pT_%s_Pass" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)
                h_lxy_pT_Fail = ROOT.TH1D("h_lxy_%s_pT_%s_Fail" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)

                for j in range(df_Pass_size):
                    h_lxy_pT_Pass.Fill(0.0)
                for l in range(df_Pass_size_with_trigger):
                    h_lxy_pT_Pass_with_trigger.Fill(0.0)
                for k in range(df_Fail_size):
                    h_lxy_pT_Fail.Fill(0.0)

                histos["h_lxy_%s_pT_%s_Pass" % (lxy_index, pt_index)] = h_lxy_pT_Pass
                histos["h_lxy_%s_pT_%s_Pass_with_trigger" % (lxy_index, pt_index)] = h_lxy_pT_Pass_with_trigger
                histos["h_lxy_%s_pT_%s_Fail" % (lxy_index, pt_index)] = h_lxy_pT_Fail
        ''' 
        '''
        for lxy_index, i in enumerate(lxy_bins_hzdzd):
            for pt_index, j in enumerate(pT_bins_hzdzd): 
                df_Pass_size_with_trigger = df.Filter(i).Filter(j).Filter("muon_pass_probe(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6) || muon_pass_probe(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6)").Count().GetValue()
                df_Pass_size_with_trigger_and_BDT = df.Filter(i).Filter(j).Filter("muon_pass_probe(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6) || muon_pass_probe(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6)").Filter("bdt_scenarioA > 0.98").Count().GetValue()
                df_Pass_size = df.Filter(i).Filter(j).Count().GetValue()
                df_Fail_size = df.Filter("gen_muonSV_lxy == -1.0").Count().GetValue()

                h_lxy_pT_Pass_with_trigger = ROOT.TH1D("h_lxy_%s_pT_%s_Pass_with_trigger" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)
                h_lxy_pT_Pass_with_trigger_and_BDT = ROOT.TH1D("h_lxy_%s_pT_%s_Pass_with_trigger_and_BDT" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)
                h_lxy_pT_Pass = ROOT.TH1D("h_lxy_%s_pT_%s_Pass" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)
                h_lxy_pT_Fail = ROOT.TH1D("h_lxy_%s_pT_%s_Fail" % (lxy_index, pt_index), " ;;Events", 1, 0, 1)

                for j in range(df_Pass_size):
                    h_lxy_pT_Pass.Fill(0.0)
                for l in range(df_Pass_size_with_trigger):
                    h_lxy_pT_Pass_with_trigger.Fill(0.0)
                for x in range(df_Pass_size_with_trigger_and_BDT):
                    h_lxy_pT_Pass_with_trigger_and_BDT.Fill(0.0)
                for k in range(df_Fail_size):
                    h_lxy_pT_Fail.Fill(0.0)

                histos["h_lxy_%s_pT_%s_Pass" % (lxy_index, pt_index)] = h_lxy_pT_Pass
                histos["h_lxy_%s_pT_%s_Pass_with_trigger" % (lxy_index, pt_index)] = h_lxy_pT_Pass_with_trigger
                histos["h_lxy_%s_pT_%s_Pass_with_trigger_and_BDT" % (lxy_index, pt_index)] = h_lxy_pT_Pass_with_trigger_and_BDT
                histos["h_lxy_%s_pT_%s_Fail" % (lxy_index, pt_index)] = h_lxy_pT_Fail
        '''

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()
    
        

class IDSFtnp(TriggerSF):
    def add_to_root(self, root):
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"
            #include <cmath>

            static double igf(double S, double Z)
            {
                if(Z < 0.0)
                {
	            return 0.0;
                }
                double Sc = (1.0 / S);
                Sc *= pow(Z, S);
                Sc *= exp(-Z);
 
                double Sum = 1.0;
                double Nom = 1.0;
                double Denom = 1.0;
 
                for(int I = 0; I < 200; I++)
                {
	            Nom *= Z;
	            S++;
	            Denom *= S;
	            Sum += (Nom / Denom);
                }
 
                return Sum * Sc;
            }

            double chisqr(int Dof, double Cv)
            {
                if(Cv < 0 || Dof < 1)
                {
                    return 0.0;
                }
                double K = ((double)Dof) * 0.5;
                double X = Cv * 0.5;
                if(Dof == 2)
                {
	            return exp(-1.0 * X);
                }
 
                double PValue = igf(K, X);
                if(std::isnan(PValue) || std::isinf(PValue) || PValue <= 1e-8)
                {
                    return 1e-14;
                } 

                PValue /= tgamma(K); 
            	
                return (1.0 - PValue);
            }

            bool chi2sort (const std::pair<int, float>& a, const std::pair<int, float>& b)
            {
              return (a.second < b.second);
            }

            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;

            int get_muonsv_index(int nmuonSV, Vfloat muonSV_chi2, Vfloat muonSV_z, float PV_z, Vfloat muonSV_mass, Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi, Vint muonSV_mu1index, Vint muonSV_mu2index, Vint muonSV_charge)
            {
                //std::cout << "call get_muonsv_index function" << std::endl;
                std::vector<std::pair<int, float>> index_chi2;
                for (int i = 0; i < nmuonSV; i++) {
                    //if (chisqr(1, muonSV_chi2[i]) < 0.01 || abs(muonSV_z[i] - PV_z) > 0.5 || reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) < 0.15 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3 || muonSV_charge[i] != 0) continue;
                    if (chisqr(1, muonSV_chi2[i]) < 0.01 || reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], muonSV_mu2eta[i], muonSV_mu2phi[i]) < 0.15 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3 || muonSV_charge[i] != 0) continue;

                    int index1 = muonSV_mu1index[i];
                    int index2 = muonSV_mu2index[i];
                    index_chi2.push_back(std::make_pair(i, muonSV_chi2[i]));
                }
                //std::cout << "index_chi2.size = " << index_chi2.size() << std::endl;
                if (index_chi2.size() > 0) {
                    //std::cout << "before sort" << std::endl;
                    std::stable_sort(index_chi2.begin(), index_chi2.end(), chi2sort);
                    //std::cout << "after sort" << std::endl;
                    //std::cout << "index = " << index_chi2[0].first << std::endl;
                    return index_chi2[0].first;
                } else {
                    return -1;
                }
            }

            
            bool muon_pass(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_tightId, int muon_nStations, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt, Vfloat TrigObjBPark_l1dR)
            {
                
                //std::cout << "call muon_pass function" << std::endl;
                
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    //std::cout << "pass trigger" << std::endl; 
                    //std::cout<< "i = " << i << " " << reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) << " " << muon_pt << abs(muon_dxy)/muon_dxyErr << muon_tightId << std::endl;   
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.1 && muon_pt > 10.0 && abs(muon_dxy)/muon_dxyErr > 8.0 && muon_tightId == 1 && muon_nStations >= 2){
                        //std::cout << "before TrigObjBPark check" << std::endl;
                        
                        for (int j = 0; j < nTrigObjBPark; j++) {
                            //std::cout<< "j = " << j << " " << reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) << " " << TrigObjBPark_l1pt[j] << " " << TrigObjBPark_l1dR[j] << std::endl;
                            if (reco::deltaR(muon_eta, muon_phi, TrigObjBPark_eta[j], TrigObjBPark_phi[j]) < 0.05 && TrigObjBPark_l1pt[j] > 10.0 && TrigObjBPark_l1dR[j] < 0.05){
                                //std::cout << "muon pass!" << std::endl;
                                return true;
                            }
                        }
                        
                    }
                }
                //std::cout << "don't pass trigger" << std::endl;
                

                return false;
            }

            float muonBPark_matched_dR(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, Vfloat MuonBPark_matched_dr)
            {
                float dR = 999999;
                int index = -1;
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_HLT_Mu9_IP6[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < dR){
                        dR = reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]);
                        index = i;
                    }
                }

                if (index != -1) 
                    return MuonBPark_matched_dr.at(index);
                else 
                    return -999.0;

            }    
            


            bool muon_pass_probe(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_mediumId, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi)
            {
                if (muon_mediumId == 1){
                    return true;
                }
                else{
                    return false;
                }
            }

            bool muon_pass_tag(float muon_eta, float muon_phi, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.3)
                        return true;
                }
                return false;
            }

            ROOT::RVec<float> probe_values(float muon1_eta, float muon1_phi, float muon1_dxy, float muon1_dxyErr, float muon1_pt, float muon1_sip3d, int muon1_tightId, int muon1_mediumId, int muon1_isTracker, int muon1_nStations,
                float muon2_eta, float muon2_phi, float muon2_dxy, float muon2_dxyErr, float muon2_pt, float muon2_sip3d, int muon2_tightId, int muon2_mediumId, int muon2_isTracker, int muon2_nStations, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, int nTrigObjBPark, Vfloat TrigObjBPark_eta, Vfloat TrigObjBPark_phi, Vfloat TrigObjBPark_l1pt, Vfloat TrigObjBPark_l1dR, Vfloat MuonBPark_matched_dr) 
            {
                //std::cout << "call probe_values function" << std::endl;
                ROOT::RVec<float> probe_dxy_pt_HLT(6);

                if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, muon1_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) && muon_pass(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, muon2_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)){
                    //std::cout<<"block 1"<<std::endl;

                    //if both muons are matched to the HLT_Mu9_IP6 trigger muon, choose the muon with highest pT (muon1) as the tag
                    //bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                    //probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    //probe_dxy_pt_HLT.at(1) = muon2_pt;
                    //probe_dxy_pt_HLT.at(2) = HLT;
                    //probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    //probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    //probe_dxy_pt_HLT.at(5) = muon2_eta;

                    float muon1_muonBPark_matched_dR = muonBPark_matched_dR(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_matched_dr);
                    float muon2_muonBPark_matched_dR = muonBPark_matched_dR(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_matched_dr);

                    if(abs(muon1_muonBPark_matched_dR) > abs(muon2_muonBPark_matched_dR) && muon1_isTracker == 1){
                        bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                        probe_dxy_pt_HLT.at(0) = muon1_dxy;
                        probe_dxy_pt_HLT.at(1) = muon1_pt;
                        probe_dxy_pt_HLT.at(2) = HLT;
                        probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                        probe_dxy_pt_HLT.at(4) = abs(muon1_dxy)/muon1_dxyErr;
                        probe_dxy_pt_HLT.at(5) = muon1_eta;
                    }

                    else if(abs(muon2_muonBPark_matched_dR) > abs(muon1_muonBPark_matched_dR) && muon2_isTracker == 1){
                        bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                        probe_dxy_pt_HLT.at(0) = muon2_dxy;
                        probe_dxy_pt_HLT.at(1) = muon2_pt;
                        probe_dxy_pt_HLT.at(2) = HLT;
                        probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                        probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                        probe_dxy_pt_HLT.at(5) = muon2_eta;
                    }
                    else{ 
                        probe_dxy_pt_HLT.at(0) = -999999.0;
                        probe_dxy_pt_HLT.at(1) = -999999.0;
                        probe_dxy_pt_HLT.at(2) = -999999.0;
                        probe_dxy_pt_HLT.at(3) = -999999.0;
                        probe_dxy_pt_HLT.at(4) = -999999.0;
                        probe_dxy_pt_HLT.at(5) = -999999.0;
                    }

                }
                
                

                else if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, muon1_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)){
                    //std::cout<<"block 2"<<std::endl;
                    bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon2_eta;
                }
                else{ 
                    //std::cout<<"block 3"<<std::endl;
                    bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi);
                    probe_dxy_pt_HLT.at(0) = muon1_dxy;
                    probe_dxy_pt_HLT.at(1) = muon1_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon1_dxy)/muon1_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon1_eta;
                }

                //if (probe_dxy_pt_HLT.at(4) > 20.0 && probe_dxy_pt_HLT.at(4) < 50.0 && probe_dxy_pt_HLT.at(1) > 16.0 && probe_dxy_pt_HLT.at(1) < 30.0 && abs(probe_dxy_pt_HLT.at(5)) < 0.4){
                    //std::cout << "Probe_muon_dxy = " << probe_dxy_pt_HLT.at(0) << std::endl;
                    //std::cout << "Probe_muon_pt = " << probe_dxy_pt_HLT.at(1) << std::endl;
                    //std::cout << "Probe_muon_HLT = " << probe_dxy_pt_HLT.at(2) << std::endl;
                    //std::cout << "Probe_muon_sip3d = " << probe_dxy_pt_HLT.at(3) << std::endl;
                    //std::cout << "Probe_muon_dxysig = " << probe_dxy_pt_HLT.at(4) << std::endl;
                    //std::cout << "Probe_muon_eta = " << probe_dxy_pt_HLT.at(5) << std::endl;
                //}  
                return probe_dxy_pt_HLT;
            }

        
        """)
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)
        #print("path = ", self.input()["data"][0].path)
        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)
        
        df = df.Filter("nmuonSV > 0")

        #df = df.Filter("nmuonSV == 1")
        #df = df.Filter("nMuon == 2")


        df = df.Define("muonSV_min_chi2_index", """
            get_muonsv_index(nmuonSV, muonSV_chi2, muonSV_z, PV_z, muonSV_mass, muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index, muonSV_charge)
        """).Filter("muonSV_min_chi2_index != -1")

        df = df.Define("muon1_index", "muonSV_mu1index.at(muonSV_min_chi2_index)")
        df = df.Define("muon2_index", "muonSV_mu2index.at(muonSV_min_chi2_index)")
        for var in ["dxy", "dxybs", "dxyErr", "pt", "sip3d", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"float var; var = Muon_{var}.at(muon1_index); return var;")
            df = df.Define(f"muon2_{var}", f"float var; var = Muon_{var}.at(muon2_index); return var;")

        for var in ["tightId", "mediumId", "looseId", "isTracker", "nStations"]:
            df = df.Define(f"muon1_{var}", f"int var; var = Muon_{var}.at(muon1_index); return var;")
            df = df.Define(f"muon2_{var}", f"int var; var = Muon_{var}.at(muon2_index); return var;")


        df = df.Define("muonSV_mass_minchi2", "muonSV_mass.at(muonSV_min_chi2_index)")

        df = df.Define("muonSV_lxy_minchi2", "muonSV_dxy.at(muonSV_min_chi2_index)")
 
        
        #df.Snapshot("Events",  "test_0p01_new.root")
        

        #print("Finish defining muon qunatities")
        
        #for tag using HLT_Mu12_IP6
        
        #tight ID for tag, pre-selection for probe
        df = df.Filter("(muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, muon1_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) && muon2_isTracker == 1) || (muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, muon2_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) && muon1_isTracker == 1)")
        
        #tight ID for tag
        #df = df.Filter("muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR) || muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR)")
        
        #df.Snapshot("Events", "test_pass_0p01_new_after_pass.root")

        #tight ID for tag, medium ID for probe
        #df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_tightId, muon1_mediumId, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_tightId, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR, MuonBPark_matched_dr)")
        
        #tight ID for tag, loose ID for probe
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_tightId, muon1_looseId, muon1_isTracker, muon1_nStations, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_tightId, muon2_looseId, muon2_isTracker, muon2_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, nTrigObjBPark, TrigObjBPark_eta, TrigObjBPark_phi, TrigObjBPark_l1pt, TrigObjBPark_l1dR, MuonBPark_matched_dr)")

        df = df.Define("probe_dxy", "probe_quantities.at(0)").Define("probe_pt", "probe_quantities.at(1)").Define("probe_HLT", "probe_quantities.at(2)").Define("probe_sip3d", "probe_quantities.at(3)").Define("probe_dxysig", "probe_quantities.at(4)").Define("probe_eta", "probe_quantities.at(5)")

        df_pass = df.Filter("probe_HLT == 1")

        #df_pass.Snapshot("Events", "test_pass_0p01_new.root")
        
        dxy_bins = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        
        '''
        dxy_bins = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.004",
            "abs(probe_dxy) > 0.004 && abs(probe_dxy) < 0.007",
            "abs(probe_dxy) > 0.007 && abs(probe_dxy) < 0.008",
            "abs(probe_dxy) > 0.008 && abs(probe_dxy) < 0.009",
            "abs(probe_dxy) > 0.009 && abs(probe_dxy) < 0.01",
            "abs(probe_dxy) > 0.01 && abs(probe_dxy) < 0.02",
            "abs(probe_dxy) > 0.02 && abs(probe_dxy) < 0.03",
            "abs(probe_dxy) > 0.03 && abs(probe_dxy) < 0.04",
            "abs(probe_dxy) > 0.04 && abs(probe_dxy) < 0.07",
            "abs(probe_dxy) > 0.07 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.2",
            "abs(probe_dxy) > 0.2 && abs(probe_dxy) < 0.3",
            "abs(probe_dxy) > 0.3 && abs(probe_dxy) < 0.4",
            "abs(probe_dxy) > 0.4 && abs(probe_dxy) < 0.5",
            "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 0.6",
            "abs(probe_dxy) > 0.6 && abs(probe_dxy) < 0.7",
            "abs(probe_dxy) > 0.7 && abs(probe_dxy) < 0.8",
            "abs(probe_dxy) > 0.8 && abs(probe_dxy) < 0.9",
            "abs(probe_dxy) > 0.9 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        '''

        pt_bins = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]

        lxy_bins = [
            "muonSV_lxy_minchi2 > 0.001 && muonSV_lxy_minchi2 < 0.1",
            "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 1.0",
            "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 10.0"
        ]

        '''
        lxy_bins = [
             "muonSV_lxy_minchi2 > 0.01 && muonSV_lxy_minchi2 < 0.04",
             "muonSV_lxy_minchi2 > 0.04 && muonSV_lxy_minchi2 < 0.07",
             "muonSV_lxy_minchi2 > 0.07 && muonSV_lxy_minchi2 < 0.1",
             "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 0.3",
             "muonSV_lxy_minchi2 > 0.3 && muonSV_lxy_minchi2 < 0.5",
             "muonSV_lxy_minchi2 > 0.5 && muonSV_lxy_minchi2 < 0.7",
             "muonSV_lxy_minchi2 > 0.7 && muonSV_lxy_minchi2 < 1.0",
             "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 2.0",
             "muonSV_lxy_minchi2 > 2.0 && muonSV_lxy_minchi2 < 3.0",
             "muonSV_lxy_minchi2 > 3.0 && muonSV_lxy_minchi2 < 10.0",
             "muonSV_lxy_minchi2 > 10.0 && muonSV_lxy_minchi2 < 20.0",
             "muonSV_lxy_minchi2 > 20.0 && muonSV_lxy_minchi2 < 55.0",
             "muonSV_lxy_minchi2 > 55.0 && muonSV_lxy_minchi2 < 100.0"
        ]
        '''

        eta_bins_bparking = "abs(probe_eta) < 1.5"

        '''
        pt_bins = [
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]
        '''
        histos = {}

        df = df.Define("tag_probe_dR", "reco::deltaR(muon1_eta, muon1_phi, muon2_eta, muon2_phi)")

        

        for dxy_index, i in enumerate(dxy_bins):
            for pt_index, j in enumerate(pt_bins):
                h_dxy_pT_total = df.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_%s_total" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_dxy_pT_pass = df_pass.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
                h_dxy_pT_fail.SetName("h_dxy_%s_pT_%s_Fail"% (dxy_index, pt_index)) 

                histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] = h_dxy_pT_pass
                histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] = h_dxy_pT_fail
        
        for lxy_index, i in enumerate(lxy_bins):
            for pt_index, j in enumerate(pt_bins):
                h_lxy_pT_total = df.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_lxy_%s_pT_%s_total" % (lxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_lxy_pT_pass = df_pass.Filter(i).Filter(j).Filter(eta_bins_bparking).Histo1D(("h_lxy_%s_pT_%s_Pass" % (lxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_lxy_pT_fail = h_lxy_pT_total.GetPtr() - h_lxy_pT_pass.GetPtr()
                h_lxy_pT_fail.SetName("h_lxy_%s_pT_%s_Fail"% (lxy_index, pt_index)) 

                histos["h_lxy_%s_pt_%s_Pass" % (lxy_index, pt_index)] = h_lxy_pT_pass
                histos["h_lxy_%s_pt_%s_Fail" % (lxy_index, pt_index)] = h_lxy_pT_fail
        
        dxysig_bins3 = [
            "probe_dxysig > 0.5 && probe_dxysig < 1.5",
            "probe_dxysig > 1.5 && probe_dxysig < 2.5",
            "probe_dxysig > 2.5 && probe_dxysig < 3.5",
            "probe_dxysig > 3.5 && probe_dxysig < 4.5",
            "probe_dxysig > 4.5 && probe_dxysig < 5.5",
            "probe_dxysig > 5.5 && probe_dxysig < 6.5",
            "probe_dxysig > 6.5 && probe_dxysig < 7.5",
            "probe_dxysig > 7.5 && probe_dxysig < 8.5",
            "probe_dxysig > 8.5 && probe_dxysig < 10.0",
            "probe_dxysig > 10.0 && probe_dxysig < 15.0",
            "probe_dxysig > 15.0 && probe_dxysig < 20.0",
            "probe_dxysig > 20.0 && probe_dxysig < 50.0"
        ]
        
        pt_bins3 = [
            "probe_pt > 8.0 && probe_pt < 9.0",
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 12.0",
            "probe_pt > 12.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 20.0",
            "probe_pt > 20.0 && probe_pt < 30.0"
        ]

        eta_bins3 = "abs(probe_eta) < 0.4"
        #eta_bins3 = "abs(probe_eta) > 0.4 && abs(probe_eta) < 0.8"
        #eta_bins3 = "abs(probe_eta) > 0.8 && abs(probe_eta) < 1.5"

        histos["tag_and_probe_dR"] = df.Filter(eta_bins3).Histo1D(("h_tag_and_probe_dR", "; dR; Events", 100, 0.0, 7.0), "tag_probe_dR")


        for dxy_index, i in enumerate(dxysig_bins3):
            for pt_index, j in enumerate(pt_bins3):
                h_dxysig_pT_total = df.Filter(i).Filter(j).Filter(eta_bins3).Histo1D(("h_dxysig_%s_pT_%s_total" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                h_dxysig_pT_pass = df_pass.Filter(i).Filter(j).Filter(eta_bins3).Histo1D(("h_dxysig_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
                h_dxysig_pT_fail = h_dxysig_pT_total.GetPtr() - h_dxysig_pT_pass.GetPtr()
                h_dxysig_pT_fail.SetName("h_dxysig_%s_pT_%s_Fail"% (dxy_index, pt_index)) 

                histos["h_dxysig_%s_pt_%s_Pass" % (dxy_index, pt_index)] = h_dxysig_pT_pass
                histos["h_dxysig_%s_pt_%s_Fail" % (dxy_index, pt_index)] = h_dxysig_pT_fail
        
        
        #for 1D efficiency
        
        dxy_bins2 = [
            "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.1",
            "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 1.0",
            "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        '''
        dxy_bins2 = [
             "abs(probe_dxy) > 0.001 && abs(probe_dxy) < 0.004",
             "abs(probe_dxy) > 0.004 && abs(probe_dxy) < 0.007",
             "abs(probe_dxy) > 0.007 && abs(probe_dxy) < 0.008",
             "abs(probe_dxy) > 0.008 && abs(probe_dxy) < 0.009",
             "abs(probe_dxy) > 0.009 && abs(probe_dxy) < 0.01",
             "abs(probe_dxy) > 0.01 && abs(probe_dxy) < 0.02",
             "abs(probe_dxy) > 0.02 && abs(probe_dxy) < 0.03",
             "abs(probe_dxy) > 0.03 && abs(probe_dxy) < 0.04",
             "abs(probe_dxy) > 0.04 && abs(probe_dxy) < 0.07",
             "abs(probe_dxy) > 0.07 && abs(probe_dxy) < 0.1",
             "abs(probe_dxy) > 0.1 && abs(probe_dxy) < 0.2",
             "abs(probe_dxy) > 0.2 && abs(probe_dxy) < 0.3",
             "abs(probe_dxy) > 0.3 && abs(probe_dxy) < 0.4",
             "abs(probe_dxy) > 0.4 && abs(probe_dxy) < 0.5",
             "abs(probe_dxy) > 0.5 && abs(probe_dxy) < 0.6",
             "abs(probe_dxy) > 0.6 && abs(probe_dxy) < 0.7",
             "abs(probe_dxy) > 0.7 && abs(probe_dxy) < 0.8",
             "abs(probe_dxy) > 0.8 && abs(probe_dxy) < 0.9",
             "abs(probe_dxy) > 0.9 && abs(probe_dxy) < 1.0",
             "abs(probe_dxy) > 1.0 && abs(probe_dxy) < 10.0"
        ]
        '''
 
        lxy_bins2 = [
            "muonSV_lxy_minchi2 > 0.001 && muonSV_lxy_minchi2 < 0.1 && probe_pt > 0.0",
            "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 1.0 && probe_pt > 0.0",
            "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 10.0 && probe_pt > 0.0"
        ]

        '''
        lxy_bins2 = [
             "muonSV_lxy_minchi2 > 0.01 && muonSV_lxy_minchi2 < 0.04",
             "muonSV_lxy_minchi2 > 0.04 && muonSV_lxy_minchi2 < 0.07",
             "muonSV_lxy_minchi2 > 0.07 && muonSV_lxy_minchi2 < 0.1",
             "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 0.3",
             "muonSV_lxy_minchi2 > 0.3 && muonSV_lxy_minchi2 < 0.5",
             "muonSV_lxy_minchi2 > 0.5 && muonSV_lxy_minchi2 < 0.7",
             "muonSV_lxy_minchi2 > 0.7 && muonSV_lxy_minchi2 < 1.0",
             "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 3.0",
             "muonSV_lxy_minchi2 > 3.0 && muonSV_lxy_minchi2 < 5.0",
             "muonSV_lxy_minchi2 > 5.0 && muonSV_lxy_minchi2 < 7.0",
             "muonSV_lxy_minchi2 > 7.0 && muonSV_lxy_minchi2 < 10.0",
             "muonSV_lxy_minchi2 > 10.0 && muonSV_lxy_minchi2 < 20.0",
             "muonSV_lxy_minchi2 > 20.0 && muonSV_lxy_minchi2 < 55.0",
             "muonSV_lxy_minchi2 > 55.0 && muonSV_lxy_minchi2 < 100.0"
        ]
        
        lxy_bins2 = [
             "muonSV_lxy_minchi2 > 0.01 && muonSV_lxy_minchi2 < 0.04 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 0.04 && muonSV_lxy_minchi2 < 0.07 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 0.07 && muonSV_lxy_minchi2 < 0.1 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 0.1 && muonSV_lxy_minchi2 < 0.3 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 0.3 && muonSV_lxy_minchi2 < 0.5 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 0.5 && muonSV_lxy_minchi2 < 0.7 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 0.7 && muonSV_lxy_minchi2 < 1.0 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 1.0 && muonSV_lxy_minchi2 < 2.0 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 2.0 && muonSV_lxy_minchi2 < 3.0 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 3.0 && muonSV_lxy_minchi2 < 10.0 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 10.0 && muonSV_lxy_minchi2 < 20.0 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 20.0 && muonSV_lxy_minchi2 < 55.0 && probe_pt > 0.0",
             "muonSV_lxy_minchi2 > 55.0 && muonSV_lxy_minchi2 < 100.0 && probe_pt > 0.0"
        ]
        '''

        pt_bins2 = [
            "probe_pt > 3.0 && probe_pt < 4.0",
            "probe_pt > 4.0 && probe_pt < 5.0",
            "probe_pt > 5.0 && probe_pt < 6.0",
            "probe_pt > 6.0 && probe_pt < 7.0",
            "probe_pt > 7.0 && probe_pt < 8.0",
            "probe_pt > 8.0 && probe_pt < 9.0",
            "probe_pt > 9.0 && probe_pt < 10.0",
            "probe_pt > 10.0 && probe_pt < 16.0",
            "probe_pt > 16.0 && probe_pt < 30.0"
        ]

        IPsig_bins2 = [
            "probe_sip3d > 0.0 && probe_sip3d < 1.0",
            "probe_sip3d > 1.0 && probe_sip3d < 2.0",
            "probe_sip3d > 2.0 && probe_sip3d < 3.0",
            "probe_sip3d > 3.0 && probe_sip3d < 4.0",
            "probe_sip3d > 4.0 && probe_sip3d < 5.0",
            "probe_sip3d > 5.0 && probe_sip3d < 6.0",
            "probe_sip3d > 6.0 && probe_sip3d < 7.0",
            "probe_sip3d > 7.0 && probe_sip3d < 15.0",
            "probe_sip3d > 15.0 && probe_sip3d < 30.0"
        ]       

        for dxy_index, i in enumerate(dxy_bins2):
            h_dxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Histo1D(("h_dxy_%s_pT_100_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Histo1D(("h_dxy_%s_pT_100_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_100_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_100_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_100_Fail" % (dxy_index)] = h_dxy_pT_fail

        for lxy_index, i in enumerate(lxy_bins2):
            h_lxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Histo1D(("h_lxy_%s_pT_100_total" % (lxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_lxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Filter("probe_pt > 10.0").Histo1D(("h_lxy_%s_pT_100_Pass" % (lxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_lxy_pT_fail = h_lxy_pT_total.GetPtr() - h_lxy_pT_pass.GetPtr()
            h_lxy_pT_fail.SetName("h_lxy_%s_pT_100_Fail"% (lxy_index)) 

            histos["h_lxy_%s_pt_100_Pass" % (lxy_index)] = h_lxy_pT_pass
            histos["h_lxy_%s_pt_100_Fail" % (lxy_index)] = h_lxy_pT_fail

        for pt_index, i in enumerate(pt_bins2):
            h_dxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_100_pT_%s_total" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_100_pT_%s_Pass" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_100_pT_%s_Fail"% (pt_index)) 

            histos["h_dxy_100_pt_%s_Pass" % (pt_index)] = h_dxy_pT_pass
            histos["h_dxy_100_pt_%s_Fail" % (pt_index)] = h_dxy_pT_fail

        for dxy_index, i in enumerate(IPsig_bins2):
            h_dxy_pT_total = df.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_1000_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Filter(eta_bins_bparking).Histo1D(("h_dxy_%s_pT_1000_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_1000_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_1000_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_1000_Fail" % (dxy_index)] = h_dxy_pT_fail

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()