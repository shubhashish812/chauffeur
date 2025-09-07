"""
Cloud Pub/Sub utilities for publishing messages
"""

import json
import logging
import os
from typing import Any, Dict

from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)


class PubSubPublisher:
    """Generic Pub/Sub publisher for various use cases"""

    def __init__(self):
        """
        Initialize Pub/Sub publisher

        Args:
            project_id: will get from environment
        """
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.publisher = pubsub_v1.PublisherClient()

    def publish(self, data: Dict[str, Any], **attributes) -> bool:
        """
        Publish a message to a Pub/Sub topic

        Args:
            data: Data to publish (will be converted to JSON)
            **attributes: Optional message attributes

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            topic_name = os.getenv("PUBSUB_TOPIC_NAME")
            topic_path = self.publisher.topic_path(self.project_id, topic_name)
            message_data = json.dumps(data).encode("utf-8")
            future = self.publisher.publish(topic_path, message_data, **attributes)
            message_id = future.result()

            logger.info(f"Published message to {topic_name}, message ID: {message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message to {topic_name}: {str(e)}")
            return False


pubsub_publisher = PubSubPublisher()
