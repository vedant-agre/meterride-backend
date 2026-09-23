from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreateRequest, VehicleUpdateRequest
from app.services.exceptions import ConflictError, NotFoundError


class VehicleService:
    @staticmethod
    def create_vehicle(
        db: Session, driver_id: UUID, data: VehicleCreateRequest
    ) -> Vehicle:
        # Check registration number uniqueness
        existing_reg = (
            db.query(Vehicle)
            .filter(Vehicle.registration_number == data.registration_number)
            .first()
        )
        if existing_reg:
            raise ConflictError("Vehicle registration number is already registered")

        vehicle = Vehicle(
            driver_id=driver_id,
            vehicle_type=data.vehicle_type,
            registration_number=data.registration_number,
            model=data.model,
            color=data.color,
            capacity=data.capacity,
            is_active=True,
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        return vehicle

    @staticmethod
    def get_driver_vehicles(db: Session, driver_id: UUID) -> List[Vehicle]:
        return db.query(Vehicle).filter(Vehicle.driver_id == driver_id).all()

    @staticmethod
    def get_vehicle_by_id(db: Session, vehicle_id: UUID) -> Vehicle:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise NotFoundError("Vehicle not found")
        return vehicle

    @staticmethod
    def update_vehicle(
        db: Session, vehicle: Vehicle, data: VehicleUpdateRequest
    ) -> Vehicle:
        if data.model is not None:
            vehicle.model = data.model
        if data.color is not None:
            vehicle.color = data.color
        if data.capacity is not None:
            vehicle.capacity = data.capacity
        if data.is_active is not None:
            vehicle.is_active = data.is_active

        db.commit()
        db.refresh(vehicle)
        return vehicle

    @staticmethod
    def delete_vehicle(db: Session, vehicle: Vehicle) -> None:
        """Soft delete/deactivate a vehicle."""
        vehicle.is_active = False
        db.commit()
