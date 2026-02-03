from typing import cast, LiteralString

from neo4j import AsyncDriver, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError
from werkzeug.exceptions import NotFound

from app.config.neo4j import validate_order, validate_field
from app.config.settings import settings
from app.dto.category import SingleCategory
from app.config.exceptions import NotFound


class CategoryDAO(object):
    def __init__(self):
        return

    @staticmethod
    async def get_category(tx: AsyncManagedTransaction, name: str):
        result = await tx.run(
            "MATCH (c:Category {name: $name}) RETURN c AS category",
            name=name,
        )
        result = await result.single()
        return result.get("category") if result else None

    @staticmethod
    async def get_categories(
        tx: AsyncManagedTransaction, sort="name", order="DESC", skip=0, limit=25
    ):
        if not validate_order(order):
            order = "DESC"
        if not validate_field(SingleCategory, sort):
            sort = "name"

        query = cast(
            LiteralString,
            f"""
            MATCH (c:Category)
            ORDER BY c.{sort} {order}
            RETURN c AS category
            SKIP $skip LIMIT $limit """,
        )

        result = await tx.run(query, skip=skip, limit=limit)

        return [row.value("category") async for row in result]

    @staticmethod
    async def add(tx: AsyncManagedTransaction, name: str):
        result = await tx.run(
            """ MERGE (c:Category {name: $name}) RETURN c AS category""", name=name
        )

        result = await result.single()
        return result.get("category") if result else None

    @staticmethod
    async def update(tx: AsyncManagedTransaction, name: str, new_name: str):
        result = await tx.run(
            """ MATCH (c:Category {name: $name}) SET c.name=$new_name RETURN c AS category""",
            name=name,
            new_name=new_name,
        )

        result = await result.single()
        return result.get("category") if result else None

    @staticmethod
    async def remove(tx: AsyncManagedTransaction, name: str):
        result = await tx.run(
            """ MATCH (c:Category {name: $name})
            DETACH DELETE c
            RETURN c AS category """,
            name=name,
        )

        result = await result.single()
        return result is not None
