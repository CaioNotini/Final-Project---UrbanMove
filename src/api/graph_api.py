from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import traceback

from db.grid_db import read_graph, load_graph, create_graph
from simulator.grid import create_city_graph

router = APIRouter(prefix="/graph", tags=["graph"])

class GraphConfig(BaseModel):
    width: int
    height: int
    default_speed: float = 50.0
    bidirectional: bool = True
    force: bool = False


@router.post("")
def get_or_create_graph(config: GraphConfig):
    try:
        if read_graph() and not config.force:
            print("Loading graph from database")
            graph = load_graph()
        else:
            print("Creating graph and saving to database")
            graph = create_city_graph(
                config.width,
                config.height,
                default_speed=config.default_speed,
                bidirectional=config.bidirectional
            )
            create_graph(graph)

        # convert graph to JSON
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

        return {
            "nodes": nodes,
            "edges": edges
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))