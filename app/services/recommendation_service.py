from neo4j import AsyncDriver

from app.config.exceptions import InvalidValue
from app.config.settings import settings
from app.dao.recommendation_dao import RecommendationDAO
from app.dto.place import SinglePlaceRecommended
from app.services.category_service import CategoryService
from app.services.user_service import UserService


class RecommendationService:
    def __init__(
        self,
        driver: AsyncDriver,
        category_service: CategoryService,
        user_service: UserService,
    ):
        self.driver = driver
        self.category_service = category_service
        self.user_service = user_service

    MAXIMUM_MAX_DISTANCE_VALUE: int = 100000

    async def recommend_places_near_by_affinity(
        self,
        user_id: str,
        base_category: str,
        latitude: float,
        longitude: float,
        max_distance_meters: int,
        skip: int = 0,
        limit: int = 10,
    ) -> list[SinglePlaceRecommended]:

        # Parameter validation
        await self.user_service.get_user_by_id(user_id=user_id)
        await self.category_service.get_single_category(name=base_category)
        if max_distance_meters > self.MAXIMUM_MAX_DISTANCE_VALUE:
            raise InvalidValue(
                f"Max distance parameter must be less or equal than {self.MAXIMUM_MAX_DISTANCE_VALUE}"
            )

        # Query execution
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            items = await session.execute_read(
                RecommendationDAO.recommend_places_near_by_affinity,
                user_id=user_id,
                base_category=base_category,
                latitude=latitude,
                longitude=longitude,
                max_distance_meters=max_distance_meters,
                skip=skip,
                limit=limit,
            )

            # Data transformation
            return [SinglePlaceRecommended(**item) for item in items]
