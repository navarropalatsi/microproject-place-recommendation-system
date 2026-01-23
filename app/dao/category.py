from typing import cast, LiteralString

from neo4j import ManagedTransaction, Driver
from neo4j.exceptions import ConstraintError
from werkzeug.exceptions import NotFound

from app.config.neo4j import validate_order, validate_field, validate_gender
from app.config.settings import settings
from app.dto.category import SingleCategory
from app.config.exceptions import NotFound

class CategoryDAO(object):
    def __init__(self, driver: Driver):
        self.driver = driver

    @staticmethod
    def get_category(tx: ManagedTransaction, name: str):
        result = tx.run(cast(LiteralString, """
        MATCH (c:Category {name: $name})
        RETURN c AS category
        """), name=name).single()

        if result and result.get('category'):
            return result.get('category')
        else:
            raise NotFound(f"Category with name {name} not found")

    def all(self, sort = "name", order = "DESC", skip = 0, limit = 25):
        def get_categories(tx: ManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(SingleCategory,sort):
                sort = "name"

            result = tx.run(cast(LiteralString, f"""
            MATCH (c:Category)
            ORDER BY c.{sort} {order}
            RETURN c AS category
            SKIP $skip LIMIT $limit 
            """), skip=skip, limit=limit)

            return [row.value('category') for row in result]

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(get_categories, sort, order, skip, limit)

    def find(self, name: str):
        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(self.get_category, name)

    def create(self, name: str):
        def add(tx: ManagedTransaction, name: str):
            result = tx.run("""
                MERGE (c:Category {name: $name})
                RETURN c AS category
            """, name=name).single()

            if result is not None:
                return result.get('category')
            return None

        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                return session.execute_write(add, name=name)
        except ConstraintError as e:
            print("ConstraintError detected: " + e.title)
            return None

    def delete(self, name: str):
        def remove(tx: ManagedTransaction, name: str):
            result = tx.run("""
                MATCH (c:Category {name: $name})
                DETACH DELETE c
                RETURN c AS category
            """, name=name).single()
            return result is not None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_category, name=name)
            return session.execute_write(remove, name=name)