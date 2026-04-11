from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.utils.logging_config import setup_logger

from src.api.auth_api import require_admin
from src.db.grid_db import read_graph, load_graph, create_graph
from src.simulator.grid import create_city_graph

router = APIRouter(
    prefix="/graph",
    tags=["graph"],
    dependencies=[Depends(require_admin)]
)

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
            logger.info("Creating new graph")
            graph = create_city_graph(
                config.width,
                config.height,
                default_speed=config.default_speed,
                bidirectional=config.bidirectional
            )
            create_graph(graph)

        nodes = [{"id": n, "x": d["x"], "y": d["y"]} for n, d in graph.nodes(data=True)]
        edges = [{"from_node": u, "to_node": v} for u, v in graph.edges()]

        logger.info("Graph returned | nodes=%d | edges=%d", len(nodes), len(edges))

        return {"nodes": nodes, "edges": edges}

    except Exception:
        logger.exception("POST /graph failed")
        raise HTTPException(status_code=500, detail="Internal server error")