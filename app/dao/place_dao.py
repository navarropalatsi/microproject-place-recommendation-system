from typing import cast, LiteralString, Any

from neo4j import AsyncDriver, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.config.neo4j import validate_order, validate_field
from app.config.settings import settings
from app.dto.place import SinglePlace, SinglePlaceExtended, SinglePlaceRecommended
from app.config.exceptions import NotFound, AlreadyExists


class PlaceDAO(object):
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    @staticmethod
    async def get_place(tx: AsyncManagedTransaction, placeId: str) -> SinglePlace:
        result = await tx.run(
            "MATCH (p:Place {placeId: $placeId}) RETURN p AS place",
            placeId=placeId,
        )

        result = await result.single()
        return result.get("place") if result else None

    @staticmethod
    async def get_place_by_yelp_id(
        tx: AsyncManagedTransaction, yelpId: str
    ) -> SinglePlace:
        result = await tx.run(
            "MATCH (p:Place {yelpId: $yelpId}) RETURN p AS place",
            yelpId=yelpId,
        )

        result = await result.single()
        return result.get("place") if result else None

    @staticmethod
    async def get_place_by_name_and_position(
        tx: AsyncManagedTransaction,
        name: str,
        latitude: float,
        longitude: float,
        max_distance_meters: int,
    ) -> SinglePlaceRecommended:
        result = await tx.run(
            """
        WITH point({latitude: $latitude, longitude: $longitude}) AS pointRef
        MATCH (candidate:Place)
        WHERE 
            point.distance(candidate.coordinates, pointRef) < $max_distance_meters AND
            apoc.text.sorensenDiceSimilarity(candidate.name, $name) > 0.5
        WITH 
            candidate,
            point.distance(candidate.coordinates, pointRef) < $max_distance_meters AS distance ,
            apoc.text.sorensenDiceSimilarity(candidate.name, $name) AS score
        ORDER BY distance ASC, score DESC
        LIMIT 1
        RETURN candidate { .*, distance: distance, score: score } AS place
        """,
            name=name,
            latitude=latitude,
            longitude=longitude,
            max_distance_meters=max_distance_meters,
        )

        result = await result.single()
        return result.get("place") if result else None

    @staticmethod
    async def get_place_extended(
        tx: AsyncManagedTransaction, placeId: str
    ) -> SinglePlaceExtended:
        result = await tx.run(
            """
            MATCH (p:Place {placeId: $placeId})
            OPTIONAL MATCH (p)-->(f:Feature)
            OPTIONAL MATCH (p)-->(c:Category)
            WITH p, collect(c) AS Cats, collect(f) AS Feats
            RETURN p { .*, features: Feats, categories: Cats } AS place
        """,
            placeId=placeId,
        )

        result = await result.single()
        return result.get("place") if result else None

    @staticmethod
    async def get_places(
        tx: AsyncManagedTransaction, sort="placeId", order="DESC", skip=0, limit=25
    ) -> list[SinglePlace]:
        if not validate_order(order):
            order = "DESC"
        if not validate_field(SinglePlace, sort):
            sort = "placeId"

        query = cast(
            LiteralString,
            f"""MATCH (p:Place)
            ORDER BY p.{sort} {order}
            RETURN p AS place
            SKIP $skip LIMIT $limit """,
        )

        result = await tx.run(
            query,
            skip=skip,
            limit=limit,
        )

        return [row.value("place") async for row in result]

    @staticmethod
    async def add(
        tx: AsyncManagedTransaction, placeId: str, data: dict[str, Any]
    ) -> SinglePlace:
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
        return result.get("place") if result else None

    @staticmethod
    async def modify(
        tx: AsyncManagedTransaction, placeId: str, data: dict[str, Any]
    ) -> SinglePlace:
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
        return result.get("place") if result else None

    @staticmethod
    async def remove(tx: AsyncManagedTransaction, placeId: str) -> bool:
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

    @staticmethod
    async def add_place_feature(
        tx: AsyncManagedTransaction, placeId: str, feature: str
    ) -> bool:
        result = await tx.run(
            """
            MATCH (p:Place {placeId: $placeId})
            MATCH (f:Feature {name: $feature})
            MERGE (p)-[:HAS_FEATURE]->(f)
            WITH (p IS NOT NULL AND f IS NOT NULL) AS result
            RETURN result
        """,
            placeId=placeId,
            feature=feature,
        )

        result = await result.single()
        return result.get("result") if result else None

    @staticmethod
    async def remove_place_feature(
        tx: AsyncManagedTransaction, placeId: str, feature: str
    ) -> bool:
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

    @staticmethod
    async def add_place_category(
        tx: AsyncManagedTransaction, placeId: str, category: str
    ) -> bool:
        result = await tx.run(
            """
            MATCH (p:Place {placeId: $placeId})
            MATCH (c:Category {name: $category})
            MERGE (p)-[:IN_CATEGORY]->(c)
            WITH (p IS NOT NULL AND c IS NOT NULL) AS result
            RETURN result
        """,
            placeId=placeId,
            category=category,
        )

        result = await result.single()
        return result.get("result") if result else None

    @staticmethod
    async def remove_place_category(
        tx: AsyncManagedTransaction, placeId: str, category: str
    ) -> bool:
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

    @staticmethod
    async def recommend_places_near_by_affinity(
        tx: AsyncManagedTransaction,
        user_id: str,
        base_category: str,
        latitude: float,
        longitude: float,
        max_distance_meters: int,
        skip: int,
        limit: int,
    ) -> list[SinglePlaceRecommended]:
        query = cast(
            LiteralString,
            """
        WITH point({latitude: $latitude, longitude: $longitude}) AS pointRef

        MATCH (user:User {userId: $user_id})-[r:RATED]->(:Place)-->(ratedCategory:Category)
        WITH 
          pointRef, 
          ratedCategory,
          avg(r.rating) AS weight

        WITH 
          pointRef,
          collect(ratedCategory) AS likedCategories,
          apoc.map.fromPairs(collect([ratedCategory.name, weight])) AS weightMap

        MATCH (candidate:Place)
        WHERE 
          point.distance(candidate.coordinates, pointRef) < $max_distance_meters
          AND EXISTS { (candidate)-->(:Category {name: $base_category}) }

        MATCH (candidate)-->(cat:Category)
        WHERE cat IN likedCategories 

        WITH 
          candidate, 
          pointRef,
          sum(weightMap[cat.name]) AS totalAffinityScore,
          collect({name: cat.name, avgRating: weightMap[cat.name]}) AS matches,
          point.distance(candidate.coordinates, pointRef) AS distance

        WITH 
          *,
          (totalAffinityScore - (distance / 200)) AS finalScore

        ORDER BY finalScore DESC
        RETURN candidate { .*, matches: matches, distance} as place
        SKIP $skip LIMIT $limit
        """,
        )

        result = await tx.run(
            query,
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            base_category=base_category,
            max_distance_meters=max_distance_meters,
            skip=skip,
            limit=limit,
        )

        return [row.value("place") async for row in result] if result else []
