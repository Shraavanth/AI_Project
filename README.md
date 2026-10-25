# Self-Organizing Multi-Agent Systems for Decentralized Environmental Monitoring

A web-based simulation in which 20 autonomous software agents (monitoring drones,
fire drones, sprinklers, pollution units and cooling units) are placed on a real
map, sense their environment, detect hazards with a local AI model, agree on what
they see through local consensus, divide the response work among themselves, move
to the incident, reduce its severity, and reorganize themselves when one of them
fails. A central Command Center receives their telemetry and stores the history.

**Agents monitor -> detect -> communicate -> coordinate -> move -> respond -> recover from failure -> continue monitoring -> report to the Command Center.**

---

## 1. Project overview

| Layer | Technology | Folder |
|---|---|---|
| Web application (6 pages, live map) | Next.js 14, React 18, TypeScript, Tailwind CSS, React-Leaflet, Recharts | `frontend/` |
| Central API, simulation loop, WebSocket | FastAPI, Uvicorn | `backend/` |
| Simulation engine (movement, incidents, tasks) | Python | `simulation/` |
| Agents, communication, consensus, allocation, failure handling | Python | `agents/` |
| Communication network and self-organization | NetworkX | `network/` |
| Anomaly detection and event classification | scikit-learn Isolation Forest + rules | `ai/` |
| Storage | SQLAlchemy, SQLite (default) or PostgreSQL/Supabase | `backend/models.py` |
| Automated tests | pytest | `tests/` |

Everything in the live simulation (positions, readings, decisions, tasks) is
computed by the Python backend. The frontend only draws what the backend sends.

## 2. Problem statement

Centralized environmental monitoring depends on one server and one network
path. When a hazard such as a wildfire damages that infrastructure, monitoring
and response stop. Single sensors also drift or fail and can trigger false
alarms. We need monitoring nodes that can detect hazards locally, check each
other's evidence, organize a response among themselves and keep working when
some of them are lost.

## 3. Objectives

1. Place a fleet of agents with different capabilities around a real geographic area.
2. Detect environmental anomalies on each agent with a lightweight ML model.
3. Classify anomalies into hazard types (fire, pollution, extreme heat).
4. Confirm hazards through local agent-to-agent consensus rather than trusting a single sensor.
5. Assign response tasks to suitable agents based on capability, distance, battery and load.
6. Move agents and reduce hazard severity through simulated response actions.
7. Detect failed agents, reassign their tasks and reorganize the communication network.
8. Report telemetry to a Command Center and store a searchable history.

## 4. System architecture

```
 Browser (Next.js)  <-- WebSocket /ws (state every tick) --  FastAPI backend
   6 pages, Leaflet map   --- REST /api/* (actions) ----->   SimulationService
                                                               |  background loop: engine.step()
                                                               v
                     +---------------- SimulationEngine (simulation/engine.py) ----------------+
                     |  environment.py   incidents and their effect on sensors                |
                     |  ai/              Isolation Forest + event classifier (batch per tick)  |
                     |  network/         NetworkX graph, range links, relay links              |
                     |  coordination.py  detection, investigation, consensus, task allocation  |
                     |  agents/          Agent, messages, consensus, allocation, failures      |
                     +-------------------------------------------------------------------------+
                                                               |  sampled records
                                                               v
                                         SQLite file (data/environmental_mas.db) or PostgreSQL
```

One simulation tick = one simulated second. Each tick runs, in order:
environment -> sensing -> local AI -> network rebuild and heartbeats -> failure
detection -> new alerts -> coordination (consensus, tasks, reassignment) ->
movement and response actions -> incident status -> telemetry.

## 5. Agent types

