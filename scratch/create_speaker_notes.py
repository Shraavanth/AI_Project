import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def build_speaker_notes():
    doc = docx.Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Document Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("COMPREHENSIVE SLIDE-BY-SLIDE SPEAKER NOTES & VIVA DEFENSE GUIDE")
    run_title.font.name = "Segoe UI"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(10, 37, 64)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Self-Organizing Multi-Agent Systems for Decentralized Environmental Monitoring\nVerbatim Spoken Narration, Timing Guides, and Anticipated Faculty Q&A")
    run_sub.font.name = "Segoe UI"
    run_sub.font.size = Pt(11)
    run_sub.font.color.rgb = RGBColor(74, 85, 104)
    run_sub.font.italic = True

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Executive Summary Box
    summary_table = doc.add_table(rows=1, cols=1)
    summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = summary_table.cell(0, 0)
    set_cell_background(cell, "EDF2F7")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    p_sum = cell.paragraphs[0]
    p_sum.add_run("HOW TO USE THIS GUIDE FOR YOUR PRESENTATION:\n").bold = True
    p_sum.add_run(
        "This guide provides exact word-for-word scripts for presenting each of the 20 slides in your defense deck. "
        "Each section includes the slide target time (for an optimal 15–18 minute viva), core technical message, "
        "spoken script, key formulas/terminology to emphasize on screen, and the most common faculty examination questions "
        "with authoritative answers derived directly from your codebase."
    )
    p_sum.runs[0].font.name = "Segoe UI"
    p_sum.runs[0].font.size = Pt(10)
    p_sum.runs[1].font.name = "Segoe UI"
    p_sum.runs[1].font.size = Pt(9.5)
    p_sum.runs[1].font.color.rgb = RGBColor(45, 55, 72)

    doc.add_paragraph().paragraph_format.space_after = Pt(16)

    # Slide Notes Data
    slides_notes = [
        {
            "num": 1,
            "title": "Title Slide — Project Identity & Scope",
            "time": "0:45 mins",
            "objective": "Establish professional credibility, state project title, and outline core technical focus.",
            "script": (
                "Good morning, respected members of the evaluation committee and faculty advisors. "
                "Today, I am proud to present our project: 'Self-Organizing Multi-Agent Systems for Decentralized Environmental Monitoring.'\n\n"
                "In traditional environmental monitoring, systems rely heavily on centralized cloud architectures. In critical emergencies—such as "
                "rapidly expanding wildfires, industrial petrochemical leaks, or urban heat waves—communication bottlenecks and single points of "
                "failure can cause catastrophic blind spots. Our project solves this fundamental limitation by embedding unsupervised machine learning "
                "and peer-to-peer consensus directly into decentralized edge monitoring agents, allowing them to autonomously detect hazards and self-heal "
                "the network communication mesh in under 20 milliseconds when nodes are physically destroyed."
            ),
            "terms": "Multi-Agent System (MAS), Edge AI, Isolation Forest, Peer-to-Peer Consensus, Mesh Self-Healing.",
            "viva": [
                ("What makes this project different from existing IoT environmental monitoring projects?",
                 "Traditional IoT systems are 'sense-and-forward'—they simply stream raw telemetry to a cloud dashboard. Our system performs decentralized AI inference directly at the edge, validates hazard detections through localized peer consensus without cloud intervention, and dynamically reorganizes the network topology when nodes physically fail.")
            ]
        },
        {
            "num": 2,
            "title": "Introduction — Autonomous Decentralized Environmental Intelligence",
            "time": "1:00 min",
            "objective": "Explain what the system does, its 6 telemetry channels, and its strategic value.",
            "script": (
                "To introduce the system, imagine an array of autonomous monitoring agents deployed across an ecologically sensitive region. "
                "Each node acts as an intelligent probe tracking six continuous environmental telemetry streams: ambient temperature, relative humidity, "
                "smoke particulate density, carbon dioxide concentration, air quality index (AQI), and soil moisture.\n\n"
                "Instead of streaming continuous raw data over scarce bandwidth to a central server, each agent evaluates its local readings using an on-node "
                "Isolation Forest model. When an abnormal signature is detected, the agent classifies the event into a specific hazard class—such as FIRE or "
                "POLLUTION—and initiates a localized peer-to-peer voting quorum with its immediate physical neighbors. This edge-first paradigm eliminates single "
                "points of failure and guarantees operational continuity during communications blackouts."
            ),
            "terms": "6D Telemetry Feature Space, Unsupervised Edge Inference, Quorum Gate, Fault Tolerance.",
            "viva": [
                ("Why monitor 6 specific parameters?",
                 "A single parameter like temperature is insufficient to differentiate between normal summer heat and an active combustion fire. By correlating Temperature, Humidity, Smoke Density, CO2, AQI, and Soil Moisture simultaneously in a 6-dimensional feature space, we can accurately distinguish between distinct hazards like wildfires, industrial pollution plumes, and extreme heat waves.")
            ]
        },
        {
            "num": 3,
            "title": "Problem Statement — Critical Shortcomings of Centralized Monitoring",
            "time": "1:15 mins",
            "objective": "Clearly expose why centralized monolithic architectures fail during disaster scenarios.",
            "script": (
                "Let us examine why traditional centralized architectures fail during real-world crises.\n\n"
                "First, centralized systems possess an inherent Single Point of Failure (SPOF). If the central cloud server, base station, or satellite uplink "
                "disconnects, the entire monitoring perimeter goes completely blind. In wildfires, high radiant heat often destroys the very cell towers needed to relay alerts.\n\n"
                "Second, transmitting continuous raw telemetry from hundreds of sensors clogs wireless bandwidth and introduces latency. In emergencies, seconds count.\n\n"
                "Third, centralized systems lack localized spatial cross-validation. A single failing sensor that drifts can trigger an expensive, unnecessary emergency dispatch. "
                "Finally, standard star topologies are fragile: if a parent gateway goes down, all downstream nodes are permanently severed. We need a system that distributes "
                "both the intelligence and the topology itself."
            ),
            "terms": "Single Point of Failure (SPOF), Bandwidth Saturation, Sensor Drift False Positives, Star Topology Rigidity.",
            "viva": [
                ("Isn't cloud computing powerful enough to handle millions of sensor messages?",
                 "While cloud computing has high compute capacity, it relies on unbroken communication backhauls. In forest fires, industrial explosions, or earthquakes, the physical infrastructure (cellular masts, cables, satellite uplinks) is frequently the first thing destroyed. Edge intelligence ensures safety decisions occur locally regardless of cloud availability.")
            ]
        },
        {
            "num": 4,
            "title": "Proposed Solution — Edge Intelligence & Dynamic Topology",
            "time": "1:00 min",
            "objective": "Present the 3 core architectural pillars of the proposed system.",
            "script": (
                "To overcome these challenges, we propose an integrated multi-agent architecture built upon three distinct pillars:\n\n"
                "Pillar One: On-Node Edge AI. Each agent executes a local scikit-learn Isolation Forest model, calculating an unsupervised anomaly score in under 1.5 milliseconds, followed by multi-hazard rule classification.\n\n"
                "Pillar Two: Peer-to-Peer Neighbor Consensus. Instead of global flooding, anomalous nodes alert only proximate active neighbors. The neighborhood computes a confidence score; only if confidence exceeds the 50% threshold is the incident officially escalated.\n\n"
                "Pillar Three: Dynamic Mesh Self-Healing. When nodes suffer hardware failure or destruction, our NetworkX engine prunes severed communication edges and automatically reconnects orphaned active nodes based on Manhattan proximity (distance ≤ 4), restoring biconnectivity in under 20 milliseconds."
            ),
            "terms": "Edge ML Inference, Localized Quorum, Proximity Reconnect, Graph Biconnectivity.",
            "viva": [
                ("How do you ensure the nodes don't exhaust their battery with heavy AI models?",
                 "We chose an Isolation Forest with 200 estimators. The entire trained model is only 2.2 megabytes and executes inference in under 1.5 ms on CPU without requiring GPU acceleration. Agents also implement graceful degradation: if battery drops below 30%, they shift to a low-frequency sentry mode.")
            ]
        },
        {
            "num": 5,
            "title": "Project Objectives — Primary Goals & Target Benchmarks",
            "time": "1:00 min",
            "objective": "Review the formal research objectives and empirical benchmarks.",
            "script": (
                "Our project pursued five primary technical objectives and three systems engineering deliverables.\n\n"
                "Primarily, we aimed to: First, simulate autonomous multi-agent monitoring over a 20-by-20 grid. Second, train and deploy an Isolation Forest model "
                "for real-time edge anomaly detection. Third, establish an explainable multi-hazard classifier. Fourth, formulate a localized neighborhood consensus "
                "algorithm with threshold validation. And fifth, implement an autonomous graph topology restructuring algorithm.\n\n"
                "In terms of system deliverables, we engineered a production-grade FastAPI backend with 22 REST endpoints and WebSocket broadcasting, a 7-table "
                "SQLAlchemy persistence schema, and a full Next.js 14 mission control frontend with interactive Leaflet GIS mapping. All eleven automated test suites "
                "pass with 100% verification."
            ),
            "terms": "20x20 Spatial Grid, 22 REST Endpoints, SQLAlchemy ORM, Leaflet GIS, 11/11 Pytest Suites.",
            "viva": [
                ("What was your primary criterion for defining a successful recovery?",
                 "Network biconnectivity. After a node fails and edges are dropped, the self-organization algorithm must discover replacement links between proximate active orphans such that `nx.is_connected(subgraph)` evaluates to True in less than 50 milliseconds. In empirical testing, recovery averaged 12 to 18 milliseconds.")
            ]
        },
        {
            "num": 6,
            "title": "System Architecture — Multilayer Technical Blueprint",
            "time": "1:30 mins",
            "objective": "Walk through the high-resolution architecture diagram.",
            "script": (
                "Here on Slide 6, you can observe the end-to-end multilayer system architecture that we have implemented.\n\n"
                "At the top is the Public Web Application Layer built in Next.js 14 and React 18. It features six operational modules including our Command Center "
                "with Leaflet GIS maps, real-time Recharts telemetry graphs, and live node inspectors.\n\n"
                "Beneath the presentation layer is our Asynchronous FastAPI Backend. It coordinates simulation state, manages real-time WebSocket broadcasting via "
                "WebSocketManager, and exposes 22 robust REST endpoints.\n\n"
                "The core computational horsepower resides in the Intelligent Engine Triad: the AI Engine running the Isolation Forest, the Multi-Agent Engine "
                "governing individual agent behaviors and local consensus, and the NetworkX Mesh Engine managing graph connectivity.\n\n"
                "Finally, at the foundation is our Relational Persistence Layer, utilizing SQLAlchemy 2.0 ORM with SQLite for local execution and full PostgreSQL / "
                "Supabase compatibility for production deployment."
            ),
            "terms": "Next.js App Router, FastAPI ASGI, WebSocketManager, NetworkX Undirected Graph, SQLAlchemy ORM.",
            "viva": [
                ("How does the Next.js frontend receive updates in real time?",
                 "We implemented a native WebSocket connection at `/ws`. Whenever an event, sensor update, or topology reorganization occurs in the backend, the `WebSocketManager` pushes the JSON state delta directly to connected frontend clients, triggering instant UI state re-rendering without HTTP polling.")
            ]
        },
        {
            "num": 7,
            "title": "Multi-Agent Architecture — Decentralized P2P vs Centralized",
            "time": "1:15 mins",
            "objective": "Articulate why a multi-agent system was chosen over a single AI model.",
            "script": (
                "Slide 7 delves into the theoretical foundation of our Multi-Agent System paradigm.\n\n"
                "A faculty member might ask: 'Why use multiple agents when you could just train a single large neural network in the cloud?'\n\n"
                "The answer lies in spatial autonomy and fault isolation. A centralized model is fragile: if the communication channel to that model drops, "
                "all monitoring ceases. In our decentralized Multi-Agent System, each agent is an independent entity possessing local state, localized perception, "
                "and its own copy of the ML decision model.\n\n"
                "Instead of master-slave orchestration, our system uses decentralized peer-to-peer coordination. When an agent senses something abnormal, it "
                "initiates a localized consensus query with its immediate spatial neighbors. This distributed division of labor ensures that high-bandwidth data "
                "never leaves the physical locality, and no single node failure can ever compromise the broader network."
            ),
            "terms": "Distributed Autonomy, Spatial Locality, Fault Isolation, Decentralized P2P Coordination.",
            "viva": [
                ("What specific coordination model do your agents follow?",
                 "Our agents follow a decentralized peer-to-peer coordination model with spatial neighborhood quorum. There is no master orchestrator or leader election overhead; decisions are reached locally through weighted neighbor voting based on spatial proximity.")
            ]
        },
        {
            "num": 8,
            "title": "Different Types of Agents — Implemented Specializations & Roles",
            "time": "1:30 mins",
            "objective": "Detail the 5 implemented agent specializations in monitoring_agent.py.",
            "script": (
                "In our codebase under `agents/monitoring_agent.py`, each agent dynamically adopts specialized functional responsibilities depending on its hardware profile and environmental zone.\n\n"
                "We have implemented five distinct agent roles:\n"
                "First, Canopy Thermal Drones: Aerial infrared nodes tasked with detecting canopy-level combustion gradients and thermal heat spikes.\n\n"
                "Second, Atmospheric Sentry Nodes: Continuous greenhouse gas and aerosol profilers tracking elevated CO2 levels exceeding 800 ppm and particulate air quality degradation.\n\n"
                "Third, Riparian Hydrology Sensors: Positioned along river basins and wetlands to measure soil moisture and thermal flux to detect flash drought or contaminated runoff.\n\n"
                "Fourth, Sub-Canopy Soil Probes: Measuring root-level moisture and organic smoldering beneath the ground cover.\n\n"
                "And Fifth, Autonomous Mesh Relays: Positioned at topological choke-points to bridge distant clusters and route consensus packets across the mesh."
            ),
            "terms": "Canopy Thermal Drone, Atmospheric Sentry, Riparian Hydrology, Sub-Canopy Soil Probe, Mesh Relay.",
            "viva": [
                ("Where in the codebase are these agent roles defined?",
                 "In `agents/monitoring_agent.py`, inside the `agent_type` and `get_assignment()` methods, where roles and dynamic missions are mapped based on agent hardware configuration, operational zone, and current hazard state.")
            ]
        },
        {
            "num": 9,
            "title": "Agent-to-Agent Communication — Protocol & Quorum Formula",
            "time": "1:15 mins",
            "objective": "Explain the P2P communication protocol and write out the consensus formula.",
            "script": (
                "Slide 9 demonstrates how our agents communicate and reach agreement.\n\n"
                "Under `agents/communication.py`, we implement the `CommunicationManager`. When an agent detects an anomaly, it avoids network-wide flooding. "
                "Instead, it creates a structured JSON alert payload specifying the hazard type, decision score, and timestamp, transmitting it directly to its active neighbors.\n\n"
                "Under `agents/consensus.py`, the `ConsensusManager` then computes the local neighborhood consensus. The mathematical formula is:\n"
                "Confidence equals the count of agreeing neighbors divided by the total active local neighborhood.\n\n"
                "If the calculated confidence is greater than or equal to our threshold of 0.50, the hazard is officially CONFIRMED. If a single defective sensor "
                "reports an anomaly while its four neighbors report normal baseline conditions, the confidence is only 0.20, and the alert is suppressed as UNCERTAIN, "
                "successfully rejecting sensor noise."
            ),
            "terms": "Localized Quorum, Confidence Threshold (θ = 0.50), False Alarm Suppression, P2P Message Dispatch.",
            "viva": [
                ("Why is the consensus threshold set to 0.50?",
                 "A 0.50 threshold represents a simple majority quorum. In a spatial neighborhood where adjacent sensors are physically close, an actual environmental hazard (like a wildfire or toxic plume) will physically affect multiple nodes. A majority requirement filters out independent, non-correlated sensor glitches while reliably catching genuine expanding hazards.")
            ]
        },
        {
            "num": 10,
            "title": "Complete System Workflow — 8-Stage Execution Lifecycle",
            "time": "1:15 mins",
            "objective": "Walk through the 8 stages shown on the Agent_Workflow.png diagram.",
            "script": (
                "Slide 10 illustrates the complete eight-stage execution lifecycle of our platform, as visualized in our workflow diagram.\n\n"
                "Stage 1 is Environmental Sensing across our six telemetry variables. Stage 2 is Local AI Anomaly Scoring using the on-node Isolation Forest. "
                "Stage 3 is Contextual Hazard Event Classification into FIRE, POLLUTION, or EXTREME HEAT. Stage 4 is P2P Alert Broadcasting to active neighbors. "
                "Stage 5 is Local Neighborhood Consensus calculation. Stage 6 is Incident Escalation and persistent database logging with WebSocket push to the web HUD.\n\n"
                "When severe hazards destroy an edge node, the system enters Stage 7: Node Failure Detection and link pruning. Finally, in Stage 8, Autonomous "
                "Self-Organization executes, searching active orphan nodes within Manhattan proximity d ≤ 4, creating replacement links, and restoring continuous "
                "monitoring in under 20 milliseconds."
            ),
            "terms": "8-Stage Lifecycle, Decision Function, P2P Escalation, Manhattan Distance Pruning.",
            "viva": [
                ("What happens if an agent experiences complete power loss during consensus?",
                 "The `ConsensusManager` dynamically filters for `neighbor.status == 'ACTIVE'`. If an agent powers down, it is omitted from both the numerator and denominator of the quorum calculation, preventing dead nodes from stalling active consensus decisions.")
            ]
        },
        {
            "num": 11,
            "title": "Technologies and Tools Used — Categorized Stack & Selection Rationale",
            "time": "1:15 mins",
            "objective": "Defend the choice of each language, framework, database, and library.",
            "script": (
                "Slide 11 breaks down our technology stack and the engineering justifications behind each choice.\n\n"
                "We chose Python 3.11 for the backend and AI engine because of its unmatched ecosystem for scientific computing with scikit-learn, NetworkX, "
                "and pandas. For the web frontend, we selected TypeScript 5.6 and Next.js 14 with Tailwind CSS, ensuring strict compile-time type safety and "
                "sub-second UI responsiveness.\n\n"
                "For the API layer, FastAPI was selected over traditional Flask or Django because of its native asynchronous ASGI architecture, automated OpenAPI "
                "documentation, and high-performance WebSockets.\n\n"
                "For graph intelligence, NetworkX provided the necessary mathematical graph abstractions. For persistence, SQLAlchemy 2.0 ORM was chosen to maintain "
                "strict relational integrity and allow seamless switching between SQLite for local development and PostgreSQL for production cloud deployment."
            ),
            "terms": "FastAPI ASGI, Next.js 14 App Router, NetworkX Graph Theory, Scikit-Learn IsolationForest, SQLAlchemy ORM.",
            "viva": [
                ("Why did you select Isolation Forest over Deep Learning autoencoders?",
                 "Isolation Forest is an unsupervised tree-based algorithm that requires zero complex backpropagation, has a microscopic memory footprint (2.2 MB), and executes inference in <1.5 ms on basic low-power CPUs. Deep autoencoders require substantial GPU memory and compute power that are impractical on edge IoT sensor nodes.")
            ]
        },
        {
            "num": 12,
            "title": "Core Algorithms & Implementation — Mathematical Formulations",
            "time": "1:30 mins",
            "objective": "Explain the mathematics behind Isolation Forest, classification rules, and Manhattan proximity healing.",
            "script": (
                "Now, let us examine the mathematical rigor behind our three core algorithms.\n\n"
                "First, Isolation Forest: Unlike density estimation methods that calculate distance between normal points, Isolation Forest recursively isolates "
                "anomalies using random axis-aligned cuts. The average path length h(x) to isolate an anomaly is significantly shorter than for normal clustered points. "
                "Our model is trained with 200 estimators and a contamination factor of 0.05.\n\n"
                "Second, Contextual Event Classification: When an anomaly is flagged, rule-based heuristics map the multi-sensor signature: FIRE requires Temperature ≥ 40°C, "
                "Smoke Density ≥ 0.50, and Humidity ≤ 30%. POLLUTION requires CO2 ≥ 800 ppm, AQI ≥ 120, and Smoke ≥ 0.30.\n\n"
                "Third, Graph Self-Healing: We calculate the Manhattan distance D(A,B) = |x_A - x_B| + |y_A - y_B|. If the distance between two active orphan agents is ≤ 4, "
                "an edge is dynamically inserted and the graph is verified using `nx.is_connected(subgraph)`."
            ),
            "terms": "Isolation Path Length h(x), Contamination Factor (0.05), Manhattan Proximity Metric, Graph Subgraph Connectivity.",
            "viva": [
                ("Why use Manhattan distance instead of Euclidean distance for network reorganization?",
                 "In grid-based deployments (such as our 20x20 coordinate simulation), Manhattan distance accurately reflects rectilinear line-of-sight and hop-count constraints without floating-point square root overhead, making it computationally faster on embedded hardware.")
            ]
        },
        {
            "num": 13,
            "title": "Database Architecture & Data Flow — 7 Relational Schemas",
            "time": "1:15 mins",
            "objective": "Review the relational database schema in backend/models.py and the data pipeline.",
            "script": (
                "Under `backend/models.py`, our platform defines seven dedicated relational tables managed by SQLAlchemy.\n\n"
                "The `agents` table tracks node coordinates, battery, and dynamic health scores. `agent_deployments` and `deployment_site` persist real-world geographic "
                "latitude, longitude, and circular deployment radius. `environmental_readings` stores high-frequency time-series telemetry. `environmental_events` records "
                "detected hazard epicenters, consensus status, and severity.\n\n"
                "`consensus_records` logs the voting evidence trail, while `network_reorganizations` records failure recovery metrics. Finally, `system_audit_logs` provides "
                "an immutable audit trail with category filtering.\n\n"
                "The data flow pipeline moves from in-memory agent objects, through atomic SQLAlchemy database transactions, directly to WebSocket client push, ensuring "
                "sub-10 millisecond query responses on the frontend."
            ),
            "terms": "SQLAlchemy 2.0, 7 Relational Schemas, Time-Series Telemetry, Immutable Audit Timeline, WebSocket Delta Push.",
            "viva": [
                ("How does the database handle concurrent writes during simulation steps?",
                 "We utilize SQLAlchemy scoped session management (`SessionLocal`) with atomic commit and rollback blocks wrapped in try-finally statements, preventing session leaks and ensuring database locks remain transient.")
            ]
        },
        {
            "num": 14,
            "title": "Real-World Use Cases — 5 Practical Disaster & Ecological Domains",
            "time": "1:15 mins",
            "objective": "Demonstrate the real-world utility of the system across 5 industrial and ecological scenarios.",
            "script": (
                "Slide 14 presents five concrete real-world domains where our architecture delivers immediate practical value.\n\n"
                "First, Wildfire Detection in High-Risk National Forests: Deploying thermal drones and sentry nodes allows detection of smoldering combustion beneath dense "
                "forest canopies hours before satellite infrared passes or smoke towers spot plumes.\n\n"
                "Second, Petrochemical & Pipeline Leak Monitoring: Surrounding industrial refineries with autonomous atmospheric sentries continuously tracks fugitive CO2 "
                "and toxic plumes without laying kilometers of expensive fixed cabling.\n\n"
                "Third, Urban Heat Island Mitigation: Micro-climate sentries detect urban street canyon thermal stress (≥42°C), alerting municipal authorities to open cooling centers.\n\n"
                "Fourth, Riparian Watershed Conservation: Hydrology probes identify extreme moisture depletion and agricultural runoff contamination.\n\n"
                "Fifth, Post-Disaster Emergency Network Mesh: Following hurricanes or earthquakes, autonomous nodes self-heal to maintain critical telemetry even when cellular towers collapse."
            ),
            "terms": "Wildfire Canopy Detection, Petrochemical Plume Profiling, Urban Heat Island, Riparian Hydrology, Post-Disaster Ad-Hoc Mesh.",
            "viva": [
                ("Could this system be deployed on actual agricultural farms?",
                 "Yes. The exact same 6-sensor configuration and consensus logic can monitor soil moisture, humidity, and ambient heat across vast agricultural transects, automating precision irrigation while detecting early localized crop diseases or smoldering peat fires.")
            ]
        },
        {
            "num": 15,
            "title": "Demonstration Scenario — Step-by-Step Viva Execution Guide",
            "time": "1:30 mins",
            "objective": "Guide the examiner through the live demo scenario implemented in the web UI.",
            "script": (
                "To demonstrate that our implementation is completely functional, Slide 15 outlines the exact step-by-step viva scenario that we can execute live on screen.\n\n"
                "In Step 1, we open `/command-center`. We observe twenty active agents connected in a healthy mesh topology, all reporting normal baseline readings.\n\n"
                "In Step 2, we navigate to `/incidents` and trigger a Fire Event at coordinates (10, 10). Agents A4, A5, A6, and A7 enter the combustion zone. Temperature surges to 46°C "
                "and smoke spikes to 0.85.\n\n"
                "In Step 3, agent A6's Isolation Forest triggers an anomaly score of -0.21, classifies FIRE, and queries its neighbors. The neighborhood quorum confirms the fire with "
                "88% confidence.\n\n"
                "In Step 4, we simulate severe fire destroying agent A6 by clicking 'Fail Agent.' A6 transitions to FAILED, battery drops to zero, and its edges are severed.\n\n"
                "In Step 5, we trigger Self-Organization. The algorithm scans active orphan nodes, establishes replacement edges between A5 and A7, and reconnects the mesh in 12 milliseconds!\n\n"
                "Finally, in Step 6, we open `/history` to review the immutable audit log verifying each step of the entire sequence."
            ),
            "terms": "Live Guided Demo, Fire Epicenter Injection, Quorum Confidence 88%, Node Destruction, 12ms Topology Reconnect.",
            "viva": [
                ("Can you prove that agent A6 actually stopped communicating after failure?",
                 "Yes. In `agents/communication.py`, `CommunicationManager.send_message()` checks `neighbor.status == 'ACTIVE'`. Once A6 is marked FAILED, its neighbor lists are wiped, all incident edges in NetworkX are removed, and subsequent alert broadcasts bypass A6 completely.")
            ]
        },
        {
            "num": 16,
            "title": "Security, Reliability & Performance — Benchmarks & Fault Tolerance",
            "time": "1:00 min",
            "objective": "Highlight empirical latency benchmarks and software reliability features.",
            "script": (
                "Slide 16 details our performance benchmarks and reliability engineering.\n\n"
                "In terms of performance: Edge inference latency is less than 1.5 milliseconds per vector. Graph topology recovery is achieved in under 20 milliseconds. "
                "The serialized model footprint is only 2.2 megabytes, and bandwidth consumption is reduced by 95% compared to continuous telemetry streaming.\n\n"
                "In terms of reliability: We compute a dynamic health metric and reliability index: Reliability equals 60% Health plus 40% Battery. Nodes with battery below 30% "
                "automatically enter a low-power sentry mode to preserve life.\n\n"
                "In terms of security: All REST endpoints strictly validate incoming payloads using Pydantic schemas, FastAPI enforces CORS domain policies, and the database "
                "audit log cannot be altered by individual edge nodes."
            ),
            "terms": "1.5ms Inference Latency, <20ms Graph Healing, 95% Bandwidth Savings, Pydantic Schema Validation.",
            "viva": [
                ("How do you prevent a rogue or malicious node from injecting false fire alerts?",
                 "Because our consensus algorithm requires a local majority quorum (θ ≥ 0.50), a compromised node broadcasting a fabricated alert will fail to reach consensus if surrounding physical neighbors report normal environmental baselines. The false alert is suppressed and logged as UNCERTAIN.")
            ]
        },
        {
            "num": 17,
            "title": "Advantages & Innovation — Multi-Agent Paradigm vs Status Quo",
            "time": "1:00 min",
            "objective": "Recap the 5 major competitive differentiators of this project.",
            "script": (
                "To summarize the core innovations of this project on Slide 17:\n\n"
                "Innovation 1: True Decentralization. We eliminate cloud dependency for mission-critical hazard detection, ensuring the system functions during total internet blackouts.\n\n"
                "Innovation 2: 95% Bandwidth Reduction. Only verified anomalies and alert payloads are transmitted across the mesh.\n\n"
                "Innovation 3: Quorum-Validated False Alarm Suppression. Solitary sensor malfunctions are rejected by neighbor voting.\n\n"
                "Innovation 4: Dynamic Mesh Self-Healing. Severed network partitions are autonomously healed in under 20 milliseconds.\n\n"
                "Innovation 5: Explainable AI Transparency. Every agent generates human-readable natural language explanations justifying its hazard assessments."
            ),
            "terms": "Zero Cloud Dependency, 95% Bandwidth Savings, Quorum Rejection, Self-Healing Mesh, Explainable AI (XAI).",
            "viva": [
                ("What is the practical value of Explainable AI in this system?",
                 "During a wildfire crisis, emergency personnel need to know *why* an AI flagged an area—whether due to high heat, sudden oxygen depletion, or dense smoke. Our XAI engine generates instant plain-English narratives (e.g., 'Elevated temperature and high smoke indicate active combustion'), providing actionable clarity to emergency dispatchers.")
            ]
        },
        {
            "num": 18,
            "title": "Limitations & Future Roadmap — Implemented Scope vs Next-Gen Research",
            "time": "1:00 min",
            "objective": "Demonstrate academic honesty by clearly distinguishing implemented features from future scope.",
            "script": (
                "A key requirement of academic defense is honesty regarding project scope. Slide 18 demarcates our currently implemented boundaries from future research.\n\n"
                "Currently, our 20 edge agents and their physical IoT radios are software-simulated across a 20x20 coordinate grid, drone patrol movements follow "
                "stochastic drift, and classification rules use fixed baseline thresholds.\n\n"
                "Our future research roadmap includes four major advancements:\n"
                "First: Physical LoRaWAN and ESP32 hardware deployment on low-power 868 and 915 MHz transceivers.\n"
                "Second: Deep Reinforcement Learning using PPO algorithms for dynamic drone swarm repositioning to physically track expanding fire perimeters.\n"
                "Third: Byzantine Fault Tolerant (BFT) blockchain ledgers for tamper-proof regulatory emission compliance.\n"
                "And Fourth: Multi-modal fusion with Sentinel-2 and NASA FIRMS satellite thermal feeds."
            ),
            "terms": "Academic Demarcation, LoRaWAN / ESP32 Physical Deployment, Deep Reinforcement Learning (PPO), BFT Blockchain Ledger.",
            "viva": [
                ("What is the biggest engineering hurdle to deploying this on physical ESP32 microcontrollers?",
                 "Flash memory and floating-point math constraints. While standard Python cannot run on microcontrollers, the Isolation Forest decision tree logic and Manhattan proximity algorithms can be compiled down to lightweight C++ binaries using MicroPython or TinyML libraries, easily fitting within ESP32's 4MB flash limit.")
            ]
        },
        {
            "num": 19,
            "title": "Conclusion — Technical Contributions & Final Takeaway",
            "time": "1:00 min",
            "objective": "Deliver a powerful closing summary of the project's success and contributions.",
            "script": (
                "In conclusion, this project has successfully engineered, validated, and demonstrated an autonomous, decentralized multi-agent system for environmental monitoring.\n\n"
                "We have proved that shifting machine learning inference and consensus logic from monolithic cloud data centers to physical edge nodes produces an extraordinarily "
                "resilient, fault-tolerant monitoring grid. We successfully combined unsupervised Isolation Forest anomaly detection, contextual multi-hazard rule classification, "
                "a 50% threshold spatial quorum protocol, and sub-20ms graph topology self-healing.\n\n"
                "Supported by a full-stack Next.js 14 mission control dashboard, a 22-endpoint FastAPI backend, and 100% test pass verification, our system demonstrates that "
                "decentralized edge intelligence is the future of environmental disaster mitigation and ecological preservation."
            ),
            "terms": "Decentralized Edge Intelligence, 100% Test Verification, Disaster Resilience, Fault-Tolerant IoT Infrastructure.",
            "viva": [
                ("What was the most challenging part of developing this project?",
                 "Synchronizing state transitions across three separate layers: the in-memory NetworkX graph topology, the relational SQLAlchemy persistence layer, and the real-time WebSocket stream to the Next.js frontend, ensuring that graph reorganizations were reflected in the UI within milliseconds without race conditions.")
            ]
        },
        {
            "num": 20,
            "title": "Thank You & Q&A — Faculty Defense Reference",
            "time": "Open Defense",
            "objective": "Invite faculty questions and provide rapid reference numbers on screen.",
            "script": (
                "Thank you very much for your time, attention, and guidance throughout this evaluation. "
                "We are now open and eager to answer any questions from the esteemed members of the faculty committee."
            ),
            "terms": "Faculty Defense, Q&A, Isolation Forest (200 trees), Manhattan Reconnect (d ≤ 4), 11/11 Passed.",
            "viva": [
                ("General closing viva prompt: 'Explain the entire project in one single sentence.'",
                 "'Our project is an AI-driven, decentralized multi-agent platform that embeds machine learning and spatial peer consensus into autonomous edge sensor nodes, enabling real-time disaster detection and sub-20ms network self-healing without relying on a central cloud server.'")
            ]
        }
    ]

    # Populate Slide-by-Slide Notes in Word Document
    for item in slides_notes:
        h1 = doc.add_heading(f"Slide {item['num']}: {item['title']}", level=1)
        h1.runs[0].font.name = "Segoe UI"
        h1.runs[0].font.size = Pt(14)
        h1.runs[0].font.bold = True
        h1.runs[0].font.color.rgb = RGBColor(10, 37, 64)

        # Meta Table
        table = doc.add_table(rows=2, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Row 0: Target Time & Objective
        c00 = table.cell(0, 0)
        c00.paragraphs[0].add_run(f"Target Duration: {item['time']}").bold = True
        set_cell_background(c00, "F7FAFC")
        set_cell_margins(c00, 80, 80, 120, 120)

        c01 = table.cell(0, 1)
        c01.paragraphs[0].add_run(f"Objective: {item['objective']}")
        set_cell_background(c01, "F7FAFC")
        set_cell_margins(c01, 80, 80, 120, 120)

        # Row 1: Key Terms
        c10 = table.cell(1, 0)
        c10.paragraphs[0].add_run("Key Terms & Formulas:").bold = True
        set_cell_background(c10, "EDF2F7")
        set_cell_margins(c10, 80, 80, 120, 120)

        c11 = table.cell(1, 1)
        c11.paragraphs[0].add_run(item['terms'])
        set_cell_background(c11, "EDF2F7")
        set_cell_margins(c11, 80, 80, 120, 120)

        for row in table.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    p.runs[0].font.name = "Segoe UI"
                    p.runs[0].font.size = Pt(9.0)

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

        # Spoken Script Section
        p_spk_head = doc.add_paragraph()
        p_spk_head.add_run("WHAT TO SAY (SPOKEN SCRIPT):").bold = True
        p_spk_head.runs[0].font.name = "Segoe UI"
        p_spk_head.runs[0].font.size = Pt(10.5)
        p_spk_head.runs[0].font.color.rgb = RGBColor(43, 108, 176)
        p_spk_head.paragraph_format.space_after = Pt(4)

        # Spoken script box
        box_table = doc.add_table(rows=1, cols=1)
        box_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        b_cell = box_table.cell(0, 0)
        set_cell_background(b_cell, "F7FAFC")
        set_cell_margins(b_cell, top=100, bottom=100, left=150, right=150)
        p_scr = b_cell.paragraphs[0]
        p_scr.add_run(item['script'])
        p_scr.runs[0].font.name = "Segoe UI"
        p_scr.runs[0].font.size = Pt(9.5)
        p_scr.runs[0].font.color.rgb = RGBColor(26, 32, 44)

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

        # Viva Q&A
        p_viva_head = doc.add_paragraph()
        p_viva_head.add_run("ANTICIPATED FACULTY VIVA QUESTIONS & ANSWERS:").bold = True
        p_viva_head.runs[0].font.name = "Segoe UI"
        p_viva_head.runs[0].font.size = Pt(10.5)
        p_viva_head.runs[0].font.color.rgb = RGBColor(197, 48, 48)
        p_viva_head.paragraph_format.space_after = Pt(4)

        for q, a in item['viva']:
            p_q = doc.add_paragraph()
            p_q.add_run("Q: " + q).bold = True
            p_q.runs[0].font.name = "Segoe UI"
            p_q.runs[0].font.size = Pt(9.5)
            p_q.runs[0].font.color.rgb = RGBColor(45, 55, 72)
            p_q.paragraph_format.space_after = Pt(2)

            p_a = doc.add_paragraph()
            p_a.add_run("Model Answer: " + a)
            p_a.runs[0].font.name = "Segoe UI"
            p_a.runs[0].font.size = Pt(9.0)
            p_a.runs[0].font.color.rgb = RGBColor(74, 85, 104)
            p_a.paragraph_format.space_after = Pt(8)

        doc.add_paragraph().paragraph_format.space_after = Pt(14)

    output_path = os.path.join(os.path.abspath("Project_Presentation"), "Speaker_Notes.docx")
    doc.save(output_path)
    print("Saved Speaker Notes successfully to:", output_path)

if __name__ == "__main__":
    build_speaker_notes()
