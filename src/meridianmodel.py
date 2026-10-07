import MMMAbs
import pandas as pd

from meridian.model import model as meridian_model




class Meridian(MMMAbs.MMMAbs):
    def __init__(self, df, config):

        super().__init__(df, config)

        self.model = None


    def fit(self):
        pass


    def getPrediction(self, ofWhat):
        pass


    def extractPosterior(self):
        pass


    def extractContributions(self):
        pass


    def extractResponseCurves(self):
        pass
