import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# ============================================================
# DESIGN SYSTEM CONSTANTS
# ============================================================
FONT_HEADING = "Segoe UI"
FONT_BODY = "Segoe UI"

COLOR_BG = RGBColor(7, 11, 20)           # #070B14 Dark Navy
COLOR_CARD = RGBColor(14, 23, 38)        # #0E1726 Deep Slate Card
COLOR_CARD_BORDER = RGBColor(30, 41, 59) # #1E293B Card Outline
COLOR_CYAN = RGBColor(0, 245, 212)       # #00F5D4 Electric Cyan
COLOR_BLUE = RGBColor(56, 189, 248)      # #38BDF8 Electric Sky Blue
COLOR_PURPLE = RGBColor(168, 85, 247)    # #A855F7 Violet / Purple
COLOR_GREEN = RGBColor(16, 185, 129)     # #10B981 Emerald Green
COLOR_ROSE = RGBColor(244, 63, 94)       # #F43F5E Coral / Rose
COLOR_AMBER = RGBColor(245, 158, 11)     # #F59E0B Warm Amber
COLOR_WHITE = RGBColor(248, 250, 252)    # #F8FAFC Pure White
COLOR_SILVER = RGBColor(203, 213, 225)   # #CBD5E1 Light Silver
COLOR_MUTED = RGBColor(148, 163, 184)    # #94A3B8 Muted Slate

def set_shape_flat(shape, fill_color, line_color=None, line_width=1.0):
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_width)
    else:
        shape.line.fill.background()

def create_base_slide(prs, category_text, title_text):
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    set_shape_flat(bg, COLOR_BG)

    # Top Category Badge & Line
    if category_text:
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8.0), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = FONT_HEADING
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_CYAN

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.65))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE

    # Subtle bottom slide divider
    divider = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(11.733), Inches(0.02))
    set_shape_flat(divider, COLOR_CARD_BORDER)

    # Slide Footer
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.1), Inches(11.733), Inches(0.3))
    tf_foot = footer_box.text_frame
    tf_foot.margin_left = tf_foot.margin_top = tf_foot.margin_right = tf_foot.margin_bottom = 0
    p_foot = tf_foot.paragraphs[0]
    p_foot.text = "Self-Organizing Multi-Agent Systems for Decentralized Environmental Monitoring  |  Academic & Technical Viva Defense"
    p_foot.font.name = FONT_BODY
    p_foot.font.size = Pt(8.5)
    p_foot.font.color.rgb = COLOR_MUTED

    return slide

def add_card(slide, left, top, width, height, border_color=COLOR_CARD_BORDER, fill_color=COLOR_CARD, border_width=1.0):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.adjustments[0] = 0.05
    set_shape_flat(card, fill_color, border_color, border_width)
    return card

# Initialize Presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

output_dir = os.path.abspath("Project_Presentation")
arch_img_path = os.path.join(output_dir, "Project_Architecture.png")
flow_img_path = os.path.join(output_dir, "Agent_Workflow.png")

# ============================================================
# SLIDE 1: TITLE SLIDE
# ============================================================
slide1 = prs.slides.add_slide(prs.slide_layouts[6])
bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
set_shape_flat(bg1, COLOR_BG)

# Title container
tbox = slide1.shapes.add_textbox(Inches(1.0), Inches(1.4), Inches(11.333), Inches(4.5))
tf1 = tbox.text_frame
tf1.word_wrap = True

p = tf1.paragraphs[0]
p.text = "ACADEMIC & TECHNICAL VIVA DEFENSE"
p.font.name = FONT_HEADING
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p.space_after = Pt(12)

p = tf1.add_paragraph()
p.text = "Self-Organizing Multi-Agent Systems for\nDecentralized Environmental Monitoring"
p.font.name = FONT_HEADING
p.font.size = Pt(32)
p.font.bold = True
p.font.color.rgb = COLOR_WHITE
p.space_after = Pt(14)

p = tf1.add_paragraph()
p.text = "Autonomous Edge Sensing, Machine Learning Anomaly Detection, P2P Consensus & Self-Healing Network Mesh"
p.font.name = FONT_BODY
p.font.size = Pt(14)
p.font.color.rgb = COLOR_BLUE
p.space_after = Pt(24)

p = tf1.add_paragraph()
p.text = "Technologies: Python 3.11  •  FastAPI  •  Scikit-Learn  •  Next.js 14  •  NetworkX  •  SQLAlchemy  •  WebSockets"
p.font.name = FONT_BODY
p.font.size = Pt(11)
p.font.color.rgb = COLOR_MUTED

# Metadata Cards at bottom
meta_card1 = add_card(slide1, 1.0, 5.4, 3.5, 1.3, border_color=COLOR_BLUE)
tx1 = slide1.shapes.add_textbox(Inches(1.15), Inches(5.5), Inches(3.2), Inches(1.1))
tf = tx1.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "PROJECT ARCHITECTURE"
p.font.size = Pt(9.5)
p.font.bold = True
p.font.color.rgb = COLOR_BLUE
p = tf.add_paragraph()
p.text = "Decentralized P2P Multi-Agent Grid\n6 Telemetry Channels  •  Sub-20ms Healing"
p.font.size = Pt(9)
p.font.color.rgb = COLOR_SILVER

meta_card2 = add_card(slide1, 4.9, 5.4, 3.5, 1.3, border_color=COLOR_CYAN)
tx2 = slide1.shapes.add_textbox(Inches(5.05), Inches(5.5), Inches(3.2), Inches(1.1))
tf = tx2.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "EVALUATION SCOPE"
p.font.size = Pt(9.5)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p = tf.add_paragraph()
p.text = "College Project & Faculty Viva\nFull Code Verification (11/11 Tests Passed)"
p.font.size = Pt(9)
p.font.color.rgb = COLOR_SILVER

meta_card3 = add_card(slide1, 8.8, 5.4, 3.5, 1.3, border_color=COLOR_PURPLE)
tx3 = slide1.shapes.add_textbox(Inches(8.95), Inches(5.5), Inches(3.2), Inches(1.1))
tf = tx3.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "KEY RESEARCH ADVANCEMENT"
p.font.size = Pt(9.5)
p.font.bold = True
p.font.color.rgb = COLOR_PURPLE
p = tf.add_paragraph()
p.text = "Zero Cloud Dependency in Crisis\nSpatial Neighborhood Consensus Quorum"
p.font.size = Pt(9)
p.font.color.rgb = COLOR_SILVER


# ============================================================
# SLIDE 2: INTRODUCTION
# ============================================================
slide2 = create_base_slide(prs, "System Overview", "Introduction: Autonomous Decentralized Environmental Intelligence")

# 3 Pillar Cards
card1 = add_card(slide2, 0.8, 1.6, 3.65, 4.3, border_color=COLOR_CYAN)
tb1 = slide2.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.25), Inches(3.9))
tf1 = tb1.text_frame
tf1.word_wrap = True
p = tf1.paragraphs[0]
p.text = "WHAT IS THE PROJECT?"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p.space_after = Pt(10)
p = tf1.add_paragraph()
p.text = "An AI-powered, decentralized environmental monitoring platform composed of autonomous edge agents deployed over a spatial coordinate grid."
p.font.size = Pt(10)
p.font.color.rgb = COLOR_SILVER
p.space_after = Pt(10)
p = tf1.add_paragraph()
p.text = "Each node acts as an intelligent physical probe tracking 6 telemetry streams: Temperature, Humidity, Smoke, CO2, AQI, and Soil Moisture."
p.font.size = Pt(9.5)
p.font.color.rgb = COLOR_MUTED

