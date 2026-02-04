import asyncio
import logging
import pytest
from _pytest.main import Session
from fastapi.testclient import TestClient
from neo4j import AsyncDriver

from app.config.neo4j import setup_db
from app.config.settings import settings, Settings, ProductionSettings, LocalSettings
from app.main import app


async def clean_db():
    driver: AsyncDriver = await setup_db()
    try:
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.run("MATCH (n) DETACH DELETE n")
    finally:
        await driver.close()


def check_if_test_datbase():
    error_msg = f"\n🚨 SAFETY VIOLATION: Attempting to test against a production-like host: '{settings.NEO4J_HOSTNAME}'. Check your .env.test file.\n\n"

    settings_docker = ProductionSettings()
    if (
        settings.NEO4J_HOSTNAME == settings_docker.NEO4J_HOSTNAME
        and settings.NEO4J_AUTH == settings_docker.NEO4J_AUTH
        and settings.NEO4J_DATABASE == settings_docker.NEO4J_DATABASE
    ):
        raise Exception(error_msg)

    local_settings = LocalSettings()
    if (
        settings.NEO4J_HOSTNAME == local_settings.NEO4J_HOSTNAME
        and settings.NEO4J_AUTH == local_settings.NEO4J_AUTH
        and settings.NEO4J_DATABASE == local_settings.NEO4J_DATABASE
    ):
        raise Exception(error_msg)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        c.headers.update({settings.SERVICE_AK_HEADER: settings.SERVICE_API_KEY})
        yield c


def pytest_sessionstart(session: Session) -> None:
    logging.getLogger("uvicorn").info("TEST ENVIRONMENT IS SETTING UP...")
    try:
        check_if_test_datbase()
    except Exception as e:
        pytest.exit(str(e), returncode=pytest.ExitCode.USAGE_ERROR)
    asyncio.run(clean_db())
