class DQCDBDTSelectionRDFProducer():
    def __init__(self, *args, **kwargs):
        self.bdt_name = kwargs.pop("bdt_name", "xgb0__m_2p0_ctau_10p0_xiO_1p0_xiL_1p0")

    def run(self, df):
        df = df.Filter("%s > 0." % self.bdt_name)
        return df, []


def DQCDBDTSelectionRDF(*args, **kwargs):
    return lambda: DQCDBDTSelectionRDFProducer(*args, **kwargs)