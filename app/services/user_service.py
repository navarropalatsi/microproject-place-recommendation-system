import datetime
from typing import Literal

from neo4j import AsyncDriver

from app.config.settings import settings
from app.dao.user_dao import UserDAO
from app.dto.user import SingleUser, SingleUserExtended
from app.config.exceptions import NotFound, AlreadyExists
from app.services.feature_service import FeatureService
from app.services.place_service import PlaceService


class UserService:
    def __init__(
        self,
        driver: AsyncDriver,
        feature_service: FeatureService,
        place_service: PlaceService,
    ):
        self.driver = driver
        self.feature_service = feature_service
        self.place_service = place_service

    async def get_all_users(
        self, sort: str = "user_id", order: str = "DESC", skip: int = 0, limit: int = 25
    ) -> list[SingleUser]:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            elements = await session.execute_read(
                UserDAO.get_users, sort=sort, order=order, limit=limit, skip=skip
            )
            return [SingleUser(**item) for item in elements]

    async def get_user_by_id(self, user_id: str) -> SingleUserExtended:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(
                UserDAO.get_user_extended, user_id=user_id
            )
            if item is not None:
                return SingleUserExtended(**item)
            else:
                raise NotFound(f"User with user_id {user_id} was not found.")

    async def create_user(
        self, user_id: str, born: datetime.date, gender: Literal["m", "f"] | None
    ) -> SingleUser:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is None:
                item = await session.execute_write(
                    UserDAO.add, user_id=user_id, born=str(born), gender=gender
                )
                return SingleUser(**item)
            else:
                raise AlreadyExists(f"User with user_id {user_id} already exists.")

    async def update_user(
        self, user_id: str, born: datetime.date, gender: Literal["m", "f"] | None
    ) -> SingleUser:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is not None:
                item = await session.execute_write(
                    UserDAO.modify, user_id=user_id, born=str(born), gender=gender
                )
                return SingleUser(**item)
            else:
                raise NotFound(f"User with user_id {user_id} was not found.")

    async def delete_user(self, user_id: str) -> bool:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is not None:
                return await session.execute_write(UserDAO.remove, user_id=user_id)
            else:
                raise NotFound(f"User with user_id {user_id} was not found.")

    async def attach_requested_feature_to_user(
        self, user_id: str, feature: str
    ) -> bool:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is None:
                raise NotFound(f"User with user_id {user_id} was not found.")
            feature = await self.feature_service.get_single_feature(name=feature)
            await session.execute_write(
                UserDAO.add_feature, user_id=user_id, feature=feature.name
            )
            return True

    async def detach_requested_feature_to_user(
        self, user_id: str, feature: str
    ) -> bool:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            item = await session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is None:
                raise NotFound(f"User with user_id {user_id} was not found.")
            feature = await self.feature_service.get_single_feature(name=feature)
            await session.execute_write(
                UserDAO.remove_feature, user_id=user_id, feature=feature.name
            )
            return True

    async def rate_place(self, user_id: str, place_id: str, rating: float) -> bool:
        await self.get_user_by_id(user_id=user_id)
        await self.place_service.get_place(placeId=place_id)
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return await session.execute_write(
                UserDAO.add_rating, user_id=user_id, rating=rating, place_id=place_id
            )
