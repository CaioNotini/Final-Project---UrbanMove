from fastapi import APIRouter, HTTPException, Depends
from src.utils.logging_config import setup_logger

from pydantic import BaseModel
from src.api.auth_api import get_current_user, require_admin
from src.db.grid_db import load_graph
from src.simulator.run_sim import serialize_fleet, spawn_buses, spawn_cars
from src.db.vehicle_db import (
    create_vehicle_event,
    create_vehicle_states,
    create_vehicles,
    read_bus_lines,
    read_vehicle_state_by_id,
    read_vehicle_states,
    read_vehicles,
    update_vehicle_current_state,
    create_reroute_event,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])
logger = setup_logger("vehicles-api", "api.log")


class FleetConfig(BaseModel):
    num_cars: int
    num_buses: int
    algorithm: str = "astar"


# ---------------- EVENTS ----------------
@router.post("/events")
def vehicle_events(events: list[dict], current_user=Depends(require_admin)):
    logger.info("POST /vehicles/events | events=%d", len(events))

    try:
        create_vehicle_event(events)

        for event in events:
            update_vehicle_current_state(event)

        logger.info("Vehicle events processed successfully")
        return {"status": "ok", "count": len(events)}

    except Exception:
        logger.exception("POST /vehicles/events failed")
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------- REROUTES ----------------
@router.post("/reroutes")
def reroute_events(events: list[dict], current_user=Depends(require_admin)):
    logger.info("POST /vehicles/reroutes | events=%d", len(events))

    try:
        create_reroute_event(events)
        logger.info("Reroute events stored successfully")
        return {"status": "ok", "count": len(events)}

    except Exception:
        logger.exception("POST /vehicles/reroutes failed")
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------- FLEET ----------------
@router.post("/fleet")
def get_or_create_fleet(config: FleetConfig, current_user=Depends(require_admin)):
    logger.info("POST /vehicles/fleet called")

    try:
        graph = load_graph()
        cars, buses = read_vehicles(graph, algorithm=config.algorithm)

        logger.info("Loaded fleet | cars=%d | buses=%d", len(cars), len(buses))

        missing_cars = max(0, config.num_cars - len(cars))
        missing_buses = max(0, config.num_buses - len(buses))

        if missing_cars > 0 or missing_buses > 0:
            logger.info("Creating missing vehicles")

            new_cars = spawn_cars(graph, missing_cars, config.algorithm, len(cars))
            new_buses = spawn_buses(graph, missing_buses, config.algorithm, len(buses))

            if new_cars or new_buses:
                create_vehicles(new_cars + new_buses)
                create_vehicle_states(graph, new_cars + new_buses)

            cars, buses = read_vehicles(graph, algorithm=config.algorithm)

        return serialize_fleet(cars, buses)

    except Exception:
        logger.exception("POST /vehicles/fleet failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/bus-lines")
def get_bus_lines(current_user=Depends(get_current_user)):
    logger.info("GET /vehicles/bus-lines called")

    try:
        lines = read_bus_lines()

        if not lines:
            logger.warning("No bus lines found")

        return {"bus_lines": lines}

    except Exception:
        logger.exception("GET /vehicles/bus-lines failed")
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------- GET VEHICLES ----------------
@router.get("")
def get_vehicles(current_user=Depends(get_current_user)):
    logger.info("GET /vehicles called")

    try:
        vehicles = read_vehicle_states()
        logger.info("Returned %d vehicles", len(vehicles))
        return {"vehicles": vehicles}

    except Exception:
        logger.exception("GET /vehicles failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: str, current_user=Depends(get_current_user)):
    logger.info("GET /vehicles/%s called", vehicle_id)

    try:
        vehicle = read_vehicle_state_by_id(vehicle_id)

        if not vehicle:
            logger.warning("Vehicle not found: %s", vehicle_id)
            raise HTTPException(status_code=404, detail="Vehicle not found")

        return vehicle

    except HTTPException:
        raise
    except Exception:
        logger.exception("GET /vehicles/%s failed", vehicle_id)
        raise HTTPException(status_code=500, detail="Internal server error")