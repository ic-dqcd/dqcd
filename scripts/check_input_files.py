from config.legacy_2018 import config

d = config.datasets.get("m_2_ctau_10_xiO_1_xiL_1")
df = config.datasets.get("m_2_ctau_10_xiO_1_xiL_1_friend")

def get_num(elem, end="."):
    return elem[elem.find("_") + 1 : elem.find(end)]

nd = [get_num(elem.split("/")[-1]) for elem in d.get_files()]
ndf = [get_num(elem.split("/")[-1], end="-icenet") for elem in df.get_files()]

for f in nd:
    if f not in ndf:
        print(f)


f = d.get_files()
f.sort()
for fil in f:
    print(fil)

f = df.get_files()
f.sort()
for fil in f:
    print(fil)