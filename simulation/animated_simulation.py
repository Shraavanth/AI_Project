import sys
import os

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

from simulation.environment_model import EnvironmentalModel


# ============================================================
# CREATE MODEL
# ============================================================

model = EnvironmentalModel(
    width=20,
    height=20,
    num_agents=20
)

# Use fixed demonstration positions
model.create_demo_layout()


# ============================================================
# FIRE PARAMETERS
# ============================================================

FIRE_X = 10
FIRE_Y = 10
FIRE_RADIUS = 3


# ============================================================
# SIMULATION STATE
# ============================================================

stage = "NORMAL"

fire_created = False
consensus_result = None
failed_agent = None
recovery_done = False


# ============================================================
# CREATE FIGURE
# ============================================================

fig, ax = plt.subplots(figsize=(12, 10))


# ============================================================
# FIRE REGION
# ============================================================

fire_circle = Circle(
    (FIRE_X, FIRE_Y),
    FIRE_RADIUS,
    fill=False,
    linewidth=3
)

ax.add_patch(fire_circle)


# ============================================================
# UPDATE FUNCTION
# ============================================================

def draw_simulation(frame):

    global stage
    global fire_created
    global consensus_result
    global failed_agent
    global recovery_done

    # --------------------------------------------------------
    # Clear current axes
    # --------------------------------------------------------

    ax.clear()

    # Re-add fire circle
    fire_circle = Circle(
        (FIRE_X, FIRE_Y),
        FIRE_RADIUS,
        fill=False,
        linewidth=3
    )

    ax.add_patch(fire_circle)

    # --------------------------------------------------------
    # STAGE 1: NORMAL
    # --------------------------------------------------------

    if frame < 30:

        stage = "NORMAL MONITORING"

    # --------------------------------------------------------
    # STAGE 2: CREATE FIRE
    # --------------------------------------------------------

    elif frame < 60:

        stage = "FIRE EVENT"

        if not fire_created:

            model.create_fire_event(
                center_x=FIRE_X,
                center_y=FIRE_Y,
                radius=FIRE_RADIUS
            )

            model.analyze_environment()

            fire_created = True

    # --------------------------------------------------------
    # STAGE 3: CONSENSUS
    # --------------------------------------------------------

    elif frame < 90:

        stage = "DECENTRALIZED CONSENSUS"

        if consensus_result is None:

            # Make sure all active agents have AI results
            model.analyze_environment()

            consensus_result = (
                model.determine_consensus()
            )

    # --------------------------------------------------------
    # STAGE 4: AGENT FAILURE
    # --------------------------------------------------------

    elif frame < 120:

        stage = "AGENT FAILURE"

        # Select a fire detecting agent
        if failed_agent is None:

            fire_agents = model.get_fire_agents()

            if fire_agents:

                # Choose one fire-monitoring agent
                failed_agent = fire_agents[0]

                failed_agent.status = "FAILED"

                # Remove its connections
                model.network.remove_agent_connections(
                    failed_agent
                )

    # --------------------------------------------------------
    # STAGE 5: SELF-ORGANIZATION
    # --------------------------------------------------------

    else:

        stage = "SELF-ORGANIZATION / NETWORK RECOVERY"

        if not recovery_done:

            active_agents = model.get_active_agents()

            # Rebuild communication network
            model.rebuild_network(
                max_distance=4
            )

            # Force additional local recovery
            # using the existing self-organization logic
            for i in range(len(active_agents)):

                for j in range(i + 1, len(active_agents)):

                    agent_a = active_agents[i]
                    agent_b = active_agents[j]

                    distance = (
                        abs(agent_a.x - agent_b.x)
                        + abs(agent_a.y - agent_b.y)
                    )

                    if distance <= 4:

                        model.network.connect_agents(
                            agent_a,
                            agent_b
                        )

            recovery_done = True

    # ========================================================
    # DRAW COMMUNICATION LINKS
    # ========================================================

    for agent_a_id, agent_b_id in model.network.graph.edges():

        agent_a = model.network.graph.nodes[
            agent_a_id
        ]["agent"]

        agent_b = model.network.graph.nodes[
            agent_b_id
        ]["agent"]

        # Do not draw links involving failed nodes
        if (
            agent_a.status == "FAILED"
            or agent_b.status == "FAILED"
        ):
            continue

        ax.plot(
            [agent_a.x, agent_b.x],
            [agent_a.y, agent_b.y],
            linewidth=1
        )

    # ========================================================
    # DRAW AGENTS
    # ========================================================

    for agent in model.agents:

        # Failed agent
        if agent.status == "FAILED":

            ax.scatter(
                agent.x,
                agent.y,
                s=300,
                marker="x"
            )

            ax.text(
                agent.x,
                agent.y + 0.45,
                f"{agent.agent_id} FAILED",
                ha="center",
                fontsize=9
            )

            continue

        # Fire detecting agent
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
                s=200,
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

    # ========================================================
    # FIRE CENTER
    # ========================================================

    if fire_created:

        ax.scatter(
            FIRE_X,
            FIRE_Y,
            s=250,
            marker="x"
        )

        ax.text(
            FIRE_X,
            FIRE_Y - FIRE_RADIUS - 0.7,
            "FIRE ZONE",
            ha="center",
            fontsize=11
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    statistics = model.get_statistics()

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    ax.set_title(
        "Self-Organizing Multi-Agent Environmental Monitoring\n"
        f"Stage: {stage}"
    )

    # --------------------------------------------------------
    # STATISTICS BOX
    # --------------------------------------------------------

    info = (
        f"Total Agents: {statistics['total_agents']}\n"
        f"Active Agents: {statistics['active_agents']}\n"
        f"Failed Agents: {statistics['failed_agents']}\n"
        f"Connections: {statistics['connections']}\n"
        f"Anomalies: {statistics['anomalies']}\n"
        f"Fire Detectors: {statistics['fire_detections']}"
    )

    if consensus_result is not None:

        info += (
            "\n\nConsensus: "
            f"{consensus_result['consensus']}"
            "\nEvent: "
            f"{consensus_result['event']}"
            "\nConfidence: "
            f"{consensus_result['confidence']}"
        )

    if failed_agent is not None:

        info += (
            f"\n\nFailed Agent: "
            f"{failed_agent.agent_id}"
        )

    ax.text(
        0.02,
        0.98,
        info,
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=10,
        bbox=dict(
            boxstyle="round",
            alpha=0.15
        )
    )

    # ========================================================
    # AXIS
    # ========================================================

    ax.set_xlim(-1, model.width)
    ax.set_ylim(-1, model.height)

    ax.set_xlabel("Environment X")
    ax.set_ylabel("Environment Y")

    ax.grid(True)


# ============================================================
# ANIMATION
# ============================================================

animation = FuncAnimation(
    fig,
    draw_simulation,
    frames=150,
    interval=150,
    repeat=True
)


# ============================================================
# SHOW
# ============================================================

plt.show()