#!/bin/bash
# MergeCategorization for the 2024 Mu10 trigger case, with config run3_2024.
# Usage: $0 <category> [scenario: A|B1, default A]
# PreCounter     -> config/weights_2024.yaml (pileup in the normalisation)
# PreprocessRDF  -> config/modules_run3_efficienciesOnly_HLT_Mu10_Barrel_L1HP11_IP6.yaml
#                   (lumi mask, alpha<2.8, puWeight); passed through Categorization, since
#                   --PreprocessRDF-modules-file is dropped via vreq (see run_2024_pipeline.sh)
# Categorization -> config/chi2_nobdt_sc<SCENARIO>_2024_Mu10.yaml
# NB: the scB1 BDT models are not on disk yet, so SCENARIO=B1 will fail at Categorization.
set -e

CATEGORY=$1
SCENARIO=${2:-A}
if [ -z "$CATEGORY" ]; then
    echo "Usage: $0 <category> [A|B1]"
    exit 1
fi

cd /home/hep/jtafoyav/vols/parking/nanoaod_base_analysis_13/dqcd
source setup.sh

law run MergeCategorizationWrapper \
    --version prod260120_SingleMuon_Mu10__WithQCD \
    --category-names "base,${CATEGORY}" \
    --config-name run3_2024 \
    --dataset-names "scenarioA_mpi_4_mA_1p33_ctau_*,scenarioA_mpi_4_mA_0p40_ctau_*,qcd*" \
    --PreCounter-weights-file weights_2024 \
    --Categorization-modules-file modules_run3_efficienciesOnly_HLT_Mu10_Barrel_L1HP11_IP6 \
    --Categorization-feature-modules-file chi2_nobdt_sc${SCENARIO}_2024_Mu10 \
    --MergeCategorization-workflow htcondor \
    --workers 40 \
    --Categorization-base-category-name base
