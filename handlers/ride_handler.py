import functions_framework

from ride.rideinterface import RideInterface
from shared.utils import create_response


@functions_framework.http
def ride_handler(request):
    try:
        # Parse request data
        if request.is_json:
            request_data = request.get_json()
        else:
            return create_response(error="Request must be JSON", status_code=400)

        # Initialize ride interface with request data
        try:
            interface = RideInterface(**request_data)
        except (ValueError, TypeError) as e:
            return create_response(
                error=f"Invalid request structure: {str(e)}", status_code=400
            )

        # Dynamically call action method
        method = getattr(interface, interface.type.value)
        result = method()
        return create_response(data=result)

    except Exception as e:
        return create_response(error=f"Request failed: {str(e)}", status_code=500)
