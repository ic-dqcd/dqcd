"""2024 ports of the 2018 trigger / ID efficiency tasks (tasks/triggerscalefactor.py, untouched).

TriggerSF2024     <- TriggerSF          : pass/fail of the trigger in a J/psi selection (no tag)
TriggerSFtnp2024  <- TriggerSFtnpRknew  : tag-and-probe trigger efficiency
IDSFtnp2024       <- IDSFtnp            : tag-and-probe muon ID efficiency

Common to all three (TriggerSF2024 base):
  * --trigger-case Mu10 (HLT_Mu10_Barrel_L1HP11_IP6, ParkingSingleMuon) or
    DoubleMu (HLT_DoubleMu4_3_LowMass, ParkingDoubleMuonLowMass); measured separately;
  * 2024 golden-JSON lumi mask on data (these tasks read the raw nano via InputData);
  * the trigger case in the output path.
T&P ports: same selections, binning and histograms as 2018; only the branches absent in 2024 are
replaced (generated from the 2018 classes by a fixed set of substitutions):
  MuonBPark_fired_HLT_Mu9_IP6 -> MuonBPark_fired_TRIG (= per-case MuonBPark_fired_HLT_<path>)
  nTrigObjBPark, TrigObjBPark_{eta,phi,l1pt} -> nTrigObjMu, TrigObjMu_{eta,phi,l1pt}
                                               (= TrigObj_* with TrigObj_id == 13)
  TrigObjBPark_l1dR < 0.05 -> TrigObj_l1pt > 10 (kept) AND MuonBPark_matched_dr < 0.05 (see muon_pass)
  C++ helpers in their own namespace (tnp24trig / tnp24id), declared once per process.
Run on the raw nano, before preprocessing (as in 2018). Commands: _tools/run_TriggerSF_2024.sh.
"""
import os
import luigi

from analysis_tools.utils import create_file_dir, import_root

from tasks.triggerscalefactor import TriggerSF

# Same golden JSON as the skims (config/modules_run3_efficienciesOnly*.yaml, lumimask block)
LUMI_MASK_2024 = "$CMT_BASE/../data/lumi/lumiMask_2024__Cert_Collisions2024_378981_386951_Golden.json"

# Mu10 and DoubleMu are measured separately, each on its own parking stream
TRIGGERS_2024 = {
    "Mu10": "HLT_Mu10_Barrel_L1HP11_IP6",
    "DoubleMu": "HLT_DoubleMu4_3_LowMass",
}
# per-muon "fired" flag of the same path (T&P tasks)
FIRED_2024 = {case: f"MuonBPark_fired_{path}" for case, path in TRIGGERS_2024.items()}


