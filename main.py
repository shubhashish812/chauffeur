from firebase_config import init_firebase
from fastapi import FastAPI
from app.routes import router

init_firebase()

app = FastAPI()

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI app!"} 