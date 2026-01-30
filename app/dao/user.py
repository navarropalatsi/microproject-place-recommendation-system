from typing import cast, LiteralString

from neo4j import ManagedTransaction, Driver
from neo4j.exceptions import ConstraintError

from app.config.exceptions import AlreadyExists, NotFound, InvalidValue
from app.config.neo4j import validate_order, validate_field, validate_gender
from app.config.settings import settings
from app.dto.user import SingleUser


class UserDAO(object):
    def __init__(self, driver: Driver):
        self.driver = driver

    RATED = "RATED"
    NEEDS_FEATURE = "NEEDS_FEATURE"

    @staticmethod
    def get_user(tx: ManagedTransaction, user_id: str):
        result = tx.run(cast(LiteralString, """
        MATCH (u:User {userId: $user_id})
        RETURN u AS user
        """), user_id=user_id).single()

        if result and result.get('user', False):
            return result.get('user')
        else:
            raise NotFound(f"User with userId {user_id} not found")

    @staticmethod
    def get_user_extended(tx: ManagedTransaction, user_id: str):
        result = tx.run(cast(LiteralString, f"""
        MATCH (u:User {{userId: $user_id}})
        OPTIONAL MATCH (u)-[:{UserDAO.NEEDS_FEATURE}]->(f:Feature)
        WITH u, collect(f) AS Feats
        RETURN u {{ .*, features: Feats }} AS user
        """), user_id=user_id).single()

        if result and result.get('user', False):
            return result.get('user')
        else:
            raise NotFound(f"User with userId {user_id} not found")

    def all(self, sort = "userId", order = "DESC", skip = 0, limit = 25):
        def get_users(tx: ManagedTransaction, sort, order, skip, limit):
            if not validate_order(order):
                order = "DESC"
            if not validate_field(SingleUser, sort):
                sort = "userId"

            result = tx.run(cast(LiteralString, f"""
            MATCH (u:User)
            ORDER BY u.{sort} {order}
            RETURN u AS user
            SKIP $skip LIMIT $limit 
            """), skip=skip, limit=limit)

            return [row.value('user') for row in result]

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(get_users, sort, order, skip, limit)

    def find(self, user_id: str):
        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(self.get_user, user_id)

    def create(self, user_id: str, born: str, gender: str):
        def add(tx: ManagedTransaction, user_id: str, born: str, gender: str):
            if not validate_gender(gender):
                raise InvalidValue(f"Invalid gender {gender}. Gender must be 'm' or 'f'")

            result = tx.run("""
                CREATE (u:User {userId: $user_id})
                SET u.born = date($born)
                SET u.gender = $gender
                RETURN u AS user
            """, user_id=user_id, born=born, gender=gender).single()

            if result is not None:
                return result.get('user')
            return None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            try:
                return session.execute_write(add, user_id=user_id, born=born, gender=gender)
            except ConstraintError:
                raise AlreadyExists(f"User with userId {user_id} already exists")

    def update(self, user_id: str, born: str, gender: str):
        def modify(tx: ManagedTransaction, user_id: str, born: str, gender: str):
            if not validate_gender(gender):
                raise InvalidValue(f"Invalid gender {gender}. Gender must be 'm' or 'f'")

            result = tx.run("""
                MATCH (u:User {userId: $user_id})
                SET u.born = date($born)
                SET u.gender = $gender
                RETURN u AS user
            """, user_id=user_id, born=born, gender=gender).single()

            if result is not None:
                return result.get('user')
            return None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_user, user_id=user_id)
            return session.execute_write(modify, user_id=user_id, born=born, gender=gender)

    def delete(self, user_id: str):
        def remove(tx: ManagedTransaction, user_id: str):
            result = tx.run("""
                MATCH (u:User {userId: $user_id})
                DETACH DELETE u
                RETURN u AS user
            """, user_id=user_id).single()
            return result is not None

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_read(self.get_user, user_id=user_id)
            return session.execute_write(remove, user_id=user_id)

    def add_feature(self, user_id: str, feature: str):
        def add_needs(tx: ManagedTransaction, user_id: str, feature: str):
            result = tx.run(cast(LiteralString, f"""
                MATCH (u:User {{userId: $user_id}})
                MATCH (f:Feature {{name: $feature}})
                MERGE (u)-[:{UserDAO.NEEDS_FEATURE}]->(f)
                RETURN u AS user
            """), user_id=user_id, feature=feature).single()
            return result.get('user')

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            if session.execute_write(add_needs, user_id=user_id, feature=feature) is None:
                raise NotFound(f"User with userId {user_id} or feature '{feature}' does not exist")
            return session.execute_read(self.get_user_extended, user_id=user_id)

    def remove_feature(self, user_id: str, feature: str):
        def remove_need(tx: ManagedTransaction, user_id: str, feature: str):
            result = tx.run(cast(LiteralString, f"""
                MATCH (u:User {{userId: $user_id}})-[r:{UserDAO.NEEDS_FEATURE}]->(f:Feature {{name: $feature}})
                DELETE r
                WITH (u IS NOT NULL AND f IS NOT NULL) AS relationship
                RETURN relationship
            """), user_id=user_id, feature=feature).single()
            return result.get('relationship')

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            if session.execute_write(remove_need, user_id=user_id, feature=feature) is False:
                raise NotFound(f"User with userId {user_id} or feature '{feature}' does not exist")
            return session.execute_read(self.get_user_extended, user_id=user_id)

    def user_has_rated_place(self, user_id: str, place_id: str) -> bool:
        def find_rating(tx: ManagedTransaction, user_id: str, place_id: str):
            result = tx.run(cast(LiteralString, f"""
            MATCH (u:User {{userId: $user_id}})-[r:{UserDAO.RATED}]->(p:Place {{placeId: $place_id}})
            WITH (r IS NOT NULL) AS rating_exists
            RETURN rating_exists
            """), user_id=user_id, place_id=place_id).single()
            return result and result.get('rating_exists')

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_read(find_rating, user_id=user_id, place_id=place_id)

    def rate_place(self, user_id: str, place_id: str, rating: float) -> bool:
        def add_rating(tx: ManagedTransaction, user_id: str, place_id: str, rating: float):
            result = tx.run(cast(LiteralString,f"""
            MATCH (u:User {{userId: $user_id}})
            MATCH (p:Place {{placeId: $place_id}})
            MERGE (u)-[r:{UserDAO.RATED}]->(p)
            SET r.rating = $rating
            RETURN (r IS NOT NULL) AS rating_exists
            """), user_id=user_id, place_id=place_id, rating=rating).single()
            return result and result.get('rating_exists')

        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            session.execute_write(add_rating, user_id=user_id, place_id=place_id, rating=rating)
            return True


