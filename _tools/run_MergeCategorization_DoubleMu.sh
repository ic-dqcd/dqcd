#!/bin/bash
set -e

CATEGORY=$1
if [ -z "$CATEGORY" ]; then
    echo "Usage: $0 <category>"
    exit 1
fi

cd /home/hep/jtafoyav/vols/parking/nanoaod_base_analysis_13/dqcd
source setup.sh

law run MergeCategorizationWrapper \
    --version prod260120_DoubleMuon_4_3__WithQCD \
    --category-names "base,${CATEGORY}" \
    --config-name run3_2024_COMPLETE \
    --dataset-names "scenarioA_mpi_4_mA_1p33_ctau_*,scenarioA_mpi_4_mA_0p40_ctau_*,qcd*" \
    --MergeCategorization-workflow htcondor \
    --workers 40 \
    --Categorization-base-category-name base
