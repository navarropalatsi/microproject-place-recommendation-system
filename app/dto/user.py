from typing import Literal

from neo4j.time import Date
from pydantic import BaseModel, ConfigDict, field_validator
from app.dto.feature import SingleFeature


class SingleUser(BaseModel):
    userId: str
    born: str | None
    gender: Literal["m", "f"] | None

    @field_validator("born", mode="before")
    @classmethod
    def transform(cls, raw: str | Date | None) -> str:
        if isinstance(raw, Date):
            return raw.strftime("%Y-%m-%d")
        return raw

    model_config = ConfigDict(from_attributes=True)


class SingleUserExtended(SingleUser):
    features: list[SingleFeature] = []