| Type | Id prefix | Count | Moves? | Special capability | Behaviour |
|---|---|---|---|---|---|
| Environmental Monitoring Drone | `MD` | 8 | Yes, 30 m/s | Patrol, investigate | Patrols its own sector of the area, raises alerts, investigates other agents' alerts |
| Fire Response Drone | `FD` | 4 | Yes, 45 m/s | Fire suppression | Waits at its base, flies to confirmed fires |
| Water Sprinkler Unit | `SP` | 3 | **No (fixed)** | Water spray, 350 m radius | Activates only for fires inside its operating radius |
| Pollution Response Unit | `PU` | 3 | Yes, 20 m/s | Pollution clean-up | Drives to confirmed pollution incidents |
| Cooling / Recovery Unit | `CU` | 2 | Yes, 22 m/s | Cooling | Drives to confirmed extreme-heat areas |

Every agent carries the same six sensors, so every agent can detect hazards and
vote in consensus. Speeds are scaled up so a demonstration fits in a few minutes.

Agent statuses used by the implementation: `IDLE`, `PATROLLING`, `DETECTING`,
`COORDINATING`, `MOVING`, `RESPONDING`, `RETURNING`, `FAILED`, `RECOVERING`, `COMPLETED`.

## 6. Geographic map and location detection

- The map uses **Leaflet** with **OpenStreetMap** data (CARTO dark tiles). No API key is needed.
- On the first visit the Area Simulator asks the browser for the user's location
  (`navigator.geolocation`). The browser shows its own permission prompt; nothing
  happens silently. Geolocation only works on a secure page: `https://` or `http://localhost`.
- If permission is granted, the position is rounded to about 100 m and the fleet is deployed around it.
- If permission is denied or unavailable, the panel says:
  *"Location access is unavailable. Search for your monitoring area or select a location on the map."*
  Three fallbacks are offered: **place search** (OpenStreetMap Nominatim; only the typed text is sent),
  **select a point on the map**, and a configurable **demo location** (VIT Vellore by default).
- The operating radius (0.4-5 km) can be changed before deploying.
- Agents are spread with a golden-angle (sunflower) pattern so no two share a position.
- All distances use the **Haversine** formula (`simulation/geo.py`). Movement converts
  "move N metres toward the target" into a new latitude/longitude.
- The monitoring area is stored in the backend, so every page and every browser shows the same area.
  In a shared public deployment other viewers will see the chosen area, so use search or the demo location there.

## 7. Movement system

Movement is computed in the backend every tick (`Agent.step_towards`):

- **Monitoring drones** follow 6 waypoints in their own sector (a zig-zag between 35 % and 85 % of the radius). Different drones cover different sectors.
- **Response units** stay at their base until given a task; they then fly/drive straight to the incident and return to base afterwards.
- **Sprinklers** never move.
- Agents with a task never return to patrol until the task ends.
- **Battery**: flying costs 2.5 % per km, a response action 0.15 % per second. Below 20 % an idle agent returns home to charge; below 25 % it is not given new response tasks; at 0 % it fails.

## 8. Environmental sensor model

Six readings per agent: temperature, humidity, smoke (0-1), CO2 (ppm), air quality index, soil moisture.

Each agent has its own normal background values plus small random noise every tick.
An incident changes readings according to distance:

```
influence = (severity / 100) * exp(-1.2 * (distance / radius)^2)
reading   = background + noise + effect[type][sensor] * influence
```

| Hazard | Main effects at the centre (severity 100) |
|---|---|
| Fire | +32 C, -75 % humidity, +0.95 smoke, +750 ppm CO2 |
| Pollution | +1100 ppm CO2, +230 AQI, +0.6 smoke |
| Extreme heat | +34 C, -35 % humidity, drier soil |

Readings move halfway toward the new value each tick, so they rise and fall
gradually. When an incident is resolved its influence disappears and readings
drift back to normal.

## 9. Anomaly detection

`ai/anomaly_detector.py` - scikit-learn **Isolation Forest** (200 trees) trained
on 3000 synthetic *normal* readings (`ai/generate_dataset.py`, with realistic
correlations, for example drier air when it is hotter). Contamination is 1 %
(the first version used 5 %, which flagged one in twenty normal readings).

- Input readings are validated (all six present, numeric, within physical limits).
- Output: `NORMAL` or `ANOMALY` and the decision score (negative = anomalous).
- All agents are evaluated in one batch per tick.
- If the model file is missing or was saved by another scikit-learn version, it is retrained automatically.

