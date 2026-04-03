smart-mobility/
│
├── services/
│ ├── simulator/
│ │ ├── vehicles/
│ │ ├── graph/
│ │ ├── emitter/
│ │ └── main.py
│ │
│ ├── api/
│ │ ├── routes/
│ │ ├── schemas/
│ │ ├── services/
│ │ ├── repositories/
│ │ └── main.py
│ │
│ ├── processor/
│ │ ├── traffic/
│ │ ├── incidents/
│ │ └── main.py
│ │
│ └── auth/
│ └── ...
│
├── shared/
│ ├── models/
│ ├── config/
│ ├── utils/
│ └── database/
│
├── data/
│ ├── scenarios/
│ │ ├── small_city.json
│ │ ├── medium_city.json
│ │ └── rush_hour.json
│ ├── seeds/
│ │ ├── graph_seed.json
│ │ ├── routes_seed.json
│ │ └── fleet_seed.json
│ └── exports/
│
├── scripts/
│ ├── init_db.py
│ ├── seed_data.py
│ ├── reset_db.py
│ └── load_scenario.py
│
├── infra/
│ ├── docker/
│ ├── compose/
│ └── aws/
│
├── tests/
│ ├── simulator/
│ ├── api/
│ └── integration/
│
├── docker-compose.yml
├── .env
├── .env.example
├── requirements.txt
└── README.md
