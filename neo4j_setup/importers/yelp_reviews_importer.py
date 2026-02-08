import asyncio
import json
import os
import sys
from neo4j import AsyncDriver

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.neo4j import setup_db
from app.services.user_service import UserService
from app.services.place_service import PlaceService
from app.config.dependencies import get_user_service, get_place_service
from app.dto.place import SinglePlace
from app.config.exceptions import NotFound


async def import_places(file_path: str) -> None:
    print(f"Importing reviews from {file_path}")
    driver: AsyncDriver = await setup_db()
    place_service: PlaceService = await get_place_service(driver=driver)
    user_service: UserService = await get_user_service(
        driver=driver, place_service=place_service
    )
    i = 0
    limit = 10000

    try:
        f = open(file=file_path, mode="r", encoding="utf-8")
    except OSError:
        print(f"Could not open/read file: {file_path}")
        sys.exit()

    with f:
        for line in f:
            data = json.loads(line)

            # Try to find the place
            place: SinglePlace | None = await place_service.get_place_by_yelp_id(
                data["business_id"]
            )
            if not place:
                print(f"No place with id {data['business_id']}")
                continue

            # Rate the place
            try:
                success: bool = await user_service.rate_place(
                    user_id="yelp-" + data["user_id"],
                    place_id=place.placeId,
                    rating=float(data["stars"]),
                )
                if success:
                    i = i + 1
                # Every $limit updates, print a message with the current updated places count
                if i % limit == 0:
                    print(f"Updated {i} places")
            except NotFound as nf:
                print(nf)

    print(f"Updated {i} reviews")


if __name__ == "__main__":
    asyncio.run(import_places(sys.argv[1]))
