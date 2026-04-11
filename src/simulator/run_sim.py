from __future__ import annotations

import random
import math
from datetime import datetime, timezone
from typing import List

import networkx as nx

from src.simulator.vehicle import Car, Bus
from src.utils.logging_config import setup_logger

logger = setup_logger("urbanmove-simulator-core", "simulator.log")

T_LOW = 0.7
T_MEDIUM = 0.4
T_HIGH = 0.1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def manhattan_distance(graph: nx.DiGraph, u: int, v: int) -> float:
    x1, y1 = graph.nodes[u]["x"], graph.nodes[u]["y"]
    x2, y2 = graph.nodes[v]["x"], graph.nodes[v]["y"]
    return abs(x1 - x2) + abs(y1 - y2)


def best_path(graph: nx.DiGraph, start: int, end: int, alg: str = "astar") -> List[int]:
    logger.info("Computing path with %s from %s to %s", alg, start, end)

    try:
        if alg == "astar":
            path = nx.astar_path(
                graph,
                start,
                end,
                heuristic=lambda u, v: manhattan_distance(graph, u, v),
                weight="weight",
            )
        elif alg == "dijkstra":
            path = nx.dijkstra_path(graph, start, end, weight="weight")
        else:
            raise ValueError(f"Unknown algorithm: {alg}")

        logger.info(
            "Path computed successfully from %s to %s with %d nodes",
            start,
            end,
            len(path),
        )
        return path

    except Exception:
        logger.exception("Failed to compute path from %s to %s using %s", start, end, alg)
        raise


################################################   Spawning Vehicles   #############################################################################


def spawn_cars(
    graph: nx.DiGraph,
    num_cars: int,
    algorithm: str = "astar",
    start_index: int = 0,
) -> List[Car]:
    nodes = list(graph.nodes())
    cars: List[Car] = []

    logger.info("Spawning %d cars starting at index %d", num_cars, start_index)

    for i in range(start_index, start_index + num_cars):
        try:
            start = random.choice(nodes)
            end = random.choice(nodes)

            while end == start:
                end = random.choice(nodes)

            path = best_path(graph, start, end, algorithm)

            car = Car(
                vehicle_id=f"car-{i:04d}",
                current_node=start,
                destination_node=end,
                path_nodes=path,
                speed_kmh=random.uniform(20.0, 50.0),
                status="stopped",
                vehicle_type="car",
            )

            cars.append(car)

            logger.info(
                "Spawned car %s | start=%s | destination=%s | path_len=%d | speed=%.2f",
                car.vehicle_id,
                start,
                end,
                len(path),
                car.speed_kmh,
            )

        except Exception:
            logger.exception("Failed to spawn car index %d", i)
            raise

    return cars


def spawn_buses(
    graph: nx.DiGraph,
    num_buses: int,
    algorithm: str = "astar",
    start_index: int = 0,
) -> List[Bus]:
    buses: List[Bus] = []
    nodes = list(graph.nodes())

    logger.info("Spawning %d buses starting at index %d", num_buses, start_index)

    for i in range(start_index, start_index + num_buses):
        try:
            num_stops = random.randint(4, 6)
            stops = random.sample(nodes, k=min(num_stops, len(nodes)))

            if len(stops) < 2:
                raise ValueError("A bus route must have at least 2 stops")

            start_node = stops[0]
            first_target_stop = stops[1]

            path = best_path(graph, start_node, first_target_stop, alg=algorithm)

            bus = Bus(
                vehicle_id=f"bus-{i:04d}",
                current_node=start_node,
                path_nodes=path,
                path_index=0,
                speed_kmh=25.0,
                current_segment_id=None,
                status="stopped",
                route_stops=stops,
                current_stop_index=1,
                line_id=f"L{i:02d}",
                direction=1,
                vehicle_type="bus",
            )

            buses.append(bus)

            logger.info(
                "Spawned bus %s | line=%s | start=%s | first_target=%s | stops=%s",
                bus.vehicle_id,
                bus.line_id,
                start_node,
                first_target_stop,
                stops,
            )

        except Exception:
            logger.exception("Failed to spawn bus index %d", i)
            raise

    return buses


