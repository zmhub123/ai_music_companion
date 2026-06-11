import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from src.core.config import reload_settings

reload_settings(BACKEND_DIR / "tests" / "fixtures" / "test.env")


@pytest.fixture
def client() -> Iterator[TestClient]:
    from src.main import app

    with TestClient(app) as test_client:
        yield test_client
