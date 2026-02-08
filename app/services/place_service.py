from typing import Any
from neo4j import AsyncDriver

from app.config.settings import settings
from app.dao.place_dao import PlaceDAO
from app.dto.place import SinglePlace, SinglePlaceExtended, SinglePlaceRecommended
from app.config.exceptions import NotFound, AlreadyExists
from app.services.category_service import CategoryService
from app.services.feature_service import FeatureService


class PlaceService:
    def __init__(
        self,
        driver: AsyncDriver,
        feature_service: FeatureService,
        category_service: CategoryService,
    ) -> None:
        self.driver = driver
        self.feature_service = feature_service
        self.category_service = category_service

    async def get_all_places(
        self, sort="placeId", order="DESC", skip=0, limit=25
    ) -> list[SinglePlace]:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            items = await session.execute_read(
                PlaceDAO.get_places, sort=sort, order=order, skip=skip, limit=limit
            )
            return [SinglePlace(**item) for item in items]

    async def get_place(self, placeId: str) -> SinglePlaceExtended:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(
                PlaceDAO.get_place_extended, placeId=placeId
            )
            if item:
                return SinglePlaceExtended(**item)
            else:
                raise NotFound(f"Place with id {placeId} was not found.")

    async def get_place_by_yelp_id(self, yelpId: str) -> SinglePlace | None:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(
                PlaceDAO.get_place_by_yelp_id, yelpId=yelpId
            )
            if item:
                return SinglePlace(**item)
            return None

    async def get_place_by_name_and_position(
        self,
        name: str,
        latitude: float,
        longitude: float,
        max_distance_meters: int = 200,
    ) -> SinglePlaceRecommended | None:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(
                PlaceDAO.get_place_by_name_and_position,
                name=name,
                latitude=latitude,
                longitude=longitude,
                max_distance_meters=max_distance_meters,
            )
            if item:
                return SinglePlaceRecommended(**item)
            return None

    async def create_place(self, placeId: str, data: dict[str, Any]) -> SinglePlace:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                raise AlreadyExists(f"Place with id {placeId} already exists.")
            else:
                item = await session.execute_write(
                    PlaceDAO.add, placeId=placeId, data=data
                )
                return SinglePlace(**item)

    async def update_place(self, placeId: str, data: dict[str, Any]) -> SinglePlace:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            data["placeId"] = placeId
            if item:
                item = await session.execute_write(
                    PlaceDAO.modify, placeId=placeId, data=data
                )
                return SinglePlace(**item)
            else:
                raise NotFound(f"Place with id {placeId} was not found.")

    async def delete_place(self, placeId: str) -> bool:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                return await session.execute_write(PlaceDAO.remove, placeId=placeId)
            else:
                raise NotFound(f"Place with id {placeId} was not found.")

    async def attach_feature_to_place(self, placeId: str, feature: str) -> bool:
        await self.feature_service.get_single_feature(name=feature)
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                result = await session.execute_write(
                    PlaceDAO.add_place_feature, placeId=placeId, feature=feature
                )
                return result
            else:
                raise NotFound(f"Place with id {placeId} was not found.")

    async def detach_feature_from_place(self, placeId: str, feature: str) -> bool:
        await self.feature_service.get_single_feature(name=feature)
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                result = await session.execute_write(
                    PlaceDAO.remove_place_feature, placeId=placeId, feature=feature
                )
                return result
            else:
                raise NotFound(f"Place with id {placeId} was not found.")

    async def attach_category_to_place(self, placeId: str, category: str) -> bool:
        await self.category_service.get_single_category(name=category)
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                result = await session.execute_write(
                    PlaceDAO.add_place_category, placeId=placeId, category=category
                )
                return result
            else:
                raise NotFound(f"Place with id {placeId} was not found.")

    async def detach_category_from_place(self, placeId: str, category: str) -> bool:
        await self.category_service.get_single_category(name=category)
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                result = await session.execute_write(
                    PlaceDAO.remove_place_category, placeId=placeId, category=category
                )
                return result
            else:
                raise NotFound(f"Place with id {placeId} was not found.")
