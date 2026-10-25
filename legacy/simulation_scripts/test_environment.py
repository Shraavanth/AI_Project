from simulation.environment_model import EnvironmentalModel


# ============================================================
# START
# ============================================================

print("=" * 70)
print("SELF-ORGANIZING MULTI-AGENT ENVIRONMENTAL MONITORING")
print("=" * 70)


# ============================================================
# CREATE ENVIRONMENT
# ============================================================

model = EnvironmentalModel(
    width=20,
    height=20,
    num_agents=20
)


# Use predictable demonstration layout
model.create_demo_layout()


# ============================================================
# DISPLAY AGENTS
# ============================================================

print("\n" + "=" * 70)
print("AGENTS")
print("=" * 70)

print(
    f"Total agents: {len(model.agents)}"
)

for agent in model.agents:

    print(
        f"{agent.agent_id:>3} "
        f"-> position=({agent.x:2}, {agent.y:2})"
    )


# ============================================================
# INITIAL NETWORK
# ============================================================

print("\n" + "=" * 70)
print("INITIAL NETWORK")
print("=" * 70)

print(model.get_statistics())

for agent in model.agents:

    neighbors = [
        neighbor.agent_id
        for neighbor in agent.neighbors
    ]

    print(
        f"{agent.agent_id:>3} "
        f"-> {neighbors}"
    )


# ============================================================
# CREATE FIRE
# ============================================================

print("\n" + "=" * 70)
print("CREATING FIRE EVENT")
print("=" * 70)

affected_agents = model.create_fire_event(
    center_x=10,
    center_y=10,
    radius=3
)

print(
    f"\nAgents physically inside fire region: "
    f"{len(affected_agents)}"
)

for agent in affected_agents:

    print(
        f"{agent.agent_id} "
        f"-> ({agent.x}, {agent.y})"
    )


# ============================================================
# LOCAL AI ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("LOCAL AI ANALYSIS")
print("=" * 70)

results = model.analyze_environment()

for agent_id, result in results.items():

    print(
        f"{agent_id:>3} -> "
        f"status={result['status']:<7} "
        f"event={result['event']:<15} "
        f"score={result['score']}"
    )


# ============================================================
# FIRE DETECTIONS
# ============================================================

print("\n" + "=" * 70)
print("FIRE DETECTIONS")
print("=" * 70)

fire_agents = model.get_fire_agents()

print(
    f"Agents detecting FIRE: "
    f"{len(fire_agents)}"
)

for agent in fire_agents:

    print(
        f"{agent.agent_id} "
        f"at ({agent.x}, {agent.y}) "
        f"-> FIRE"
    )


# ============================================================
# ALERT PROPAGATION
# ============================================================

print("\n" + "=" * 70)
print("AGENT-TO-AGENT ALERT PROPAGATION")
print("=" * 70)

model.broadcast_alerts()


# ============================================================
# LOCAL CONSENSUS DETAILS
# ============================================================

print("\n" + "=" * 70)
print("LOCAL CONSENSUS")
print("=" * 70)

for agent in model.get_active_agents():

    result = (
        __import__(
            "agents.consensus",
            fromlist=["ConsensusManager"]
        )
        .ConsensusManager.local_consensus(
            agent,
            threshold=0.5
        )
    )

    print(
        f"{agent.agent_id:>3} -> "
        f"event={result['event']:<15} "
        f"confidence={result['confidence']:.2f} "
        f"consensus={result['consensus']}"
    )


# ============================================================
# NETWORK-LEVEL RESULT
# ============================================================

print("\n" + "=" * 70)
print("DECENTRALIZED CONSENSUS")
print("=" * 70)

consensus = model.determine_consensus()

print(
    "Consensus reached:",
    consensus["consensus"]
)

print(
    "Detected event:",
    consensus["event"]
)

print(
    "Confidence:",
    consensus["confidence"]
)


# ============================================================
# FINAL STATISTICS
# ============================================================

print("\n" + "=" * 70)
print("FINAL STATISTICS")
print("=" * 70)

statistics = model.get_statistics()

for key, value in statistics.items():

    print(
        f"{key.replace('_', ' ').title():<20}: "
        f"{value}"
    )


print("\n" + "=" * 70)
print("SIMULATION COMPLETE")
print("=" * 70)