import asyncio

import pytest
from _pytest.main import Session
from fastapi.testclient import TestClient
from neo4j import AsyncDriver

from app.config.neo4j import setup_db
from app.config.settings import settings
from app.main import app


async def clean_db():
    driver: AsyncDriver = await setup_db()
    async with driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        c.headers.update({settings.SERVICE_AK_HEADER: settings.SERVICE_API_KEY})
        yield c


def pytest_sessionstart(session: Session) -> None:
    print("TEST ENVIRONMENT IS SETTING UP...")
    asyncio.run(clean_db())
