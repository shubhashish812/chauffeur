import uuid
from enum import Enum
from typing import Any, Dict

from ride.models import Ride, RideCollection, RideRequest
from shared.pubsub import pubsub_publisher


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
            )

            RideCollection.sync(ride_id, ride_data, create=True)

            # Publish to Pub/Sub for driver matching
            pubsub_success = pubsub_publisher.publish(ride_data.model_dump())

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
