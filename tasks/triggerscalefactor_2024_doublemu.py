"""2024 dimuon-trigger (HLT_DoubleMu4_3_LowMass) efficiency with a factorised tag-and-probe.

The self-tag T&P of tasks/triggerscalefactor_2024.py:TriggerSFtnp2024 cannot be made unbiased for a
dimuon path (both legs are needed), so the efficiency is split in two measurements,

    eff(DoubleMu4_3_LowMass) = eff(L1) x eff(HLT | L1)

each a standard T&P on J/psi -> mu mu (same event selection, histogram families and bins as the
Mu10 task; only the tag / probe definitions differ):

  stage  tag (event bit + kinematic tag)              probe passes if                       data stream
  L1     HLT_Mu8 fired; muon loose ID, pT > 8          OR of the 5 dominant dimuon L1 seeds   ParkingSingleMuon
                                                       of the path (event bits, L1_OR below)
  HLT    HLT_Mu4_L1DoubleMu fired; muon loose ID,      HLT_DoubleMu4_3_LowMass fired AND the   ParkingDoubleMuonLowMass
         pT > 4 (parking path seeded by the            probe matched to it (per-muon flag)
         dimuon L1 seeds, ~L1 pass-through)

  (user 2026-11-06: the L1 probe is the OR of the 5 dominant seeds, L1_OR below, instead of all 12. Using L1_OR
  also as the HLT-stage tag was tried and reverted: the DoubleMuonLowMass stream only holds events where some
  parking HLT path fired, so a bare L1 tag loses the L1-fired/HLT-failed events and the data efficiency came
  out at 0.997 vs 0.92 in MC. The HLT_Mu4_L1DoubleMu tag path guarantees the stream presence.)

MC: BuToJpsiK for both stages (no prescales). The combination (product of the efficiencies / SFs) is
done by _tools/fitTnPScaleFactors.py --combine-stages.

2024 nano limitations (checked 2026-11-06): HLT_Mu8 and HLT_Mu4_L1DoubleMu exist only as event bits
(per-muon MuonBPark_fired_* flags cover the parking paths only) and their L3 objects are mostly absent
from TrigObj (objects need a filterBit and pT > 5), so the tags are not matched to trigger objects.
HLT_Mu8 is a prescaled Muon-PD path: ~5 events per ParkingSingleMuon file (the full stream is needed);
HLT_Mu4_L1DoubleMu fires in ~130 events per ParkingDoubleMuonLowMass file, 2/3 without the measured
path, so the stream presence is guaranteed by the tag path.

Outputs: $CMT_STORE/DoubleMuSFtnp2024/run3_2024/<dataset>/cat_base/DoubleMu_<stage>/<version>/histos_<n>.root
Commands:
    law run DoubleMuSFtnp2024 --version <v> --category-name base --config-name run3_2024 \\
        --dataset-name data_2024_singlemu --stage L1  [--families dxy,lxy] --workflow htcondor ...
    law run DoubleMuSFtnp2024 ... --dataset-name data_2024_doublemu --stage HLT ...
    law run DoubleMuSFtnp2024 ... --dataset-name BuToJpsiK --stage L1|HLT ...
"""
import luigi

from tasks.triggerscalefactor_2024 import TriggerSF2024, TriggerSFtnp2024, TRIGGERS_2024, FIRED_2024

# Dimuon L1 seeds of HLT_DoubleMu4_3_LowMass in 2024 (the doubleMuon__l1_conditions list of
# modules/muon_selection.py, with the fraction of the year each seed was active). Reference list.
ALL_DOUBLEMU_L1_SEEDS = [
    "L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",     # [84.5%] stable all year
    "L1_DoubleMu4p5_SQ_OS_dR_Max1p2",        # [61.0%] stable all year
    "L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",     # [60.5%] stable all year
    "L1_DoubleMu3er2p0_SQ_OS_dR_Max1p6",     # [34.7%] off in F-v2, H-v1
    "L1_DoubleMu4_SQ_OS_dR_Max1p2",          # [32.4%] off in F-v2, H-v1
    "L1_DoubleMu0er1p5_SQ_OS_dR_Max1p4",     # [24.0%]
    "L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",   # [15.4%] on from era E
    "L1_DoubleMu0er1p4_SQ_OS_dEta_Max1p2",
    "L1_DoubleMu5_SQ_OS_dR_Max1p6",
    "L1_DoubleMu0er1p5_SQ_OS_dEta_Max1p2",
    "L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",
    "L1_DoubleMu0er1p4_OQ_OS_dEta_Max1p6",
]

