from typing import cast, LiteralString, Any

from neo4j import AsyncDriver, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.config.neo4j import validate_order, validate_field
from app.config.settings import settings
from app.dto.place import SinglePlace, SinglePlaceExtended, SinglePlaceRecommended
from app.config.exceptions import NotFound, AlreadyExists


class RecommendationDAO(object):
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

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

        MATCH (user:User {userId: $user_id})-[r:RATED]->(:Place)-[:IN_CATEGORY]->(ratedCategory:Category)
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
          AND EXISTS { (candidate)-[:IN_CATEGORY]->(:Category {name: $base_category}) }

        MATCH (candidate)-[:IN_CATEGORY]->(cat:Category)
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
