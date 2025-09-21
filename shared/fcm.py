"""
Firebase Cloud Messaging (FCM) service for sending notifications
"""

import logging
from typing import Any, Dict, List

from firebase_admin import messaging

logger = logging.getLogger(__name__)


class FCMService:
    """FCM service for sending notifications to drivers"""

    def __init__(self):
        self.fcm = messaging

    def send_ride_request_notification(
        self,
        driver_fcm_token: str,
        ride_id: str,
        rider_uid: str,
        origin: Dict[str, float],
        destination: Dict[str, float],
        rider_name: str = "Rider",
    ) -> bool:
        """
        Send ride request notification to driver

        Args:
            driver_fcm_token: Driver's FCM token
            ride_id: Unique ride identifier
            rider_uid: Rider's UID
            origin: Pickup location {lat, lng}
            destination: Dropoff location {lat, lng}
            rider_name: Rider's display name
        """
        try:
            notification = messaging.Notification(
                title="New Ride Request",
                body=f"Pickup request from {rider_name}",
            )

            data = {
                "rideId": ride_id,
                "riderUid": rider_uid,
                "originLat": str(origin["lat"]),
                "originLng": str(origin["lng"]),
                "destinationLat": str(destination["lat"]),
                "destinationLng": str(destination["lng"]),
                "riderName": rider_name,
                "action": "ride_request",
            }

            message = messaging.Message(
                notification=notification,
                data=data,
                token=driver_fcm_token,
            )

            response = messaging.send(message)
            logger.info(f"FCM notification sent successfully: {response}")
            return True

        except Exception as e:
            logger.error(f"FCM notification failed: {str(e)}")
            raise Exception(f"FCM notification failed: {str(e)}")

    def send_multicast_notification(
        self,
        driver_fcm_tokens: List[str],
        ride_id: str,
        rider_uid: str,
        origin: Dict[str, float],
        destination: Dict[str, float],
        rider_name: str = "Rider",
    ) -> Dict[str, Any]:
        """
        Send ride request notification to multiple drivers

        Returns:
            Dict with success_count and failure_count
        """
        try:
            notification = messaging.Notification(
                title="New Ride Request",
                body=f"Pickup request from {rider_name}",
            )

            data = {
                "rideId": ride_id,
                "riderUid": rider_uid,
                "originLat": str(origin["lat"]),
                "originLng": str(origin["lng"]),
                "destinationLat": str(destination["lat"]),
                "destinationLng": str(destination["lng"]),
                "riderName": rider_name,
                "action": "ride_request",
            }

            message = messaging.MulticastMessage(
                notification=notification,
                data=data,
                tokens=driver_fcm_tokens,
            )

            response = messaging.send_multicast(message)
            logger.info(
                f"FCM multicast sent: {response.success_count} success, {response.failure_count} failures"
            )

            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": response.responses,
            }

        except Exception as e:
            logger.error(f"Failed to send FCM multicast: {str(e)}")
            return {
                "success_count": 0,
                "failure_count": len(driver_fcm_tokens),
                "responses": [],
            }


# Global instance
fcm_service = FCMService()
