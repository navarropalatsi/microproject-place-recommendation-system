from fastapi import Request, Depends

from app.dao.place_dao import PlaceDAO
from app.services.category_service import CategoryService
from app.services.feature_service import FeatureService
from app.services.place_service import PlaceService
from app.services.recommendation_service import RecommendationService
from app.services.user_service import UserService


def get_driver(request: Request):
    return request.app.state.driver


async def get_user_service(driver=Depends(get_driver)):
    return UserService(driver)


async def get_feature_service(driver=Depends(get_driver)):
    return FeatureService(driver)


async def get_category_service(driver=Depends(get_driver)):
    return CategoryService(driver)


async def get_place_service(driver=Depends(get_driver)):
    return PlaceService(driver)


async def get_recommendation_service(driver=Depends(get_driver)):
    return RecommendationService(driver)
