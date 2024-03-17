def login(client, username):
    resp = client.post("/session/login", json={"username": username})
    assert resp.status_code == 201
    assert resp.json.get("username") == username


def test_user_sessions(client):
    resp = client.get("/session")
    assert resp.status_code == 200
    assert resp.json in [{}, None]

    login(client, "john")

    resp = client.get("/session")
    assert resp.status_code == 200
    assert resp.json.get("username") == "john"

    resp = client.delete("/session/logout")
    assert resp.status_code == 204

    resp = client.get("/session")
    assert resp.status_code == 200
    # we should get back nothing
    assert resp.json in [{}, None]


def test_list_repos(client):
    login(client, "john")
    resp = client.get("/orgs/1/repos")
    assert resp.status_code == 200
    repos = resp.json
    assert len(repos) == 1
    assert repos[0]["id"] == 1
