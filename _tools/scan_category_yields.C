// Faithful per-category yield scan for sizing the "merging" (n_files_after_merging) values.
// Reproduces DQCDMuonSVSelectionRDF (neutral filtering + get_multivertices + remap to full
// indices + index fix) and DQCDFourMuonSVSelectionRDF (quadv), then classifies each event
// into singlev_cat1..6 / multiv_cat1..6 / quadv_cat1..6 exactly as run3_2024.add_categories.
// deltaR is inlined so it runs with a plain ROOT (no CMSSW headers).
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <set>
#include <cmath>
#include <algorithm>
#include <fstream>

using namespace ROOT::VecOps;
using Vf = const RVec<float>&;
using Vi = const RVec<int>&;

inline float mydr(float e1, float p1, float e2, float p2) {
    float de = e1 - e2; float dp = p1 - p2;
    while (dp > M_PI) dp -= 2 * M_PI;
    while (dp < -M_PI) dp += 2 * M_PI;
    return std::sqrt(de * de + dp * dp);
}

// faithful port of get_multivertices (operates on the NEUTRAL muonSV subset);
// returns the neutral-subset indices of the selected vertices and their chi2.
struct mv_t { RVec<int> idx; RVec<float> chi2; };
mv_t get_mv(Vf mass, Vf chi2, Vf m1e, Vf m1p, Vf m2e, Vf m2p, Vi m1i, Vi m2i) {
    int n = (int) chi2.size();
    RVec<int> mvidx; RVec<float> mvchi2;
    std::vector<std::pair<int,int>> pairs;
    for (int i = 0; i < n - 1; i++) {
        if (chi2[i] > 10 || m1e[i] == 0 || m2e[i] == 0 ||
                mydr(m1e[i], m1p[i], m2e[i], m2p[i]) > 1.2) continue;
        for (int j = i + 1; j < n; j++) {
            if (chi2[j] > 10 || m1e[j] == 0 || m2e[j] == 0 ||
                    mydr(m1e[i], m1p[i], m2e[i], m2p[i]) > 1.2) continue;  // (preserves original i-index dR)
            if ((std::fabs(mass[i] - mass[j]) / mass[i]) < 3 * 0.01 * mass[i]) {
                if (m1i[i] != m1i[j] && m1i[i] != m2i[j] && m2i[i] != m1i[j] && m2i[i] != m2i[j])
                    pairs.push_back({i, j});
            }
        }
    }
    std::vector<bool> valid(pairs.size(), true);
    for (int i = 0; i + 1 < (int) pairs.size(); i++) {
        if (!valid[i]) continue;
        for (int j = i + 1; j < (int) pairs.size(); j++) {
            if (!valid[j]) continue;
            if (pairs[i].first == pairs[j].first) {
                if (chi2[pairs[i].second] > chi2[pairs[j].second]) { valid[i] = false; break; }
                else valid[j] = false;
            } else if (pairs[i].second == pairs[j].second) {
                if (chi2[pairs[i].first] > chi2[pairs[j].first]) { valid[i] = false; break; }
                else valid[j] = false;
            }
        }
    }
    for (int i = 0; i < (int) pairs.size(); i++) {
        if (!valid[i]) continue;
        for (int e : {pairs[i].first, pairs[i].second})
            if (std::find(mvidx.begin(), mvidx.end(), e) == mvidx.end()) {
                mvidx.push_back(e); mvchi2.push_back(chi2[e]);
            }
    }
    if (mvidx.size() == 0) {
        RVec<int> id; RVec<float> c;
        for (int i = 0; i < n; i++) {
            if (chi2[i] > 10 || m1e[i] == 0 || m2e[i] == 0 ||
                    mydr(m1e[i], m1p[i], m2e[i], m2p[i]) > 1.2) continue;
            id.push_back(i); c.push_back(chi2[i]);
        }
        if (id.size() > 0) { auto mi = ArgMin(c); mvidx.push_back(id[mi]); mvchi2.push_back(c[mi]); }
    }
    return {mvidx, mvchi2};
}

