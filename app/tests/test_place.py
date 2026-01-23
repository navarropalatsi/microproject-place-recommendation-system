from app.tests import client, faker
from app.tests.fakers import get_place_faker


def test_create_place():
    place = get_place_faker()

    response = client.post("/places", json={
        "placeId": place.placeId,
        "name": place.name,
        "fullAddress": place.fullAddress
    })
    assert response.status_code == 201

    assert response.json() == {
        "placeId": place.placeId,
        "name": place.name,
        "fullAddress": place.fullAddress
    }

def test_create_places_and_list_them():
    size = 10
    places = []
    for i in range(size):
        place = get_place_faker()
        places.append(place)
        client.post("/places", json={
            "placeId": place.placeId,
            "name": place.name,
            "fullAddress": place.fullAddress
        })

    response = client.get("/places?limit=" + str(max(300, size)))
    assert response.status_code == 200
    assert len(response.json()) >= size

def test_cannot_create_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]

    response = client.post("/places", json={
        "placeId": place['placeId'],
        "name": place['name'],
        "fullAddress": place['fullAddress']
    })
    assert response.status_code == 409

def test_can_update_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]

    new_name = faker.company()
    new_address = faker.address()
    response = client.put("/places/" + place['placeId'], json={
        "placeId": place['placeId'],
        "name": new_name,
        "fullAddress": new_address
    })
    assert response.status_code == 200
    assert response.json() == {
        "placeId": place['placeId'],
        "name": new_name,
        "fullAddress": new_address
    }

def test_can_delete_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]
    response = client.delete("/places/" + place['placeId'])
    assert response.status_code == 200
    response = client.get("/places/" + place['placeId'])
    assert response.status_code == 404

def test_cannot_delete_non_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]

    response = client.delete("/places/" + place['placeId'])
    assert response.status_code == 200

    response = client.delete("/places/" + place['placeId'])
    assert response.status_code == 404