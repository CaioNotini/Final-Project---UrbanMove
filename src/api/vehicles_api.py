from fastapi import APIRouter, HTTPException, Depends
import traceback

from pydantic import BaseModel
from src.api.auth_api import get_current_user, require_admin
from src.db.grid_db import load_graph
from src.db.grid_db import load_graph, read_graph
from pydantic import BaseModel
import networkx as nx
from fastapi import HTTPException
import traceback
from src.simulator.run_sim import serialize_fleet, spawn_buses, spawn_cars
from src.db.vehicle_db import (create_vehicle_event,create_vehicle_states,create_vehicles, read_bus_lines, read_vehicle_state_by_id, read_vehicle_states, read_vehicles, update_vehicle_current_state, create_reroute_event,)
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
    
@router.get("/bus-lines")
def get_bus_lines(current_user=Depends(get_current_user)):
    try:
        lines = read_bus_lines()
        return {"bus_lines": lines}
    except Exception as e:
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
    

    ################################################   POST Routes   #############################################################################

class RouteRequest(BaseModel):
    start_point: int
    end_point: int
    algorithm: str = "astar"

@router.post("/recommend")
def recommend_route(payload: RouteRequest):
    try:
        if not read_graph():
            raise HTTPException(status_code=404, detail="Graph not found")

        graph = load_graph()

        if payload.start_point not in graph.nodes:
            raise HTTPException(status_code=404, detail="Start point not found")

        if payload.end_point not in graph.nodes:
            raise HTTPException(status_code=404, detail="End point not found")

        if payload.algorithm == "astar":
            path_nodes = nx.astar_path(
                graph,
                payload.start_point,
                payload.end_point,
                heuristic=lambda a, b: abs(graph.nodes[a]["x"] - graph.nodes[b]["x"]) + abs(graph.nodes[a]["y"] - graph.nodes[b]["y"]),
                weight="weight"
            )
        elif payload.algorithm == "dijkstra":
            path_nodes = nx.dijkstra_path(
                graph,
                payload.start_point,
                payload.end_point,
                weight="weight"
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid algorithm")

        total_weight = nx.path_weight(graph, path_nodes, weight="weight")
        estimated_time_min = round(total_weight * 60, 2)

        return {
            "start_point": payload.start_point,
            "end_point": payload.end_point,
            "path": path_nodes,
            "total_weight": total_weight,
            "estimated_time_min": estimated_time_min
        }

    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path found")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))