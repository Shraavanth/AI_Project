import sys
import os

import streamlit as st
import matplotlib.pyplot as plt


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORT PROJECT
# ============================================================

from simulation.environment_model import EnvironmentalModel


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Environmental Multi-Agent Monitoring",
    page_icon="🌍",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title(
    "🌍 Self-Organizing Multi-Agent Environmental Monitoring"
)

st.caption(
    "AI-driven decentralized environmental monitoring "
    "with autonomous agents, local consensus, and "
    "self-organizing network recovery."
)


# ============================================================
# SESSION STATE
# ============================================================

if "model" not in st.session_state:

    model = EnvironmentalModel(
        width=20,
        height=20,
        num_agents=20
    )

    model.create_demo_layout()

    st.session_state.model = model
    st.session_state.event_created = False
    st.session_state.event_type = "None"
    st.session_state.consensus = None


model = st.session_state.model


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Simulation Controls")


# ============================================================
# CREATE FIRE
# ============================================================

if st.sidebar.button("🔥 Create Fire", use_container_width=True):

    model.create_fire_event(
        center_x=10,
        center_y=10,
        radius=3
    )

    model.analyze_environment()
    model.broadcast_alerts()

    st.session_state.consensus = (
        model.determine_consensus()
    )

    st.session_state.event_created = True
    st.session_state.event_type = "FIRE"

    st.rerun()


# ============================================================
# CREATE POLLUTION
# ============================================================

if st.sidebar.button(
    "🏭 Create Pollution",
    use_container_width=True
):

    for agent in model.agents:

        distance = (
            abs(agent.x - 10)
            + abs(agent.y - 10)
        )

        if distance <= 3:

            agent.temperature = 30
            agent.humidity = 40
            agent.smoke = 0.60
            agent.co2 = 1200
            agent.air_quality = 180
            agent.soil_moisture = 50

    model.analyze_environment()

    st.session_state.consensus = (
        model.determine_consensus()
    )

    st.session_state.event_created = True
    st.session_state.event_type = "POLLUTION"

    st.rerun()


# ============================================================
# CREATE EXTREME HEAT
# ============================================================

if st.sidebar.button(
    "🌡️ Create Extreme Heat",
    use_container_width=True
):

    for agent in model.agents:

        distance = (
            abs(agent.x - 10)
            + abs(agent.y - 10)
        )

        if distance <= 3:

            agent.temperature = 43
            agent.humidity = 20
            agent.smoke = 0.12
            agent.co2 = 450
            agent.air_quality = 60
            agent.soil_moisture = 30

    model.analyze_environment()

    st.session_state.consensus = (
        model.determine_consensus()
    )

    st.session_state.event_created = True
    st.session_state.event_type = "EXTREME_HEAT"

    st.rerun()


# ============================================================
# FAIL FIRE AGENT
# ============================================================

if st.sidebar.button(
    "❌ Fail Fire Agent",
    use_container_width=True
):

    fire_agents = model.get_fire_agents()

    if fire_agents:

        failed_agent = fire_agents[0]

        failed_agent.status = "FAILED"

        model.network.remove_agent_connections(
            failed_agent
        )

        st.sidebar.success(
            f"{failed_agent.agent_id} failed."
        )

    else:

        st.sidebar.warning(
            "No FIRE-detecting agent available."
        )

    st.rerun()


# ============================================================
# RECOVER NETWORK
# ============================================================

if st.sidebar.button(
    "🔄 Recover Network",
    use_container_width=True
):

    model.rebuild_network(
        max_distance=4
    )

    st.sidebar.success(
        "Network reorganized successfully."
    )

    st.rerun()


# ============================================================
# RESET
# ============================================================

if st.sidebar.button(
    "♻️ Reset Simulation",
    use_container_width=True
):

    model = EnvironmentalModel(
        width=20,
        height=20,
        num_agents=20
    )

    model.create_demo_layout()

    st.session_state.model = model
    st.session_state.event_created = False
    st.session_state.event_type = "None"
    st.session_state.consensus = None

    st.rerun()


# ============================================================
# ANALYZE CURRENT STATE
# ============================================================

if st.session_state.event_created:

    model.analyze_environment()


# ============================================================
# STATISTICS
# ============================================================

stats = model.get_statistics()


# ============================================================
# TOP METRICS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Total Agents",
        stats["total_agents"]
    )

with c2:
    st.metric(
        "Active Agents",
        stats["active_agents"]
    )

with c3:
    st.metric(
        "Failed Agents",
        stats["failed_agents"]
    )

with c4:
    st.metric(
        "Connections",
        stats["connections"]
    )


c5, c6, c7, c8 = st.columns(4)

with c5:
    st.metric(
        "Anomalies",
        stats["anomalies"]
    )

with c6:
    st.metric(
        "Fire Detectors",
        stats["fire_detections"]
    )

with c7:

    if st.session_state.consensus:
        consensus_status = (
            "CONFIRMED"
            if st.session_state.consensus["consensus"]
            else "UNCERTAIN"
        )
    else:
        consensus_status = "NONE"

    st.metric(
        "Consensus",
        consensus_status
    )

