import law
import os

from cmt.base_tasks.base import DatasetTaskWithCategory, HTCondorWorkflow, SGEWorkflow, InputData

from analysis_tools.utils import create_file_dir, import_root

class TriggerSFnewselections2(DatasetTaskWithCategory, law.LocalWorkflow, HTCondorWorkflow, SGEWorkflow):
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

    def add_to_root(self, root):
        root.gInterpreter.Declare("""
        #include "TMath.h"
        #include <Math/Vector3D.h>
        #include <algorithm>
        #include <iostream>
        #include <vector>
        #include <cmath>
        #include "DataFormats/Math/interface/deltaR.h"


        using Vfloat = const ROOT::RVec<float>&;
        ROOT::RVec<float> triggered_muonSV_mass(Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, Vfloat muonSV_mu1phi, Vfloat muonSV_mu2phi, ROOT::RVec<int> muonSV_mu1index, ROOT::RVec<int> muonSV_mu2index, ROOT::RVec<int> Muon_looseId, Vfloat Muon_dxy, Vfloat Muon_pt, ROOT::RVec<int> MuonBPark_fired_HLT_Mu9_IP6, Vfloat MuonBPark_eta, Vfloat MuonBPark_phi, Vfloat muonSV_x, Vfloat muonSV_y, Vfloat muonSV_z, Vfloat muonSV_mass, Vfloat muonSV_dxySig, Vfloat muonSV_chi2)
        {
        const auto muonSV_size = muonSV_x.size();
        const auto MuonBPark_size = MuonBPark_eta.size();
        ROOT::RVec<float> dxy1_pt1_dxy2_pt2_muonSVmass(6);

        std::cout << "muonSV_size = " << muonSV_size << std::endl;

        std::vector<float> pt1;
        std::vector<float> pt2;
        std::vector<float> dxy1;
        std::vector<float> dxy2;
        std::vector<float> mass1;
        std::vector<float> mass2;
        std::vector<float> chi2;

        for(auto i = 0; i < muonSV_size; i++){
            //std::cout << "muonSV_dxySig = " << muonSV_dxySig[i] << std::endl;
            //std::cout << "muonSV_chi2 = " << muonSV_chi2[i] << std::endl;
            //std::cout << "muonSV_mass = " << muonSV_mass[i] << std::endl;

            if(muonSV_dxySig[i] < 2.0 || muonSV_chi2[i] > 5.0 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3) continue;
            
            ROOT::Math::XYZVector muonSV_vertex(muonSV_x[i], muonSV_y[i], muonSV_z[i]); 
            //std::cout << "muonSV_vertex x = " << muonSV_vertex.X() << std::endl;

            int index1 = muonSV_mu1index[i];
            int index2 = muonSV_mu2index[i];

            if(abs(muonSV_mu1eta[i]) > 2.4 || abs(muonSV_mu2eta[i]) > 2.4 || Muon_looseId[index1] == 0 || Muon_looseId[index2] == 0) continue;
            
            int trigger_match1 = 0;
            int trigger_match2 = 0;

            for(auto k = 0; k < MuonBPark_size; k++){
                
                if(MuonBPark_fired_HLT_Mu9_IP6[k] == 0) continue;

                if(reco::deltaR(muonSV_mu1eta[i], muonSV_mu1phi[i], MuonBPark_eta[k], MuonBPark_phi[k]) < 0.3) trigger_match1 += 1; 
 
                if(reco::deltaR(muonSV_mu2eta[i], muonSV_mu2phi[i], MuonBPark_eta[k], MuonBPark_phi[k]) < 0.3) trigger_match2 += 1;
                
            }

            if(trigger_match1 == 1){
                dxy1.push_back(Muon_dxy[index1]);
                pt1.push_back(Muon_pt[index1]);
                dxy2.push_back(-1.0);
                pt2.push_back(-1.0);
                mass1.push_back(muonSV_mass[i]);
                mass2.push_back(-1.0);
                chi2.push_back(muonSV_chi2[i]);
            } 
            if(trigger_match2 == 1){
                dxy1.push_back(-1.0);
                pt1.push_back(-1.0);
                dxy2.push_back(Muon_dxy[index2]);
                pt2.push_back(Muon_pt[index2]);
                mass1.push_back(-1.0);
                mass2.push_back(muonSV_mass[i]);
                chi2.push_back(muonSV_chi2[i]);
            }
        }
        if(mass1.size() > 0){
            auto result = std::min_element(chi2.begin(), chi2.end()); 
            int min_chi2_index = std::distance(chi2.begin(), result);
            
            dxy1_pt1_dxy2_pt2_muonSVmass.at(0) = dxy1[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(1) = pt1[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(2) = mass1[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(3) = dxy2[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(4) = pt2[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(5) = mass2[min_chi2_index];
        }
        if(mass1.size() == 0){
            dxy1_pt1_dxy2_pt2_muonSVmass.at(0) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(1) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(2) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(3) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(4) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(5) = -1.0;

        }
        return dxy1_pt1_dxy2_pt2_muonSVmass;
        }

        ROOT::RVec<float> not_triggered_muonSV_mass(Vfloat muonSV_mu1eta, Vfloat muonSV_mu2eta, ROOT::RVec<int> muonSV_mu1index, ROOT::RVec<int> muonSV_mu2index, ROOT::RVec<int> Muon_looseId, Vfloat Muon_dxy, Vfloat Muon_pt, ROOT::RVec<int> MuonBPark_fired_HLT_Mu9_IP6, Vfloat MuonBPark_vx, Vfloat MuonBPark_vy, Vfloat MuonBPark_vz, Vfloat muonSV_x, Vfloat muonSV_y, Vfloat muonSV_z, Vfloat muonSV_mass, Vfloat muonSV_dxySig, Vfloat muonSV_chi2)
        {
        const auto muonSV_size = muonSV_x.size();
        const auto MuonBPark_size = MuonBPark_vx.size();
        ROOT::RVec<float> dxy1_pt1_dxy2_pt2_muonSVmass(6);

        std::cout << "muonSV_size = " << muonSV_size << std::endl;

        std::vector<float> pt1;
        std::vector<float> pt2;
        std::vector<float> dxy1;
        std::vector<float> dxy2;
        std::vector<float> mass1;
        std::vector<float> mass2;
        std::vector<float> chi2;


        for(auto i = 0; i < muonSV_size; i++){

            //std::cout << "muonSV_chi2 = " << muonSV_chi2[i] << std::endl;
            //std::cout << "muonSV_mass = " << muonSV_mass[i] << std::endl;

            if(muonSV_dxySig[i] < 2.0 || muonSV_chi2[i] > 5.0 || muonSV_mass[i] < 2.9 || muonSV_mass[i] > 3.3) continue;
            
            ROOT::Math::XYZVector muonSV_vertex(muonSV_x[i], muonSV_y[i], muonSV_z[i]); 
            //std::cout << "muonSV_vertex x = " << muonSV_vertex.X() << std::endl;

            int index1 = muonSV_mu1index[i];
            int index2 = muonSV_mu2index[i];

            if(abs(muonSV_mu1eta[i]) > 2.4 || abs(muonSV_mu2eta[i]) > 2.4 || Muon_looseId[index1] == 0 || Muon_looseId[index2] == 0) continue;
            
            dxy1.push_back(Muon_dxy[index1]);
            pt1.push_back(Muon_pt[index1]);
            dxy2.push_back(Muon_dxy[index2]);
            pt2.push_back(Muon_pt[index2]);
            mass1.push_back(muonSV_mass[i]);
            mass2.push_back(muonSV_mass[i]);
            chi2.push_back(muonSV_chi2[i]);
            
        }

        if(mass1.size() > 0){
            auto result = std::min_element(chi2.begin(), chi2.end()); 
            int min_chi2_index = std::distance(chi2.begin(), result);
            
            dxy1_pt1_dxy2_pt2_muonSVmass.at(0) = dxy1[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(1) = pt1[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(2) = mass1[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(3) = dxy2[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(4) = pt2[min_chi2_index];
            dxy1_pt1_dxy2_pt2_muonSVmass.at(5) = mass2[min_chi2_index];
        }
        if(mass1.size() == 0){
            dxy1_pt1_dxy2_pt2_muonSVmass.at(0) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(1) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(2) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(3) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(4) = -1.0;
            dxy1_pt1_dxy2_pt2_muonSVmass.at(5) = -1.0;

        }


        return dxy1_pt1_dxy2_pt2_muonSVmass;
        }
        """)
        return root
 
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)
        def create_histos(path):

            df = ROOT.RDataFrame("Events", path)

            df = df.Filter("nmuonSV > 0")

            df_pass = df.Filter("nMuonBPark > 0").Define("triggered_mass", "triggered_muonSV_mass(muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index, Muon_looseId, Muon_dxy, Muon_pt, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_eta, MuonBPark_phi, muonSV_x, muonSV_y, muonSV_z, muonSV_mass, muonSV_dxySig, muonSV_chi2)").Define("triggered_muon1_dxy", "triggered_mass.at(0)").Define("triggered_muon1_pt", "triggered_mass.at(1)").Define("triggered_JPsi_mass1", "triggered_mass.at(2)").Define("triggered_muon2_dxy", "triggered_mass.at(3)").Define("triggered_muon2_pt", "triggered_mass.at(4)").Define("triggered_JPsi_mass2", "triggered_mass.at(5)")

            df_total = df.Define("not_triggered_mass", "not_triggered_muonSV_mass(muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1index, muonSV_mu2index, Muon_looseId, Muon_dxy, Muon_pt, MuonBPark_fired_HLT_Mu9_IP6, MuonBPark_vx, MuonBPark_vy, MuonBPark_vz, muonSV_x, muonSV_y, muonSV_z, muonSV_mass, muonSV_dxySig, muonSV_chi2)").Define("not_triggered_muon1_dxy", "not_triggered_mass.at(0)").Define("not_triggered_muon1_pt", "not_triggered_mass.at(1)").Define("not_triggered_JPsi_mass1", "not_triggered_mass.at(2)").Define("not_triggered_muon2_dxy", "not_triggered_mass.at(3)").Define("not_triggered_muon2_pt", "not_triggered_mass.at(4)").Define("not_triggered_JPsi_mass2", "not_triggered_mass.at(5)")
            

            #df = df.Filter("HLT_Photon20 == 1")

            #df_trigger = df.Filter("HLT_Mu9_IP6_part0==1 || HLT_Mu9_IP6_part1==1 || HLT_Mu9_IP6_part2==1 || HLT_Mu9_IP6_part3==1 || HLT_Mu9_IP6_part4==1")
            #df_not_trigger =  df.Filter("HLT_Mu9_IP6_part0==0 && HLT_Mu9_IP6_part1==0 && HLT_Mu9_IP6_part2==0 && HLT_Mu9_IP6_part3==0 && HLT_Mu9_IP6_part4==0")
    

            #df = df.Define("min_dxy", "Min(abs(Muon_dxy))").Define("min_pt", "Min(Muon_pt)")

            #dxy_bin_1 = "min_dxy > 0.00001 && min_dxy < 0.001"
            muon1_dxy_bin_1 = "triggered_muon1_dxy > 0.001 &&  triggered_muon1_dxy < 0.1"
            muon1_dxy_bin_2 = "triggered_muon1_dxy > 0.1 && triggered_muon1_dxy < 1.0" 
            muon1_dxy_bin_3 = "triggered_muon1_dxy > 1.0 && triggered_muon1_dxy < 10.0"

            muon1_pt_bin_1 = "triggered_muon1_pt > 3.0 && triggered_muon1_pt < 4.0"
            muon1_pt_bin_2 = "triggered_muon1_pt > 4.0 && triggered_muon1_pt < 6.0"
            muon1_pt_bin_3 = "triggered_muon1_pt > 6.0 && triggered_muon1_pt < 10.0"
            muon1_pt_bin_4 = "triggered_muon1_pt > 10.0 && triggered_muon1_pt < 16.0"
            muon1_pt_bin_5 = "triggered_muon1_pt > 16.0 && triggered_muon1_pt < 30.0"

            muon1_dxy_bins = [muon1_dxy_bin_1, muon1_dxy_bin_2, muon1_dxy_bin_3]
            muon1_pt_bins = [muon1_pt_bin_1, muon1_pt_bin_2, muon1_pt_bin_3, muon1_pt_bin_4, muon1_pt_bin_5]

            muon2_dxy_bin_1 = "triggered_muon2_dxy > 0.001 && triggered_muon2_dxy < 0.1"
            muon2_dxy_bin_2 = "triggered_muon2_dxy > 0.1 && triggered_muon2_dxy < 1.0" 
            muon2_dxy_bin_3 = "triggered_muon2_dxy > 1.0 && triggered_muon2_dxy < 10.0"

            muon2_pt_bin_1 = "triggered_muon2_pt > 3.0 && triggered_muon2_pt < 4.0"
            muon2_pt_bin_2 = "triggered_muon2_pt > 4.0 && triggered_muon2_pt < 6.0"
            muon2_pt_bin_3 = "triggered_muon2_pt > 6.0 && triggered_muon2_pt < 10.0"
            muon2_pt_bin_4 = "triggered_muon2_pt > 10.0 && triggered_muon2_pt < 16.0"
            muon2_pt_bin_5 = "triggered_muon2_pt > 16.0 && triggered_muon2_pt < 30.0"

            muon2_dxy_bins = [muon2_dxy_bin_1, muon2_dxy_bin_2, muon2_dxy_bin_3]
            muon2_pt_bins = [muon2_pt_bin_1, muon2_pt_bin_2, muon2_pt_bin_3, muon2_pt_bin_4, muon2_pt_bin_5]



            histos = {}   

            #histos["h_dxy_pt"] = df.Histo2D(("h_dxy_pt", "; dxy (cm); pT (GeV)", 100, 0.00001, 10.0, 100, 3.0, 30.0), "min_dxy", "min_pt") 

            for i in muon1_dxy_bins:
                for j in muon1_pt_bins:
                   
                    dxy_index = muon1_dxy_bins.index(i)
                    pt_index = muon1_pt_bins.index(j)

                    a = muon2_dxy_bins[dxy_index]
                    b = muon2_pt_bins[pt_index]
        
                    h_dxy_pT_pass_muon1 = df_pass.Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_Pass_muon1" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "triggered_JPsi_mass1")
                    h_dxy_pT_pass_muon2 = df_pass.Filter(a).Filter(b).Histo1D(("h_dxy_%s_pT_%s_Pass_muon2" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "triggered_JPsi_mass2")

                    
                    h_dxy_pT_pass = h_dxy_pT_pass_muon1.GetPtr() + h_dxy_pT_pass_muon2.GetPtr()
                    h_dxy_pT_pass.SetName("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index))
    

                    #histos["h_dxy_%s_pt_%s_Pass_muon1" % (dxy_index, pt_index)] = h_dxy_pT_pass_muon1
                    #histos["h_dxy_%s_pt_%s_Pass_muon2" % (dxy_index, pt_index)] = h_dxy_pT_pass_muon2
                    histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] = h_dxy_pT_pass

                    '''                      
                    histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] = df.Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "triggered_JPsi_mass") 

                    histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] = df.Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_Fail" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "not_triggered_JPsi_mass")    

                    '''
            not_triggered_muon1_dxy_bin_1 = "not_triggered_muon1_dxy > 0.001 && not_triggered_muon1_dxy < 0.1"
            not_triggered_muon1_dxy_bin_2 = "not_triggered_muon1_dxy > 0.1 && not_triggered_muon1_dxy < 1.0" 
            not_triggered_muon1_dxy_bin_3 = "not_triggered_muon1_dxy > 1.0 && not_triggered_muon1_dxy < 10.0"

            not_triggered_muon1_pt_bin_1 = "not_triggered_muon1_pt > 3.0 && not_triggered_muon1_pt < 4.0"
            not_triggered_muon1_pt_bin_2 = "not_triggered_muon1_pt > 4.0 && not_triggered_muon1_pt < 6.0"
            not_triggered_muon1_pt_bin_3 = "not_triggered_muon1_pt > 6.0 && not_triggered_muon1_pt < 10.0"
            not_triggered_muon1_pt_bin_4 = "not_triggered_muon1_pt > 10.0 && not_triggered_muon1_pt < 16.0"
            not_triggered_muon1_pt_bin_5 = "not_triggered_muon1_pt > 16.0 && not_triggered_muon1_pt < 30.0"

            not_triggered_muon1_dxy_bins = [not_triggered_muon1_dxy_bin_1, not_triggered_muon1_dxy_bin_2, not_triggered_muon1_dxy_bin_3]
            not_triggered_muon1_pt_bins = [not_triggered_muon1_pt_bin_1, not_triggered_muon1_pt_bin_2, not_triggered_muon1_pt_bin_3, not_triggered_muon1_pt_bin_4, not_triggered_muon1_pt_bin_5]

            not_triggered_muon2_dxy_bin_1 = "not_triggered_muon2_dxy > 0.001 && not_triggered_muon2_dxy < 0.1"
            not_triggered_muon2_dxy_bin_2 = "not_triggered_muon2_dxy > 0.1 && not_triggered_muon2_dxy < 1.0" 
            not_triggered_muon2_dxy_bin_3 = "not_triggered_muon2_dxy > 1.0 && not_triggered_muon2_dxy < 10.0"

            not_triggered_muon2_pt_bin_1 = "not_triggered_muon2_pt > 3.0 && not_triggered_muon2_pt < 4.0"
            not_triggered_muon2_pt_bin_2 = "not_triggered_muon2_pt > 4.0 && not_triggered_muon2_pt < 6.0"
            not_triggered_muon2_pt_bin_3 = "not_triggered_muon2_pt > 6.0 && not_triggered_muon2_pt < 10.0"
            not_triggered_muon2_pt_bin_4 = "not_triggered_muon2_pt > 10.0 && not_triggered_muon2_pt < 16.0"
            not_triggered_muon2_pt_bin_5 = "not_triggered_muon2_pt > 16.0 && not_triggered_muon2_pt < 30.0"

            not_triggered_muon2_dxy_bins = [not_triggered_muon2_dxy_bin_1, not_triggered_muon2_dxy_bin_2, not_triggered_muon2_dxy_bin_3]
            not_triggered_muon2_pt_bins = [not_triggered_muon2_pt_bin_1, not_triggered_muon2_pt_bin_2, not_triggered_muon2_pt_bin_3, not_triggered_muon2_pt_bin_4, not_triggered_muon2_pt_bin_5]
            
            for i in not_triggered_muon1_dxy_bins:
                for j in not_triggered_muon1_pt_bins:
                    dxy_index = not_triggered_muon1_dxy_bins.index(i)
                    pt_index = not_triggered_muon1_pt_bins.index(j)

                    a = not_triggered_muon2_dxy_bins[dxy_index]
                    b = not_triggered_muon2_pt_bins[pt_index]  

                    k = muon1_dxy_bins[dxy_index]
                    l = muon1_pt_bins[pt_index]

                    c = muon2_dxy_bins[dxy_index]
                    d = muon2_pt_bins[pt_index]

                    h_dxy_pT_total_muon1 = df_total.Filter(i).Filter(j).Histo1D(("h_dxy_%s_pT_%s_fail_muon1" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "not_triggered_JPsi_mass1")
                    h_dxy_pT_pass_muon1 = df_pass.Filter(k).Filter(l).Histo1D(("h_dxy_%s_pT_%s_Pass_muon1" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "triggered_JPsi_mass1") 
                    h_dxy_pT_total_muon2 = df_total.Filter(a).Filter(b).Histo1D(("h_dxy_%s_pT_%s_fail_muon2" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "not_triggered_JPsi_mass2") 
                    h_dxy_pT_pass_muon2 = df_pass.Filter(c).Filter(d).Histo1D(("h_dxy_%s_pT_%s_Pass_muon2" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "triggered_JPsi_mass2") 

                    
                    h_dxy_pT_fail = h_dxy_pT_total_muon1.GetPtr() - h_dxy_pT_pass_muon1.GetPtr() + h_dxy_pT_total_muon2.GetPtr() - h_dxy_pT_pass_muon2.GetPtr()
                    h_dxy_pT_fail.SetName("h_dxy_%s_pT_%s_Fail" % (dxy_index, pt_index))

                    #histos["h_dxy_%s_pt_%s_Fail_muon1" % (dxy_index, pt_index)] = h_dxy_pT_fail_muon1
                    #histos["h_dxy_%s_pt_%s_Fail_muon2" % (dxy_index, pt_index)] = h_dxy_pT_fail_muon2
                    histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] = h_dxy_pT_fail

            '''
            for a in muon2_dxy_bins:
                for b in muon2_pt_bins:
                   
                    dxy_index = muon2_dxy_bins.index(a)
                    pt_index = muon2_pt_bins.index(b)

                    histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] = histos["h_dxy_%s_pt_%s_Pass" % (dxy_index, pt_index)] + df.Filter(a).Filter(b).Histo1D(("h_dxy_%s_pT_%s_Pass" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "triggered_JPsi_mass")
                    histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] = histos["h_dxy_%s_pt_%s_Fail" % (dxy_index, pt_index)] + df.Filter(a).Filter(b).Histo1D(("h_dxy_%s_pT_%s_Fail" % (dxy_index, pt_index), "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "not_triggered_JPsi_mass")
            '''

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
     
 
