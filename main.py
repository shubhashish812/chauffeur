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

# 4. Add verification callback endpoint
@app.get("/verify-email")
async def verify_email_callback(mode: str = None, oobCode: str = None):
    """Handle email verification callback from Firebase"""
    if mode == "verifyEmail" and oobCode:
        try:
            from firebase_admin import auth
            # Verify the action code
            email = auth.verify_action_code(oobCode)['data']['email']
            user = auth.get_user_by_email(email)
            
            # Check if email is already verified
            if user.email_verified:
                return HTMLResponse(content="""
                <html>
                <head><title>Email Already Verified</title></head>
                <body>
                    <h1>✅ Email Already Verified</h1>
                    <p>Your email has already been verified. You can close this window.</p>
                    <script>setTimeout(() => window.close(), 3000);</script>
                </body>
                </html>
                """)
            else:
                return HTMLResponse(content="""
                <html>
                <head><title>Email Verification</title></head>
                <body>
                    <h1>✅ Email Verified Successfully!</h1>
                    <p>Your email has been verified. You can close this window and return to the app.</p>
                    <script>setTimeout(() => window.close(), 3000);</script>
                </body>
                </html>
                """)
        except Exception as e:
            return HTMLResponse(content=f"""
            <html>
            <head><title>Verification Error</title></head>
            <body>
                <h1>❌ Verification Failed</h1>
                <p>Error: {str(e)}</p>
                <p>Please try again or contact support.</p>
            </body>
            </html>
            """)
    else:
        return HTMLResponse(content="""
        <html>
        <head><title>Invalid Verification Link</title></head>
        <body>
            <h1>❌ Invalid Verification Link</h1>
            <p>This verification link is invalid or has expired.</p>
        </body>
        </html>
        """)