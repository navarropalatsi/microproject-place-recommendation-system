from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.config.neo4j import setup_db
from app.config.settings import settings
from app.router.users import router as user_router
from app.router.features import router as feature_router
from app.router.categories import router as category_router
from app.router.places import router as places_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.driver = await setup_db()
    yield
    await app.state.driver.close()


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/",
    redoc_url="/redoc",
    contact={
        "email": "joannavarropalatsi@gmail.com",
        "name": "Joan Navarro Palatsi",
        "url": "https://github.com/navarropalatsi",
    },
)


@app.exception_handler(HTTPException)
async def exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


app.include_router(user_router)
app.include_router(feature_router)
app.include_router(category_router)
app.include_router(places_router)
