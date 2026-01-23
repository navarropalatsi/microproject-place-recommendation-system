import os
from neo4j import GraphDatabase, Driver
from app.config.settings import settings


def setup_db() -> Driver:
    driver = GraphDatabase.driver(
        settings.NEO4J_HOSTNAME,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    )
    driver.verify_connectivity()
    return driver

def validate_field(obj: object, field: str):
    return obj is not None and field is not None and hasattr(obj, field)

def validate_order(order: str):
    return  order is not None and order.upper() in {"ASC", "DESC"}

def validate_gender(gender: str):
    return  gender is not None and gender.upper() in {"M", "F"}