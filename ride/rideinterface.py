import logging
import uuid
from enum import Enum
from typing import Any, Dict

from ride.models import Ride, RideCollection, RideRequest
from shared.fcm import fcm_service
from shared.pubsub import pubsub_publisher
from shared.rtdb import rtdb_client

logger = logging.getLogger(__name__)


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

            nearest_drivers = rtdb_client.search(
                origin_lat=ride.origin.lat,
                origin_lng=ride.origin.lng,
                blacklisted_drivers=ride.blacklistedDrivers,
                max_distance_km=10.0,  # Configurable search radius
            )

            if not nearest_drivers:
                logger.warning(f"No available drivers found for ride {ride_id}")
                return

            closest_driver = nearest_drivers[0]
            driver_uid = closest_driver["driverUid"]
            logger.info(f"Found closest driver {driver_uid} for ride {ride_id}")

            # Check if driver has FCM token
            driver_fcm_token = closest_driver.get("fcmToken")
            if not driver_fcm_token:
                raise Exception(f"Driver {driver_uid} has no FCM token")

            # Send FCM notification
            fcm_service.send_ride_request_notification(
                driver_fcm_token=driver_fcm_token,
                ride_id=ride_id,
                rider_uid=ride.riderUid,
                origin={"lat": ride.origin.lat, "lng": ride.origin.lng},
                destination={"lat": ride.destination.lat, "lng": ride.destination.lng},
                rider_name="Rider",  # TODO: Get actual rider name
            )

            logger.info(f"FCM notification sent to driver {driver_uid}")
            return

        except Exception as e:
            raise Exception(f"Failed to process ride request: {str(e)}")
