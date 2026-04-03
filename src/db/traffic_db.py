from psycopg2.extras import execute_values
from src.db.connection import get_connection


def create_traffic_event(events: list[dict]) -> None:
    if not events:
        return

    conn = get_connection()
    cur = conn.cursor()

    rows = []
    for event in events:
        rows.append((
            event["type"],
            event["segment_id"],
            event["from_node"],
            event["to_node"],
            event["traffic_level"],
            event["traffic_multiplier"],
            event.get("weight"),
            event["timestamp"],
        ))

    execute_values(
        cur,
        """
        INSERT INTO traffic_events (
            event_type,
            segment_id,
            from_node,
            to_node,
            traffic_level,
            traffic_multiplier,
            weight,
            event_timestamp
        )
        VALUES %s
        """,
        rows,
    )

    conn.commit()
    cur.close()
    conn.close()