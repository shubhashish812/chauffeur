from firebase_config import init_firebase
from google_oauth_config import init_google_oauth
from fastapi import FastAPI
from app.routes import router

init_firebase()
init_google_oauth()

app = FastAPI()

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI app!"} 