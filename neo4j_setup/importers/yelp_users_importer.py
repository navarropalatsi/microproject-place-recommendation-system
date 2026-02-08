import asyncio
import json
import os
import sys
from typing import cast, LiteralString
from neo4j import AsyncDriver

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.neo4j import setup_db
from app.config.settings import settings

BULK_IMPORT_QUERY = """
UNWIND $batch AS row
MERGE (u:User {userId: row.userId})
RETURN u AS user
"""


async def import_users(file_path: str) -> None:
    driver: AsyncDriver = await setup_db()
    i = 0
    limit = 10000
    buffer = list()
    try:
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    if "user_id" not in data:
                        print(f"Invalid user in {data}")
                        continue

                    user = {"userId": "yelp-" + data["user_id"]}
                    buffer.append(user)

                    if len(buffer) > limit:
                        await session.run(
                            cast(LiteralString, BULK_IMPORT_QUERY), batch=buffer
                        )
                        print(f"Imported {len(buffer)} users")
                        i = i + len(buffer)
                        buffer = list()

            if len(buffer) > 0:
                await session.run(cast(LiteralString, BULK_IMPORT_QUERY), batch=buffer)
                i = i + len(buffer)

            print(f"Imported {i} users")
    except Exception as e:
        print(f"EXCEPTION ---> {e}")
    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(import_users(sys.argv[1]))
