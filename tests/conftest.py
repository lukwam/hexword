"""Shared test fixtures for the hexword test suite."""

from pathlib import Path

import pytest
import yaml

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def snow_white_dict() -> dict:
    """Return the Snow White puzzle as a raw dict (from YAML)."""
    with (FIXTURES_DIR / "snow_white.yaml").open() as f:
        return yaml.safe_load(f)
