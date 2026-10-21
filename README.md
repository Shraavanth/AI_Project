# Self-Organizing Multi-Agent Systems for Decentralized Environmental Monitoring

An AI-driven, decentralized environmental monitoring platform demonstrating autonomous edge sensing, local anomaly classification, peer-to-peer alert propagation, neighbor consensus, and self-healing network topology reorganization under node failures.

---

## 1. Problem Statement
Traditional centralized environmental monitoring systems rely heavily on monolithic cloud architectures and centralized telemetry aggregators. In mission-critical emergency situations (such as wildfires, toxic atmospheric emissions, or industrial pipeline breaches), communication bottlenecks, single points of failure, and infrastructure disconnections can prevent timely hazard detection and response.

## 2. Project Objectives
- **Autonomous Local Sensing**: Deploy autonomous monitoring agents across a geographic grid tracking 6 critical environmental indicators: Temperature, Humidity, Smoke Index, CO2 Concentration, Air Quality Index (AQI), and Soil Moisture.
- **On-Node AI Anomaly Detection**: Evaluate environmental readings locally using a machine-learning Isolation Forest model without sending raw continuous data to a central cloud server.
- **Decentralized Event Classification**: Categorize anomalous sensor patterns into specific hazard classes (`FIRE`, `POLLUTION`, `EXTREME_HEAT`, `OTHER_ANOMALY`).
- **Peer-to-Peer Alert Propagation**: Transmit local hazard detections directly to proximate active neighbors.
- **Local Neighbor Consensus**: Form localized consensus decisions through weighted neighbor voting with confidence scoring.
- **Fault Tolerance & Self-Organization**: Detect physical node destruction or hardware failure, isolate severed links, and dynamically restructure the P2P communication mesh through proximity-based link formation.
- **Full Operational Web Dashboard**: Provide a mission-control web application structured into 6 distinct operational areas.

---

## 3. End-to-End System Workflow

```
Environmental Sensing (6 Telemetry Variables)
        ↓
Local Machine Learning Inference (Isolation Forest)
        ↓
Anomaly Detection & Scoring
        ↓
Contextual Hazard Event Classification (FIRE, POLLUTION, EXTREME HEAT)
        ↓
Peer-to-Peer Agent Communication & Alert Broadcasting
        ↓
Neighbor-Based Local Consensus & Confidence Calculation
        ↓
Hazard Incident Confirmation
        ↓
Agent Hardware Failure (Simulated Node Loss)
        ↓
Failure Detection & Link Pruning
        ↓
Autonomous Network Self-Organization
        ↓
Mesh Reorganization & Path Recovery (d ≤ 4 Manhattan Proximity)
        ↓
Continuous Monitoring & Persistent Telemetry Logging
```

---

## 4. System Architecture

```
                                  PUBLIC WEB APPLICATION
                                             |
                                             v
                           NEXT.JS 14 / REACT / TYPESCRIPT FRONTEND
                       (Command Center, Agents, Network, Incidents, Analytics, History)
                                             |
                                        REST / WebSocket
                                             |
                                             v
                                  FASTAPI APPLICATION SERVER
                                             |
                   ┌─────────────────────────┼────────────────────────┐
                   v                         v                        v
            AI ENGINE (ML)            AGENT ENGINE             NETWORK ENGINE
         - Isolation Forest        - Monitoring Agents       - NetworkX Mesh Graph
         - Event Classifier        - P2P Communication       - Proximity Reconnect
         - Anomaly Scoring         - Local Consensus         - Topology Recovery
                   |                         |                        |
                   └─────────────────────────┼────────────────────────┘
                                             |
                                             v
                                 SQLAlchemy ORM DATABASE
                           (PostgreSQL / Supabase / SQLite)
```

---

## 5. Module Breakdown & Algorithms

### A. AI Engine & Anomaly Detection (`ai/`)
- **Isolation Forest (`anomaly_detector.py`)**: Evaluates anomalous deviations in 6-dimensional feature space (`temperature`, `humidity`, `smoke`, `co2`, `air_quality`, `soil_moisture`). Returns `NORMAL` vs `ANOMALY` status and decision function score.
- **Event Classifier (`event_classifier.py`)**:
  - `FIRE`: High Temperature (≥40°C), Dense Smoke (≥0.50), Low Humidity (≤30%).
  - `POLLUTION`: High CO2 (≥800 ppm), Hazardous Air Quality (≥120 AQI), Moderate Smoke (≥0.30).
  - `EXTREME_HEAT`: Critical Ambient Temperature (≥40°C) with low particulates.
  - `OTHER_ANOMALY`: Statistical outlier in multi-sensor space.

### B. Autonomous Agents & Consensus (`agents/`)
- **Monitoring Agent (`monitoring_agent.py`)**: Encapsulates position, 6-sensor state, battery level, health rating, connectivity mesh score, and explainable AI evidence generator.
- **Peer Communication (`communication.py`)**: Asynchronous P2P message exchange between neighboring nodes.
- **Local Consensus (`consensus.py`)**: Aggregates the local agent's detection with active neighbors' decisions. Computes confidence:
  $$\text{Confidence} = \frac{\text{Count of Agreeing Neighbors}}{\text{Total Active Local Neighborhood}}$$
  Consensus is confirmed when confidence exceeds threshold ($\theta = 0.50$).

