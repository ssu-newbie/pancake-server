"""Synthetic payloads following the uploaded Unity registration flow.

The Unity editor is not executed here. These tests verify the server side of
the confirmed q1..q112 field contract without publishing real survey rows.
"""


def test_full_registration_keeps_prefilled_claim_first(client):
    # GameFlowController adds the ending's claim first, then all other claims.
    order = [81] + [index for index in range(1, 113) if index != 81]
    payload = {
        "claims": [f"q{index}" for index in order],
        "agrees": [index % 2 == 0 for index in order],
    }
    response = client.post("/responses", json=payload)
    assert response.status_code == 200
    assert response.json() == {"ok": True, "total": 1}
    assert client.get("/residents?n=100").json() == {
        "count": 1,
        "residents": [payload],
    }


def test_partial_record_keeps_claim_ids_without_server_padding(client):
    # Older/partial records stay sparse. The client supplies missing answers.
    payload = {"claims": ["q112", "q1", "q21"], "agrees": [False, True, False]}
    assert client.post("/responses", json=payload).json()["ok"] is True
    assert client.get("/residents?n=100").json()["residents"] == [payload]
