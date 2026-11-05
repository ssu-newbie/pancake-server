import json
from concurrent.futures import ThreadPoolExecutor

import pytest


def write_rows(data_dir, filename, rows):
    (data_dir / filename).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def test_empty_store(client, data_dir):
    assert client.get("/health").json() == {"ok": True, "responses": 0}
    assert client.get("/residents").json() == {"count": 0, "residents": []}
    assert client.get("/best").json() == {"best": 0, "count": 0}
    assert list(data_dir.iterdir()) == []


def test_response_round_trip_and_disk_format(client, data_dir):
    payload = {"claims": ["q1", "임의의 문자열"], "agrees": [True, False]}
    result = client.post("/responses", json=payload)
    assert result.status_code == 200
    assert result.json() == {"ok": True, "total": 1}
    assert client.get("/health").json() == {"ok": True, "responses": 1}
    assert client.get("/residents").json() == {"count": 1, "residents": [payload]}
    rows = json.loads((data_dir / "responses.json").read_text(encoding="utf-8"))
    assert len(rows) == 1
    assert isinstance(rows[0].pop("ts"), (int, float))
    assert rows[0] == payload
    assert not (data_dir / "responses.json.tmp").exists()


@pytest.mark.parametrize("claims,agrees", [(["q1", "q2"], [True]), (["q1"], [True, False])])
def test_mismatched_lists_keep_the_shorter_length(client, claims, agrees):
    assert client.post("/responses", json={"claims": claims, "agrees": agrees}).json() == {
        "ok": True, "total": 1,
    }
    assert client.get("/residents").json()["residents"] == [{"claims": ["q1"], "agrees": [True]}]


@pytest.mark.parametrize("claims,agrees", [([], []), (["q1"], []), ([], [True])])
def test_empty_lists_return_legacy_200_without_writing(client, data_dir, claims, agrees):
    result = client.post("/responses", json={"claims": claims, "agrees": agrees})
    assert result.status_code == 200
    assert result.json() == {"ok": False, "error": "empty"}
    assert not (data_dir / "responses.json").exists()


@pytest.mark.parametrize("query,expected", [("", 100), ("?n=-5", 1), ("?n=0", 1), ("?n=1", 1), ("?n=2", 2), ("?n=1000", 1000), ("?n=1001", 1000)])
def test_residents_order_default_and_clamping(client, data_dir, query, expected):
    write_rows(data_dir, "responses.json", [
        {"ts": i, "claims": [f"q{i}"], "agrees": [True]} for i in range(1002)
    ])
    result = client.get("/residents" + query)
    assert result.status_code == 200
    assert result.json() == {
        "count": expected,
        "residents": [{"claims": [f"q{i}"], "agrees": [True]} for i in range(1001, 1001 - expected, -1)],
    }


@pytest.mark.parametrize("path,payload", [
    ("/responses", {}),
    ("/responses", {"claims": ["q1"], "agrees": ["not-a-bool"]}),
    ("/score", {}),
    ("/score", {"score": "not-an-int"}),
    ("/score", {"score": 1.5}),
])
def test_invalid_payloads_are_rejected_without_writing(client, data_dir, path, payload):
    assert client.post(path, json=payload).status_code == 422
    assert list(data_dir.iterdir()) == []


def test_invalid_resident_limit(client):
    assert client.get("/residents?n=invalid").status_code == 422


def test_scores_include_negative_values_and_keep_maximum(client, data_dir):
    for count, (score, best) in enumerate([(-10, -10), (25, 25), (7, 25)], start=1):
        result = client.post("/score", json={"score": score})
        assert result.status_code == 200
        assert result.json() == {"ok": True, "best": best, "count": count}
        assert client.get("/best").json() == {"best": best, "count": count}
    rows = json.loads((data_dir / "scores.json").read_text(encoding="utf-8"))
    assert [r["score"] for r in rows] == [-10, 25, 7]
    assert all(isinstance(r["ts"], (float, int)) for r in rows)
    assert not (data_dir / "scores.json.tmp").exists()


def test_existing_json_files_survive_app_restart(client_factory, data_dir):
    write_rows(data_dir, "responses.json", [{"ts": 1, "claims": ["q1"], "agrees": [False]}])
    write_rows(data_dir, "scores.json", [{"ts": 2, "score": 55}])
    with client_factory(data_dir) as client:
        assert client.post("/responses", json={"claims": ["q2"], "agrees": [True]}).json()["total"] == 2
        assert client.post("/score", json={"score": 3}).json() == {"ok": True, "best": 55, "count": 2}
    with client_factory(data_dir) as client:
        assert client.get("/health").json() == {"ok": True, "responses": 2}
        assert client.get("/residents").json()["residents"] == [
            {"claims": ["q2"], "agrees": [True]}, {"claims": ["q1"], "agrees": [False]},
        ]
        assert client.get("/best").json() == {"best": 55, "count": 2}


@pytest.mark.parametrize("filename,path,empty", [
    ("responses.json", "/health", {"ok": True, "responses": 0}),
    ("scores.json", "/best", {"best": 0, "count": 0}),
])
def test_invalid_json_keeps_legacy_empty_fallback(client, data_dir, filename, path, empty):
    file = data_dir / filename
    file.write_text("{incomplete", encoding="utf-8")
    assert client.get(path).json() == empty
    assert file.read_text(encoding="utf-8") == "{incomplete"


def test_cors_preflight(client):
    result = client.options("/responses", headers={
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert result.status_code == 200
    assert result.headers["access-control-allow-origin"] == "*"
    assert "POST" in result.headers["access-control-allow-methods"]


def test_small_in_process_concurrent_writes_preserve_records(client):
    """Regression check for locking, not a throughput or deployed load benchmark."""
    def submit(i):
        response = client.post("/responses", json={"claims": [f"q{i}"], "agrees": [True]})
        score = client.post("/score", json={"score": i})
        assert response.status_code == score.status_code == 200
        return response.json()["total"], score.json()["count"]

    with ThreadPoolExecutor(max_workers=4) as executor:
        counts = list(executor.map(submit, range(12)))
    assert sorted(total for total, _ in counts) == list(range(1, 13))
    assert sorted(count for _, count in counts) == list(range(1, 13))
    residents = client.get("/residents").json()
    assert residents["count"] == 12
    assert {r["claims"][0] for r in residents["residents"]} == {f"q{i}" for i in range(12)}
    assert client.get("/best").json() == {"best": 11, "count": 12}
