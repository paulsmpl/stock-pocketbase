import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://pocketbase:8090")
    POCKETBASE_EMAIL = os.getenv("POCKETBASE_EMAIL", "admin@example.com")
    POCKETBASE_PASSWORD = os.getenv("POCKETBASE_PASSWORD", "admin123")
    API_KEY = os.getenv("API_KEY", "change-me")

settings = Settings()