card2 = add_card(slide2, 4.85, 1.6, 3.65, 4.3, border_color=COLOR_BLUE)
tb2 = slide2.shapes.add_textbox(Inches(5.05), Inches(1.8), Inches(3.25), Inches(3.9))
tf2 = tb2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "WHAT DOES IT DO?"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_BLUE
p.space_after = Pt(10)
p = tf2.add_paragraph()
p.text = "Executes local Machine Learning inference (Isolation Forest) directly on the node to detect anomalies without uploading raw streams to a central cloud."
p.font.size = Pt(10)
p.font.color.rgb = COLOR_SILVER
p.space_after = Pt(10)
p = tf2.add_paragraph()
p.text = "Autonomously coordinates peer-to-peer alert broadcasts, evaluates local consensus with neighbors, and heals network partitions when nodes physically fail."
p.font.size = Pt(9.5)
p.font.color.rgb = COLOR_MUTED

card3 = add_card(slide2, 8.9, 1.6, 3.65, 4.3, border_color=COLOR_PURPLE)
tb3 = slide2.shapes.add_textbox(Inches(9.1), Inches(1.8), Inches(3.25), Inches(3.9))
tf3 = tb3.text_frame
tf3.word_wrap = True
p = tf3.paragraphs[0]
p.text = "WHY IS IT IMPORTANT?"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_PURPLE
p.space_after = Pt(10)
p = tf3.add_paragraph()
p.text = "Traditional centralized telemetry systems fail catastrophically during disasters (wildfires, pipeline leaks) due to telecom bottlenecks and single points of failure."
p.font.size = Pt(10)
p.font.color.rgb = COLOR_SILVER
p.space_after = Pt(10)
p = tf3.add_paragraph()
p.text = "By shifting intelligence and consensus to the physical edge, the system guarantees 100% operational continuity during severe infrastructure blackouts."
p.font.size = Pt(9.5)
p.font.color.rgb = COLOR_MUTED

# Bottom Stat Bar
stat_card = add_card(slide2, 0.8, 6.1, 11.75, 0.8, border_color=COLOR_GREEN)
stb = slide2.shapes.add_textbox(Inches(1.0), Inches(6.15), Inches(11.35), Inches(0.7))
stf = stb.text_frame
stf.word_wrap = True
p = stf.paragraphs[0]
p.text = "CORE METRICS AT A GLANCE:   6 Telemetry Sensors/Node   |   <20ms Graph Topology Healing   |   θ ≥ 0.50 Quorum Threshold   |   22 REST API Endpoints"
p.font.size = Pt(10.5)
p.font.bold = True
p.font.color.rgb = COLOR_GREEN


# ============================================================
# SLIDE 3: PROBLEM STATEMENT
# ============================================================
slide3 = create_base_slide(prs, "Industry Context & Motivation", "Problem Statement: Critical Shortcomings of Centralized Monitoring")

# Left Column: The Real-World Crisis
pcard1 = add_card(slide3, 0.8, 1.6, 5.65, 5.2, border_color=COLOR_ROSE)
ptb1 = slide3.shapes.add_textbox(Inches(1.05), Inches(1.8), Inches(5.15), Inches(4.8))
ptf1 = ptb1.text_frame
ptf1.word_wrap = True
p = ptf1.paragraphs[0]
p.text = "THE REAL-WORLD CRISIS ENVIRONMENT"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_ROSE
p.space_after = Pt(12)

bullets_left = [
    ("Rapid Catastrophic Hazards: ", "Wildfires, toxic chemical breaches, and pipeline emissions expand exponentially within minutes, demanding instantaneous local response."),
    ("Infrastructure Collapse: ", "High-heat fires and natural disasters incinerate central cellular towers, fiber-optic lines, and satellite uplink base stations."),
    ("Severe Bandwidth Bottlenecks: ", "Transmitting high-frequency raw multi-sensor telemetry across hundreds of nodes clogs scarce wireless spectrum."),
    ("Costly False Alarms: ", "Sensor drift or hardware glitches in single centralized sensors trigger expensive, disruptive emergency team deployments.")
]
for title, desc in bullets_left:
    p = ptf1.add_paragraph()
    p.text = "• " + title
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_after = Pt(4)
    p = ptf1.add_paragraph()
    p.text = "  " + desc
    p.font.size = Pt(9.0)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(8)

# Right Column: Centralized System Vulnerabilities
pcard2 = add_card(slide3, 6.9, 1.6, 5.65, 5.2, border_color=COLOR_AMBER)
ptb2 = slide3.shapes.add_textbox(Inches(7.15), Inches(1.8), Inches(5.15), Inches(4.8))
ptf2 = ptb2.text_frame
ptf2.word_wrap = True
p = ptf2.paragraphs[0]
p.text = "LIMITATIONS OF MONOLITHIC CLOUD ARCHITECTURES"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_AMBER
p.space_after = Pt(12)

bullets_right = [
    ("Single Point of Failure (SPOF): ", "If the centralized cloud aggregator or ingress gateway disconnects, the entire monitoring perimeter goes completely blind."),
    ("Cloud Processing Latency: ", "Ingestion, queuing, cloud ML inference, and alert relay introduce seconds of critical delay when milliseconds matter."),
    ("No Local Consensus: ", "Central systems lack spatial proximity awareness; they process data in isolation rather than cross-verifying with proximate physical neighbors."),
    ("Rigid, Fragile Topologies: ", "Standard IoT star topologies disconnect all downstream sensors when a single parent relay station is destroyed.")
]
for title, desc in bullets_right:
    p = ptf2.add_paragraph()
    p.text = "• " + title
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_after = Pt(4)
    p = ptf2.add_paragraph()
    p.text = "  " + desc
    p.font.size = Pt(9.0)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(8)


# ============================================================
# SLIDE 4: PROPOSED SOLUTION
# ============================================================
slide4 = create_base_slide(prs, "Innovation & Approach", "Proposed Solution: Decentralized Edge Intelligence & Dynamic Topology")

# 3 Solution Cards
sol_cards = [
    ("1. ON-NODE EDGE AI", COLOR_CYAN, 0.8, [
        ("Autonomous Sensing:", "Continuous edge tracking of 6 environmental telemetry streams."),
        ("Isolation Forest Inference:", "Trained unsupervised ML model runs locally on node; computes decision score in <2ms."),
        ("Contextual Event Classifier:", "Categorizes anomalies into FIRE, POLLUTION, or EXTREME HEAT without cloud consultation.")
    ]),
    ("2. P2P NEIGHBOR CONSENSUS", COLOR_BLUE, 4.85, [
        ("Localized Alert Broadcast:", "Anomalous agents broadcast alert payloads strictly to active proximate neighbors."),
        ("Weighted Spatial Quorum:", "Confidence = Agreeing Neighbors / Total Active Neighborhood."),
        ("False Alarm Rejection:", "Threshold gate (θ ≥ 0.50) guarantees solitary sensor glitches are rejected instantly.")
    ]),
    ("3. SELF-ORGANIZING MESH", COLOR_PURPLE, 8.9, [
        ("Dynamic Failure Detection:", "Immediate recognition of physical node destruction or dead communication links."),
        ("Proximity Link Restoration:", "Searches active orphan nodes within Manhattan proximity: D(A,B) = |Δx| + |Δy| ≤ 4."),
        ("Sub-20ms Graph Healing:", "Restores global biconnectivity autonomously before network partitions escalate.")
    ])
]

for title, color, left, items in sol_cards:
    sc = add_card(slide4, left, 1.6, 3.65, 5.2, border_color=color)
    stb = slide4.shapes.add_textbox(Inches(left + 0.2), Inches(1.8), Inches(3.25), Inches(4.8))
    stf = stb.text_frame
    stf.word_wrap = True
    p = stf.paragraphs[0]
    p.text = title
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = color
    p.space_after = Pt(14)
    
    for heading, desc in items:
        p = stf.add_paragraph()
        p.text = heading
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p = stf.add_paragraph()
        p.text = desc
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_SILVER
        p.space_after = Pt(10)


