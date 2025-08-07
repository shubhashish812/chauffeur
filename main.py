# 1. Add these new imports
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from firebase_config import init_firebase
from google_oauth_config import init_google_oauth
from fastapi import FastAPI
from app.routes import router
from fastapi.middleware.cors import CORSMiddleware

init_firebase()
init_google_oauth()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Mount the static directory to serve files like CSS, JS, etc.
# The path "/static" means that files in the "static" directory
# will be accessible at http://localhost:8000/static/...
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)

# 3. Update the root endpoint to serve your HTML file
@app.get("/home", response_class=HTMLResponse)
async def get_root():
    with open(os.path.join('static', 'index.html'), encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)