## 10. Event classification

`ai/event_classifier.py` - simple documented rules applied **only** to anomalous readings
(the Isolation Forest does not know what a fire is):

| Class | Rule |
|---|---|
| FIRE | temperature >= 40 C and humidity <= 30 % and smoke >= 0.50 |
| POLLUTION | CO2 >= 800 ppm and AQI >= 120 and smoke >= 0.30 |
| EXTREME_HEAT | temperature >= 40 C and smoke < 0.30 |
| OTHER_ANOMALY | flagged by the model but matches no rule |

An agent raises an alert only after seeing the **same** hazard class on two consecutive readings.

## 11. Agent communication

`agents/communication.py`. A message is delivered only if the NetworkX graph has
a path (one or more hops) between sender and receiver. Failed agents are not in
the graph, so they can neither send nor receive. Every message has an id, sender,
receiver, type, incident id, payload (evidence), timestamp, hop count and a
delivered flag, and is stored in the database.

Message types: `INCIDENT_ALERT`, `SENSOR_EVIDENCE`, `CONSENSUS_UPDATE`,
`COORDINATOR_CHANGE`, `TASK_PROPOSAL`, `TASK_ACCEPTED`, `FAILURE_ALERT`,
`TASK_REASSIGNED`, `RESPONSE_PROGRESS`, `TASK_COMPLETED`.

## 12. Local consensus

`agents/consensus.py`. Only agents involved in the alert vote: the detectors,
the neighbours that received the `INCIDENT_ALERT`, and investigators sent to the
area. Each votes with its **own** latest sensor analysis:

- **Support**: its AI classified the same hazard type.
- **Oppose**: its readings are normal and it is within 300 m of the alert point.
- **Abstain**: too far to observe, a different anomaly pattern, or no network route to the coordinator.

```
confidence = support / (support + oppose)
CONFIRMED  if support >= 2 and confidence >= 0.6   (never on the first round)
REJECTED   if not confirmed within 40 s, or nobody supports it for 6 s
```

If too few agents can observe the area, the coordinator sends up to two
monitoring drones to **investigate**: they fly to the alert point and visit four
points 180 m around it. The incident position is estimated as the weighted
centre of agents that currently sense the hazard.

A single faulty sensor cannot confirm an incident (tested in `tests/test_consensus_false_alarm.py`).

## 13. Coordination and task assignment

The **coordinator** of an incident is the agent with the strongest local evidence
when the alert is raised. If it fails, the nearest involved agent takes over
(`COORDINATOR_CHANGE`).

On confirmation the coordinator follows the response plan (`simulation/config.py`):

| Hazard | Units requested |
|---|---|
| Fire | 2 fire drones + up to 2 sprinklers that already cover the fire |
| Pollution | 2 pollution units |
| Extreme heat | 1 cooling unit |

For each unit (`agents/task_allocation.py`):
1. must have the capability, 2. must be operational, 3. must be free (task load),
4. battery >= 25 %, 5. reachable from the coordinator, 6. fixed sprinklers must be in range.
Among the remaining candidates the lowest **score = distance in km + (100 - battery)/100** wins.
The UI shows every candidate and why it was or was not chosen.
The coordinator sends `TASK_PROPOSAL`; the agent answers `TASK_ACCEPTED`.

## 14. Incident response

- Responders travel to the incident and switch to `RESPONDING` on arrival.
- Each responder removes severity every second while it is close to the real hazard (fire drone 0.5, sprinkler 0.35, pollution unit 0.55, cooling unit 1.0 points per second).
- An untreated fire **grows** by 0.12 per second; pollution and heat do not fade by themselves.
- An incident is **resolved only when its severity falls to 3 or below**.
- If no capable agent is available for 15 s, the incident becomes `NEEDS_INTERVENTION` and keeps its severity (the fire keeps growing). It is never silently closed.

## 15. Failure handling