# ============================================================
# SLIDE 5: PROJECT OBJECTIVES
# ============================================================
slide5 = create_base_slide(prs, "Scope & Deliverables", "Project Objectives: Primary Goals, Secondary Features & Targets")

# Left: Primary Objectives
oc1 = add_card(slide5, 0.8, 1.6, 5.65, 5.2, border_color=COLOR_CYAN)
otb1 = slide5.shapes.add_textbox(Inches(1.05), Inches(1.8), Inches(5.15), Inches(4.8))
otf1 = otb1.text_frame
otf1.word_wrap = True
p = otf1.paragraphs[0]
p.text = "PRIMARY SYSTEM OBJECTIVES"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p.space_after = Pt(10)

prim_items = [
    ("1. Autonomous 6-Sensor Telemetry Grid: ", "Deploy multi-agent sensor nodes monitoring Temperature, Humidity, Smoke Density, CO2, AQI, and Soil Moisture."),
    ("2. Edge Anomaly Detection: ", "Embed an Isolation Forest model (200 trees, 0.05 contamination) to perform unsupervised anomaly scoring locally."),
    ("3. Contextual Hazard Classification: ", "Implement rule-based classification mapping multidimensional anomalies to FIRE, POLLUTION, EXTREME HEAT, or OTHER."),
    ("4. Peer-to-Peer Consensus Mechanism: ", "Build localized neighbor voting protocol to calculate quorum confidence and confirm hazard incidents."),
    ("5. Autonomous Topology Self-Organization: ", "Develop Manhattan proximity graph restructuring using NetworkX to reconnect severed mesh nodes in <20ms.")
]
for head, body in prim_items:
    p = otf1.add_paragraph()
    p.text = head
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = otf1.add_paragraph()
    p.text = body
    p.font.size = Pt(8.8)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)

# Right: Secondary & Expected Outcomes
oc2 = add_card(slide5, 6.9, 1.6, 5.65, 5.2, border_color=COLOR_BLUE)
otb2 = slide5.shapes.add_textbox(Inches(7.15), Inches(1.8), Inches(5.15), Inches(4.8))
otf2 = otb2.text_frame
otf2.word_wrap = True
p = otf2.paragraphs[0]
p.text = "SECONDARY OBJECTIVES & TARGET BENCHMARKS"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_BLUE
p.space_after = Pt(10)

sec_items = [
    ("Full Mission Control Web UI: ", "Develop a responsive Next.js 14 / TypeScript dashboard across 6 operational domains (Command Center, Agents, Network, Incidents, Analytics, History)."),
    ("Asynchronous REST & WebSocket Server: ", "Implement FastAPI backend with 22 REST endpoints and real-time bidirectional WebSocket state streaming."),
    ("Relational Persistence Schema: ", "Design 7 SQLAlchemy database tables logging node health, incident history, consensus evidence, and topology changes."),
    ("Empirical Target 1 — Latency: ", "Achieve edge inference <2ms and network partition recovery <20ms."),
    ("Empirical Target 2 — Quorum Accuracy: ", "Ensure incident detection confidence exceeds 85% during active multi-agent hazards while rejecting solitary sensor noise.")
]
for head, body in sec_items:
    p = otf2.add_paragraph()
    p.text = head
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = otf2.add_paragraph()
    p.text = body
    p.font.size = Pt(8.8)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)


# ============================================================
# SLIDE 6: SYSTEM ARCHITECTURE
# ============================================================
slide6 = create_base_slide(prs, "System Design & Decomposition", "System Architecture: End-to-End Multilayer Technical Blueprint")

# Insert generated architecture image if available
if os.path.exists(arch_img_path):
    slide6.shapes.add_picture(arch_img_path, Inches(0.8), Inches(1.5), Inches(8.5), Inches(5.3))
    
    # Right-hand explanation panel
    arch_panel = add_card(slide6, 9.5, 1.5, 3.05, 5.3, border_color=COLOR_CYAN)
    aptb = slide6.shapes.add_textbox(Inches(9.65), Inches(1.65), Inches(2.75), Inches(5.0))
    aptf = aptb.text_frame
    aptf.word_wrap = True
    p = aptf.paragraphs[0]
    p.text = "ARCHITECTURAL LAYERS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p.space_after = Pt(8)

    layer_notes = [
        ("1. Web Presentation", "Next.js 14, React 18, Leaflet GIS, Recharts SVG charts, real-time WebSocket HUD."),
        ("2. API & Orchestration", "FastAPI server, Uvicorn ASGI, 22 REST endpoints, WebSocketManager broadcast."),
        ("3. Edge Intelligence Triad", "• AI Engine: Isolation Forest\n• Agent Engine: P2P Consensus\n• Network Engine: NetworkX graph"),
        ("4. Persistent Storage", "SQLAlchemy 2.0 ORM with SQLite (local) / PostgreSQL (production); 7 relational tables.")
    ]
    for ltitle, ldesc in layer_notes:
        p = aptf.add_paragraph()
        p.text = ltitle
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p = aptf.add_paragraph()
        p.text = ldesc
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_SILVER
        p.space_after = Pt(8)


# ============================================================
# SLIDE 7: MULTI-AGENT ARCHITECTURE
# ============================================================
slide7 = create_base_slide(prs, "Core Theoretical Paradigm", "Multi-Agent Architecture: Decentralized Peer-to-Peer vs Centralized")

# Top row: Why MAS?
mtop = add_card(slide7, 0.8, 1.6, 11.75, 1.6, border_color=COLOR_PURPLE)
mtb = slide7.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(11.35), Inches(1.3))
mtf = mtb.text_frame
mtf.word_wrap = True
p = mtf.paragraphs[0]
p.text = "WHY A MULTI-AGENT SYSTEM (MAS) INSTEAD OF A SINGLE MONOLITHIC MODEL?"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_PURPLE
p.space_after = Pt(6)
p = mtf.add_paragraph()
p.text = "A single centralized model requires continuous telemetry transmission from every sensor to the cloud. In contrast, Multi-Agent Systems distribute autonomy to the edge. Each node perceives local conditions, computes inferences independently, and communicates strictly with proximate peers. If an agent fails or is destroyed, the surrounding collective autonomously reconfigures without systemic collapse."
p.font.size = Pt(9.5)
p.font.color.rgb = COLOR_SILVER

# Bottom comparison: Centralized Orchestration vs Decentralized MAS
mc1 = add_card(slide7, 0.8, 3.4, 5.65, 3.4, border_color=COLOR_ROSE)
mctb1 = slide7.shapes.add_textbox(Inches(1.05), Inches(3.55), Inches(5.15), Inches(3.1))
mctf1 = mctb1.text_frame
mctf1.word_wrap = True
p = mctf1.paragraphs[0]
p.text = "TRADITIONAL CENTRALIZED ORCHESTRATION"
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = COLOR_ROSE
p.space_after = Pt(8)
cent_points = [
    ("Master-Slave Dependency: ", "Edge devices are dumb sensors; cloud orchestrator controls all logic."),
    ("Communication Flooding: ", "Raw continuous data transfers congest wireless bandwidth."),
    ("Fragile Point of Failure: ", "Ingress cloud outage disables entire regional monitoring."),
    ("No Local Consensus: ", "Cannot verify spatial coherence between adjacent sensors.")
]
for h, d in cent_points:
    p = mctf1.add_paragraph()
    p.text = "✗ " + h + d
    p.font.size = Pt(8.8)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(4)

