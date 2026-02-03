from typing import Any

import neo4j.spatial
from pydantic import BaseModel, ConfigDict, model_validator
from app.dto.category import SingleCategory
from app.dto.feature import SingleFeature


class SinglePlace(BaseModel):
    placeId: str
    name: str

    latitude: float | None = None
    longitude: float | None = None
    locality: str | None = None
    country: str | None = None
    region: str | None = None
    postcode: str | None = None
    freeform: str | None = None
    confidence: float | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def unpack_neo4j_point(cls, data: Any) -> Any:
        # Verificamos si 'data' se comporta como un diccionario (los Nodos Neo4j lo hacen)
        if hasattr(data, "get"):
            location = data.get("coordinates")

            # Si existe location y tiene atributos de coordenadas (x=lon, y=lat)
            if (
                location is not None
                and hasattr(location, "x")
                and hasattr(location, "y")
            ):
                new_data = dict(data)
                new_data["latitude"] = location.y
                new_data["longitude"] = location.x
                return new_data

        return data


class SinglePlaceExtended(SinglePlace):
    features: list[SingleFeature] = []
    categories: list[SingleCategory] = []


class SinglePlaceCategoryMatch(BaseModel):
    name: str
    avgRating: float

    model_config = ConfigDict(from_attributes=True)


class SinglePlaceRecommended(SinglePlace):
    matches: list[SinglePlaceCategoryMatch]
    distance: float
