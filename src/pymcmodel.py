import MMMAbs
import pandas as pd

from pymc_marketing.mmm import (
    GeometricAdstock,
    LogisticSaturation,
    MMM,
)
from pymc_marketing.paths import data_dir




class PYMC(MMMAbs.MMMAbs):
    def __init__(self, X, y, config):

        super().__init__(X, y, config)
        
        self.mmm = MMM(
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
        self.mmm.fit(self.X, self.y, chains=4, target_accept=0.9)


    def getPrediction(self):
        pass


    def extractPosterior(self, ofWhat):
        self.mmm.sample_posterior_predictive(X, extend_idata=True, combined=True)
        self.mmm.plot_posterior_predictive(original_scale=True)


    def extractContributions(self):
        self.mmm.plot_components_contributions(original_scale=True)
        fig = self.mmm.plot_grouped_contribution_breakdown_over_time(...)

    def extractResponseCurves(self):
        pass

    def extractDiagnostics(self):
        pass
    


