from app.tests.fakers import get_category_faker


def test_can_add_category(client):
    category = get_category_faker()
    response = client.post(
        "/categories",
        json={
            "name": category.name,
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == category.name


def test_can_add_categories_and_list_them(client):
    size = 50
    categories = []
    for i in range(size):
        category = get_category_faker()
        categories.append(category)
        client.post(
            "/categories",
            json={
                "name": category.name,
            },
        )

    response = client.get("/categories?limit=" + str(max(300, size)))
    assert response.status_code == 200
    assert len(response.json()) >= size


def test_can_delete_existing_category(client):
    response = client.get("/categories?limit=1")
    assert response.status_code == 200
    category = response.json()[0]

    response = client.delete("/categories/" + category["name"])
    assert response.status_code == 200

    response = client.get("/categories/" + category["name"])
    assert response.status_code == 404


def test_cannot_delete_non_existing_category(client):
    response = client.get("/categories?limit=1")
    assert response.status_code == 200
    category = response.json()[0]

    response = client.delete("/categories/" + category["name"])
    assert response.status_code == 200

    response = client.delete("/categories/" + category["name"])
    assert response.status_code == 404