def serialize_vehicle(v):
    base = {
        "vehicle_id": v.vehicle_id,
        "current_node": v.current_node,
        "path_nodes": v.path_nodes,
        "path_index": v.path_index,
        "speed_kmh": v.speed_kmh,
        "current_segment_id": v.current_segment_id,
        "status": v.status,
        "vehicle_type": v.vehicle_type,
        "remaining_ticks": v.remaining_ticks,
        "next_node": v.next_node,
    }

    if v.vehicle_type == "car":
        base.update(
            {
                "destination_node": v.destination_node,
                "parked_tickets": v.parked_tickets,
            }
        )

    elif v.vehicle_type == "bus":
        base.update(
            {
                "route_stops": v.route_stops,
                "current_stop_index": v.current_stop_index,
                "line_id": v.line_id,
                "direction": v.direction,
            }
        )

    return base


def serialize_fleet(cars, buses):
    logger.info("Serializing fleet | cars=%d | buses=%d", len(cars), len(buses))
    return {
        "cars": [serialize_vehicle(c) for c in cars],
        "buses": [serialize_vehicle(b) for b in buses],
    }


def parse_fleet(data):
    cars = []
    buses = []

    logger.info("Parsing fleet data")

    try:
        for c in data["cars"]:
            cars.append(
                Car(
                    vehicle_id=c["vehicle_id"],
                    current_node=c["current_node"],
                    path_nodes=c["path_nodes"],
                    path_index=c["path_index"],
                    speed_kmh=c["speed_kmh"],
                    current_segment_id=c["current_segment_id"],
                    status=c["status"],
                    remaining_ticks=c["remaining_ticks"],
                    next_node=c["next_node"],
                    destination_node=c["destination_node"],
                    parked_tickets=c["parked_tickets"],
                )
            )

        for b in data["buses"]:
            buses.append(
                Bus(
                    vehicle_id=b["vehicle_id"],
                    current_node=b["current_node"],
                    path_nodes=b["path_nodes"],
                    path_index=b["path_index"],
                    speed_kmh=b["speed_kmh"],
                    current_segment_id=b["current_segment_id"],
                    status=b["status"],
                    remaining_ticks=b["remaining_ticks"],
                    next_node=b["next_node"],
                    route_stops=b["route_stops"],
                    current_stop_index=b["current_stop_index"],
                    line_id=b["line_id"],
                    direction=b["direction"],
                )
            )

        logger.info("Parsed fleet successfully | cars=%d | buses=%d", len(cars), len(buses))
        return cars, buses

    except Exception:
        logger.exception("Failed to parse fleet data")
        raise


################################################   Moving Vehicles   #############################################################################


def segment_travel_ticks(edge_data: dict, vehicle_speed_kmh: float, tick_minutes: float = 1.0) -> int:
    length_km = edge_data["length_km"]
    speed_limit_kmh = edge_data["speed_limit_kmh"]
    traffic_multiplier = edge_data.get("traffic_multiplier", 1.0)

    effective_speed = min(vehicle_speed_kmh, speed_limit_kmh) * traffic_multiplier

    if effective_speed <= 0:
        logger.warning(
            "Effective speed <= 0 | segment=%s | vehicle_speed=%.2f | speed_limit=%.2f | multiplier=%.2f",
            edge_data.get("segment_id"),
            vehicle_speed_kmh,
            speed_limit_kmh,
            traffic_multiplier,
        )
        return 999999

    travel_time_hours = length_km / effective_speed
    tick_hours = tick_minutes / 60.0
    ticks = max(1, math.ceil(travel_time_hours / tick_hours))

    logger.info(
        "Segment %s travel ticks computed: %d",
        edge_data.get("segment_id"),
        ticks,
    )
    return ticks


