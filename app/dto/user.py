from pydantic import BaseModel

from app.dto.feature import SingleFeature


class SingleUser(BaseModel):
    userId: str
    born: str
    gender: str

    class Config:
        from_attributes = True

class SingleUserExtended(SingleUser):
    features: list[SingleFeature]