import MMMAbs
import pandas as pd

from pymc_marketing.mmm import (
    GeometricAdstock,
    LogisticSaturation,
    MMM,
)
from pymc_marketing.paths import data_dir




class PYMC(MMMAbs.MMMAbs):
    def __init__(self, df):

        super().__init__(df)
        
        self.model = MMM(
            adstock=GeometricAdstock(l_max=8),
            saturation=LogisticSaturation(),
            date_column="date_week",
            channel_columns=["x1", "x2"],
            control_columns=[
                "event_1",
                "event_2",
                "t",
            ],
            yearly_seasonality=2,
        )

    def fit(self):
        pass

    def getPrediction(self):
        pass

    def extractPosterior(self, ofWhat):
        pass

    def extractContribution(self):
        pass

    def extractContributions(self):
        pass

    def extractResponseCurves(self):
        pass

    


