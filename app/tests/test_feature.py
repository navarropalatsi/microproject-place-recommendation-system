from app.tests.fakers import get_feature_faker


def test_can_add_feature(client):
    feature = get_feature_faker()
    response = client.post(
        "/features",
        json={
            "name": feature.name,
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == feature.name


def test_can_add_features_and_list_them(client):
    size = 50
    features = []
    for i in range(size):
        feature = get_feature_faker()
        features.append(feature)
        client.post(
            "/features",
            json={
                "name": feature.name,
            },
        )

    limit = int(size / 2)
    response = client.get("/features?limit=" + str(limit))
    assert response.status_code == 200
    assert len(response.json()) == limit


def test_can_delete_existing_feature(client):
    response = client.get("/features?limit=1")
    assert response.status_code == 200
    feature = response.json()[0]

    response = client.delete("/features/" + feature["name"])
    assert response.status_code == 200

    response = client.get("/features/" + feature["name"])
    assert response.status_code == 404


def test_cannot_delete_non_existing_feature(client):
    response = client.get("/features?limit=1")
    assert response.status_code == 200
    feature = response.json()[0]

    response = client.delete("/features/" + feature["name"])
    assert response.status_code == 200

    response = client.delete("/features/" + feature["name"])
    assert response.status_code == 404
