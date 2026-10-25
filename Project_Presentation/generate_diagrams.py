import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

output_dir = os.path.abspath("Project_Presentation")

def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(18, 11), dpi=200)
    fig.patch.set_facecolor('#070B14')
    ax.set_facecolor('#070B14')

    # Title & Subtitle
    ax.text(9, 10.4, "DECENTRALIZED ENVIRONMENTAL MULTI-AGENT SYSTEM ARCHITECTURE", 
            fontsize=20, weight='bold', color='#00F5D4', ha='center', va='center', family='sans-serif')
    ax.text(9, 10.0, "End-to-End System Layers: Edge Sensing, Edge AI, P2P Consensus, Network Healing, and Web HUD", 
            fontsize=11, color='#94A3B8', ha='center', va='center')

    # Card 1: Web Presentation Layer
    p1 = patches.FancyBboxPatch((0.8, 8.0), 16.4, 1.5, boxstyle="round,pad=0.1,rounding_size=0.15",
                                ec="#38BDF8", fc="#0E1726", lw=1.8)
    ax.add_patch(p1)
    ax.text(1.2, 9.15, "1. PUBLIC WEB APPLICATION & MISSION CONTROL LAYER", fontsize=12, weight='bold', color='#38BDF8')
    ax.text(1.2, 8.75, "Next.js 14 (App Router) | React 18 | TypeScript | Tailwind CSS | Lucide Icons | Recharts SVG Engine", fontsize=9.5, color='#E2E8F0')
    ax.text(1.2, 8.35, "• Command Center (/command-center) with Leaflet GIS Map  • Fleet Operations Table (/agents) with Health Gauges\n• Network Topology Graph Visualizer (/network)  • Incident & Consensus Drilldown (/incidents)  • Audit Timeline (/history)", fontsize=8.5, color='#94A3B8')

    # Arrow 1 down
    ax.annotate('', xy=(9, 7.3), xytext=(9, 8.0),
                arrowprops=dict(arrowstyle="<->", color="#00F5D4", lw=2, mutation_scale=15))
    ax.text(9.2, 7.65, "Bidirectional REST / HTTP & WebSocket (/ws)", fontsize=8.5, color="#00F5D4", weight='bold')

    # Card 2: Application API & Orchestration Server
    p2 = patches.FancyBboxPatch((0.8, 5.7), 16.4, 1.5, boxstyle="round,pad=0.1,rounding_size=0.15",
                                ec="#818CF8", fc="#0E1726", lw=1.8)
    ax.add_patch(p2)
    ax.text(1.2, 6.85, "2. FASTAPI ASYNCHRONOUS BACKEND & COORDINATION LAYER", fontsize=12, weight='bold', color='#818CF8')
    ax.text(1.2, 6.45, "Python 3.11 | FastAPI Framework | Uvicorn ASGI Server | WebSocketManager | CORS Middleware", fontsize=9.5, color='#E2E8F0')
    ax.text(1.2, 6.05, "• 22 REST API Endpoints (/api/agents, /api/network, /api/events, /api/analytics, /api/history)\n• Live Simulation State Coordination & Geo-Coordinate Persistence • Real-time Broadcast Streaming to Connected Web Sockets", fontsize=8.5, color='#94A3B8')

    # Three Columns: AI Engine, Agent Engine, Network Engine
    # Column A: AI Engine
    p3a = patches.FancyBboxPatch((0.8, 3.0), 5.1, 2.3, boxstyle="round,pad=0.1,rounding_size=0.15",
                                 ec="#F43F5E", fc="#111827", lw=1.5)
    ax.add_patch(p3a)
    ax.text(1.1, 4.95, "3A. LOCAL AI / ML ENGINE", fontsize=11, weight='bold', color='#F43F5E')
    ax.text(1.1, 4.6, "• Scikit-Learn IsolationForest\n  - 200 Estimators, Contamination=0.05\n  - 6D Telemetry Feature Space\n  - Real-time Decision Function Scoring", fontsize=8.5, color='#E2E8F0')
    ax.text(1.1, 3.65, "• Multi-Hazard Event Classifier\n  - FIRE: High Temp, Dense Smoke, Low Hum\n  - POLLUTION: Elevated CO2, Hazardous AQI\n  - EXTREME HEAT: Ambient Thermal Stress\n  - OTHER: High-Dimensional Outliers", fontsize=8.2, color='#94A3B8')

    # Column B: Multi-Agent Engine
    p3b = patches.FancyBboxPatch((6.45, 3.0), 5.1, 2.3, boxstyle="round,pad=0.1,rounding_size=0.15",
                                 ec="#10B981", fc="#111827", lw=1.5)
    ax.add_patch(p3b)
    ax.text(6.75, 4.95, "3B. MULTI-AGENT ENGINE", fontsize=11, weight='bold', color='#10B981')
    ax.text(6.75, 4.6, "• Autonomous MonitoringAgent\n  - 6 Environmental Sensors On-Node\n  - Battery & Dynamic Health Rating\n  - Explainable AI Narrative Engine\n  - Asynchronous P2P Alert Broadcasting", fontsize=8.5, color='#E2E8F0')
    ax.text(6.75, 3.65, "• Local Neighborhood Consensus\n  - Distributed Spatial Voting\n  - Confidence = Agreeing / Active Neighbors\n  - Threshold Gate (Confidence >= 0.50)\n  - False Alarm Elimination", fontsize=8.2, color='#94A3B8')

    # Column C: Network & Mesh Engine
    p3c = patches.FancyBboxPatch((12.1, 3.0), 5.1, 2.3, boxstyle="round,pad=0.1,rounding_size=0.15",
                                 ec="#F59E0B", fc="#111827", lw=1.5)
    ax.add_patch(p3c)
    ax.text(12.4, 4.95, "3C. NETWORKX MESH ENGINE", fontsize=11, weight='bold', color='#F59E0B')
    ax.text(12.4, 4.6, "• Dynamic P2P Mesh Topology\n  - Undirected Graph G=(V,E)\n  - Manhattan Proximity Links (d <= 4)\n  - Active Biconnectivity Verification", fontsize=8.5, color='#E2E8F0')
    ax.text(12.4, 3.65, "• Self-Organization & Healing\n  - Instant Hardware Failure Detection\n  - Dead Link Pruning & Isolation\n  - Proximity-based Orphan Reconnection\n  - Recovery Duration < 20 ms", fontsize=8.2, color='#94A3B8')

    # Connecting Arrows between API and Engines
    ax.annotate('', xy=(3.35, 5.3), xytext=(3.35, 5.7), arrowprops=dict(arrowstyle="->", color="#F43F5E", lw=1.5))
    ax.annotate('', xy=(9.0, 5.3), xytext=(9.0, 5.7), arrowprops=dict(arrowstyle="->", color="#10B981", lw=1.5))
    ax.annotate('', xy=(14.65, 5.3), xytext=(14.65, 5.7), arrowprops=dict(arrowstyle="->", color="#F59E0B", lw=1.5))

    # P2P Arrows between Agents and Network
    ax.annotate('', xy=(6.45, 4.15), xytext=(5.9, 4.15), arrowprops=dict(arrowstyle="<->", color="#A855F7", lw=1.5))
    ax.annotate('', xy=(12.1, 4.15), xytext=(11.55, 4.15), arrowprops=dict(arrowstyle="<->", color="#A855F7", lw=1.5))

    # Card 4: Persistent Database Storage Layer
    p4 = patches.FancyBboxPatch((0.8, 0.6), 16.4, 1.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                                ec="#06B6D4", fc="#0E1726", lw=1.8)
    ax.add_patch(p4)
    ax.text(1.2, 2.05, "4. RELATIONAL PERSISTENCE & AUDIT STORAGE LAYER (SQLAlchemy 2.0 ORM)", fontsize=12, weight='bold', color='#06B6D4')
    ax.text(1.2, 1.65, "SQLite (Local Embedded Development) | PostgreSQL / Supabase (Production Cloud Deployment)", fontsize=9.5, color='#E2E8F0')
    
    # Tables grid
    ax.text(1.2, 1.25, "• agents (Node positions, battery, health scores)\n• agent_deployments & deployment_site (GPS coords, radius)\n• environmental_readings (6-sensor telemetry time-series)", fontsize=8.2, color='#94A3B8')
    ax.text(9.2, 1.25, "• environmental_events (Hazard epicenter, severity, consensus state)\n• consensus_records (Neighbor voter distributions & evidence logs)\n• network_reorganizations (Severed/created links, recovery ms)\n• system_audit_logs (Immutable audit timeline)", fontsize=8.2, color='#94A3B8')

    # Arrow down to Database
    ax.annotate('', xy=(9, 2.4), xytext=(9, 3.0),
                arrowprops=dict(arrowstyle="->", color="#06B6D4", lw=2, mutation_scale=15))

    ax.set_xlim(0, 18)
    ax.set_ylim(0, 11)
    ax.axis('off')

    plt.tight_layout()
    arch_path = os.path.join(output_dir, "Project_Architecture.png")
    plt.savefig(arch_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=200)
    plt.close()
    print("Saved:", arch_path)

