from pathlib import Path

from fastapi.testclient import TestClient

from docugraph.api import main

DEMO = Path("demo_data")


def _use_demo_data(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DB", tmp_path / "reviews.db")
    monkeypatch.setattr(main, "REPORT", DEMO / "report.json")
    monkeypatch.setattr(main, "ROLES", DEMO / "roles.json")


def test_default_paths_point_at_the_right_files():
    assert main.REPORT.name == "report.json"
    assert main.ROLES.name == "roles.json"
    assert main.DB.name == "reviews.db"
    assert main.PAGE.exists()


def test_index_page_is_served():
    r = TestClient(main.app).get("/")
    assert r.status_code == 200
    assert "DocuGraph" in r.text


def test_graph_has_nodes_edges_and_roles(monkeypatch, tmp_path):
    _use_demo_data(monkeypatch, tmp_path)
    g = TestClient(main.app).get("/api/graph").json()
    assert g["nodes"] and g["edges"]
    assert all("role" in n["data"] for n in g["nodes"])


def test_review_roundtrip(monkeypatch, tmp_path):
    _use_demo_data(monkeypatch, tmp_path)
    client = TestClient(main.app)
    items = client.get("/api/report").json()
    assert len(items) >= 1
    fid = items[0]["id"]
    assert client.post("/api/review", json={"finding_id": fid, "decision": "accept"}).status_code == 200
    after = client.get("/api/report").json()
    assert next(i for i in after if i["id"] == fid)["review"]["decision"] == "accept"
    assert client.post("/api/review", json={"finding_id": "nope", "decision": "accept"}).status_code == 404