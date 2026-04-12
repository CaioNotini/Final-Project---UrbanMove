import traceback

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.db.vehicle_db import read_bus_lines, read_vehicle_states
from src.utils.logging_config import setup_logger

from src.db.grid_db import read_graph, load_graph, create_graph
from src.simulator.grid import create_city_graph

router = APIRouter(prefix="/graph", tags=["graph"])
logger = setup_logger("graph-api", "api.log")


class GraphConfig(BaseModel):
    width: int
    height: int
    default_speed: float = 50.0
    bidirectional: bool = True
    force: bool = False


@router.post("")
def get_or_create_graph(config: GraphConfig):
    logger.info("POST /graph called")

    try:
        if read_graph() and not config.force:
            logger.info("Loading graph from database")
            graph = load_graph()
        else:
            logger.info("Creating graph and saving to database")
            graph = create_city_graph(
                config.width,
                config.height,
                default_speed=config.default_speed,
                bidirectional=config.bidirectional
            )
            create_graph(graph)

        nodes = [
            {"id": n, "x": data["x"], "y": data["y"]}
            for n, data in graph.nodes(data=True)
        ]

        edges = [
            {
                "from_node": u,
                "to_node": v,
                "segment_id": data.get("segment_id"),
                "weight": data.get("weight"),
                "length_km": data.get("length_km"),
                "speed_limit_kmh": data.get("speed_limit_kmh"),
                "traffic_level": data.get("traffic_level"),
                "traffic_multiplier": data.get("traffic_multiplier"),
                "base_travel_time_h": data.get("base_travel_time_h"),
            }
            for u, v, data in graph.edges(data=True)
        ]

        logger.info("Graph returned | nodes=%d | edges=%d", len(nodes), len(edges))

        return {
            "nodes": nodes,
            "edges": edges
        }

    except Exception:
        logger.exception("POST /graph failed")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/state")
def get_graph_state():
    try:
        if not read_graph():
            raise HTTPException(status_code=404, detail="Graph not found")

        graph = load_graph()

        nodes = []
        for node_id, data in graph.nodes(data=True):
            nodes.append({
                "node_id": node_id,
                "x": data.get("x"),
                "y": data.get("y"),
            })

        edges = []
        for u, v, data in graph.edges(data=True):
            edges.append({
                "from_node": u,
                "to_node": v,
                "segment_id": data.get("segment_id"),
                "traffic_level": data.get("traffic_level", "low"),
                "weight": data.get("weight"),
            })

        vehicle_states = read_vehicle_states() or []
        vehicles = []
        for item in vehicle_states:
            vehicles.append({
                "vehicle_id": item.get("vehicle_id"),
                "vehicle_type": item.get("vehicle_type"),
                "x": item.get("x"),
                "y": item.get("y"),
                "current_node": item.get("current_node"),
                "status": item.get("status"),
                "line_id": item.get("line_id"),
            })

        bus_lines = read_bus_lines() or []

        return {
            "nodes": nodes,
            "edges": edges,
            "vehicles": vehicles,
            "bus_lines": bus_lines,
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))