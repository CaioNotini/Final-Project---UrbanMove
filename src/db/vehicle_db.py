import json
from typing import List
from src.db.connection import get_connection
from src.simulator.vehicle import Car, Bus
from src.simulator.run_sim import utc_now_iso
from typing import List, Tuple
import networkx as nx
from psycopg2.extras import Json, execute_values

from src.db.connection import get_connection
from src.simulator.vehicle import Car, Bus
from src.simulator.run_sim import best_path

def create_vehicles(vehicles: List[Car | Bus]) -> None:
    conn = get_connection()
    cur = conn.cursor()

    try:
        insert_query = """
        INSERT INTO vehicles (
            vehicle_id, vehicle_type, line_id, created_at
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (vehicle_id) DO NOTHING
        """

        for v in vehicles:
            line_id = v.line_id if isinstance(v, Bus) else None
            cur.execute(
                insert_query,
                (
                    v.vehicle_id,
                    v.vehicle_type,
                    line_id,
                    utc_now_iso(),
                ),
            )

        conn.commit()

    finally:
        cur.close()
        conn.close()


def read_vehicles(graph: nx.DiGraph, algorithm: str = "astar") -> Tuple[List[Car], List[Bus]]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            v.vehicle_id,
            v.vehicle_type,
            v.line_id,
            s.current_node,
            s.speed_kmh,
            s.status,
            s.destination_node,
            s.current_target_stop,
            s.route_stops,
            s.current_stop_index,
            s.direction,
            s.segment_id
        FROM vehicles v
        JOIN vehicle_current_state s
            ON v.vehicle_id = s.vehicle_id
    """)

    rows = cur.fetchall()

    cars: List[Car] = []
    buses: List[Bus] = []

    for row in rows:
        (
            vehicle_id,
            vehicle_type,
            line_id,
            current_node,
            speed_kmh,
            status,
            destination_node,
            current_target_stop,
            route_stops,
            current_stop_index,
            direction,
            segment_id,
        ) = row

        if vehicle_type == "car":
            if destination_node is None:
                raise ValueError(f"Car {vehicle_id} has no destination_node in vehicle_current_state")

            path = best_path(graph, current_node, destination_node, algorithm)

            car = Car(
                vehicle_id=vehicle_id,
                current_node=current_node,
                destination_node=destination_node,
                path_nodes=path,
                speed_kmh=speed_kmh,
                status=status,
                vehicle_type="car",
            )

            car.current_segment_id = segment_id

            # Como o carro já pode estar no meio do caminho, ajustamos o path_index
            try:
                car.path_index = path.index(current_node)
            except ValueError:
                car.path_index = 0

            cars.append(car)

        elif vehicle_type == "bus":
            if route_stops is None:
                raise ValueError(f"Bus {vehicle_id} has no route_stops in vehicle_current_state")
            if current_stop_index is None:
                raise ValueError(f"Bus {vehicle_id} has no current_stop_index in vehicle_current_state")
            if direction is None:
                raise ValueError(f"Bus {vehicle_id} has no direction in vehicle_current_state")

            # Se current_target_stop não vier preenchido, recalcula a partir do índice
            if current_target_stop is None:
                current_target_stop = route_stops[current_stop_index]

            path = best_path(graph, current_node, current_target_stop, algorithm)

            bus = Bus(
                vehicle_id=vehicle_id,
                current_node=current_node,
                path_nodes=path,
                path_index=0,
                speed_kmh=speed_kmh,
                current_segment_id=segment_id,
                status=status,
                route_stops=route_stops,
                current_stop_index=current_stop_index,
                line_id=line_id,
                direction=direction,
                vehicle_type="bus",
            )

            try:
                bus.path_index = path.index(current_node)
            except ValueError:
                bus.path_index = 0

            buses.append(bus)

        else:
            raise ValueError(f"Unknown vehicle_type '{vehicle_type}' for vehicle {vehicle_id}")

    cur.close()
    conn.close()

    return cars, buses   

def read_vehicle_states():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            v.vehicle_id,
            v.vehicle_type,
            v.line_id,
            s.current_node,
            s.segment_id,
            s.destination_node,
            s.status,
            s.x,
            s.y,
            s.speed_kmh,
            s.current_target_stop,
            s.route_stops,
            s.current_stop_index,
            s.direction,
            s.updated_at
        FROM vehicles v
        JOIN vehicle_current_state s
            ON v.vehicle_id = s.vehicle_id
        ORDER BY v.vehicle_id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    vehicles = []

    for r in rows:
        vehicles.append({
            "vehicle_id": r[0],
            "vehicle_type": r[1],
            "line_id": r[2],
            "current_node": r[3],
            "segment_id": r[4],
            "destination_node": r[5],
            "status": r[6],
            "x": r[7],
            "y": r[8],
            "speed_kmh": r[9],
            "current_target_stop": r[10],
            "route_stops": r[11],
            "current_stop_index": r[12],
            "direction": r[13],
            "updated_at": r[14].isoformat() if r[14] else None,
        })

    return vehicles

def read_vehicle_state_by_id(vehicle_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            v.vehicle_id,
            v.vehicle_type,
            v.line_id,
            s.current_node,
            s.segment_id,
            s.destination_node,
            s.status,
            s.x,
            s.y,
            s.speed_kmh,
            s.current_target_stop,
            s.route_stops,
            s.current_stop_index,
            s.direction,
            s.updated_at
        FROM vehicles v
        JOIN vehicle_current_state s
            ON v.vehicle_id = s.vehicle_id
        WHERE v.vehicle_id = %s
    """, (vehicle_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "vehicle_id": row[0],
        "vehicle_type": row[1],
        "line_id": row[2],
        "current_node": row[3],
        "segment_id": row[4],
        "destination_node": row[5],
        "status": row[6],
        "x": row[7],
        "y": row[8],
        "speed_kmh": row[9],
        "current_target_stop": row[10],
        "route_stops": row[11],
        "current_stop_index": row[12],
        "direction": row[13],
        "updated_at": row[14].isoformat() if row[14] else None,
    }


