from fastapi import APIRouter, Depends

from app.config.dependencies import get_place_service, get_recommendation_service
from app.dto.place import SinglePlace, SinglePlaceExtended, SinglePlaceRecommended
from app.services.place_service import PlaceService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/places", tags=["places"])


@router.get("", description="Get all places", response_model=list[SinglePlace])
async def get_all_places(
    service: PlaceService = Depends(get_place_service), skip: int = 0, limit: int = 25
) -> list[SinglePlace]:
    return await service.get_all_places(skip=skip, limit=limit, order="ASC")


@router.get("/{placeId}", description="Get a single place", response_model=SinglePlace)
async def find_place_by_place_id(
    placeId: str, service: PlaceService = Depends(get_place_service)
) -> SinglePlace:
    return await service.get_place(placeId=placeId)


@router.get(
    "/find/{name}/near/{latitude}/{longitude}",
    description="Find place by name and position similarity",
    response_model=SinglePlaceRecommended,
)
async def find_place_by_name_and_position(
    name: str,
    latitude: float,
    longitude: float,
    service: PlaceService = Depends(get_place_service),
) -> SinglePlaceRecommended | None:
    return await service.get_place_by_name_and_position(
        name=name, latitude=latitude, longitude=longitude
    )


@router.post(
    "", description="Create a new place", response_model=SinglePlace, status_code=201
)
async def create_place(
    data: SinglePlace, service: PlaceService = Depends(get_place_service)
) -> SinglePlace:
    return await service.create_place(placeId=data.placeId, data=data.model_dump())


@router.put(
    "/{placeId}",
    description="Update a place",
    response_model=SinglePlace,
    status_code=200,
)
async def update_place(
    placeId: str, data: SinglePlace, service: PlaceService = Depends(get_place_service)
) -> SinglePlace:
    return await service.update_place(placeId=placeId, data=data.model_dump())


@router.post(
    "/{placeId}/has/{feature}",
    description="Attach a feature to place",
    status_code=201,
    response_model=SinglePlaceExtended,
)
async def create_place_feature(
    placeId: str, feature: str, service: PlaceService = Depends(get_place_service)
) -> SinglePlaceExtended:
    await service.attach_feature_to_place(placeId=placeId, feature=feature)
    return await service.get_place(placeId=placeId)


@router.post(
    "/{placeId}/is-in/{category}",
    description="Attach a category to place",
    status_code=201,
    response_model=SinglePlaceExtended,
)
async def create_place_category(
    placeId: str, category: str, service: PlaceService = Depends(get_place_service)
) -> SinglePlaceExtended:
    await service.attach_category_to_place(placeId=placeId, category=category)
    return await service.get_place(placeId=placeId)


@router.delete("/{placeId}", description="Delete a place", response_model=bool)
async def delete_place(
    placeId: str, service: PlaceService = Depends(get_place_service)
) -> bool:
    return await service.delete_place(placeId=placeId)


@router.delete(
    "/{placeId}/has-not/{feature}",
    description="Detach a feature from place",
    response_model=SinglePlaceExtended,
)
async def delete_place_feature(
    placeId: str, feature: str, service: PlaceService = Depends(get_place_service)
) -> SinglePlaceExtended:
    await service.detach_feature_from_place(placeId=placeId, feature=feature)
    return await service.get_place(placeId=placeId)


@router.delete(
    "/{placeId}/is-not-in/{category}",
    description="Detach a category from place",
    response_model=SinglePlaceExtended,
)
async def delete_place_category(
    placeId: str, category: str, service: PlaceService = Depends(get_place_service)
) -> SinglePlaceExtended:
    await service.detach_category_from_place(placeId=placeId, category=category)
    return await service.get_place(placeId=placeId)


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
    service: RecommendationService = Depends(get_recommendation_service),
) -> list[SinglePlaceRecommended]:
    return await service.recommend_places_near_by_affinity(
        user_id=user_id,
        base_category=base_category,
        latitude=latitude,
        longitude=longitude,
        max_distance_meters=max_distance_meters,
        skip=skip,
        limit=limit,
    )
