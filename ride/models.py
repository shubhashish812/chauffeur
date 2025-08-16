from typing import Optional

from pydantic import BaseModel


# Base model with fields common to all transactions
class RideBase(BaseModel):
    rideId: str
    status: str


# 1️⃣ Request transaction
class RideRequest(RideBase):
    riderId: str
    pickup: dict  # {"lat": float, "lng": float, "address": str}
    drop: dict  # {"lat": float, "lng": float, "address": str}
    fareEstimate: Optional[float] = None
    metadata: Optional[dict] = {}


# 2️⃣ Accept transaction
class RideAccept(RideBase):
    driverId: str
    metadata: Optional[dict] = {}


# 3️⃣ Arriving transaction
class RideArriving(RideBase):
    driverId: str
    eta: Optional[int] = None  # in seconds
    metadata: Optional[dict] = {}


# 4️⃣ Active transaction
class RideActive(RideBase):
    driverId: str
    startTime: Optional[str] = None
    metadata: Optional[dict] = {}


# 5️⃣ Completed transaction
class RideCompleted(RideBase):
    driverId: str
    endTime: Optional[str] = None
    fare: Optional[float] = None
    metadata: Optional[dict] = {}


# 6️⃣ Cancelled transaction
class RideCancelled(RideBase):
    cancelledBy: str  # "rider" or "driver"
    reason: Optional[str] = None
    metadata: Optional[dict] = {}
