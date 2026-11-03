#!/bin/bash
# 2024 trigger / muon-ID efficiency histograms (J/psi pass/fail per bin), 2024 ports of the 2018 tasks
#   law run TriggerSF --version prod_1710 --category-name base --config-name ul_2018 \
#       --dataset-name data_2018d --workflow htcondor --tasks-per-job 10
# Tasks (tasks/triggerscalefactor_2024.py), all on the raw nano (before preprocessing), golden JSON
# applied to data inside the task:
#   TriggerSF2024    <- TriggerSF          (pass/fail, no tag)
#   TriggerSFtnp2024 <- TriggerSFtnpRknew  (tag-and-probe trigger efficiency; 2018 lxy x pT SFs)
#   IDSFtnp2024      <- IDSFtnp            (tag-and-probe loose-ID efficiency; 2018 lxy x pT SFs)
# Each trigger is measured on its own parking stream:
#   Mu10     -> ParkingSingleMuon       (data_2024_singlemu_*)
#   DoubleMu -> ParkingDoubleMuonLowMass (data_2024_doublemu_*)
# For the MC efficiency, run the same command with --dataset-name qcd_<bin>.
# Outputs: $CMT_STORE/TriggerSF2024/run3_2024/<dataset>/cat_base/<trigger_case>/<version>/histos_<n>.root
set -e
VERSION=${1:-prod_2024_trigsf}

cd /home/hep/jtafoyav/vols/parking/nanoaod_base_analysis_13/dqcd
source setup.sh

for TASK in TriggerSF2024 TriggerSFtnp2024 IDSFtnp2024; do
    for DS in data_2024_singlemu_HalfPerMil data_2024_singlemu_HalfPerMil_epoch0; do
        law run ${TASK} --version "${VERSION}" --category-name base --config-name run3_2024 \
            --dataset-name "${DS}" --trigger-case Mu10 --workflow htcondor --tasks-per-job 10
    done
    for DS in data_2024_doublemu_HalfPerMil data_2024_doublemu_HalfPerMil_epoch0; do
        law run ${TASK} --version "${VERSION}" --category-name base --config-name run3_2024 \
            --dataset-name "${DS}" --trigger-case DoubleMu --workflow htcondor --tasks-per-job 10
    done
done
