from faker import Faker
from faker.config import AVAILABLE_LOCALES
from fastapi.testclient import TestClient
from app.main import app

faker = Faker(locale=AVAILABLE_LOCALES)
