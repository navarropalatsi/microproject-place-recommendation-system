from fastapi import APIRouter, Depends

from app.config.dependencies import get_place_dao
from app.dao.place import PlaceDAO
from app.dto.place import SinglePlace, SinglePlaceExtended

router = APIRouter(
    prefix="/places",
    tags=["places"]
)

@router.get("", description="Get all places", response_model=list[SinglePlace])
def get_all_places(dao: PlaceDAO = Depends(get_place_dao), skip: int = 0, limit: int = 25) -> list[SinglePlace]:
    return dao.all(skip=skip, limit=limit, order="ASC")

@router.get("/{place_id}", description="Get a single place", response_model=SinglePlace)
def find_place_by_place_id(place_id: str, dao: PlaceDAO = Depends(get_place_dao)) -> SinglePlace:
    return dao.find(place_id=place_id)

@router.post("", description="Create a new place", response_model=SinglePlace, status_code=201)
def create_place(data: SinglePlace, dao: PlaceDAO = Depends(get_place_dao)) -> SinglePlace:
    return dao.create(place_id=data.placeId, name=data.name, full_address=data.fullAddress)

@router.put("/{place_id}", description="Update a place", response_model=SinglePlace, status_code=200)
def update_place(place_id: str, data: SinglePlace, dao: PlaceDAO = Depends(get_place_dao)) -> SinglePlace:
    return dao.update(place_id=place_id, name=data.name, full_address=data.fullAddress)

@router.post("/{place_id}/has/{feature}", description="Attach a feature to place", status_code=201, response_model=SinglePlaceExtended)
def create_place_feature(place_id: str, feature: str, dao: PlaceDAO = Depends(get_place_dao)) -> SinglePlaceExtended:
    return dao.add_feature(place_id=place_id, feature=feature)

@router.post("/{place_id}/is-in/{category}", description="Attach a category to place", status_code=201, response_model=SinglePlaceExtended)
def create_place_category(place_id: str, category: str, dao: PlaceDAO = Depends(get_place_dao)) -> SinglePlaceExtended:
    return dao.add_category(place_id=place_id, category=category)

@router.delete("/{place_id}", description="Delete a place", response_model=bool)
def delete_place(place_id: str, dao: PlaceDAO = Depends(get_place_dao)) -> bool:
    return dao.delete(place_id=place_id)

@router.delete("/{place_id}/has-not/{feature}", description="Detach a feature from place", response_model=SinglePlaceExtended)
def delete_place_feature(place_id: str, feature: str, dao: PlaceDAO = Depends(get_place_dao)) -> SinglePlaceExtended:
    return dao.remove_feature(place_id=place_id, feature=feature)

@router.delete("/{place_id}/is-not-in/{category}", description="Detach a category from place", response_model=SinglePlaceExtended)
def delete_place_category(place_id: str, category: str, dao: PlaceDAO = Depends(get_place_dao)) -> SinglePlaceExtended:
    return dao.remove_category(place_id=place_id, category=category)