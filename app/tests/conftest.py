import asyncio

import pytest
from _pytest.main import Session
from fastapi.testclient import TestClient
from neo4j import AsyncDriver

from app.config.neo4j import setup_db
from app.main import app


async def clean_db():
    driver: AsyncDriver = await setup_db()
    async with driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def pytest_sessionstart(session: Session) -> None:
    asyncio.run(clean_db())
    print("TEST ENVIRONMENT IS GOING TO START!!!!!")
