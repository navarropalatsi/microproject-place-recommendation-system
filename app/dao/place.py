from typing import cast, LiteralString

from neo4j import ManagedTransaction, Driver
from neo4j.exceptions import ConstraintError

from app.config.neo4j import validate_order, validate_field, validate_gender
from app.config.settings import settings
from app.dto.place import SinglePlace
from app.config.exceptions import NotFound, AlreadyExists

class PlaceDAO(object):
    def __init__(self, driver: Driver):
        self.driver = driver

    @staticmethod
    def get_place(tx: ManagedTransaction, place_id: str):
        result = tx.run(cast(LiteralString, """
        MATCH (p:Place {placeId: $place_id})
        RETURN p AS place
        """), place_id=place_id).single()

        if result and result.get('place'):
            return result.get('place')
        else:
            raise NotFound(f"Place with placeId {place_id} not found")

    @staticmethod
    def get_place_extended(tx: ManagedTransaction, place_id: str):
        result = tx.run("""
            MATCH (p:Place {placeId: $placeId})
            OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f:Feature)
            OPTIONAL MATCH (p)-[:IN_CATEGORY]->(c:Category)
            WITH p, collect(c) AS Cats, collect(f) AS Feats
            RETURN p { .*, features: Feats, categories: Cats } AS place
        """, placeId=place_id).single()
        if result and result.get('place'):
            return result.get('place')
        else:
            raise NotFound(f"[EXT] Place with placeId {place_id} not found")

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

    def find(self, place_id: str):
        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(self.get_place, place_id)

    def create_or_update(self, place_id: str, name: str, full_address: str, create=True):
        def add(tx: ManagedTransaction, place_id: str, name: str, full_address: str):
            result = tx.run("""
                MERGE (p:Place {placeId: $place_id})
                SET p.name = $name
                SET p.fullAddress = $full_address
                RETURN p AS place
            """, place_id=place_id, name=name, full_address=full_address).single()

            if result is not None:
                return result.get('place')
            return None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            if create:
                try:
                    session.execute_read(self.get_place, place_id)
                    raise AlreadyExists(f"Place with id {place_id} already exists")
                except NotFound:
                    return session.execute_write(add, place_id=place_id, name=name, full_address=full_address)
            else:
                session.execute_read(self.get_place, place_id)
                return session.execute_write(add, place_id=place_id, name=name, full_address=full_address)

    def delete(self, place_id: str):
        def remove(tx: ManagedTransaction, place_id: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $place_id})
                DETACH DELETE p
                RETURN p AS place
            """, place_id=place_id).single()
            return result is not None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, place_id=place_id)
            return session.execute_write(remove, place_id=place_id)

    def add_feature(self, place_id: str, feature: str):
        def add_place_feature(tx: ManagedTransaction, place_id: str, feature: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})
                MATCH (f:Feature {name: $feature})
                MERGE (p)-[:HAS_FEATURE]->(f)
                RETURN p AS place
            """, placeId=place_id, feature=feature).single()
            return result.get('place')

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, place_id=place_id)
            session.execute_write(add_place_feature, place_id=place_id, feature=feature)
            return session.execute_read(self.get_place_extended, place_id=place_id)

    def remove_feature(self, place_id: str, feature: str):
        def remove_place_feature(tx: ManagedTransaction, place_id: str, feature: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})-[r:HAS_FEATURE]->(f:Feature {name: $feature})
                DELETE r
                RETURN r AS relationship
            """, placeId=place_id, feature=feature).single()
            return result is None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, place_id=place_id)
            session.execute_write(remove_place_feature, place_id=place_id, feature=feature)
            return session.execute_read(self.get_place_extended, place_id=place_id)

    def add_category(self, place_id: str, category: str):
        def add_place_category(tx: ManagedTransaction, place_id: str, category: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})
                MATCH (c:Category {name: $category})
                MERGE (p)-[:IN_CATEGORY]->(c)
                RETURN p AS place
            """, placeId=place_id, category=category).single()
            return result.get('place')

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, place_id=place_id)
            session.execute_write(add_place_category, place_id=place_id, category=category)
            return session.execute_read(self.get_place_extended, place_id=place_id)

    def remove_category(self, place_id: str, category: str):
        def remove_place_category(tx: ManagedTransaction, place_id: str, category: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $placeId})-[r:IN_CATEGORY]->(c:Category {name: $category})
                DELETE r
                RETURN r AS relationship
            """, placeId=place_id, category=category).single()
            return result is None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_place, place_id=place_id)
            session.execute_write(remove_place_category, place_id=place_id, category=category)
            return session.execute_read(self.get_place_extended, place_id=place_id)

