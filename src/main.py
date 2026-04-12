from __future__ import annotations

import random
import time

from src.utils.logging_config import setup_logger

from src.simulator.run_sim import (
    parse_fleet,
    update_traffic,
    step_bus,
    step_car,
    emit_vehicle_update,
    restart_path,
    should_reroute_car,
    reroute_car,
)
from src.api.api import (
    get_graph,
    get_or_create_fleet,
    send_traffic_events,
    send_reroute_events,
    send_vehicle_events,
)

# CONFIG
CARS = 6
BUSES = 2
NODES_X = 10
NODES_Y = 10
ALGORITHM = "astar"
TICK_DELAY_SECONDS = 4
RANDOM_SEED = 42

# LOGGER
logger = setup_logger("urbanmove-simulator", "simulator.log")


def main() -> None:
    logger.info("Simulator starting")

    try:
        random.seed(RANDOM_SEED)

        width, height = NODES_X, NODES_Y

        # ---------------- GRAPH ----------------
        logger.info("Loading graph...")
        graph = get_graph(width, height)
        logger.info("Graph loaded successfully")

        # ---------------- VEHICLES ----------------
        logger.info("Loading fleet...")
        fleet_data = get_or_create_fleet(CARS, BUSES, ALGORITHM)
        cars, buses = parse_fleet(fleet_data)

        logger.info("Fleet loaded: %d cars | %d buses", len(cars), len(buses))

    except Exception:
        logger.exception("❌ Failed during initialization")
        return

    # ---------------- CONTINUOUS SIMULATION LOOP ----------------
    tick = 0

    while True:
        tick += 1
        logger.info("========== TICK %d ==========", tick)

        vehicle_events = []
        traffic_events_to_send = []
        reroute_events_to_send = []

        try:
            # ---------------- TRAFFIC ----------------
            try:
                traffic_events = update_traffic(graph, cars, buses)
                traffic_events_to_send.extend(traffic_events)
                logger.info("Traffic updated: %d events", len(traffic_events))
            except Exception:
                logger.exception("Error updating traffic")

            # ---------------- BUSES ----------------
            for b in buses:
                try:
                    step_bus(graph, b, algorithm=ALGORITHM)
                    event = emit_vehicle_update(graph, b)
                    vehicle_events.append(event)
                except Exception:
                    logger.exception("Error processing bus %s", b.vehicle_id)

            # ---------------- CARS ----------------
            for c in cars:
                try:
                    # parked cars wait before restarting
                    if c.status == "parked":
                        c.parked_tickets -= 1

                        if c.parked_tickets <= 0:
                            logger.info("Car %s restarting route", c.vehicle_id)
                            restart_path(graph, c, algorithm=ALGORITHM)

                            event = emit_vehicle_update(graph, c)
                            vehicle_events.append(event)

                        continue

                    # reroute only when appropriate
                    if should_reroute_car(graph, c):
                        reroute_event = reroute_car(graph, c, algorithm=ALGORITHM)
                        if reroute_event:
                            reroute_events_to_send.append(reroute_event)
                            logger.info("Car %s rerouted", c.vehicle_id)

                    # move car
                    step_car(graph, c)

                    # if arrived, park for a while before restarting
                    if c.arrived() and c.status != "parked":
                        c.status = "parked"
                        c.parked_tickets = random.randint(4, 9)

                        logger.info(
                            "Car %s parked for %d ticks",
                            c.vehicle_id,
                            c.parked_tickets,
                        )

                        event = emit_vehicle_update(graph, c)
                        vehicle_events.append(event)
                        continue

                    # normal update
                    event = emit_vehicle_update(graph, c)
                    vehicle_events.append(event)

                except Exception:
                    logger.exception("Error processing car %s", c.vehicle_id)

            # ---------------- SEND EVENTS ----------------
            try:
                if traffic_events_to_send:
                    send_traffic_events(traffic_events_to_send)
                    logger.info("Sent %d traffic events", len(traffic_events_to_send))
            except Exception:
                logger.exception("Failed to send traffic events")

            try:
                if reroute_events_to_send:
                    send_reroute_events(reroute_events_to_send)
                    logger.info("Sent %d reroute events", len(reroute_events_to_send))
            except Exception:
                logger.exception("Failed to send reroute events")

            try:
                if vehicle_events:
                    send_vehicle_events(vehicle_events)
                    logger.info("Sent %d vehicle events", len(vehicle_events))
            except Exception:
                logger.exception("Failed to send vehicle events")

        except Exception:
            logger.exception("❌ Fatal error in tick %d", tick)

        time.sleep(TICK_DELAY_SECONDS)


if __name__ == "__main__":
    main()