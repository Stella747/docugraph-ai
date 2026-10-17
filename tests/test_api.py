from fastapi.testclient import TestClient

from docugraph.api import main


def test_review_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB", tmp_path / "reviews.db")
    client = TestClient(main.app)
    items = client.get("/api/report").json()
    assert len(items) >= 1
    fid = items[0]["id"]
    assert client.post("/api/review", json={"finding_id": fid, "decision": "accept"}).status_code == 200
    after = client.get("/api/report").json()
    assert next(i for i in after if i["id"] == fid)["review"]["decision"] == "accept"
    assert client.post("/api/review", json={"finding_id": "nope", "decision": "accept"}).status_code == 404