import functions_framework
from flask import Request, jsonify
import sys
import os

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from firebase_client import firebase_client
from auth_utils import get_user_from_token, create_user_response
from models import ErrorResponse

@functions_framework.http
def main(request: Request):
    """HTTP Cloud Function for user management."""
    
    # Set CORS headers
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    
    try:
        # Get the path and method
        path = request.path.strip('/')
        method = request.method
        
        # Route based on path
        if path.startswith('user/profile'):
            return handle_profile(request, headers)
        elif path.startswith('user/delete'):
            return handle_delete_account(request, headers)
        elif path.startswith('user/health'):
            return handle_health_check(headers)
        else:
            return jsonify(ErrorResponse(
                error="Not Found",
                message="Endpoint not found"
            ).dict()), 404, headers
            
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Internal Server Error",
            message=str(e)
        ).dict()), 500, headers

def handle_profile(request: Request, headers):
    """Handle profile operations."""
    method = request.method
    
    if method == 'GET':
        # Get user profile
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify(ErrorResponse(
                error="Unauthorized",
                message="Missing or invalid authorization header"
            ).dict()), 401, headers
        
        token = auth_header.split(' ')[1]
        user = get_user_from_token(token)
        
        if not user:
            return jsonify(ErrorResponse(
                error="Unauthorized",
                message="Invalid token"
            ).dict()), 401, headers
        
        return jsonify(create_user_response(user)), 200, headers
    
    elif method == 'PUT':
        # Update user profile
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify(ErrorResponse(
                error="Unauthorized",
                message="Missing or invalid authorization header"
            ).dict()), 401, headers
        
        token = auth_header.split(' ')[1]
        user = get_user_from_token(token)
        
        if not user:
            return jsonify(ErrorResponse(
                error="Unauthorized",
                message="Invalid token"
            ).dict()), 401, headers
        
        # Get update data from request
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error="Bad Request",
                message="No data provided"
            ).dict()), 400, headers
        
        # Update user profile (basic implementation)
        try:
            # For now, just return success
            # In a real implementation, you'd update the user in Firebase
            return jsonify({
                "message": "Profile updated successfully",
                "user": create_user_response(user)
            }), 200, headers
        except Exception as e:
            return jsonify(ErrorResponse(
                error="Update Failed",
                message=str(e)
            ).dict()), 500, headers
    
    else:
        return jsonify(ErrorResponse(
            error="Method Not Allowed",
            message=f"Method {method} not allowed for this endpoint"
        ).dict()), 405, headers

def handle_delete_account(request: Request, headers):
    """Handle account deletion."""
    if request.method != 'DELETE':
        return jsonify(ErrorResponse(
            error="Method Not Allowed",
            message=f"Method {request.method} not allowed for this endpoint"
        ).dict()), 405, headers
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify(ErrorResponse(
            error="Unauthorized",
            message="Missing or invalid authorization header"
        ).dict()), 401, headers
    
    token = auth_header.split(' ')[1]
    user = get_user_from_token(token)
    
    if not user:
        return jsonify(ErrorResponse(
            error="Unauthorized",
            message="Invalid token"
        ).dict()), 401, headers
    
    try:
        # Delete user from Firebase
        firebase_client.delete_user(user['uid'])
        return jsonify({
            "message": "Account deleted successfully"
        }), 200, headers
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Deletion Failed",
            message=str(e)
        ).dict()), 500, headers

def handle_health_check(headers):
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "user-management",
        "timestamp": "2024-01-01T00:00:00Z"
    }), 200, headers
