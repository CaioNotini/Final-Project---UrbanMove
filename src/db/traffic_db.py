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


def read_traffic():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            segment_id,
            traffic_level,
            traffic_multiplier,
            updated_at
        FROM traffic_events
        ORDER BY updated_at DESC
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    traffic = []

    for r in rows:
        traffic.append({
            "segment_id": r[0],
            "traffic_level": r[1],
            "traffic_multiplier": r[2],
            "updated_at": r[3].isoformat() if r[3] else None,
        })

    return traffic