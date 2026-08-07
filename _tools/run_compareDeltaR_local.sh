#!/bin/bash
# Full-sample compareDeltaR, run locally -- no condor.
#
# Runs the 13 shards (12 QCD PT-hat bins + all signal) a few at a time, then merges
# them into the PDF. Sequentially this is ~30 h; at 4 at a time it is ~8 h, while
# staying a reasonable citizen on a shared login node (4 cores, ~1 GB each).
#
# Resumable: a shard whose .npz already exists is skipped, so re-running after an
# interruption only redoes what is missing.
#
#   nohup bash _tools/run_compareDeltaR_local.sh > _tools/compareDeltaR_local.log 2>&1 &

# NB no `set -u`: setup.sh reads unset variables (CMT_ON_HTCONDOR and friends) and
# dies under it. No `set -e` either -- a single failed shard must not abort the rest.

REPO=/vols/cms/jtafoyav/parking/nanoaod_base_analysis_13/dqcd
# Overridable so a new shard FORMAT can be built without destroying the old set:
#   SHARDDIR=$REPO/_tools/shards_local_v3 bash _tools/run_compareDeltaR_local.sh
SHARDDIR=${SHARDDIR:-$REPO/_tools/shards_local}
OUTPUT=${OUTPUT:-$REPO/_tools/compareDeltaR_AllSamples.pdf}
WEBDIR=/home/hep/jtafoyav/public_html/parking/2024/kinematic_checks
NPAR=${NPAR:-4}

cd "$REPO"
source setup.sh

# See _tools/condor/run_compareDeltaR_shard.sh: these come from the login shell, and
# without them xrdfs cannot authenticate.
export X509_CERT_DIR=${X509_CERT_DIR:-/cvmfs/grid.cern.ch/etc/grid-security/certificates}
export X509_VOMS_DIR=${X509_VOMS_DIR:-/cvmfs/grid.cern.ch/etc/grid-security/vomsdir}
export VOMS_USERCONF=${VOMS_USERCONF:-/cvmfs/grid.cern.ch/etc/grid-security/vomses}

mkdir -p "$SHARDDIR"
echo "[local] $(date) starting, $NPAR shards at a time -> $SHARDDIR"

run_shard() {
    shard=$1
    if [ "$shard" = "signal" ]; then
        out=$SHARDDIR/signal.npz
        set -- --signal-only --n-signal 0
    else
        out=$SHARDDIR/qcd_$shard.npz
        set -- --qcd-bin "$shard" --n-qcd 0
    fi
    if [ -s "$out" ]; then
        echo "[skip] $(date +%H:%M:%S) $shard (already done)"
        return 0
    fi
    tmp=$SHARDDIR/.tmp_$$_$(basename "$out")
    echo "[start] $(date +%H:%M:%S) $shard"
    if python3 _tools/compareDeltaR.py "$@" --dump "$tmp" \
            > "$SHARDDIR/${shard}.log" 2>&1; then
        mv -f "$tmp" "$out"
        echo "[done]  $(date +%H:%M:%S) $shard"
    else
        rm -f "$tmp"
        echo "[FAIL]  $(date +%H:%M:%S) $shard -- see $SHARDDIR/${shard}.log"
        return 1
    fi
}
export -f run_shard
export SHARDDIR REPO

# Signal first (it is the quickest, so a broken proxy/CA surfaces in minutes rather
# than hours), then the QCD bins largest-first so the long pole starts earliest.
SHARDS=$(python3 - <<'PY'
import sys
sys.path.insert(0, "_tools")
import compareDeltaR as C
print("signal")
for n in ["QCD_Bin-PT-1000", "QCD_Bin-PT-600to800", "QCD_Bin-PT-15to20",
          "QCD_Bin-PT-800to1000", "QCD_Bin-PT-170to300", "QCD_Bin-PT-120to170",
          "QCD_Bin-PT-50to80", "QCD_Bin-PT-300to470", "QCD_Bin-PT-80to120",
          "QCD_Bin-PT-470to600", "QCD_Bin-PT-30to50", "QCD_Bin-PT-20to30"]:
    full = [k for k in C.QCD_XS if k.startswith(n + "_")]
    assert len(full) == 1, (n, full)
    print(full[0])
PY
)

printf '%s\n' $SHARDS | xargs -I{} -P "$NPAR" bash -c 'run_shard "$@"' _ {}
rc=$?

n=$(find "$SHARDDIR" -name '*.npz' | wc -l)
echo "[local] $(date) shards complete: $n/13 (xargs rc=$rc)"
if [ "$n" -ne 13 ]; then
    echo "[local] not merging -- $((13 - n)) shard(s) missing. Re-run this script to retry them."
    exit 1
fi

echo "[local] $(date) merging"
python3 _tools/compareDeltaR.py --merge "$SHARDDIR" --output "$OUTPUT"
cp "$OUTPUT" "$WEBDIR/" && echo "[local] published to $WEBDIR"
echo "[local] $(date) DONE -> $OUTPUT"
