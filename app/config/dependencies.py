from fastapi import Request, Depends

from app.services.category_service import CategoryService
from app.services.feature_service import FeatureService
from app.services.place_service import PlaceService
from app.services.recommendation_service import RecommendationService
from app.services.user_service import UserService


def get_driver(request: Request):
    return request.app.state.driver


async def get_feature_service(driver=Depends(get_driver)):
    return FeatureService(driver)


async def get_category_service(driver=Depends(get_driver)):
    return CategoryService(driver)


async def get_place_service(
    driver=Depends(get_driver),
    category_service: CategoryService = Depends(get_category_service),
    feature_service: FeatureService = Depends(get_feature_service),
):
    return PlaceService(
        driver,
        category_service=category_service,
        feature_service=feature_service,
    )


async def get_user_service(
    driver=Depends(get_driver),
    feature_service: FeatureService = Depends(get_feature_service),
    place_service: PlaceService = Depends(get_place_service),
):
    return UserService(
        driver,
        feature_service=feature_service,
        place_service=place_service,
    )


async def get_recommendation_service(
    driver=Depends(get_driver),
    category_service: CategoryService = Depends(get_category_service),
    user_service: UserService = Depends(get_user_service),
):
    return RecommendationService(
        driver,
        category_service=category_service,
        user_service=user_service,
    )
