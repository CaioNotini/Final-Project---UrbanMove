from __future__ import annotations

import json
import random
from dotenv import load_dotenv
import requests
import os

from simulator.grid import create_city_graph
from simulator.run_sim import *
from db.grid_db import create_graph, read_graph, load_graph
from db.vehicle_db import *
from api.api import send_traffic_events, send_reroute_events, send_vehicle_events

CARS = 5
BUSES = 2
NODES_X = 10
NODES_Y = 10
TICKS = 10
TRAFIC_PROBABILITY = 0.02

load_dotenv()
API_URL = os.getenv("API_URL")



def main():
    random.seed(42)

    width, height = NODES_X, NODES_Y

    # ---------------- GRAPH ----------------
    if read_graph():
        print("Loading graph from database")
        graph = load_graph()
    else:
        print("Creating graph and saving to database")
        graph = create_city_graph(
            width, height,
            default_speed=50.0,
            bidirectional=True
        )
        create_graph(graph)

    # ---------------- VEHICLES ----------------
    num_cars = CARS
    num_buses = BUSES
    algo = "astar"

    cars, buses = read_vehicles(graph, algorithm=algo)

    missing_cars = max(0, num_cars - len(cars))
    missing_buses = max(0, num_buses - len(buses))

    if missing_cars == 0 and missing_buses == 0:
        print(f"Loaded {len(cars)} cars and {len(buses)} buses from database")
    else:
        print("Creating fleet")

        new_cars = spawn_cars(
            graph=graph,
            num_cars=missing_cars,
            algorithm=algo,
            start_index=len(cars),
        )

        new_buses = spawn_buses(
            graph=graph,
            num_buses=missing_buses,
            algorithm=algo,
            start_index=len(buses),
        )

        if new_cars or new_buses:
            create_vehicles(new_cars + new_buses)
            create_vehicle_states(graph, new_cars + new_buses)

        cars, buses = read_vehicles(graph, algorithm=algo)

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
            step_bus(graph, b, algorithm=algo)

            event = emit_vehicle_update(graph, b)
            vehicle_events.append(event)

        # 3) Move cars
        for c in cars:

            # -------- PARKED LOGIC --------
            if c.status == "parked":
                c.parked_tickets -= 1

                if c.parked_tickets <= 0:
                    restart_path(graph, c, algorithm=algo)

                    event = emit_vehicle_update(graph, c)
                    vehicle_events.append(event)

                continue

            # -------- REROUTING LOGIC --------
            if should_reroute_car(graph, c):
                reroute_event = reroute_car(graph, c, algorithm=algo)

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
    print("API_URL usada:", API_URL)

if __name__ == "__main__":
    main()