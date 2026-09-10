from abc import ABC, abstractmethod
import pandas as pd

class MMMAbs(ABC):
    """
        Abstract class for MMM wrapper. Meant to satisft req MMM-01 (framework-agnostic adapter interface for models).
    """
    def __init__(self, df):
        self.df = df
        self.fitted = False



    @abstractmethod
    def fit(self) -> None:
        """Fit the model on the provided dataframe"""
    
    @abstractmethod
    def getPrediction(self, ofWhat):
        """After fitting the model"""

    @abstractmethod
    def extractPosterior(self):
        """extract posterior"""

    @abstractmethod
    def extractContributions(self):
        """extract contributions"""

    @abstractmethod
    def extractResponseCurves(self):
        """extract response curves"""
