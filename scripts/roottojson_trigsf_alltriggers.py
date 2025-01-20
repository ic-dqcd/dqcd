from copy import deepcopy as copy

# Valores del eje x (probe p_T [GeV])
x_values = [0.0, 6.0, 7.0, 8.0, 8.5, 9.0, 10.0, 10.5, 11.0, 12.0, 20.0, 100.0, float("inf")]

# Valores del eje y (probe |d/σ_xy|)
y_values = [0.0, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0, 20.0, 500.0, float("inf")]

data = {
    (20.0, 500.0): [0.179, 0.162, 0.261, 0.293, 0.754, 0.796, 0.802, 0.811, 0.968, 0.976],
    (10.0, 20.0): [0.157, 0.161, 0.266, 0.298, 0.757, 0.814, 0.820, 0.805, 0.975, 0.957],
    (8.0, 10.0): [0.156, 0.169, 0.268, 0.303, 0.761, 0.813, 0.804, 0.808, 0.970, 0.965],
    (6.0, 8.0):  [0.171, 0.170, 0.263, 0.295, 0.738, 0.787, 0.790, 0.778, 0.934, 0.938],
    (5.0, 6.0):  [0.133, 0.169, 0.259, 0.292, 0.642, 0.670, 0.665, 0.672, 0.770, 0.778],
    (4.0, 5.0):  [0.232, 0.169, 0.227, 0.249, 0.457, 0.476, 0.477, 0.482, 0.537, 0.529],
    (3.5, 4.0):  [0.185, 0.169, 0.174, 0.202, 0.313, 0.324, 0.336, 0.326, 0.377, 0.427],
    (3.0, 3.5):  [0.106, 0.154, 0.149, 0.152, 0.234, 0.254, 0.252, 0.257, 0.309, 0.361],
    (0.0, 3.0):  [0.316, 0.180, 0.121, 0.173, 0.286, 0.256, 0.260, 0.254, 0.335, 0.371],
}

errors = {
    (20.0, 500.0): [0.019, 0.001, 0.003, 0.003, 0.003, 0.006, 0.006, 0.005, 0.003, 0.009],
    (10.0, 20.0): [0.017, 0.001, 0.005, 0.003, 0.004, 0.008, 0.006, 0.007, 0.004, 0.019],
    (8.0, 10.0): [0.035, 0.003, 0.005, 0.005, 0.007, 0.012, 0.008, 0.012, 0.007, 0.020],
    (6.0, 8.0):  [0.036, 0.003, 0.005, 0.003, 0.006, 0.011, 0.012, 0.010, 0.007, 0.019],
    (5.0, 6.0):  [0.039, 0.003, 0.005, 0.002, 0.009, 0.015, 0.015, 0.014, 0.010, 0.026],
    (4.0, 5.0):  [0.084, 0.004, 0.007, 0.009, 0.014, 0.015, 0.014, 0.014, 0.008, 0.021],
    (3.5, 4.0):  [0.101, 0.008, 0.010, 0.012, 0.011, 0.018, 0.020, 0.017, 0.017, 0.033],
    (3.0, 3.5):  [0.072, 0.010, 0.011, 0.012, 0.011, 0.011, 0.020, 0.017, 0.017, 0.035],
    (0.0, 3.0):  [0.167, 0.012, 0.009, 0.012, 0.017, 0.017, 0.020, 0.017, 0.031, 0.028],
}

d = {
    "schema_version": 2,
    "corrections": [
        {
            "name": "scale_factor2D_trigger_absdxy_pt_TnP_2018_syst",
            "description": "scale_factor2D_trigger_absdxy_pt_TnP_2018_syst",
            "version": 1,
            "inputs": [
                {
                    "name": "pt",
                    "type": "real",
                    "description": "Probe pt"
                },
                {
                    "name": "dxysig",
                    "type": "real",
                    "description": "Probe dxysig"
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
                "input": "pt",
                "edges": x_values,
                "content": [],
                "flow": "error"
            }
        }
    ]
}


d_dxysig = {
    "nodetype": "binning",
    "input": "dxysig",
    "edges": y_values,
    "content": [],
    "flow": "error"
}

d_syst = {
    "nodetype": "category",
    "input": "ValType",
    "content": [
        {
            "key": "sf",
            "value": 0.
        },
        {
            "key": "systup",
            "value": 0.
        },
        {
            "key": "systdown",
            "value": 0.
        }
    ]
}


for ib in range(0, len(x_values) - 1):
    new_d_dxysig = copy(d_dxysig)
    for ib_y in range(len(y_values) - 1):
        new_d_syst = copy(d_syst)

        if ib == 0 or ib == len(x_values) - 1 or ib == len(x_values) - 2 or ib_y == len(y_values) - 2:
            new_d_syst["content"][0]["value"] = 0.
            new_d_syst["content"][1]["value"] = 0.
            new_d_syst["content"][2]["value"] = 0.
        else:
        
            bin_x = (y_values[ib_y], y_values[ib_y + 1])
        
            new_d_syst["content"][0]["value"] = data[bin_x][ib - 1]
            new_d_syst["content"][1]["value"] = data[bin_x][ib - 1] + errors[bin_x][ib - 1]
            new_d_syst["content"][2]["value"] = data[bin_x][ib - 1] - errors[bin_x][ib - 1]
            print(ib + 1, d["corrections"][0]["data"]["edges"][ib - 1], ib_y + 1, bin_x, data[bin_x][ib - 1], errors[bin_x][ib - 1])

        new_d_dxysig["content"].append(new_d_syst)

    d["corrections"][0]["data"]["content"].append(new_d_dxysig)


import json
with open("data/trigger_sf_alltriggers.json", "w+") as f:
    json.dump(d, f, indent=4)


