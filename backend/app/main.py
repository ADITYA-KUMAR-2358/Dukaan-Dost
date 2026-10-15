from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import get_settings
from app.core.errors import AppError
from app.db.session import ensure_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_database()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="DukaanDost", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(AppError)
    async def app_error(_request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(Exception)
    async def unexpected(_request: Request, _exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "server_error",
                    "message": "Something went wrong while handling that request.",
                    "details": [],
                }
            },
        )

    app.include_router(router)
    return app


app = create_app()
