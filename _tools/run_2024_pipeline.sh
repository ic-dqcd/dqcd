#!/bin/bash
# Reference command chain for the 2024 analysis (documentation; adapt version/datasets/case).
#
# Which config each stage reads:
#   PreCounter      -> weights file: config/weights_2024.yaml (default for run3_2024 via
#                      add_default_module_files; computes puWeight + filter_efficiency on the raw
#                      nano for weights.total_events_weights, i.e. the normalisation denominator)
#   PreprocessRDF   -> modules file: config/modules_run3_efficienciesOnly_<CASE>.yaml
#                      (lumimask first [data only], selections incl. muonSV alpha < 2.8, puweight [MC])
#                      NOT defaulted: the file selects the trigger case, always pass it.
#                      Pass it as --Categorization-modules-file (Categorization forwards it to
#                      PreprocessRDF through vreq). --PreprocessRDF-modules-file is OVERRIDDEN to
#                      NO_STR when PreprocessRDF is reached via Categorization (checked with
#                      --print-deps), i.e. the skims would be produced with NO modules.
#   Categorization  -> feature modules: config/chi2_nobdt_sc{A,B1}_2024_<CASE>.yaml
#   FeaturePlot     -> weights.base = ["puWeight"] (config/run3_2024.py), "pu" systematic reads
#                      puWeightUp/puWeightDown (alias CMS_parking_pileup_2024)
#
# The pileup file/correction must be identical in weights_2024.yaml and the modules files.
# NB: _tools/run_MergeCategorization_{Mu10,DoubleMu}.sh still use --config-name run3_2024_COMPLETE.

set -e
CASE=${1:-Mu10orDoubleMu}      # Mu10 | DoubleMu | Mu10orDoubleMu
VERSION=${2:-prod_2024_${CASE}}
DATASETS=${3:-"scenarioA_mpi_4_mA_1p33_ctau_*,qcd*,data_2024_*_HalfPerMil"}

cd /home/hep/jtafoyav/vols/parking/nanoaod_base_analysis_13/dqcd
source setup.sh

law run MergeCategorizationWrapper \
    --version "${VERSION}" \
    --config-name run3_2024 \
    --category-names "base" \
    --dataset-names "${DATASETS}" \
    --PreCounter-weights-file weights_2024 \
    --Categorization-modules-file "modules_run3_efficienciesOnly_${CASE}" \
    --Categorization-feature-modules-file "chi2_nobdt_scA_2024_${CASE}" \
    --Categorization-base-category-name base \
    --MergeCategorization-workflow htcondor \
    --workers 40