# The dominant seeds of the path (user 2026-11-06): the L1-stage probe condition
DOUBLEMU_L1_SEEDS = [
    "L1_DoubleMu4er2p0_SQ_OS_dR_Max1p6",
    "L1_DoubleMu0er1p4_SQ_OS_dR_Max1p4",
    "L1_DoubleMu4p5_SQ_OS_dR_Max1p2",
    "L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p5",
    "L1_DoubleMu0er2p0_SQ_OS_dEta_Max1p6",
]
L1_OR = "(" + " || ".join(DOUBLEMU_L1_SEEDS) + ")"

STAGES = {   # tag_cond: event-level condition of the tag; tag_pt: pT of the tag muon
    "L1": dict(tag_cond="HLT_Mu8", tag_label="HLT_Mu8", tag_pt=8.0, data_stream="singlemu"),
    "HLT": dict(tag_cond="HLT_Mu4_L1DoubleMu", tag_label="HLT_Mu4_L1DoubleMu", tag_pt=4.0, data_stream="doublemu"),
}
MEASURED = TRIGGERS_2024["DoubleMu"]           # HLT_DoubleMu4_3_LowMass
MEASURED_FLAG = FIRED_2024["DoubleMu"]         # MuonBPark_fired_HLT_DoubleMu4_3_LowMass


