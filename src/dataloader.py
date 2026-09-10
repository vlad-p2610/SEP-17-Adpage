

class DL:
    """Reads the clickhouse, puts it into a pandas dataframe. Does preproscessing."""

    def __init__(self, model, path, config):
        self.model = model
        self.path = path
        self.config = config
        pass

    def load(self):
        """load into a pd dataframe suitable for the model, according to cfg"""
        pass