Fail any agent from the map, Agent Fleet or Network page (or it fails when its battery runs out). Immediately:
it stops moving, sensing and communicating, its links are removed, and its task is marked `INTERRUPTED`.

Other agents discover the failure, because none of them can read its status directly:
1. **Peer heartbeat**: linked neighbours hear each other every second. After 3 s of silence with no route through the mesh, a neighbour declares it lost and sends `FAILURE_ALERT`. (If it is still reachable through other agents it only moved out of range.)
2. **Task owner check**: the incident coordinator notices the same timeout for its task owner.
3. **Command Center**: marks an agent offline after 5 s without telemetry (monitoring only).

## 16. Task reassignment

When the coordinator detects the lost owner it removes the task from that agent,
runs the same selection (excluding the lost agent), sends `TASK_PROPOSAL` /
`TASK_ACCEPTED` and broadcasts `TASK_REASSIGNED`. **The task keeps its id but its
owner in the backend changes**; the owner history is shown in the UI
(for example `FD-04 (interrupted) then FD-01`). The new owner then travels to the
incident and continues the response. If no suitable agent exists the task stays
`UNASSIGNED` and the incident eventually shows `NEEDS_INTERVENTION`; it is picked
up automatically when a capable agent is restored.

## 17. Self-organization

`network/network_manager.py` rebuilds the graph every tick from real positions:

1. **Range links**: operational agents within 600 m (Haversine) link automatically.
2. **Relay links**: if the graph is split into clusters, the closest pair of agents from two clusters form a relay link, as long as they are within 1000 m (boosted transmit power). This repeats until the graph is connected or no bridge is possible.

After a failure or restore, a reorganization record stores the failed agent, the links removed, the links created, the relay links, the cluster count, whether the network is connected, and the measured computation time. If it stays partitioned, that is reported as partitioned.

## 18. Central Command Center

The Command Center page shows the totals (operational, failed, responding, incidents, links, connectivity, battery),
open incidents, task ownership, the telemetry table for every agent with the time since its last report, and the
live activity feed. Telemetry is received every tick and sampled to the database every 5 s.

## 19. Database

SQLite file `data/environmental_mas.db` by default, PostgreSQL/Supabase via `DATABASE_URL`. Tables are created automatically.

| Table | Contents |
|---|---|
| `deployment_sites` | every deployed area (run id, centre, radius, source) |
| `agent_states` | latest state of every agent |
| `telemetry` | sampled readings, AI result, battery, position (every 5 s; capped at 30 000 rows) |
| `incidents` | incident lifecycle, severity, estimate, coordinator, timeline |
| `incident_severity` | severity samples (every 2 s) |
| `consensus_records` | every consensus round with all votes |
| `tasks` / `task_events` | tasks, owners, assigned / started / interrupted / reassigned / completed events |
| `agent_messages` | every agent-to-agent message |
| `agent_failures` | failure, who detected it, how, after how long, who took over, restoration |
| `network_events` | reorganizations with removed / created links |
| `activity_log` | human-readable timeline for the History page |

After a backend restart, a fresh fleet is deployed at the last area; incidents left open are marked `CLOSED_BY_RESTART`; all history remains.

## 20. API structure

Interactive documentation: `http://127.0.0.1:8000/docs`

| Method & path | Purpose |
|---|---|
| `GET /api/state` | full live snapshot (same as the WebSocket message) |
| `GET /api/status`, `GET /api/config` | summary, configuration and rules |
| `POST /api/simulation/deploy` | deploy the fleet at a location (lat, lng, radius, label, source) |
| `POST /api/simulation/pause` / `resume` / `reset` / `speed` / `step` | simulation control |
| `GET /api/agents`, `GET /api/agents/{id}` | agents, agent detail with messages and task history |
| `POST /api/agents/{id}/fail` / `restore` / `move` / `sensors` | operator actions |
| `POST /api/agents`, `DELETE /api/agents/{id}` | add / remove an agent |
| `POST /api/incidents`, `GET /api/incidents`, `GET /api/incidents/{id}` | create and inspect incidents |
| `GET /api/tasks`, `GET /api/network`, `GET /api/messages` | live tasks, graph, messages |
| `GET /api/history`, `/api/history/messages`, `/incidents`, `/failures`, `/task-events`, `/network-events` | stored history |
| `GET /api/analytics` | statistics computed from stored records |
| `WS /ws` | pushes `{"type": "state", "data": ...}` every tick; replies `pong` to `ping` |

