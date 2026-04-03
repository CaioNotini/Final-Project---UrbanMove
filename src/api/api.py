import requests
from requests.exceptions import RequestException, ReadTimeout
import os
from dotenv import load_dotenv

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