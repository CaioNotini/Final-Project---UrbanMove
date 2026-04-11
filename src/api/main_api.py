from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.vehicles_api import router as vehicles_router
from src.api.traffic_api import router as traffic_router
from src.api.graph_api import router as graph_router
from src.api.analytics_api import router as analytics_router
from src.api.auth_api import router as auth_router

from src.utils.logging_config import setup_logger

# Initialize app
app = FastAPI(title="UrbanMove API")

# Logger
logger = setup_logger("urbanmove-api", "api.log")


# -----------------------------
# Middleware: log all requests
# -----------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request started: %s %s", request.method, request.url.path)

    try:
        response = await call_next(request)

        logger.info(
            "Request finished: %s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response

    except Exception:
        logger.exception(
            "Unhandled error on request: %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


# -----------------------------
# Routers
# -----------------------------
app.include_router(vehicles_router)
app.include_router(traffic_router)
app.include_router(graph_router)
app.include_router(analytics_router)
app.include_router(auth_router)


# -----------------------------
# Health check (important)
# -----------------------------
@app.get("/health")
def health():
    logger.info("Health check called")
    return {"status": "ok"}