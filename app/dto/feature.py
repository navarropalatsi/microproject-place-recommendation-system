from pydantic import BaseModel

class SingleFeature(BaseModel):
    name: str

    class Config:
        from_attributes = True
