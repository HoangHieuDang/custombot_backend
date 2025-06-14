from dotenv import load_dotenv
import os
import redis

load_dotenv()

class ApplicationConfig:
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SAMESITE = "Lax"  # or "None" if using HTTPS
    SESSION_COOKIE_SECURE = False  # True if using HTTPS
    SECRET_KEY = "your_secret_key"
