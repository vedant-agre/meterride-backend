"""Pydantic schemas for data validation and serialization."""

from app.schemas.auth import (
    TokenResponse,
    UserLoginInfo,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.driver import (
    DriverRegisterRequest,
    DriverResponse,
    DriverStatusResponse,
    DriverStatusUpdateRequest,
    DriverUpdateRequest,
)
from app.schemas.user import UserResponse, UserUpdateRequest
from app.schemas.vehicle import (
    VehicleCreateRequest,
    VehicleResponse,
    VehicleUpdateRequest,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserLoginInfo",
    "TokenResponse",
    "UserResponse",
    "UserUpdateRequest",
    "DriverRegisterRequest",
    "DriverResponse",
    "DriverUpdateRequest",
    "DriverStatusUpdateRequest",
    "DriverStatusResponse",
    "VehicleCreateRequest",
    "VehicleResponse",
    "VehicleUpdateRequest",
]
