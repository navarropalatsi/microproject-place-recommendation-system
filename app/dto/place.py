from pydantic import BaseModel, ConfigDict
from app.dto.category import SingleCategory
from app.dto.feature import SingleFeature


class SinglePlace(BaseModel):
    placeId: str
    name: str
    fullAddress: str

    model_config = ConfigDict(from_attributes=True)

class SinglePlaceExtended(SinglePlace):
    features: list[SingleFeature] = []
    categories: list[SingleCategory] = []