from typing import cast, LiteralString

from neo4j import ManagedTransaction, Driver
from neo4j.exceptions import ConstraintError
from werkzeug.exceptions import NotFound

from app.config.exceptions import AlreadyExists
from app.config.neo4j import validate_order, validate_field, validate_gender
from app.config.settings import settings

class CategoryDAO(object):
    def __init__(self, driver: Driver):
        self.driver = driver

    @staticmethod
    def get_category(tx: ManagedTransaction, name: str):
        result = tx.run(cast(LiteralString, """
        MATCH (c:Category {name: $name})
        RETURN c AS category
        """), name=name, database_=settings.NEO4J_DATABASE).single()

        return result.get('category') if result is not None else None

    def all(self, sort = "name", order = "DESC", skip = 0, limit = 25):
        def get_categories(tx: ManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(sort):
                sort = "name"

            result = tx.run(cast(LiteralString, f"""
            MATCH (c:Category)
            ORDER BY f.{sort} {order}
            RETURN c AS category
            SKIP $skip LIMIT $limit 
            """), skip=skip, limit=limit, database_=settings.NEO4J_DATABASE)

            return [row.value('category') for row in result]

        with self.driver.session() as session:
            return session.execute_read(get_categories, sort, order, skip, limit)

    def find(self, name: str):
        with self.driver.session() as session:
            result = session.execute_read(self.get_category, name)
            if result is not None:
                return result
            else:
                raise NotFound(f"Category with name {name} not found")

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
            with self.driver.session() as session:
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

        with self.driver.session() as session:
            return session.execute_write(remove, name=name)