Errors are explicit: unknown agent or incident -> 404; already failed, not failed,
fixed unit moved, duplicate id, location outside the area -> 400; invalid input -> 422.

## 21. Frontend navigation

| Page | Answers |
|---|---|
| **Area simulator** `/simulator` | Live map: agents (shape = type, colour = status), radio links, trails, hazard zones, the agents' estimated incident position, sprinkler ranges. Click Fire / Pollution / Extreme heat then the map to start an incident. Pause, resume, step, speed, reset. Click an agent to fail, restore or move it. The workflow strip shows the stage of the incident in focus. |
| **Command center** `/command-center` | What is happening across the whole system right now. |
| **Agent fleet** `/agents` | Every agent: sensors, neighbours, task, task history, messages, why it was chosen; fail, restore, move, override sensors. |
| **Incidents & response** `/incidents` | Timeline, consensus votes, task owners and reassignments, severity chart, affected agents, messages. |
| **Network** `/network` | The real communication graph by position, clusters, removed and created links, reorganization log; fail an agent here too. |
| **History & analytics** `/history` | Stored timeline, messages, failures and reassignments, charts (readings over time, availability, incidents by type, resolution times, detection pipeline). |

If the WebSocket drops, the app reconnects automatically and polls `/api/state` every 2 s meanwhile.
If the backend is unreachable a notice explains how to start it. If map tiles cannot load, agents are still drawn on a plain grid.

## 22. Local setup (Windows, PowerShell)

Requirements: Python 3.10-3.13, Node.js 18 or newer. No paid services or accounts are needed.

**Terminal 1 - backend** (from the project folder, e.g. `C:\Users\you\environmental-mas`):

