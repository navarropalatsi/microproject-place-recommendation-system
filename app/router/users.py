from fastapi import APIRouter, Depends

from app.config.dependencies import get_user_dao
from app.dao.user import UserDAO
from app.dto.user import SingleUser, SingleUserExtended

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", description="Get all users", response_model=list[SingleUser])
async def get_all_users(
    dao: UserDAO = Depends(get_user_dao), skip: int = 0, limit: int = 25
) -> list[SingleUser]:
    return await dao.all(skip=skip, limit=limit)


@router.get("/{user_id}", description="Get a single user", response_model=SingleUser)
async def find_user_by_id(
    user_id: str, dao: UserDAO = Depends(get_user_dao)
) -> SingleUser:
    return await dao.find(user_id=user_id)


@router.post(
    "", description="Create a new user", response_model=SingleUser, status_code=201
)
async def create_user(
    data: SingleUser, dao: UserDAO = Depends(get_user_dao)
) -> SingleUser:
    return await dao.create(user_id=data.userId, born=data.born, gender=data.gender)


@router.post(
    "/{user_id}/needs/{feature}",
    description="Attach a feature to user",
    status_code=201,
    response_model=SingleUserExtended,
)
async def create_user_feature(
    user_id: str, feature: str, dao: UserDAO = Depends(get_user_dao)
) -> SingleUserExtended:
    return await dao.add_feature(user_id=user_id, feature=feature)


@router.post(
    "/{user_id}/rates/{place_id}/with/{rating}",
    description="Attach a feature to user",
    status_code=201,
)
async def create_user_rating(
    user_id: str, place_id: str, rating: float, dao: UserDAO = Depends(get_user_dao)
) -> bool:
    return await dao.rate_place(user_id=user_id, place_id=place_id, rating=rating)


@router.put("/{user_id}", description="Update a user", response_model=SingleUser)
async def update_user(
    data: SingleUser, dao: UserDAO = Depends(get_user_dao)
) -> SingleUser:
    return await dao.update(user_id=data.userId, born=data.born, gender=data.gender)


@router.delete("/{user_id}", description="Delete a user", response_model=bool)
async def delete_user(user_id: str, dao: UserDAO = Depends(get_user_dao)) -> bool:
    return await dao.delete(user_id=user_id)


@router.delete(
    "/{user_id}/does-not-need/{feature}",
    description="Detach a feature from user",
    response_model=SingleUserExtended,
)
async def remove_user_feature(
    user_id: str, feature: str, dao: UserDAO = Depends(get_user_dao)
) -> SingleUserExtended:
    return await dao.remove_feature(user_id=user_id, feature=feature)