#################################################################################################################

def create_vehicle_event(events):
    if not events:
        return

    conn = get_connection()
    cur = conn.cursor()

    rows = []
    for event in events:
        rows.append((
            event.get("type"),
            event.get("vehicle_id"),
            event.get("timestamp"),
            event.get("x"),
            event.get("y"),
            event.get("speed_kmh"),
            event.get("current_node"),
            event.get("segment_id"),
            event.get("destination_node"),
            event.get("status"),
            event.get("current_target_stop"),
            json.dumps(event.get("route_stops")) if event.get("route_stops") is not None else None,
        ))

    execute_values(
        cur,
        """
        INSERT INTO vehicle_events (
            event_type,
            vehicle_id,
            event_timestamp,
            x,
            y,
            speed_kmh,
            current_node,
            segment_id,
            destination_node,
            status,
            current_target_stop,
            route_stops
        )
        VALUES %s
        """,
        rows
    )

    conn.commit()
    cur.close()
    conn.close()




#################################################################################################################
def create_vehicle_states(graph: nx.DiGraph, vehicles: List[Car | Bus]) -> None:
    conn = get_connection()
    cur = conn.cursor()

    try:
        insert_query = """
        INSERT INTO vehicle_current_state (
            vehicle_id,
            last_timestamp,
            x,
            y,
            speed_kmh,
            current_node,
            segment_id,
            destination_node,
            status,
            current_target_stop,
            route_stops,
            updated_at,
            direction,
            current_stop_index
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (vehicle_id) DO NOTHING
        """

        now = utc_now_iso()

        for v in vehicles:
            x = graph.nodes[v.current_node]["x"]
            y = graph.nodes[v.current_node]["y"]

            destination_node = v.destination_node if isinstance(v, Car) else None
            current_target_stop = v.current_target_stop() if isinstance(v, Bus) else None
            route_stops = json.dumps(v.route_stops) if isinstance(v, Bus) else None
            current_stop_index = v.current_stop_index if isinstance(v, Bus) else None
            direction = v.direction if isinstance(v, Bus) else None

            cur.execute(
                insert_query,
                (
                    v.vehicle_id,
                    now,
                    x,
                    y,
                    v.speed_kmh,
                    v.current_node,
                    getattr(v, "current_segment_id", None),
                    destination_node,
                    v.status,
                    current_target_stop,
                    route_stops,
                    now,
                    direction,
                    current_stop_index,
                ),
            )

        conn.commit()

    finally:
        cur.close()
        conn.close()



def update_vehicle_current_state(event: dict) -> None:
    conn = get_connection()
    cur = conn.cursor()

    upsert_query = """
    INSERT INTO vehicle_current_state (
        vehicle_id,
        last_timestamp,
        x,
        y,
        speed_kmh,
        current_node,
        segment_id,
        destination_node,
        status,
        current_target_stop,
        route_stops,
        updated_at,
        direction,
        current_stop_index
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (vehicle_id)
    DO UPDATE SET
        last_timestamp = EXCLUDED.last_timestamp,
        x = EXCLUDED.x,
        y = EXCLUDED.y,
        speed_kmh = EXCLUDED.speed_kmh,
        current_node = EXCLUDED.current_node,
        segment_id = EXCLUDED.segment_id,
        destination_node = EXCLUDED.destination_node,
        status = EXCLUDED.status,
        current_target_stop = EXCLUDED.current_target_stop,
        route_stops = EXCLUDED.route_stops,
        updated_at = EXCLUDED.updated_at,
        direction = EXCLUDED.direction,
        current_stop_index = EXCLUDED.current_stop_index
    """

    route_stops = event.get("route_stops")
    if route_stops is not None:
        route_stops = Json(route_stops)


    cur.execute(
        upsert_query,
        (
            event["vehicle_id"],
            event["timestamp"],
            event.get("x"),
            event.get("y"),
            event.get("speed_kmh"),
            event.get("current_node"),
            event.get("segment_id"),
            event.get("destination_node"),
            event.get("status"),
            event.get("current_target_stop"),
            route_stops,
            utc_now_iso(),
            event.get("direction"),
            event.get("current_stop_index"),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()



#################################################################################################################
def create_reroute_event(events: list[dict]):
    if not events:
        return

    conn = get_connection()
    cur = conn.cursor()

    rows = []
    for event in events:
        rows.append((
            event["vehicle_id"],
            event["timestamp"],
            event.get("reason"),
            json.dumps(event.get("old_path")) if event.get("old_path") else None,
            json.dumps(event.get("new_path")) if event.get("new_path") else None,
            event.get("old_cost"),
            event.get("new_cost"),
        ))

    execute_values(
        cur,
        """
        INSERT INTO reroute_events (
            vehicle_id,
            event_timestamp,
            reason,
            old_path,
            new_path,
            old_cost,
            new_cost
        )
        VALUES %s
        """,
        rows
    )

    conn.commit()
    cur.close()
    conn.close()


