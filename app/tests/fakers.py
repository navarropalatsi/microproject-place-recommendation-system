import random
import uuid
import pytz

from app.dto.feature import SingleFeature
from app.dto.place import SinglePlaceExtended
from app.dto.user import SingleUserExtended
from app.tests import faker

def get_user_faker() -> SingleUserExtended:
    return SingleUserExtended(
        userId=str(uuid.uuid4()),
        born=faker.date_of_birth(tzinfo=pytz.UTC, minimum_age=15, maximum_age=75).isoformat(),
        gender=random.choice(["m", "f"]),
    )

def get_place_faker() -> SinglePlaceExtended:
    return SinglePlaceExtended(
        placeId=str(uuid.uuid4()),
        name=faker.company(),
        fullAddress=faker.address(),
        categories=[],
        features=[]
    )

def get_feature_faker() -> SingleFeature:
    return SingleFeature(
        name=faker.word()
    )

def get_category_faker() -> SingleFeature:
    return SingleFeature(
        name=faker.word()
    )