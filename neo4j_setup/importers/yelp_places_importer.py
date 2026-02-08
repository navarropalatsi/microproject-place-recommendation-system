import asyncio
import json
import os
import sys
from typing import cast, LiteralString
from neo4j import AsyncDriver
from neo4j.exceptions import ConstraintError

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.neo4j import setup_db
from app.services.place_service import PlaceService
from app.config.dependencies import get_place_service
from app.dto.place import SinglePlace


async def import_places(file_path: str) -> None:
    print(f"Importing places from {file_path}")
    driver: AsyncDriver = await setup_db()
    place_service: PlaceService = await get_place_service(driver=driver)
    i = 0

    found = 0
    notfound = 0

    limit = 10000

    try:
        f = open(file=file_path, mode="r", encoding="utf-8")
    except OSError:
        print(f"Could not open/read file: {file_path}")
        sys.exit()

    with f:
        for line in f:
            data = json.loads(line)
            if "business_id" not in data:
                print(f"Invalid place in {data}")
                continue

            # Try to find the Overturemaps Place based on name and position similarity (with an error margin of distance)
            candidate: SinglePlace | None = (
                await place_service.get_place_by_name_and_position(
                    data["name"],
                    float(data["latitude"]),
                    float(data["longitude"]),
                    max_distance_meters=300,
                )
            )
            if not candidate:
                notfound = notfound + 1
                # print(f"!!!! Candidate not found with {data['name']} near (lt:{data['latitude']}, lg:{data['longitude']})!!!!")
                if found + notfound > 0:
                    print(f"Current progress: {round(found/(found+notfound)*100, 2)}")
                continue
            else:
                # print(f"Candidate found with real name: {candidate.name}")
                found = found + 1
                if found + notfound > 0:
                    print(f"Current progress: {round(found/(found+notfound)*100, 2)}")

            try:
                # If we found the candidate and it has not the yelpId attribute yet
                if not candidate.yelpId:
                    # Set the yelpId attribute
                    candidate.yelpId = data["business_id"]
                    # Update the place with the new attribute
                    candidate_updated = await place_service.update_place(
                        candidate.placeId,
                        candidate.model_dump(include={"placeId", "yelpId"}),
                    )

                    # Check if the update has been successful
                    if candidate_updated.yelpId == candidate.yelpId:
                        i = i + 1
                    else:
                        print(
                            f"Update has not worked with {data['name']} vs {candidate.name}"
                        )

                    # Every $limit updates, print a message with the current updated places count
                    if i % limit == 0:
                        print(f"Updated {i} places")
            except ConstraintError as ce:
                print(ce)
                print(
                    f"Candidate found in DB: {candidate.placeId} ### {candidate.name} ### {candidate.yelpId}"
                )
                yelp_candidate: SinglePlace | None = (
                    await place_service.get_place_by_yelp_id(data["business_id"])
                )
                if yelp_candidate:
                    print(
                        f"Already existing YELP: {yelp_candidate.placeId} ### {yelp_candidate.name} ### {yelp_candidate.yelpId}"
                    )
                print("-----------------------")

    print(f"Updated {i} places")


if __name__ == "__main__":
    asyncio.run(import_places(sys.argv[1]))
