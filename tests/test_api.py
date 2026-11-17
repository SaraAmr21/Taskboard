def test_liveness(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readiness(client):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["database"] == "up"


def test_create_and_read_task(client):
    r = client.post("/api/tasks", json={"title": "Write the Dockerfile"})
    assert r.status_code == 201
    task = r.json()
    assert task["title"] == "Write the Dockerfile"
    assert task["status"] == "todo"

    r = client.get(f"/api/tasks/{task['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == task["id"]


def test_list_and_filter(client):
    client.post("/api/tasks", json={"title": "A", "status": "todo"})
    client.post("/api/tasks", json={"title": "B", "status": "done"})
    assert len(client.get("/api/tasks").json()) == 2
    assert len(client.get("/api/tasks", params={"status_filter": "done"}).json()) == 1


def test_update_status(client):
    task_id = client.post("/api/tasks", json={"title": "Ship it"}).json()["id"]
    r = client.patch(f"/api/tasks/{task_id}", json={"status": "doing"})
    assert r.status_code == 200
    assert r.json()["status"] == "doing"


def test_delete(client):
    task_id = client.post("/api/tasks", json={"title": "Temporary"}).json()["id"]
    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.get(f"/api/tasks/{task_id}").status_code == 404


def test_missing_task_returns_404(client):
    assert client.get("/api/tasks/424242").status_code == 404


def test_validation_rejects_empty_title(client):
    assert client.post("/api/tasks", json={"title": ""}).status_code == 422


def test_validation_rejects_unknown_status(client):
    assert client.post("/api/tasks", json={"title": "x", "status": "nope"}).status_code == 422


def test_stats(client):
    client.post("/api/tasks", json={"title": "1", "status": "todo"})
    client.post("/api/tasks", json={"title": "2", "status": "doing"})
    client.post("/api/tasks", json={"title": "3", "status": "done"})
    body = client.get("/api/stats").json()
    assert body == {"total": 3, "todo": 1, "doing": 1, "done": 1}


def test_homepage_serves_ui(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Task board" in r.text
