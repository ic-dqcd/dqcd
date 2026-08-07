# Vector-portal filter efficiencies for 2024 -- DELIBERATELY EMPTY.
#
# No 2024 vector-portal samples exist yet: config/run3_2024.py has
# add_vp_grid_datasets_2024() commented out (~line 879), so nothing looks this up today.
#
# Empty rather than filled with 1.0 on purpose. The 2024 SCENARIO samples are known to
# have been produced without a generator filter, which is why
# modules/scenario_filter_effs_2024.py is all 1.0. Nobody has established that for a
# future vector-portal production. Leaving this empty means the first person to enable
# VP-2024 datasets gets the loud "no filter efficiency found" alert from
# modules/DQCD_SF.py, instead of silently inheriting an assumption that was only ever
# checked for a different sample set.
#
# To use: add "<process_name>": <efficiency> entries, exactly as in vp_filter_effs.py
# (keys look like "vector_m_0p3_ctau_100_xiO_1_xiL_1").

d = {
}
