import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "agents")
    )
)

from monitoring_agent import MonitoringAgent
from network_manager import NetworkManager


# Create agents

a1 = MonitoringAgent(
    "A1", 1, 1,
    28, 60, 0.1, 420, 50, 55
)

a2 = MonitoringAgent(
    "A2", 2, 1,
    29, 58, 0.1, 430, 50, 55
)

a3 = MonitoringAgent(
    "A3", 3, 1,
    30, 57, 0.1, 440, 50, 54
)


agents = [a1, a2, a3]


# Create network

network = NetworkManager()

for agent in agents:
    network.add_agent(agent)

network.connect_agents(a1, a2)
network.connect_agents(a2, a3)


print("=" * 60)
print("INITIAL NETWORK")
print("=" * 60)

print(network.get_network_info())

for agent in agents:
    print(
        agent.agent_id,
        "->",
        [neighbor.agent_id for neighbor in agent.neighbors]
    )


# Simulate failure

print("\n" + "=" * 60)
print("SIMULATING A2 FAILURE")
print("=" * 60)

a2.status = "FAILED"

network.remove_agent_connections(a2)

print("A2 status:", a2.status)
print("A2 neighbors:", a2.neighbors)

print("\nNetwork before recovery:")
print(network.get_network_info())


# Automatic recovery

network.reorganize_network(
    agents,
    max_distance=2
)


print("\n" + "=" * 60)
print("NETWORK AFTER SELF-ORGANIZATION")
print("=" * 60)

print(network.get_network_info())

for agent in agents:
    print(
        agent.agent_id,
        "->",
        [neighbor.agent_id for neighbor in agent.neighbors]
    )