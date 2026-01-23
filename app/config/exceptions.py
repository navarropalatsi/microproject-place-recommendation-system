from fastapi import HTTPException


class AlreadyExists(HTTPException):
    def __init__(self, detail="Already exists"):
        self.status_code = 409
        self.detail = detail

class NotFound(HTTPException):
    def __init__(self, detail: str="Not Found"):
        self.status_code = 404
        self.detail = detail