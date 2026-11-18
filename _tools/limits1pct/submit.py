#!/usr/bin/env python3
"""
Stage 1 driver: submit select_events.py to HTCondor for the 1% data of a trigger case plus the signal points of
config/scenario{A,B1}.yaml. Re-running it only submits groups whose output is missing (rescue mode).

  submit.py --case Mu10 [--scenarios A,B1] [--tag v2] [--files-per-job 5] [--dry-run] [--split-missing]
  submit.py --case Mu10 --tag v2_nobdt --no-signal --min-bdt -1     # full preselected data spectrum (BDT WPs)
  submit.py --case Mu10 --tag v2_qcd --qcd --no-data --no-signal --min-bdt -1 --priority 5
                                                                    # QCD MC background (make_limits.py --bkg qcd)

Outputs: $CMT_STORE/Limits1pct/<tag>/<case>/<dataset>/part_<i>.root  and  .../<case>/data_dirs.json
--split-missing: resubmit missing data groups one file per job (to isolate corrupt files after a first pass).

The "1%" of data
----------------
config/run3_2024.py defines data_2024_{singlemu,doublemu}_1percent as the files nano_1..nano_15 of every CRAB task
directory below ParkingSingleMuon0-11 / ParkingDoubleMuonLowMass0-7 (file_pattern "nano_([1-9]|1[0-5]).root").
On dcache most (primary dataset, era) pairs were produced SEVERAL times (CRAB task dirs with different timestamps,
2025-10-07 / 2025-11-19 / 2025-12-21 / 2026-02..04): the later complete productions are byte-identical copies, the
early ones are partial. Reading all of them (what the framework datasets do) duplicates events 2-4x in many eras.
Here ONE directory per (dataset, era) is used: the one with most files (ties -> latest timestamp), and the 1% is
nano_1..15 of that directory. The per-directory file counts are written to data_dirs.json so that make_limits.py can
weight each directory's events by n_total/n_read, i.e. scale the 1% up to the full 2024 dataset era by era.
"""
import argparse, glob, json, os, re, subprocess, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
XRD = "gfe02.grid.hep.ph.ic.ac.uk"
SAMPLE_BASE = "/pnfs/hep.ph.ic.ac.uk/data/cms/store/user/tafoyava/samples/bParking/2024/"
DATA = {"Mu10": "data_2024_singlemu_1percent", "DoubleMu": "data_2024_doublemu_1percent"}
DATA_FULL = {"Mu10": "data_2024_singlemu", "DoubleMu": "data_2024_doublemu"}          # cached full lists
# Mu-enriched pT-binned QCD MC (config/run3_2024.py datasets qcd_<bin>); file lists = the cached $CMT_TMP_DIR ones
QCD_BINS = ["15to20", "20to30", "30to50", "50to80", "80to120", "120to170", "170to300", "300to470", "470to600",
            "600to800", "800to1000", "1000toInf"]
DATA_FOLDERS = {"Mu10": [f"ParkingSingleMuon{i}" for i in range(12)],
                "DoubleMu": [f"ParkingDoubleMuonLowMass{i}" for i in range(8)]}        # run3_2024.py:792-848
ONEPCT_RE = re.compile(r"nano_([1-9]|1[0-5])\.root$")                                  # file_pattern (fullmatch)
CRAB_DIR_RE = re.compile(r"^(.*)/\d{4}/nano_\d+\.root$")
LUMI_FULL_PB = 109950.   # 2024 C-I, run3_2024.py lumi_pb


def signal_points(scen):
    with open(os.path.join(REPO, "config", f"scenario{scen}.yaml")) as f:
        return re.findall(r"^(scenario\S+?):", f.read(), flags=re.M)


def xrdfs_ls(folder):
    out = subprocess.run(["xrdfs", XRD, "ls", "-R", folder], capture_output=True, text=True).stdout
    return [l.strip() for l in out.splitlines() if re.search(r"/nano_\d+\.root$", l)]


def cached_list(tmp_dir, name):
    cache = os.path.join(tmp_dir, "run3_2024", name + ".txt")
    if os.path.exists(cache):
        return [l.strip() for l in open(cache) if l.strip()]
    return None


