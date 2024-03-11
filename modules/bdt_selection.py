class DQCDBDTSelectionRDFProducer():
    def __init__(self, *args, **kwargs):
        self.bdt_name = kwargs.pop("bdt_name", "xgb0__m_2p0_ctau_10p0_xiO_1p0_xiL_1p0")
        self.bdt_cut_value = kwargs.pop("bdt_cut_value", 0.)

    def run(self, df):
        df = df.Filter(f"{self.bdt_name} > {self.bdt_cut_value}",
            f"{self.bdt_name} > {self.bdt_cut_value}")
        return df, []


def DQCDBDTSelectionRDF(*args, **kwargs):
    return lambda: DQCDBDTSelectionRDFProducer(*args, **kwargs)
