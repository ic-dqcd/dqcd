#!/bin/bash
set -e

# One shard of the full-sample compareDeltaR run.
#   $1 = "signal"                       -> every file of all 6 signal mass points
#   $1 = "minbias"                      -> the MinBias fraction (--minbias-frac, 5%)
#   $1 = <QCD PT-hat bin directory>     -> every file of that one bin
# Writes only the shard's histograms (~2 kB); _tools/condor/run_compareDeltaR_merge.sh
# turns the 14 shards into the PDF.

SHARD=$1
if [ -z "$SHARD" ]; then
    echo "Usage: $0 <signal|minbias|QCD_Bin-PT-...>"
    exit 1
fi

REPO=/home/hep/jtafoyav/vols/parking/nanoaod_base_analysis_13/dqcd
SHARDDIR=$REPO/_tools/condor/shards

cd "$REPO"
source setup.sh

# Grid CA / VOMS paths. These normally come from the interactive login shell, NOT from
# setup.sh -- and `getenv = True` in the .sub captures the environment of whatever
# submitted the job, which under DAGMan is DAGMan's environment, not yours. Without
# them a worker node falls back to /etc/grid-security/certificates, which is empty on
# several nodes in this pool, and every xrdfs listing fails. Set them explicitly, but
# let an already-set value win.
export X509_CERT_DIR=${X509_CERT_DIR:-/cvmfs/grid.cern.ch/etc/grid-security/certificates}
export X509_VOMS_DIR=${X509_VOMS_DIR:-/cvmfs/grid.cern.ch/etc/grid-security/vomsdir}
export VOMS_USERCONF=${VOMS_USERCONF:-/cvmfs/grid.cern.ch/etc/grid-security/vomses}
[ -d "$X509_CERT_DIR" ] || { echo "[error] no CA dir at $X509_CERT_DIR"; exit 1; }

echo "[certs] $X509_CERT_DIR"
echo "[proxy] $X509_USER_PROXY"
# Only the file's existence is checked hard. voms-proxy-info needs the CA directory
# /etc/grid-security/certificates, which some worker nodes in this pool do not have --
# there it exits non-zero on a perfectly good proxy, and under `set -e` that killed the
# job before it read a single file (clusters 4623825/4623826). So the validity check is
# best-effort and must never be fatal.
[ -s "$X509_USER_PROXY" ] || { echo "[error] proxy missing or empty: $X509_USER_PROXY"; exit 1; }
voms-proxy-info -timeleft -file "$X509_USER_PROXY" 2>/dev/null \
    || echo "[warn] voms-proxy-info unavailable on $(hostname -s) (no CA dir?); continuing"

mkdir -p "$SHARDDIR"

if [ "$SHARD" = "signal" ]; then
    OUT=$SHARDDIR/signal.npz
    ARGS=(--signal-only --n-signal 0)
elif [ "$SHARD" = "minbias" ]; then
    # No --minbias-frac override: the script's own 5% default IS the intended
    # configuration, and pinning a different value here would silently disagree with
    # what every non-sharded run of the same script produces.
    OUT=$SHARDDIR/minbias.npz
    ARGS=(--minbias-only)
else
    OUT=$SHARDDIR/qcd_$SHARD.npz
    ARGS=(--qcd-bin "$SHARD" --n-qcd 0)
fi

# Dump to a temporary name and rename only on success: a job killed mid-write would
# otherwise leave a truncated .npz that the merge step would either choke on or,
# worse, silently mis-read.
TMP=$SHARDDIR/.tmp_$$_$(basename "$OUT")

echo "[run] $(date) shard=$SHARD -> $OUT"
python3 _tools/compareDeltaR.py "${ARGS[@]}" --dump "$TMP"
mv -f "$TMP" "$OUT"
echo "[run] $(date) done -> $OUT"
