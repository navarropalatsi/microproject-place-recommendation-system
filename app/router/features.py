from fastapi import APIRouter, Depends

from app.config.dependencies import get_feature_dao
from app.dao.feature import FeatureDAO
from app.dto.feature import SingleFeature

router = APIRouter(
    prefix="/features",
    tags=["features"]
)

@router.get("", description="Get all features", response_model=list[SingleFeature])
def get_all_features(dao: FeatureDAO = Depends(get_feature_dao), skip: int = 0, limit: int = 25) -> list[SingleFeature]:
    return dao.all(skip=skip, limit=limit, order="ASC")

@router.get("/{name}", description="Get a single feature", response_model=SingleFeature)
def find_feature_by_name(name: str, dao: FeatureDAO = Depends(get_feature_dao)) -> SingleFeature:
    return dao.find(name=name)

@router.post("", description="Create a new feature", response_model=SingleFeature)
def create_feature(data: SingleFeature, dao: FeatureDAO = Depends(get_feature_dao)) -> SingleFeature:
    return dao.create(name=data.name)

@router.delete("/{name}", description="Delete a feature", response_model=bool)
def delete_feature(name: str, dao: FeatureDAO = Depends(get_feature_dao)) -> bool:
    return dao.delete(name=name)