class TriggerSF2024(TriggerSF):
    trigger_case = luigi.ChoiceParameter(choices=list(TRIGGERS_2024), default="Mu10",
        description="trigger whose efficiency is measured: Mu10 (HLT_Mu10_Barrel_L1HP11_IP6) or "
        "DoubleMu (HLT_DoubleMu4_3_LowMass), default: Mu10")

    def store_parts(self):
        parts = super(TriggerSF2024, self).store_parts()
        parts["trigger_case"] = self.trigger_case
        return parts

    def run(self):
        ROOT = import_root()
        trigger = TRIGGERS_2024[self.trigger_case]

        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)

        if not self.dataset.process.isMC:
            from modules.lumi_mask import DQCDLumiMaskRDFProducer
            df, _ = DQCDLumiMaskRDFProducer(isMC=False, jsonFile=LUMI_MASK_2024).run(df)

        # --- selection identical to the 2018 TriggerSF task ---
        df = df.Filter("nMuon == 2", "2 muons").Filter("Muon_charge.at(0) != Muon_charge.at(1)", "OS")
        df = df.Filter("abs(Muon_eta.at(0)) < 2.4 && abs(Muon_eta.at(1)) < 2.4", "|eta| < 2.4")
        df = df.Filter("Muon_looseId.at(0) == 1 && Muon_looseId.at(1) == 1", "loose ID")
        df = df.Filter("nmuonSV == 1", "1 muonSV").Filter("muonSV_dxySig.at(0) > 2", "muonSV dxySig > 2")
        df = df.Filter("muonSV_chi2.at(0) < 5", "muonSV chi2 < 5")
        df = df.Filter("muonSV_mass.at(0) > 2.9 && muonSV_mass.at(0) < 3.3", "J/psi window")

        df = df.Define("min_dxy", "Min(abs(Muon_dxy))").Define("min_pt", "Min(Muon_pt)")

        dxy_bins = [
            "min_dxy > 0.00001 && min_dxy < 0.001",
            "min_dxy > 0.001 && min_dxy < 0.1",
            "min_dxy > 0.1 && min_dxy < 1.0",
            "min_dxy > 1.0 && min_dxy < 10.0",
        ]
        pt_bins = [
            "min_pt > 3.0 && min_pt < 4.0",
            "min_pt > 4.0 && min_pt < 6.0",
            "min_pt > 6.0 && min_pt < 10.0",
            "min_pt > 10.0 && min_pt < 16.0",
            "min_pt > 16.0 && min_pt < 30.0",
        ]

        df_pass = df.Filter(trigger, "trigger fired")
        df_fail = df.Filter(f"!{trigger}", "trigger not fired")

        histos = {"h_dxy_pt": df.Histo2D(("h_dxy_pt", "; dxy (cm); pT (GeV)",
            100, 0.00001, 10.0, 100, 3.0, 30.0), "min_dxy", "min_pt")}
        for dxy_index, dxy_sel in enumerate(dxy_bins):
            for pt_index, pt_sel in enumerate(pt_bins):
                for label, frame in (("Pass", df_pass), ("Fail", df_fail)):
                    name = f"h_dxy_{dxy_index}_pt_{pt_index}_{label}"
                    histos[name] = frame.Filter(dxy_sel).Filter(pt_sel).Histo1D(
                        (f"h_dxy_{dxy_index}_pT_{pt_index}_{label}",
                         "; Dimuon mass (GeV); Events/0.04 GeV", 15, 2.8, 3.4), "muonSV_mass")

        histo_file = ROOT.TFile.Open(create_file_dir(self.output().path), "RECREATE")
        for histo in histos.values():
            histo.Write()
        histo_file.Close()

        print(f"TriggerSF2024: trigger case {self.trigger_case} -> {trigger}")
        df.Report().Print()
        df_pass.Report().Print()


