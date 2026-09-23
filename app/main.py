from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth_router, drivers_router, users_router, vehicles_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the MeterRide Smart Mobility Platform.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def read_root() -> dict[str, str]:
    """Root endpoint welcoming consumers to the API."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["Monitoring"])
def health_check() -> dict[str, str]:
    """Health check endpoint to verify service availability."""
    return {
        "status": "ok",
        "service": "meterride-backend",
    }


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(drivers_router)
app.include_router(vehicles_router)
