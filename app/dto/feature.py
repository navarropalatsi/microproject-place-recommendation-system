from pydantic import BaseModel, ConfigDict


class SingleFeature(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)
