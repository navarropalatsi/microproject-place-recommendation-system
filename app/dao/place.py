from typing import cast, LiteralString, Any

from neo4j import AsyncDriver, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.config.neo4j import validate_order, validate_field
from app.config.settings import settings
from app.dto.place import SinglePlace
from app.config.exceptions import NotFound, AlreadyExists


class PlaceDAO(object):
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    @staticmethod
    async def get_place(tx: AsyncManagedTransaction, placeId: str):
        result = await tx.run(
            cast(
                LiteralString,
                """
        MATCH (p:Place {placeId: $placeId})
        RETURN p AS place
        """,
            ),
            placeId=placeId,
        )

        result = await result.single()
        if result and result.get("place"):
            return result.get("place")
        else:
            raise NotFound(f"Place with placeId {placeId} not found")

    @staticmethod
    async def get_place_extended(tx: AsyncManagedTransaction, placeId: str):
        result = await tx.run(
            """
            MATCH (p:Place {placeId: $placeId})
            OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f:Feature)
            OPTIONAL MATCH (p)-[:IN_CATEGORY]->(c:Category)
            WITH p, collect(c) AS Cats, collect(f) AS Feats
            RETURN p { .*, features: Feats, categories: Cats } AS place
        """,
            placeId=placeId,
        )

        result = await result.single()
        if result and result.get("place"):
            return result.get("place")
        else:
            raise NotFound(f"[EXT] Place with placeId {placeId} not found")

    async def all(self, sort="placeId", order="DESC", skip=0, limit=25):
        async def get_places(tx: AsyncManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(SinglePlace, sort):
                sort = "placeId"

            result = await tx.run(
                cast(
                    LiteralString,
                    f"""
            MATCH (p:Place)
            ORDER BY p.{sort} {order}
            RETURN p AS place
            SKIP $skip LIMIT $limit 
            """,
                ),
                skip=skip,
                limit=limit,
            )

            return [row.value("place") async for row in result]

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return await session.execute_read(get_places, sort, order, skip, limit)

    async def find(self, placeId: str):
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return await session.execute_read(self.get_place, placeId)

    async def create(self, placeId: str, data: dict[str, Any]):
        async def add(tx: AsyncManagedTransaction, placeId: str, data: dict[str, Any]):
            result = await tx.run(
                """
                CREATE (p:Place {placeId: $placeId})
                FOREACH (k IN keys($data) | SET p[k]=$data[k])
                RETURN p AS place
            """,
                placeId=placeId,
                data=data,
            )

            result = await result.single()
            if result is not None:
                return result.get("place")
            return None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            try:
                return await session.execute_write(add, placeId=placeId, data=data)
            except ConstraintError:
                raise AlreadyExists(f"Place with id {placeId} already exists")

    async def update(self, placeId: str, data: dict[str, Any]):
        async def modify(
            tx: AsyncManagedTransaction, placeId: str, data: dict[str, Any]
        ):
            result = await tx.run(
                """
                MATCH (p:Place {placeId: $placeId})
                FOREACH (k IN keys($data) | SET p[k]=$data[k])
                RETURN p AS place
            """,
                placeId=placeId,
                data=data,
            )

            result = await result.single()
            if result is not None:
                return result.get("place")
            return None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_read(self.get_place, placeId=placeId)
            return await session.execute_write(modify, placeId=placeId, data=data)

    async def delete(self, placeId: str):
        async def remove(tx: AsyncManagedTransaction, placeId: str):
            result = await tx.run(
                """
                MATCH (p:Place {placeId: $placeId})
                DETACH DELETE p
                RETURN p AS place
            """,
                placeId=placeId,
            )

            result = await result.single()
            return result is not None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_read(self.get_place, placeId=placeId)
            return await session.execute_write(remove, placeId=placeId)

    async def add_feature(self, placeId: str, feature: str):
        async def add_place_feature(
            tx: AsyncManagedTransaction, placeId: str, feature: str
        ):
            result = await tx.run(
                """
                MATCH (p:Place {placeId: $placeId})
                MATCH (f:Feature {name: $feature})
                MERGE (p)-[:HAS_FEATURE]->(f)
                RETURN p AS place
            """,
                placeId=placeId,
                feature=feature,
            )

            result = await result.single()
            return result.get("place")

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_read(self.get_place, placeId=placeId)
            await session.execute_write(
                add_place_feature, placeId=placeId, feature=feature
            )
            return await session.execute_read(self.get_place_extended, placeId=placeId)

    async def remove_feature(self, placeId: str, feature: str):
        async def remove_place_feature(
            tx: AsyncManagedTransaction, placeId: str, feature: str
        ):
            result = await tx.run(
                """
                MATCH (p:Place {placeId: $placeId})-[r:HAS_FEATURE]->(f:Feature {name: $feature})
                DELETE r
                RETURN r AS relationship
            """,
                placeId=placeId,
                feature=feature,
            )

            result = await result.single()
            return result is None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_read(self.get_place, placeId=placeId)
            await session.execute_write(
                remove_place_feature, placeId=placeId, feature=feature
            )
            return await session.execute_read(self.get_place_extended, placeId=placeId)

    async def add_category(self, placeId: str, category: str):
        async def add_place_category(
            tx: AsyncManagedTransaction, placeId: str, category: str
        ):
            result = await tx.run(
                """
                MATCH (p:Place {placeId: $placeId})
                MATCH (c:Category {name: $category})
                MERGE (p)-[:IN_CATEGORY]->(c)
                RETURN p AS place
            """,
                placeId=placeId,
                category=category,
            )

            result = await result.single()
            return result.get("place")

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_read(self.get_place, placeId=placeId)
            await session.execute_write(
                add_place_category, placeId=placeId, category=category
            )
            return await session.execute_read(self.get_place_extended, placeId=placeId)

    async def remove_category(self, placeId: str, category: str):
        async def remove_place_category(
            tx: AsyncManagedTransaction, placeId: str, category: str
        ):
            result = await tx.run(
                """
                MATCH (p:Place {placeId: $placeId})-[r:IN_CATEGORY]->(c:Category {name: $category})
                DELETE r
                RETURN r AS relationship
            """,
                placeId=placeId,
                category=category,
            )

            result = await result.single()
            return result is None

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.execute_read(self.get_place, placeId=placeId)
            await session.execute_write(
                remove_place_category, placeId=placeId, category=category
            )
            return await session.execute_read(self.get_place_extended, placeId=placeId)

    async def recommend_places_near_by_affinity(
        self,
        user_id: str,
        base_category: str,
        latitude: float,
        longitude: float,
        max_distance_meters: int,
        skip: int = 0,
        limit: int = 10,
    ):
        async def get_places(
            tx: AsyncManagedTransaction,
            user_id: str,
            base_category: str,
            latitude: float,
            longitude: float,
            max_distance_meters: int,
            skip: int,
            limit: int,
        ):
            result = await tx.run(
                """
            // EXPLAIN
            WITH point({latitude: $latitude, longitude: $longitude}) AS pointRef

            // Obtenim les categories ben valorades per part de l'usuari "0" 
            MATCH (user:User {userId: $user_id})-[r:RATED]->(:Place)-[:IN_CATEGORY]->(ratedCategory:Category)
            WITH 
              pointRef, 
              ratedCategory,
              avg(r.rating) AS weight

            WITH 
              pointRef,
              collect(ratedCategory) AS likedCategories,
              apoc.map.fromPairs(collect([ratedCategory.name, weight])) AS weightMap

            // Busquem tots els llocs a menys de 30 km del punt de referència
            // que estiguin relacionats amb la categoria restaurant
            MATCH (candidate:Place)
            WHERE 
              point.distance(candidate.coordinates, pointRef) < $max_distance_meters
              AND EXISTS { (candidate)-[:IN_CATEGORY]->(:Category {name: $base_category}) }

            MATCH (candidate)-[:IN_CATEGORY]->(cat:Category)
            WHERE cat IN likedCategories 

            // Computem els valors a retornar
            WITH 
              candidate, 
              pointRef,
              sum(weightMap[cat.name]) AS totalAffinityScore,
              collect({name: cat.name, avgRating: weightMap[cat.name]}) AS matches,
              point.distance(candidate.coordinates, pointRef) AS distance

            WITH 
              *,
              (totalAffinityScore - (distance / 200)) AS finalScore

            // Ordenem per distància més propera 
            ORDER BY  finalScore DESC
            // Retornem els candidats
            RETURN candidate { .*, matches: matches, distance} as place
            SKIP $skip LIMIT $limit
            """,
                user_id=user_id,
                latitude=latitude,
                longitude=longitude,
                base_category=base_category,
                max_distance_meters=max_distance_meters,
                skip=skip,
                limit=limit,
            )

            if result is None:
                return []
            else:
                return [row.value("place") async for row in result]

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return await session.execute_read(
                get_places,
                user_id=user_id,
                base_category=base_category,
                latitude=latitude,
                longitude=longitude,
                max_distance_meters=max_distance_meters,
                skip=skip,
                limit=limit,
            )
