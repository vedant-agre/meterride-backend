from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.driver import Driver, DriverStatus
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.schemas.driver import DriverRegisterRequest, DriverUpdateRequest
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


class DriverService:
    @staticmethod
    def register_driver(
        db: Session, user: User, data: DriverRegisterRequest
    ) -> Driver:
        # Check if user already has a driver profile
        existing_driver = db.query(Driver).filter(Driver.user_id == user.id).first()
        if existing_driver:
            raise ConflictError("User already has a registered driver profile")

        # Check if license number already exists
        existing_license = (
            db.query(Driver)
            .filter(Driver.license_number == data.license_number)
            .first()
        )
        if existing_license:
            raise ConflictError("Driver license number is already registered")

        # Elevate user role to DRIVER if not already
        if user.role != UserRole.ADMIN:
            user.role = UserRole.DRIVER

        driver = Driver(
            user_id=user.id,
            license_number=data.license_number,
            status=DriverStatus.OFFLINE,
            current_latitude=None,
            current_longitude=None,
            rating_average=Decimal("5.00"),
            total_rides=0,
        )
        db.add(driver)
        db.commit()
        db.refresh(driver)
        return driver

    @staticmethod
    def get_driver_by_user_id(db: Session, user_id: UUID) -> Driver:
        driver = db.query(Driver).filter(Driver.user_id == user_id).first()
        if not driver:
            raise NotFoundError("Driver profile not found")
        return driver

    @staticmethod
    def update_driver_profile(
        db: Session, driver: Driver, data: DriverUpdateRequest
    ) -> Driver:
        if (
            data.license_number is not None
            and data.license_number != driver.license_number
        ):
            existing_license = (
                db.query(Driver)
                .filter(
                    Driver.license_number == data.license_number,
                    Driver.id != driver.id,
                )
                .first()
            )
            if existing_license:
                raise ConflictError("License number is already registered")
            driver.license_number = data.license_number

        db.commit()
        db.refresh(driver)
        return driver

    @staticmethod
    def update_driver_status(
        db: Session, driver: Driver, new_status: DriverStatus
    ) -> Driver:
        if new_status == DriverStatus.AVAILABLE:
            active_vehicle = (
                db.query(Vehicle)
                .filter(
                    Vehicle.driver_id == driver.id,
                    Vehicle.is_active == True,
                )
                .first()
            )
            if not active_vehicle:
                raise BadRequestError(
                    "Cannot set status to AVAILABLE without an active vehicle"
                )

        driver.status = new_status
        db.commit()
        db.refresh(driver)
        return driver
