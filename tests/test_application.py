from fastapi.testclient import TestClient

from pancake.application import create_app


def test_app_instances_with_separate_directories_do_not_share_data(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    with TestClient(create_app(first)) as a, TestClient(create_app(second)) as b:
        assert a.post("/score", json={"score": 42}).json()["best"] == 42
        assert b.get("/best").json() == {"best": 0, "count": 0}
        assert a.get("/best").json() == {"best": 42, "count": 1}
