from chdb import session
import pandas as pd
from pathlib import Path

class DL:
    """Reads the clickhouse, puts it into a pandas dataframe. Does preproscessing."""

    def __init__(self, model, config):
        self.model = model
        #self.path = path
        self.config = config
        pass

    def load(self):
        """load into a pd dataframe suitable for the model, according to cfg"""

        if self.config["dataloader"]["source"] == "chdb":
            db_path = Path(__file__).resolve().parent.parent / "data" / "chdb_data"
            sess = session.Session(str(db_path))
            df = sess.query("SELECT * FROM mydb.mytable", "DataFrame")

        if self.config["dataloader"]["source"] == "csv":
            df = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "csv")

        return df
