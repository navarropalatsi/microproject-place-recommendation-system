from pydantic import BaseModel
from app.dto.category import SingleCategory
from app.dto.feature import SingleFeature


class SinglePlace(BaseModel):
    placeId: str
    name: str
    fullAddress: str

    class Config:
        from_attributes = True

class SinglePlaceExtended(SinglePlace):
    features: list[SingleFeature]
    categories: list[SingleCategory]