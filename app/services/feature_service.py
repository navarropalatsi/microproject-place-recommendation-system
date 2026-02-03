from neo4j import AsyncDriver

from app.dao.feature_dao import FeatureDAO
from app.dto.feature import SingleFeature
from app.config.exceptions import NotFound, AlreadyExists


class FeatureService:
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    async def get_all_features(
        self, sort: str = "name", order: str = "DESC", skip: int = 0, limit: int = 25
    ) -> list[SingleFeature]:
        async with self.driver.session() as session:
            elements = await session.execute_read(
                FeatureDAO.get_features, sort=sort, order=order, limit=limit, skip=skip
            )
            return [SingleFeature(name=item["name"]) for item in elements]

    async def get_single_feature(self, name: str) -> SingleFeature:
        async with self.driver.session() as session:
            element = await session.execute_read(FeatureDAO.get_feature, name)
            if element is None:
                raise NotFound(f"Feature {name} not found")
            return SingleFeature(name=element["name"])

    async def create_feature(self, name: str) -> SingleFeature:
        async with self.driver.session() as session:
            candidate = await session.execute_read(FeatureDAO.get_feature, name=name)
            if candidate is None:
                candidate = await session.execute_write(FeatureDAO.add, name=name)
                return SingleFeature(name=candidate["name"])
            else:
                raise AlreadyExists(f"Feature {name} already exists")

    async def update_feature(self, name: str, new_name: str) -> SingleFeature:
        async with self.driver.session() as session:
            candidate = await session.execute_read(FeatureDAO.get_feature, name=name)
            if candidate is None:
                raise NotFound(f"Feature {name} not found")
            else:
                candidate = await session.execute_write(
                    FeatureDAO.update, name=name, new_name=new_name
                )
                return SingleFeature(name=candidate["name"])

    async def delete_feature(self, name: str) -> bool:
        async with self.driver.session() as session:
            candidate = await session.execute_read(FeatureDAO.get_feature, name=name)
            if candidate is None:
                raise NotFound(f"Feature {name} not found")
            else:
                return await session.execute_write(FeatureDAO.remove, name=name)
