from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.driver import Driver
from app.models.user import User, UserRole
from app.routers.deps import get_current_driver, get_current_user
from app.schemas.vehicle import (
    VehicleCreateRequest,
    VehicleResponse,
    VehicleUpdateRequest,
)
from app.services.exceptions import ConflictError, NotFoundError
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new vehicle",
)
def create_vehicle(
    payload: VehicleCreateRequest,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> VehicleResponse:
    """Register a new vehicle owned by the authenticated driver."""
    try:
        vehicle = VehicleService.create_vehicle(db, current_driver.id, payload)
        return vehicle
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.get(
    "",
    response_model=List[VehicleResponse],
    status_code=status.HTTP_200_OK,
    summary="List all vehicles for current driver",
)
def list_vehicles(
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> List[VehicleResponse]:
    """List all vehicles registered under the authenticated driver."""
    return VehicleService.get_driver_vehicles(db, current_driver.id)


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vehicle details",
)
def get_vehicle(
    vehicle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VehicleResponse:
    """Get details of a specific vehicle. Driver must be the owner, or requester must be Admin."""
    try:
        vehicle = VehicleService.get_vehicle_by_id(db, vehicle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    if current_user.role != UserRole.ADMIN:
        # Check if user has driver profile and is the owner
        if not current_user.driver or vehicle.driver_id != current_user.driver.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Driver does not own this vehicle",
            )

    return vehicle


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update vehicle details",
)
def update_vehicle(
    vehicle_id: UUID,
    payload: VehicleUpdateRequest,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> VehicleResponse:
    """Update vehicle properties. Only owning driver can update."""
    try:
        vehicle = VehicleService.get_vehicle_by_id(db, vehicle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    if vehicle.driver_id != current_driver.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver does not own this vehicle",
        )

    return VehicleService.update_vehicle(db, vehicle, payload)


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete or deactivate a vehicle",
)
def delete_vehicle(
    vehicle_id: UUID,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> None:
    """Soft delete or deactivate a vehicle owned by the driver."""
    try:
        vehicle = VehicleService.get_vehicle_by_id(db, vehicle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    if vehicle.driver_id != current_driver.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver does not own this vehicle",
        )

    VehicleService.delete_vehicle(db, vehicle)
    return None
