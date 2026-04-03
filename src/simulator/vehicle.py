from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Vehicle:
    vehicle_id: str
    current_node: int
    path_nodes: List[int]
    path_index: int = 0
    speed_kmh: float = 30.0
    current_segment_id: Optional[str] = None
    status: str = "parked"  # moving, parked, accident.
    vehicle_type: str = None
    remaining_ticks: int = 0
    next_node: Optional[int] = None

    def arrived(self) -> bool:
        return self.path_index >= len(self.path_nodes) - 1


@dataclass
class Car(Vehicle):
    destination_node: int = -1
    vehicle_type: str = "car"
    parked_tickets: int = 0

    def arrived(self) -> bool:
        return (
            self.current_node == self.destination_node
            or self.path_index >= len(self.path_nodes) - 1
        )


@dataclass
class Bus(Vehicle):
    route_stops: List[int] = field(default_factory=list)
    current_stop_index: int = 0
    line_id: str = "L1"
    vehicle_type: str = "bus"
    direction: int = 1  # 1 for forward, -1 for reverse

    def current_target_stop(self) -> int:
        return self.route_stops[self.current_stop_index]

    def reached_stop(self) -> bool:
        return self.current_node == self.current_target_stop()

    def advance_to_next_stop(self) -> None:
        if not self.route_stops or len(self.route_stops) == 1:
            return

        next_index = self.current_stop_index + self.direction

        if next_index >= len(self.route_stops):
            self.direction = -1
            next_index = self.current_stop_index + self.direction

        elif next_index < 0:
            self.direction = 1
            next_index = self.current_stop_index + self.direction

        self.current_stop_index = next_index
        
    def arrived(self) -> bool:
        return self.reached_stop()