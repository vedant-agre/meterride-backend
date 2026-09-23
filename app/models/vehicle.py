import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.driver import Driver


class VehicleType(str, enum.Enum):
    BIKE = "BIKE"
    AUTO = "AUTO"
    SEDAN = "SEDAN"
    SUV = "SUV"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, name="vehicle_type", native_enum=False),
        nullable=False,
    )
    registration_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    color: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    driver: Mapped["Driver"] = relationship(
        "Driver",
        back_populates="vehicles",
    )
