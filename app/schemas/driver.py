from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.driver import DriverStatus


class DriverRegisterRequest(BaseModel):
    license_number: str = Field(..., min_length=3, max_length=50)


class DriverResponse(BaseModel):
    id: UUID
    user_id: UUID
    license_number: str
    status: DriverStatus
    current_latitude: Optional[Decimal] = None
    current_longitude: Optional[Decimal] = None
    rating_average: Decimal
    total_rides: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DriverUpdateRequest(BaseModel):
    license_number: Optional[str] = Field(None, min_length=3, max_length=50)


class DriverStatusUpdateRequest(BaseModel):
    status: DriverStatus


class DriverStatusResponse(BaseModel):
    driver_id: UUID
    status: DriverStatus
