from werkzeug.exceptions import HTTPException


class AlreadyExists(HTTPException):
    code = 409
    description = "Already exists"