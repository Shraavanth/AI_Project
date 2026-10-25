import sys
import os

import matplotlib.pyplot as plt
import networkx as nx


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from simulation.environment_model import EnvironmentalModel


# ============================================================
# CREATE MODEL
# ============================================================

model = EnvironmentalModel(
    width=20,
    height=20,
    num_agents=20
)

# Use our predictable demonstration layout
model.create_demo_layout()


# ============================================================
# CREATE FIRE
# ============================================================

fire_x = 10
fire_y = 10
fire_radius = 3

affected_agents = model.create_fire_event(
    center_x=fire_x,
    center_y=fire_y,
    radius=fire_radius
)


# ============================================================
# AI ANALYSIS
# ============================================================

model.analyze_environment()


# ============================================================
# BUILD NETWORK GRAPH
# ============================================================

graph = model.network.graph


# ============================================================
# DRAW
# ============================================================

plt.figure(figsize=(12, 10))


# ------------------------------------------------------------
# Draw communication links
# ------------------------------------------------------------

for agent_a, agent_b in graph.edges():

    a = graph.nodes[agent_a]["agent"]
    b = graph.nodes[agent_b]["agent"]

    plt.plot(
        [a.x, b.x],
        [a.y, b.y],
        linewidth=1
    )


# ------------------------------------------------------------
# Draw agents
# ------------------------------------------------------------

for agent in model.agents:

    # Fire detecting agents
    if (
        agent.ai_result
        and agent.ai_result["event"] == "FIRE"
    ):

        plt.scatter(
            agent.x,
            agent.y,
            s=300,
            marker="o"
        )

        plt.text(
            agent.x,
            agent.y,
            agent.agent_id,
            fontsize=9,
            ha="center",
            va="center"
        )

    else:

        plt.scatter(
            agent.x,
            agent.y,
            s=200,
            marker="o"
        )

        plt.text(
            agent.x,
            agent.y,
            agent.agent_id,
            fontsize=9,
            ha="center",
            va="center"
        )


# ============================================================
# FIRE REGION
# ============================================================

fire_circle = plt.Circle(
    (fire_x, fire_y),
    fire_radius,
    fill=False,
    linewidth=3
)

plt.gca().add_patch(fire_circle)


# Fire center
plt.scatter(
    fire_x,
    fire_y,
    marker="x",
    s=200
)


# ============================================================
# TITLES
# ============================================================

fire_count = len(
    model.get_fire_agents()
)

connection_count = (
    model.network.graph.number_of_edges()
)

plt.title(
    "Self-Organizing Multi-Agent Environmental Monitoring\n"
    f"Agents: {len(model.agents)} | "
    f"Connections: {connection_count} | "
    f"Fire Detectors: {fire_count}"
)


plt.xlabel("Environment X")
plt.ylabel("Environment Y")


plt.xlim(
    -1,
    model.width
)

plt.ylim(
    -1,
    model.height
)


plt.grid(True)


# ============================================================
# DISPLAY
# ============================================================

plt.show()