class DoubleMuSFtnp2024(TriggerSFtnp2024):
    stage = luigi.ChoiceParameter(choices=list(STAGES), default="L1",
        description="L1: eff(L1 seed OR | HLT_Mu8 tag); HLT: eff(HLT_DoubleMu4_3_LowMass | "
        "HLT_Mu4_L1DoubleMu tag); default: L1")
    trigger_case = luigi.ChoiceParameter(choices=["DoubleMu"], default="DoubleMu",
        description="fixed to DoubleMu (HLT_DoubleMu4_3_LowMass)")

    def __init__(self, *args, **kwargs):
        # skip TriggerSFtnp2024.__init__ (it refuses DoubleMu on the doublemu stream: not an issue here)
        super(TriggerSFtnp2024, self).__init__(*args, **kwargs)
        is_mc = getattr(getattr(self.dataset, "process", None), "isMC", False)
        stream = STAGES[self.stage]["data_stream"]
        if not is_mc and stream not in self.dataset_name.lower():
            raise ValueError(f"DoubleMuSFtnp2024 --stage {self.stage} runs on the {stream} stream "
                             f"(tag {STAGES[self.stage]['tag_label']}) or on MC, not on {self.dataset_name}")

    def store_parts(self):
        parts = super(DoubleMuSFtnp2024, self).store_parts()
        parts["trigger_case"] = f"DoubleMu_{self.stage}"
        return parts

    def add_to_root(self, root):
        super(DoubleMuSFtnp2024, self).add_to_root(root)   # tnp24trig (muonSV choice etc.)
        if getattr(type(self), "_declared_dm", False):
            return
        type(self)._declared_dm = True
        root.gInterpreter.Declare("""
            #include "DataFormats/Math/interface/deltaR.h"
            #include <cmath>
            namespace tnp24dm {
            using Vfloat = const ROOT::RVec<float>&;

            // muon within dR < 0.1 of a flagged MuonBPark muon
            bool matched_flag(float eta, float phi, int n, Vfloat b_eta, Vfloat b_phi, Vfloat flag)
            {
                for (int i = 0; i < n; i++)
                    if (flag[i] > 0 && reco::deltaR(eta, phi, b_eta[i], b_phi[i]) < 0.1) return true;
                return false;
            }

            // MuonBPark_matched_dr of the closest flagged MuonBPark muon (-999 if none); same role as
            // tnp24trig::muonBPark_matched_dR
            float matched_dr(float eta, float phi, int n, Vfloat b_eta, Vfloat b_phi, Vfloat flag, Vfloat b_mdr)
            {
                float best = 999999; int index = -1;
                for (int i = 0; i < n; i++) {
                    if (flag[i] <= 0) continue;
                    float dr = reco::deltaR(eta, phi, b_eta[i], b_phi[i]);
                    if (dr < best) { best = dr; index = i; }
                }
                return index >= 0 ? b_mdr.at(index) : -999.0;
            }

            // Same contract as tnp24trig::probe_values: (dxy, pt, pass, sip3d, |dxy|/err, eta) of the probe.
            // Tag = loose-ID muon matched to a MuonBPark muon with flag_TRIG (event bit && pT threshold).
            // Both muons tags -> the probe is the one with the larger |MuonBPark_matched_dr| (parent's rule).
            // pass = probe matched to a MuonBPark muon with flag_PROBE.
            ROOT::RVec<float> probe_values_kin(
                float m1_eta, float m1_phi, float m1_dxy, float m1_dxyErr, float m1_pt, float m1_sip3d, int m1_looseId,
                float m2_eta, float m2_phi, float m2_dxy, float m2_dxyErr, float m2_pt, float m2_sip3d, int m2_looseId,
                int n, Vfloat b_eta, Vfloat b_phi, Vfloat flag_TRIG, Vfloat flag_PROBE, Vfloat b_mdr)
            {
                ROOT::RVec<float> out(6);
                bool t1 = m1_looseId == 1 && matched_flag(m1_eta, m1_phi, n, b_eta, b_phi, flag_TRIG);
                bool t2 = m2_looseId == 1 && matched_flag(m2_eta, m2_phi, n, b_eta, b_phi, flag_TRIG);
                int probe = 1;
                if (t1 && t2) {
                    float d1 = std::abs(matched_dr(m1_eta, m1_phi, n, b_eta, b_phi, flag_TRIG, b_mdr));
                    float d2 = std::abs(matched_dr(m2_eta, m2_phi, n, b_eta, b_phi, flag_TRIG, b_mdr));
                    probe = (d1 > d2) ? 1 : 2;
                } else if (t1) {
                    probe = 2;
                } else {
                    probe = 1;
                }
                if (probe == 1) {
                    out.at(0) = m1_dxy; out.at(1) = m1_pt;
                    out.at(2) = matched_flag(m1_eta, m1_phi, n, b_eta, b_phi, flag_PROBE);
                    out.at(3) = m1_sip3d; out.at(4) = std::abs(m1_dxy) / m1_dxyErr; out.at(5) = m1_eta;
                } else {
                    out.at(0) = m2_dxy; out.at(1) = m2_pt;
                    out.at(2) = matched_flag(m2_eta, m2_phi, n, b_eta, b_phi, flag_PROBE);
                    out.at(3) = m2_sip3d; out.at(4) = std::abs(m2_dxy) / m2_dxyErr; out.at(5) = m2_eta;
                }
                return out;
            }
            } // namespace tnp24dm
        """)

    # ---- hooks ----------------------------------------------------------------------------------
    def define_trigger_flags(self, df):
        st = STAGES[self.stage]
        # event-level tag condition && pT above the threshold, per MuonBPark muon (the loose ID is required
        # on the Muon side in apply_tag_filter / probe_values_kin)
        df = df.Define("MuonBPark_fired_TRIG",
                       f"ROOT::RVec<float>(({st['tag_cond']} && MuonBPark_pt > {st['tag_pt']}))")
        if self.stage == "HLT":
            df = df.Define("MuonBPark_fired_PROBE", f"ROOT::RVec<float>({MEASURED_FLAG})")
        else:  # L1: the pass decision is the event-level seed OR (select_pass); flag unused
            df = df.Define("MuonBPark_fired_PROBE", "ROOT::RVec<float>(nMuonBPark, 1.f)")
        return df

    def apply_tag_filter(self, df):
        tag = "tnp24dm::matched_flag({m}_eta, {m}_phi, nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG)"
        return df.Filter(f"({tag.format(m='muon1')} && muon1_looseId == 1 && muon2_looseId == 1) || "
                         f"({tag.format(m='muon2')} && muon2_looseId == 1 && muon1_looseId == 1)")

    def define_probe(self, df):
        return df.Define("probe_quantities", "tnp24dm::probe_values_kin("
            "muon1_eta, muon1_phi, muon1_dxybs, muon1_dxyErr, muon1_pt, muon1_sip3d, muon1_looseId, "
            "muon2_eta, muon2_phi, muon2_dxybs, muon2_dxyErr, muon2_pt, muon2_sip3d, muon2_looseId, "
            "nMuonBPark, MuonBPark_eta, MuonBPark_phi, MuonBPark_fired_TRIG, MuonBPark_fired_PROBE, MuonBPark_matched_dr)")

    def select_pass(self, df):
        if self.stage == "L1":
            return df.Filter(L1_OR, "L1 dimuon seed OR")
        return df.Filter(f"probe_HLT == 1 && {MEASURED}", "probe fired " + MEASURED)

    def probe_eta_cut(self):
        return "abs(probe_eta) < 1.5"
