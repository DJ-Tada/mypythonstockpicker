# Copilot Instructions

## Vision / Image Restrictions

Do NOT use vision or image-analysis capabilities (e.g. `view_image`, inline image interpretation).
Vision is not enabled for this organization and will cause a **400 error** that interrupts the chat.

When working with image files (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.tiff`):
- Read metadata or file paths only — never attempt to view or analyze image content.
- If the user asks about an image, describe what can be inferred from the file name, path, or surrounding code instead.

## CLI Convention

All CLI commands and usage examples assume the **project root** (`MyPythonStockPicker/`) as the working directory (i.e. the folder containing `config.py`). Always write commands accordingly — e.g. `python -m scripts.run_full_summary`, not instructions to `cd` into subfolders first.

```
python -m scripts.fetch_tickers
python -m scripts.run_full_summary
python -m stockpicker.screener
```

## Project Setup

When setting up a new project or clone:
1. Create venv: `python -m venv .venv` in project root
2. Create `.gitignore` from the template below
3. Create `config.template.py` (tracked, placeholder values) → copy to `config.py` (git-ignored, real secrets). Never commit `config.py`.
4. Create `output/` folders where needed and add each `<module>/output/` to `.gitignore`
5. Install deps: `pip install -r requirements.txt`
6. Windows paths: use raw strings (`r"C:\..."`) or `pathlib.Path`

### Initial config.py Setup

After cloning or on first run:

```bash
# Copy template to create local config file
cp config.template.py config.py
```

Then edit `config.py` with your actual configuration values (API keys, credentials, etc.). The `.gitignore` ensures `config.py` is never committed.

**Key principle:**
- **`config.template.py`** → Tracked in git, contains placeholder/default values
- **`config.py`** → Git-ignored, contains your real secrets and local settings

Never hardcode secrets in tracked files.

### Output Folder Convention

Every module that generates files **must** have an `output/` subfolder. When creating a new module with output:
1. Create `<module>/output/` directory
2. Add `<module>/output/` to root `.gitignore` with a comment

### New Module Checklist

- [ ] `__init__.py` with single-line package docstring only (no imports)
- [ ] `output/` subfolder if module generates files → add to `.gitignore`
- [ ] New config values go in `config.template.py` (never hardcode secrets)

## Terminal Maintenance

**Every day or when terminal operations slow down**, check if many terminals are open:
1. Look for hidden/background terminals in VS Code that may have accumulated
2. If many terminals exist (even more than indicated in the UI), close them all and reopen only what's needed
3. Background processes and orphaned terminals can accumulate and significantly slow down terminal performance

This is especially important if you notice terminal commands running slower than expected.

## Periodic Repo Health Check

**Remind the user once in a while** (e.g. when starting a new feature or after a big coding session) to review the repo for hygiene issues:

1. **Flat-file sprawl** — Are new `.py` files piling up in the project root instead of going into packages/subfolders? Suggest moving them.
2. **Redundant / dead code** — Look for duplicated logic across files (e.g. the same config-resolution boilerplate, copy-pasted utility functions). Flag duplicates and suggest consolidating into a single shared module.
3. **Sandbox / scratch files** — Identify experimental or notebook-style scripts (`#%%` cells, commented-out blocks, `print()` at module level). Suggest moving them to a `sandbox/` folder so they don't clutter the importable codebase.
4. **Hardcoded secrets** — Scan for API keys, tokens, or passwords that appear directly in tracked source files or in files not covered by `.gitignore`. Flag immediately.
5. **Unused imports / files** — Check for modules that are imported nowhere, or imports inside files that are never used.
6. **`.gitignore` coverage** — Verify that `config.py`, `output/`, `__pycache__/`, and generated data files (`.parquet`, large `.csv`) are properly ignored.

When any of these issues are found, proactively propose a fix rather than just flagging it.

### `.gitignore` Template

```gitignore
# Secrets / environment-specific config (use config.template.py as reference)
config.py
failed_images_log.txt
# Model weights (keep locally, don't track)
*.pt
*.pb
*.onnx
*.h5
*.exe
*.der
*.pem
*.spec
 

# Other files: 
*.json
*.pyc
loop_heartbeat.txt

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pipenv
#Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# Module output folders (add new ones as modules are created)
analysis/output/
ground_truth/output/
model_development/output/
```

## Python Conventions

### Imports (strict order, blank line between groups)

```python
import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from config import BASE_RESULTS_DIR
from utils.coilid import extract_coil_id_from_filename
```

Always absolute imports, never relative.

### Module Template

```python
"""One-line module description."""

import logging

logger = logging.getLogger(__name__)
```

`print()` only for user-facing CLI output.

### Function Signatures & Docstrings

```python
def process_image(image_path: str, threshold: float = 0.5) -> Optional[dict]:
    """
    One-line summary.

    Parameters
    ----------
    image_path : str
        Path to the input image.
    threshold : float
        Confidence threshold.

    Returns
    -------
    dict or None
        Result dict with keys 'coil_id', 'confidence', or None on failure.
    """
```

- Type hints on all function signatures; `Optional[X]` or `X | None`
- NumPy-style docstrings with Parameters/Returns/Examples sections

### Naming

| Category | Style | Example |
|----------|-------|---------|
| Functions / variables | `snake_case` | `extract_coil_id` |
| Constants | `UPPER_CASE` | `OPC_URL` |
| Private | `_leading_underscore` | `_parse_timestamp()` |
| Classes | `PascalCase` | `WatchdogSupervisor` |

### Patterns

- **Lazy caching**: global `_cache = None` with loader function using `global`
- **Error handling**: try/except in I/O and external calls; log the error, don't silently swallow
- **Constants at module top**: `UPPER_CASE` after imports
- **Context managers**: use `@contextmanager` for resource cleanup
- **Regex patterns**: centralize in module-level constants
- **Dict-based metadata**: prefer dicts for structured results over tuples
