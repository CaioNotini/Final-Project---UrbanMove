from fastapi import APIRouter, HTTPException
import traceback

from pydantic.v1 import BaseModel
from src.db.grid_db import load_graph
from src.simulator.run_sim import serialize_fleet, spawn_buses, spawn_cars
from src.db.vehicle_db import create_vehicle_event, create_vehicle_states, create_vehicles, read_vehicle_state_by_id, read_vehicle_states, read_vehicles, update_vehicle_current_state, create_reroute_event

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


class FleetConfig(BaseModel):
    num_cars: int
    num_buses: int
    algorithm: str = "astar"



################################################   Events   #############################################################################

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



################################################   Reroutes   #############################################################################

@router.post("/reroutes")
def reroute_events(events: list[dict]):
    try:
        create_reroute_event(events)
        return {"status": "ok", "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



################################################   Fleet   #############################################################################

@router.post("/fleet")
def get_or_create_fleet(config: FleetConfig):
    try:
        graph = load_graph()

        cars, buses = read_vehicles(graph, algorithm=config.algorithm)

        missing_cars = max(0, config.num_cars - len(cars))
        missing_buses = max(0, config.num_buses - len(buses))

        if missing_cars == 0 and missing_buses == 0:
            print(f"Loaded {len(cars)} cars and {len(buses)} buses from database")
        else:
            print("Creating fleet")

            new_cars = spawn_cars(
                graph=graph,
                num_cars=missing_cars,
                algorithm=config.algorithm,
                start_index=len(cars),
            )

            new_buses = spawn_buses(
                graph=graph,
                num_buses=missing_buses,
                algorithm=config.algorithm,
                start_index=len(buses),
            )

            if new_cars or new_buses:
                create_vehicles(new_cars + new_buses)
                create_vehicle_states(graph, new_cars + new_buses)

            cars, buses = read_vehicles(graph, algorithm=config.algorithm)

        return serialize_fleet(cars, buses)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    


    ################################################   GET Vehicles   #############################################################################

@router.get("")
def get_vehicles():
    try:
        vehicles = read_vehicle_states()
        return {"vehicles": vehicles}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: str):
    try:
        vehicle = read_vehicle_state_by_id(vehicle_id)

        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        return vehicle

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))