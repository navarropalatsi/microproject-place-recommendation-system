from fastapi import APIRouter, Depends

from app.config.dependencies import get_category_service
from app.dto.category import SingleCategory
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", description="Get all categories", response_model=list[SingleCategory])
async def get_all_categories(
    service: CategoryService = Depends(get_category_service),
    skip: int = 0,
    limit: int = 25,
) -> list[SingleCategory]:
    return await service.get_all_categories(skip=skip, limit=limit, order="ASC")


@router.get(
    "/{name}", description="Get a single category", response_model=SingleCategory
)
async def find_category_by_name(
    name: str, service: CategoryService = Depends(get_category_service)
) -> SingleCategory:
    return await service.get_single_category(name=name)


@router.post("", description="Create a new category", response_model=SingleCategory)
async def create_category(
    data: SingleCategory, service: CategoryService = Depends(get_category_service)
) -> SingleCategory:
    return await service.create_category(name=data.name)


@router.put(
    "/{name}", description="Update an existing category", response_model=SingleCategory
)
async def update_category(
    name: str,
    data: SingleCategory,
    service: CategoryService = Depends(get_category_service),
) -> SingleCategory:
    return await service.update_category(name=name, new_name=data.name)


@router.delete("/{name}", description="Delete a category", response_model=bool)
async def delete_category(
    name: str, service: CategoryService = Depends(get_category_service)
) -> bool:
    return await service.delete_category(name=name)
