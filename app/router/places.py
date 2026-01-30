from fastapi import APIRouter, Depends

from app.config.dependencies import get_place_dao
from app.dao.place import PlaceDAO
from app.dto.place import SinglePlace, SinglePlaceExtended, SinglePlaceRecommended

router = APIRouter(prefix="/places", tags=["places"])


@router.get("", description="Get all places", response_model=list[SinglePlace])
async def get_all_places(
    dao: PlaceDAO = Depends(get_place_dao), skip: int = 0, limit: int = 25
) -> list[SinglePlace]:
    return await dao.all(skip=skip, limit=limit, order="ASC")


@router.get("/{placeId}", description="Get a single place", response_model=SinglePlace)
async def find_place_by_place_id(
    placeId: str, dao: PlaceDAO = Depends(get_place_dao)
) -> SinglePlace:
    return await dao.find(placeId=placeId)


@router.post(
    "", description="Create a new place", response_model=SinglePlace, status_code=201
)
async def create_place(
    data: SinglePlace, dao: PlaceDAO = Depends(get_place_dao)
) -> SinglePlace:
    return await dao.create(placeId=data.placeId, data=data.model_dump())


@router.put(
    "/{placeId}",
    description="Update a place",
    response_model=SinglePlace,
    status_code=200,
)
async def update_place(
    placeId: str, data: SinglePlace, dao: PlaceDAO = Depends(get_place_dao)
) -> SinglePlace:
    return await dao.update(placeId=data.placeId, data=data.model_dump())


@router.post(
    "/{placeId}/has/{feature}",
    description="Attach a feature to place",
    status_code=201,
    response_model=SinglePlaceExtended,
)
async def create_place_feature(
    placeId: str, feature: str, dao: PlaceDAO = Depends(get_place_dao)
) -> SinglePlaceExtended:
    return await dao.add_feature(placeId=placeId, feature=feature)


@router.post(
    "/{placeId}/is-in/{category}",
    description="Attach a category to place",
    status_code=201,
    response_model=SinglePlaceExtended,
)
async def create_place_category(
    placeId: str, category: str, dao: PlaceDAO = Depends(get_place_dao)
) -> SinglePlaceExtended:
    return await dao.add_category(placeId=placeId, category=category)


@router.delete("/{placeId}", description="Delete a place", response_model=bool)
async def delete_place(placeId: str, dao: PlaceDAO = Depends(get_place_dao)) -> bool:
    return await dao.delete(placeId=placeId)


@router.delete(
    "/{placeId}/has-not/{feature}",
    description="Detach a feature from place",
    response_model=SinglePlaceExtended,
)
async def delete_place_feature(
    placeId: str, feature: str, dao: PlaceDAO = Depends(get_place_dao)
) -> SinglePlaceExtended:
    return await dao.remove_feature(placeId=placeId, feature=feature)


@router.delete(
    "/{placeId}/is-not-in/{category}",
    description="Detach a category from place",
    response_model=SinglePlaceExtended,
)
async def delete_place_category(
    placeId: str, category: str, dao: PlaceDAO = Depends(get_place_dao)
) -> SinglePlaceExtended:
    return await dao.remove_category(placeId=placeId, category=category)


@router.get(
    "/recommend/{base_category}/for/{user_id}/near/{latitude}/{longitude}/with-max-distance/{max_distance_meters}",
    description="Recommend places belonged to base category, based on user affinity, position and max distance",
    response_model=list[SinglePlaceRecommended],
)
async def find_place_by_place_id(
    user_id: str,
    base_category: str,
    latitude: float,
    longitude: float,
    max_distance_meters: int,
    skip: int = 0,
    limit: int = 10,
    dao: PlaceDAO = Depends(get_place_dao),
) -> list[SinglePlaceRecommended]:
    return await dao.recommend_places_near_by_affinity(
        user_id=user_id,
        base_category=base_category,
        latitude=latitude,
        longitude=longitude,
        max_distance_meters=max_distance_meters,
        skip=skip,
        limit=limit,
    )
