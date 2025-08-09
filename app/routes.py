from fastapi import APIRouter

router = APIRouter()

from .auth import main_router
router.include_router(main_router)

@router.get("/hello")
def say_hello():
    return {"message": "Hello from the router!"}

# --- Firebase test route ---
@router.get("/test-firebase")
def test_firebase():
    try:
        import firebase_admin
        from firebase_admin import firestore
        db = firestore.client(database_id='chauffeur')
        collections = [col.id for col in db.collections()]
        return {"success": True, "collections": collections}
    except Exception as e:
        return {"success": False, "error": str(e)} 