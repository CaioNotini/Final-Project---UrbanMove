from fastapi import FastAPI
from src.api.vehicles_api import router as vehicles_router
from src.api.traffic_api import router as traffic_router
from src.api.graph_api import router as graph_router
from src.api.analytics_api import router as analytics_router

app = FastAPI(title="UrbanMove API")

app.include_router(vehicles_router)
app.include_router(traffic_router)
app.include_router(graph_router)
app.include_router(analytics_router)

@app.get("/health")
def health():
    return {"status": "ok"}