def signal_files(name, tmp_dir):
    """Same source as dataset.get_files: the cached $CMT_TMP_DIR list, else xrdfs ls of the dcache folder."""
    files = cached_list(tmp_dir, name)
    if files is None:
        sys.path.insert(0, os.path.join(REPO, "config"))
        from datasets_scenario_2024 import d as SIGNALS
        files = xrdfs_ls(SAMPLE_BASE + SIGNALS[name].split("/")[1])
    return sorted(f"root://{XRD}/" + f if not f.startswith("root://") else f for f in files)


def data_dirs(case, tmp_dir, bad):
    """One CRAB task directory per (primary dataset, era); its nano_1..15 files minus the known-bad ones."""
    full = cached_list(tmp_dir, DATA_FULL[case])
    if full is None:
        print(f"no cached full list for {DATA_FULL[case]}, listing dcache (slow) ...")
        full = sum((xrdfs_ls(SAMPLE_BASE + d) for d in DATA_FOLDERS[case]), [])
    full = [f.split(XRD + "/")[-1] if "://" in f else f for f in full]
    by_dir = defaultdict(list)
    for f in full:
        m = CRAB_DIR_RE.match(f)
        if m:
            by_dir[m.group(1)].append(f)
    groups = defaultdict(list)
    for d in by_dir:
        rel = d[len(SAMPLE_BASE):].split("/")
        if rel[0] not in DATA_FOLDERS[case] or len(rel) != 3:
            continue
        groups[(rel[0], rel[1])].append(d)
    dirs = []
    for key in sorted(groups):
        cands = sorted(groups[key], key=lambda d: (len(by_dir[d]), d))     # most files, then latest timestamp
        canon = cands[-1]
        onepct = sorted(f for f in by_dir[canon] if ONEPCT_RE.search(f))
        dirs.append({"id": len(dirs), "dataset": key[0], "era": key[1], "dir": canon,
                     "n_total": len(by_dir[canon]), "n_1pct": len(onepct),
                     "files": [f for f in onepct if f not in bad],
                     "duplicates": {d.rsplit("/", 1)[1]: len(by_dir[d]) for d in cands[:-1]}})
    return dirs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=list(DATA))
    ap.add_argument("--scenarios", default="A,B1")
    ap.add_argument("--tag", default="v2")
    ap.add_argument("--files-per-job", type=int, default=5)
    ap.add_argument("--sig-files-per-job", type=int, default=10)
    ap.add_argument("--no-data", action="store_true")
    ap.add_argument("--no-signal", action="store_true")
    ap.add_argument("--qcd", action="store_true", help="also select the 12 Mu-enriched QCD MC pT bins (background)")
    ap.add_argument("--qcd-files-per-job", type=int, default=20)
    ap.add_argument("--priority", type=int, default=0, help="condor job priority (higher runs first among own jobs)")
    ap.add_argument("--split-missing", action="store_true")
    ap.add_argument("--exclude", default=os.path.join(HERE, "bad_files.txt"),
                    help="files known to be unreadable (one per line)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-bdt", type=float, default=0.6, help="select_events.py --min-bdt (-1: no BDT cut)")
    a = ap.parse_args()

    store = os.path.join(os.environ["CMT_STORE"], "Limits1pct", a.tag, a.case)
    tmp_dir = os.environ["CMT_TMP_DIR"]
    bad = set()
    if os.path.exists(a.exclude):
        bad = {l.strip() for l in open(a.exclude) if l.strip() and not l.startswith("#")}

    groups = []   # (dataset, is_mc, part, files, dir_ids)
    if not a.no_data:
        dirs = data_dirs(a.case, tmp_dir, bad)
        os.makedirs(store, exist_ok=True)
        info = {"case": a.case, "dataset": DATA[a.case], "lumi_full_pb": LUMI_FULL_PB,
                "n_total": sum(d["n_total"] for d in dirs), "n_submitted": sum(len(d["files"]) for d in dirs),
                "dirs": dirs}
        with open(os.path.join(store, "data_dirs.json"), "w") as f:
            json.dump(info, f, indent=1)
        ndup = sum(1 for d in dirs if d["duplicates"])
        print(f"data: {len(dirs)} (dataset, era) directories ({ndup} had duplicate productions, ignored), "
              f"{info['n_total']} files in total, {info['n_submitted']} in the 1% "
              f"({100. * info['n_submitted'] / info['n_total']:.3f} %), {len(bad)} excluded as bad")
        flat = [(f"root://{XRD}/" + f, d["id"]) for d in dirs for f in d["files"]]
        n = a.files_per_job
        for i in range(0, len(flat), n):
            chunk = flat[i:i + n]
            groups.append((DATA[a.case], False, i // n, [c[0] for c in chunk], [c[1] for c in chunk]))
    if not a.no_signal:
        for scen in a.scenarios.split(","):
            for sig in signal_points(scen):
                files = signal_files(sig, tmp_dir)
                n = a.sig_files_per_job
                for i in range(0, len(files), n):
                    groups.append((sig, True, i // n, files[i:i + n], None))

    if a.qcd:
        for b in QCD_BINS:
            files = cached_list(tmp_dir, f"qcd_{b}")
            if files is None:
                sys.exit(f"no cached file list for qcd_{b} in {tmp_dir}/run3_2024")
            files = sorted(f"root://{XRD}/" + f if not f.startswith("root://") else f for f in files)
            n = a.qcd_files_per_job
            for i in range(0, len(files), n):
                groups.append((f"qcd_{b}", True, i // n, files[i:i + n], None))

    todo = []
    for ds, mc, part, files, ids in groups:
        out = os.path.join(store, ds, f"part_{part}.root")
        if os.path.exists(out):
            continue
        if a.split_missing and not mc and len(files) > 1:
            # split a failed group into single files: part_<i>_<j>
            for j, f in enumerate(files):
                o = os.path.join(store, ds, f"part_{part}_{j}.root")
                if not os.path.exists(o):
                    todo.append((ds, mc, o, [f], [ids[j]]))
            continue
        todo.append((ds, mc, out, files, ids))
    print(f"{len(groups)} groups, {len(todo)} to submit -> {store}")
    if not todo or a.dry_run:
        for t in todo[:5]:
            print("  e.g.", t[0], t[2], len(t[3]), "files", "dir ids", t[4])
        return

    jobdir = os.path.join(store, "condor"); os.makedirs(jobdir, exist_ok=True)
    # one job per line of the jobs file, indexed by $(Process): condor's "queue ... from <file>" splits lines
    # on commas as well as whitespace, which breaks the comma-joined file lists
    jobs_file = os.path.join(jobdir, f"jobs_{os.getpid()}.txt")
    with open(jobs_file, "w") as f:
        for ds, mc, out, files, ids in todo:
            f.write(f"{ds} {'--mc' if mc else '-'} {out} {','.join(files)} "
                    f"{','.join(str(i) for i in ids) if ids else '-'}\n")
    wrapper = os.path.join(jobdir, "run.sh")
    with open(wrapper, "w") as f:
        f.write(f"""#!/bin/bash
# $1 jobs file, $2 0-based job index. Line fields: dataset, --mc or -, output, comma-separated input files,
# comma-separated dir ids (data) or -
read -r DS MC OUT FILES IDS < <(sed -n "$(( $2 + 1 ))p" "$1")
cd {REPO}
source setup.sh > /dev/null 2>&1
export OMP_NUM_THREADS=1 NTHREADS=1
[ "$MC" = "--mc" ] || MC=""
[ "$IDS" = "-" ] && IDS="" || IDS="--dir-ids $IDS"
timeout 10000 python3 {HERE}/select_events.py --case {a.case} --dataset $DS $MC $IDS --min-bdt {a.min_bdt} --out $OUT ${{FILES//,/ }}
""")
    os.chmod(wrapper, 0o755)
    sub = os.path.join(jobdir, f"submit_{os.getpid()}.sub")
    with open(sub, "w") as f:
        f.write(f"""universe = vanilla
executable = {wrapper}
arguments = {jobs_file} $(Process)
getenv = true
output = /dev/null
error = {jobdir}/err_$(Cluster)_$(Process).txt
log = /dev/null
request_cpus = 1
request_memory = 2000
priority = {a.priority}
+MaxRuntime = 10799
x509userproxy = {os.environ.get('X509_USER_PROXY', '')}
queue {len(todo)}
""")
    print(subprocess.run(["condor_submit", sub], capture_output=True, text=True).stdout.strip())


if __name__ == "__main__":
    main()
