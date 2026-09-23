from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.driver import Driver
from app.models.user import User, UserRole
from app.routers.deps import get_current_driver, get_current_user, require_roles
from app.schemas.driver import (
    DriverRegisterRequest,
    DriverResponse,
    DriverStatusResponse,
    DriverStatusUpdateRequest,
    DriverUpdateRequest,
)
from app.services.driver_service import DriverService
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.post(
    "/register",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register as a driver",
)
def register_driver(
    payload: DriverRegisterRequest,
    current_user: User = Depends(
        require_roles(UserRole.RIDER, UserRole.DRIVER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
) -> DriverResponse:
    """Create a Driver profile linked to the authenticated user account and elevate user role to DRIVER."""
    try:
        driver = DriverService.register_driver(db, current_user, payload)
        return driver
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.get(
    "/me",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current driver profile",
)
def get_driver_profile(
    current_driver: Driver = Depends(get_current_driver),
) -> DriverResponse:
    """Return current driver's profile and active statistics."""
    return current_driver


@router.patch(
    "/me",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK,
    summary="Update driver profile",
)
def update_driver_profile(
    payload: DriverUpdateRequest,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> DriverResponse:
    """Update driver-specific details (e.g. license update)."""
    try:
        updated_driver = DriverService.update_driver_profile(
            db, current_driver, payload
        )
        return updated_driver
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.patch(
    "/status",
    response_model=DriverStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Change driver availability state",
)
def update_driver_status(
    payload: DriverStatusUpdateRequest,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> DriverStatusResponse:
    """Change driver availability state (OFFLINE, AVAILABLE, BUSY)."""
    try:
        driver = DriverService.update_driver_status(db, current_driver, payload.status)
        return DriverStatusResponse(
            driver_id=driver.id,
            status=driver.status,
        )
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
