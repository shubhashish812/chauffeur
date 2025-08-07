from fastapi import APIRouter

test_router = APIRouter()

@test_router.get("/test/ping")
def ping():
    return {"status": "ok", "message": "pong"}
