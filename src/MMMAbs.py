from abc import ABC, abstractmethod
import pandas as pd

class MMMAbs(ABC):
    """
        Abstract class for MMM wrapper. Meant to provide modularity to the pipeline.
    """
    def __init__(self, df):
        self.df = df
        self.fitted = False

    @abstractmethod
    def fit(self) -> None:
        """Fit the model on the provided dataframe"""
        pass

    @abstractmethod
    def getPrediction(self, ofWhat):
        """After fitting the """
        pass
