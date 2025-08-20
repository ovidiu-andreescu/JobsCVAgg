import os
import pytest

def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="run slow tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
