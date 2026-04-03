from fastapi import APIRouter, HTTPException
import traceback
from src.db.vehicle_db import create_vehicle_event, update_vehicle_current_state, create_reroute_event

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("/events")
def vehicle_events(events: list[dict]):
    try:
        create_vehicle_event(events)

        for i, event in enumerate(events):
            print(f"[STATE] updating {i} - {event.get('vehicle_id')}")
            update_vehicle_current_state(event)

        return {"status": "ok", "count": len(events)}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reroutes")
def reroute_events(events: list[dict]):
    try:
        create_reroute_event(events)
        return {"status": "ok", "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))