### C. Network Engine & Self-Organization (`network/`)
- **Graph Topology (`network_manager.py`)**: NetworkX undirected graph where vertices represent agents and edges represent P2P communication links.
- **Self-Healing Protocol**:
  1. Detect failed/unresponsive node.
  2. Prune all dead edges connected to the node.
  3. Search active orphan agents within Manhattan distance:
     $$D(A, B) = |x_A - x_B| + |y_A - y_B| \le 4$$
  4. Establish replacement links and verify global graph connectivity.

### D. Persistent Database Schema (`backend/models.py`)
- `agents`: Node registry, positions, battery, health scores.
- `agent_deployments` and `deployment_site`: Persisted geographic coordinates for deployed agents and their selected deployment area.
- `environmental_readings`: Time-series sensor snapshots and AI inference scores.
- `environmental_events`: Detected hazard incidents, epicenters, severity, consensus state.
- `consensus_records`: Voter distribution and neighbor evidence logs.
- `network_reorganizations`: Failure triggers, removed/created links, recovery duration in milliseconds.
- `system_audit_logs`: Searchable system audit trail with category filters.

---

## 6. Frontend Operational Sections (Next.js)

1. **Command Center (`/command-center`)**: Live spatial map, fleet HUD metrics, and real-time activity stream. Deploy the fleet at the browser's current location (with location permission) or select a map point, then choose a 0.5–10 km deployment radius. Agent coordinates are persisted by the backend; drone patrol motion is simulated.
2. **Agent Operations (`/agents`)**: Fleet table with battery/health gauges, agent inspector drawer, interactive 6-sensor sliders for manual tuning, and node deployment.
3. **Network Intelligence (`/network`)**: Interactive NetworkX graph topology visualizer, failure simulation button, self-organization trigger, and recovery metrics.
4. **Incident Management (`/incidents`)**: Multi-hazard triggers (`FIRE`, `POLLUTION`, `EXTREME HEAT`), active incident records, and decentralized consensus drilldown.
5. **Environmental Analytics (`/analytics`)**: Time-series charts for temperature, smoke, CO2, AQI, anomaly distributions, and recovery benchmarks.
6. **System History (`/history`)**: Chronological audit timeline with category filters (`ALL`, `EVENT`, `ANOMALIES`, `CONSENSUS`, `FAILURES`, `RECOVERY`, `NETWORK`, `AGENTS`).

---

## 7. How to Run Locally

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# Navigate to project root
cd environmental-mas

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
Backend API will be live at: `http://127.0.0.1:8000` (API Docs: `http://127.0.0.1:8000/docs`).

### 2. Frontend Setup
```bash
# Open a new terminal and navigate to frontend directory
cd environmental-mas/frontend

# Install dependencies (already prepared)
npm install

# Start Next.js development server
npm run dev
```
Open your browser at: `http://localhost:3000`.

---

## 8. Environment Variables

Create a `.env` file in the project root:

```env
# Database URL (Defaults to local SQLite if unset)
DATABASE_URL=sqlite:///./environmental_mas.db
# For Supabase / PostgreSQL in production:
# DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres

# Frontend API URL (in frontend/.env.local)
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

---

## 9. Evaluator Demo Scenario (Step-by-Step Viva Guide)

1. **Start System**: Open `/command-center`. Observe 20 active agents connected in a healthy mesh topology.
2. **Trigger Incident**: Navigate to `/incidents` (or click **Run Guided Demo** in the top bar). Click **Trigger Fire Event**.
3. **Inspect Local AI & Consensus**: Observe affected agents detect abnormal temperature and smoke, propagate alerts, and reach `CONFIRMED` local consensus with 85%+ confidence.
4. **Inspect Node Operations**: Navigate to `/agents`, select agent `A6`, inspect its 6 sensor readings, battery level, and AI explanation.
5. **Simulate Agent Failure**: Click **Fail Agent** on `A6`. Observe `A6` transition to `FAILED` and its communication links get severed.
6. **Inspect Network Intelligence**: Navigate to `/network`. See node `A6` highlighted in red/grey with dropped edges.
7. **Trigger Self-Organization**: Click **Trigger Self-Organization**. Watch the algorithm autonomously discover replacement links and reconnect orphan neighbors in under 20ms.
8. **Inspect Analytics & History**:
   - Go to `/analytics` to see the spike in temperature/smoke time-series charts.
   - Go to `/history` to review the immutable audit timeline verifying each step of the lifecycle.

---

## 10. Automated Test Suite

Run unit and integration tests using pytest:
```bash
python -m pytest tests/ -v
```
Test suite verifies:
- ML Anomaly Detector and Multi-Hazard Classifier
- MonitoringAgent health calculations and explainable AI narratives
- P2P message broadcast
- Local neighbor consensus calculations
- Network creation, failure isolation, and proximity self-organization
- FastAPI REST endpoints and database persistence

---

## 11. Project Limitations
- **Sensor Telemetry**: Physical IoT radio transceivers and hardware probes are software-simulated on a 20x20 spatial coordinate system.
- **Coordination Layer**: Local decision-making and consensus are decentralized at the agent peer level, while the centralized FastAPI server coordinates simulation state persistence and web UI streaming.