mc2 = add_card(slide7, 6.9, 3.4, 5.65, 3.4, border_color=COLOR_GREEN)
mctb2 = slide7.shapes.add_textbox(Inches(7.15), Inches(3.55), Inches(5.15), Inches(3.1))
mctf2 = mctb2.text_frame
mctf2.word_wrap = True
p = mctf2.paragraphs[0]
p.text = "OUR DECENTRALIZED MULTI-AGENT MESH"
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = COLOR_GREEN
p.space_after = Pt(8)
mas_points = [
    ("Autonomous Edge Agents: ", "Each agent runs its own ML inference and decision functions."),
    ("Sparse Alert Transmission: ", "Communication occurs only when statistically anomalous hazards occur."),
    ("Zero Cloud Dependency: ", "Detection and consensus succeed even during complete Internet blackouts."),
    ("Autonomous Topology Healing: ", "Mesh dynamically repairs severed links in under 20ms.")
]
for h, d in mas_points:
    p = mctf2.add_paragraph()
    p.text = "✓ " + h + d
    p.font.size = Pt(8.8)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(4)


# ============================================================
# SLIDE 8: DIFFERENT TYPES OF AGENTS & ROLES
# ============================================================
slide8 = create_base_slide(prs, "Agent Taxonomy & Roles", "Implemented Agent Types: Functional Roles, Telemetry & Decision Engine")

agent_roles = [
    ("Canopy Thermal Drone", COLOR_ROSE, 0.8, 
     "Aerial thermal & combustion profiling", 
     "Temp, Smoke, Battery", 
     "High-temperature IR gradient & smoke density", 
     "Combat fire spread; patrol transect"),
    
    ("Atmospheric Sentry Node", COLOR_BLUE, 3.2, 
     "Greenhouse gas & aerosol monitoring", 
     "CO2, AQI, Smoke", 
     "CO2 thresholding (≥800ppm) & particulate AQI", 
     "Plume trajectory & toxic air warnings"),
    
    ("Riparian Hydrology Sensor", COLOR_CYAN, 5.6, 
     "Watershed & stream hydrological flux", 
     "Soil Moisture, Humidity, Temp", 
     "Soil dehydration & riparian thermal baseline", 
     "Flash drought & wetland boundary alerts"),
    
    ("Sub-Canopy Soil Probe", COLOR_AMBER, 8.0, 
     "Subterranean organic burn & microbial heat", 
     "Soil Moisture, Temp, Smoke", 
     "Root-level smoldering & soil dryness (<25%)", 
     "Underground fire & soil degradation tracking"),
    
    ("Autonomous Mesh Relay", COLOR_PURPLE, 10.4, 
     "P2P route routing & consensus bridge", 
     "Neighbor links, Connectivity, Latency", 
     "Manhattan distance optimization (d ≤ 4)", 
     "Biconnectivity maintenance & alert relay")
]

for title, color, left, desc, in_rec, proc, role in agent_roles:
    ac = add_card(slide8, left, 1.6, 2.15, 5.2, border_color=color)
    atb = slide8.shapes.add_textbox(Inches(left + 0.1), Inches(1.75), Inches(1.95), Inches(4.9))
    atf = atb.text_frame
    atf.word_wrap = True
    
    p = atf.paragraphs[0]
    p.text = title
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = color
    p.space_after = Pt(8)

    p = atf.add_paragraph()
    p.text = desc
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(10)

    p = atf.add_paragraph()
    p.text = "INPUT SENSORS:"
    p.font.size = Pt(8.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = atf.add_paragraph()
    p.text = in_rec
    p.font.size = Pt(7.8)
    p.font.color.rgb = COLOR_MUTED
    p.space_after = Pt(8)

    p = atf.add_paragraph()
    p.text = "DECISION LOGIC:"
    p.font.size = Pt(8.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = atf.add_paragraph()
    p.text = proc
    p.font.size = Pt(7.8)
    p.font.color.rgb = COLOR_MUTED
    p.space_after = Pt(8)

    p = atf.add_paragraph()
    p.text = "MISSION ASSIGNMENT:"
    p.font.size = Pt(8.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = atf.add_paragraph()
    p.text = role
    p.font.size = Pt(7.8)
    p.font.color.rgb = COLOR_MUTED


# ============================================================
# SLIDE 9: AGENT-TO-AGENT COMMUNICATION
# ============================================================
slide9 = create_base_slide(prs, "Peer-to-Peer Protocol", "Agent-to-Agent Communication & Neighborhood Consensus Mechanics")

# Left Column: P2P Communication Protocol
cc1 = add_card(slide9, 0.8, 1.6, 5.65, 5.2, border_color=COLOR_CYAN)
ctb1 = slide9.shapes.add_textbox(Inches(1.05), Inches(1.8), Inches(5.15), Inches(4.8))
ctf1 = ctb1.text_frame
ctf1.word_wrap = True
p = ctf1.paragraphs[0]
p.text = "COMMUNICATION PROTOCOL SPECIFICATION"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p.space_after = Pt(10)

p2p_details = [
    ("CommunicationManager Architecture: ", "Asynchronous peer message dispatch. When an agent detects an anomaly, it avoids flood broadcasting and directly alerts active proximate neighbors."),
    ("Alert Payload Schema: ", "Serialized JSON dictionary transmitting:\n• type: 'ENVIRONMENTAL_ALERT'\n• event: Hazard classification (FIRE, POLLUTION, EXTREME_HEAT)\n• score: Isolation Forest decision score (float)"),
    ("Bi-directional Handshake: ", "Neighbor nodes receive the message, append it to their local message buffer, and immediately trigger local evidence analysis."),
    ("Zero Global Master: ", "No central broker (e.g. MQTT or Kafka) is mandatory for consensus; messages pass directly between local graph vertices.")
]
for head, desc in p2p_details:
    p = ctf1.add_paragraph()
    p.text = head
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = ctf1.add_paragraph()
    p.text = desc
    p.font.size = Pt(8.8)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)

# Right Column: Consensus Algorithm
cc2 = add_card(slide9, 6.9, 1.6, 5.65, 5.2, border_color=COLOR_GREEN)
ctb2 = slide9.shapes.add_textbox(Inches(7.15), Inches(1.8), Inches(5.15), Inches(4.8))
ctf2 = ctb2.text_frame
ctf2.word_wrap = True
p = ctf2.paragraphs[0]
p.text = "LOCAL NEIGHBORHOOD CONSENSUS ALGORITHM"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_GREEN
p.space_after = Pt(10)

p = ctf2.add_paragraph()
p.text = "Mathematical Quorum Formula:"
p.font.size = Pt(10)
p.font.bold = True
p.font.color.rgb = COLOR_WHITE

p = ctf2.add_paragraph()
p.text = "Confidence = (Count of Agreeing Neighbors) / (Total Active Local Neighborhood)"
p.font.size = Pt(9.5)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p.space_after = Pt(8)

consensus_steps = [
    ("Step 1 — Local Evidence Gathering: ", "The initiating agent polls all active neighbors within graph distance d ≤ 4. Each node contributes its independent AI inference."),
    ("Step 2 — Quorum Evaluation: ", "If the dominant non-normal event count reaches threshold θ ≥ 0.50, consensus is CONFIRMED."),
    ("Step 3 — False Alarm Suppression: ", "If a single sensor drifts due to hardware failure while neighbors report NORMAL, confidence falls below 0.50 and the alert is rejected as UNCERTAIN."),
    ("Step 4 — Persistence: ", "Confirmed incidents are committed to the relational database with full voter distribution logs.")
]
for head, desc in consensus_steps:
    p = ctf2.add_paragraph()
    p.text = head
    p.font.size = Pt(9.2)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = ctf2.add_paragraph()
    p.text = desc
    p.font.size = Pt(8.6)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)


# ============================================================
# SLIDE 10: COMPLETE SYSTEM WORKFLOW
# ============================================================
slide10 = create_base_slide(prs, "Operational Flow & Execution", "Complete System Workflow: 8-Stage Sensing-to-Healing Lifecycle")

if os.path.exists(flow_img_path):
    slide10.shapes.add_picture(flow_img_path, Inches(0.8), Inches(1.5), Inches(8.5), Inches(5.3))
    
    # Workflow step explanation card
    wf_panel = add_card(slide10, 9.5, 1.5, 3.05, 5.3, border_color=COLOR_PURPLE)
    wftb = slide10.shapes.add_textbox(Inches(9.65), Inches(1.65), Inches(2.75), Inches(5.0))
    wftf = wftb.text_frame
    wftf.word_wrap = True
    p = wftf.paragraphs[0]
    p.text = "LIFECYCLE SUMMARY"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p.space_after = Pt(8)

    w_steps = [
        ("1. Sensing & Telemetry", "Continuous 6-sensor sampling at each physical edge node."),
        ("2. ML Anomaly Scoring", "Isolation Forest computes local decision function score."),
        ("3. Event Classification", "Maps anomaly patterns to FIRE, POLLUTION, or HEAT."),
        ("4. P2P Alert Broadcast", "Direct localized transmission to proximate active peers."),
        ("5. Local Consensus", "Quorum calculation validates hazard with confidence θ ≥ 0.50."),
        ("6. Escalation & Log", "Committed to SQLite/PostgreSQL and pushed to Web HUD."),
        ("7. Node Loss Simulation", "Simulated destruction isolates severed edges."),
        ("8. Self-Healing Mesh", "Manhattan reconnect (d ≤ 4) restores mesh in <20ms.")
    ]
    for stitle, sdesc in w_steps:
        p = wftf.add_paragraph()
        p.text = stitle + ": "
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p = wftf.add_paragraph()
        p.text = sdesc
        p.font.size = Pt(7.8)
        p.font.color.rgb = COLOR_SILVER
        p.space_after = Pt(4)


# ============================================================
# SLIDE 11: TECHNOLOGIES & TOOLS USED
# ============================================================
slide11 = create_base_slide(prs, "Full Technology Stack", "Technologies & Tools Used: Architectural Stack & Justifications")

tech_categories = [
    ("Languages", "Python 3.11\nTypeScript 5.6", "Python for ML, scientific computing & graph processing; TypeScript for strict type-safe UI architecture."),
    ("Frontend UI", "Next.js 14 (App Router)\nReact 18 • Tailwind CSS\nLeaflet GIS • Recharts", "Modern React server/client components, high-performance GIS geospatial maps, and responsive SVG telemetry charts."),
    ("Backend Server", "FastAPI 0.141\nUvicorn ASGI Server\nWebSockets (RFC 6455)", "High-throughput asynchronous ASGI web server with automatic OpenAPI schemas and low-latency bidirectional socket push."),
    ("AI / ML Engine", "Scikit-Learn 1.9\nIsolationForest\nPandas • Joblib", "Unsupervised anomaly detection in 6-dimensional feature space; serialized 2.2MB model loads instantly on edge hardware."),
    ("Graph & Mesh", "NetworkX 3.6\nManhattan Distance Metric", "Mathematical graph topology algorithms, node connectivity checks, and dynamic proximity-based edge reorganization."),
    ("Database & ORM", "SQLAlchemy 2.0 ORM\nSQLite 3 • PostgreSQL", "ACID-compliant relational persistence with 7 tables; portable embedded SQLite for development and PostgreSQL for production.")
]

for idx, (cat, stack, just) in enumerate(tech_categories):
    col = idx % 3
    row = idx // 3
    left = 0.8 + col * 4.05
    top = 1.6 + row * 2.7
    
    border_c = [COLOR_CYAN, COLOR_BLUE, COLOR_PURPLE, COLOR_ROSE, COLOR_AMBER, COLOR_GREEN][idx]
    add_card(slide11, left, top, 3.65, 2.5, border_color=border_c)
    
    tb = slide11.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.15), Inches(3.35), Inches(2.2))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = cat.upper()
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = border_c
    p.space_after = Pt(4)

    p = tf.add_paragraph()
    p.text = stack
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_after = Pt(6)

    p = tf.add_paragraph()
    p.text = just
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_SILVER


