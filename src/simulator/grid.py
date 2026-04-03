from __future__ import annotations
import pandas as pd

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None


def _index(x: int, y: int, width: int) -> int:
    return y * width + x


def _coords(node: int, width: int) -> tuple[int, int]:
    x = node % width
    y = node // width
    return x, y


def segment_id_canonical(u: int, v: int, width: int) -> str:
    a = _coords(u, width)
    b = _coords(v, width)
    (x1, y1), (x2, y2) = (a, b) if a <= b else (b, a)
    return f"S-{x1}-{y1}-{x2}-{y2}"


def create_city_graph(
    width: int = 10,
    height: int = 10,
    default_speed: float = 50.0,
    bidirectional: bool = True,
) -> "nx.DiGraph":
    if nx is None:
        raise ImportError("networkx is required to create a graph")

    g = nx.DiGraph()

    # nodes with coordinates
    for y in range(height):
        for x in range(width):
            nid = _index(x, y, width)
            g.add_node(nid, x=x, y=y)

    directions = [(1, 0), (0, 1)]  # right and down

    for y in range(height):
        for x in range(width):
            for dx, dy in directions:
                nx_ = x + dx
                ny_ = y + dy

                if nx_ < width and ny_ < height:
                    src = _index(x, y, width)
                    dst = _index(nx_, ny_, width)

                    sid = segment_id_canonical(src, dst, width)

                    length_km = 1.0
                    travel_time_h = length_km / default_speed

                    g.add_edge(
                        src,
                        dst,
                        segment_id=sid,
                        speed_limit_kmh=default_speed,
                        length_km=length_km,
                        base_travel_time_h=travel_time_h,

                        # TRAFFIC FIELDS
                        traffic_level="low",
                        traffic_multiplier=1.0,
                        blocked=False,

                        # dynamic weight (used by routing)
                        weight=travel_time_h,
                    )

                    if bidirectional:
                        g.add_edge(
                            dst,
                            src,
                            segment_id=sid,
                            speed_limit_kmh=default_speed,
                            length_km=length_km,
                            base_travel_time_h=travel_time_h,

                            # TRAFFIC FIELDS
                            traffic_level="low",
                            traffic_multiplier=1.0,
                            blocked=False,

                            weight=travel_time_h,
                        )

    return g


def initialize_traffic_state(graph: "nx.DiGraph") -> None:
    """
    Ensures all edges have traffic fields (useful when loading from DB).
    """
    for _, _, data in graph.edges(data=True):
        if "traffic_level" not in data:
            data["traffic_level"] = "low"

        if "traffic_multiplier" not in data:
            data["traffic_multiplier"] = 1.0

        if "blocked" not in data:
            data["blocked"] = False

        if "base_travel_time_h" not in data:
            data["base_travel_time_h"] = data["weight"]

        # always recompute current weight
        multiplier = data["traffic_multiplier"]
        data["weight"] = data["base_travel_time_h"] / multiplier


def segments_dataframe(graph: "nx.DiGraph") -> "pd.DataFrame":
    rows = []

    for u, v, data in graph.edges(data=True):
        rows.append(
            {
                "segment_id": data.get("segment_id"),
                "from_node": u,
                "to_node": v,

                "from_x": graph.nodes[u].get("x"),
                "from_y": graph.nodes[u].get("y"),
                "to_x": graph.nodes[v].get("x"),
                "to_y": graph.nodes[v].get("y"),

                "speed_limit_kmh": data.get("speed_limit_kmh"),
                "length_km": data.get("length_km"),
                "base_travel_time_h": data.get("base_travel_time_h"),

                # TRAFFIC INFO
                "traffic_level": data.get("traffic_level"),
                "traffic_multiplier": data.get("traffic_multiplier"),
                "blocked": data.get("blocked"),

                # CURRENT COST USED BY ROUTING
                "weight": data.get("weight"),
            }
        )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    g = create_city_graph()

    initialize_traffic_state(g)

    df = segments_dataframe(g)

    print(df.head())
    print(f"Grid with {len(g.nodes())} nodes and {len(g.edges())} edges")