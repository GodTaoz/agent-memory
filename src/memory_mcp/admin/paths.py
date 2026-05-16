"""Helpers for resolving admin data file paths."""

from __future__ import annotations

import os
from pathlib import Path


DATA_DIR_NAME = "data"


def default_data_path(filename: str, env_var: str) -> Path:
    """Resolve a writable admin data path.

    Environment variables win when present. Otherwise persist under the current
    working directory's data/ directory so editable installs and packaged
    console-script launches behave the same way.
    """

    configured = os.environ.get(env_var)
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.cwd() / DATA_DIR_NAME / filename).resolve()
