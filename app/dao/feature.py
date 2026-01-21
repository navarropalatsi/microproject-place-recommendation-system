from typing import cast, LiteralString

from neo4j import ManagedTransaction, Driver
from neo4j.exceptions import ConstraintError
from werkzeug.exceptions import NotFound

from app.config.exceptions import AlreadyExists
from app.config.neo4j import validate_order, validate_field, validate_gender
from app.config.settings import settings

class FeatureDAO(object):
    def __init__(self, driver: Driver):
        self.driver = driver

    @staticmethod
    def get_feature(tx: ManagedTransaction, name: str):
        result = tx.run(cast(LiteralString, """
        MATCH (f:Feature {name: $name})
        RETURN f AS feature
        """), name=name, database_=settings.NEO4J_DATABASE).single()

        return result.get('feature') if result is not None else None

    def all(self, sort = "name", order = "DESC", skip = 0, limit = 25):
        def get_features(tx: ManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(sort):
                sort = "name"

            result = tx.run(cast(LiteralString, f"""
            MATCH (f:Feature)
            ORDER BY f.{sort} {order}
            RETURN f AS feature
            SKIP $skip LIMIT $limit 
            """), skip=skip, limit=limit, database_=settings.NEO4J_DATABASE)

            return [row.value('feature') for row in result]

        with self.driver.session() as session:
            return session.execute_read(get_features, sort, order, skip, limit)

    def find(self, name: str):
        with self.driver.session() as session:
            result = session.execute_read(self.get_feature, name)
            if result is not None:
                return result
            else:
                raise NotFound(f"Feature with name {name} not found")

    def create(self, name: str):
        def add(tx: ManagedTransaction, name: str):
            result = tx.run("""
                MERGE (f:Feature {name: $name})
                RETURN f AS feature
            """, name=name).single()

            if result is not None:
                return result.get('feature')
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
                MATCH (f:Feature {name: $name})
                DETACH DELETE f
                RETURN f AS feature
            """, name=name).single()
            return result is not None

        with self.driver.session() as session:
            return session.execute_write(remove, name=name)