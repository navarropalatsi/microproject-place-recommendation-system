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
            "MATCH (f:Feature {name: $name}) RETURN f AS feature",
            name=name,
        )
        result = await result.single()
        return result.get("feature") if result else None

    @staticmethod
    async def get_features(
        tx: AsyncManagedTransaction, sort="name", order="DESC", skip=0, limit=25
    ):
        if not validate_order(order):
            order = "DESC"
        if not validate_field(SingleFeature, sort):
            sort = "name"

        query = cast(
            LiteralString,
            f"""
                MATCH (f:Feature)
                ORDER BY f.{sort} {order}
                RETURN f AS feature
                SKIP $skip LIMIT $limit """,
        )

        result = await tx.run(query, skip=skip, limit=limit)

        return [row.value("feature") async for row in result]

    @staticmethod
    async def add(tx: AsyncManagedTransaction, name: str):
        result = await tx.run(
            "MERGE (f:Feature {name: $name}) RETURN f AS feature",
            name=name,
        )

        result = await result.single()
        return result.get("feature") if result else None

    @staticmethod
    async def update(tx: AsyncManagedTransaction, name: str, new_name: str):
        result = await tx.run(
            "MATCH (f:Feature {name: $name}) SET f.name = $new_name RETURN f AS feature",
            name=name,
            new_name=new_name,
        )

        result = await result.single()
        return result.get("feature") if result else None

    @staticmethod
    async def remove(tx: AsyncManagedTransaction, name: str):
        result = await tx.run(
            "MATCH (f:Feature {name: $name}) DETACH DELETE f RETURN f AS feature",
            name=name,
        )

        result = await result.single()
        return result is not None
