import datetime
from typing import cast, LiteralString
import ijson
import os
import sys
import asyncio

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import settings
from app.config.neo4j import setup_db

BULK_IMPORT_QUERY = """
UNWIND $batch AS row
CALL (row) {
    WITH row, point({latitude: row.latitude, longitude: row.longitude}) AS refPoint
    MATCH (p:Place) 
    WHERE point.distance(refPoint, p.coordinates) < 10000
    WITH row, p, apoc.text.sorensenDiceSimilarity(toUpper(p.name), toUpper(row.name)) AS score
    ORDER BY score DESC
    RETURN p
    LIMIT 1
}
MATCH (u:User {userId: row.userId})
MERGE (u)-[r:RATED]->(p)
SET r.rating = row.rating
RETURN p AS place
"""

USER_ID = "0"


def get_country(location):
    if "country_code" in location:
        return location["country_code"]
    else:
        if "España" in location["address"]:
            return "ES"
        if "Italia" in location["address"]:
            return "IT"
        if "Francia" in location["address"]:
            return "FR"
        if "Alemania" in location["address"]:
            return "DE"
        else:
            return ""


async def import_data(file_path: str) -> None:
    driver = await setup_db()

    i = 0
    created = 0
    limit = 10000
    buffer = list()

    for item in ijson.items(open(file_path, "r", encoding="utf-8"), "features.item"):
        if not "properties" in item or not "location" in item["properties"]:
            # print('INVALID ITEM')
            # print(item)
            continue

        review = {
            "userId": USER_ID,
            "name": str(item["properties"]["location"]["name"]).replace("/", ""),
            "country": get_country(item["properties"]["location"]),
            "rating": item["properties"]["five_star_rating_published"],
            "latitude": float(item["geometry"]["coordinates"][1]),
            "longitude": float(item["geometry"]["coordinates"][0]),
        }

        print("")
        print(review)
        buffer.append(review)

        i = i + 1
        if i >= limit:
            async with driver.session(database=settings.NEO4J_DATABASE) as session:
                now = datetime.datetime.now()
                print(f"Executing import query at {i} review...")

                result = await session.run(
                    cast(LiteralString, BULK_IMPORT_QUERY), batch=buffer
                )
                result = await result.single()
                if result and result.get("place"):
                    created = created + 1

                buffer = list()
                diff = datetime.datetime.now() - now
                print(f"Last batch has taken {diff.total_seconds()} seconds")

    if len(buffer) > 0:
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            print(f"Executing import query at {i} review...")
            result = await session.run(
                cast(LiteralString, BULK_IMPORT_QUERY), batch=buffer
            )
            result = await result.single()
            if result and result.get("place"):
                created = created + 1

    print(f"Reviews seen: {i}. {created} reviews created")


if __name__ == "__main__":
    loop = asyncio.run(import_data(sys.argv[1]))
