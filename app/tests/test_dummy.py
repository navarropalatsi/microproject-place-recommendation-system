def test_startup(client):
    response = client.get("/")
    assert response.status_code == 200
