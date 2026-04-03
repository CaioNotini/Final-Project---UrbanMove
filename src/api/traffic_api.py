from fastapi import APIRouter, HTTPException
from src.db.traffic_db import create_traffic_event

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.post("/events")
def traffic_events(events: list[dict]):
    try:
        create_traffic_event(events)
        return {"status": "ok", "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
def get_traffic_events():
    return {"message": "not implemented yet"}