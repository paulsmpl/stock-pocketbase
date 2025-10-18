from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routes.inventory import router as inventory_router
from app.routes.models import router as models_router
from app.routes.movements import router as movements_router
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Management API",
    description="API de gestion de stock pour chaussures",
    version="1.0.0"
)

# Exception handler global pour capturer toutes les erreurs
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔥 ERREUR NON GÉRÉE sur {request.method} {request.url}")
    logger.error(f"Type: {type(exc).__name__}")
    logger.error(f"Message: {str(exc)}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )

app.include_router(inventory_router)
app.include_router(models_router)
app.include_router(movements_router)

@app.get("/")
def root():
    return {"message": "Stock Management API is running"}