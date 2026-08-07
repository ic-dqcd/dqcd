#!/usr/bin/env python3
"""Shared golden-JSON lumisection mask for the _tools scripts that read DATA.

Single source of truth so every tool masks data the same way, with the same CLI and the
same default file. Use it as:

    import goldenjson as gj

    gj.add_args(parser)                     # --golden-json / --no-golden
    cert = gj.from_args(args, log)          # None when disabled or unavailable
    ...
    arrs = tree.arrays(branches + gj.BRANCHES, library="np")   # or "ak"
    keep = gj.mask(arrs["run"], arrs["luminosityBlock"], cert)

Why LUMISECTION level and not run level: uncertified lumisections sit INSIDE certified
runs. Measured on 2024 parking data (comparePileUp.py, 230M events), 2.6% of events fall
in uncertified lumisections and they are low-pileup enriched -- <N_PV> 29.7 against 36.1
for certified ones. A run-level test misses them entirely: 29% of runs are certified as
several disjoint intervals, and the runs that are NOT certified at all have perfectly
normal pileup. See _tools/plotGoldenJSON.py for the picture.

MC must NOT be masked -- it has no meaningful run/lumisection.
"""

import atexit
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN_JSON = os.path.join(HERE, "data", "Cert_Collisions2024_378981_386951_Golden.json")

# the two branches every caller must read alongside its own
BRANCHES = ["run", "luminosityBlock"]


def add_args(parser):
    """Attach --golden-json / --no-golden to an argparse parser."""
    parser.add_argument("--golden-json", default=GOLDEN_JSON,
                        help="Certified-lumisection JSON applied to DATA "
                             "(default: the 2024 golden cert in _tools/data)")
    parser.add_argument("--no-golden", action="store_true",
                        help="Do NOT apply the golden JSON -- use every data event")
    return parser


def load(path=GOLDEN_JSON, log=print):
    """{run: [(lo, hi), ...]}, or None if the file is missing."""
    if not path or not os.path.exists(path):
        return None
    with open(path) as fh:
        cert = json.load(fh)
    out = {int(r): [(int(a), int(b)) for a, b in v] for r, v in cert.items()}
    if log:
        n_ls = sum(b - a + 1 for v in out.values() for a, b in v)
        log(f"  golden JSON: {len(out)} runs, {n_ls:,} lumisections "
            f"({os.path.basename(path)})")
    return out


def from_args(args, log=print):
    """The mask implied by the parsed args: None when --no-golden, else the loaded JSON.

    Warns rather than dies when the file is absent, so a tool still runs -- but says
    loudly that it is using uncertified data."""
    if getattr(args, "no_golden", False):
        if log:
            log("  [--no-golden] data NOT filtered by the certification JSON")
        return None
    cert = load(getattr(args, "golden_json", GOLDEN_JSON), log=log)
    if cert is None and log:
        log(f"  [warn] no golden JSON at {getattr(args, 'golden_json', '')} "
            f"-- using ALL data events, including uncertified ones")
    return cert


def mask(runs, lumis, cert):
    """Per-event bool: is this (run, lumisection) certified?

    A run absent from the JSON is not certified, so every one of its events is dropped.
    """
    runs = np.asarray(runs)
    lumis = np.asarray(lumis)
    if cert is None:
        return np.ones(len(runs), dtype=bool)
    keep = np.zeros(len(runs), dtype=bool)
    for run in np.unique(runs):
        ranges = cert.get(int(run))
        if not ranges:
            continue
        sel = runs == run
        l = lumis[sel]
        m = np.zeros(len(l), dtype=bool)
        for lo, hi in ranges:
            m |= (l >= lo) & (l <= hi)
        keep[sel] = m
    return keep


# Every Counter registers itself so the tally is ALWAYS reported at exit. Reporting used
# to be left to each script, and every one of them forgot -- the filter ran correctly but
# silently, which is indistinguishable from not running at all.
_COUNTERS = []


def _report_at_exit():
    for c in _COUNTERS:
        if c.kept or c.dropped:
            print(f"[goldenjson] {c.summary()}", flush=True)


atexit.register(_report_at_exit)


class Counter:
    """Running tally of what the mask removed, reported automatically at exit."""

    def __init__(self, name="data"):
        self.name = name
        self.kept = 0
        self.dropped = 0
        _COUNTERS.append(self)

    def update(self, keep):
        n = int(np.size(keep))
        k = int(np.count_nonzero(keep))
        self.kept += k
        self.dropped += n - k
        return keep

    def summary(self):
        tot = self.kept + self.dropped
        if tot == 0:
            return "no data events read"
        return (f"golden JSON: kept {self.kept:,} of {tot:,} data events "
                f"({100.0 * self.dropped / tot:.2f}% dropped as uncertified)")