# ============================================================
# SLIDE 12: CORE ALGORITHMS & TECHNICAL IMPLEMENTATION
# ============================================================
slide12 = create_base_slide(prs, "Algorithmic Formulations", "Core Algorithms: Isolation Forest, Rule Classifier & Network Recovery")

# Algorithm 1: Isolation Forest
a1 = add_card(slide12, 0.8, 1.6, 3.65, 5.2, border_color=COLOR_CYAN)
atb1 = slide12.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.25), Inches(4.8))
atf1 = atb1.text_frame
atf1.word_wrap = True
p = atf1.paragraphs[0]
p.text = "1. ISOLATION FOREST ML"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p.space_after = Pt(8)
if_notes = [
    ("Mathematical Basis: ", "Isolates observations by randomly selecting a feature and a split value between min and max."),
    ("Path Length Anomaly: ", "Outliers require fewer splits to isolate (shallow tree depth) compared to clustered normal points."),
    ("Hyperparameters: ", "• n_estimators = 200\n• contamination = 0.05\n• random_state = 42"),
    ("Execution: ", "data[FEATURES] -> model.predict() (+1: Normal, -1: Anomaly) & decision_function() score.")
]
for h, d in if_notes:
    p = atf1.add_paragraph()
    p.text = h
    p.font.size = Pt(9.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = atf1.add_paragraph()
    p.text = d
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)

# Algorithm 2: Event Classifier
a2 = add_card(slide12, 4.85, 1.6, 3.65, 5.2, border_color=COLOR_ROSE)
atb2 = slide12.shapes.add_textbox(Inches(5.05), Inches(1.8), Inches(3.25), Inches(4.8))
atf2 = atb2.text_frame
atf2.word_wrap = True
p = atf2.paragraphs[0]
p.text = "2. CONTEXTUAL CLASSIFIER"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_ROSE
p.space_after = Pt(8)
rule_notes = [
    ("Multi-Hazard Rules: ", "Executes when Isolation Forest flags condition as ANOMALY."),
    ("FIRE Class: ", "Temp ≥ 40°C  AND\nHumidity ≤ 30%  AND\nSmoke Density ≥ 0.50"),
    ("POLLUTION Class: ", "CO2 ≥ 800 ppm  AND\nAir Quality (AQI) ≥ 120  AND\nSmoke Density ≥ 0.30"),
    ("EXTREME HEAT Class: ", "Ambient Temp ≥ 40°C with non-combustion particulates."),
    ("OTHER ANOMALY: ", "Multi-sensor statistical deviation outside baseline distribution.")
]
for h, d in rule_notes:
    p = atf2.add_paragraph()
    p.text = h
    p.font.size = Pt(9.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = atf2.add_paragraph()
    p.text = d
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)

# Algorithm 3: Self-Healing Network
a3 = add_card(slide12, 8.9, 1.6, 3.65, 5.2, border_color=COLOR_PURPLE)
atb3 = slide12.shapes.add_textbox(Inches(9.1), Inches(1.8), Inches(3.25), Inches(4.8))
atf3 = atb3.text_frame
atf3.word_wrap = True
p = atf3.paragraphs[0]
p.text = "3. GRAPH SELF-HEALING"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_PURPLE
p.space_after = Pt(8)
graph_notes = [
    ("Dead Link Pruning: ", "Upon node failure detection, all incident edges E(failed) are removed from NetworkX graph."),
    ("Manhattan Metric: ", "Calculates proximity between active orphans:\nD(A,B) = |xA - xB| + |yA - yB|"),
    ("Proximity Link Insertion: ", "Connects active agents satisfying D(A,B) ≤ 4 if no active edge exists."),
    ("Biconnectivity Check: ", "nx.is_connected(subgraph) validates full operational restoration in <20ms.")
]
for h, d in graph_notes:
    p = atf3.add_paragraph()
    p.text = h
    p.font.size = Pt(9.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = atf3.add_paragraph()
    p.text = d
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)