```powershell
cd environmental-mas
python -m venv venv                      # first time only
.\venv\Scripts\Activate.ps1              # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt

python ai\generate_dataset.py            # optional: creates data\environmental_data.csv
python ai\train_model.py                 # optional: the backend trains it automatically if missing

uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The database file `data\environmental_mas.db` and its tables are created automatically on first start.
(To create them without starting the server: `python -c "from backend.database import init_db; init_db()"`.)

**Terminal 2 - frontend:**

```powershell
cd environmental-mas\frontend
copy .env.example .env.local             # first time only (points to http://127.0.0.1:8000)
npm install                              # first time only
npm run dev
```

Open **http://localhost:3000**. Allow location access when the browser asks (or use the search / map / demo options).
API docs: http://127.0.0.1:8000/docs

## 23. Testing

```powershell
# from the project folder with the venv active
python -m pytest -v
```

44 tests in `tests/` use a temporary database and drive the simulation tick by tick:

- `test_ai.py` - normal / fire / pollution / heat readings, false alarm rate, input validation
- `test_geo_network.py` - Haversine, movement, range links, relay bridging, honest partition reporting
- `test_engine_workflow.py` - deployment, patrol, distance-based sensor change, full fire workflow, pollution, readings returning to normal, untreated fire growth
- `test_failure_reassignment.py` - failed responder replaced by another capable agent (task owner changes), coordinator re-election, no replacement -> needs intervention, restore, battery failure, invalid operations
- `test_consensus_false_alarm.py` - one faulty sensor is rejected
- `test_api.py` - every endpoint, error codes, WebSocket ping, history from the database, history survives a restart

Frontend checks (in `frontend\`): `npm run typecheck`, `npm run lint`, `npm run build`.

## 24. Demonstration steps (faculty demo)

1. **Open the map.** Allow location: the map centres on you and 20 agents appear. Point out the five shapes, the patrolling drones, the radio links.
2. **Create a fire.** Click *Fire*, then click on the map near a sprinkler (square). The dashed orange zone appears ("not yet detected").
3. **Agents coordinate.** Within ~3 s nearby agents turn amber (detecting); the workflow strip shows Detected -> Local consensus with supporters; monitoring drones may fly in to investigate; the coordinator gets a dashed ring.
4. **Response begins.** Two fire drones (triangles) turn purple and fly along dashed lines; a sprinkler in range activates; severity drops in the strip.
5. **Fail an agent.** Click a responding fire drone -> *Fail agent*. It turns grey with a cross and stops; its links vanish; the strip shows "Responder lost". (Use speed 1x or pause/step to take your time.)
6. **Replacement.** About 3 s later a neighbour detects the silence, the coordinator reassigns the task, and another fire drone flies in. The strip shows "1 reassignment".
7. **Resolution.** The incident resolves only when severity reaches 3. Optional: fail all fire drones and sprinklers to show "Needs intervention" while the fire grows.
8. **Command Center and history.** Show the telemetry table, activity feed, the incident's timeline and consensus votes, the task owner chain `FD-xx (interrupted) then FD-yy`, the Network page reorganization log, and the History analytics (failure detected after 3 s, task taken over after 3 s).

Optional false alarm demo: Agent Fleet -> choose a sprinkler -> Controls -> *Fill fire-like values* -> *Apply override*. Its neighbours read normal, so consensus rejects the alert.

## 25. Deployment preparation

- **Backend on Render**: `render.yaml` is included (build trains the model; start runs Uvicorn; health check `/health`). Set `ALLOWED_ORIGINS` to your Vercel URL and `DATABASE_URL` to Supabase (Render's free disk is wiped on redeploy).
- **Database on Supabase**: create a project, copy the PostgreSQL connection string into `DATABASE_URL`. Tables are created on first start.
- **Frontend on Vercel**: import the repository, set *Root Directory* to `frontend`, add `NEXT_PUBLIC_API_URL=https://<your-backend>.onrender.com`. No `localhost` URL is hard-coded for production.
- Geolocation requires HTTPS, which Vercel provides.
- Map tiles: CARTO basemaps with OpenStreetMap data, attribution shown on the map. Fine for an academic demo; for heavy public use, choose a tile plan or set `NEXT_PUBLIC_TILE_URL` to another provider.
- `Dockerfile` is included for container hosts.
- Nothing has been published or deployed yet.

## 26. Limitations (what is simulated)

- Sensors, radios and movement are simulated in software; there is no hardware.
- Agents run inside one Python process. Decisions use only information an agent could have (its own readings, received messages, network reachability), but it is not a physically distributed system.
- The Command Center has a direct telemetry link to every agent (assumed uplink); it monitors and records but does not give orders.
- Movement is in straight lines with no terrain or obstacles; speeds are scaled up for the demo.
- The ML model is trained on synthetic data; classification uses fixed rules.
- Alert grouping uses the incident's true position to decide which incident an alert belongs to (a simulation shortcut); the response itself uses the agents' estimated position.
- One shared simulation per backend: every viewer sees and controls the same area.
- The documents in `Project_Presentation/` describe the first version and must be regenerated (see the note in that folder).

## Folder structure

```
environmental-mas/
  ai/                 anomaly_detector.py, event_classifier.py, generate_dataset.py, train_model.py, analyze_data.py
  agents/             agent.py, agent_types.py, communication.py, consensus.py, task_allocation.py, self_organization.py
  network/            network_manager.py
  simulation/         engine.py, coordination.py, environment.py, tasks.py, geo.py, config.py
  backend/            main.py, database.py, models.py, persistence.py, websocket_manager.py, api/, schemas/, services/
  frontend/           Next.js app (src/app/<page>/page.tsx, src/components, src/lib)
  tests/              pytest suite
  data/, models/      dataset, trained model, SQLite database
  legacy/             original scripts kept for reference (not used)
  Project_Presentation/  slides and documents from the first version
```
