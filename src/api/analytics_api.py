from fastapi import APIRouter, HTTPException, Depends
from src.utils.logging_config import setup_logger

from src.api.auth_api import require_admin
from src.db.analytics_db import (
    get_stats_overview,
    get_congestion_hotspots,
    get_average_speed,
)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_admin)],
)

logger = setup_logger("analytics-api", "api.log")


@router.get("/overview")
def analytics_overview():
    logger.info("GET /analytics/overview called")

    try:
        data = get_stats_overview()
        logger.info("GET /analytics/overview success")
        return data

    except Exception:
        logger.exception("GET /analytics/overview failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/congestion-hotspots")
def congestion_hotspots():
    logger.info("GET /analytics/congestion-hotspots called")

    try:
        hotspots = get_congestion_hotspots()
        logger.info("Hotspots found: %d", len(hotspots))
        return {"hotspots": hotspots}

    except Exception:
        logger.exception("GET /analytics/congestion-hotspots failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/avg-speed")
def avg_speed():
    logger.info("GET /analytics/avg-speed called")

    try:
        data = get_average_speed()
        logger.info("GET /analytics/avg-speed success")
        return data

    except Exception:
        logger.exception("GET /analytics/avg-speed failed")
        raise HTTPException(status_code=500, detail="Internal server error")