def step_car(graph, car):
    try:
        if car.arrived():
            logger.info(
                "Car %s already arrived | current_node=%s | destination=%s",
                car.vehicle_id,
                car.current_node,
                car.destination_node,
            )
            return

        if car.remaining_ticks > 0:
            car.remaining_ticks -= 1
            logger.info(
                "Car %s progressing on segment %s | remaining_ticks=%d",
                car.vehicle_id,
                car.current_segment_id,
                car.remaining_ticks,
            )

            if car.remaining_ticks == 0 and car.next_node is not None:
                car.current_node = car.next_node
                car.path_index += 1
                car.next_node = None

                if car.arrived():
                    car.status = "arrived"
                    car.current_segment_id = None
                    logger.info(
                        "Car %s arrived at destination %s",
                        car.vehicle_id,
                        car.destination_node,
                    )
                else:
                    car.status = "moving"
                    logger.info(
                        "Car %s reached node %s | path_index=%d",
                        car.vehicle_id,
                        car.current_node,
                        car.path_index,
                    )
            return

        if car.path_index >= len(car.path_nodes) - 1:
            car.status = "arrived"
            car.current_segment_id = None
            logger.info(
                "Car %s path finished | current_node=%s | destination=%s",
                car.vehicle_id,
                car.current_node,
                car.destination_node,
            )
            return

        next_node = car.path_nodes[car.path_index + 1]
        edge_data = graph.get_edge_data(car.current_node, next_node)

        if edge_data is None:
            raise ValueError(f"No edge from {car.current_node} to {next_node}")

        car.current_segment_id = edge_data["segment_id"]
        car.next_node = next_node
        car.status = "moving"

        travel_ticks = segment_travel_ticks(edge_data, car.speed_kmh)
        car.remaining_ticks = travel_ticks - 1

        logger.info(
            "Car %s started segment %s | from=%s | to=%s | travel_ticks=%d",
            car.vehicle_id,
            car.current_segment_id,
            car.current_node,
            next_node,
            travel_ticks,
        )

        if travel_ticks == 1:
            car.current_node = next_node
            car.path_index += 1
            car.next_node = None

            if car.arrived():
                car.status = "arrived"
                car.current_segment_id = None
                logger.info(
                    "Car %s arrived immediately at destination %s",
                    car.vehicle_id,
                    car.destination_node,
                )

    except Exception:
        logger.exception("Error in step_car for %s", car.vehicle_id)
        raise


def step_bus(graph: nx.DiGraph, bus: Bus, algorithm: str = "astar") -> None:
    try:
        if not bus.path_nodes:
            bus.status = "stopped"
            bus.current_segment_id = None
            logger.warning("Bus %s has empty path_nodes", bus.vehicle_id)
            return

        if bus.reached_stop():
            logger.info(
                "Bus %s reached stop %s | line=%s",
                bus.vehicle_id,
                bus.current_target_stop(),
                bus.line_id,
            )

            bus.advance_to_next_stop()
            next_stop = bus.current_target_stop()

            logger.info(
                "Bus %s advancing to next stop %s | current_stop_index=%d | direction=%d",
                bus.vehicle_id,
                next_stop,
                bus.current_stop_index,
                bus.direction,
            )

            bus.path_nodes = best_path(graph, bus.current_node, next_stop, alg=algorithm)
            bus.path_index = 0
            bus.current_segment_id = None
            bus.status = "stopped"
            return

        if bus.path_index >= len(bus.path_nodes) - 1:
            bus.current_segment_id = None
            bus.status = "stopped"
            logger.warning(
                "Bus %s path ended before reaching target stop | current_node=%s | target_stop=%s",
                bus.vehicle_id,
                bus.current_node,
                bus.current_target_stop(),
            )
            return

        bus.status = "moving"
        next_node = bus.path_nodes[bus.path_index + 1]
        edge_data = graph.get_edge_data(bus.current_node, next_node)

        if edge_data is None:
            raise ValueError(f"No edge from {bus.current_node} to {next_node}")

        bus.current_segment_id = edge_data["segment_id"]
        bus.current_node = next_node
        bus.path_index += 1

        logger.info(
            "Bus %s moved | line=%s | current_node=%s | next_target_stop=%s | segment=%s",
            bus.vehicle_id,
            bus.line_id,
            bus.current_node,
            bus.current_target_stop(),
            bus.current_segment_id,
        )

    except Exception:
        logger.exception("Error in step_bus for %s", bus.vehicle_id)
        raise


def emit_vehicle_update(graph: nx.DiGraph, v) -> dict:
    try:
        x = graph.nodes[v.current_node]["x"]
        y = graph.nodes[v.current_node]["y"]

        event = {
            "type": "vehicle_update",
            "vehicle_id": v.vehicle_id,
            "vehicle_type": v.vehicle_type,
            "timestamp": utc_now_iso(),
            "x": x,
            "y": y,
            "current_node": v.current_node,
            "status": v.status,
            "speed_kmh": v.speed_kmh,
        }

        if v.vehicle_type == "car":
            event["destination_node"] = v.destination_node

        elif v.vehicle_type == "bus":
            event["route_stops"] = v.route_stops
            event["current_target_stop"] = v.current_target_stop()
            event["current_stop_index"] = v.current_stop_index
            event["direction"] = v.direction
            event["line_id"] = v.line_id
            event["segment_id"] = v.current_segment_id

        return event

    except Exception:
        logger.exception("Failed to emit vehicle update for %s", getattr(v, "vehicle_id", "unknown"))
        raise


