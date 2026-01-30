from typing import cast, LiteralString

from neo4j import AsyncDriver, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.config.neo4j import validate_order, validate_field
from app.config.settings import settings
from app.dto.feature import SingleFeature
from app.config.exceptions import NotFound


class FeatureDAO(object):
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    @staticmethod
    async def get_feature(tx: AsyncManagedTransaction, name: str):
        result = await tx.run(
            cast(
                LiteralString,
                """
        MATCH (f:Feature {name: $name})
        RETURN f AS feature
        """,
            ),
            name=name,
        )

        result = await result.single()
        if result and result.get("feature"):
            return result.get("feature")
        else:
            raise NotFound(f"Feature with name {name} not found")

    async def all(self, sort="name", order="DESC", skip=0, limit=25):
        async def get_features(tx: AsyncManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(SingleFeature, sort):
                sort = "name"

            result = await tx.run(
                cast(
                    LiteralString,
                    f"""
            MATCH (f:Feature)
            ORDER BY f.{sort} {order}
            RETURN f AS feature
            SKIP $skip LIMIT $limit 
            """,
                ),
                skip=skip,
                limit=limit,
            )

            return [row.value("feature") async for row in result]

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return await session.execute_read(get_features, sort, order, skip, limit)

    async def find(self, name: str):
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return await session.execute_read(self.get_feature, name)

    async def create(self, name: str):
        async def add(tx: AsyncManagedTransaction, name: str):
            result = await tx.run(
                """
                MERGE (f:Feature {name: $name})
                RETURN f AS feature
            """,
                name=name,
            )

            result = await result.single()
            if result is not None:
                return result.get("feature")
            return None

        try:
            async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                return await session.execute_write(add, name=name)
        except ConstraintError as e:
            print("ConstraintError detected: " + e.title)
            return None

    async def delete(self, name: str):
        async def remove(tx: AsyncManagedTransaction, name: str):
            result = await tx.run(
                """
                MATCH (f:Feature {name: $name})
                DETACH DELETE f
                RETURN f AS feature
            """,
                name=name,
            )

            result = await result.single()
            return result is not None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_read(self.get_feature, name=name)
            return await session.execute_write(remove, name=name)
