from fastapi import APIRouter

router = APIRouter()

from .test import test_router
from .auth import auth_router  # Import unified auth router

router.include_router(test_router)
router.include_router(auth_router)  # Include unified auth router

@router.get("/hello")
def say_hello():
    return {"message": "Hello from the router!"}

# --- Firebase test route ---
@router.get("/test-firebase")
def test_firebase():
    try:
        import firebase_admin
        from firebase_admin import firestore
        # Get Firestore client
        db = firestore.client(database_id='chauffeur')
        # Attempt to list collections (should work if connected)
        collections = [col.id for col in db.collections()]
        return {"success": True, "collections": collections}
    except Exception as e:
        return {"success": False, "error": str(e)} 