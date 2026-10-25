from monitoring_agent import MonitoringAgent
from consensus import ConsensusManager


# -----------------------------------------
# Create agents
# -----------------------------------------

a1 = MonitoringAgent(
    agent_id="A1",
    x=1,
    y=1,
    temperature=45,
    humidity=15,
    smoke=0.90,
    co2=950,
    air_quality=80,
    soil_moisture=20
)

a2 = MonitoringAgent(
    agent_id="A2",
    x=2,
    y=1,
    temperature=44,
    humidity=18,
    smoke=0.85,
    co2=920,
    air_quality=75,
    soil_moisture=22
)

a3 = MonitoringAgent(
    agent_id="A3",
    x=3,
    y=1,
    temperature=28,
    humidity=60,
    smoke=0.10,
    co2=420,
    air_quality=50,
    soil_moisture=55
)

a4 = MonitoringAgent(
    agent_id="A4",
    x=2,
    y=2,
    temperature=46,
    humidity=14,
    smoke=0.88,
    co2=940,
    air_quality=82,
    soil_moisture=18
)


agents = [a1, a2, a3, a4]


# -----------------------------------------
# Analyze local environments
# -----------------------------------------

print("=" * 60)
print("LOCAL AGENT DECISIONS")
print("=" * 60)

for agent in agents:

    result = agent.analyze_environment()

    print(
        agent.agent_id,
        "->",
        result
    )


# -----------------------------------------
# Determine consensus
# -----------------------------------------

print("\n" + "=" * 60)
print("DECENTRALIZED CONSENSUS")
print("=" * 60)

consensus = ConsensusManager.determine_consensus(
    agents,
    threshold=0.5
)

print("Consensus reached:", consensus["consensus"])
print("Event:", consensus["event"])
print("Confidence:", consensus["confidence"])

print("\nIndividual decisions:")

for decision in consensus["decisions"]:

    print(
        decision["agent_id"],
        "->",
        decision["event"]
    )