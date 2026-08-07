#!/bin/bash
set -e

# compareDeltaR.py over the FULL samples: every QCD file of all 12 PT-hat bins
# (--n-qcd 0) and every file of all 6 signal mass points at both lifetimes
# (--n-signal 0). Nothing is a partial read, so the in-plot "Partial sample plot"
# legend should come out empty and the QCD curve needs no files_avail/files_read
# scale-up.

REPO=/home/hep/jtafoyav/vols/parking/nanoaod_base_analysis_13/dqcd
OUTPUT=$REPO/_tools/compareDeltaR_AllSamples.pdf
# where the other _tools/compare*.py plots get published
WEBDIR=/home/hep/jtafoyav/public_html/parking/2024/kinematic_checks

cd "$REPO"
source setup.sh

# setup.sh points X509_USER_PROXY at $CMT_BASE/x509up (on /vols, so the worker
# node can read it). Fail early with a clear message rather than after hours of
# xrootd timeouts if it has expired.
# Grid CA / VOMS paths come from the interactive login shell, not from setup.sh. A
# directly-submitted job inherits them via `getenv = True`, but set them explicitly
# anyway: several nodes in this pool have an empty /etc/grid-security/certificates,
# and without these every xrdfs listing fails.
export X509_CERT_DIR=${X509_CERT_DIR:-/cvmfs/grid.cern.ch/etc/grid-security/certificates}
export X509_VOMS_DIR=${X509_VOMS_DIR:-/cvmfs/grid.cern.ch/etc/grid-security/vomsdir}
export VOMS_USERCONF=${VOMS_USERCONF:-/cvmfs/grid.cern.ch/etc/grid-security/vomses}
[ -d "$X509_CERT_DIR" ] || { echo "[error] no CA dir at $X509_CERT_DIR"; exit 1; }

echo "[certs] $X509_CERT_DIR"
echo "[proxy] $X509_USER_PROXY"
# Best-effort only -- see run_compareDeltaR_shard.sh: some worker nodes lack
# /etc/grid-security/certificates, where voms-proxy-info fails on a valid proxy.
[ -s "$X509_USER_PROXY" ] || { echo "[error] proxy missing or empty: $X509_USER_PROXY"; exit 1; }
voms-proxy-info -timeleft -file "$X509_USER_PROXY" 2>/dev/null \
    || echo "[warn] voms-proxy-info unavailable on $(hostname -s) (no CA dir?); continuing"

echo "[run] $(date) starting compareDeltaR.py -> $OUTPUT"
python3 _tools/compareDeltaR.py --output "$OUTPUT" --n-qcd 0 --n-signal 0

echo "[run] $(date) done"

cp "$OUTPUT" "$WEBDIR/" && echo "[copy] published to $WEBDIR"
