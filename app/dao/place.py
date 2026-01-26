from typing import cast, LiteralString, Any

from neo4j import ManagedTransaction, Driver
from neo4j.exceptions import ConstraintError

from app.config.neo4j import validate_order, validate_field
from app.config.settings import settings
from app.dto.place import SinglePlace
from app.config.exceptions import NotFound, AlreadyExists

class PlaceDAO(object):
    def __init__(self, driver: Driver):
        self.driver = driver

    @staticmethod
    def get_place(tx: ManagedTransaction, placeId: str):
        result = tx.run(cast(LiteralString, """
        MATCH (p:Place {placeId: $placeId})
        RETURN p AS place
        """), placeId=placeId).single()

        if result and result.get('place'):
            return result.get('place')
        else:
            raise NotFound(f"Place with placeId {placeId} not found")

    @staticmethod
    def get_place_extended(tx: ManagedTransaction, placeId: str):
        result = tx.run("""
            MATCH (p:Place {placeId: $placeId})
            OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f:Feature)
            OPTIONAL MATCH (p)-[:IN_CATEGORY]->(c:Category)
            WITH p, collect(c) AS Cats, collect(f) AS Feats
            RETURN p { .*, features: Feats, categories: Cats } AS place
        """, placeId=placeId).single()
        if result and result.get('place'):
            return result.get('place')
        else:
            raise NotFound(f"[EXT] Place with placeId {placeId} not found")

    def all(self, sort = "placeId", order = "DESC", skip = 0, limit = 25):
        def get_places(tx: ManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(SinglePlace, sort):
                sort = "placeId"

            result = tx.run(cast(LiteralString, f"""
            MATCH (p:Place)
            ORDER BY p.{sort} {order}
            RETURN p AS place
            SKIP $skip LIMIT $limit 
            """), skip=skip, limit=limit)

            return [row.value('place') for row in result]

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(get_places, sort, order, skip, limit)

    def find(self, placeId: str):
        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(self.get_place, placeId)

    def create(self, placeId: str, data: dict[str, Any]):
        def add(tx: ManagedTransaction, placeId: str, data: dict[str, Any]):
            result = tx.run("""
                CREATE (p:Place {placeId: $placeId})
                FOREACH (k IN keys($data) | SET p[k]=$data[k])
                RETURN p AS place
            """, placeId=placeId, data=data).single()

            if result is not None:
                return result.get('place')
            return None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            try:
                return session.execute_write(add, placeId=placeId, data=data)
            except ConstraintError:
                raise AlreadyExists(f"Place with id {placeId} already exists")

    def update(self, placeId: str, data: dict[str, Any]):
        def modify(tx: ManagedTransaction, placeId: str, data: dict[str, Any]):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})
                FOREACH (k IN keys($data) | SET p[k]=$data[k])
                RETURN p AS place
            """, placeId=placeId, data=data).single()

            if result is not None:
                return result.get('place')
            return None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, placeId=placeId)
            return session.execute_write(modify, placeId=placeId, data=data)

    def delete(self, placeId: str):
        def remove(tx: ManagedTransaction, placeId: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})
                DETACH DELETE p
                RETURN p AS place
            """, placeId=placeId).single()
            return result is not None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, placeId=placeId)
            return session.execute_write(remove, placeId=placeId)

    def add_feature(self, placeId: str, feature: str):
        def add_place_feature(tx: ManagedTransaction, placeId: str, feature: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})
                MATCH (f:Feature {name: $feature})
                MERGE (p)-[:HAS_FEATURE]->(f)
                RETURN p AS place
            """, placeId=placeId, feature=feature).single()
            return result.get('place')

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, placeId=placeId)
            session.execute_write(add_place_feature, placeId=placeId, feature=feature)
            return session.execute_read(self.get_place_extended, placeId=placeId)

    def remove_feature(self, placeId: str, feature: str):
        def remove_place_feature(tx: ManagedTransaction, placeId: str, feature: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})-[r:HAS_FEATURE]->(f:Feature {name: $feature})
                DELETE r
                RETURN r AS relationship
            """, placeId=placeId, feature=feature).single()
            return result is None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, placeId=placeId)
            session.execute_write(remove_place_feature, placeId=placeId, feature=feature)
            return session.execute_read(self.get_place_extended, placeId=placeId)

    def add_category(self, placeId: str, category: str):
        def add_place_category(tx: ManagedTransaction, placeId: str, category: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})
                MATCH (c:Category {name: $category})
                MERGE (p)-[:IN_CATEGORY]->(c)
                RETURN p AS place
            """, placeId=placeId, category=category).single()
            return result.get('place')

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, placeId=placeId)
            session.execute_write(add_place_category, placeId=placeId, category=category)
            return session.execute_read(self.get_place_extended, placeId=placeId)

    def remove_category(self, placeId: str, category: str):
        def remove_place_category(tx: ManagedTransaction, placeId: str, category: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})-[r:IN_CATEGORY]->(c:Category {name: $category})
                DELETE r
                RETURN r AS relationship
            """, placeId=placeId, category=category).single()
            return result is None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, placeId=placeId)
            session.execute_write(remove_place_category, placeId=placeId, category=category)
            return session.execute_read(self.get_place_extended, placeId=placeId)

