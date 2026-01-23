from app.tests import client

def test_startup():
    response = client.get("/")
    assert response.status_code == 200