with c8:
    st.metric(
        "Current Event",
        st.session_state.event_type
    )


# ============================================================
# SYSTEM DECISION
# ============================================================

st.subheader("System Decision")


if st.session_state.consensus:

    consensus = st.session_state.consensus

    if consensus["event"] == "FIRE":

        st.error(
            f"🔥 FIRE CONFIRMED"
        )

        d1, d2, d3, d4 = st.columns(4)

        with d1:
            st.write("**Fire Detectors**")
            st.write(
                f"{stats['fire_detections']} / "
                f"{stats['total_agents']}"
            )

        with d2:
            st.write("**Consensus**")
            st.write("CONFIRMED")

        with d3:
            st.write("**Network**")
            st.write(
                "CONNECTED"
                if stats["connections"] > 0
                else "DISCONNECTED"
            )

        with d4:
            st.write("**Failed Agents**")
            st.write(stats["failed_agents"])

        st.caption(
            f"Local-consensus network score: "
            f"{consensus['confidence']:.2f}"
        )

    elif consensus["event"] != "NORMAL":

        st.warning(
            f"⚠️ {consensus['event']} DETECTED"
        )

        st.write(
            f"Consensus confidence: "
            f"{consensus['confidence']:.2f}"
        )

    else:

        st.success(
            "✅ Environment is currently NORMAL."
        )

else:

    st.info(
        "No environmental event has been triggered."
    )


# ============================================================
# VISUALIZATION
# ============================================================

st.subheader("Multi-Agent Environment")


fig, ax = plt.subplots(
    figsize=(12, 8)
)


# ============================================================
# COMMUNICATION LINKS
# ============================================================

for agent_a_id, agent_b_id in (
    model.network.graph.edges()
):

    agent_a = model.network.graph.nodes[
        agent_a_id
    ]["agent"]

    agent_b = model.network.graph.nodes[
        agent_b_id
    ]["agent"]

    if (
        agent_a.status == "ACTIVE"
        and agent_b.status == "ACTIVE"
    ):

        ax.plot(
            [agent_a.x, agent_b.x],
            [agent_a.y, agent_b.y],
            linewidth=1
        )


# ============================================================
# AGENTS
# ============================================================

for agent in model.agents:

    # --------------------------------------------------------
    # Failed
    # --------------------------------------------------------

    if agent.status == "FAILED":

        ax.scatter(
            agent.x,
            agent.y,
            s=350,
            marker="x"
        )

        ax.text(
            agent.x,
            agent.y + 0.45,
            f"{agent.agent_id} FAILED",
            ha="center",
            fontsize=8
        )

        continue


    # --------------------------------------------------------
    # Fire detector
    # --------------------------------------------------------

    if (
        agent.ai_result
        and agent.ai_result["event"] == "FIRE"
    ):

        ax.scatter(
            agent.x,
            agent.y,
            s=350,
            marker="*"
        )

    else:

        ax.scatter(
            agent.x,
            agent.y,
            s=180,
            marker="o"
        )


    ax.text(
        agent.x,
        agent.y,
        agent.agent_id,
        ha="center",
        va="center",
        fontsize=8
    )


# ============================================================
# EVENT REGION
# ============================================================

if st.session_state.event_created:

    event_circle = plt.Circle(
        (10, 10),
        3,
        fill=False,
        linewidth=3
    )

    ax.add_patch(event_circle)

    ax.text(
        10,
        6.5,
        f"{st.session_state.event_type} ZONE",
        ha="center",
        fontsize=11
    )


# ============================================================
# GRAPH FORMATTING
# ============================================================

ax.set_xlim(-1, 20)
ax.set_ylim(-1, 20)

ax.set_xlabel("Environment X")
ax.set_ylabel("Environment Y")

ax.grid(True)

st.pyplot(
    fig,
    use_container_width=True
)


# ============================================================
# AGENT STATUS TABLE
# ============================================================

st.subheader("Agent Status")


rows = []

for agent in model.agents:

    if agent.ai_result:

        ai_status = agent.ai_result["status"]
        event = agent.ai_result["event"]
        score = agent.ai_result["score"]

    else:

        ai_status = "NOT ANALYZED"
        event = "None"
        score = 0


    rows.append({
        "Agent": agent.agent_id,
        "X": agent.x,
        "Y": agent.y,
        "Status": agent.status,
        "AI Status": ai_status,
        "Event": event,
        "Battery": agent.battery,
        "Neighbors": len(agent.neighbors),
        "Score": score
    })


st.dataframe(
    rows,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# PROJECT PIPELINE
# ============================================================

st.subheader("System Pipeline")

st.write(
    """
    **Environmental Sensing**
    → **Local AI Anomaly Detection**
    → **Event Classification**
    → **Agent-to-Agent Communication**
    → **Decentralized Consensus**
    → **Agent Failure Detection**
    → **Self-Organization**
    → **Network Recovery**
    """
)