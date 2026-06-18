// Estimate quadv vs multiv yields to size the "merging" (n_files_after_merging) values.
// Inline deltaR so it runs with a plain ROOT (no CMSSW headers needed).
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <set>
#include <cmath>
#include <algorithm>
#include <vector>
#include <string>

using namespace ROOT::VecOps;
using Vf = const RVec<float>&;
using Vi = const RVec<int>&;

inline float mydr(float e1, float p1, float e2, float p2) {
    float de = e1 - e2; float dp = p1 - p2;
    while (dp > M_PI) dp -= 2 * M_PI;
    while (dp < -M_PI) dp += 2 * M_PI;
    return std::sqrt(de * de + dp * dp);
}

// multiv (cat_index != 0) proxy: at least one mass-coherent neutral dimuon pair with
// distinct muons, chi2<10, dR<1.2, using the framework's reldiff < 0.03*mass condition.
int is_multiv(Vf chi2, Vf mass, Vi charge, Vf e1, Vf p1, Vf e2, Vf p2, Vi i1, Vi i2) {
    for (size_t a = 0; a < chi2.size(); ++a) {
        if (charge[a] != 0 || chi2[a] >= 10) continue;
        if (mydr(e1[a], p1[a], e2[a], p2[a]) >= 1.2) continue;
        for (size_t b = a + 1; b < chi2.size(); ++b) {
            if (charge[b] != 0 || chi2[b] >= 10) continue;
            if (mydr(e1[b], p1[b], e2[b], p2[b]) >= 1.2) continue;
            std::set<int> s = {i1[a], i2[a], i1[b], i2[b]};
            if (s.size() != 4) continue;
            float mA = mass[a], mB = mass[b];
            if (mA <= 0 || mB <= 0) continue;
            if (std::fabs(mA - mB) / mA < 3 * 0.01 * mA) return 1;
        }
    }
    return 0;
}

// quadv: returns selected fourmuonSV index (>=0) or -1 (exact production logic, 0.03 flat).
int quadv_index(Vf f_chi2, Vi f_charge, Vi f1, Vi f2, Vi f3, Vi f4,
        Vf chi2, Vf mass, Vi charge, Vf e1, Vf p1, Vf e2, Vf p2, Vi i1, Vi i2) {
    for (size_t i = 0; i < f_chi2.size(); ++i) {
        if (f_chi2[i] >= 10 || f_charge[i] != 0) continue;
        RVec<int> fourMuons = {f1[i], f2[i], f3[i], f4[i]};
        for (size_t a = 0; a < i1.size(); ++a) {
            if (charge[a] != 0 || chi2[a] >= 10) continue;
            if (mydr(e1[a], p1[a], e2[a], p2[a]) >= 1.2) continue;
            if (std::find(fourMuons.begin(), fourMuons.end(), i1[a]) == fourMuons.end() ||
                    std::find(fourMuons.begin(), fourMuons.end(), i2[a]) == fourMuons.end()) continue;
            for (size_t b = a + 1; b < i1.size(); ++b) {
                if (charge[b] != 0 || chi2[b] >= 10) continue;
                if (mydr(e1[b], p1[b], e2[b], p2[b]) >= 1.2) continue;
                if (std::find(fourMuons.begin(), fourMuons.end(), i1[b]) == fourMuons.end() ||
                        std::find(fourMuons.begin(), fourMuons.end(), i2[b]) == fourMuons.end()) continue;
                std::set<int> comb = {i1[a], i2[a], i1[b], i2[b]};
                if (comb.size() != 4) continue;
                float mA = mass[a], mB = mass[b];
                if (mA <= 0 || mB <= 0) continue;
                if (std::fabs(mA - mB) / mA < 0.03f) return (int) i;
            }
        }
    }
    return -1;
}

int quadv_bin(int idx, Vf f_dxy, Vf f_pAngle) {
    if (idx < 0) return 0;
    float d = f_dxy[idx], a = f_pAngle[idx];
    if (d < 1  && a < 0.2) return 1;
    if (d < 1  && a > 0.2) return 2;
    if (d > 1 && d < 10 && a < 0.2) return 3;
    if (d > 1 && d < 10 && a > 0.2) return 4;
    if (d > 10 && a < 0.2) return 5;
    if (d > 10 && a > 0.2) return 6;
    return 0;
}

void scan_quadv_yield(std::string filelist, std::string label) {
    ROOT::EnableImplicitMT();
    TChain ch("Events");
    std::ifstream in(filelist);
    std::string line; int nf = 0;
    while (std::getline(in, line)) { if (!line.empty()) { ch.Add(line.c_str()); nf++; } }
    ROOT::RDataFrame df(ch);

    auto d = df.Define("is_multiv", is_multiv,
            {"muonSV_chi2","muonSV_mass","muonSV_charge","muonSV_mu1eta","muonSV_mu1phi",
             "muonSV_mu2eta","muonSV_mu2phi","muonSV_mu1index","muonSV_mu2index"})
        .Define("qidx", quadv_index,
            {"fourmuonSV_chi2","fourmuonSV_charge","fourmuonSV_mu1index","fourmuonSV_mu2index",
             "fourmuonSV_mu3index","fourmuonSV_mu4index","muonSV_chi2","muonSV_mass","muonSV_charge",
             "muonSV_mu1eta","muonSV_mu1phi","muonSV_mu2eta","muonSV_mu2phi","muonSV_mu1index","muonSV_mu2index"})
        .Define("is_quadv", "qidx >= 0 ? 1 : 0")
        .Define("qbin", quadv_bin, {"qidx","fourmuonSV_dxy","fourmuonSV_pAngle"});

    auto n_tot   = d.Count();
    auto n_multiv = d.Filter("is_multiv == 1").Count();
    auto n_quadv = d.Filter("is_quadv == 1").Count();
    auto hbin = d.Filter("is_quadv == 1").Histo1D({"hbin","",7,-0.5,6.5}, "qbin");

    printf("\n===== %s  (%d files) =====\n", label.c_str(), nf);
    printf("total events : %lld\n", (long long)*n_tot);
    printf("multiv events: %lld\n", (long long)*n_multiv);
    printf("quadv events : %lld   (quadv/multiv = %.4f)\n",
        (long long)*n_quadv, *n_multiv ? (double)*n_quadv / *n_multiv : 0.);
    printf("quadv per bin (1..6): ");
    for (int b = 1; b <= 6; ++b) printf("%d=%lld  ", b, (long long)hbin->GetBinContent(hbin->FindBin(b)));
    printf("\n");
}
