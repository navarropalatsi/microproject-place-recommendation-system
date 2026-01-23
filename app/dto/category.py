from pydantic import BaseModel, ConfigDict


class SingleCategory(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)
