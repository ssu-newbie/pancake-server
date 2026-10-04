import importlib.util
import os
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path


@pytest.fixture
def client_factory():
    """Run the same contract suite against a saved legacy module or the app factory."""
    @contextmanager
    def make_client(data_dir):
        legacy_source = os.environ.get("PANCAKE_LEGACY_SOURCE")
        if legacy_source:
            spec = importlib.util.spec_from_file_location("pancake_legacy", legacy_source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.DATA_FILE = str(Path(data_dir) / "responses.json")
            module.SCORE_FILE = str(Path(data_dir) / "scores.json")
            app = module.app
        else:
            from pancake.application import create_app

            app = create_app(data_dir=data_dir)
        with TestClient(app) as client:
            yield client

    return make_client


@pytest.fixture
def client(client_factory, data_dir):
    with client_factory(data_dir) as client:
        yield client
