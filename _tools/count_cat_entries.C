// Sum Events-tree entries per category under a (dataset, prod) directory.
// Usage: root -l -b -q 'count_cat_entries.C("<dataset_dir>","<prodtag>")'
#include <TSystemDirectory.h>
#include <TList.h>
void count_cat_entries(std::string basedir, std::string prodtag) {
    const char* cats[] = {
        "cat_base",
        "cat_singlev_cat1","cat_singlev_cat2","cat_singlev_cat3",
        "cat_singlev_cat4","cat_singlev_cat5","cat_singlev_cat6",
        "cat_multiv_cat1","cat_multiv_cat2","cat_multiv_cat3",
        "cat_multiv_cat4","cat_multiv_cat5","cat_multiv_cat6"};
    printf("# %s  [%s]\n", basedir.c_str(), prodtag.c_str());
    for (auto c : cats) {
        std::string glob = basedir + "/" + c + "/" + prodtag + "/data_*.root";
        TChain ch("Events");
        int nf = ch.Add(glob.c_str());           // number of files matched
        long long n = (nf > 0) ? ch.GetEntries() : -1;
        printf("%-18s files=%-4d events=%lld\n", c, nf, n);
    }
}
