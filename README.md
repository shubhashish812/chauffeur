# Chauffeur - Cab Service Backend

## Local Development Setup

### Prerequisites
- Python 3.8+
- Google Cloud SDK (for authentication)
- Firebase project credentials

### Environment Variables
Create a `.env` file in the root directory:

```bash
# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key
GOOGLE_OAUTH_CLIENT_ID=your_google_oauth_client_id
FIREBASE_RTDB_URL=https://your-project-id-default-rtdb.firebaseio.com

# Google Cloud Configuration (for local development)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
GOOGLE_CLOUD_PROJECT=your_project_id
PUBSUB_TOPIC_NAME=your_request_listener
```

### Installation
```bash
pip install -r requirements.txt
```

### Running Handlers Locally

#### 1. Auth Handler
```bash
functions-framework --target=auth_handler --port=8080 --source=handlers/auth_handler.py
```

**Test with:**
```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "type": "basic",
    "action": "signup",
    "data": {
      "email": "test@example.com",
      "password": "password123",
      "display_name": "Test User",
      "role": "rider"
    }
  }'
```

#### 2. Ride Handler
```bash
functions-framework --target=ride_handler --port=8081 --source=handlers/ride_handler.py
```

**Test with:**
```bash
curl -X POST http://localhost:8081 \
  -H "Content-Type: application/json" \
  -d '{
    "type": "request",
    "data": {
      "riderId": "user123",
      "pickup": {"lat": 40.7128, "lng": -74.0060, "address": "New York"},
      "drop": {"lat": 40.7589, "lng": -73.9851, "address": "Times Square"}
    }
  }'
```

### Common Error Handling

#### 1. Credentials Error
```
google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found
```
**Solution:** Set up Application Default Credentials:
```bash
gcloud auth application-default login
```

#### 2. Firebase Initialization Error
```
Failed to initialize Firebase
```
**Solution:** Ensure environment variables are set correctly and service account key exists.

#### 3. Port Already in Use
```
Address already in use
```
**Solution:** Use different ports:
```bash
functions-framework --target=auth_handler --port=8082 --source=handlers/auth_handler.py
```

### Testing Different Auth Actions

#### Basic Auth Actions
- `signup` - User registration
- `signin` - User login
- `signout` - User logout
- `reset_password` - Password reset
- `change_password` - Change password

#### Google OAuth Actions
- `signin` - Google OAuth authentication

### Testing Different Ride Actions
- `request` - Request a ride
- `accept` - Driver accepts ride
- `arriving` - Driver arriving at pickup
- `active` - Ride in progress
- `complete` - Complete ride
- `cancel` - Cancel ride

### Development Workflow
1. Set environment variables
2. Start handler with functions-framework
3. Test with curl or Postman
4. Check logs for debugging
5. Restart handler after code changes 