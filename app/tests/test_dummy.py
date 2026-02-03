from app.config.settings import settings


def test_startup(client):
    response = client.get("/", headers={settings.SERVICE_AK_HEADER: ""})
    assert response.status_code == 200
