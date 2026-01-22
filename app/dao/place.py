from typing import cast, LiteralString

from neo4j import ManagedTransaction, Driver
from neo4j.exceptions import ConstraintError
from werkzeug.exceptions import NotFound

from app.config.neo4j import validate_order, validate_field, validate_gender
from app.config.settings import settings

class PlaceDAO(object):
    def __init__(self, driver: Driver):
        self.driver = driver

    @staticmethod
    def get_place(tx: ManagedTransaction, place_id: str):
        result = tx.run(cast(LiteralString, """
        MATCH (p:Place {placeId: $place_id})
        RETURN p AS place
        """), place_id=place_id, database_=settings.NEO4J_DATABASE).single()

        return result.get('place') if result is not None else None

    def all(self, sort = "placeId", order = "DESC", skip = 0, limit = 25):
        def get_places(tx: ManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(sort):
                sort = "placeId"

            result = tx.run(cast(LiteralString, f"""
            MATCH (p:Place)
            ORDER BY f.{sort} {order}
            RETURN p AS place
            SKIP $skip LIMIT $limit 
            """), skip=skip, limit=limit, database_=settings.NEO4J_DATABASE)

            return [row.value('place') for row in result]

        with self.driver.session() as session:
            return session.execute_read(get_places, sort, order, skip, limit)

    def find(self, place_id: str):
        with self.driver.session() as session:
            result = session.execute_read(self.get_place, place_id)
            if result is not None:
                return result
            else:
                raise NotFound(f"Place with placeId {place_id} not found")

    def create(self, place_id: str, name: str, full_address: str):
        def add(tx: ManagedTransaction, name: str):
            result = tx.run("""
                MERGE (p:Place {placeId: $placeId})
                SET p.name = $name
                SET p.fullAddress = $full_address
                RETURN p AS place
            """, place_id=place_id, name=name, full_address=full_address).single()

            if result is not None:
                return result.get('place')
            return None

        try:
            with self.driver.session() as session:
                return session.execute_write(add, name=name)
        except ConstraintError as e:
            print("ConstraintError detected: " + e.title)
            return None

    def delete(self, place_id: str):
        def remove(tx: ManagedTransaction, place_id: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $place_id})
                DETACH DELETE p
                RETURN p AS place
            """, place_id=place_id).single()
            return result is not None

        with self.driver.session() as session:
            return session.execute_write(remove, place_id=place_id)

    def add_feature(self, place_id: str, feature: str):
        def add_place_feature(tx: ManagedTransaction, place_id: str, feature: str):
            result = tx.run("""
                MERGE (p:Place {placeId: $placeId})
                MERGE (f:Feature {name: $feature})
                MERGE (p)-[:HAS_FEATURE]->(f)
                WITH p, collect(f.name) AS FeaturesList
                RETURN p { .*, features: FeaturesList } AS place
            """, placeId=place_id, feature=feature).single()
            return result.get('place')

        self.find(place_id)
        with self.driver.session() as session:
            return session.execute_write(add_place_feature, place_id=place_id, feature=feature)

    def remove_feature(self, place_id: str, feature: str):
        def remove_place_feature(tx: ManagedTransaction, place_id: str, feature: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $place_id})-[r:HAS_FEATURE]->(f:Feature {name: $feature})
                DELETE r
                RETURN r AS relationship
            """, placeId=place_id, feature=feature).single()
            return result.get('relationship')

        self.find(place_id)
        with self.driver.session() as session:
            return session.execute_write(remove_place_feature, place_id=place_id, feature=feature) is not None

    def add_category(self, place_id: str, category: str):
        def add_place_category(tx: ManagedTransaction, place_id: str, category: str):
            result = tx.run("""
                MERGE (p:Place {placeId: $placeId})
                MERGE (c:Category {name: $category})
                MERGE (p)-[:IN_CATEGORY]->(c)
                WITH p, collect(c.name) AS CategoriesList
                RETURN p { .*, features: CategoriesList } AS place
            """, placeId=place_id, category=category).single()
            return result.get('place')

        self.find(place_id)
        with self.driver.session() as session:
            return session.execute_write(add_place_category, place_id=place_id, category=category)

    def remove_category(self, place_id: str, category: str):
        def remove_place_category(tx: ManagedTransaction, place_id: str, category: str):
            result = tx.run("""
                MATCH (p:Place {placeId: $place_id})-[r:HAS_FEATURE]->(c:Category {name: $category})
                DELETE r
                RETURN r AS relationship
            """, placeId=place_id, category=category).single()
            return result.get('relationship')

        self.find(place_id)
        with self.driver.session() as session:
            return session.execute_write(remove_place_category, place_id=place_id, category=category) is not None