# ============================================================
# SLIDE 13: DATABASE & DATA FLOW
# ============================================================
slide13 = create_base_slide(prs, "Relational Persistence & Schemas", "Database Architecture: SQLAlchemy Relational Schema & Telemetry Flow")

# Left Column: 7 Schema Tables
dc1 = add_card(slide13, 0.8, 1.6, 5.65, 5.2, border_color=COLOR_BLUE)
dtb1 = slide13.shapes.add_textbox(Inches(1.05), Inches(1.8), Inches(5.15), Inches(4.8))
dtf1 = dtb1.text_frame
dtf1.word_wrap = True
p = dtf1.paragraphs[0]
p.text = "7 PERSISTENT RELATIONAL TABLES"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_BLUE
p.space_after = Pt(8)

tables_info = [
    ("agents: ", "Agent registry, grid coordinates (x,y), status (ACTIVE/FAILED), battery, health, connectivity."),
    ("agent_deployments & site: ", "Persisted real-world GPS coordinates (latitude, longitude) and deployment radius (0.5–10km)."),
    ("environmental_readings: ", "Time-series logging 6 sensor features, AI anomaly score, and classified event."),
    ("environmental_events: ", "Active & resolved hazard events, epicenters, severity, consensus state, affected agent IDs."),
    ("consensus_records: ", "Evidence audit trail, total voters, agreeing voters, confidence score."),
    ("network_reorganizations: ", "Triggered failures, severed connections, created links, recovery duration (ms)."),
    ("system_audit_logs: ", "Chronological audit timeline categorized by EVENT, FAILURES, CONSENSUS, RECOVERY, etc.")
]
for tname, tdesc in tables_info:
    p = dtf1.add_paragraph()
    p.text = tname
    p.font.size = Pt(9.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = dtf1.add_paragraph()
    p.text = tdesc
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(4)

# Right Column: Data Flow Lifecycle
dc2 = add_card(slide13, 6.9, 1.6, 5.65, 5.2, border_color=COLOR_CYAN)
dtb2 = slide13.shapes.add_textbox(Inches(7.15), Inches(1.8), Inches(5.15), Inches(4.8))
dtf2 = dtb2.text_frame
dtf2.word_wrap = True
p = dtf2.paragraphs[0]
p.text = "TELEMETRY & STATE DATA FLOW PIPELINE"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p.space_after = Pt(8)

flow_stages = [
    ("Stage 1 — In-Memory Edge State: ", "Agents maintain live telemetry, neighbor references, and battery metrics in memory for sub-millisecond local P2P access."),
    ("Stage 2 — Atomic Relational Sync: ", "SimulationService executes periodic and event-triggered commits syncing active agent states, readings, and events via SQLAlchemy ORM."),
    ("Stage 3 — WebSocket Broadcast (/ws): ", "FastAPI WebSocketManager pushes live JSON state deltas to connected Next.js browser clients instantly."),
    ("Stage 4 — Historical Query Optimization: ", "Indexed timestamps on telemetry and audit log tables enable sub-10ms REST responses for Next.js historical analytics.")
]
for sname, sdesc in flow_stages:
    p = dtf2.add_paragraph()
    p.text = sname
    p.font.size = Pt(9.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = dtf2.add_paragraph()
    p.text = sdesc
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)


# ============================================================
# SLIDE 14: REAL-WORLD USE CASES
# ============================================================
slide14 = create_base_slide(prs, "Industry Impact & Practical Applications", "Real-World Use Cases: 5 Practical Disaster & Ecological Scenarios")

use_cases = [
    ("1. Wildfire Detection in Dense National Forests", COLOR_ROSE,
     "Thermal drones and canopy sentries detect early smoldering combustion beneath tree canopies hours before satellite or smoke detection towers spot plumes. Autonomous consensus eliminates false alarms from campfire smoke."),
    
    ("2. Petrochemical Industrial Refinery Compliance", COLOR_AMBER,
     "Grid of autonomous atmospheric sensors surrounding chemical plants continuously profiles volatile organic compounds, fugitive CO2, and smoke emissions. Operates without expensive fixed cable infrastructure."),
    
    ("3. Urban Heat Island & Public Health Mitigation", COLOR_BLUE,
     "Micro-climate thermal sentries deployed across urban street canyons identify hyper-local thermal stress zones (≥42°C), automatically signaling municipal teams to trigger targeted cooling centers."),
    
    ("4. Watershed & Riparian Habitat Conservation", COLOR_CYAN,
     "Hydrology and soil probes track river basin agricultural runoff, extreme moisture depletion, and soil acidification, providing early warnings for flash droughts and aquatic ecosystem collapse."),
    
    ("5. Post-Disaster Emergency Network Restoration", COLOR_PURPLE,
     "Following earthquakes or hurricanes when cellular towers are flattened, autonomous mesh nodes self-organize replacement communication links, establishing resilient emergency hazard telemetry for first responders.")
]

for idx, (title, color, desc) in enumerate(use_cases):
    top = 1.6 + idx * 1.05
    add_card(slide14, 0.8, top, 11.75, 0.95, border_color=color)
    tb = slide14.shapes.add_textbox(Inches(1.0), Inches(top + 0.08), Inches(11.35), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = color
    p.space_after = Pt(2)
    p = tf.add_paragraph()
    p.text = desc
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_SILVER


# ============================================================
# SLIDE 15: DEMONSTRATION & EXAMPLE SCENARIO
# ============================================================
slide15 = create_base_slide(prs, "Technical Viva Demonstration", "Demonstration Scenario: Step-by-Step Viva Execution Guide")

demo_steps = [
    ("Step 1: Baseline Fleet Normalcy", COLOR_CYAN,
     "Inspect /command-center. 20 active agents report normal baseline telemetry (28°C, 60% humidity, 0.10 smoke). NetworkX confirms a fully connected P2P mesh topology."),
    
    ("Step 2: Hazard Injection (/incidents)", COLOR_ROSE,
     "Trigger simulated Fire Event at epicenter (10, 10). Agents A4, A5, A6, A7 enter the combustion zone. Temperature surges to 46°C, smoke spikes to 0.85, humidity drops to 18%."),
    
    ("Step 3: Edge AI Detection & Consensus", COLOR_AMBER,
     "Agent A6's local Isolation Forest scores -0.21 (ANOMALY); rule classifier flags FIRE. A6 broadcasts alerts to neighbors A5, A7, A8. Neighborhood quorum confirms FIRE with 88% confidence."),
    
    ("Step 4: Simulated Node Destruction", COLOR_ROSE,
     "Simulate extreme heat destroying agent A6 ('Fail Agent'). A6's status flips to FAILED, battery drops to 0%, and its communication edges are instantly pruned by the NetworkManager."),
    
    ("Step 5: Autonomous Self-Organization", COLOR_GREEN,
     "Trigger Self-Organization. Algorithm scans active orphan nodes, calculates Manhattan distances (d ≤ 4), establishes replacement connections between A5 <-> A7, and restores connectivity in 12ms!"),
    
    ("Step 6: Audit History Verification", COLOR_PURPLE,
     "Open /history to inspect the immutable audit log verifying each step: Hazard Detection -> P2P Consensus -> Link Pruning -> Autonomous Topology Recovery.")
]

for idx, (title, color, desc) in enumerate(demo_steps):
    top = 1.6 + idx * 0.88
    add_card(slide15, 0.8, top, 11.75, 0.80, border_color=color)
    tb = slide15.shapes.add_textbox(Inches(1.0), Inches(top + 0.05), Inches(11.35), Inches(0.7))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = color
    p.space_after = Pt(2)
    p = tf.add_paragraph()
    p.text = desc
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER


# ============================================================
# SLIDE 16: SECURITY, RELIABILITY & PERFORMANCE
# ============================================================
slide16 = create_base_slide(prs, "Operational Resilience", "Security, Reliability & Performance: Benchmarks and Robustness")

# 3 Columns
c1 = add_card(slide16, 0.8, 1.6, 3.65, 5.2, border_color=COLOR_GREEN)
tb1 = slide16.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.25), Inches(4.8))
tf1 = tb1.text_frame
tf1.word_wrap = True
p = tf1.paragraphs[0]
p.text = "PERFORMANCE BENCHMARKS"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_GREEN
p.space_after = Pt(8)
perf_data = [
    ("Inference Latency: ", "< 1.5 milliseconds per 6-sensor vector on edge node."),
    ("Topology Recovery: ", "< 20 milliseconds to identify severed edges and restore biconnectivity."),
    ("Model Memory Footprint: ", "Serialized Isolation Forest is 2.2 MB; easily fits in edge RAM."),
    ("Network Throughput: ", "Reduces communication bandwidth by 95% compared to streaming raw continuous telemetry.")
]
for h, d in perf_data:
    p = tf1.add_paragraph()
    p.text = h
    p.font.size = Pt(9.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = tf1.add_paragraph()
    p.text = d
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)

