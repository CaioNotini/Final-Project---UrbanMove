from __future__ import annotations

import json
import random
import requests


from src.simulator.grid import create_city_graph
from src.simulator.run_sim import *
from src.db.grid_db import create_graph, read_graph, load_graph
from src.db.vehicle_db import *
from src.api.api import get_graph, get_or_create_fleet, send_traffic_events, send_reroute_events, send_vehicle_events

CARS = 6
BUSES = 2
NODES_X = 10
NODES_Y = 10
TICKS = 10
TRAFIC_PROBABILITY = 0.02
ALGORITHM = "astar"  # or "dijkstra"





def main():
    random.seed(42)

    width, height = NODES_X, NODES_Y

    # ---------------- GRAPH ----------------
    graph = get_graph(width, height)

    # ---------------- VEHICLES ----------------
    fleet_data = get_or_create_fleet(CARS, BUSES, ALGORITHM)
    cars, buses = parse_fleet(fleet_data)

  # ---------------- SIMULATION LOOP ----------------
    for tick in range(TICKS):
        print(f"\n--- TICK {tick} ---")

        vehicle_events = []
        traffic_events_to_send = []
        reroute_events_to_send = []

        # 1) Update traffic FIRST
        traffic_events = update_traffic(graph, cars, buses)

        for te in traffic_events:
            traffic_events_to_send.append(te)
            print(json.dumps(te, ensure_ascii=False))

        # 2) Move buses
        for b in buses:
            step_bus(graph, b, algorithm=ALGORITHM)

            event = emit_vehicle_update(graph, b)
            vehicle_events.append(event)

        # 3) Move cars
        for c in cars:

            # -------- PARKED LOGIC --------
            if c.status == "parked":
                c.parked_tickets -= 1

                if c.parked_tickets <= 0:
                    restart_path(graph, c, algorithm=ALGORITHM)

                    event = emit_vehicle_update(graph, c)
                    vehicle_events.append(event)

                continue

            # -------- REROUTING LOGIC --------
            if should_reroute_car(graph, c):
                reroute_event = reroute_car(graph, c, algorithm=ALGORITHM)

                if reroute_event:
                    reroute_events_to_send.append(reroute_event)
                    print(json.dumps(reroute_event, ensure_ascii=False))

            # -------- MOVE CAR --------
            step_car(graph, c)

            # -------- ARRIVAL LOGIC --------
            if c.arrived() and c.status != "parked":
                c.status = "parked"
                c.parked_tickets = random.randint(4, 9)

                event = emit_vehicle_update(graph, c)
                vehicle_events.append(event)
                continue

            # -------- NORMAL UPDATE --------
            event = emit_vehicle_update(graph, c)
            vehicle_events.append(event)

        # 4) SEND IN BATCH
        if traffic_events_to_send:
            send_traffic_events(traffic_events_to_send)

        if reroute_events_to_send:
            send_reroute_events(reroute_events_to_send)

        if vehicle_events:
            send_vehicle_events(vehicle_events)

    print("Simulation finished.")

if __name__ == "__main__":
    main()