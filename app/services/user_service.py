import datetime
from typing import Literal

from fastapi import Depends
from neo4j import AsyncDriver

from app.dao.feature_dao import FeatureDAO
from app.dao.user_dao import UserDAO
from app.dto.user import SingleUser, SingleUserExtended
from app.config.exceptions import NotFound, AlreadyExists
from app.services.feature_service import FeatureService


class UserService:
    def __init__(
        self,
        driver: AsyncDriver,
        feature_service: FeatureService = Depends(FeatureService),
    ):
        self.driver = driver
        self.feature_service = feature_service

    async def get_all_users(
        self, sort: str = "user_id", order: str = "DESC", skip: int = 0, limit: int = 25
    ) -> list[SingleUser]:
        async with self.driver.session() as session:
            elements = await session.execute_read(
                UserDAO.get_users, sort=sort, order=order, limit=limit, skip=skip
            )
            return [item.get("user") for item in elements]

    async def get_user_by_id(self, user_id: str) -> SingleUserExtended:
        async with self.driver.session() as session:
            item = await session.execute_read(
                UserDAO.get_user_extended, user_id=user_id
            )
            if item is not None:
                return SingleUserExtended(**item.get("user"))
            else:
                raise NotFound(f"User with user_id {user_id} was not found.")

    async def create_user(
        self, user_id: str, born: datetime.date, gender: Literal["m", "f"] | None
    ) -> SingleUser:
        async with self.driver.session() as session:
            item = session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is None:
                item = await session.execute_write(
                    UserDAO.add, user_id=user_id, born=str(born), gender=gender
                )
                return SingleUser(**item.get("user"))
            else:
                raise AlreadyExists(f"User with user_id {user_id} already exists.")

    async def update_user(
        self, user_id: str, born: datetime.date, gender: Literal["m", "f"] | None
    ) -> SingleUser:
        async with self.driver.session() as session:
            item = session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is not None:
                item = await session.execute_write(
                    UserDAO.modify, user_id=user_id, born=str(born), gender=gender
                )
                return SingleUser(**item.get("user"))
            else:
                raise NotFound(f"User with user_id {user_id} was not found.")

    async def delete_user(self, user_id: str) -> bool:
        async with self.driver.session() as session:
            item = session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is not None:
                return await session.execute_write(UserDAO.remove, user_id=user_id)
            else:
                raise NotFound(f"User with user_id {user_id} was not found.")

    async def attach_requested_feature_to_user(
        self, user_id: str, feature: str
    ) -> bool:
        async with self.driver.session() as session:
            item = session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is None:
                raise NotFound(f"User with user_id {user_id} was not found.")
            feature = await self.feature_service.get_single_feature(name=feature)
            session.execute_write(
                UserDAO.add_feature, user_id=user_id, feature=feature.name
            )
            return True

    async def detach_requested_feature_to_user(
        self, user_id: str, feature: str
    ) -> bool:
        async with self.driver.session() as session:
            item = session.execute_read(UserDAO.get_user, user_id=user_id)
            if item is None:
                raise NotFound(f"User with user_id {user_id} was not found.")
            feature = await self.feature_service.get_single_feature(name=feature)
            session.execute_write(
                UserDAO.remove_feature, user_id=user_id, feature=feature.name
            )
            return True
