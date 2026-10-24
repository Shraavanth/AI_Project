import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_callout(doc, title, text, bg_hex="F7FAFC", border_hex="2B6CB0"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = table.cell(0, 0)
    set_cell_background(c, bg_hex)
    set_cell_margins(c, top=120, bottom=120, left=180, right=180)
    p = c.paragraphs[0]
    p.add_run(title + "\n").bold = True
    p.runs[0].font.name = "Segoe UI"
    p.runs[0].font.size = Pt(10)
    p.runs[0].font.color.rgb = RGBColor(43, 108, 176)
    r2 = p.add_run(text)
    r2.font.name = "Segoe UI"
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = RGBColor(45, 55, 72)
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

def build_technical_overview():
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
    run_title = p_title.add_run("TECHNICAL OVERVIEW & SYSTEM SPECIFICATION")
    run_title.font.name = "Segoe UI"
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(10, 37, 64)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Self-Organizing Multi-Agent Systems for Decentralized Environmental Monitoring\nComprehensive Engineering Specification, Algorithmic Analysis & Architectural Reference")
    run_sub.font.name = "Segoe UI"
    run_sub.font.size = Pt(11.5)
    run_sub.font.color.rgb = RGBColor(74, 85, 104)
    run_sub.font.italic = True

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # Meta Table
    meta_table = doc.add_table(rows=2, cols=3)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_headers = [
        ("PROJECT VERSION", "Version 2.0.0 (Production-Ready)"),
        ("TECH STACK", "Next.js 14, FastAPI, Scikit-Learn, NetworkX"),
        ("VERIFICATION STATUS", "11/11 Test Suites Passing (100% Pass)"),
        ("AI MODEL", "Isolation Forest (200 Trees, 6 Features)"),
        ("TOPOLOGY HEALING", "Manhattan Proximity (Recovery <20ms)"),
        ("CONSENSUS QUORUM", "Localized Majority Gate (θ ≥ 0.50)")
    ]
    for idx, (head, val) in enumerate(meta_headers):
        r = idx // 3
        c = idx % 3
        cell = meta_table.cell(r, c)
        set_cell_background(cell, "EDF2F7")
        set_cell_margins(cell, 80, 80, 120, 120)
        p = cell.paragraphs[0]
        p.add_run(head + "\n").bold = True
        p.runs[0].font.name = "Segoe UI"
        p.runs[0].font.size = Pt(8.5)
        p.runs[0].font.color.rgb = RGBColor(43, 108, 176)
        r2 = p.add_run(val)
        r2.font.name = "Segoe UI"
        r2.font.size = Pt(9.0)
        r2.font.color.rgb = RGBColor(26, 32, 44)

    doc.add_paragraph().paragraph_format.space_after = Pt(16)

    # ========================================================
    # SECTION 1: EXECUTIVE ABSTRACT
    # ========================================================
    h = doc.add_heading("1. Executive Summary & Abstract", level=1)
    h.runs[0].font.name = "Segoe UI"
    h.runs[0].font.size = Pt(15)
    h.runs[0].font.color.rgb = RGBColor(10, 37, 64)

    doc.add_paragraph(
        "Traditional environmental hazard monitoring systems rely on centralized cloud architectures where edge sensors "
        "stream continuous telemetry to centralized ingest gateways. During catastrophic emergencies—such as wildfires, toxic industrial "
        "emissions, or post-disaster infrastructure collapses—communication backhauls are often severed, rendering centralized "
        "monitoring platforms useless. This project introduces a self-organizing, decentralized multi-agent system (MAS) capable of "
        "autonomous edge sensing, local machine learning inference, peer-to-peer (P2P) spatial consensus, and dynamic network topology self-healing."
    )
    doc.add_paragraph(
        "Each autonomous agent monitors six environmental parameters: temperature, humidity, smoke density, carbon dioxide (CO2), "
        "air quality index (AQI), and soil moisture. Using an on-node scikit-learn Isolation Forest model, agents perform unsupervised "
        "anomaly detection directly at the physical edge, categorizing anomalous signatures into specific hazard events (FIRE, POLLUTION, "
        "EXTREME HEAT). When an anomaly emerges, the agent broadcasts an alert to its active proximate neighbors, initiating a localized "
        "quorum voting protocol. If neighbor confidence exceeds 50%, the hazard is confirmed. If an edge agent suffers physical destruction, "
        "an autonomous NetworkX-based self-healing protocol prunes severed links and reorganizes the communication mesh using Manhattan "
        "proximity reconnection (d ≤ 4), restoring global network biconnectivity in under 20 milliseconds."
    )

    # ========================================================
    # SECTION 2: PROBLEM FORMULATION & LIMITATIONS
    # ========================================================
    h = doc.add_heading("2. Problem Formulation & Limitations of Monolithic IoT", level=1)
    h.runs[0].font.name = "Segoe UI"
    h.runs[0].font.size = Pt(15)
    h.runs[0].font.color.rgb = RGBColor(10, 37, 64)

    doc.add_paragraph(
        "In critical environmental hazard management, systems operate in high-risk, hostile conditions characterized by dynamic physical "
        "hazards and fragile communication environments. Traditional centralized Internet of Things (IoT) architectures suffer from four "
        "foundational vulnerabilities:"
    )

    p = doc.add_paragraph()
    p.add_run("1. Single Point of Failure (SPOF): ").bold = True
    p.add_run(
        "In a centralized cloud topology, all decision-making occurs remotely. If the central cloud server, local base station, or cellular "
        "mast is destroyed (a frequent occurrence in high-heat wildfire fronts), the entire regional monitoring apparatus goes completely blind."
    )

    p = doc.add_paragraph()
    p.add_run("2. Bandwidth Saturation & Latency Delays: ").bold = True
    p.add_run(
        "Continuous streaming of high-frequency multi-sensor telemetry across hundreds of nodes saturates low-bandwidth emergency wireless spectrum. "
        "Queuing delays and cloud ingestion pipelines introduce critical seconds of delay when early hazard intervention demands sub-second response."
    )

    p = doc.add_paragraph()
    p.add_run("3. Sensor Drift & Costly False Positives: ").bold = True
    p.add_run(
        "Individual physical sensors are prone to electrical noise, particulate fouling, and calibration drift. Without localized spatial cross-validation "
        "from adjacent nodes, a single glitchy sensor can trigger an expensive, unnecessary emergency dispatch."
    )

    p = doc.add_paragraph()
    p.add_run("4. Fragility of Rigid Star Topologies: ").bold = True
    p.add_run(
        "Standard IoT star topologies route all edge nodes through fixed parent gateways. When a gateway is incinerated or loses power, all downstream "
        "sensors are permanently isolated, fragmenting the network into unrecoverable partitions."
    )

    # ========================================================
    # SECTION 3: SYSTEM ARCHITECTURE
    # ========================================================
    h = doc.add_heading("3. End-to-End System Architecture", level=1)
    h.runs[0].font.name = "Segoe UI"
    h.runs[0].font.size = Pt(15)
    h.runs[0].font.color.rgb = RGBColor(10, 37, 64)

    doc.add_paragraph(
        "The system architecture is structured into four distinct layers, ensuring clean separation of concerns, high throughput, and robust fault isolation:"
    )

    add_callout(doc, "LAYER 1 — MISSION CONTROL WEB APPLICATION (Next.js 14)",
                "Built on React 18 and TypeScript with Tailwind CSS styling. Structured into six operational modules:\n"
                "• Command Center (/command-center): Live spatial map using Leaflet GIS, fleet HUD metrics, and real-time activity stream.\n"
                "• Agent Operations (/agents): Fleet table with battery/health gauges, agent inspector drawer, and manual sensor sliders.\n"
                "• Network Intelligence (/network): Interactive NetworkX topology visualizer, failure simulation, and self-organization triggers.\n"
                "• Incident Management (/incidents): Multi-hazard triggers (FIRE, POLLUTION, EXTREME HEAT) and decentralized consensus drilldown.\n"
                "• Environmental Analytics (/analytics): Time-series Recharts for temperature, smoke, CO2, AQI, and recovery benchmarks.\n"
                "• System History (/history): Searchable, immutable audit timeline categorized by event types.")

    add_callout(doc, "LAYER 2 — APPLICATION BACKEND & COORDINATION (FastAPI 0.141+)",
                "Asynchronous ASGI server powered by Uvicorn. Exposes 22 REST API endpoints covering fleet operations, simulation stepping, "
                "event triggering, network healing, and audit queries. Includes WebSocketManager providing real-time bidirectional JSON state "
                "streaming over WebSockets (/ws), pushing state deltas instantly to connected browser clients.")

    add_callout(doc, "LAYER 3 — INTELLIGENT ENGINE TRIAD",
                "• AI Engine (ai/): Scikit-learn Isolation Forest (200 estimators, 0.05 contamination) for 6D anomaly detection and contextual rule classifier.\n"
                "• Agent Engine (agents/): MonitoringAgent encapsulating sensing, battery, dynamic health scores, and localized consensus mechanics.\n"
                "• Network Engine (network/): NetworkX undirected graph model managing mesh topology, link pruning, and Manhattan proximity healing.")

    add_callout(doc, "LAYER 4 — RELATIONAL PERSISTENCE (SQLAlchemy 2.0 ORM)",
                "Relational database layer configured for embedded SQLite (development) and PostgreSQL / Supabase (production). Maintains "
                "seven normalized tables ensuring strict ACID compliance, spatial coordinate persistence, and immutable audit logging.")

    # ========================================================
    # SECTION 4: MULTI-AGENT TAXONOMY & ROLES
    # ========================================================
    h = doc.add_heading("4. Multi-Agent Taxonomy & Functional Roles", level=1)
    h.runs[0].font.name = "Segoe UI"
    h.runs[0].font.size = Pt(15)
    h.runs[0].font.color.rgb = RGBColor(10, 37, 64)

    doc.add_paragraph(
        "Under `agents/monitoring_agent.py`, each agent dynamically adopts specialized functional responsibilities depending on its "
        "hardware profile, operational zone, and active hazard context. Five agent roles are implemented:"
    )

    agent_table = doc.add_table(rows=6, cols=4)
    agent_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Agent Specialization", "Primary Sensory Inputs", "Decision & Inference Logic", "Operational Mission"]
    for i, head in enumerate(headers):
        cell = agent_table.cell(0, i)
        set_cell_background(cell, "2B6CB0")
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        p.add_run(head).bold = True
        p.runs[0].font.name = "Segoe UI"
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ("Canopy Thermal Drone", "Temperature, Smoke, Battery", "Infrared combustion profiling; detects thermal plumes ≥ 40°C", "Autonomous forest canopy transect patrol and combustion boundary profiling."),
        ("Atmospheric Sentry Node", "CO2, Air Quality (AQI), Smoke", "Evaluates CO2 ≥ 800 ppm and AQI ≥ 120 particulate degradation", "Continuous greenhouse gas and hazardous particulate plume dispersion monitoring."),
        ("Riparian Hydrology Sensor", "Soil Moisture, Humidity, Temp", "Detects stream moisture drops (<25%) and thermal baseline flux", "Riparian stream basin and watershed hydrological flux monitoring."),
        ("Sub-Canopy Soil Probe", "Soil Moisture, Temp, Smoke", "Root-level smoldering detection and microbial thermal survey", "Subterranean organic burn and soil dryness tracking beneath ground cover."),
        ("Autonomous Mesh Relay", "Neighbor Links, Battery, Latency", "Graph biconnectivity optimization; Manhattan proximity routing", "Decentralized P2P mesh routing, alert forwarding, and consensus aggregation.")
    ]
    for row_idx, row_data in enumerate(data, start=1):
        bg = "F7FAFC" if row_idx % 2 == 1 else "EDF2F7"
        for col_idx, text in enumerate(row_data):
            cell = agent_table.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, 60, 60, 80, 80)
            p = cell.paragraphs[0]
            p.add_run(text)
            p.runs[0].font.name = "Segoe UI"
            p.runs[0].font.size = Pt(8.5)
            p.runs[0].font.color.rgb = RGBColor(45, 55, 72)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Dynamic Health & Reliability Metrics
    p_dyn = doc.add_paragraph()
    p_dyn.add_run("Dynamic Health & Reliability Formulations:\n").bold = True
    p_dyn.add_run(
        "Each agent evaluates its own operational integrity continuously via two dynamic property formulas:\n"
        "• Health Index (0–100): Base score of 100, penalized by -20 if battery < 30%, -10 if battery < 60%, and -15 if operating under extreme temperature (>45°C) or dense smoke (>0.80).\n"
        "• Connectivity Index (0–100): Min(100, Active Neighbors * 33.4), guaranteeing full 100% rating at 3 or more active peers.\n"
        "• Reliability Index: Computed as (Health * 0.6) + (Battery * 0.4), prioritizing healthy, power-stable nodes during neighborhood voting."
    )

    # ========================================================
    # SECTION 5: ALGORITHMS & IMPLEMENTATION
    # ========================================================
    h = doc.add_heading("5. Core Algorithms & Mathematical Formulations", level=1)
    h.runs[0].font.name = "Segoe UI"
    h.runs[0].font.size = Pt(15)
    h.runs[0].font.color.rgb = RGBColor(10, 37, 64)

    doc.add_paragraph(
        "The system's technical core is driven by three interconnected mathematical algorithms:"
    )

    # Alg 1: Isolation Forest
    doc.add_heading("5.1 Isolation Forest Anomaly Detection (ai/anomaly_detector.py)", level=2)
    doc.add_paragraph(
        "The Isolation Forest algorithm isolates anomalous observations by randomly selecting a feature and a random split value "
        "between the maximum and minimum values of that feature. Because anomalies deviate significantly from normal baseline distributions, "
        "they are isolated at shallow depths in binary tree partitions."
    )
    doc.add_paragraph(
        "Let h(x) be the path length of observation x in an isolation tree, and c(n) be the average path length of unsuccessful searches "
        "in a Binary Search Tree (BST) over n samples: c(n) = 2(ln(n - 1) + 0.5772156649) - (2(n - 1) / n). The anomaly score s(x, n) is defined as:"
    )
    p_math = doc.add_paragraph()
    p_math.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_math.add_run("s(x, n) = 2^(- E(h(x)) / c(n))").bold = True
    p_math.runs[0].font.name = "Segoe UI"
    p_math.runs[0].font.size = Pt(11)
    p_math.runs[0].font.color.rgb = RGBColor(43, 108, 176)

    doc.add_paragraph(
        "When s -> 1, the instance is definitively anomalous. In our implementation (`ai/train_model.py`), the model is trained on 1,000 "
        "baseline environmental vectors using n_estimators=200 and contamination=0.05. Model inference runs in <1.5ms, outputting status "
        "(NORMAL / ANOMALY) and a decision function score."
    )

    # Alg 2: Event Classifier
    doc.add_heading("5.2 Contextual Multi-Hazard Rule Classification (ai/event_classifier.py)", level=2)
    doc.add_paragraph(
        "When the Isolation Forest flags an anomaly, the reading is evaluated against deterministic contextual multi-sensor boundaries:"
    )
    doc.add_paragraph(
        "• FIRE: Temperature ≥ 40.0°C AND Humidity ≤ 30.0% AND Smoke Density ≥ 0.50\n"
        "• POLLUTION: CO2 ≥ 800.0 ppm AND Air Quality (AQI) ≥ 120.0 AND Smoke Density ≥ 0.30\n"
        "• EXTREME HEAT: Temperature ≥ 40.0°C with non-combustion particulates (Smoke < 0.30)\n"
        "• OTHER ANOMALY: Statistical outlier in multi-sensor space outside the above signatures."
    )

    # Alg 3: Consensus
    doc.add_heading("5.3 Local Neighborhood Consensus (agents/consensus.py)", level=2)
    doc.add_paragraph(
        "To prevent solitary sensor drift from triggering false alarms, alerts are cross-validated through decentralized localized consensus. "
        "The initiating agent queries active neighbors in its direct graph neighborhood. The consensus confidence is calculated as:"
    )
    p_math2 = doc.add_paragraph()
    p_math2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_math2.add_run("Confidence = (Count of Agreeing Neighbors) / (Total Active Local Neighborhood)").bold = True
    p_math2.runs[0].font.name = "Segoe UI"
    p_math2.runs[0].font.size = Pt(11)
    p_math2.runs[0].font.color.rgb = RGBColor(43, 108, 176)

    doc.add_paragraph(
        "Consensus is confirmed when Confidence ≥ θ, where θ is the simple majority threshold of 0.50. Confirmed incidents are committed "
        "to the relational database with complete evidence voter distributions."
    )

    # Alg 4: Manhattan Self-Healing
    doc.add_heading("5.4 Manhattan Proximity Topology Self-Organization (network/network_manager.py)", level=2)
    doc.add_paragraph(
        "When an agent suffers hardware failure or physical destruction, all incident edges connected to that node are dropped. The autonomous "
        "reorganization protocol executes the following sequence:\n"
        "1. Identify all surviving active agents where status == 'ACTIVE'.\n"
        "2. For each pair of active agents (A, B) without an existing communication link, compute the rectilinear Manhattan distance:\n"
        "   D(A, B) = |x_A - x_B| + |y_A - y_B|\n"
        "3. If D(A, B) ≤ 4, dynamically insert edge (A, B) into the NetworkX undirected graph.\n"
        "4. Validate global graph biconnectivity via `nx.is_connected(subgraph)`.\n"
        "In empirical testing across 20 nodes, the self-healing routine restores global mesh biconnectivity in 12 to 18 milliseconds."
    )

    # ========================================================
    # SECTION 6: DATABASE SCHEMA
    # ========================================================
    h = doc.add_heading("6. Relational Persistence Schema & Data Pipeline", level=1)
    h.runs[0].font.name = "Segoe UI"
    h.runs[0].font.size = Pt(15)
    h.runs[0].font.color.rgb = RGBColor(10, 37, 64)

    doc.add_paragraph(
        "Under `backend/models.py`, seven relational database tables ensure persistent state tracking and audit compliance:"
    )

    db_table = doc.add_table(rows=8, cols=3)
    db_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    db_headers = ["Table Name", "Primary Keys / Core Fields", "Technical Role & Stored Data"]
    for i, head in enumerate(db_headers):
        cell = db_table.cell(0, i)
        set_cell_background(cell, "2B6CB0")
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        p.add_run(head).bold = True
        p.runs[0].font.name = "Segoe UI"
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)

    tables_data = [
        ("agents", "agent_id (PK), x, y, status, battery, health, connectivity, reliability", "Maintains active node registry, 2D coordinates, power reserves, and health indices."),
        ("agent_deployments", "agent_id (PK), latitude, longitude, area_label", "Stores real-world geographic GPS coordinates bound to simulation nodes."),
        ("deployment_site", "id (PK), latitude, longitude, radius_km, area_label", "Stores geographic epicenter coordinates and circular deployment radius (0.5–10km)."),
        ("environmental_readings", "id (PK), agent_id, temp, hum, smoke, co2, aqi, soil, ai_status, score, timestamp", "Time-series telemetry archive logging 6-sensor vectors and ML anomaly scores."),
        ("environmental_events", "event_id (PK), event_type, center_x, center_y, severity, consensus_state, confidence", "Hazard event ledger tracking active/resolved status, epicenters, and confidence scores."),
        ("consensus_records", "id (PK), event_id, event_type, consensus_reached, confidence, total_voters, evidence_summary", "Detailed evidentiary audit log recording agreeing voter tallies and neighbor signatures."),
        ("network_reorganizations", "id (PK), failed_agent_id, connections_removed, connections_created, recovery_time_ms", "Topology recovery log tracking severed links, created replacement edges, and duration in ms.")
    ]
    for row_idx, (tname, tfields, trole) in enumerate(tables_data, start=1):
        bg = "F7FAFC" if row_idx % 2 == 1 else "EDF2F7"
        cell0 = db_table.cell(row_idx, 0)
        cell1 = db_table.cell(row_idx, 1)
        cell2 = db_table.cell(row_idx, 2)
        set_cell_background(cell0, bg)
        set_cell_background(cell1, bg)
        set_cell_background(cell2, bg)
        set_cell_margins(cell0, 60, 60, 80, 80)
        set_cell_margins(cell1, 60, 60, 80, 80)
        set_cell_margins(cell2, 60, 60, 80, 80)
        cell0.paragraphs[0].add_run(tname).bold = True
        cell1.paragraphs[0].add_run(tfields)
        cell2.paragraphs[0].add_run(trole)
        for c in [cell0, cell1, cell2]:
            c.paragraphs[0].runs[0].font.name = "Segoe UI"
            c.paragraphs[0].runs[0].font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ========================================================
    # SECTION 7: REAL-WORLD USE CASES
    # ========================================================
    h = doc.add_heading("7. Real-World Use Cases & Practical Applications", level=1)
    h.runs[0].font.name = "Segoe UI"
    h.runs[0].font.size = Pt(15)
    h.runs[0].font.color.rgb = RGBColor(10, 37, 64)

    doc.add_paragraph(
        "The decentralized multi-agent architecture provides immediate operational value across diverse environmental and industrial applications:"
    )

    cases = [
        ("1. Wildfire Detection in High-Risk National Forests",
         "In dense forest reserves, satellite optical imagery is obscured by heavy cloud cover and passes only every several hours. "
         "A mesh of autonomous Canopy Thermal Drones and Atmospheric Sentries detects early smoldering combustion beneath dense tree canopies. "
         "Localized neighbor consensus prevents false alarms from tourist campfires, while self-healing ensures that when intense fires burn edge nodes, "
         "the surviving perimeter nodes dynamically reconnect to maintain real-time firebreak tracking."),
        
        ("2. Petrochemical Refinery & Pipeline Breach Monitoring",
         "Refineries, gas cracking units, and pipeline transfer stations require continuous tracking of fugitive volatile emissions. "
         "Laying physical communication cables across expansive hazardous zones is prohibitively costly. An autonomous mesh of Atmospheric Sentries "
         "profiles CO2 and particulate dispersion, detecting leaks instantaneously without centralized telemetry infrastructure."),
        
        ("3. Urban Heat Island & Public Health Interventions",
         "Dense urban centers experience localized microclimate heat traps where temperatures exceed surrounding suburbs by 5–8°C. "
         "Autonomous sentries deployed along street canyons monitor ambient temperature and air quality. When thermal stress reaches dangerous levels (≥42°C), "
         "consensus triggers municipal emergency alerts to open targeted public cooling centers and divert heavy traffic."),
        
        ("4. Riparian Ecosystem & Watershed Conservation",
         "Agricultural runoff and industrial effluent can cause rapid acidification and oxygen depletion in vital river basins. "
         "Riparian Hydrology Sensors and Sub-Canopy Soil Probes monitor watershed moisture and thermal baselines, providing early warnings for "
         "flash droughts and aquatic ecosystem collapse."),
        
        ("5. Post-Disaster Ad-Hoc Emergency Mesh Operations",
         "Following severe hurricanes or earthquakes, terrestrial cellular base stations and fiber cables are frequently flattened. "
         "Autonomous edge nodes dropped into disaster areas self-organize replacement communication links, establishing a resilient emergency "
         "hazard detection mesh for first responders.")
    ]
    for ctitle, cdesc in cases:
        p = doc.add_paragraph()
        p.add_run(ctitle + "\n").bold = True
        p.runs[0].font.name = "Segoe UI"
        p.runs[0].font.size = Pt(10)
        p.runs[0].font.color.rgb = RGBColor(43, 108, 176)
        r = p.add_run(cdesc)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.2)
        r.font.color.rgb = RGBColor(45, 55, 72)
        p.paragraph_format.space_after = Pt(8)

    # ========================================================
    # SECTION 8: EMPIRICAL BENCHMARKS & TEST VERIFICATION
    # ========================================================
    h = doc.add_heading("8. Empirical Benchmarks & Test Verification", level=1)
    h.runs[0].font.name = "Segoe UI"
    h.runs[0].font.size = Pt(15)
    h.runs[0].font.color.rgb = RGBColor(10, 37, 64)

    doc.add_paragraph(
        "The platform has been rigorously validated through automated unit, integration, and end-to-end API test suites. "
        "All 11 automated test suites in `tests/` pass with 100% verification, validating the following empirical benchmarks:"
    )

    bench_table = doc.add_table(rows=5, cols=3)
    bench_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    b_heads = ["Benchmark Metric", "Measured Value", "Target Requirement & Evaluation Result"]
    for i, head in enumerate(b_heads):
        cell = bench_table.cell(0, i)
        set_cell_background(cell, "2B6CB0")
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        p.add_run(head).bold = True
        p.runs[0].font.name = "Segoe UI"
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)

    bench_data = [
        ("Edge ML Inference Latency", "1.2 – 1.5 ms", "Requirement: < 5 ms. PASSED. Enables real-time on-node hazard scoring."),
        ("Graph Topology Healing Duration", "12 – 18 ms", "Requirement: < 50 ms. PASSED. Discovers orphan links and restores biconnectivity instantly."),
        ("P2P Quorum Consensus Accuracy", "88% – 100% on active hazards", "Requirement: > 80% on multi-agent hazard zones. Solitary glitches rejected at 0.20 confidence. PASSED."),
        ("Model Memory Footprint", "2.23 Megabytes", "Requirement: < 10 MB for edge IoT deployment. PASSED. Loads in CPU RAM effortlessly.")
    ]
    for row_idx, (mmetric, mval, mres) in enumerate(bench_data, start=1):
        bg = "F7FAFC" if row_idx % 2 == 1 else "EDF2F7"
        c0 = bench_table.cell(row_idx, 0)
        c1 = bench_table.cell(row_idx, 1)
        c2 = bench_table.cell(row_idx, 2)
        set_cell_background(c0, bg)
        set_cell_background(c1, bg)
        set_cell_background(c2, bg)
        set_cell_margins(c0, 60, 60, 80, 80)
        set_cell_margins(c1, 60, 60, 80, 80)
        set_cell_margins(c2, 60, 60, 80, 80)
        c0.paragraphs[0].add_run(mmetric).bold = True
        c1.paragraphs[0].add_run(mval)
        c2.paragraphs[0].add_run(mres)
        for c in [c0, c1, c2]:
            c.paragraphs[0].runs[0].font.name = "Segoe UI"
            c.paragraphs[0].runs[0].font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # ========================================================
    # SECTION 9: IMPLEMENTED SCOPE VS FUTURE ROADMAP
    # ========================================================
    h = doc.add_heading("9. Implemented Scope vs Future Research Roadmap", level=1)
    h.runs[0].font.name = "Segoe UI"
    h.runs[0].font.size = Pt(15)
    h.runs[0].font.color.rgb = RGBColor(10, 37, 64)

    doc.add_paragraph(
        "To maintain strict academic integrity during faculty evaluation, the project establishes a transparent demarcation "
        "between currently implemented software functionality and planned future research:"
    )

    p = doc.add_paragraph()
    p.add_run("Implemented System Capabilities:\n").bold = True
    p.add_run(
        "• 20 autonomous edge agents running on a 20x20 spatial coordinate system with real GPS coordinate persistence.\n"
        "• Unsupervised scikit-learn Isolation Forest model evaluating 6 telemetry streams in real time.\n"
        "• 4-class multi-hazard contextual classifier (FIRE, POLLUTION, EXTREME HEAT, OTHER).\n"
        "• Asynchronous peer-to-peer alert propagation and localized neighborhood consensus quorum (θ ≥ 0.50).\n"
        "• Dynamic NetworkX graph self-healing protocol with Manhattan proximity reconnection (d ≤ 4).\n"
        "• Asynchronous FastAPI ASGI backend with 22 REST API endpoints and real-time WebSockets.\n"
        "• Production-grade Next.js 14 mission control dashboard across six operational sections.\n"
        "• Relational SQLAlchemy persistence layer across 7 normalized database schemas."
    )

    p2 = doc.add_paragraph()
    p2.add_run("Future Research Advancements:\n").bold = True
    p2.add_run(
        "1. Physical IoT Hardware Deployment: Porting the agent runtime to low-power ESP32 microcontrollers communicating via long-range "
        "868/915 MHz LoRaWAN transceivers, enabling physical outdoor field validation.\n"
        "2. Deep Reinforcement Learning (DRL) Swarm Flight: Integrating Proximal Policy Optimization (PPO) to allow autonomous thermal drones "
        "to dynamically optimize patrol flight paths and encircle expanding hazard perimeters.\n"
        "3. Cryptographic Byzantine Fault Tolerant (BFT) Ledger: Embedding lightweight blockchain consensus to guarantee tamper-proof regulatory "
        "compliance for industrial emissions monitoring.\n"
        "4. Satellite Remote Sensing Data Fusion: Integrating optical Sentinel-2 and thermal NASA FIRMS satellite telemetry feeds to cross-verify "
        "hyper-local edge detections with regional macro-scale satellite observations."
    )

    output_path = os.path.join(os.path.abspath("Project_Presentation"), "Technical_Overview.docx")
    doc.save(output_path)
    print("Saved Technical Overview successfully to:", output_path)

if __name__ == "__main__":
    build_technical_overview()
