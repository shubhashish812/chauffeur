"""
Matchmaker Handler - GCP Cloud Function
Listens to Pub/Sub events for ride matching and driver assignment
"""

import json
import logging

import functions_framework
from cloudevents.http import CloudEvent

from ride.rideinterface import RideInterface

logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def matchmaker_handler(cloud_event: CloudEvent):
    """
    GCP Cloud Function triggered by Pub/Sub subscription
    Processes ride requests for driver matching
    """
    try:
        # Extract message data from CloudEvent
        message_data = cloud_event.data.get("message", {})

        if not message_data:
            logger.error("No message data found in CloudEvent")
            return

        # Decode the message data
        if isinstance(message_data.get("data"), str):
            import base64

            decoded_data = base64.b64decode(message_data["data"]).decode("utf-8")
            message_payload = json.loads(decoded_data)
        else:
            message_payload = message_data.get("data", {})

        ride_id = message_payload["rideId"]
        logger.info(f"Processing ride request for rideId: {ride_id}")

        RideInterface.matchmake(ride_id)

        logger.info(f"Successfully processed ride request for rideId: {ride_id}")

    except Exception as e:
        logger.error(f"Matchmaker handler failed: {str(e)}")
        # In production, you might want to:
        # 1. Send the message to a dead letter queue
        # 2. Retry the processing
        # 3. Send notifications to administrators
        raise
