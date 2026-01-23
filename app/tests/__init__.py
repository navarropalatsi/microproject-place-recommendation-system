from faker import Faker
from fastapi.testclient import TestClient
from app.main import app

client: TestClient = TestClient(app)
faker = Faker()