def restart_path(graph, car, algorithm="astar"):
    try:
        old_destination = car.destination_node
        new_dest = random.choice([n for n in graph.nodes() if n != car.current_node])

        car.destination_node = new_dest
        car.path_nodes = best_path(graph, car.current_node, new_dest, alg=algorithm)
        car.path_index = 0
        car.status = "moving"
        car.parked_tickets = 0
        car.current_segment_id = None
        car.next_node = None
        car.remaining_ticks = 0

        logger.info(
            "Car %s restarted path | old_destination=%s | new_destination=%s | path_len=%d",
            car.vehicle_id,
            old_destination,
            new_dest,
            len(car.path_nodes),
        )

    except Exception:
        logger.exception("Failed to restart path for car %s", car.vehicle_id)
        raise


################################################   Traffic Logic   #############################################################################


def update_traffic(graph, cars, buses):
    counts = {}

    try:
        for vehicle in cars + buses:
            if vehicle.status == "parked":
                continue

            sid = getattr(vehicle, "current_segment_id", None)
            if sid is None:
                continue

            counts[sid] = counts.get(sid, 0) + 1

        events = []

        for u, v, data in graph.edges(data=True):
            sid = data["segment_id"]
            count = counts.get(sid, 0)

            old_level = data.get("traffic_level", "low")

            if count <= 1:
                new_level = "low"
                multiplier = T_LOW
            elif count <= 3:
                new_level = "medium"
                multiplier = T_MEDIUM
            else:
                new_level = "high"
                multiplier = T_HIGH

            data["traffic_level"] = new_level
            data["traffic_multiplier"] = multiplier
            data["weight"] = data["base_travel_time_h"] / multiplier

            if new_level != old_level:
                events.append(
                    {
                        "type": "traffic_update",
                        "segment_id": sid,
                        "from_node": u,
                        "to_node": v,
                        "traffic_level": new_level,
                        "traffic_multiplier": multiplier,
                        "weight": data["weight"],
                        "timestamp": utc_now_iso(),
                    }
                )

        logger.info("Traffic updated | changed_segments=%d", len(events))
        return events

    except Exception:
        logger.exception("Failed to update traffic")
        raise


def should_reroute_car(graph, car, lookahead_edges=3):
    try:
        if car.remaining_ticks > 0:
            return False

        remaining = car.path_nodes[car.path_index:]
        if len(remaining) < 2:
            return False

        upcoming_edges = list(zip(remaining[:-1], remaining[1:]))[:lookahead_edges]

        for u, v in upcoming_edges:
            if graph[u][v].get("traffic_level") == "high":
                logger.info(
                    "Car %s should reroute due to high traffic on edge %s -> %s",
                    car.vehicle_id,
                    u,
                    v,
                )
                return True

        return False

    except Exception:
        logger.exception("Failed while checking reroute condition for car %s", car.vehicle_id)
        raise


def compute_path_cost(graph, path_nodes):
    if len(path_nodes) < 2:
        return 0.0

    total = 0.0
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        total += graph[u][v]["weight"]
    return total


def reroute_car(graph, car, algorithm="astar"):
    try:
        old_remaining = car.path_nodes[car.path_index:]
        new_path = best_path(graph, car.current_node, car.destination_node, alg=algorithm)

        old_cost = compute_path_cost(graph, old_remaining)
        new_cost = compute_path_cost(graph, new_path)

        logger.info(
            "Reroute evaluation for car %s | old_cost=%.6f | new_cost=%.6f",
            car.vehicle_id,
            old_cost,
            new_cost,
        )

        if new_cost >= old_cost * 0.90:
            logger.info("Car %s reroute skipped | improvement too small", car.vehicle_id)
            return None

        car.path_nodes = new_path
        car.path_index = 0
        car.current_segment_id = None
        car.next_node = None
        car.remaining_ticks = 0

        logger.info(
            "Car %s rerouted successfully | old_path_len=%d | new_path_len=%d",
            car.vehicle_id,
            len(old_remaining),
            len(new_path),
        )

        return {
            "type": "route_recalculated",
            "vehicle_id": car.vehicle_id,
            "vehicle_type": car.vehicle_type,
            "timestamp": utc_now_iso(),
            "reason": "traffic",
            "old_path": old_remaining,
            "new_path": new_path,
            "old_cost": old_cost,
            "new_cost": new_cost,
        }

    except Exception:
        logger.exception("Failed to reroute car %s", car.vehicle_id)
        raise