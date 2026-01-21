from pydantic import BaseModel

class SingleCategory(BaseModel):
    name: str

    class Config:
        from_attributes = True
