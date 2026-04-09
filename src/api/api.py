import requests
from requests.exceptions import RequestException, ReadTimeout
import os
from dotenv import load_dotenv
import networkx as nx


load_dotenv()
API_URL = os.getenv("API_URL")
def send_vehicle_events(events: list[dict]):
    try:
        response = requests.post(
            f"{API_URL}/vehicles/events",
            json=events,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except ReadTimeout:
        print(f"[TIMEOUT] vehicle batch timed out ({len(events)} events)")
        return None
    except RequestException as e:
        body = ""
        if getattr(e, "response", None) is not None:
            body = e.response.text
        print(f"[ERROR] failed to send vehicle batch: {e}")
        if body:
            print(f"[ERROR BODY] {body}")
        return None
    
    
def send_traffic_events(events: list[dict]):
    try:
        response = requests.post(
            f"{API_URL}/traffic/events",
            json=events,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except ReadTimeout:
        print(f"[TIMEOUT] traffic batch timed out ({len(events)} events)")
        return None
    except RequestException as e:
        print(f"[ERROR] failed to send traffic batch: {e}")
        return None


def send_reroute_events(events: list[dict]):
    try:
        response = requests.post(
            f"{API_URL}/vehicles/reroutes",
            json=events,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except ReadTimeout:
        print(f"[TIMEOUT] reroute batch timed out ({len(events)} events)")
        return None
    except RequestException as e:
        print(f"[ERROR] failed to send reroute batch: {e}")
        return None
    

def get_graph(width, height):
    response = requests.post(
        f"{API_URL}/graph",
        json={
            "width": width,
            "height": height
        },
        timeout=30
    )
    response.raise_for_status()
    data = response.json()

    graph = nx.DiGraph()

    for node in data["nodes"]:
        graph.add_node(node["id"], x=node["x"], y=node["y"])

    for edge in data["edges"]:
        graph.add_edge(
            edge["from_node"],
            edge["to_node"],
            segment_id=edge["segment_id"],
            weight=edge["weight"],
            length_km=edge["length_km"],
            speed_limit_kmh=edge["speed_limit_kmh"],
            traffic_level=edge["traffic_level"],
            traffic_multiplier=edge["traffic_multiplier"],
            base_travel_time_h=edge["base_travel_time_h"],
        )

    return graph

def get_or_create_fleet(num_cars, num_buses, algorithm="astar"):
    try:
        response = requests.post(
            f"{API_URL}/vehicles/fleet",
            json={
                "num_cars": num_cars,
                "num_buses": num_buses,
                "algorithm": algorithm
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] failed to get fleet through API: {e}")
        return None