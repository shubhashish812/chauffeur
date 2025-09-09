import uuid
from enum import Enum
from typing import Any, Dict

from ride.models import Ride, RideCollection, RideRequest
from shared.pubsub import pubsub_publisher
from shared.rtdb import rtdb_client


class RideType(str, Enum):
    REQUEST = "request"
    ACCEPT = "accept"
    ARRIVING = "arriving"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RideInterface:
    def __init__(self, data: Dict[str, Any], type: RideType):
        self.data = data
        self.type = RideType(type)

    def request(self):
        """Create a new ride request in Firestore"""
        try:
            ride_request = RideRequest(**self.data)
            ride_id = str(uuid.uuid4())

            ride_data = Ride(
                rideId=ride_id,
                riderUid=ride_request.riderUid,
                driverUid=None,
                origin=ride_request.origin,
                destination=ride_request.destination,
                status="request",
                blacklistedDrivers=[],
            )

            RideCollection.sync(ride_id, ride_data, create=True)
            pubsub_success = pubsub_publisher.publish({"rideId": ride_id})

            return {
                "rideId": ride_id,
                "status": "request",
                "message": "Ride request created successfully",
                "driverMatchingQueued": pubsub_success,
            }
        except Exception as e:
            raise Exception(f"Failed to create ride request: {str(e)}")

    def accept(self):
        pass

    def arriving(self):
        pass

    def inprogress(self):
        pass

    def complete(self):
        pass

    def cancel(self):
        pass

    @staticmethod
    def matchmake(ride_id: str) -> Dict[str, Any]:
        """
        Static method to process ride request for driver matching
        Fetches ride from Firestore and searches for nearest drivers
        """
        try:
            ride = RideCollection.get(ride_id)
            if not ride:
                raise Exception(f"Ride not found: {ride_id}")

            nearest_drivers = rtdb_client.search("available")

            return {
                "rideId": ride_id,
                "status": "processing",
                "driversFound": len(nearest_drivers),
                "message": "Ride request processed for matching",
            }

        except Exception as e:
            raise Exception(f"Failed to process ride request: {str(e)}")
