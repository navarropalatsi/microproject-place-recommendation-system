import random
import uuid
import pytz

from app.dto.feature import SingleFeature
from app.dto.place import SinglePlace
from app.dto.user import SingleUserExtended
from app.tests import faker

def get_user_faker() -> SingleUserExtended:
    return SingleUserExtended(
        userId=str(uuid.uuid4()),
        born=faker.date_of_birth(tzinfo=pytz.UTC, minimum_age=15, maximum_age=75).isoformat(),
        gender=random.choice(["m", "f"]),
    )

def get_place_faker() -> SinglePlace:
    return SinglePlace(
        placeId=str(uuid.uuid4()),
        name=faker.company(),
        locality=faker.city(),
        country=faker.country(),
        postcode=faker.postcode(),
        region=faker.word(),
        freeform=faker.address()
    )

def get_feature_faker() -> SingleFeature:
    return SingleFeature(
        name=faker.word()
    )

def get_category_faker() -> SingleFeature:
    return SingleFeature(
        name=faker.word()
    )