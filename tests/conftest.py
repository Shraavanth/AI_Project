"""
Shared test setup.

The backend is pointed at a temporary SQLite database and the background
simulation loop is disabled, so tests drive the simulation tick by tick.
"""

import os
import sys
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

_tmp_dir = tempfile.mkdtemp(prefix="envmas-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp_dir, 'test.db')}"
os.environ["SIM_AUTOSTART"] = "0"
os.environ["SIM_SEED"] = "7"

import pytest  # noqa: E402

from tests.helpers import make_engine  # noqa: E402


@pytest.fixture
def engine():
    return make_engine()
