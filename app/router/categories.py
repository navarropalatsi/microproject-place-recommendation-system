from fastapi import APIRouter, Depends

from app.config.dependencies import get_category_dao
from app.dao.category import CategoryDAO
from app.dto.category import SingleCategory

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", description="Get all categories", response_model=list[SingleCategory])
async def get_all_categories(
    dao: CategoryDAO = Depends(get_category_dao), skip: int = 0, limit: int = 25
) -> list[SingleCategory]:
    return await dao.all(skip=skip, limit=limit, order="ASC")


@router.get(
    "/{name}", description="Get a single category", response_model=SingleCategory
)
async def find_category_by_name(
    name: str, dao: CategoryDAO = Depends(get_category_dao)
) -> SingleCategory:
    return await dao.find(name=name)


@router.post("", description="Create a new category", response_model=SingleCategory)
async def create_category(
    data: SingleCategory, dao: CategoryDAO = Depends(get_category_dao)
) -> SingleCategory:
    return await dao.create(name=data.name)


@router.delete("/{name}", description="Delete a category", response_model=bool)
async def delete_category(
    name: str, dao: CategoryDAO = Depends(get_category_dao)
) -> bool:
    return await dao.delete(name=name)
