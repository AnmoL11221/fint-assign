import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import api_router
from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError, ParseError, ValidationError


def _configure_logging() -> None:
    level = logging.DEBUG if settings.debug or settings.parse_debug_logging else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("app.services.parsing").setLevel(level)
    logging.getLogger("app.services.pdf_extraction").setLevel(level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    _configure_logging()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    lifespan=lifespan,
)

app.include_router(api_router)


@app.exception_handler(ValidationError)
async def validation_error_handler(_: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": exc.code, "message": exc.message})


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": exc.code, "message": exc.message})


@app.exception_handler(ParseError)
async def parse_error_handler(_: Request, exc: ParseError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": exc.code, "message": exc.message})


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": exc.code, "message": exc.message})
