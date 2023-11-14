import law
import os

from cmt.base_tasks.base import DatasetTaskWithCategory, HTCondorWorkflow, SGEWorkflow, InputData

from analysis_tools.utils import create_file_dir, import_root

class TriggerSF(DatasetTaskWithCategory, law.LocalWorkflow, HTCondorWorkflow, SGEWorkflow):
    def create_branch_map(self):
        return len(self.dataset.get_files(
            os.path.expandvars("$CMT_TMP_DIR/%s/" % self.config_name), add_prefix=False,
            check_empty=True))


    def requires(self):
        return {"data": InputData.req(self, file_index=self.branch)}

    def workflow_requires(self):
        return {"data": InputData.req(self)}

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

            ROOT::RVec<float> probe_values(float muon1_eta, float muon1_phi, float muon1_dxy, float muon1_pt, 
                float muon2_eta, float muon2_phi, float muon2_dxy, float muon2_pt, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, Vfloat MuonBPark_fired_HLT_Mu20, Vfloat MuonBPark_fired_HLT_Mu27, Vfloat MuonBPark_fired_HLT_Mu50, Vfloat MuonBPark_fired_HLT_Mu55) 
            {
                ROOT::RVec<float> probe_dxy_pt_HLT(3);

                if (muon_pass_tag(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55]) && muon_pass_tag(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55])){
                    bool HLT = muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                }
                
                //if both muons are matched to the HLT_Mu20 trigger muon, choose the muon with highest pT (muon1) as the tag

                else if (muon_pass_tag(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55])){
                    bool HLT = muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                }
                else{ 
                    bool HLT = muon_pass(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon1_dxy;
                    probe_dxy_pt_HLT.at(1) = muon1_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
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
        for var in ["dxy", "pt", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"Muon_{var}.at(muon1_index)")
            df = df.Define(f"muon2_{var}", f"Muon_{var}.at(muon2_index)")
        df = df.Define("muonSV_mass_minchi2", "muonSV_mass.at(muonSV_min_chi2_index)")
 
        #for tag using HLT_Mu20
        
        df = df.Filter("muon_pass_tag(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55]) && muon_pass_tag(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55], MuonBPark_phi[MuonBPark_fired_HLT_Mu20 || MuonBPark_fired_HLT_Mu27 || MuonBPark_fired_HLT_Mu50 || MuonBPark_fired_HLT_Mu55])")
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxy, muon1_pt, muon2_eta, muon2_phi, muon2_dxy, muon2_pt, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_fired_HLT_Mu20, MuonBPark_fired_HLT_Mu27, MuonBPark_fired_HLT_Mu50, MuonBPark_fired_HLT_Mu55)")
        
 
        #for tag using HLT_Mu12_IP6
        '''
        df = df.Filter("muon_pass(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu12_IP6) || muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu12_IP6)")
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxy, muon1_pt, muon2_eta, muon2_phi, muon2_dxy, muon2_pt, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_fired_HLT_Mu12_IP6)")
        '''

        df = df.Define("probe_dxy", "probe_quantities.at(0)").Define("probe_pt", "probe_quantities.at(1)").Define("probe_HLT", "probe_quantities.at(2)")

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

        for dxy_index, i in enumerate(dxy_bins2):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_%s_pT_100_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_%s_pT_100_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_100_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_100_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_100_Fail" % (dxy_index)] = h_dxy_pT_fail

        for pt_index, i in enumerate(pt_bins):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_100_pT_%s_total" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_100_pT_%s_Pass" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_100_pT_%s_Fail"% (pt_index)) 

            histos["h_dxy_100_pt_%s_Pass" % (pt_index)] = h_dxy_pT_pass
            histos["h_dxy_100_pt_%s_Fail" % (pt_index)] = h_dxy_pT_fail


        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()
        


class TriggerSFtnpbparking(TriggerSF):
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

            ROOT::RVec<float> probe_values(float muon1_eta, float muon1_phi, float muon1_dxy, float muon1_pt, 
                float muon2_eta, float muon2_phi, float muon2_dxy, float muon2_pt, int nMuonBPark, Vfloat MuonBPark_eta,
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_HLT_Mu9_IP6, Vfloat MuonBPark_fired_HLT_Mu20) 
            {
                ROOT::RVec<float> probe_dxy_pt_HLT(3);

                if (muon_pass(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu20) && muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu20)){
                    bool HLT = muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                }
                
                //if both muons are matched to the HLT_Mu20 trigger muon, choose the muon with highest pT (muon1) as the tag

                else if (muon_pass(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu20)){
                    bool HLT = muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                }
                else{ 
                    bool HLT = muon_pass(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6);
                    probe_dxy_pt_HLT.at(0) = muon1_dxy;
                    probe_dxy_pt_HLT.at(1) = muon1_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
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
        for var in ["dxy", "pt", "eta", "phi"]:
            df = df.Define(f"muon1_{var}", f"Muon_{var}.at(muon1_index)")
            df = df.Define(f"muon2_{var}", f"Muon_{var}.at(muon2_index)")
        df = df.Define("muonSV_mass_minchi2", "muonSV_mass.at(muonSV_min_chi2_index)")
 
        
        #for tag using HLT_Mu12_IP6
        
        df = df.Filter("muon_pass(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu12_IP6) || muon_pass(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu12_IP6)")
        df = df.Define("probe_quantities", "probe_values(muon1_eta, muon1_phi, muon1_dxy, muon1_pt, muon2_eta, muon2_phi, muon2_dxy, muon2_pt, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_fired_HLT_Mu12_IP6)")
        

        df = df.Define("probe_dxy", "probe_quantities.at(0)").Define("probe_pt", "probe_quantities.at(1)").Define("probe_HLT", "probe_quantities.at(2)")

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

        for dxy_index, i in enumerate(dxy_bins2):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_%s_pT_100_total" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_%s_pT_100_Pass" % (dxy_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_%s_pT_100_Fail"% (dxy_index)) 

            histos["h_dxy_%s_pt_100_Pass" % (dxy_index)] = h_dxy_pT_pass
            histos["h_dxy_%s_pt_100_Fail" % (dxy_index)] = h_dxy_pT_fail

        for pt_index, i in enumerate(pt_bins):
            h_dxy_pT_total = df.Filter(i).Histo1D(("h_dxy_100_pT_%s_total" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
            h_dxy_pT_pass = df_pass.Filter(i).Histo1D(("h_dxy_100_pT_%s_Pass" % (pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass_minchi2")
                
            h_dxy_pT_fail = h_dxy_pT_total.GetPtr() - h_dxy_pT_pass.GetPtr()
            h_dxy_pT_fail.SetName("h_dxy_100_pT_%s_Fail"% (pt_index)) 

            histos["h_dxy_100_pt_%s_Pass" % (pt_index)] = h_dxy_pT_pass
            histos["h_dxy_100_pt_%s_Fail" % (pt_index)] = h_dxy_pT_fail

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()
















