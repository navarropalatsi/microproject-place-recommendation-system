from pydantic import BaseModel, ConfigDict
from app.dto.category import SingleCategory
from app.dto.feature import SingleFeature


class SinglePlace(BaseModel):
    placeId: str
    name: str

    locality: str | None = None
    country: str | None = None
    region: str | None = None
    postcode: str | None = None
    freeform: str | None = None
    confidence: float | None = None

    model_config = ConfigDict(from_attributes=True)

class SinglePlaceExtended(SinglePlace):
    features: list[SingleFeature] = []
    categories: list[SingleCategory] = []