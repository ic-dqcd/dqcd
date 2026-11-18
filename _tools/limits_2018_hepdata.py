#!/usr/bin/env python3
"""
HEPData ins3083980 (2018 DQCD search, 41.6/fb) -> plain-text limit files, scenarios A and B1, one per m_A'.

Input: the CSV bundle https://www.hepdata.net/download/submission/ins3083980/1/csv (a .tar.gz), unpacked.
Output: limits_2018/limits_2018_HEPData_sc<A|B1>_mA<m>.txt with columns
    ctau_mm observed expected exp68_down exp68_up exp95_down exp95_up   (absolute BR(H->psi psi) values)
Usage: limits_2018_hepdata.py <unpacked csv dir> [--out limits_2018]
"""
import argparse, glob, os, re


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "limits_2018"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for sc in ("A", "B1"):
        for f in sorted(glob.glob(f"{a.src}/Scenario{sc}limits,m_{{A'}}=*GeV.csv")):
            mA = re.search(r"=([\d.]+)GeV", f).group(1)
            txt = open(f).read()
            doi = re.search(r"table_doi: (\S+)", txt).group(1)
            desc = re.search(r"description: (.*)", txt).group(1)
            mpi = re.search(r"m_\{\\tilde\{\\pi\}_\{3\}\}=(\d+)", desc).group(1)
            brmm = re.search(r"\\mu\\mu\)=([\d.]+)", desc).group(1)
            obs, exp, block = {}, {}, None
            for line in txt.splitlines():
                if line.startswith("#: Limit,"):
                    block = line.split(",")[1].strip()
                    continue
                if not line or line.startswith("#") or line.startswith("$"):
                    continue
                v = [float(x) for x in line.split(",")]
                (obs if block == "Observed" else exp)[v[0]] = v[1:]
            cts = sorted(set(obs) | set(exp))
            name = os.path.join(a.out, f"limits_2018_HEPData_sc{sc}_mA{mA.replace('.', 'p')}.txt")
            with open(name, "w") as o:
                o.write(f"# 2018 DQCD search (41.6 fb-1, 13 TeV), HEPData ins3083980 v1, {doi}\n")
                o.write(f"# scenario {sc}, m_pi3 = {mpi} GeV, m_A' = {mA} GeV, BR(A'->mumu) = {brmm}\n")
                o.write("# 95% CL upper limits on BR(H -> psi psi); band columns are absolute values (median +/- HEPData errors)\n")
                o.write("# columns: ctau_mm observed expected exp68_down exp68_up exp95_down exp95_up\n")
                for ct in cts:
                    e = exp.get(ct)
                    ob = obs[ct][0] if ct in obs else float("nan")
                    if e:
                        med, p1, m1, p2, m2 = e
                        vals = [med, med + m1, med + p1, med + m2, med + p2]
                    else:
                        vals = [float("nan")] * 5
                    o.write(f"{ct:8.3g} {ob:11.5g} " + " ".join(f"{x:11.5g}" for x in vals) + "\n")
            print(name, len(cts), "ctau points")


if __name__ == "__main__":
    main()
