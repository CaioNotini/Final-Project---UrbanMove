from src.db.connection import get_connection


def get_stats_overview():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM vehicles")
    total_vehicles = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicles WHERE vehicle_type = 'car'")
    total_cars = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicles WHERE vehicle_type = 'bus'")
    total_buses = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicle_current_state WHERE status = 'moving'")
    moving_vehicles = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicle_current_state WHERE status = 'parked'")
    parked_vehicles = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicle_current_state WHERE status = 'arrived'")
    arrived_vehicles = cur.fetchone()[0]

    cur.execute("""
        SELECT AVG(speed_kmh)
        FROM vehicle_current_state
        WHERE speed_kmh IS NOT NULL
    """)
    avg_speed = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "total_vehicles": total_vehicles,
        "total_cars": total_cars,
        "total_buses": total_buses,
        "moving_vehicles": moving_vehicles,
        "parked_vehicles": parked_vehicles,
        "arrived_vehicles": arrived_vehicles,
        "avg_speed_kmh": float(avg_speed) if avg_speed is not None else 0.0,
    }


def get_average_speed():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT AVG(speed_kmh)
        FROM vehicle_current_state
        WHERE speed_kmh IS NOT NULL
    """)
    avg_speed = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "avg_speed_kmh": float(avg_speed) if avg_speed is not None else 0.0
    }


def get_congestion_hotspots(limit: int = 10):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            segment_id,
            traffic_level,
            traffic_multiplier,
            weight,
            event_timestamp
        FROM traffic_events
        WHERE traffic_level = 'high'
        ORDER BY event_timestamp DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    hotspots = []
    for row in rows:
        hotspots.append({
            "segment_id": row[0],
            "traffic_level": row[1],
            "traffic_multiplier": row[2],
            "weight": row[3],
            "event_timestamp": row[4].isoformat() if row[4] else None,
        })

    return hotspots