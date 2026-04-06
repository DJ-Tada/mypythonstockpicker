"""stockpicker – core library for MyPythonStockPicker."""

import os
from pathlib import Path


def get_output_dir() -> Path:
    """Resolve the output directory from env var, config.py, or default 'output'."""
    out = os.getenv('DEFAULT_OUTPUT_DIR')
    if not out:
        try:
            from config import DEFAULT_OUTPUT_DIR
            out = DEFAULT_OUTPUT_DIR
        except Exception:
            out = 'output'
    p = Path(out)
    p.mkdir(parents=True, exist_ok=True)
    return p
