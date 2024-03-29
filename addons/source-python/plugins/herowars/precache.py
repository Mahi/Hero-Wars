# Source.Python imports
from engines.precache import Model


_models = {}


def get_model(name: str) -> Model:
    """Get a model for a name."""
    return _models.setdefault(name, Model(name))
