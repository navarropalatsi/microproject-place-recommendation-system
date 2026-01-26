from app.dto.place import SinglePlaceExtended
from app.tests import client, faker
from app.tests.fakers import get_place_faker, get_feature_faker, get_category_faker


def test_create_place():
    place = get_place_faker()
    response = client.post("/places", json=place.model_dump())
    assert response.status_code == 201

    assert response.json()["placeId"] == place.placeId

def test_create_places_and_list_them():
    size = 10
    places = []
    for i in range(size):
        place = get_place_faker()
        places.append(place)
        response = client.post("/places", json=place.model_dump())
        assert response.status_code == 201

    response = client.get("/places?limit=" + str(max(300, size)))
    assert response.status_code == 200
    assert len(response.json()) >= size

def test_cannot_create_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]

    response = client.post("/places", json=dict(place))
    assert response.status_code == 409

def test_can_update_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]

    new_name = faker.company()
    new_address = faker.address()
    place['name'] = new_name
    place['freeform'] = new_address
    response = client.put("/places/" + place['placeId'], json=dict(place))
    assert response.status_code == 200
    assert response.json()['freeform'] == new_address

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

def test_can_attach_a_feature_to_an_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]

    feature = get_feature_faker()
    response = client.post("/features", json={
        "name": feature.name,
    })
    assert response.status_code == 200
    feature = response.json()

    response = client.post("/places/" + place["placeId"] + "/has/" + feature["name"])
    assert response.status_code == 201

    place: SinglePlaceExtended = response.json()
    for f in place["features"]:
        if feature['name'] == f['name']:
            assert feature['name'] == f['name']
            return
    assert False

def test_can_detach_a_feature_to_an_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]

    feature = get_feature_faker()
    response = client.post("/features", json={
        "name": feature.name,
    })
    assert response.status_code == 200
    feature = response.json()

    response = client.post("/places/" + place["placeId"] + "/has/" + feature["name"])
    assert response.status_code == 201

    response = client.delete("/places/" + place["placeId"] + "/has-not/" + feature["name"])
    assert response.status_code == 200
    place: SinglePlaceExtended = response.json()
    for f in place["features"]:
        if feature['name'] == f['name']:
            assert False
    assert True

def test_can_attach_a_category_to_an_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]

    category = get_category_faker()
    response = client.post("/categories", json={
        "name": category.name,
    })
    assert response.status_code == 200
    category = response.json()

    response = client.post("/places/" + place["placeId"] + "/is-in/" + category["name"])
    assert response.status_code == 201

    place: SinglePlaceExtended = response.json()
    for f in place["categories"]:
        if category['name'] == f['name']:
            assert category['name'] == f['name']
            return
    assert False

def test_can_detach_a_category_to_an_existing_place():
    response = client.get("/places?limit=1")
    assert response.status_code == 200
    place = response.json()[0]

    category = get_category_faker()
    response = client.post("/categories", json={
        "name": category.name,
    })
    assert response.status_code == 200
    category = response.json()

    response = client.post("/places/" + place["placeId"] + "/is-in/" + category["name"])
    assert response.status_code == 201

    response = client.delete("/places/" + place["placeId"] + "/is-not-in/" + category["name"])
    assert response.status_code == 200
    place: SinglePlaceExtended = response.json()
    for f in place["categories"]:
        if category['name'] == f['name']:
            assert False
    assert True