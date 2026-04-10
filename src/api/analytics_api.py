from fastapi import APIRouter, HTTPException, Depends
import traceback

from src.api.auth_api import require_admin
from src.db.analytics_db import get_stats_overview, get_congestion_hotspots, get_average_speed


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_admin)]
)


@router.get("/overview")
def analytics_overview():
    try:
        return get_stats_overview()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/congestion-hotspots")
def congestion_hotspots():
    try:
        return {"hotspots": get_congestion_hotspots()}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/avg-speed")
def avg_speed():
    try:
        return get_average_speed()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))