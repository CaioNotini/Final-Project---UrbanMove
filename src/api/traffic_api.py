import traceback

from fastapi import APIRouter, HTTPException
from src.db.traffic_db import create_traffic_event, read_traffic

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.post("/events")
def traffic_events(events: list[dict]):
    try:
        create_traffic_event(events)
        return {"status": "ok", "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.get("")
def get_traffic():
    try:
        traffic = read_traffic()
        return {"traffic": traffic}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))