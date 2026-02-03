from typing import cast, LiteralString, Literal

from neo4j import AsyncDriver, AsyncManagedTransaction
from app.config.exceptions import InvalidValue
from app.config.neo4j import validate_order, validate_field, validate_gender
from app.dto.user import SingleUser


class UserDAO(object):
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    RATED = "RATED"
    NEEDS_FEATURE = "NEEDS_FEATURE"

    @staticmethod
    async def get_user(tx: AsyncManagedTransaction, user_id: str):
        result = await tx.run(
            "MATCH (u:User {userId: $user_id}) RETURN u AS user",
            user_id=user_id,
        )

        result = await result.single()
        return result.get("user") if result else None

    @staticmethod
    async def get_user_extended(tx: AsyncManagedTransaction, user_id: str):
        query = cast(
            LiteralString,
            f"""
            MATCH (u:User {{userId: $user_id}})
            OPTIONAL MATCH (u)-[:{UserDAO.NEEDS_FEATURE}]->(f:Feature)
            WITH u, collect(f) AS Feats
            RETURN u {{ .*, features: Feats }} AS user """,
        )

        result = await tx.run(query, user_id=user_id)

        result = await result.single()
        return result.get("user") if result else None

    @staticmethod
    async def get_users(
        tx: AsyncManagedTransaction, sort="userId", order="DESC", skip=0, limit=25
    ):
        if not validate_order(order):
            order = "DESC"
        if not validate_field(SingleUser, sort):
            sort = "userId"

        query = cast(
            LiteralString,
            f"""
            MATCH (u:User)
            ORDER BY u.{sort} {order}
            RETURN u AS user 
            SKIP $skip LIMIT $limit """,
        )

        result = await tx.run(
            query,
            skip=skip,
            limit=limit,
        )

        return [row.value("user") async for row in result]

    @staticmethod
    async def add(
        tx: AsyncManagedTransaction,
        user_id: str,
        born: str,
        gender: Literal["m", "f"] | None,
    ):
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
        return result.get("user") if result else None

    @staticmethod
    async def modify(
        tx: AsyncManagedTransaction,
        user_id: str,
        born: str,
        gender: Literal["m", "f"] | None,
    ):
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
        return result.get("user") if result else None

    @staticmethod
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

    @staticmethod
    async def add_feature(
        tx: AsyncManagedTransaction, user_id: str, feature: str
    ) -> bool:
        query = cast(
            LiteralString,
            f"""
            MATCH (u:User {{userId: $user_id}})
            MATCH (f:Feature {{name: $feature}})
            MERGE (u)-[:{UserDAO.NEEDS_FEATURE}]->(f)
            RETURN u AS user """,
        )

        result = await tx.run(
            query,
            user_id=user_id,
            feature=feature,
        )

        result = await result.single()
        return result is not None

    @staticmethod
    async def remove_feature(tx: AsyncManagedTransaction, user_id: str, feature: str):
        query = cast(
            LiteralString,
            f"""
            MATCH (u:User {{userId: $user_id}})-[r:{UserDAO.NEEDS_FEATURE}]->(f:Feature {{name: $feature}})
            DELETE r
            WITH (u IS NOT NULL AND f IS NOT NULL) AS relationship
            RETURN relationship """,
        )

        result = await tx.run(
            query,
            user_id=user_id,
            feature=feature,
        )

        result = await result.single()
        return result.get("relationship") if result else None

    @staticmethod
    async def find_rating(tx: AsyncManagedTransaction, user_id: str, place_id: str):
        query = cast(
            LiteralString,
            f"""
            MATCH (u:User {{userId: $user_id}})-[r:{UserDAO.RATED}]->(p:Place {{placeId: $place_id}})
            WITH (r IS NOT NULL) AS rating_exists
            RETURN rating_exists """,
        )

        result = await tx.run(
            query,
            user_id=user_id,
            place_id=place_id,
        )

        result = await result.single()
        return result and result.get("rating_exists")

    @staticmethod
    async def add_rating(
        tx: AsyncManagedTransaction, user_id: str, place_id: str, rating: float
    ) -> bool:
        query = cast(
            LiteralString,
            f"""
            MATCH (u:User {{userId: $user_id}})
            MATCH (p:Place {{placeId: $place_id}})
            MERGE (u)-[r:{UserDAO.RATED}]->(p)
            SET r.rating = $rating
            RETURN (r IS NOT NULL) AS rating_exists """,
        )

        result = await tx.run(
            query,
            user_id=user_id,
            place_id=place_id,
            rating=rating,
        )

        result = await result.single()
        return result and result.get("rating_exists")
