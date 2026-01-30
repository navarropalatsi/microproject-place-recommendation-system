from typing import cast, LiteralString

from neo4j import AsyncDriver, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.config.exceptions import AlreadyExists, NotFound, InvalidValue
from app.config.neo4j import validate_order, validate_field, validate_gender
from app.config.settings import settings
from app.dto.user import SingleUser


class UserDAO(object):
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    RATED = "RATED"
    NEEDS_FEATURE = "NEEDS_FEATURE"

    @staticmethod
    async def get_user(tx: AsyncManagedTransaction, user_id: str):
        result = await tx.run(
            cast(
                LiteralString,
                """
        MATCH (u:User {userId: $user_id})
        RETURN u AS user
        """,
            ),
            user_id=user_id,
        )

        result = await result.single()
        if result and result.get("user", False):
            return result.get("user")
        else:
            raise NotFound(f"User with userId {user_id} not found")

    @staticmethod
    async def get_user_extended(tx: AsyncManagedTransaction, user_id: str):
        result = await tx.run(
            cast(
                LiteralString,
                f"""
        MATCH (u:User {{userId: $user_id}})
        OPTIONAL MATCH (u)-[:{UserDAO.NEEDS_FEATURE}]->(f:Feature)
        WITH u, collect(f) AS Feats
        RETURN u {{ .*, features: Feats }} AS user
        """,
            ),
            user_id=user_id,
        )

        result = await result.single()
        if result and result.get("user", False):
            return result.get("user")
        else:
            raise NotFound(f"User with userId {user_id} not found")

    async def all(self, sort="userId", order="DESC", skip=0, limit=25):
        async def get_users(tx: AsyncManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(SingleUser, sort):
                sort = "userId"

            result = await tx.run(
                cast(
                    LiteralString,
                    f"""
            MATCH (u:User)
            ORDER BY u.{sort} {order}
            RETURN u AS user
            SKIP $skip LIMIT $limit 
            """,
                ),
                skip=skip,
                limit=limit,
            )

            return [row.value("user") async for row in result]

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return await session.execute_read(get_users, sort, order, skip, limit)

    async def find(self, user_id: str):
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return await session.execute_read(self.get_user, user_id)

    async def create(self, user_id: str, born: str, gender: str):
        async def add(
            tx: AsyncManagedTransaction, user_id: str, born: str, gender: str
        ):
            if not validate_gender(gender):
                raise InvalidValue(
                    f"Invalid gender {gender}. Gender must be 'm' or 'f'"
                )

            result = await tx.run(
                """
                CREATE (u:User {userId: $user_id})
                SET u.born = date($born)
                SET u.gender = $gender
                RETURN u AS user
            """,
                user_id=user_id,
                born=born,
                gender=gender,
            )

            result = await result.single()
            if result is not None:
                return result.get("user")
            return None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            try:
                return await session.execute_write(
                    add, user_id=user_id, born=born, gender=gender
                )
            except ConstraintError:
                raise AlreadyExists(f"User with userId {user_id} already exists")

    async def update(self, user_id: str, born: str, gender: str):
        async def modify(
            tx: AsyncManagedTransaction, user_id: str, born: str, gender: str
        ):
            if not validate_gender(gender):
                raise InvalidValue(
                    f"Invalid gender {gender}. Gender must be 'm' or 'f'"
                )

            result = await tx.run(
                """
                MATCH (u:User {userId: $user_id})
                SET u.born = date($born)
                SET u.gender = $gender
                RETURN u AS user
            """,
                user_id=user_id,
                born=born,
                gender=gender,
            )

            result = await result.single()
            if result is not None:
                return result.get("user")
            return None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_read(self.get_user, user_id=user_id)
            return await session.execute_write(
                modify, user_id=user_id, born=born, gender=gender
            )

    async def delete(self, user_id: str):
        async def remove(tx: AsyncManagedTransaction, user_id: str):
            result = await tx.run(
                """
                MATCH (u:User {userId: $user_id})
                DETACH DELETE u
                RETURN u AS user
            """,
                user_id=user_id,
            )

            result = await result.single()
            return result is not None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_read(self.get_user, user_id=user_id)
            return await session.execute_write(remove, user_id=user_id)

    async def add_feature(self, user_id: str, feature: str):
        async def add_needs(tx: AsyncManagedTransaction, user_id: str, feature: str):
            result = await tx.run(
                cast(
                    LiteralString,
                    f"""
                MATCH (u:User {{userId: $user_id}})
                MATCH (f:Feature {{name: $feature}})
                MERGE (u)-[:{UserDAO.NEEDS_FEATURE}]->(f)
                RETURN u AS user
            """,
                ),
                user_id=user_id,
                feature=feature,
            )

            result = await result.single()
            return result.get("user")

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            if (
                await session.execute_write(add_needs, user_id=user_id, feature=feature)
                is None
            ):
                raise NotFound(
                    f"User with userId {user_id} or feature '{feature}' does not exist"
                )
            return await session.execute_read(self.get_user_extended, user_id=user_id)

    async def remove_feature(self, user_id: str, feature: str):
        async def remove_need(tx: AsyncManagedTransaction, user_id: str, feature: str):
            result = await tx.run(
                cast(
                    LiteralString,
                    f"""
                MATCH (u:User {{userId: $user_id}})-[r:{UserDAO.NEEDS_FEATURE}]->(f:Feature {{name: $feature}})
                DELETE r
                WITH (u IS NOT NULL AND f IS NOT NULL) AS relationship
                RETURN relationship
            """,
                ),
                user_id=user_id,
                feature=feature,
            )

            result = await result.single()
            return result.get("relationship")

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            if (
                await session.execute_write(
                    remove_need, user_id=user_id, feature=feature
                )
                is False
            ):
                raise NotFound(
                    f"User with userId {user_id} or feature '{feature}' does not exist"
                )
            return await session.execute_read(self.get_user_extended, user_id=user_id)

    async def user_has_rated_place(self, user_id: str, place_id: str) -> bool:
        async def find_rating(tx: AsyncManagedTransaction, user_id: str, place_id: str):
            result = await tx.run(
                cast(
                    LiteralString,
                    f"""
            MATCH (u:User {{userId: $user_id}})-[r:{UserDAO.RATED}]->(p:Place {{placeId: $place_id}})
            WITH (r IS NOT NULL) AS rating_exists
            RETURN rating_exists
            """,
                ),
                user_id=user_id,
                place_id=place_id,
            )

            result = await result.single()
            return result and result.get("rating_exists")

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return await session.execute_read(
                find_rating, user_id=user_id, place_id=place_id
            )

    async def rate_place(self, user_id: str, place_id: str, rating: float) -> bool:
        async def add_rating(
            tx: AsyncManagedTransaction, user_id: str, place_id: str, rating: float
        ):
            result = await tx.run(
                cast(
                    LiteralString,
                    f"""
            MATCH (u:User {{userId: $user_id}})
            MATCH (p:Place {{placeId: $place_id}})
            MERGE (u)-[r:{UserDAO.RATED}]->(p)
            SET r.rating = $rating
            RETURN (r IS NOT NULL) AS rating_exists
            """,
                ),
                user_id=user_id,
                place_id=place_id,
                rating=rating,
            )

            result = await result.single()
            return result and result.get("rating_exists")

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_write(
                add_rating, user_id=user_id, place_id=place_id, rating=rating
            )
            return True
