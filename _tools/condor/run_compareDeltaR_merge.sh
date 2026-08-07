#!/bin/bash
set -e

# Merge the 13 shards written by run_compareDeltaR_shard.sh into the 5-page PDF and
# publish it. Reads no ROOT files and needs no grid proxy -- it only sums ~210 floats
# per sample -- so this is seconds of work.

REPO=/home/hep/jtafoyav/vols/parking/nanoaod_base_analysis_13/dqcd
SHARDDIR=$REPO/_tools/condor/shards
OUTPUT=$REPO/_tools/compareDeltaR_AllSamples.pdf
# where the other _tools/compare*.py plots get published
WEBDIR=/home/hep/jtafoyav/public_html/parking/2024/kinematic_checks

cd "$REPO"
source setup.sh

echo "[merge] $(date) shards in $SHARDDIR:"
ls -l "$SHARDDIR"

# --merge hard-fails if any of the 12 QCD bins is absent, so a shard that died takes
# the merge down with it rather than producing a plot with a quietly low QCD curve.
python3 _tools/compareDeltaR.py --merge "$SHARDDIR" --output "$OUTPUT"

cp "$OUTPUT" "$WEBDIR/" && echo "[copy] published to $WEBDIR"
echo "[merge] $(date) done"
