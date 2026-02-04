from neo4j import AsyncDriver

from app.config.settings import settings
from app.dao.category_dao import CategoryDAO
from app.dto.category import SingleCategory
from app.config.exceptions import NotFound, AlreadyExists


class CategoryService:
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    async def get_all_categories(
        self, sort: str = "name", order: str = "DESC", skip: int = 0, limit: int = 25
    ) -> list[SingleCategory]:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            elements = await session.execute_read(
                CategoryDAO.get_categories,
                sort=sort,
                order=order,
                limit=limit,
                skip=skip,
            )
            return [SingleCategory(name=item["name"]) for item in elements]

    async def get_single_category(self, name: str) -> SingleCategory:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            element = await session.execute_read(CategoryDAO.get_category, name)
            if element is None:
                raise NotFound(f"Category {name} not found")
            return SingleCategory(name=element["name"])

    async def create_category(self, name: str) -> SingleCategory:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            candidate = await session.execute_read(CategoryDAO.get_category, name=name)
            if candidate is None:
                candidate = await session.execute_write(CategoryDAO.add, name=name)
                return SingleCategory(name=candidate["name"])
            else:
                raise AlreadyExists(f"Category {name} already exists")

    async def update_category(self, name: str, new_name: str) -> SingleCategory:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            candidate = await session.execute_read(CategoryDAO.get_category, name=name)
            if candidate is None:
                raise NotFound(f"Category {name} not found")
            else:
                candidate = await session.execute_write(
                    CategoryDAO.update, name=name, new_name=new_name
                )
                return SingleCategory(name=candidate["name"])

    async def delete_category(self, name: str) -> bool:
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            candidate = await session.execute_read(CategoryDAO.get_category, name=name)
            if candidate is None:
                raise NotFound(f"Category {name} not found")
            else:
                return await session.execute_write(CategoryDAO.remove, name=name)
