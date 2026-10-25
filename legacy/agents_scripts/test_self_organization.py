from monitoring_agent import MonitoringAgent
from self_organization import SelfOrganizationManager


# Create four agents

a1 = MonitoringAgent(
    agent_id="A1",
    x=1,
    y=1,
    temperature=28,
    humidity=60,
    smoke=0.10,
    co2=420,
    air_quality=50,
    soil_moisture=55
)

a2 = MonitoringAgent(
    agent_id="A2",
    x=2,
    y=1,
    temperature=29,
    humidity=58,
    smoke=0.12,
    co2=430,
    air_quality=52,
    soil_moisture=54
)

a3 = MonitoringAgent(
    agent_id="A3",
    x=3,
    y=1,
    temperature=30,
    humidity=57,
    smoke=0.11,
    co2=440,
    air_quality=53,
    soil_moisture=52
)

a4 = MonitoringAgent(
    agent_id="A4",
    x=2,
    y=2,
    temperature=28,
    humidity=59,
    smoke=0.10,
    co2=425,
    air_quality=51,
    soil_moisture=56
)


agents = [a1, a2, a3, a4]


# Initial network

a1.add_neighbor(a2)
a2.add_neighbor(a1)

a2.add_neighbor(a3)
a3.add_neighbor(a2)

a2.add_neighbor(a4)
a4.add_neighbor(a2)


print("=" * 60)
print("INITIAL NETWORK")
print("=" * 60)

for agent in agents:
    print(
        agent.agent_id,
        "->",
        [neighbor.agent_id for neighbor in agent.neighbors]
    )


# Simulate A2 failure

print("\n" + "=" * 60)
print("SIMULATING AGENT FAILURE")
print("=" * 60)

a2.status = "FAILED"

print("Agent A2 status:", a2.status)


# Self-organize the network

SelfOrganizationManager.reorganize_network(agents)


# Display new network

print("\n" + "=" * 60)
print("NETWORK AFTER SELF-ORGANIZATION")
print("=" * 60)

for agent in agents:
    print(
        agent.agent_id,
        "->",
        [neighbor.agent_id for neighbor in agent.neighbors]
    )