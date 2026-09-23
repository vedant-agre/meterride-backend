from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.vehicle import VehicleType


class VehicleCreateRequest(BaseModel):
    vehicle_type: VehicleType
    registration_number: str = Field(..., min_length=3, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    color: str = Field(..., min_length=1, max_length=50)
    capacity: int = Field(..., ge=1, le=50)


class VehicleResponse(BaseModel):
    id: UUID
    driver_id: UUID
    vehicle_type: VehicleType
    registration_number: str
    model: str
    color: str
    capacity: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class VehicleUpdateRequest(BaseModel):
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, min_length=1, max_length=50)
    capacity: Optional[int] = Field(None, ge=1, le=50)
    is_active: Optional[bool] = None
