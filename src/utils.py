# src/utils.py

import yaml
import logging
import os
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_file=None):

    handlers = [logging.StreamHandler()]
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def load_config(config_path):

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    _validate_config(config)
    return config


def _validate_config(config):

    required_sections = ["selection", "binning", "gtlike", "model"]
    missing = [s for s in required_sections if s not in config]
    if missing:
        raise ValueError(
            f"Config file is missing required sections: {missing}\n"
            "Make sure your config.yaml follows the Fermipy format."
        )


def ensure_dirs(*paths):

    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def save_json(data, filepath):

    import json
    import numpy as np

    class _NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.floating, np.integer)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, bytes):
                return obj.decode("utf-8", errors="replace")
            if isinstance(obj, (set, tuple)):
                return list(obj)
            try:
                return str(obj)
            except Exception:
                return None

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4, cls=_NumpyEncoder)
    logging.getLogger(__name__).info(f"Saved JSON → {filepath}")
