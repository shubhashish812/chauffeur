"""
Shared utilities for the codebase
"""

import json
import time
from typing import Any, Dict, Optional

from flask import Response


def create_response(
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    status_code: int = 200,
) -> Response:
    """
    Create a standardized response

    Args:
        data: Response data (for success)
        error: Error message (for errors)
        status_code: HTTP status code

    Returns:
        Flask Response object
    """
    response_data = {"success": error is None, "timestamp": time.time()}

    if error:
        response_data["error"] = error
    else:
        response_data["data"] = data

    return Response(
        json.dumps(response_data), status=status_code, content_type="application/json"
    )