# ---------------------------------------------------------------------------------------------
# Port of tasks/triggerscalefactor.py:TriggerSFtnpRknew (generated 2026-11-03, see module docstring)
# ---------------------------------------------------------------------------------------------
class TriggerSFtnp2024(TriggerSF2024):
    def add_to_root(self, root):
        if getattr(type(self), '_declared', False):
            return
        type(self)._declared = True
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"
            #include <cmath>
            namespace tnp24trig {

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
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_TRIG, int nTrigObjMu, Vfloat TrigObjMu_eta, Vfloat TrigObjMu_phi, Vfloat TrigObjMu_l1pt, Vfloat MuonBPark_matched_dr)
            //bool muon_pass(float muon_pt, float muon_dxy, float muon_dxyErr, float muon_eta, float muon_phi, int muon_tightId, int nMuonBPark, Vfloat MuonBPark_eta,
                //Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_TRIG, int nTrigObjMu, Vfloat TrigObjMu_eta, Vfloat TrigObjMu_phi, Vfloat TrigObjMu_l1pt)
            {
                
                //std::cout << "call muon_pass function" << std::endl;
                
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_TRIG[i])
                        continue;
                    //std::cout << "pass trigger" << std::endl; 
                    //std::cout<< "i = " << i << " " << reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) << " " << muon_pt << abs(muon_dxy)/muon_dxyErr << muon_tightId << std::endl;   
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.1 && muon_pt > 10.0 && abs(muon_dxy)/muon_dxyErr > 8.0 && muon_tightId == 1){
                        //std::cout << "before TrigObjBPark check" << std::endl;
                        
                        for (int j = 0; j < nTrigObjMu; j++) {
                            //std::cout<< "j = " << j << " " << reco::deltaR(muon_eta, muon_phi, TrigObjMu_eta[j], TrigObjMu_phi[j]) << " " << TrigObjMu_l1pt[j] << " " << MuonBPark_matched_dr[j] << std::endl;
                            // 2024: TrigObjBPark_l1dR (tag-L1 seed dR < 0.05) is not stored in the standard TrigObj table.
                            // It is replaced by requiring an associated L1 seed (TrigObj_l1pt > 10, below) AND a tight
                            // HLT match of the tag (MuonBPark_matched_dr < 0.05).
                            if (reco::deltaR(muon_eta, muon_phi, TrigObjMu_eta[j], TrigObjMu_phi[j]) < 0.05 && TrigObjMu_l1pt[j] > 10.0 && MuonBPark_matched_dr[i] < 0.05){
                            //if (reco::deltaR(muon_eta, muon_phi, TrigObjMu_eta[j], TrigObjMu_phi[j]) < 0.05 && TrigObjMu_l1pt[j] > 10.0){
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
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_TRIG, Vfloat MuonBPark_matched_dr)
            {
                float dR = 999999;
                int index = -1;
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_TRIG[i])
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
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_TRIG, int nTrigObjMu, Vfloat TrigObjMu_eta, Vfloat TrigObjMu_phi)
            {
                for (int i = 0; i < nMuonBPark; i++) {
                    //std::cout<< i << " "<< MuonBPark_fired_TRIG[i] << " " << reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) << std::endl;
                    if (!MuonBPark_fired_TRIG[i])
                        continue;
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.1 && muon_mediumId == 1){  
                        for (int j = 0; j < nTrigObjMu; j++) {
                            if (reco::deltaR(muon_eta, muon_phi, TrigObjMu_eta[j], TrigObjMu_phi[j]) < 0.2)
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
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_TRIG, int nTrigObjMu, Vfloat TrigObjMu_eta, Vfloat TrigObjMu_phi, Vfloat TrigObjMu_l1pt, Vfloat MuonBPark_matched_dr) 
            {
                //std::cout << "call probe_values function" << std::endl;
                ROOT::RVec<float> probe_dxy_pt_HLT(6);

                if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr) && muon_pass(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)){
                    //std::cout<<"block 1"<<std::endl;

                    //if both muons are matched to the HLT_Mu9_IP6 trigger muon, choose the muon with highest pT (muon1) as the tag
                    //bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
                    //probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    //probe_dxy_pt_HLT.at(1) = muon2_pt;
                    //probe_dxy_pt_HLT.at(2) = HLT;
                    //probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    //probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    //probe_dxy_pt_HLT.at(5) = muon2_eta;

                    float muon1_muonBPark_matched_dR = muonBPark_matched_dR(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, MuonBPark_matched_dr);
                    float muon2_muonBPark_matched_dR = muonBPark_matched_dR(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, MuonBPark_matched_dr);

                    if(abs(muon1_muonBPark_matched_dR) > abs(muon2_muonBPark_matched_dR)){
                        bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
                        probe_dxy_pt_HLT.at(0) = muon1_dxy;
                        probe_dxy_pt_HLT.at(1) = muon1_pt;
                        probe_dxy_pt_HLT.at(2) = HLT;
                        probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                        probe_dxy_pt_HLT.at(4) = abs(muon1_dxy)/muon1_dxyErr;
                        probe_dxy_pt_HLT.at(5) = muon1_eta;
                    }

                    else{
                        bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
                        probe_dxy_pt_HLT.at(0) = muon2_dxy;
                        probe_dxy_pt_HLT.at(1) = muon2_pt;
                        probe_dxy_pt_HLT.at(2) = HLT;
                        probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                        probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                        probe_dxy_pt_HLT.at(5) = muon2_eta;
                    }

                }
                
                

                else if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)){
                    //std::cout<<"block 2"<<std::endl;
                    bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon2_eta;
                }
                else{ 
                    //std::cout<<"block 3"<<std::endl;
                    bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
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

        
            } // namespace tnp24trig
        """)
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)
        #print("path = ", self.input()["data"][0].path)
        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)
        # --- 2024 inputs (TriggerSF2024 port) ---
        if not self.dataset.process.isMC:
            from modules.lumi_mask import DQCDLumiMaskRDFProducer
            df, _ = DQCDLumiMaskRDFProducer(isMC=False, jsonFile=LUMI_MASK_2024).run(df)
        # muon trigger objects of the standard TrigObj table replace TrigObjBPark (absent in 2024)
        df = df.Define("TrigObjMu_sel", "TrigObj_id == 13")
        df = df.Define("nTrigObjMu", "(int) Sum(TrigObjMu_sel)")
        for var in ["eta", "phi", "l1pt"]:
            df = df.Define(f"TrigObjMu_{var}", f"ROOT::RVec<float>(TrigObj_{var}[TrigObjMu_sel])")
        # per-muon "fired" flag of the measured path (2018: MuonBPark_fired_HLT_Mu9_IP6)
        df = df.Define("MuonBPark_fired_TRIG", f"ROOT::RVec<float>({FIRED_2024[self.trigger_case]})")
        
        df = df.Filter("nmuonSV > 0")

        #df = df.Filter("nmuonSV == 1")
        #df = df.Filter("nMuon == 2")


        df = df.Define("muonSV_min_chi2_index", """
            tnp24trig::get_muonsv_index(nmuonSV, muonSV_chi2, muonSV_z, PV_z, muonSV_mass, muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index, muonSV_charge)
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
        df = df.Filter("(tnp24trig::muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_looseId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr) && muon2_looseId == 1) || (tnp24trig::muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_looseId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr) && muon1_looseId == 1)")
        
        #tight ID for tag
        #df = df.Filter("tnp24trig::muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr) || tnp24trig::muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)")
        
        #df.Snapshot("Events", "test_pass_0p01_new_after_pass.root")

        #tight ID for tag, medium ID for probe
        #df = df.Define("probe_quantities", "tnp24trig::probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_tightId, muon1_mediumId, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_tightId, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)")
        
        #loose ID for tag, loose ID for probe
        df = df.Define("probe_quantities", "tnp24trig::probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_looseId, muon1_looseId, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_looseId, muon2_looseId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)")

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


