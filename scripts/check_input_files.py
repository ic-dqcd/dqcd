from config.legacy_2018 import config

for d in config.datasets:
    # if not d.name.startswith("qcd") or d.has_tag("friend"):
    if not d.name.startswith("data") or d.has_tag("friend"):
        continue
    print(d.name)
    # d = config.datasets.get("m_2_ctau_10_xiO_1_xiL_1")
    df = config.datasets.get(f"{d.name}_friend")

    def get_num(elem, end="."):
        return elem[elem.find("_") + 1 : elem.find(end)]

    nd = [get_num(elem.split("/")[-1]) for elem in d.get_files(check_empty=True)]
    ndf = [get_num(elem.split("/")[-1], end="-icenet") for elem in df.get_files(check_empty=True)]

    for f in nd:
        if f not in ndf:
            print(f)

    for f in ndf:
        if f not in nd:
            print(f)

    # f = d.get_files()
    # f.sort()
    # for fil in f:
        # print(fil)

    # f = df.get_files()
    # f.sort()
    # for fil in f:
        # print(fil)