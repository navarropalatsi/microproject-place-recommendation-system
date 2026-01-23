from fastapi import APIRouter, Depends

from app.config.dependencies import get_user_dao
from app.dao.user import UserDAO
from app.dto.user import SingleUser, SingleUserExtended

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("", description="Get all users", response_model=list[SingleUser])
def get_all_users(dao: UserDAO = Depends(get_user_dao), skip: int = 0, limit: int = 25) -> list[SingleUser]:
    return dao.all(skip=skip, limit=limit)

@router.get("/{user_id}", description="Get a single user", response_model=SingleUser)
def find_user_by_id(user_id: str, dao: UserDAO = Depends(get_user_dao)) -> SingleUser:
    return dao.find(user_id=user_id)

@router.post("", description="Create a new user", response_model=SingleUser, status_code=201)
def create_user(data: SingleUser, dao: UserDAO = Depends(get_user_dao)) -> SingleUser:
    return dao.create_or_update(user_id=data.userId, born=data.born, gender=data.gender)

@router.post("/{user_id}/needs/{feature}", description="Attach a feature to user", status_code=201, response_model=SingleUserExtended)
def create_user_feature(user_id: str, feature: str, dao: UserDAO = Depends(get_user_dao)) -> SingleUserExtended:
    return dao.add_feature(user_id=user_id, feature=feature)

@router.put("/{user_id}", description="Update a user", response_model=SingleUser)
def update_user(data: SingleUser, dao: UserDAO = Depends(get_user_dao)) -> SingleUser:
    return dao.create_or_update(user_id=data.userId, born=data.born, gender=data.gender, create=False)

@router.delete("/{user_id}", description="Delete a user", response_model=bool)
def delete_user(user_id: str, dao: UserDAO = Depends(get_user_dao)) -> bool:
    return dao.delete(user_id=user_id)

@router.delete("/{user_id}/does-not-need/{feature}", description="Detach a feature from user", response_model=SingleUserExtended)
def remove_user_feature(user_id: str, feature: str, dao: UserDAO = Depends(get_user_dao)) -> SingleUserExtended:
    return dao.remove_feature(user_id=user_id, feature=feature)