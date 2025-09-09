"""
Simple RTDB Client
"""

from typing import Any, Dict, List

from shared.firebase import firebase_client


class RTDBClient:
    """Simple RTDB client"""

    def __init__(self):
        self.rtdb = firebase_client.get_rtdb()

    def search(
        self,
        path: str = "drivers",
        query_params: Dict[str, Any] = {"status": "available"},
    ) -> List[Dict[str, Any]]:
        """Generic search method for RTDB"""
        try:
            ref = self.rtdb.child(path)
            data = ref.get()
            if data:
                return [data] if isinstance(data, dict) else data
            return []
        except Exception as e:
            raise Exception(f"RTDB search failed: {str(e)}")


# Global instance
rtdb_client = RTDBClient()
