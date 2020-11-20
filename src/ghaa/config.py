import json
import os

def load_config(config_path=None):
    """Load config

    Parameters
    ----------
    config_path : str, optional
        path to config file - not necessary if running from a development
        installation (python setup.py develop)

    Returns
    -------
    config : dict
        configuration dictionary. Keys should include "base_path" for project
        data directory.
    """
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'config.json')

    with open(config_path) as fh:
        config = json.load(fh)

    return config
