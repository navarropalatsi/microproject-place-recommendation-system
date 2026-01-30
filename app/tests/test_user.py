import pytz

from app.dto.user import SingleUserExtended
from app.tests import faker
from app.tests.fakers import get_user_faker, get_feature_faker


def test_create_user(client):
    user = get_user_faker()

    response = client.post(
        "/users", json={"userId": user.userId, "gender": user.gender, "born": user.born}
    )

    assert response.status_code == 201
    assert response.json()["userId"] == user.userId
    assert response.json()["born"] == user.born


def test_create_users_and_list_them(client):
    size = 10
    users = []
    for i in range(size):
        user = get_user_faker()
        users.append(user)
        client.post(
            "/users",
            json={"userId": user.userId, "gender": user.gender, "born": user.born},
        )

    response = client.get("/users?limit=" + str(max(300, size)))
    assert response.status_code == 200
    assert len(response.json()) >= size


def test_cannot_create_existing_user(client):
    response = client.get("/users?limit=1")
    assert response.status_code == 200
    user = response.json()[0]

    response = client.post(
        "/users",
        json={"userId": user["userId"], "gender": user["gender"], "born": user["born"]},
    )
    assert response.status_code == 409


def test_update_existing_user(client):
    response = client.get("/users?limit=1")
    assert response.status_code == 200
    if len(response.json()) == 0:
        assert True

    user = response.json()[0]
    new_born = faker.date_of_birth(
        tzinfo=pytz.UTC, minimum_age=20, maximum_age=40
    ).isoformat()
    new_gender = "m" if user["gender"] == "f" else "f"
    response = client.put(
        "/users/" + user["userId"],
        json={"userId": user["userId"], "gender": new_gender, "born": new_born},
    )
    assert response.status_code == 200
    assert response.json()["userId"] == user["userId"]
    assert response.json()["gender"] == new_gender
    assert response.json()["born"] == new_born


def can_delete_existing_user(client):
    response = client.get("/users?limit=1")
    assert response.status_code == 200
    user = response.json()[0]

    response = client.delete("/users/" + user["userId"])
    assert response.status_code == 200

    response = client.get("/users/" + user["userId"])
    assert response.status_code == 404


def test_cannot_delete_non_existing_user(client):
    response = client.get("/users?limit=1")
    assert response.status_code == 200
    user = response.json()[0]

    response = client.delete("/users/" + user["userId"])
    assert response.status_code == 200

    response = client.delete("/users/" + user["userId"])
    assert response.status_code == 404


def test_can_attach_a_feature_to_an_existing_user(client):
    response = client.get("/users?limit=1")
    assert response.status_code == 200
    user = response.json()[0]

    feature = get_feature_faker()
    response = client.post(
        "/features",
        json={
            "name": feature.name,
        },
    )
    assert response.status_code == 200
    feature = response.json()

    response = client.post("/users/" + user["userId"] + "/needs/" + feature["name"])
    assert response.status_code == 201

    user: SingleUserExtended = response.json()
    for f in user["features"]:
        if feature["name"] == f["name"]:
            assert feature["name"] == f["name"]
            return
    assert False


def test_can_detach_a_feature_to_an_existing_user(client):
    response = client.get("/users?limit=1")
    assert response.status_code == 200
    user = response.json()[0]

    feature = get_feature_faker()
    response = client.post(
        "/features",
        json={
            "name": feature.name,
        },
    )
    assert response.status_code == 200
    feature = response.json()

    response = client.post("/users/" + user["userId"] + "/needs/" + feature["name"])
    assert response.status_code == 201

    response = client.delete(
        "/users/" + user["userId"] + "/does-not-need/" + feature["name"]
    )
    assert response.status_code == 200
    user: SingleUserExtended = response.json()
    for f in user["features"]:
        if feature["name"] == f["name"]:
            assert False
    assert True
