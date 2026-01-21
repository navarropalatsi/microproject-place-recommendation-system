from typing import cast, LiteralString

from neo4j import ManagedTransaction, Driver
from neo4j.exceptions import ConstraintError
from pyexpat import features
from werkzeug.exceptions import NotFound

from app.config.exceptions import AlreadyExists
from app.config.neo4j import validate_order, validate_field, validate_gender
from app.config.settings import settings

class UserDAO(object):
    def __init__(self, driver: Driver):
        self.driver = driver

    @staticmethod
    def get_user(tx: ManagedTransaction, user_id: str):
        result = tx.run(cast(LiteralString, """
        MATCH (u:User {userId: $user_id})
        RETURN u AS user
        """), userId=user_id, database_=settings.NEO4J_DATABASE).single()

        return result.get('user') if result is not None else None

    def all(self, sort = "userId", order = "DESC", skip = 0, limit = 25):
        def get_users(tx: ManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(sort):
                sort = "userId"

            result = tx.run(cast(LiteralString, f"""
            MATCH (u:User)
            ORDER BY u.{sort} {order}
            RETURN u AS user
            SKIP $skip LIMIT $limit 
            """), skip=skip, limit=limit, database_=settings.NEO4J_DATABASE)

            return [row.value('user') for row in result]

        with self.driver.session() as session:
            return session.execute_read(get_users, sort, order, skip, limit)

    def find(self, user_id: str):
        with self.driver.session() as session:
            result = session.execute_read(self.get_user, user_id)
            if result is not None:
                return result
            else:
                raise NotFound(f"User with userId {user_id} not found")

    def create_or_update(self, user_id: str, born: str, gender: str):
        def add_or_update(tx: ManagedTransaction, user_id: str, born: str, gender: str):
            if not validate_gender(gender):
                gender = "m"

            result = tx.run("""
                MERGE (u:User, {userId: $user_id})
                SET u.born = date($born)
                SET u.gender = $gender
                RETURN u AS user
            """, userId=user_id, born=born, gender=gender).single()

            if result is not None:
                return result.get('user')
            return None

        try:
            with self.driver.session() as session:
                user = session.execute_read(self.get_user, user_id)
                if user is not None:
                    raise AlreadyExists(f"User with userId {user_id} already exists")
                return session.execute_write(add_or_update, user_id=user_id, born=born, gender=gender)
        except ConstraintError as e:
            print("ConstraintError detected: " + e.title)
            return None

    def delete(self, user_id: str):
        def remove(tx: ManagedTransaction, user_id: str):
            result = tx.run("""
                MATCH (u:User, {userId: $user_id})
                DELETE u
                RETURN u AS user
            """, userId=user_id).single()
            return result is not None

        with self.driver.session() as session:
            return session.execute_write(remove, user_id=user_id)

    def add_feature(self, user_id: str, feature: str):
        def add_needs(tx: ManagedTransaction, user_id: str, feature: str):
            result = tx.run("""
                MERGE (u:User {userId: $user_id})
                MERGE (f:Feature {name: $feature})
                MERGE (u)-[:NEEDS_FEATURE]->(f)
                WITH u, collect(f.name) AS FeaturesList
                RETURN u { .*, features: FeaturesList } AS user
            """, userId=user_id, feature=feature).single()
            return result.get('user')

        self.find(user_id)
        with self.driver.session() as session:
            return session.execute_write(add_needs, user_id=user_id, feature=feature)

    def remove_feature(self, user_id: str, feature: str):
        def add_needs(tx: ManagedTransaction, user_id: str, feature: str):
            result = tx.run("""
                MATCH (u:User {userId: $user_id})-[r:NEEDS_FEATURE]->(f:Feature {name: $feature})
                DELETE r
                RETURN r AS relationship
            """, userId=user_id, feature=feature).single()
            return result.get('relationship')

        self.find(user_id)
        with self.driver.session() as session:
            return session.execute_write(add_needs, user_id=user_id, feature=feature) is not None

