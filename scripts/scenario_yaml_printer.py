from config.ul_2018 import config

for pgn in config.process_group_names:
    if pgn.startswith("scenarioA"):
        print(pgn + ":")
        print("    singlev_cat3: False")
        print("    singlev_cat4: False")
        print("    singlev_cat5: True")
        print("    singlev_cat6: True")
        print("    multiv_cat1: True")
        print("    multiv_cat2: True")
        print("    multiv_cat3: True")
        print("    multiv_cat4: True")
        print("    multiv_cat5: True")
        print("    multiv_cat6: True")
        print()
