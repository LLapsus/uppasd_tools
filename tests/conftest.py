from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uppasd_tools.uppout import UppOut  # noqa: E402


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return ROOT / "data"


@pytest.fixture(scope="session")
def bccfe_dir(data_dir: Path) -> Path:
    return data_dir / "bccFe"


@pytest.fixture(scope="session")
def feco_dir(data_dir: Path) -> Path:
    return data_dir / "FeCo"


@pytest.fixture(scope="session")
def bccfe_uppout(bccfe_dir: Path) -> UppOut:
    return UppOut(bccfe_dir, simid="bcc_Fe_T")


@pytest.fixture(scope="session")
def feco_uppout(feco_dir: Path) -> UppOut:
    return UppOut(feco_dir, simid="FeCo__B2")