# ---------------------------------------------------------------------------------------------
# Port of tasks/triggerscalefactor.py:IDSFtnp (generated 2026-11-03, see module docstring)
# ---------------------------------------------------------------------------------------------
class IDSFtnp2024(TriggerSF2024):
    def add_to_root(self, root):
        if getattr(type(self), '_declared', False):
            return
        type(self)._declared = True
        root.gInterpreter.Declare("""
            #include <utility>
            #include "DataFormats/Math/interface/deltaR.h"
            #include <cmath>
            namespace tnp24id {

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
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_TRIG, int nTrigObjMu, Vfloat TrigObjMu_eta, Vfloat TrigObjMu_phi, Vfloat TrigObjMu_l1pt, Vfloat MuonBPark_matched_dr)
            {
                
                //std::cout << "call muon_pass function" << std::endl;
                
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_TRIG[i])
                        continue;
                    //std::cout << "pass trigger" << std::endl; 
                    //std::cout<< "i = " << i << " " << reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) << " " << muon_pt << abs(muon_dxy)/muon_dxyErr << muon_tightId << std::endl;   
                    if (reco::deltaR(muon_eta, muon_phi, MuonBPark_eta[i], MuonBPark_phi[i]) < 0.1 && muon_pt > 10.0 && abs(muon_dxy)/muon_dxyErr > 8.0 && muon_tightId == 1 && muon_nStations >= 2){
                        //std::cout << "before TrigObjBPark check" << std::endl;
                        
                        for (int j = 0; j < nTrigObjMu; j++) {
                            //std::cout<< "j = " << j << " " << reco::deltaR(muon_eta, muon_phi, TrigObjMu_eta[j], TrigObjMu_phi[j]) << " " << TrigObjMu_l1pt[j] << " " << MuonBPark_matched_dr[j] << std::endl;
                            // 2024: TrigObjBPark_l1dR (tag-L1 seed dR < 0.05) is not stored in the standard TrigObj table.
                            // It is replaced by requiring an associated L1 seed (TrigObj_l1pt > 10, below) AND a tight
                            // HLT match of the tag (MuonBPark_matched_dr < 0.05).
                            if (reco::deltaR(muon_eta, muon_phi, TrigObjMu_eta[j], TrigObjMu_phi[j]) < 0.05 && TrigObjMu_l1pt[j] > 10.0 && MuonBPark_matched_dr[i] < 0.05){
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
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_TRIG, Vfloat MuonBPark_matched_dr)
            {
                float dR = 999999;
                int index = -1;
                for (int i = 0; i < nMuonBPark; i++) {
                    if (!MuonBPark_fired_TRIG[i])
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
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_TRIG, int nTrigObjMu, Vfloat TrigObjMu_eta, Vfloat TrigObjMu_phi)
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
                Vfloat MuonBPark_phi, Vfloat MuonBPark_fired_TRIG, int nTrigObjMu, Vfloat TrigObjMu_eta, Vfloat TrigObjMu_phi, Vfloat TrigObjMu_l1pt, Vfloat MuonBPark_matched_dr) 
            {
                //std::cout << "call probe_values function" << std::endl;
                ROOT::RVec<float> probe_dxy_pt_HLT(6);

                if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, muon1_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr) && muon_pass(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, muon2_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)){
                    //std::cout<<"block 1"<<std::endl;

                    //if both muons are matched to the HLT_Mu9_IP6 trigger muon, choose the muon with highest pT (muon1) as the tag
                    //bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
                    //probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    //probe_dxy_pt_HLT.at(1) = muon2_pt;
                    //probe_dxy_pt_HLT.at(2) = HLT;
                    //probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    //probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    //probe_dxy_pt_HLT.at(5) = muon2_eta;

                    float muon1_muonBPark_matched_dR = muonBPark_matched_dR(muon1_eta, muon1_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, MuonBPark_matched_dr);
                    float muon2_muonBPark_matched_dR = muonBPark_matched_dR(muon2_eta, muon2_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, MuonBPark_matched_dr);

                    if(abs(muon1_muonBPark_matched_dR) > abs(muon2_muonBPark_matched_dR) && muon1_isTracker == 1){
                        bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
                        probe_dxy_pt_HLT.at(0) = muon1_dxy;
                        probe_dxy_pt_HLT.at(1) = muon1_pt;
                        probe_dxy_pt_HLT.at(2) = HLT;
                        probe_dxy_pt_HLT.at(3) = muon1_sip3d;
                        probe_dxy_pt_HLT.at(4) = abs(muon1_dxy)/muon1_dxyErr;
                        probe_dxy_pt_HLT.at(5) = muon1_eta;
                    }

                    else if(abs(muon2_muonBPark_matched_dR) > abs(muon1_muonBPark_matched_dR) && muon2_isTracker == 1){
                        bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
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
                
                

                else if (muon_pass(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, muon1_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)){
                    //std::cout<<"block 2"<<std::endl;
                    bool HLT = muon_pass_probe(muon2_pt, muon2_dxy, muon2_dxyErr, muon2_eta, muon2_phi, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
                    probe_dxy_pt_HLT.at(0) = muon2_dxy;
                    probe_dxy_pt_HLT.at(1) = muon2_pt;
                    probe_dxy_pt_HLT.at(2) = HLT;
                    probe_dxy_pt_HLT.at(3) = muon2_sip3d;
                    probe_dxy_pt_HLT.at(4) = abs(muon2_dxy)/muon2_dxyErr;
                    probe_dxy_pt_HLT.at(5) = muon2_eta;
                }
                else{ 
                    //std::cout<<"block 3"<<std::endl;
                    bool HLT = muon_pass_probe(muon1_pt, muon1_dxy, muon1_dxyErr, muon1_eta, muon1_phi, muon1_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi);
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

        
            } // namespace tnp24id
        """)
    def run(self):
        ROOT = import_root()
        self.add_to_root(ROOT)
        #print("path = ", self.input()["data"][0].path)
        df = ROOT.RDataFrame("Events", self.input()["data"][0].path)
        # --- 2024 inputs (TriggerSF2024 port) ---
        if not self.dataset.process.isMC:
            from modules.lumi_mask import DQCDLumiMaskRDFProducer
            df, _ = DQCDLumiMaskRDFProducer(isMC=False, jsonFile=LUMI_MASK_2024).run(df)
        # muon trigger objects of the standard TrigObj table replace TrigObjBPark (absent in 2024)
        df = df.Define("TrigObjMu_sel", "TrigObj_id == 13")
        df = df.Define("nTrigObjMu", "(int) Sum(TrigObjMu_sel)")
        for var in ["eta", "phi", "l1pt"]:
            df = df.Define(f"TrigObjMu_{var}", f"ROOT::RVec<float>(TrigObj_{var}[TrigObjMu_sel])")
        # per-muon "fired" flag of the measured path (2018: MuonBPark_fired_HLT_Mu9_IP6)
        df = df.Define("MuonBPark_fired_TRIG", f"ROOT::RVec<float>({FIRED_2024[self.trigger_case]})")
        
        df = df.Filter("nmuonSV > 0")

        #df = df.Filter("nmuonSV == 1")
        #df = df.Filter("nMuon == 2")


        df = df.Define("muonSV_min_chi2_index", """
            tnp24id::get_muonsv_index(nmuonSV, muonSV_chi2, muonSV_z, PV_z, muonSV_mass, muonSV_mu1eta, muonSV_mu2eta, muonSV_mu1phi, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index, muonSV_charge)
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
        df = df.Filter("(tnp24id::muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, muon1_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr) && muon2_isTracker == 1) || (tnp24id::muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, muon2_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr) && muon1_isTracker == 1)")
        
        #tight ID for tag
        #df = df.Filter("tnp24id::muon_pass(muon1_pt, muon1_dxybs, muon1_dxyErr, muon1_eta, muon1_phi, muon1_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr) || tnp24id::muon_pass(muon2_pt, muon2_dxybs, muon2_dxyErr, muon2_eta, muon2_phi, muon2_tightId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)")
        
        #df.Snapshot("Events", "test_pass_0p01_new_after_pass.root")

        #tight ID for tag, medium ID for probe
        #df = df.Define("probe_quantities", "tnp24id::probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_tightId, muon1_mediumId, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_tightId, muon2_mediumId, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)")
        
        #tight ID for tag, loose ID for probe
        df = df.Define("probe_quantities", "tnp24id::probe_values(muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_tightId, muon1_looseId, muon1_isTracker, muon1_nStations, muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_tightId, muon2_looseId, muon2_isTracker, muon2_nStations, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, nTrigObjMu, TrigObjMu_eta, TrigObjMu_phi, TrigObjMu_l1pt, MuonBPark_matched_dr)")

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
