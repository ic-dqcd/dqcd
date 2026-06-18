// Direct GetEntries on a list of MergeCategorization files; accumulate per
// (dataset, category, prodtag). Usage: root -l -b -q 'count_merge_entries.C("filelist.txt")'
#include <TFile.h>
#include <TTree.h>
#include <fstream>
#include <map>
#include <string>

static std::string between(const std::string& s, const std::string& a, const std::string& b) {
    auto i = s.find(a); if (i == std::string::npos) return "";
    i += a.size(); auto j = s.find(b, i);
    return (j == std::string::npos) ? s.substr(i) : s.substr(i, j - i);
}

void count_merge_entries(std::string filelist) {
    std::ifstream in(filelist);
    std::string path;
    std::map<std::string, long long> tot;          // key: dataset\tcategory\tprod
    std::map<std::string, int> nfiles;
    long long done = 0;
    while (std::getline(in, path)) {
        if (path.empty()) continue;
        std::string ds   = between(path, "run3_2024_COMPLETE/", "/");
        std::string cat  = between(path, "/cat_", "/");
        std::string prod = between(path, "/prod", "/"); prod = "prod" + prod;
        std::string key = ds + "\t" + cat + "\t" + prod;
        long long n = 0;
        TFile* f = TFile::Open(path.c_str());
        if (f && !f->IsZombie()) {
            TTree* t = (TTree*) f->Get("Events");
            if (t) n = t->GetEntries();
        }
        if (f) f->Close();
        tot[key] += n;
        nfiles[key] += 1;
        if (++done % 250 == 0) fprintf(stderr, "  ...%lld files\n", done);
    }
    for (auto& kv : tot)
        printf("%s\t%d\t%lld\n", kv.first.c_str(), nfiles[kv.first], kv.second);
}