c2 = add_card(slide16, 4.85, 1.6, 3.65, 5.2, border_color=COLOR_BLUE)
tb2 = slide16.shapes.add_textbox(Inches(5.05), Inches(1.8), Inches(3.25), Inches(4.8))
tf2 = tb2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "RELIABILITY ENGINEERING"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_BLUE
p.space_after = Pt(8)
rel_data = [
    ("Dynamic Health Metric: ", "Evaluates battery and operating temperatures to compute health score (0-100)."),
    ("Reliability Formula: ", "Reliability = (Health * 0.6) + (Battery * 0.4); prioritizes high-trust nodes in voting."),
    ("Graceful Degradation: ", "Nodes with battery < 30% automatically transition to low-frequency passive sentry mode."),
    ("Deadlock Prevention: ", "Asynchronous non-blocking message handling prevents agent stall during network partitions.")
]
for h, d in rel_data:
    p = tf2.add_paragraph()
    p.text = h
    p.font.size = Pt(9.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = tf2.add_paragraph()
    p.text = d
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)

c3 = add_card(slide16, 8.9, 1.6, 3.65, 5.2, border_color=COLOR_AMBER)
tb3 = slide16.shapes.add_textbox(Inches(9.1), Inches(1.8), Inches(3.25), Inches(4.8))
tf3 = tb3.text_frame
tf3.word_wrap = True
p = tf3.paragraphs[0]
p.text = "SECURITY & INTEGRITY"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_AMBER
p.space_after = Pt(8)
sec_data = [
    ("Pydantic Validation: ", "Strict schema verification rejects corrupted or out-of-bounds telemetry payloads."),
    ("CORS Protection: ", "FastAPI middleware restricts API origin access to authorized client domains."),
    ("Immutable Audit Trail: ", "Database system_audit_logs cannot be rewritten by edge agents, ensuring regulatory compliance."),
    ("Fault Isolation: ", "Rogue or compromised nodes sending anomalous noise fail neighborhood quorum and are isolated.")
]
for h, d in sec_data:
    p = tf3.add_paragraph()
    p.text = h
    p.font.size = Pt(9.0)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = tf3.add_paragraph()
    p.text = d
    p.font.size = Pt(8.2)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)


# ============================================================
# SLIDE 17: ADVANTAGES & KEY INNOVATIONS
# ============================================================
slide17 = create_base_slide(prs, "Competitive Differentiation", "Advantages & Innovation: Multi-Agent Paradigm vs Status Quo")

innovations = [
    ("1. True Decentralization (Zero SPOF)", COLOR_CYAN,
     "Eliminates reliance on cloud servers during critical emergencies. Hazard detection, neighbor voting, and alert escalation proceed seamlessly even if all external internet access is severed."),
    
    ("2. 95% Communication Bandwidth Savings", COLOR_BLUE,
     "Rather than continuously streaming raw high-frequency sensor readings, agents transmit lightweight alert payloads only when statistically confirmed anomalies emerge."),
    
    ("3. Quorum-Validated False Alarm Rejection", COLOR_GREEN,
     "Solitary defective sensors or transient dust bursts cannot trigger false alarms because the consensus threshold requires spatial agreement across active neighbors (θ ≥ 0.50)."),
    
    ("4. Dynamic Graph Mesh Self-Healing", COLOR_PURPLE,
     "When edge nodes are physically burned or destroyed, the autonomous NetworkX reorganization algorithm reconnects orphaned neighbors via Manhattan proximity in under 20ms."),
    
    ("5. Explainable AI (XAI) Transparency", COLOR_AMBER,
     "Generates human-interpretable natural language narrative explanations on every node, informing command staff exactly which sensors exceeded thresholds and why.")
]

for idx, (title, color, desc) in enumerate(innovations):
    top = 1.6 + idx * 1.05
    add_card(slide17, 0.8, top, 11.75, 0.95, border_color=color)
    tb = slide17.shapes.add_textbox(Inches(1.0), Inches(top + 0.08), Inches(11.35), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = color
    p.space_after = Pt(2)
    p = tf.add_paragraph()
    p.text = desc
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_SILVER


# ============================================================
# SLIDE 18: LIMITATIONS & FUTURE ENHANCEMENTS
# ============================================================
slide18 = create_base_slide(prs, "Research Roadmap", "Limitations & Future Roadmap: Implemented Scope vs Next-Gen Features")

# Left: Current Boundaries
lc1 = add_card(slide18, 0.8, 1.6, 5.65, 5.2, border_color=COLOR_AMBER)
ltb1 = slide18.shapes.add_textbox(Inches(1.05), Inches(1.8), Inches(5.15), Inches(4.8))
ltf1 = ltb1.text_frame
ltf1.word_wrap = True
p = ltf1.paragraphs[0]
p.text = "CURRENT SYSTEM BOUNDARIES"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_AMBER
p.space_after = Pt(10)

current_bounds = [
    ("Software Simulation of Hardware Probes: ", "Physical IoT radio transceivers (LoRa/Zigbee) and hardware microcontrollers are simulated in software over a 20x20 coordinate grid."),
    ("Deterministic Patrol Trajectories: ", "Drone patrol steps follow stochastic drift instead of aerodynamic physics and terrain elevation contours."),
    ("Static Classification Thresholds: ", "Event classification rules use fixed sensor thresholds rather than dynamically adjusting for seasonal temperature baselines."),
    ("Centralized Web Coordination: ", "While edge consensus is fully decentralized, UI visualization state sync is coordinated via FastAPI server.")
]
for head, desc in current_bounds:
    p = ltf1.add_paragraph()
    p.text = head
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = ltf1.add_paragraph()
    p.text = desc
    p.font.size = Pt(8.8)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)

