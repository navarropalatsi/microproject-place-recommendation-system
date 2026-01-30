from typing import cast, LiteralString

from neo4j import AsyncDriver, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError
from werkzeug.exceptions import NotFound

from app.config.neo4j import validate_order, validate_field
from app.config.settings import settings
from app.dto.category import SingleCategory
from app.config.exceptions import NotFound


class CategoryDAO(object):
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    @staticmethod
    async def get_category(tx: AsyncManagedTransaction, name: str):
        result = await tx.run(
            cast(
                LiteralString,
                """
        MATCH (c:Category {name: $name})
        RETURN c AS category
        """,
            ),
            name=name,
        )

        result = await result.single()
        if result and result.get("category"):
            return result.get("category")
        else:
            raise NotFound(f"Category with name {name} not found")

    async def all(self, sort="name", order="DESC", skip=0, limit=25):
        async def get_categories(tx: AsyncManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(SingleCategory, sort):
                sort = "name"

            result = await tx.run(
                cast(
                    LiteralString,
                    f"""
            MATCH (c:Category)
            ORDER BY c.{sort} {order}
            RETURN c AS category
            SKIP $skip LIMIT $limit 
            """,
                ),
                skip=skip,
                limit=limit,
            )

            return [row.value("category") async for row in result]

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(get_categories, sort, order, skip, limit)

    async def find(self, name: str):
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(self.get_category, name)

    async def create(self, name: str):
        async def add(tx: AsyncManagedTransaction, name: str):
            result = await tx.run(
                """
                MERGE (c:Category {name: $name})
                RETURN c AS category
            """,
                name=name,
            )

            result = await result.single()
            if result is not None:
                return result.get("category")
            return None

        try:
            async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                return session.execute_write(add, name=name)
        except ConstraintError as e:
            print("ConstraintError detected: " + e.title)
            return None

    async def delete(self, name: str):
        async def remove(tx: AsyncManagedTransaction, name: str):
            result = await tx.run(
                """
                MATCH (c:Category {name: $name})
                DETACH DELETE c
                RETURN c AS category
            """,
                name=name,
            )

            result = await result.single()
            return result is not None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_category, name=name)
            return await session.execute_write(remove, name=name)
