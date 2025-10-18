from pocketbase import PocketBase
from app.core.config import settings

def get_pb() -> PocketBase:
    pb = PocketBase(settings.POCKETBASE_URL)
    # auth admin (you can switch to user auth later)
    pb.admins.auth_with_password(settings.POCKETBASE_EMAIL, settings.POCKETBASE_PASSWORD)
    return pb
