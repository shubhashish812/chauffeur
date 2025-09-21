"""
Simple RTDB Client
"""

import math
from typing import Any, Dict, List

from shared.firebase import firebase_client


class RTDBClient:
    """Simple RTDB client"""

    def __init__(self):
        self.rtdb = firebase_client.get_rtdb()

    def search(
        self,
        origin_lat: float,
        origin_lng: float,
        blacklisted_drivers: List[str],
        path: str = "zones",
        max_distance_km: float = 10.0,
    ) -> List[Dict[str, Any]]:
        """
        Search for drivers in zones around origin location

        Args:
            origin_lat: Origin latitude for zone calculation
            origin_lng: Origin longitude for zone calculation
            blacklisted_drivers: List of driver UIDs to exclude
            path: RTDB path (default: "zones")
            max_distance_km: Maximum distance in kilometers to search
        """
        try:
            # Calculate zones around origin (3x3 grid)
            zones_to_check = self._calculate_zones_around_point(origin_lat, origin_lng)

            available_drivers = []

            # Query each zone
            for zone in zones_to_check:
                zone_data = self.rtdb.child(path).child(zone).get()
                if not zone_data or "drivers" not in zone_data:
                    continue

                # Process drivers in this zone
                for driver_uid, driver_info in zone_data["drivers"].items():
                    if driver_uid in blacklisted_drivers:
                        continue

                    if driver_info.get("status") != "available":
                        continue

                    location = driver_info.get("location")
                    if not location or "lat" not in location or "lng" not in location:
                        continue

                    # Calculate distance and filter
                    distance = self._calculate_distance(
                        location["lat"], location["lng"], origin_lat, origin_lng
                    )

                    if distance <= max_distance_km:
                        driver_info["driverUid"] = driver_uid
                        driver_info["distanceFromOrigin"] = distance
                        available_drivers.append(driver_info)

            # Sort by distance and return closest driver only
            if available_drivers:
                available_drivers.sort(key=lambda x: x["distanceFromOrigin"])
                return [available_drivers[0]]  # Return only the closest driver
            return []

        except Exception as e:
            raise Exception(f"RTDB search failed: {str(e)}")

    def _calculate_zones_around_point(self, lat: float, lng: float) -> List[str]:
        """Calculate zone keys around a point (3x3 grid)"""
        zone_size = 0.01  # ~1km
        zones = []
        for lat_offset in [-1, 0, 1]:
            for lng_offset in [-1, 0, 1]:
                zone_lat = round((lat + lat_offset * zone_size) * 100) / 100
                zone_lng = round((lng + lng_offset * zone_size) * 100) / 100
                zones.append(f"{zone_lat}_{zone_lng}")
        return zones

    def _calculate_distance(
        self, lat1: float, lng1: float, lat2: float, lng2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in kilometers
        """
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])

        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        radius = 6371
        return c * radius


# Global instance
rtdb_client = RTDBClient()
