d = {
    "schema_version": 2,
    "corrections": [
        {
            "name": "NUM_LooseID_DEN_SAMuons_absdxy_pt_TnP_2018_syst",
            "description": "NUM_LooseID_DEN_SAMuons_absdxy_pt_TnP_2018_syst",
            "version": 1,
            "inputs": [
                {
                    "name": "absdxy",
                    "type": "real",
                    "description": "Probe dxy"
                },
                {
                    "name": "pt",
                    "type": "real",
                    "description": "Probe pt"
                },
                {
                    "name": "ValType",
                    "type": "string",
                    "description": "sf or syst (currently 'sf' is nominal, and 'systup' and 'systdown' are up/down variations with total stat+syst uncertainties"
                }
            ],
            "output": {
                "name": "weight",
                "type": "real",
                "description": "Output scale factor (nominal) or uncertainty"
            },
            "data": {
                "nodetype": "binning",
                "input": "absdxy",
                "edges": [
                    0.,
                    1e-1,
                    1.,
                    10.,
                    float("inf")
                ],
                "content": [],
                "flow": "error"
            }
        }
    ]
}


d_pt = {
    "nodetype": "binning",
    "input": "pt",
    "edges": [
        0.,
        4.,
        6.,
        10.,
        16.,
        float("inf")
    ],
    "content": [],
    "flow": "error"
}

d_syst = {
    "nodetype": "category",
    "input": "ValType",
    "content": [
        {
            "key": "sf",
            "value": 0
        },
        {
            "key": "systup",
            "value": 0
        },
        {
            "key": "systdown",
            "value": 0
        }
    ]
}

from copy import deepcopy as copy
from analysis_tools.utils import import_root
ROOT = import_root()
tf = ROOT.TFile.Open("data/scale_factor2D_id_lxy_pt_TnP_2018_syst_19Jun.root")
histo = tf.Get("scale_factors_2018")

for ib in range(len(d["corrections"][0]["data"]["edges"]) - 1):
    new_d_pt = copy(d_pt)
    for ibpt in range(len(new_d_pt["edges"]) - 1):
        new_d_syst = copy(d_syst)
        if d["corrections"][0]["data"]["edges"][ib] == 10.0:
            print("Filling dxy bins 10-inf with 1 +- 0.05")
            content = 1.
            error = 0.05
            new_d_syst["content"][0]["value"] = content
            new_d_syst["content"][1]["value"] = content + error
            new_d_syst["content"][2]["value"] = content - error
        else:
            content = histo.GetBinContent(ib + 1, ibpt + 1)
            error = histo.GetBinError(ib + 1, ibpt + 1)
            new_d_syst["content"][0]["value"] = content
            new_d_syst["content"][1]["value"] = content + error
            new_d_syst["content"][2]["value"] = content - error
        print(ib + 1, d["corrections"][0]["data"]["edges"][ib], ibpt + 1, new_d_pt["edges"][ibpt], content, error)
        new_d_pt["content"].append(new_d_syst)
    d["corrections"][0]["data"]["content"].append(new_d_pt)


import json
with open("data/scale_factor2D_NUM_LooseID_DEN_SAMuons_absdxy_pt_TnP_2018_syst.json", "w+") as f:
    json.dump(d, f, indent=4)
    

