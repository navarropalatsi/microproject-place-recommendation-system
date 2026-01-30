import logging
from typing import LiteralString, cast

from neo4j import GraphDatabase, Driver, AsyncGraphDatabase, AsyncDriver
from pydantic import BaseModel

from app.config.settings import settings


async def setup_db() -> AsyncDriver:
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_HOSTNAME, auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    )
    await driver.verify_connectivity()

    async with driver.session(database=settings.NEO4J_DATABASE) as session:
        with open("neo4j_setup/data_model/data_model_startup.cypher", "r") as f:
            data_model_startup = f.read()
            for query in data_model_startup.split(";"):
                query = query.strip()
                if len(query) > 0:
                    await session.run(cast(LiteralString, query))
            logging.getLogger("uvicorn").info(
                "Neo4J startup script executed successfully"
            )

    return driver


def validate_field(obj: type[BaseModel], field: str):
    return obj is not None and field is not None and field in obj.model_fields.keys()


def validate_order(order: str):
    return order is not None and order.upper() in {"ASC", "DESC"}


def validate_gender(gender: str):
    return gender is not None and gender.upper() in {"M", "F"}
