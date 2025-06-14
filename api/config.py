from dotenv import load_dotenv
import os

load_dotenv()

class ApplicationConfig:
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SAMESITE = "None"  # Use "None" only for HTTPS with Secure=True
    SESSION_COOKIE_SECURE = False  # Set to True only on HTTPS
    SECRET_KEY = os.environ["SECRET_KEY"]
