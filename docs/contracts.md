## VehicleUpdate

Produced by: Simulator
Consumed by: System, Analytics

Meaning:
Represents the real-time position and speed of a vehicle in the grid city.

Fields:

- vehicle_id: unique vehicle identifier
- ts: timestamp
- x: grid X coordinate (0–9)
- y: grid Y coordinate (0–9)
- speed_kmh: speed in kilometers per hour

Rules:

- Emitted every simulation tick
- speed_kmh must be >= 0
