from fastapi import APIRouter, HTTPException, Depends
from src.utils.logging_config import setup_logger

from src.api.auth_api import get_current_user, require_admin
from src.db.traffic_db import create_traffic_event, read_traffic

router = APIRouter(prefix="/traffic", tags=["traffic"])

logger = setup_logger("traffic-api", "api.log")


@router.post("/events")
def traffic_events(events: list[dict], current_user=Depends(require_admin)):
    logger.info("POST /traffic/events called | events=%d", len(events))

    try:
        create_traffic_event(events)
        logger.info("Traffic events stored successfully")
        return {"status": "ok", "count": len(events)}

    except Exception:
        logger.exception("POST /traffic/events failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("")
def get_traffic(current_user=Depends(get_current_user)):
    logger.info("GET /traffic called")

    try:
        traffic = read_traffic()
        logger.info("GET /traffic success | records=%d", len(traffic))
        return {"traffic": traffic}

    except Exception:
        logger.exception("GET /traffic failed")
        raise HTTPException(status_code=500, detail="Internal server error")