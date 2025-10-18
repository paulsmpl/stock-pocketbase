from fastapi import FastAPI
from app.routes.inventory import router as inventory_router
from app.routes.models import router as models_router
from app.routes.movements import router as movements_router

app = FastAPI(title="Stock Assistant API", version="1.0.0")

app.include_router(inventory_router)
app.include_router(models_router)
app.include_router(movements_router)
