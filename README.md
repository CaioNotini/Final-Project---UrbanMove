## 📌 Overview

UrbanMove is a cloud-native smart mobility management platform designed to simulate, process, and analyze urban transportation data in real time.

The system integrates distributed simulation, cloud APIs, persistent storage, and analytics services to support intelligent mobility use cases such as:

- 🚗 Traffic simulation (cars & buses)
- 📊 Real-time analytics (speed, congestion)
- 🧭 Route recommendation
- ☁️ Cloud monitoring & logging

This project was developed as part of a Big Data & Cloud Computing final project, with a strong focus on:

- Architecture
- Scalability
- High availability
- Security
- Observability
- Cost optimization

---

## 🧱 Architecture

UrbanMove follows a distributed cloud architecture deployed on AWS.

| Component       | Technology             | Description                                    |
| --------------- | ---------------------- | ---------------------------------------------- |
| **Simulator**   | AWS EC2                | Generates real-time vehicle and traffic events |
| **API Service** | FastAPI + Docker (EC2) | Processes requests and exposes REST endpoints  |
| **Database**    | PostgreSQL (AWS RDS)   | Stores vehicles, traffic, and event data       |
| **Monitoring**  | AWS CloudWatch         | Collects logs and system metrics               |
| **Storage**     | AWS S3                 | Stores archived logs and backups               |
| **Dashboard**   | Streamlit              | Provides data visualization and analytics      |

---

## ⚙️ Tech Stack

- Backend: FastAPI, Python 3.12
- Database: PostgreSQL (AWS RDS)
- Simulation: NetworkX (A\*)
- Containerization: Docker
- Frontend: Streamlit
- Cloud: AWS (EC2, RDS, CloudWatch, S3, IAM)

---

## ☁️ System Access

> ⚠️ Ensure EC2 instances are running before proceeding.

#### 1. Start EC2 Instances

-   urbanmove-api\
-   urbanmove-simulator

#### 2. SSH Access (One terminal for instance)

```bash
ssh -i key.pem ubuntu@<API_IP>

ssh -i key.pem ubuntu@<SIM_IP>
```

#### 3. Enter the project space

```bash
cd Final-Project---UrbanMove

source .venv/bin/activate
```

#### 4. Run API

```bash
docker build -t urbanmove-api .

docker run -d -p 8000:8000 --env-file .env urbanmove-api
```

#### 5. Run Simulator

```bash
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

python -m src.main
```

#### 6. Test API

Open:

http://`<API_IP>`{=html}:8000/health

#### 7. Open dahsboard

```bash
streamlit run src/dashboard/app.py --server.address 0.0.0.0 --server.port 8501
```

---

## 🔐 Security

Security is a core part of the UrbanMove architecture and is implemented across identity, networking, and application layers.

-   **IAM Roles**: AWS IAM roles are used to grant controlled permissions to EC2 instances and cloud services. This avoids hardcoding credentials in the application and ensures least-privilege access.
- **Security Groups**: Network access is restricted using AWS Security Groups. The API exposes only required ports, while the database is private and only accessible from authorized services.
-   **JWT Authentication**: JSON Web Tokens protect sensitive endpoints and ensure only authorized users can access restricted operations.
-   **Protected Cloud Architecture**: The database is deployed in a private subnet and internal communication is restricted to necessary flows.

---

## 📊 Observability

UrbanMove includes monitoring and logging mechanisms to improve visibility and reliability.

-   **CloudWatch Logging**: Centralized logs from API and simulator for debugging and monitoring.
-   **S3 Log Archival**: Logs are stored long-term in S3 for backup and auditing.
-   **Service Monitoring**: Tracks API and simulator activity for faster issue detection.
-   **Operational Visibility**: Centralized monitoring improves maintainability and reliability.

---

## ♻️ Scalability

The system is designed to support growth in traffic and data.

-   **Stateless API Design**: Requests are independent, enabling easy replication of services.
-   **Horizontal Scaling Potential**: API can scale by adding instances behind a load balancer.
-   **Decoupled Components**: Simulator, API, and database operate independently.

---

## 🧯 Disaster Recovery

UrbanMove includes mechanisms to ensure resilience and continuity.

-   **RDS Automated Backups**: Enables recovery of database data in case of failure.
-   **Redundant Log Storage**: Logs stored in CloudWatch and S3 ensure persistence.
-   **Reproducible Deployment**: Containerized services allow easy redeployment.
-   **Minimal Downtime Objective**: System can be restored quickly with minimal disruption.
