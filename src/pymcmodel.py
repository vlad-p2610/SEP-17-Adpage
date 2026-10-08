import MMMAbs
import pandas as pd
from pymc_config import PyMCConfig
from pymc_marketing.mmm import GeometricAdstock, LogisticSaturation, MMM

from pymc_marketing.mmm import (
    GeometricAdstock,
    LogisticSaturation,
    MMM,
)


class PYMC(MMMAbs.MMMAbs):
    def __init__(self, df, config):
        # Accept the existing dictionary or already validated settings
        settings = config if isinstance(config, PyMCConfig) else PyMCConfig.from_mapping(config)
        super().__init__(df, config)
        self.pymc_config = settings
        # Target selection belongs in fit(), not in the predictor columns

        data_config = config["data"]
        pymc_config = config["pymc"]

        if pymc_config["adstock"]["type"] != "geometric":
            raise ValueError("Only geometric adstock is supported")

        if pymc_config["saturation"]["type"] != "logistic":
            raise ValueError("Only logistic saturation is supported")

        self.model = MMM(
            adstock=GeometricAdstock(l_max=settings.adstock_l_max),
            date_column=data_config["date_column"],
            target_column=data_config["target_column"],
            channel_columns=data_config["channel_columns"],
            control_columns=data_config["control_columns"] or None,
            adstock=GeometricAdstock(
                l_max=pymc_config["adstock"]["l_max"]
            ),
            saturation=LogisticSaturation(),
            date_column=settings.data.date_column,
            channel_columns=list(settings.data.channel_columns),
            control_columns=list(settings.data.control_columns) or None,
            yearly_seasonality=settings.yearly_seasonality,
            sampler_config=settings.sampler.as_kwargs(),
            yearly_seasonality=pymc_config["yearly_seasonality"],
            sampler_config=pymc_config["sampler"],
        )

    def fit(self) -> None:
        """Fit on prepared training rows for one company.
        pass

        The caller handles cleaning, chronological ordering and train/test
        splitting. Adstock and saturation are handled by the MMM model.
        """
        self.fitted = False
        if not isinstance(self.df, pd.DataFrame):
            raise ValueError("Training data must be a pandas DataFrame")
        if self.df.empty:
            raise ValueError("Training data must contain at least one row")
        if not self.df.columns.is_unique:
            raise ValueError("Training data must have unique column names")

        data = self.pymc_config.data
        predictors = [data.date_column, *data.channel_columns, *data.control_columns]
        required = [*predictors, data.target_column]
        missing = [column for column in required if column not in self.df.columns]
        if missing:
            raise ValueError(f"Training data is missing configured columns: {missing}")

        # Copies keep library-side changes away from the caller's dataframe
        X = self.df.loc[:, predictors].copy()
        y = self.df.loc[:, data.target_column].copy()
        self.model.fit(X=X, y=y)
        self.fitted = True

    def getPrediction(self, ofWhat):
        raise NotImplementedError("Prediction is not implemented yet")
        pass

    def extractPosterior(self):
        raise NotImplementedError("Posterior extraction is not implemented yet")
        pass

    def extractContributions(self):
        raise NotImplementedError("Contribution extraction is not implemented yet")
        pass

    def extractResponseCurves(self):
        raise NotImplementedError("Response curve extraction is not implemented yet")

    

        pass