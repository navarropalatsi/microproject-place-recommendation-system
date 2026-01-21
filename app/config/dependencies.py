from fastapi import Request, Depends

from app.dao.category import CategoryDAO
from app.dao.feature import FeatureDAO
from app.dao.place import PlaceDAO
from app.dao.user import UserDAO


def get_driver(request: Request):
    return request.app.state.driver

def get_user_dao(driver = Depends(get_driver)):
    return UserDAO(driver)

def get_feature_dao(driver = Depends(get_driver)):
    return FeatureDAO(driver)

def get_category_dao(driver = Depends(get_driver)):
    return CategoryDAO(driver)

def get_place_dao(driver = Depends(get_driver)):
    return PlaceDAO(driver)