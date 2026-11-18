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
#   Mu10     -> ParkingSingleMuon       (data_2024_singlemu_HalfPerMil)
#   DoubleMu -> ParkingDoubleMuonLowMass (data_2024_doublemu_HalfPerMil)
# TriggerSFtnp2024 runs for Mu10 only: the self-tag T&P is biased to ~1 for the dimuon path.
# HalfPerMil only (the *_epoch0 datasets are one file already contained in it). Statistics are
# low (~110 trigger probes per file over ~100 bins): first look; use *_1percent or the full
# streams for the measurement.
# For the MC efficiency, run the same command with --dataset-name qcd_<bin> (histograms are
# unweighted: normalise each QCD bin by xs/N_gen when merging).
# Outputs: $CMT_STORE/<task>/run3_2024/<dataset>/cat_base/<trigger_case>/<version>/histos_<n>.root
set -e
VERSION=${1:-prod_2024_trigsf}

cd /home/hep/jtafoyav/vols/parking/nanoaod_base_analysis_13/dqcd
source setup.sh

run() {  # task, dataset, trigger case
    law run "$1" --version "${VERSION}" --category-name base --config-name run3_2024 \
        --dataset-name "$2" --trigger-case "$3" --workflow htcondor --tasks-per-job 10
}

for TASK in TriggerSF2024 TriggerSFtnp2024 IDSFtnp2024; do
    run ${TASK} data_2024_singlemu_HalfPerMil Mu10
done
for TASK in TriggerSF2024 IDSFtnp2024; do
    run ${TASK} data_2024_doublemu_HalfPerMil DoubleMu
done
