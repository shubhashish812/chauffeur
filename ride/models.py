from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from shared.firestore_mixin import FirestoreSyncMixin


class Location(BaseModel):
    """Location model for coordinates"""

    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")


class Ride(BaseModel):
    """Main ride model for Firestore collection"""

    rideId: str = Field(..., description="Auto-generated document ID")
    riderUid: str = Field(..., description="UID of the rider")
    driverUid: Optional[str] = Field(default=None, description="UID of assigned driver")
    origin: Location = Field(..., description="Pickup location")
    destination: Location = Field(..., description="Dropoff location")
    status: Literal[
        "request", "accept", "arriving", "active", "completed", "cancelled"
    ] = Field(default="request", description="Current ride status")

    @field_validator("origin", "destination", mode="before")
    def validate_location(cls, v):
        # If it's already a Location instance, return it
        if isinstance(v, Location):
            return v
        # If it's a dict, validate and convert to Location
        if isinstance(v, dict):
            if "lat" not in v or "lng" not in v:
                raise ValueError("Location must contain 'lat' and 'lng' fields")
            return Location(**v)
        raise ValueError("Location must be a dict with 'lat' and 'lng' fields")


class RideRequest(BaseModel):
    """Request model for ride creation"""

    riderUid: str = Field(..., description="UID of the rider")
    origin: Location = Field(..., description="Pickup location")
    destination: Location = Field(..., description="Dropoff location")


class RideCollection(FirestoreSyncMixin):
    """Ride class for Firestore operations"""

    collection_name = "rides"
    model = Ride