int quadv_index(Vf f_chi2, Vi f_charge, Vi f1, Vi f2, Vi f3, Vi f4,
        Vf chi2, Vf mass, Vi charge, Vf e1, Vf p1, Vf e2, Vf p2, Vi i1, Vi i2) {
    for (size_t i = 0; i < f_chi2.size(); ++i) {
        if (f_chi2[i] >= 10 || f_charge[i] != 0) continue;
        RVec<int> fm = {f1[i], f2[i], f3[i], f4[i]};
        for (size_t a = 0; a < i1.size(); ++a) {
            if (charge[a] != 0 || chi2[a] >= 10) continue;
            if (mydr(e1[a], p1[a], e2[a], p2[a]) >= 1.2) continue;
            if (std::find(fm.begin(), fm.end(), i1[a]) == fm.end() ||
                    std::find(fm.begin(), fm.end(), i2[a]) == fm.end()) continue;
            for (size_t b = a + 1; b < i1.size(); ++b) {
                if (charge[b] != 0 || chi2[b] >= 10) continue;
                if (mydr(e1[b], p1[b], e2[b], p2[b]) >= 1.2) continue;
                if (std::find(fm.begin(), fm.end(), i1[b]) == fm.end() ||
                        std::find(fm.begin(), fm.end(), i2[b]) == fm.end()) continue;
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

int bin6(float dxy, float pa) {
    if (dxy < 1  && pa < 0.2) return 1;
    if (dxy < 1  && pa > 0.2) return 2;
    if (dxy > 1 && dxy < 10 && pa < 0.2) return 3;
    if (dxy > 1 && dxy < 10 && pa > 0.2) return 4;
    if (dxy > 10 && pa < 0.2) return 5;
    if (dxy > 10 && pa > 0.2) return 6;
    return 0;
}

// returns a code: 0 = no category (fails baseline); 1..6 singlev; 11..16 multiv; 21..26 quadv
int classify(
        Vi muonSV_charge, Vf muonSV_chi2, Vf muonSV_mass, Vf muonSV_dxy, Vf muonSV_pAngle,
        Vf muonSV_mu1eta, Vf muonSV_mu1phi, Vf muonSV_mu2eta, Vf muonSV_mu2phi,
        Vi muonSV_mu1index, Vi muonSV_mu2index,
        Vf f_chi2, Vi f_charge, Vi f1, Vi f2, Vi f3, Vi f4, Vf f_dxy, Vf f_pAngle) {
    // quadv takes priority
    int qi = quadv_index(f_chi2, f_charge, f1, f2, f3, f4, muonSV_chi2, muonSV_mass, muonSV_charge,
        muonSV_mu1eta, muonSV_mu1phi, muonSV_mu2eta, muonSV_mu2phi, muonSV_mu1index, muonSV_mu2index);
    if (qi >= 0) { int b = bin6(f_dxy[qi], f_pAngle[qi]); return b ? 20 + b : 0; }

    // neutral subset -> get_mv -> remap to full index
    RVec<int> neu;
    for (int i = 0; i < (int) muonSV_charge.size(); i++) if (muonSV_charge[i] == 0) neu.push_back(i);
    if (neu.empty()) return 0;
    auto take = [&](Vf v) { RVec<float> o; for (int k : neu) o.push_back(v[k]); return o; };
    auto takei = [&](Vi v) { RVec<int> o; for (int k : neu) o.push_back(v[k]); return o; };
    auto mv = get_mv(take(muonSV_mass), take(muonSV_chi2), take(muonSV_mu1eta), take(muonSV_mu1phi),
        take(muonSV_mu2eta), take(muonSV_mu2phi), takei(muonSV_mu1index), takei(muonSV_mu2index));
    if (mv.idx.empty()) return 0;                          // fails chi2_multivertices.size()>0
    int cat_index = (int) mv.idx.size() / 2;
    int min_chi2_full = neu[mv.idx[ArgMin(mv.chi2)]];      // remap to full collection
    int b = bin6(muonSV_dxy[min_chi2_full], muonSV_pAngle[min_chi2_full]);
    if (b == 0) return 0;
    return (cat_index == 0) ? b : 10 + b;
}

// cat_index over the neutral subset, independent of quadv: -1 if it fails the baseline
// (no neutral muonSV / get_mv returns nothing), else 0 (singlev) or >0 (multiv).
int cat_index_neutral(
        Vi muonSV_charge, Vf muonSV_chi2, Vf muonSV_mass,
        Vf muonSV_mu1eta, Vf muonSV_mu1phi, Vf muonSV_mu2eta, Vf muonSV_mu2phi,
        Vi muonSV_mu1index, Vi muonSV_mu2index) {
    RVec<int> neu;
    for (int i = 0; i < (int) muonSV_charge.size(); i++) if (muonSV_charge[i] == 0) neu.push_back(i);
    if (neu.empty()) return -1;
    auto take = [&](Vf v) { RVec<float> o; for (int k : neu) o.push_back(v[k]); return o; };
    auto takei = [&](Vi v) { RVec<int> o; for (int k : neu) o.push_back(v[k]); return o; };
    auto mv = get_mv(take(muonSV_mass), take(muonSV_chi2), take(muonSV_mu1eta), take(muonSV_mu1phi),
        take(muonSV_mu2eta), take(muonSV_mu2phi), takei(muonSV_mu1index), takei(muonSV_mu2index));
    if (mv.idx.empty()) return -1;
    return (int) mv.idx.size() / 2;
}

void scan_category_yields(std::string filelist, std::string label) {
    ROOT::EnableImplicitMT();
    TChain ch("Events");
    std::ifstream in(filelist);
    std::string line; int nf = 0;
    while (std::getline(in, line)) if (!line.empty()) { ch.Add(line.c_str()); nf++; }
    ROOT::RDataFrame df(ch);
    auto d = df.Define("code", classify,
        {"muonSV_charge","muonSV_chi2","muonSV_mass","muonSV_dxy","muonSV_pAngle",
         "muonSV_mu1eta","muonSV_mu1phi","muonSV_mu2eta","muonSV_mu2phi",
         "muonSV_mu1index","muonSV_mu2index",
         "fourmuonSV_chi2","fourmuonSV_charge","fourmuonSV_mu1index","fourmuonSV_mu2index",
         "fourmuonSV_mu3index","fourmuonSV_mu4index","fourmuonSV_dxy","fourmuonSV_pAngle"});
    // overlap diagnostic: is the event quadv, and what cat_index would it have (ignoring quadv)?
    d = d.Define("qidx_only", quadv_index,
            {"fourmuonSV_chi2","fourmuonSV_charge","fourmuonSV_mu1index","fourmuonSV_mu2index",
             "fourmuonSV_mu3index","fourmuonSV_mu4index","muonSV_chi2","muonSV_mass","muonSV_charge",
             "muonSV_mu1eta","muonSV_mu1phi","muonSV_mu2eta","muonSV_mu2phi","muonSV_mu1index","muonSV_mu2index"})
        .Define("catidx_only", cat_index_neutral,
            {"muonSV_charge","muonSV_chi2","muonSV_mass","muonSV_mu1eta","muonSV_mu1phi",
             "muonSV_mu2eta","muonSV_mu2phi","muonSV_mu1index","muonSV_mu2index"});
    auto n_tot = d.Count();
    auto h = d.Histo1D({"h","",30,-0.5,29.5}, "code");
    auto n_quadv      = d.Filter("qidx_only >= 0").Count();
    auto n_quadv_cat0 = d.Filter("qidx_only >= 0 && catidx_only == 0").Count();   // leaks into singlev w/o exclusion
    auto n_quadv_catN = d.Filter("qidx_only >= 0 && catidx_only >  0").Count();   // would be multiv
    printf("\n===== %s  (%d files) =====\n", label.c_str(), nf);
    printf("total events: %lld\n", (long long) *n_tot);
    auto C = [&](int c){ return (long long) h->GetBinContent(h->FindBin(c)); };
    printf("singlev cat1..6: "); for (int b=1;b<=6;b++) printf("%lld ", C(b)); printf("\n");
    printf("multiv  cat1..6: "); for (int b=1;b<=6;b++) printf("%lld ", C(10+b)); printf("\n");
    printf("quadv   cat1..6: "); for (int b=1;b<=6;b++) printf("%lld ", C(20+b)); printf("\n");
    printf("OVERLAP: quadv total=%lld  of which cat_index==0 (would-be singlev)=%lld, cat_index>0 (would-be multiv)=%lld\n",
        (long long)*n_quadv, (long long)*n_quadv_cat0, (long long)*n_quadv_catN);
}
