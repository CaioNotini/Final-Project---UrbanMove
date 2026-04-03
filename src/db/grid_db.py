import networkx as nx
from src.db.connection import get_connection
from src.simulator.grid import segments_dataframe


def create_graph(graph: nx.DiGraph):
    df = segments_dataframe(graph)

    conn = get_connection()
    cur = conn.cursor()

    insert_query = """
    INSERT INTO road_segments (
        segment_id,
        from_node,
        to_node,
        from_x,
        from_y,
        to_x,
        to_y,
        speed_limit_kmh,
        length_km,
        base_travel_time_h
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    for _, row in df.iterrows():
        cur.execute(
            insert_query,
            (
                row["segment_id"],
                row["from_node"],
                row["to_node"],
                row["from_x"],
                row["from_y"],
                row["to_x"],
                row["to_y"],
                row["speed_limit_kmh"],
                row["length_km"],
                row["base_travel_time_h"],
            ),
        )

    conn.commit()
    cur.close()
    conn.close()


def read_graph():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM road_segments")
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count > 0


def load_graph():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            segment_id,
            from_node,
            to_node,
            from_x,
            from_y,
            to_x,
            to_y,
            speed_limit_kmh,
            length_km,
            base_travel_time_h,
            created_at
        FROM road_segments
    """)

    rows = cur.fetchall()

    graph = nx.DiGraph()

    for row in rows:
        (
            _id,
            segment_id,
            from_node,
            to_node,
            from_x,
            from_y,
            to_x,
            to_y,
            speed_limit_kmh,
            length_km,
            base_travel_time_h,
            created_at,
        ) = row

        graph.add_node(from_node, x=from_x, y=from_y)
        graph.add_node(to_node, x=to_x, y=to_y)

        graph.add_edge(
            from_node,
            to_node,
            segment_id=segment_id,
            speed_limit_kmh=speed_limit_kmh,
            length_km=length_km,
            base_travel_time_h=base_travel_time_h,
            traffic_level="low",
            traffic_multiplier=1.0,
            blocked=False,
            weight=base_travel_time_h,
        )

    cur.close()
    conn.close()

    return graph