def create_workflow_diagram():
    fig, ax = plt.subplots(figsize=(18, 11), dpi=200)
    fig.patch.set_facecolor('#070B14')
    ax.set_facecolor('#070B14')

    ax.text(9, 10.4, "END-TO-END MULTI-AGENT EXECUTION & RECOVERY WORKFLOW", 
            fontsize=20, weight='bold', color='#00F5D4', ha='center', va='center', family='sans-serif')
    ax.text(9, 10.0, "Step-by-Step Lifecycle: Sensing, Edge AI, P2P Propagation, Local Consensus, Failure & Self-Healing", 
            fontsize=11, color='#94A3B8', ha='center', va='center')

    steps = [
        ("Step 1: Environmental Sensing", 
         "Each deployed agent tracks 6 telemetry parameters:\n• Temperature (°C), Humidity (%)\n• Smoke Density (0.0-1.0), CO2 (ppm)\n• Air Quality Index (AQI), Soil Moisture (%)",
         "#38BDF8", 0.8, 6.6),
        
        ("Step 2: Local AI Anomaly Scoring",
         "On-node Isolation Forest evaluates 6D vector:\n• Contamination = 0.05, 200 Estimators\n• Generates real-time anomaly score\n• Flags status as NORMAL or ANOMALY",
         "#818CF8", 4.9, 6.6),
        
        ("Step 3: Hazard Event Classification",
         "Contextual rule classifier evaluates patterns:\n• FIRE: Temp >= 40°C, Smoke >= 0.5, Hum <= 30%\n• POLLUTION: CO2 >= 800, AQI >= 120, Smoke >= 0.3\n• EXTREME HEAT: Temp >= 40°C without smoke particulates",
         "#F43F5E", 9.0, 6.6),

        ("Step 4: P2P Alert Broadcasting",
         "Anomalous agent broadcasts alert payload:\n• Alert contains event type, score, timestamp\n• Transmitted directly to active proximate neighbors\n• Avoids flooding entire network",
         "#F59E0B", 13.1, 6.6),

        ("Step 5: Local Neighbor Consensus",
         "Decentralized weighted voting across neighborhood:\n• Confidence = Count(Agreeing) / Total(Active)\n• Threshold gate: Confirmed if Confidence >= 0.50\n• Rejects transient sensor noise / false alarms",
         "#10B981", 0.8, 2.5),

        ("Step 6: Incident Escalation & Log",
         "Incident confirmed with localized consensus:\n• Saved to relational database (environmental_events)\n• Broadcast to Next.js Web UI via WebSocket\n• Mission-critical HUD alerts & spatial map ping",
         "#06B6D4", 4.9, 2.5),

        ("Step 7: Node Failure / Loss Simulation",
         "Simulated physical destruction or hardware failure:\n• Agent transitions to FAILED state, battery drops to 0%\n• CommunicationManager cuts links to failed node\n• Network partition or severed graph topology detected",
         "#E11D48", 9.0, 2.5),

        ("Step 8: Autonomous Self-Organization",
         "Dynamic mesh self-healing protocol executes:\n• Scans active orphan nodes within Manhattan d <= 4\n• Establishes replacement P2P links dynamically\n• Restores graph biconnectivity in under 20 ms",
         "#A855F7", 13.1, 2.5)
    ]

    for title, desc, color, x, y in steps:
        p = patches.FancyBboxPatch((x, y), 3.9, 3.0, boxstyle="round,pad=0.1,rounding_size=0.15",
                                    ec=color, fc="#0E1726", lw=1.8)
        ax.add_patch(p)
        ax.text(x + 0.2, y + 2.55, title, fontsize=10.5, weight='bold', color=color)
        ax.text(x + 0.2, y + 1.25, desc, fontsize=8.2, color='#E2E8F0', va='center')

    # Horizontal Arrows Row 1 (Steps 1 -> 2 -> 3 -> 4)
    ax.annotate('', xy=(4.9, 8.1), xytext=(4.7, 8.1), arrowprops=dict(arrowstyle="->", color="#00F5D4", lw=2))
    ax.annotate('', xy=(9.0, 8.1), xytext=(8.8, 8.1), arrowprops=dict(arrowstyle="->", color="#00F5D4", lw=2))
    ax.annotate('', xy=(13.1, 8.1), xytext=(12.9, 8.1), arrowprops=dict(arrowstyle="->", color="#00F5D4", lw=2))

    # Downward Transition from Step 4 to Step 5
    ax.annotate('', xy=(2.75, 5.5), xytext=(15.05, 6.6), 
                arrowprops=dict(arrowstyle="->", color="#A855F7", lw=2, connectionstyle="arc3,rad=-0.25"))
    ax.text(9.0, 5.9, "Localized P2P Alert Delivery triggers Neighbor Consensus", 
            fontsize=9, color="#A855F7", ha='center', weight='bold')

    # Horizontal Arrows Row 2 (Steps 5 -> 6 -> 7 -> 8)
    ax.annotate('', xy=(4.9, 4.0), xytext=(4.7, 4.0), arrowprops=dict(arrowstyle="->", color="#00F5D4", lw=2))
    ax.annotate('', xy=(9.0, 4.0), xytext=(8.8, 4.0), arrowprops=dict(arrowstyle="->", color="#00F5D4", lw=2))
    ax.annotate('', xy=(13.1, 4.0), xytext=(12.9, 4.0), arrowprops=dict(arrowstyle="->", color="#00F5D4", lw=2))

    # Feedback loop from Step 8 back to Continuous Monitoring (Step 1)
    ax.annotate('', xy=(2.0, 6.6), xytext=(15.05, 2.5),
                arrowprops=dict(arrowstyle="->", color="#00F5D4", lw=2, connectionstyle="arc3,rad=0.35"))
    ax.text(9.0, 0.9, "Continuous Decentralized Edge Monitoring with Restored Communication Mesh", 
            fontsize=9.5, color="#00F5D4", ha='center', weight='bold')

    ax.set_xlim(0, 18)
    ax.set_ylim(0, 11)
    ax.axis('off')

    plt.tight_layout()
    flow_path = os.path.join(output_dir, "Agent_Workflow.png")
    plt.savefig(flow_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=200)
    plt.close()
    print("Saved:", flow_path)

if __name__ == "__main__":
    create_architecture_diagram()
    create_workflow_diagram()
