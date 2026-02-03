from datetime import datetime

from fastapi import APIRouter, Depends

from app.config.dependencies import get_user_service
from app.dto.user import SingleUser, SingleUserExtended
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", description="Get all users", response_model=list[SingleUser])
async def get_all_users(
    service: UserService = Depends(get_user_service), skip: int = 0, limit: int = 25
) -> list[SingleUser]:
    return await service.get_all_users(skip=skip, limit=limit)


@router.get("/{user_id}", description="Get a single user", response_model=SingleUser)
async def find_user_by_id(
    user_id: str, service: UserService = Depends(get_user_service)
) -> SingleUser:
    return await service.get_user_by_id(user_id=user_id)


@router.post(
    "", description="Create a new user", response_model=SingleUser, status_code=201
)
async def create_user(
    data: SingleUser, service: UserService = Depends(get_user_service)
) -> SingleUser:
    return await service.create_user(
        user_id=data.userId,
        born=datetime.strptime(data.born, "%Y-%m-%d").date(),
        gender=data.gender,
    )


@router.post(
    "/{user_id}/needs/{feature}",
    description="Attach a feature to user",
    status_code=201,
    response_model=SingleUserExtended,
)
async def create_user_feature(
    user_id: str, feature: str, service: UserService = Depends(get_user_service)
) -> SingleUserExtended:
    await service.attach_requested_feature_to_user(user_id=user_id, feature=feature)
    return await service.get_user_by_id(user_id=user_id)


@router.post(
    "/{user_id}/rates/{place_id}/with/{rating}",
    description="Attach a feature to user",
    status_code=201,
)
async def create_user_rating(
    user_id: str,
    place_id: str,
    rating: float,
    service: UserService = Depends(get_user_service),
) -> bool:
    return await service.create_user_rating(
        user_id=user_id, place_id=place_id, rating=rating
    )


@router.put("/{user_id}", description="Update a user", response_model=SingleUser)
async def update_user(
    data: SingleUser, service: UserService = Depends(get_user_service)
) -> SingleUser:
    return await service.update_user(
        user_id=data.userId,
        born=datetime.strptime(data.born, "%Y-%m-%d").date(),
        gender=data.gender,
    )


@router.delete("/{user_id}", description="Delete a user", response_model=bool)
async def delete_user(
    user_id: str, service: UserService = Depends(get_user_service)
) -> bool:
    return await service.delete_user(user_id=user_id)


@router.delete(
    "/{user_id}/does-not-need/{feature}",
    description="Detach a feature from user",
    response_model=SingleUserExtended,
)
async def remove_user_feature(
    user_id: str, feature: str, service: UserService = Depends(get_user_service)
) -> SingleUserExtended:
    await service.detach_requested_feature_to_user(user_id=user_id, feature=feature)
    return await service.get_user_by_id(user_id=user_id)
