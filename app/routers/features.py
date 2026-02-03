from fastapi import APIRouter, Depends

from app.config.dependencies import get_feature_service
from app.services.feature_service import FeatureService
from app.dto.feature import SingleFeature

router = APIRouter(prefix="/features", tags=["features"])


@router.get("", description="Get all features", response_model=list[SingleFeature])
async def get_all_features(
    service: FeatureService = Depends(get_feature_service),
    skip: int = 0,
    limit: int = 25,
) -> list[SingleFeature]:
    return await service.get_all_features(skip=skip, limit=limit, order="ASC")


@router.get("/{name}", description="Get a single feature", response_model=SingleFeature)
async def find_feature_by_name(
    name: str, service: FeatureService = Depends(get_feature_service)
) -> SingleFeature:
    return await service.get_single_feature(name=name)


@router.post("", description="Create a new feature", response_model=SingleFeature)
async def create_feature(
    data: SingleFeature, service: FeatureService = Depends(get_feature_service)
) -> SingleFeature:
    return await service.create_feature(name=data.name)


@router.put("/{name}", description="Create a new feature", response_model=SingleFeature)
async def update_feature(
    name: str,
    data: SingleFeature,
    service: FeatureService = Depends(get_feature_service),
) -> SingleFeature:
    return await service.update_feature(name=name, new_name=data.name)


@router.delete("/{name}", description="Delete a feature", response_model=bool)
async def delete_feature(
    name: str, service: FeatureService = Depends(get_feature_service)
) -> bool:
    return await service.delete_feature(name=name)
