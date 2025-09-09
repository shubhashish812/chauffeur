"""
Authentication Handler - GCP Cloud Function
Simple request router that initializes appropriate auth interfaces
"""

import logging

import functions_framework
from flask import Request, Response

from config import AUTH_REGISTRY
from config.models import AuthRequest
from shared.utils import create_response

logger = logging.getLogger(__name__)


@functions_framework.http
def auth_handler(request: Request) -> Response:
    """
    GCP Cloud Function for authentication
    Routes requests to appropriate auth interfaces based on 'type' and 'action' fields
    """
    try:
        # Parse request data
        if request.is_json:
            request_data = request.get_json()
        else:
            return create_response(error="Request must be JSON", status_code=400)

        # Validate main request structure
        try:
            auth_request = AuthRequest(**request_data)
        except Exception as e:
            return create_response(
                error=f"Invalid request structure: {str(e)}", status_code=400
            )

        # Get interface and model from registry
        try:
            interface_class, _ = AUTH_REGISTRY[auth_request.type]
        except KeyError:
            return create_response(
                error=f"Unsupported auth type: {auth_request.type}", status_code=400
            )

        # Initialize auth interface with request data
        interface = interface_class(request_data)

        # Dynamically call action method if it exists
        if not hasattr(interface, auth_request.action):
            return create_response(
                error=f"Unsupported action '{auth_request.action}' for {auth_request.type}",
                status_code=400,
            )

        # Get the method and call it
        method = getattr(interface, auth_request.action)
        result = method()

        return create_response(data=result)

    except Exception as e:
        return create_response(
            error=f"Authentication failed: {str(e)}", status_code=500
        )