# Right: Future Roadmap
lc2 = add_card(slide18, 6.9, 1.6, 5.65, 5.2, border_color=COLOR_PURPLE)
ltb2 = slide18.shapes.add_textbox(Inches(7.15), Inches(1.8), Inches(5.15), Inches(4.8))
ltf2 = ltb2.text_frame
ltf2.word_wrap = True
p = ltf2.paragraphs[0]
p.text = "FUTURE RESEARCH ROADMAP"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_PURPLE
p.space_after = Pt(10)

future_goals = [
    ("1. Physical LoRaWAN / ESP32 Hardware: ", "Deploy embedded C++ agent runtimes onto low-power ESP32 microcontrollers with 868/915 MHz LoRa transceivers."),
    ("2. Deep Reinforcement Learning (DRL): ", "Implement PPO/DQN algorithms for autonomous drone swarm repositioning to dynamically contain expanding fire perimeters."),
    ("3. Byzantine Fault Tolerant (BFT) Ledger: ", "Integrate lightweight cryptographic blockchain consensus for tamper-proof regulatory emission compliance."),
    ("4. Satellite Remote Sensing Fusion: ", "Fuse local edge agent alerts with Sentinel-2 optical and NASA FIRMS thermal anomaly satellite feeds.")
]
for head, desc in future_goals:
    p = ltf2.add_paragraph()
    p.text = head
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p = ltf2.add_paragraph()
    p.text = desc
    p.font.size = Pt(8.8)
    p.font.color.rgb = COLOR_SILVER
    p.space_after = Pt(6)


# ============================================================
# SLIDE 19: CONCLUSION
# ============================================================
slide19 = create_base_slide(prs, "Project Synthesis & Summary", "Conclusion: Summary of Technical Contributions & Practical Significance")

# 3 Synthesis Cards
conc_items = [
    ("CORE PROJECT SUMMARY", COLOR_CYAN, 0.8, [
        ("Decentralized Paradigm Proved: ", "Demonstrated that shifting environmental sensing and AI inference from centralized clouds to autonomous edge agents provides unmatched disaster resilience."),
        ("Multi-Sensor Mastery: ", "Simultaneous tracking of 6 telemetry parameters provides robust multi-dimensional coverage across diverse ecological hazard types."),
        ("Fault-Tolerant Mesh: ", "NetworkX self-organization algorithm restores network connectivity dynamically in under 20ms following node destruction.")
    ]),
    ("MAJOR TECHNICAL CONTRIBUTIONS", COLOR_BLUE, 4.85, [
        ("Local ML + Rule Engine: ", "Hybrid approach combining unsupervised Isolation Forest anomaly scoring with contextual multi-hazard event classification."),
        ("Spatial Quorum Protocol: ", "Neighborhood consensus mechanism (θ ≥ 0.50) successfully suppresses sensor drift while ensuring 85%+ hazard confirmation."),
        ("Production Full-Stack: ", "Complete Next.js 14 mission control application powered by FastAPI ASGI server and 7-table SQLAlchemy persistence.")
    ]),
    ("FINAL TAKEAWAY FOR DEFENSE", COLOR_PURPLE, 8.9, [
        ("Mission-Critical Reliability: ", "Disasters don't wait for cloud uplinks. Edge-based Multi-Agent Systems are the future of environmental disaster mitigation."),
        ("Verified Implementation: ", "All 11 unit and integration test suites pass; 22 REST endpoints fully functional and tested live."),
        ("Extensible Foundation: ", "Provides a battle-tested architecture ready for physical LoRaWAN hardware deployment and real-world field trials.")
    ])
]

for title, color, left, bullets in conc_items:
    cc = add_card(slide19, left, 1.6, 3.65, 5.2, border_color=color)
    ctb = slide19.shapes.add_textbox(Inches(left + 0.15), Inches(1.8), Inches(3.35), Inches(4.8))
    ctf = ctb.text_frame
    ctf.word_wrap = True
    p = ctf.paragraphs[0]
    p.text = title
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = color
    p.space_after = Pt(12)

    for h, d in bullets:
        p = ctf.add_paragraph()
        p.text = h
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p = ctf.add_paragraph()
        p.text = d
        p.font.size = Pt(8.8)
        p.font.color.rgb = COLOR_SILVER
        p.space_after = Pt(8)


# ============================================================
# SLIDE 20: THANK YOU & Q&A
# ============================================================
slide20 = prs.slides.add_slide(prs.slide_layouts[6])
bg20 = slide20.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
set_shape_flat(bg20, COLOR_BG)

# Thank you box
ty_box = slide20.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.333), Inches(3.5))
tyf = ty_box.text_frame
tyf.word_wrap = True

p = tyf.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
p.text = "THANK YOU!"
p.font.name = FONT_HEADING
p.font.size = Pt(40)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p.space_after = Pt(10)

p = tyf.add_paragraph()
p.alignment = PP_ALIGN.CENTER
p.text = "Questions & Answers  •  Faculty Viva Evaluation"
p.font.name = FONT_HEADING
p.font.size = Pt(20)
p.font.color.rgb = COLOR_WHITE
p.space_after = Pt(14)

p = tyf.add_paragraph()
p.alignment = PP_ALIGN.CENTER
p.text = "Self-Organizing Multi-Agent Systems for Decentralized Environmental Monitoring"
p.font.name = FONT_BODY
p.font.size = Pt(13)
p.font.color.rgb = COLOR_BLUE
p.space_after = Pt(20)

# 3 Quick Viva Reference Cards at bottom
qcard1 = add_card(slide20, 1.5, 4.8, 3.2, 1.8, border_color=COLOR_CYAN)
qtb1 = slide20.shapes.add_textbox(Inches(1.65), Inches(4.95), Inches(2.9), Inches(1.5))
qtf1 = qtb1.text_frame
qtf1.word_wrap = True
p = qtf1.paragraphs[0]
p.text = "AI MODEL"
p.font.size = Pt(10.5)
p.font.bold = True
p.font.color.rgb = COLOR_CYAN
p = qtf1.add_paragraph()
p.text = "Isolation Forest (200 trees)\n6 Telemetry Features\nInference Latency: <1.5 ms"
p.font.size = Pt(9.0)
p.font.color.rgb = COLOR_SILVER

qcard2 = add_card(slide20, 5.066, 4.8, 3.2, 1.8, border_color=COLOR_BLUE)
qtb2 = slide20.shapes.add_textbox(Inches(5.2), Inches(4.95), Inches(2.9), Inches(1.5))
qtf2 = qtb2.text_frame
qtf2.word_wrap = True
p = qtf2.paragraphs[0]
p.text = "CONSENSUS & HEALING"
p.font.size = Pt(10.5)
p.font.bold = True
p.font.color.rgb = COLOR_BLUE
p = qtf2.add_paragraph()
p.text = "Spatial Quorum: θ ≥ 0.50\nManhattan Reconnect: d ≤ 4\nRecovery: <20 ms"
p.font.size = Pt(9.0)
p.font.color.rgb = COLOR_SILVER

qcard3 = add_card(slide20, 8.633, 4.8, 3.2, 1.8, border_color=COLOR_PURPLE)
qtb3 = slide20.shapes.add_textbox(Inches(8.8), Inches(4.95), Inches(2.9), Inches(1.5))
qtf3 = qtb3.text_frame
qtf3.word_wrap = True
p = qtf3.paragraphs[0]
p.text = "TEST VERIFICATION"
p.font.size = Pt(10.5)
p.font.bold = True
p.font.color.rgb = COLOR_PURPLE
p = qtf3.add_paragraph()
p.text = "11/11 Pytest Suites Passed\n22 REST API Endpoints\nLive Next.js 14 Dashboard"
p.font.size = Pt(9.0)
p.font.color.rgb = COLOR_SILVER

pptx_path = os.path.join(output_dir, "Project_Explanation.pptx")
prs.save(pptx_path)
print("Saved Presentation successfully to:", pptx_path)
