from typing import Any

from fastapi.params import Depends
from neo4j import AsyncDriver

from app.dao.place_dao import PlaceDAO
from app.dto.place import SinglePlace, SinglePlaceExtended
from app.config.exceptions import NotFound, AlreadyExists
from app.config.dependencies import get_feature_service, get_category_service
from app.services.category_service import CategoryService
from app.services.feature_service import FeatureService


class PlaceService:
    def __init__(
        self,
        driver: AsyncDriver,
        feature_service: FeatureService = Depends(get_feature_service),
        category_service: CategoryService = Depends(get_category_service),
    ) -> None:
        self.driver = driver
        self.feature_service = feature_service
        self.category_service = category_service

    async def get_all_places(
        self, sort="placeId", order="DESC", skip=0, limit=25
    ) -> list[SinglePlace]:
        async with self.driver.session() as session:
            items = await session.execute_read(
                PlaceDAO.get_places, sort=sort, order=order, skip=skip, limit=limit
            )
            return [SinglePlace(**item) for item in items]

    async def get_place(self, placeId: str) -> SinglePlace:
        async with self.driver.session() as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                return SinglePlaceExtended(**item)
            else:
                raise NotFound(f"Place with id {placeId} was not found.")

    async def create_place(self, placeId: str, data: dict[str, Any]) -> SinglePlace:
        async with self.driver.session() as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                raise AlreadyExists(f"Place with id {placeId} already exists.")
            else:
                item = await session.execute_write(
                    PlaceDAO.add, placeId=placeId, data=data
                )
                return SinglePlace(**item)

    async def update_place(self, placeId: str, data: dict[str, Any]) -> SinglePlace:
        async with self.driver.session() as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                item = await session.execute_write(
                    PlaceDAO.add, placeId=placeId, data=data
                )
                return SinglePlace(**item)
            else:
                raise NotFound(f"Place with id {placeId} was not found.")

    async def delete_place(self, placeId: str) -> bool:
        async with self.driver.session() as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                return await session.execute_write(PlaceDAO.remove, placeId=placeId)
            else:
                raise NotFound(f"Place with id {placeId} was not found.")

    async def attach_feature_to_place(self, placeId: str, feature: str) -> bool:
        await self.feature_service.get_single_feature(name=feature)
        async with self.driver.session() as session:
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
        async with self.driver.session() as session:
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
        async with self.driver.session() as session:
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
        async with self.driver.session() as session:
            item = await session.execute_read(PlaceDAO.get_place, placeId=placeId)
            if item:
                result = await session.execute_write(
                    PlaceDAO.remove_place_category, placeId=placeId, category=category
                )
                return result
            else:
                raise NotFound(f"Place with id {placeId} was not found.")
