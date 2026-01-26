import datetime
from typing import cast, LiteralString
import ijson
import os
import sys

from app.config.neo4j import setup_db
from app.dto.category import SingleCategory

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.dto.place import SinglePlace

BULK_IMPORT_QUERY = """
UNWIND $batch AS row
MERGE (p:Place {placeId: row[0].placeId})
SET p += row[0]
FOREACH (cat IN row[1] |
    MERGE (c:Category {name: cat.name})
    MERGE (p)-[:IN_CATEGORY]->(c)
)
"""

def import_data():
    driver = setup_db()
    file_path = "spain_portugal.geojson"

    i = 0
    limit = 10000
    buffer = list()

    for item in ijson.items(open(file_path, "r"), 'features.item'):
        place = SinglePlace(
            placeId = item['properties']['id'],
            name = str(item['properties']['names']['primary']) if item['properties']['names']['primary'] else None,
            freeform = str(item['properties']['addresses'][0]['freeform']) if item['properties']['addresses'][0]['freeform'] else None,
            locality = str(item['properties']['addresses'][0]['locality']).upper() if item['properties']['addresses'][0]['locality'] else None,
            country = str(item['properties']['addresses'][0]['country']).upper() if item['properties']['addresses'][0]['country'] else None,
            postcode = str(item['properties']['addresses'][0]['postcode']) if item['properties']['addresses'][0]['postcode'] else None,
            region = str(item['properties']['addresses'][0]['region']).upper() if item['properties']['addresses'][0]['region'] else None,
            confidence = float(round(item['properties']['confidence'], 4)),
        ).model_dump()

        categories = list()
        categories.append(SingleCategory(
            name = item['properties']['categories']['primary'],
        ).model_dump())
        if item['properties']['categories']['alternate']:
            for cat in item['properties']['categories']['alternate']:
                categories.append(SingleCategory(
                    name = cat,
                ).model_dump())

        buffer.append([place, categories])

        i = i + 1
        if len(buffer) == limit:
            with driver.session() as session:
                now = datetime.datetime.now()
                print(f"Executing import query at {i} place...")
                session.run(cast(LiteralString, BULK_IMPORT_QUERY), batch=buffer)
                buffer = list()
                diff = datetime.datetime.now() - now
                print(f"Last batch has taken {diff.total_seconds()} seconds")

    if len(buffer) > 0:
        with driver.session() as session:
            print(f"Executing import query at {i} place...")
            session.run(cast(LiteralString, BULK_IMPORT_QUERY), batch=buffer)

    print(f"Places seen: {i}")

if __name__ == '__main__':
    import_data()